# 09 · Performance

> Rule one: **measure before you touch anything.** Intuition about where the bottleneck is is
> systematically wrong. Rule two: optimizing something that is not the bottleneck **improves nothing**
> (Amdahl's law).


**Covers from the syllabus:** `concepts` · `caching` · `optimization` · `scaling` · `profiling` · `implementations` · `bottlenecks` · `tradeoffs`

---

## How to actually measure

**Percentiles, not averages.** An average of 100ms can hide the fact that 1% of your users wait 8 seconds.
And that 1% is almost always the customers with the most data: the most valuable ones.

- **p50** (median): the typical experience.
- **p95 / p99**: the bad experience. **This is what defines your reputation.**
- **p99.9**: where GC, retries and timeouts live.
- **Tail latency:** if a page makes 10 internal calls in parallel and each one has a
  p99 of 1s, **the probability that the whole page takes longer than 1s is ~10%**, not 1%. That is why the p99 of your
  dependencies becomes the p50 of your product.

**The metrics that matter:** latency (by percentile), **throughput** (RPS), **saturation** (CPU,
memory, pool and queue usage) and **error rate**. See the *four golden signals* in `12-observability.md`.

**Little's law:** `concurrency = throughput × latency`. If you serve 100 RPS at 200ms latency,
you have ~20 requests in flight. This is how you size pools and workers without guessing.

**Amdahl's law:** if something takes 20% of the time and you make it infinitely fast, you gain at most
20%. **Always attack whatever dominates the profile.**

> **Card** · **When:** before touching a single line to optimize ·
> **Pattern:** percentiles (p50/p95/p99) and histograms, never averages ·
> **Anti-pattern:** averaging the p99s of several instances — mathematically it means nothing ·
> **Limits:** Amdahl's law bounds what you can gain by optimizing one part ·
> **How it fails:** a 100 ms average hides the fact that 1% wait 8 seconds ·
> **Decision:** use Little's law (`concurrency = throughput × latency`) to size pools ·
> **Trade-off:** measuring costs (cardinality, storage) and not measuring costs more ·
> **Related:** metrics, SLOs `[10, 12]`

---

## Profiling and bottleneck analysis

**The right order of investigation:**
1. **Where is the time going?** Distributed tracing to see the per-service breakdown (`12-observability.md`).
2. **Is it CPU, I/O, memory or contention?** Each one has a different signature:
   - CPU at 100% → CPU profiler, flame graph.
   - Low CPU but slow → **you are waiting**: DB, network, lock, exhausted pool.
   - Growing memory → leak or unbounded cache.
   - Periodic spikes → GC, cron, synchronized cache expiry.
3. **Profiler:** flame graphs (`py-spy`, `async-profiler`, `pprof`), *continuous profiling* in production
   (Pyroscope, Parca — and OpenTelemetry profiling, which is in alpha in 2026).
4. **Database:** `pg_stat_statements` sorted by total time — the culprit is usually a "fast" query
   executed a million times, not the slow one.

**The real bottlenecks in a typical app, by frequency:**
1. **N+1 queries** (`04-databases.md`) — the undisputed champion.
2. Missing index, or a useless one.
3. Synchronous external calls with no timeout and no cache.
4. Serializing huge payloads (fetching 10,000 rows to render 20).
5. Exhausted connection pool (it looks like latency, it is a queue).
6. Work that should be asynchronous done inside the request (sending email, generating a PDF, resizing).

> **Card** · **When:** when the metrics point but don't explain ·
> **Pattern:** metrics → traces → logs → profiler, in that order ·
> **Anti-pattern:** optimizing by intuition without profiling ·
> **Limits:** profiling in production adds overhead; continuous profiling minimizes it ·
> **How it fails:** the culprit is usually a fast query executed a million times, not the slow one ·
> **Decision:** sort `pg_stat_statements` by **total time**, not by mean ·
> **Trade-off:** instrumentation overhead vs blindness ·
> **Related:** N+1, tracing `[04, 12]`

---

## Caching

**The full hierarchy**, from nearest to farthest:

```
Browser → CDN → Reverse proxy → Application cache (in-process) → Redis → DB (buffer pool)
```

**Patterns:**

| Pattern | How | When |
|---|---|---|
| **Cache-aside** (lazy) | the app checks the cache; on a miss it goes to the DB and fills it | **the default**; simple and robust |
| Read-through | the cache goes to the DB for you | less code, less control |
| Write-through | you write to cache and DB at the same time | reads always fresh, slower writes |
| Write-behind | you write to the cache, it is flushed later | blazing fast; **you can lose data** |
| Refresh-ahead | refreshes before expiry | avoids the miss on hot keys |

**Invalidation — "one of the two hard problems in computer science":**
- **TTL** is the most robust strategy because it fails predictably. Always start here.
- **Explicit invalidation on write** is fresher but gets forgotten in the new endpoint.
- **Key versioning** (`product:42:v7`) avoids deleting: you bump the version and the old one expires on its own.
- **Cache the result, not the process**, and **never cache data with different permissions under the same key**
  (cross-user leak). If it depends on the user, the key includes the user.

**The three classic pathologies:**
- **Thundering herd / stampede:** a hot key expires and 5,000 requests hit the DB at once.
  Fix: *single-flight* (only one regenerates, the rest wait), TTL with jitter, or `stale-while-revalidate`.
- **Cache penetration:** lookups for keys that don't exist always fall through to the DB. Fix: cache the
  "does not exist" with a short TTL, or a bloom filter.
- **Hot key:** one key concentrates the traffic and saturates a single Redis node. Fix: replicate the key with
  suffixes, or also cache it in the process's local memory.

**Key metric:** **hit ratio**. A cache with a 20% hit rate adds latency and complexity while giving nothing back;
below ~80-90% on hot reads, rethink the key or the TTL.

> **Card** · **When:** high read/write ratio and data that tolerates some staleness ·
> **Pattern:** cache-aside + TTL with jitter + single-flight ·
> **Anti-pattern:** caching data with different permissions under the same key — it is a leak ·
> **Limits:** invalidation is the hard problem; TTL fails predictably and that is why it is preferred ·
> **How it fails:** **thundering herd** when a hot key expires ·
> **Decision:** if the hit ratio does not exceed ~80-90%, the cache adds latency while giving nothing back ·
> **Trade-off:** freshness vs latency and origin load ·
> **Related:** CDN, Redis, invalidation `[02, 04]`

---

## CDN and HTTP caching

- Serve static assets **and also cacheable API responses** from the edge (`s-maxage`).
- **Cache key:** URL + the `Vary` headers. If you vary by `Authorization` without declaring it, you serve one
  user's data to another (**security incident**, see `02-web-protocols.md`).
- **Purge** by tag/surrogate key instead of by URL: you invalidate "everything for product 42" in one go.
- **Origin shield** and `stale-while-revalidate` / `stale-if-error`: the CDN keeps serving slightly stale
  content while your origin recovers. **It is one of the best defenses against a spike.**

> **Card** · **When:** static assets, and also cacheable API responses ·
> **Pattern:** purge by tag and `stale-while-revalidate` / `stale-if-error` ·
> **Anti-pattern:** varying by `Authorization` without declaring `Vary` ·
> **Limits:** you cannot take back what has already been served; you can only purge what remains ·
> **How it fails:** the CDN serves one user's content to another ·
> **Decision:** `stale-if-error` is one of the best defenses against a spike at the origin ·
> **Trade-off:** minimal latency at the edge vs slightly stale data ·
> **Related:** HTTP caching, headers `[02]`

---

## Database optimization

Operational summary (the detail is in `04-databases.md`):
correct indexes with the correct column order · kill the N+1 · `SELECT` only the columns you need ·
keyset pagination · **batching** (one query with `IN (...)` instead of 100) · materialized views for
expensive aggregations · partitioning for huge tables · read replicas to offload reads ·
`work_mem` and the rest of the parameters tuned · **watch bloat and autovacuum**.

**The two tips that give the most performance per unit of effort:**
1. **Batch.** Turning N calls into one is almost always an order-of-magnitude improvement, because the
   dominant cost is the round trip, not the work.
2. **Move work out of the request.** If the user does not need the result now, it goes to a queue.

> **Card** · **When:** this is almost always where the bottleneck is ·
> **Pattern:** batching (`IN (...)`) and moving work out of the request ·
> **Anti-pattern:** the N+1, and fetching 10,000 rows to render 20 ·
> **Limits:** materialized views are stale until they are refreshed ·
> **How it fails:** a query loses its index when the table grows and the plan changes ·
> **Decision:** if the user does not need the result now, it goes to a queue ·
> **Trade-off:** denormalizing speeds up reads and adds consistency work ·
> **Related:** indexes, N+1, queues `[04, 08]`

---

## Connection pools

A badly sized pool shows up as **latency**, but it is a **queue**:
`total time = wait for a connection + query time`.

- **Bigger is not better.** Past the sweet spot (roughly `cores × 2` for the DB), adding
  connections *lowers* throughput through context switching and lock contention.
- Size with Little's law: if you need 500 RPS and each query takes 20ms, you need ~10 busy connections
  on average. Leave headroom for spikes, not 100×.
- **Mandatory timeouts:** acquisition (fail fast if the pool is full), query, and idle
  connection. Without an acquisition timeout, one slow query produces a cascading collapse.
- **Separate pools** for critical work and for batch/reporting. If the monthly report exhausts the pool, your
  API goes down. That is a **bulkhead** (`10-reliability.md`).

> **Card** · **When:** every connection to a database or external service ·
> **Pattern:** size with Little's law and **separate pools** by criticality ·
> **Anti-pattern:** one giant pool shared between the API and the reports ·
> **Limits:** past the sweet spot (~cores × 2 on the DB), more connections **lower** throughput ·
> **How it fails:** it looks like latency, but it is a queue waiting for a connection ·
> **Decision:** short acquisition timeout: failing fast is better than collapsing ·
> **Trade-off:** isolation (separate pools) vs utilization ·
> **Related:** bulkheads, PgBouncer `[04, 10]`

---

## Load balancing

**Algorithms:** round robin · **least connections** (better with variable-duration requests) ·
weighted (heterogeneous nodes) · **consistent hashing** (cache or session affinity) · EWMA / least response
time (the smartest, picks by observed latency).

- **L4 (TCP) vs L7 (HTTP):** L4 is fast and opaque; L7 understands routes and headers and can do retries,
  path-based routing and TLS termination.
- **Health checks:** *liveness* (is it alive?) vs *readiness* (can it take traffic?). A check that only
  pings the port will declare healthy a service whose DB is down.
- **Connection draining:** when removing a node, stop sending it new traffic but **let it finish what is in
  flight**. Without this, every deployment produces visible 502 errors.
- **Sticky sessions:** needed for WebSocket, but they unbalance the load and complicate scaling.
  Better: state outside the process (Redis) and interchangeable nodes.

> **Card** · **When:** from the second instance onwards ·
> **Pattern:** least-connections or EWMA + readiness probes + connection draining ·
> **Anti-pattern:** a health check that only pings the port ·
> **Limits:** sticky sessions unbalance the load and complicate scaling ·
> **How it fails:** without draining, **every deployment produces visible 502s** ·
> **Decision:** state outside the process so that nodes are interchangeable ·
> **Trade-off:** affinity (warm local cache) vs even distribution ·
> **Related:** health checks, deployments `[12, 13, 14]`

---

## Horizontal vs vertical scaling

| | Vertical (bigger machine) | Horizontal (more machines) |
|---|---|---|
| Complexity | **none** | shared state, coordination, LB |
| Ceiling | physical and expensive (the price curve is worse than linear) | practically unlimited |
| Availability | **single point of failure** | fault tolerance |
| Cost | jumps in large steps | granular |

**The pragmatic advice:** scale vertically first — it is one line of Terraform and buys you years. Scale
horizontally when you need **availability** (not just capacity) or when vertical runs out.

**Horizontal's prerequisite: services must be stateless.** Session in Redis, files in S3, nothing on
local disk, nothing in process memory that has to survive. If any node can serve any
request, scaling is trivial.

**Autoscaling:** scale on the metric that reflects real saturation (RPS, queue depth, latency),
not just CPU. Watch out for *flapping*: add cooldowns and scale down much more slowly than you scale
up. And remember that **starting an instance takes time** — if the spike is faster than your startup time,
autoscaling won't save you (you need spare capacity or a queue to absorb it).

> **Card** · **When:** when you hit the capacity limit ·
> **Pattern:** vertical first (one line, buys years), horizontal when you need availability ·
> **Anti-pattern:** a distributed architecture for traffic that fits on one machine ·
> **Limits:** horizontal requires **stateless** services ·
> **How it fails:** scaling does nothing if the bottleneck is the shared database ·
> **Decision:** do you need capacity or fault tolerance? Only the latter forces horizontal ·
> **Trade-off:** simplicity vs availability ·
> **Related:** stateless, autoscaling `[13]`

---

## Compression

- **brotli** for text (best ratio), **gzip** as the universal option, **zstd** when you control both ends
  (very fast and a good ratio).
- Compression level: compressing at maximum burns CPU on your server. For dynamic content, a medium level
  is usually optimal; for static assets, precompress at maximum **at build time**, not on every request.
- **Don't compress** what is already compressed, or tiny responses (the overhead exceeds the gain).
- **Compression in the database and in the queue**: smaller payloads = more things in the buffer pool,
  less I/O, less bandwidth. Sometimes it is the cheapest optimization there is.

> **Card** · **When:** text responses of meaningful size ·
> **Pattern:** brotli for text; precompress static assets at build time ·
> **Anti-pattern:** compressing what is already compressed, or at maximum level on every dynamic response ·
> **Limits:** compression costs CPU on the critical path ·
> **How it fails:** compressing secrets alongside reflected input opens the door to BREACH ·
> **Decision:** medium level for dynamic content, maximum for static ·
> **Trade-off:** bandwidth vs CPU ·
> **Related:** content negotiation `[02]`

---

## Backpressure

**What it is:** when the producer is faster than the consumer, someone has to slow down. If nobody does,
memory piles up until the OOM and the system does not degrade: it **collapses**.

- **Bounded queues.** An unbounded queue only moves the point where you blow up, and in the meantime it adds latency
  to everything inside it.
- **Load shedding:** reject early (429/503) what you will not be able to serve. **It is better to serve 80% well
  than 100% terribly.** Prioritize: drop the lowest-value traffic first (batch, bots, retries).
- **Timeouts and propagated deadlines:** if the client has already given up, your server should not keep working.
  Propagating the deadline down the whole chain avoids phantom work that only burns resources.
- **Streaming with flow control:** TCP already does it; in your app, process in batches and don't load everything into memory.
- **Bounded concurrency** (semaphores, pools): the simplest form of backpressure.

**The typical failure without backpressure:** a spike arrives, the queue grows, latency rises, clients
time out **and retry**, which doubles the load on an already saturated system. It is a death spiral,
and it is exactly what load shedding and the circuit breaker prevent.

> **Card** · **When:** any system with queues or fast producers ·
> **Pattern:** **bounded** queues, load shedding, bounded concurrency, propagated deadlines ·
> **Anti-pattern:** unbounded queue — it only moves the point where you blow up, and adds latency in the meantime ·
> **Limits:** rejecting early means returning errors to legitimate users ·
> **How it fails:** death spiral — timeout, retry, more load, more timeouts ·
> **Decision:** it is better to serve 80% well than 100% terribly ·
> **Trade-off:** partial availability vs total collapse ·
> **Related:** rate limiting, circuit breakers `[03, 10]`

---

## Implementation: the techniques, in code

**Cache-aside with single-flight** — the default pattern, protected against the thundering herd:

```python
_in_flight: dict[str, asyncio.Future] = {}

async def with_cache(key: str, ttl: int, compute):
    if (value := await redis.get(key)) is not None:
        return json.loads(value)

    # single-flight: if someone is already computing this key, wait for their result
    if key in _in_flight:
        return await _in_flight[key]

    fut = _in_flight[key] = asyncio.get_event_loop().create_future()
    try:
        value = await compute()
        jitter = random.uniform(0.8, 1.2)          # TTL with jitter: avoids synchronized expiry
        await redis.setex(key, int(ttl * jitter), json.dumps(value))
        fut.set_result(value)
        return value
    except Exception as e:
        fut.set_exception(e)
        raise
    finally:
        _in_flight.pop(key, None)
```

**Killing an N+1 with batching** (the DataLoader pattern, which also solves the GraphQL N+1):

```python
# BAD: 1 + N queries
orders = await repo.orders.list(limit=100)
for o in orders:
    o.customer = await repo.customers.get(o.customer_id)     # 100 queries

# GOOD: 2 queries
orders = await repo.orders.list(limit=100)
ids = {o.customer_id for o in orders}
customers = {c.id: c for c in await repo.customers.get_many(ids)}   # WHERE id = ANY($1)
for o in orders:
    o.customer = customers[o.customer_id]
```

**Limiting concurrency towards a dependency** (bulkhead, `[10]`):

```python
class LimitedClient:
    def __init__(self, sem_max=10, timeout=2.0):
        self._sem = asyncio.Semaphore(sem_max)     # at most 10 in flight
        self._timeout = timeout

    async def get(self, url):
        async with self._sem:                      # if it is full, wait (backpressure)
            return await asyncio.wait_for(self._http.get(url), self._timeout)
```

**Streaming a large export** — constant memory instead of linear:

```python
async def export_csv():
    async def rows():
        yield "id,total,currency\n"
        async for o in repo.orders.iterate(batch=1000):   # server-side cursor, not fetchall
            yield f"{o.id},{o.total},{o.currency}\n"
    return StreamingResponse(rows(), media_type="text/csv")
```

> **Card** · **When:** all four show up in almost any service under load ·
> **Pattern:** cache with single-flight and jitter; batch; bound concurrency; stream ·
> **Anti-pattern:** cache without TTL, query loop, unbounded concurrency, `fetchall()` ·
> **Limits:** in-memory single-flight only protects **within one process**; with N replicas you get N regenerations or need a distributed lock ·
> **How it fails:** without jitter, a thousand keys created at the same time expire at the same time ·
> **Decision:** batch whenever the dominant cost is the round trip ·
> **Trade-off:** batching improves throughput and worsens individual latency ·
> **Related:** N+1, bulkheads, backpressure `[04, 10]`

---

## Diagnosing a performance incident

Typical symptom: *"the app is slow"*. The order that works:

1. **Slow for whom, and where?** One endpoint or all of them? All users or those with lots of
   data? Sudden or gradual?
   - **Sudden** → a change: deployment, configuration, traffic spike, a noisy neighbor.
   - **Gradual** → growth: data, bloat, memory leak, an index that stopped being selective,
     a cache that lost effectiveness.
2. **Saturation or waiting?** High CPU = your code. Low CPU and slow = **you are waiting** on something:
   database, network, lock, or a queue in a pool.
3. **Trace of a real slow request** (`[12]`) and look at where the time goes.
4. **Mitigate:** scale, raise limits, turn on caching, switch off the expensive feature, rate limit the culprit.
5. **Fix it properly** afterwards, once the incident is closed.

| Signature | Probable cause |
|---|---|
| p50 fine, p99 terrible | GC, cache miss, users with lots of data, a slow shard |
| Everything slow at once | shared dependency: DB, cache, network |
| Slow only on deploy | cold cache, JIT not warmed up, empty connection pool |
| Slow with periodic spikes | cron, synchronized cache expiry, autovacuum |
| High latency with low CPU | a queue in some pool, or waiting on an external service |
| Gets worse the longer it runs since startup | memory leak, unclosed connections, fragmentation |

> **Card** · **When:** on any latency alert ·
> **Pattern:** narrow down before hypothesizing; ask **what changed** ·
> **Anti-pattern:** changing three things at once under pressure and not knowing which one worked ·
> **Limits:** without traces and percentiles you can only guess ·
> **How it fails:** you optimize what was not the bottleneck and nothing improves (Amdahl) ·
> **Decision:** mitigate first, diagnose later ·
> **Trade-off:** fast mitigation (you lose evidence) vs investigating (users keep suffering) ·
> **Related:** tracing, incident response `[10, 12]`

---

## Scaling in production: the order of intervention

From cheapest to most expensive. **Skipping steps is how you end up with unnecessary sharding.**

1. **Measure** and find the real limit (load test, `[11]`).
2. **Fix the obvious:** missing index, N+1, unbounded query, synchronous work that should be a queue.
3. **Cache.**
4. **Scale vertically** — one line of Terraform; buys months or years.
5. **Scale horizontally** the stateless parts.
6. **Read replicas.**
7. **Partitioning and archiving** of cold data.
8. **Sharding or splitting services** — the last resort (`[04]`).

**Signs you are approaching the limit:** latency rises before CPU does (a queue in a pool) · connection
pool maxed out · consumer lag growing · disk filling at a steady rate · autoscaling always at the
ceiling. **Watch trends, not instantaneous values:** the goal is to find out with weeks of margin.

**Autoscaling:** scale on the metric that reflects real saturation (RPS, queue depth, latency),
not just CPU. Add cooldowns, scale down much more slowly than you scale up, and remember that
**starting an instance takes time**: if the spike is faster than your startup time, you need spare
capacity or a queue to absorb it.

> **Card** · **When:** when planning capacity or facing sustained growth ·
> **Pattern:** exhaust the cheap options before the structural ones ·
> **Anti-pattern:** sharding or splitting into microservices before you have added an index ·
> **Limits:** horizontal scaling requires stateless services; vertical has a physical ceiling ·
> **How it fails:** autoscaling does not arrive in time because startup takes longer than the spike ·
> **Decision:** do you need capacity or availability? Only the latter forces horizontal ·
> **Trade-off:** infrastructure cost vs the engineering cost of optimizing ·
> **Related:** capacity planning, sharding, cost `[04, 13, 19]`

---

## Interview questions and trade-offs

**Q: Your endpoint takes 2s at p99 and 80ms at p50. What do you investigate?**
Something that only happens in some cases: users with lots of data (an N+1 that scales with volume), cache misses,
GC, pool contention, or a slow shard. *Signal:* you say the average is useless and that the first step is a trace
of one specific slow request, not a blind change.

**Q: How do you avoid the thundering herd when a hot cache entry expires?**
Single-flight (only one thread regenerates, the others wait or serve the stale value), TTL with jitter and
`stale-while-revalidate`. *Signal:* you mention that the problem is not the cache, it is that **the DB suddenly
receives all the traffic the cache was hiding from it**, and that you have to size with that in mind.

**Q: Does increasing the connection pool improve performance?**
Up to a point; after that it makes it worse. *Signal:* you explain Little's law for sizing, and that the DB has
a sweet spot close to `cores × 2` because more connections compete for the same resources.

**Q: What is backpressure and how do you implement it?**
Slowing down the producer when the consumer cannot keep up: bounded queues, load shedding, bounded concurrency
and propagated deadlines. *Signal:* you describe the retry spiral and say that rejecting fast is a
deliberate design decision, not a failure.

**Q: You are asked to "make the app faster". Where do you start?**
Define what fast means (which endpoint, which percentile, which target), measure, and attack whatever dominates the
profile. *Signal:* you cite Amdahl and ask about the business goal before touching code — optimizing without
a target number means not knowing when to stop.

**Core trade-off of this box:** *latency vs freshness vs cost*. Caching trades freshness for
latency; scaling trades money for capacity; batching trades individual latency for overall
throughput. There is no plain "faster" — there is **what you are willing to pay, and in which currency**.

---

## Sources

- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) — the four golden signals.
- Gil Tene, *How NOT to Measure Latency* — why averages and coordinated omission mislead you.
- [Brendan Gregg — Flame Graphs](https://www.brendangregg.com/flamegraphs.html) and the USE method.
- [AWS Builders' Library — Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)
- [PostgreSQL Performance Tuning Checklist 2026](https://dev.to/_d7eb1c1703182e3ce1782/postgresql-performance-tuning-checklist-2026-complete-guide-65a)
