# 01 · Fundamentals

> The foundation you are assumed to already have. Nobody asks you about this directly in a senior interview,
> but everything else collapses if you haven't mastered it: you give yourself away when explaining why a query
> is slow or why your service falls over with 200 concurrent users.

**Covers from the syllabus:** `concepts` · `patterns` · `implementations` · `constraints` · `failure_modes`
· `tradeoffs` · `tests`

---

## Algorithmic complexity

Big-O notation describes **how the cost grows** as the input grows, not how long it takes. `O(n)` with a
huge constant can be slower than `O(n²)` for small n. In real backend work, the constant and memory
access matter more than your degree led you to believe.

| Notation | Name | Typical backend example |
|---|---|---|
| O(1) | constant | hash map lookup, Redis access by key |
| O(log n) | logarithmic | B-tree index lookup, binary search |
| O(n) | linear | iterating over a list, full table scan |
| O(n log n) | linearithmic | sort, merging sorted lists |
| O(n²) | quadratic | doubly nested loop, the classic badly solved N+1 |
| O(2ⁿ) | exponential | brute force over subsets |

**Amortized vs worst case.** An `append` to a dynamic array is O(1) amortized, but the occasional resize
is O(n). If you have a p99 latency SLA, **the worst case *is* your latency**.

**Space complexity.** Loading 2 million rows into memory "just to sum them" is the most common
production bug there is. Streaming > loading everything.

```python
# O(n) in time and O(n) in MEMORY: 2M rows in RAM -> OOMKilled
total = sum(row.amount for row in cursor.fetchall())

# O(n) in time and O(1) in memory: the cursor fetches batches as it goes
total = 0
for row in cursor:               # server-side cursor
    total += row.amount
```

> **Card** · **When:** choosing a structure or algorithm over collections that grow ·
> **Pattern:** measure the order of growth before optimizing the constant ·
> **Anti-pattern:** optimizing an O(n²) loop over 50 elements that has 50 queries inside it ·
> **Limits:** Big-O ignores constants and the memory hierarchy; with small n it can lie ·
> **How it fails:** OOM from space complexity, and p99 blowing up because of the amortized worst case ·
> **Decision:** if the dominant cost is I/O, attack the I/O, not the loop ·
> **Trade-off:** time vs memory — almost every speedup is paid for in RAM ·
> **Related:** N+1 queries, query optimization `[04, 09]`

---

## The latency numbers you need to know by heart

```
L1 cache reference               ~1 ns
RAM reference                    ~100 ns
read 1 MB sequentially from RAM  ~10 µs
SSD random read                  ~100 µs        (1,000× slower than RAM)
round trip within the same DC    ~500 µs
read 1 MB from SSD               ~1 ms
intercontinental round trip      ~150 ms
```

The practical takeaway: **a network call costs as much as tens of thousands of in-memory
operations.** That's why batching and caching always win, and why moving work "to another service" is
never free.

> **Card** · **When:** estimating capacity or deciding whether to cache something `[19]` ·
> **Pattern:** turn N calls into one (batching) before optimizing the computation ·
> **Anti-pattern:** micro-optimizing CPU while making one round trip per element ·
> **Limits:** latency isn't fixed with more bandwidth, only by being closer ·
> **How it fails:** a "fast" service with 200 chained internal calls is slow without any single
> piece looking guilty · **Decision:** if it crosses the network, batch; if it crosses the continent, cache at the edge ·
> **Trade-off:** batching improves throughput and worsens the latency of each individual element ·
> **Related:** tail latency, CDN, capacity planning `[09, 13, 19]`

---

## Data structures

It's not about implementing a red-black tree; it's about choosing the right structure and knowing what you pay.

| Structure | Lookup | Insertion | When you use it in backend |
|---|---|---|---|
| Array / slice | O(n) | O(1) at the end | ordered lists, iteration, cache-friendly |
| Hash map | O(1) average | O(1) average | in-memory indexes, dedup, counters |
| B-tree | O(log n) | O(log n) | **database indexes** (disk: few levels, high fanout) |
| LSM-tree | O(log n) | very fast | Cassandra, RocksDB: optimized for writes |
| Heap | O(1) for the min | O(log n) | priority queues, schedulers, top-K |
| Trie | O(k) | O(k) | autocomplete, URL routing, prefixes |
| Bloom filter | O(k) probabilistic | O(k) | "is it definitely NOT there?" before going to disk |
| Skip list | O(log n) | O(log n) | Redis sorted sets |

**The three that set a senior apart:**

- **B-tree vs LSM-tree.** The B-tree updates in place (good for reads and updates, with page-level write
  amplification). The LSM-tree writes sequentially into levels and compacts later (brutal writes, more
  expensive reads). Postgres/MySQL = B-tree. Cassandra/RocksDB = LSM. **If you're asked "why does
  Cassandra write so fast?", the answer is LSM + append-only.**
- **Bloom filter.** It can give false positives but **never false negatives**. It's used to avoid I/O:
  "could this key be in this SSTable?" If it says no, you skip the disk.
- **Consistent hashing ring.** Distributing keys across N nodes so that adding a node only moves 1/N of
  the data. The basis of sharding and distributed caches. **It comes up constantly in system design.**

```python
# Consistent hashing in 12 lines: the ring is a sorted list of (hash, node)
import bisect, hashlib

class Ring:
    def __init__(self, nodes, replicas=150):        # replicas = virtual nodes
        self.ring = sorted(
            (self._h(f"{n}:{i}"), n) for n in nodes for i in range(replicas))

    def _h(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def node_for(self, key):
        i = bisect.bisect(self.ring, (self._h(key),))
        return self.ring[i % len(self.ring)][1]   # the next one on the ring
```

> **Card** · **When:** designing indexes, caches or distributing data across nodes ·
> **Pattern:** virtual nodes so the distribution is even with few physical nodes ·
> **Anti-pattern:** `hash(key) % N` to distribute: adding a node remaps **everything** ·
> **Limits:** a bloom filter doesn't support deletes; a hash map degrades to O(n) with collisions ·
> **How it fails:** hotspots when the partitioning key isn't uniform (one huge tenant) ·
> **Decision:** LSM if the bottleneck is writes, B-tree if it's reads and updates ·
> **Trade-off:** memory vs access speed, and writes vs reads (LSM vs B-tree) ·
> **Related:** indexes, sharding, caching `[04, 09]`

---

## Concurrency vs parallelism

They are not the same thing, and confusing them in an interview is a red flag.

- **Concurrency** = managing several tasks *in progress* at the same time (they can interleave on a single core).
  It's a model of program *structure*.
- **Parallelism** = executing several things *simultaneously* on several cores. It's a model of *execution*.

> "Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at
> once." — Rob Pike

A Node.js server is **concurrent but not parallel** (a single JS thread). It handles 10,000 connections
because it spends almost all of its time waiting on I/O, not computing.

**The three models you'll run into:**

1. **Thread per request** (traditional Java, Rails, PHP-FPM). Each request occupies an OS thread. Simple to
   reason about; each thread costs ~1 MB of stack and context switches are expensive. Ceiling: thousands, not hundreds of thousands.
2. **Event loop / async I/O** (Node, asyncio, nginx). One thread, one event queue. Scales to tens of
   thousands of connections with little RAM. **The price: if you block the loop, you kill the whole server.**
3. **Green threads / coroutines** (Go, Java 21+ virtual threads, Erlang). The runtime multiplexes millions of
   lightweight "threads" over a few OS threads. You write sequential code and get event-loop scaling.
   **This is the model that has won.**

> **Card** · **When:** choosing a stack and sizing workers ·
> **Pattern:** I/O-bound → concurrency; CPU-bound → real parallelism (processes) ·
> **Anti-pattern:** "adding threads" to speed up a computation in Python (GIL) ·
> **Limits:** the event loop is a single core; thread-per-request has a memory ceiling ·
> **How it fails:** a `bcrypt` or a 50 MB `json.loads` inside the event loop freezes **all** connections ·
> **Decision:** if your workload is waiting on the DB and on APIs (95% of backend), concurrency is enough ·
> **Trade-off:** ease of reasoning (threads) vs scale with little RAM (event loop) ·
> **Related:** async/await, connection pools, backpressure `[09]`

---

## Concurrency patterns

The four that show up again and again in backend, and that are implemented the same way in any language.

**1. Worker pool** — N workers consume from a queue. It's **the default pattern** for limiting
concurrency: you process quickly without opening 10,000 connections at once.

```python
import asyncio

async def worker_pool(tasks, job, n=10):
    queue = asyncio.Queue()
    for t in tasks:
        queue.put_nowait(t)

    async def worker():
        while not queue.empty():
            await job(await queue.get())

    await asyncio.gather(*[worker() for _ in range(n)])   # exactly n in flight
```

**2. Producer-consumer with a bounded queue** — the producer blocks if the queue is full. It's
**backpressure** implemented in three lines: `asyncio.Queue(maxsize=100)`.

**3. Fan-out / fan-in** — you launch N independent tasks in parallel and wait for all of them.

```python
user, orders, balance = await asyncio.gather(
    get_user(uid), get_orders(uid), get_balance(uid))   # 100ms instead of 300ms
```

**4. Pipeline** — stages chained together by queues, each with its own concurrency. It lets the slow stage
have more workers than the fast one.

> **Card** · **When:** whenever you process a collection against external resources ·
> **Pattern:** **bounded** concurrency (semaphore or pool), never unbounded ·
> **Anti-pattern:** `gather` over 10,000 items: you open 10,000 connections and take down the DB ·
> **Limits:** useful parallelism is set by the slowest resource, not by the number of workers ·
> **How it fails:** without a bounded queue, a fast producer fills memory until OOM ·
> **Decision:** worker pool if the tasks are homogeneous; pipeline if they have stages with different costs ·
> **Trade-off:** more workers = more throughput until saturation, and then less (contention) ·
> **Related:** backpressure, connection pooling, queues `[08, 09]`

---

## Async / await

Syntactic sugar over "register a continuation and hand control back".

```python
# This is NOT concurrent: sequential await = waiting for one after the other
a = await fetch_user()         # 100ms
b = await fetch_orders()       # 100ms  -> total 200ms

# This IS: you launch both and wait for them together
a, b = await asyncio.gather(fetch_user(), fetch_orders())   # total 100ms

# And this is the right way when there are many: bounded with a semaphore
sem = asyncio.Semaphore(10)
async def limited(coro):
    async with sem:
        return await coro
results = await asyncio.gather(*(limited(fetch(i)) for i in ids))
```

**The four mistakes you see in production:**

1. **Blocking the event loop** with heavy synchronous work. Fix: `run_in_executor` / `worker_threads`.
2. **Function color / contagious async.** An async function can only be called from async code; mixing the
   two produces ugly wrappers and subtle bugs.
3. **Fire-and-forget without a reference.** If you don't keep a reference to the task, the GC can kill it
   halfway through and the exception is silently lost.
4. **No concurrency limit** (see above).

> **Card** · **When:** every modern I/O-bound backend ·
> **Pattern:** `gather` for independent calls + a semaphore to bound them ·
> **Anti-pattern:** `time.sleep()`, `requests.get()` or a bcrypt hash inside a coroutine ·
> **Limits:** it doesn't speed up CPU work; a single thread is still a single core ·
> **How it fails:** one blocking task makes **all** requests suffer, not just its own ·
> **Decision:** CPU-intensive work → executor or separate process; never on the loop ·
> **Trade-off:** performance vs debugging complexity (async stack traces are worse) ·
> **Related:** concurrency patterns, GIL, backpressure `[09]`

---

## Threads vs processes

| | Thread | Process |
|---|---|---|
| Memory | shared | isolated |
| Cost to create | low (~µs) | high (~ms) |
| Communication | shared variables (needs locks) | IPC, pipes, sockets (serialization) |
| A crash | kills the whole process | isolated |
| Real parallelism in Python | **no** (GIL) | yes |

**Python's GIL** allows only one bytecode instruction at a time per process. Threads in Python are useful
for I/O-bound work (the GIL is released during I/O), **never** for CPU-bound work. (Python 3.13+ has an
experimental GIL-free build — *free-threading* — which in 2026 is still not the production default.)

**Typical production model:** N processes (one per core) × one event loop inside each. That's
literally what `gunicorn -k uvicorn.workers.UvicornWorker -w 4` does.

> **Card** · **When:** sizing the application server ·
> **Pattern:** processes = `available cores`; inside each, async or threads depending on the language ·
> **Anti-pattern:** 32 workers in a container with 1 CPU: all you add is context switching ·
> **Limits:** each process duplicates the app's base memory; each thread costs its stack ·
> **How it fails:** shared memory without a lock → race condition; too many processes → OOMKilled ·
> **Decision:** CPU-bound in Python → `multiprocessing`; I/O-bound → async ·
> **Trade-off:** isolation (processes) vs communication and memory cost ·
> **Related:** containers and resource limits `[13]`

---

## Memory management

- **Stack:** fast, LIFO, freed automatically. Limited size (hence the stack overflow from recursion).
- **Heap:** dynamic, managed by the allocator or the GC. Fragmentation and allocation cost live here.

**Garbage collection** saves you from memory bugs and charges you in **pauses**. Modern GCs (G1, ZGC, Go's
generational one) aim for sub-millisecond pauses, but under memory pressure your API's p99
shoots up. **If your latency has unexplained periodic spikes, suspect the GC.**

**Memory leaks with a GC** are references you never let go of: caches with no size limit or TTL, listeners
that are never unregistered, closures that capture giant objects, connections that are never closed.

> **Card** · **When:** debugging steadily growing memory usage or periodic latency spikes ·
> **Pattern:** every in-memory cache gets a **maximum size and a TTL** ·
> **Anti-pattern:** a global `dict` that accumulates entries per request "to speed things up" ·
> **Limits:** the container has a hard limit; exceeding it means instant death, not degradation ·
> **How it fails:** OOMKilled and a restart loop; or GC thrashing (the app is "alive" but makes no progress) ·
> **Decision:** if the size of what you process is unbounded, streaming is mandatory ·
> **Trade-off:** in-memory caching is the fastest option and the one that scales worst horizontally ·
> **Related:** caching, container limits, backpressure `[09, 13]`

---

## Error handling

Almost the entire difference between a junior and a senior lies here.

| Type | Example | What you do |
|---|---|---|
| Expected / business | insufficient balance, duplicate email | 4xx with a clear contract, **don't** log it as an error |
| Transient | network timeout, 503 from the provider | **retry with backoff** |
| Permanent | invalid payload, 401 | fail fast, don't retry |
| Programming | null pointer, index out of range | log with the stack trace, alert, fix it |
| Catastrophic | DB down, disk full | circuit breaker, degrade, alert |

```python
class BusinessError(Exception):       # -> 4xx, expected, no alert
    code = "generic"

class InsufficientFunds(BusinessError):
    code = "insufficient_funds"

class TransientError(Exception):      # -> retryable
    pass

try:
    charge(order)
except InsufficientFunds:
    raise                                            # propagates as is; the edge translates it to 409
except TimeoutError as e:
    raise TransientError(f"timeout charging order {order.id}") from e   # context + cause
```

**Principles:** fail fast in development, degrade gracefully in production · **never an empty `catch`**
(a silently swallowed error is the worst bug: the system lies about its own state) · wrap by adding
context, don't swallow · idempotency and errors go together: if you retry, the transient error must not
duplicate the effect.

> **Card** · **When:** at every system boundary ·
> **Pattern:** an exception hierarchy that distinguishes business / transient / programming errors ·
> **Anti-pattern:** `except Exception: pass`, and returning 200 with `{"error": ...}` inside ·
> **Limits:** you can't tell a "never arrived" timeout from an "arrived and I never saw the response" one ·
> **How it fails:** retrying a permanent error multiplies the load without fixing anything ·
> **Decision:** is it retryable? Only if it's transient **and** the operation is idempotent ·
> **Trade-off:** errors as values (explicit, verbose) vs exceptions (clean, easy to ignore) ·
> **Related:** retries, idempotency, error contracts `[03, 08, 10]`

---

## Networking basics

The details are in `[02]`. The bare minimum so you don't get caught out:

- **The mental model:** DNS resolves name → IP · TCP establishes the connection · TLS negotiates encryption ·
  HTTP carries the message.
- **TCP vs UDP:** TCP guarantees ordering and delivery (at the cost of handshakes and retransmission); UDP
  guarantees nothing. HTTP/3 runs over QUIC, which is UDP with reliability on top.
- **Sockets and file descriptors:** every open connection is an FD. The `ulimit -n` limit is the real cause
  of a huge number of "too many open files" errors under load.
- **Latency vs throughput:** you can't fix latency with more bandwidth — only by being closer
  (CDN) or by talking less (batching).

> **Card** · **When:** debugging any failure that crosses the network ·
> **Pattern:** persistent connections and pooling instead of opening one per operation ·
> **Anti-pattern:** opening a new DB connection on every request ·
> **Limits:** file descriptors, ephemeral ports (~28,000), and the 60s `TIME_WAIT` ·
> **How it fails:** "too many open files" or "cannot assign requested address" under load ·
> **Decision:** if you open and close a lot, pool; if the destination is far away, cache at the edge ·
> **Trade-off:** persistent connections save handshakes and consume idle FDs ·
> **Related:** connection pooling, TCP handshake `[02, 04, 09]`

---

## Paradigms and patterns

**Paradigms:** OOP (encapsulation, polymorphism; dangerous once inheritance grows — **composition
over inheritance**) · functional (pure functions and immutability: it wins at concurrency because there is
no shared state) · procedural (sometimes a function that transforms data is all you need).

**Patterns you use every day** (the catalog is in `[05]`): Repository · Factory · Strategy · Adapter ·
Decorator/middleware · Observer/pub-sub · Singleton (the most abused: a disguised global that ruins
your tests).

**The most expensive anti-pattern:** *premature abstraction*. Three layers of interfaces with a single
implementation each isn't clean architecture, it's debt. **The rule of three:** abstract when the third
case shows up, not the first.

> **Card** · **When:** structuring code that is going to change ·
> **Pattern:** composition over inheritance; immutability by default ·
> **Anti-pattern:** abstracting with a single use case; 6-level inheritance hierarchies ·
> **Limits:** every abstraction costs a mental jump when reading the code ·
> **How it fails:** "flexible" code that nobody understands ends up being rewritten ·
> **Decision:** are there three real cases? Then abstract ·
> **Trade-off:** future flexibility vs readability today ·
> **Related:** SOLID, design patterns, DI `[05]`

---

## How to test all of this

The fundamentals have their own testing strategy, different from that of an API (`[11]`).

**Algorithms and data structures → property-based testing.** Instead of examples, you declare invariants and the
library generates hundreds of cases and shrinks the counterexample down to the minimum.

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs):
    assert sort(sort(xs)) == sort(xs)

@given(st.text())
def test_serialize_round_trip(s):
    assert deserialize(serialize(s)) == s      # finds the weird unicode you didn't think of
```

**Concurrency → forced determinism.** Race conditions don't reproduce with a normal test.
What works: inject the clock and the randomness (never call `now()` or `random()` directly), run
the operation N times in parallel and assert on the **final state**, and use the language's detectors
(`-race` in Go, ThreadSanitizer).

```python
def test_stock_is_never_oversold():
    with ThreadPoolExecutor(max_workers=50) as ex:
        results = list(ex.map(lambda _: buy(product_id=1), range(50)))
    assert sum(results) == 10          # there were only 10 units
    assert stock(1) == 0               # and never negative
```

**Performance → a benchmark with a threshold in CI**, not "it seems fast". **Memory → soak test**: run it
for an hour and check that memory doesn't grow monotonically.

> **Card** · **When:** in code with strong invariants or concurrency ·
> **Pattern:** property-based for pure logic; parallel execution + assertion on the final state for concurrency ·
> **Anti-pattern:** a `sleep(0.1)` to "synchronize" the test — guaranteed flakiness ·
> **Limits:** a passing test doesn't prove the absence of race conditions, only that none showed up ·
> **How it fails:** tests that pass locally and fail in CI (a different machine, a different number of cores) ·
> **Decision:** if the bug would be silent and would corrupt data, invest in property-based testing ·
> **Trade-off:** concurrency tests are slow and non-deterministic: keep them apart from the fast suite ·
> **Related:** property-based testing, flaky tests, load testing `[11]`

---

## Interview questions and trade-offs

**Q: What's the difference between concurrency and parallelism?**
Concurrency is structure (several tasks in progress, interleaved); parallelism is simultaneous execution
on several cores. *Signal:* you bring up the Node example — concurrent with a single thread — and explain
that concurrency is what saves you in I/O-bound workloads, which are 95% of backend.

**Q: Your API has p99 latency spikes every few minutes. Where do you start?**
GC pauses, synchronized cache expiration, a cron job competing for resources, an exhausted pool, or
container CPU throttling. *Signal:* you mention that you look at p99 and not the average, and that the
first step is correlating the spike with GC, pool and throttling metrics.

**Q: Why not use threads in Python to speed up a heavy computation?**
The GIL. For CPU-bound work you need processes. *Signal:* you know that threads do help for I/O-bound work
because the GIL is released during I/O, and you mention the free-threading build as the future direction.

**Q: How do you avoid a deadlock?**
A global lock acquisition order, timeouts, short transactions and a smaller lock scope.
*Signal:* you mention that in practice the ones that bite you are in the database, that Postgres
detects them and kills a victim, and that **your code must retry that transaction**.

**Q: How do you test that there's no race condition in your counter?**
You run N operations in parallel and assert on the final state, with a race detector if the language
has one. *Signal:* you acknowledge that a green test doesn't prove the absence of races, and that the robust
fix is a design one (an atomic operation in the DB), not a testing one.

**Core trade-off of this box:** *simplicity vs control*. An event loop scales further with less RAM but
forces you to never block; thread-per-request is trivial to debug but has a ceiling. Go and Java 21
try to give you both. Choosing wrong here shapes the entire architecture of the service.

---

## Sources

- Rob Pike, *Concurrency is not Parallelism* — the canonical distinction.
- Jeff Dean, *Latency Numbers Every Programmer Should Know* — origin of the latency table.
- Python docs: [GIL](https://docs.python.org/3/glossary.html#term-global-interpreter-lock) ·
  [PEP 703 free-threading](https://peps.python.org/pep-0703/)
- [Hypothesis](https://hypothesis.readthedocs.io/) — property-based testing in Python.
