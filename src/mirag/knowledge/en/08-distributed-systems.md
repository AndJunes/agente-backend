# 08 · Distributed Systems

> A distributed system is one in which the failure of a computer you didn't even know existed can render
> your own computer unusable (Lamport). Everything in this box exists because **the network fails, messages
> get duplicated and ordering is not guaranteed.**


**Covers from the syllabus:** `concepts` · `messaging` · `events` · `patterns` · `reliability` · `idempotency` · `implementations` · `failure_modes` · `tradeoffs`

---

## The fallacies of distributed computing

The eight false assumptions everyone makes at first:
the network is reliable · latency is zero · bandwidth is infinite · the network is secure · topology doesn't
change · there is one administrator · transport cost is zero · the network is homogeneous.

**Every pattern in this box is the answer to one of these fallacies.**

> **Card** · **When:** designing anything that crosses the network ·
> **Pattern:** treat failure, latency and duplicates as the normal state, not the exception ·
> **Anti-pattern:** treating a remote call like a function call ·
> **Limits:** from the outside you cannot tell "slow" from "down" ·
> **How it fails:** an ambiguous timeout: you don't know whether the operation ran ·
> **Decision:** everything remote needs a timeout, bounded retries and idempotency ·
> **Trade-off:** local guarantees (ACID) are extremely expensive in a distributed setting ·
> **Related:** timeouts, idempotency `[10]`

---

## CAP, PACELC and consistency

**CAP:** during a **network partition** (P), you choose between **consistency** (C) and **availability** (A).
It is not "pick 2 of 3": partitions happen, so in practice you choose between **CP** and **AP**.

- **CP** — when in doubt, refuse the write. Banks, inventory, bookings. (Postgres with synchronous replication,
  etcd, ZooKeeper.)
- **AP** — keep accepting writes and reconcile later. Shopping carts, feeds, counters, DNS.
  (Cassandra, DynamoDB in eventual mode.)

**PACELC** completes the idea: *if Partition then A or C, Else Latency or Consistency*. In other words, **even
without a partition** you choose between latency and consistency. It is the trade-off you live with every day with read replicas.

**The consistency spectrum:**
- **Strong / linearizable:** everyone sees the latest write. Expensive, requires coordination.
- **Sequential / causal:** causal order is respected, there is no global clock.
- **Read-your-writes:** at least *you* see what you just wrote. **The bare minimum a user expects.**
- **Monotonic reads:** you never see time go backwards.
- **Eventual:** if you stop writing, it converges. It doesn't say when.

**Consensus** (Raft, Paxos): how a group of nodes agrees on a value despite failures. You need a **quorum**
(majority: `N/2 + 1`), which is why clusters have odd sizes (3, 5). Raft is what gets used today (etcd, Consul,
CockroachDB) because it is understandable. **What you should be able to say:** consensus is expensive (round trips between
nodes), so it is used for metadata and coordination, not for the critical path of every request.

> **Card** · **When:** choosing an engine and a replication model ·
> **Pattern:** strong consistency where money or stock is involved; eventual everywhere else ·
> **Anti-pattern:** "we picked 2 of 3" — partitions happen, you only choose C or A ·
> **Limits:** PACELC: even **without** a partition you choose between latency and consistency ·
> **How it fails:** the user writes, reads from a replica and doesn't see their own change ·
> **Decision:** read-your-writes is the minimum a user expects ·
> **Trade-off:** coordination (correct, slow) vs availability (fast, reconcile later) ·
> **Related:** replication, consensus `[04]`

---

## Message queues and brokers

**Why a queue:** decouple in time (the consumer can be down), absorb spikes
(buffer), retry without blocking the user, and parallelise work.

| | **Kafka** | **RabbitMQ** | **SQS / Pub-Sub** |
|---|---|---|---|
| Model | **partitioned, persistent log** | broker with queues and exchanges | managed service |
| Retention | by time/size; **can be re-read** | deleted on consumption (ack) | days |
| Ordering | **guaranteed within a partition** | per queue (lost with multiple consumers) | optional FIFO |
| Throughput | extremely high | high | high, elastic |
| Routing | the consumer picks topic/partition | **exchanges: direct, topic, fanout, headers** | basic |
| Strong at | event streaming, replay, multiple independent consumers | task queues, complex routing, priorities | operational simplicity |

**Kafka concepts that come up in interviews:**
- **Partition** = the unit of parallelism and of ordering. Order is only guaranteed **within** a partition,
  which is why the **partition key** (usually `user_id`, `order_id`) decides which events are ordered together.
- **Consumer group:** each partition is consumed by **a single** member of the group. More consumers than
  partitions = idle consumers. **Your maximum parallelism is the number of partitions.**
- **Offset:** the read pointer. Committing it before processing = at-most-once (you lose messages);
  after = at-least-once (you duplicate). **Choose after, and make yourself idempotent.**
- **Consumer lag:** the number one health metric of a consumer. If it keeps growing, you can't keep up.

> **Card** · **When:** decoupling in time, absorbing spikes, parallelising ·
> **Pattern:** a partition key that groups whatever must stay ordered (`order_id`) ·
> **Anti-pattern:** adding consumers beyond the number of partitions (they sit idle) ·
> **Limits:** order is **only** guaranteed within a partition ·
> **How it fails:** consumer lag grows and nobody watches it until there are hours of delay ·
> **Decision:** Kafka for streaming and replay; RabbitMQ for task queues with routing ·
> **Trade-off:** parallelism vs ordering — they are directly opposed ·
> **Related:** DLQ, consumer lag, backpressure `[09, 12]`

---

## Delivery semantics

| Guarantee | What it means | Reality |
|---|---|---|
| **At-most-once** | 0 or 1 times | you lose messages; almost never acceptable |
| **At-least-once** | 1 or more times | **the industry standard**; duplicates guaranteed |
| **Exactly-once** | exactly 1 | **impossible end to end** in the general case |

**"Exactly-once" only exists inside a system with transactions** (Kafka transactions between Kafka
topics). As soon as there is an external side effect (charging a card, sending an email, calling an API), the only thing achievable is
**at-least-once + idempotent processing**, which produces an *effectively* unique result.

**This is a very common trick question.** The right answer is: *"exactly-once delivery doesn't exist;
exactly-once processing is achieved with at-least-once plus idempotency."*

> **Card** · **When:** defining the guarantees of any consumer ·
> **Pattern:** at-least-once + idempotent processing = *effectively* once ·
> **Anti-pattern:** promising end-to-end exactly-once ·
> **Limits:** exactly-once only exists inside a transactional system (Kafka↔Kafka) ·
> **How it fails:** committing the offset **before** processing silently loses messages ·
> **Decision:** commit after processing and make yourself idempotent ·
> **Trade-off:** losing messages vs duplicating them ·
> **Related:** idempotency, outbox `[03]`

---

## Idempotency (the pillar of everything)

Processing the same message twice must produce the same final state.

**Strategies, from best to worst:**
1. **Naturally idempotent operations.** `SET status = 'paid'` is; `balance = balance + 10` is not.
   Redesigning the operation is always better than adding infrastructure.
2. **Deduplication table (inbox pattern).** `INSERT INTO processed(message_id) ON CONFLICT DO NOTHING`
   **in the same transaction** as the effect. If the insert adds no row, it was already processed.
3. **Conditional update / version.** `UPDATE ... WHERE version = $1`.
4. **Upsert on a natural key.** `ON CONFLICT (order_id) DO UPDATE`.

**The detail that makes it correct: the deduplication and the effect must be in the same transaction.**
If you mark "processed" in Redis and then write to Postgres, a crash in between leaves you inconsistent.

> **Card** · **When:** in every consumer and every endpoint that mutates ·
> **Pattern:** redesign the operation to be naturally idempotent before adding infrastructure ·
> **Anti-pattern:** marking "processed" in Redis and writing the effect to Postgres ·
> **Limits:** it only works if dedupe and effect share a transaction ·
> **How it fails:** a crash between the two writes leaves the system inconsistent ·
> **Decision:** `SET status='paid'` is idempotent; `balance = balance + 10` is not ·
> **Trade-off:** one extra write in exchange for safe retries ·
> **Related:** inbox pattern, idempotency keys `[03, 07]`

---

## Outbox pattern (the dual-write problem)

**The problem:** you want to save the order in the DB **and** publish `OrderCreated` to the queue. They are two
systems: there is no shared transaction.

- If you publish first and the DB fails → an event for an order that doesn't exist.
- If you save first and the broker fails → an order with no event; nobody finds out.
- And distributed commits (2PC/XA) are slow, fragile and avoided nowadays.

**The solution — turn two writes into one:**

```sql
BEGIN;
  INSERT INTO orders (...) VALUES (...);
  INSERT INTO outbox (id, type, payload, created_at)
       VALUES (gen_random_uuid(), 'OrderCreated', '{...}', now());
COMMIT;                      -- atomic: either both are there, or neither is
```

Afterwards, a **relay** reads the `outbox` table and publishes to the broker (marking or deleting what was sent). If the relay
fails, it retries; if it publishes twice, the consumer deduplicates (at-least-once again).

**How the outbox is read:**
- **Polling** with `SELECT ... FOR UPDATE SKIP LOCKED` — simple, good enough for most cases.
- **CDC (Change Data Capture)** reading the WAL with Debezium — lower latency and no polling load, but
  it is new infrastructure to operate.

**Inbox pattern** is the mirror image on the consumer side: you store the received `message_id` in the same transaction
as the effect, in order to deduplicate.

**Production details:** archive or delete published events (the table grows fast), and watch the relay
lag as a first-class metric.

> **Card** · **When:** every time you save state **and** publish an event ·
> **Pattern:** insert the event into a table within the same transaction; a relay publishes it ·
> **Anti-pattern:** publishing to the broker before the commit, or using 2PC ·
> **Limits:** the relay can publish twice → the consumer must deduplicate ·
> **How it fails:** the outbox table grows without archiving and the relay lag goes unnoticed ·
> **Decision:** polling with `SKIP LOCKED` to start with; CDC if you need lower latency ·
> **Trade-off:** polling latency vs the operational complexity of CDC ·
> **Related:** transactions, idempotency, events `[04, 07]`

---

## Sagas (distributed transactions)

When a business operation spans several services and you can't have a global ACID transaction,
you split it into local steps, **each with its own compensation**.

```
Create order → Reserve stock → Charge → Schedule shipping
    ↓ failure in "Charge"
Compensate: release stock  →  cancel order
```

**Two styles:**
- **Choreography:** each service listens to events and reacts. No coordinator, low coupling, but
  **nobody knows the full flow** — to understand it you have to read five repos. It becomes unmanageable
  beyond 4-5 steps.
- **Orchestration:** an orchestrator drives the flow explicitly. The flow is readable and debuggable in one place; the
  price is a central component that must be durable (this is where Temporal, AWS Step Functions, or the
  Workflow DevKit come in).

**What you really need to understand:** a compensation **is not a rollback**. It doesn't erase what happened: it applies
an inverse business action (a refund, not an "un-charge"). And some steps **cannot be
compensated** (a sent email, an SMS) — those go at the end, or are designed to be reversible.

**Also:** sagas expose visible intermediate states (someone may see the order as "reserved but not
paid"), so the UI and the model must account for them.

> **Card** · **When:** a business operation spans several services ·
> **Pattern:** orchestration with a durable coordinator if there are more than 3-4 steps ·
> **Anti-pattern:** choreography across 6 services: nobody can explain the full flow ·
> **Limits:** a compensation **is not a rollback**: some steps cannot be compensated ·
> **How it fails:** a visible intermediate state (reserved but not paid) that the UI doesn't handle ·
> **Decision:** put the irreversible steps last ·
> **Trade-off:** autonomy (choreography) vs traceability (orchestration) ·
> **Related:** service boundaries, state machines `[05, 17]`

---

## Retries, backoff and their dangers

```python
for attempt in range(max_attempts):
    try:
        return call()
    except TransientError:
        if attempt == max_attempts - 1:
            raise
        wait = min(base * (2 ** attempt), cap)
        time.sleep(wait * (0.5 + random.random() / 2))   # JITTER: essential
```

- **Only retry what is transient.** A 400 or a 401 won't get better by retrying; a 429/503/timeout will.
- **Exponential backoff + jitter.** Without jitter, a thousand clients that fail at the same time retry at the same time and
  cause a **retry storm** that finishes off the service that was recovering.
- **Retry budget.** Retrying at every layer multiplies: 3 levels × 3 retries = 27 calls.
  **Retry at a single level**, ideally the one closest to the failure, and cap the global retry ratio.
- **Honour `Retry-After`** when the server gives it to you.
- **Your timeout must always be shorter than your caller's**, or you'll keep retrying after the upstream client has already given up.
- **Combine with a circuit breaker** (`10-reliability.md`): if the target is down, stop trying.

> **Card** · **When:** every remote call that can fail transiently ·
> **Pattern:** exponential backoff **with jitter** and a global retry budget ·
> **Anti-pattern:** retrying at three layers: 3×3×3 = 27 calls per request ·
> **Limits:** retrying is only safe if the operation is idempotent ·
> **How it fails:** **retry storm** — everyone retries at once and finishes off the service that was recovering ·
> **Decision:** retry at a single layer, the one closest to the failure ·
> **Trade-off:** success rate vs load on an already degraded system ·
> **Related:** circuit breakers, timeouts `[10]`

---

## Dead-letter queues

Messages that fail repeatedly go to a separate queue instead of blocking consumption.

- **Why it is mandatory:** without a DLQ, a single *poison message* that always fails
  blocks the partition or the whole queue, and the lag grows forever.
- **What to store:** the original message, the error, the number of attempts and the stack trace. Without that, the DLQ is a
  black hole.
- **Operations:** alert when messages arrive, and have tooling to inspect and **reprocess** them after fixing
  the bug. A DLQ nobody looks at is accumulated garbage that costs money.

> **Card** · **When:** mandatory in every consumer ·
> **Pattern:** DLQ with the original message, error, attempts and stack trace; alert on the first arrival ·
> **Anti-pattern:** a DLQ nobody looks at ·
> **Limits:** when reprocessed, that message arrives out of order ·
> **How it fails:** without a DLQ, a **poison message** blocks the partition and the lag grows endlessly ·
> **Decision:** N retries and then to the DLQ; never infinite inline retries ·
> **Trade-off:** discarding (you move forward) vs blocking (you don't lose ordering) ·
> **Related:** consumer lag, alerts `[12]`

---

## Distributed locks

**First: avoid them.** Most cases of "I need a lock" are better solved with an atomic operation in the
database, a `UNIQUE` constraint, partitioning by key (which serialises naturally) or idempotency.

If you really need one:
- **Redis:** `SET lock value NX PX 30000`, and release it **only if the value is yours** (Lua script). Redlock is
  disputed: under GC pauses or skewed clocks it can hand out two holders at the same time.
- **Postgres advisory locks** — `pg_advisory_lock`: correct and transactional, no new infrastructure.
- **etcd / ZooKeeper** — real consensus, the right option if you need strong guarantees.

**The uncomfortable truth:** a distributed lock with a TTL **does not guarantee mutual exclusion** if the holder freezes
(GC pause) for longer than the TTL. For strict correctness you need **fencing tokens**: an increasing number that the
protected resource checks, rejecting it if it is stale.

> **Card** · **When:** last resort, when there is no atomic alternative ·
> **Pattern:** first try a `UNIQUE`, an atomic update or partitioning by key ·
> **Anti-pattern:** relying on a TTL lock to guarantee correctness ·
> **Limits:** if the holder freezes (GC) for longer than the TTL, **there are two holders at once** ·
> **How it fails:** two processes believe they hold the lock and both write ·
> **Decision:** for strict correctness you need **fencing tokens** ·
> **Trade-off:** simplicity (Redis) vs real correctness (etcd/Postgres with fencing) ·
> **Related:** database locks, idempotency `[04]`

---

## Eventual consistency in practice

- **Read-your-writes:** after writing, read from the primary for a few seconds, or store the LSN/version
  and wait for the replica to catch up.
- **Consistency in the UI:** optimistic update (render the expected result and correct it if it fails) or an honest
  "processing" state. The worst thing is to lie and then contradict yourself.
- **CRDTs:** data structures that converge without coordination (counters, sets). The foundation of collaborative editing.
- **Vector clocks / Lamport timestamps:** to establish causality without a global clock. **Wall clocks
  are not reliable across machines** (drift, NTP, backwards jumps): never order distributed events
  by `now()`.

> **Card** · **When:** with replicas, caches or projections ·
> **Pattern:** per-session read-your-writes; optimistic UI with visible correction ·
> **Anti-pattern:** ordering distributed events by `now()` ·
> **Limits:** "eventual" doesn't say **when**; measure the lag and set a target for it ·
> **How it fails:** the user saves, reloads and sees stale data ·
> **Decision:** for causality use versions or vector clocks, never timestamps ·
> **Trade-off:** low latency (reading replicas) vs always seeing the latest ·
> **Related:** CAP, replication, CQRS `[04, 05]`

---

## Events: schema, versioning and contract

**A published event is a public API.** The difference is that almost nobody versions it, which is why
event-driven systems break silently.

```json
{
  "event_id": "01J8XZ...",              // unique and stable -> the consumer deduplicates with this
  "event_type": "order.paid",
  "event_version": 2,                    // version of the SCHEMA, not of the resource
  "occurred_at": "2026-09-15T04:12:33Z", // when it actually happened (not when it was published)
  "producer": "payments-service",
  "trace_id": "4bf92f...",               // propagates the tracing context [12]
  "tenant_id": "t_7",
  "resource": {"id": "ord_123", "version": 4},   // resource version -> detect out-of-order delivery
  "data": { "total_cents": 5000, "currency": "EUR" }
}
```

**The evolution rules**, the same as for a REST API (`[03]`):

- **Compatible:** adding an optional field, adding a new event type.
- **Breaking:** removing or renaming a field, changing a type, **changing the meaning**.
- For a breaking change: publish `v2` **in parallel** with `v1`, migrate the consumers, and retire `v1`
  once you can prove nobody consumes it.

**Name the event as a past fact** (`order.paid`, not `pay_order`): an event notifies something
that **already happened**, it doesn't command anything. If your "event" is a command, what you want is a command or a
synchronous call.

**Two payload styles:**

| | Notification | State transfer |
|---|---|---|
| Payload | minimal (just the id) | the relevant state |
| The consumer | calls you back for the details | doesn't need to call you |
| Coupling | low | high on the schema |
| Cost | more traffic and latency | data duplication |
| Risk | the resource has already changed by the time you query it | stale payload if it arrives late |

**Schema registry** (Avro/Protobuf with Confluent, or JSON Schema in your repo): validates at publish time that the
event meets the contract and blocks incompatible changes in CI. Without it, the contract only exists in the
head of whoever wrote it.

> **Card** · **When:** before publishing the first event ·
> **Pattern:** survival by design — `event_id`, schema version, resource version and `trace_id` ·
> **Anti-pattern:** publishing your database's internal model as an event ·
> **Limits:** once published, you cannot pull an event out of other people's consumption ·
> **How it fails:** a consumer assumes ordering and `paid` arrives before `created` ·
> **Decision:** include the resource version so the consumer can discard stale data ·
> **Trade-off:** rich payload (self-contained) vs minimal (decoupled from the schema) ·
> **Related:** API versioning, contract testing, tracing `[03, 11, 12]`

---

## Implementation: a correct producer and consumer

**Producer with an outbox** — the relay that turns two writes into one:

```python
SQL_PENDING = (
    "SELECT * FROM outbox WHERE published_at IS NULL "
    "ORDER BY created_at LIMIT 100 "
    "FOR UPDATE SKIP LOCKED"        # several relays grab different rows without blocking each other
)

async def relay_outbox():
    while True:
        async with uow.transaction() as tx:
            for e in await tx.execute(SQL_PENDING):
                await broker.publish(e.type, e.payload, key=e.partition_key)
                await tx.execute("UPDATE outbox SET published_at = now() WHERE id = $1", e.id)
        await asyncio.sleep(0.5)
```

**Idempotent consumer** — the inbox: deduplication and effect in the same transaction:

```python
async def consume(message):
    for attempt in range(3):
        try:
            async with uow.transaction() as tx:
                # if it was already there, nothing is inserted and it returns 0 rows -> already processed
                new = await tx.execute(
                    "INSERT INTO processed (event_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    message.event_id)
                if new.rowcount == 0:
                    return await message.ack()          # duplicate: ack and done

                await apply_effect(tx, message)         # SAME transaction as the dedupe
            return await message.ack()                  # ack AFTER processing
        except TransientError:
            await asyncio.sleep((2 ** attempt) * random.uniform(0.5, 1.5))   # backoff + jitter
        except Exception as e:
            await dlq.send(message, error=e, attempts=attempt + 1)   # poison -> DLQ
            return await message.ack()
```

**The five details that make it correct:** `SKIP LOCKED` allows several relays · the ack goes **after**
processing · dedupe and effect share a transaction · transient errors are retried with jitter ·
permanent ones go to the DLQ instead of blocking the partition forever.

> **Card** · **When:** the template for any queue consumer ·
> **Pattern:** dedupe + effect in one transaction; ack at the end; DLQ for poisoned messages ·
> **Anti-pattern:** `ack` on receipt "so the queue doesn't get blocked" — you lose messages ·
> **Limits:** the message can be redelivered even if the process did everything right (lost ack) ·
> **How it fails:** without `ON CONFLICT DO NOTHING`, two simultaneous deliveries apply the effect twice ·
> **Decision:** if the effect can't be idempotent, store the result and return it ·
> **Trade-off:** batch processing (throughput) vs one at a time (failure isolation) ·
> **Related:** outbox, DLQ, retries `[04]`

---

## Failure modes: a distributed system

| Failure | Symptom | Mitigation |
|---|---|---|
| **Ambiguous timeout** | you don't know whether it ran | idempotency + reconciliation `[07]` |
| **Network partition** | two halves operating separately | quorum, fencing |
| **Split-brain** | two primaries accepting writes | consensus (Raft), fencing tokens |
| **Duplicates** | effect applied twice | dedupe by `event_id` |
| **Out-of-order delivery** | `paid` before `created` | state-based logic + resource version |
| **Poison message** | lag growing, consumer stuck in a loop | DLQ after N attempts |
| **Retry storm** | the service can't manage to recover | backoff with jitter + circuit breaker `[10]` |
| **Consumer lag** | effects arrive hours late | alert on lag, scale consumers |
| **Clock skew** | events ordered incorrectly | never order by `now()` across machines |
| **Cascading failure** | everything goes down because of one slow service | timeouts, bulkheads, degradation `[10]` |
| **Stuck outbox** | nobody receives events and the DB looks fine | monitor the age of the oldest unpublished event |

**The common pattern:** distributed failures are **partial and silent**. Nothing returns an error;
the system simply stops agreeing with itself. That is why observability (`[12]`) is not
an extra in distributed architectures: it is the only way to know something is wrong.

> **Card** · **When:** setting up monitoring for a system with queues ·
> **Pattern:** alert on **consumer lag** and on the age of the oldest message, not just on errors ·
> **Anti-pattern:** taking "there are no errors in the logs" as proof that all is well ·
> **Limits:** you can't tell a slow consumer from a stopped one without looking at the lag ·
> **How it fails:** the system "works" but is two hours behind and nobody knows ·
> **Decision:** every queue needs an owner, a lag alert and a runbook ·
> **Trade-off:** more alerts vs late detection ·
> **Related:** observability, DLQ, SLOs `[10, 12]`

---

## Interview questions and trade-offs

**Q: Can exactly-once be guaranteed?**
Not for end-to-end delivery. You achieve at-least-once + idempotency in the consumer. *Signal:*
you explain that the problem is the lost ack: the producer doesn't know whether the message arrived, so it resends; and
that Kafka's "exactly-once" only applies within Kafka.

**Q: You save an order and publish an event. How do you guarantee that both happen or neither does?**
Outbox pattern: insert the event into a table within the same transaction, and a relay publishes it.
*Signal:* you mention why 2PC was ruled out (slow, fragile, blocks if the coordinator goes down) and that the relay
can duplicate, which puts the ball back in the court of consumer idempotency.

**Q: Kafka or RabbitMQ?**
Kafka for event streaming, replay and several independent consumers of the same stream; RabbitMQ for
task queues with routing and priorities. *Signal:* you mention that parallelism in Kafka is capped by
the number of partitions and that the partition key determines ordering, which is the real design decision.

**Q: A consumer has 4 million messages of lag. What do you do?**
First you measure whether it is a spike or a degradation; you check for poison messages, whether processing has become
slow (a new query, a slow external service), and whether you can scale consumers (capped by
partitions). *Signal:* you know that adding consumers beyond the number of partitions does nothing, and
you propose batching or parallel processing inside the consumer if you can't repartition.

**Q: What is write skew / how do you compensate a saga?**
(See also `04-databases.md`.) A compensation applies an inverse business action, not a technical
rollback. *Signal:* you point out the non-compensable steps and say they are placed at the end of the flow.

**Q: Why jitter in retries?**
Because without it, all the clients that failed at the same time retry at the same time and create a wave that prevents
the service from recovering. *Signal:* you mention the retry budget and the danger of retrying at
several layers at once.

**Core trade-off of this box:** *guarantees vs coordination*. Every strong guarantee (total ordering,
strict consistency, mutual exclusion) is paid for with coordination, and coordination costs latency and
availability. Senior design means **demanding strong guarantees only where the business truly
needs them** (money, stock) and accepting eventual consistency everywhere else.

---

## Sources

- *Designing Data-Intensive Applications* (Martin Kleppmann) — the reference for this box.
- [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html) and [Saga](https://microservices.io/patterns/data/saga.html) — Chris Richardson.
- [Outbox pattern: best practices 2026](https://www.sachith.co.uk/outbox-pattern-for-reliable-events-best-practices-in-2025-practical-guide-may-8-2026/)
- [Idempotency Patterns: Building Retry-Safe Distributed Systems](https://backendbytes.com/articles/idempotency-patterns-distributed-systems/)
- Martin Kleppmann, [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) — why Redlock does not guarantee mutual exclusion.
- [AWS Builders' Library — Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
