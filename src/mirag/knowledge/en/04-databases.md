# 04 · Databases

> The box where the most people stumble in senior interviews and where the most money is lost in production.
> Rule of thumb cited by almost every Postgres team: **80% of performance problems are missing indexes,
> 15% are badly designed queries and 5% are connection management.**


**Covers from the syllabus:** `concepts` · `modeling` · `queries` · `indexing` · `transactions` · `scaling` · `caching` · `implementations` · `failure_modes` · `tradeoffs`

---

## Relational vs NoSQL: how you actually choose

The question isn't "which one is better?" but **"what guarantees do I need and what access pattern do I have?"**

| You need | Choose |
|---|---|
| Multi-entity transactions, referential integrity, ad-hoc queries | **PostgreSQL** |
| Massive writes, horizontal scale, per-document schema | MongoDB, DynamoDB |
| Sub-ms latency, in-memory structures, TTL | **Redis** |
| Brutal write throughput, high availability, no joins | Cassandra (LSM) |
| Column analytics, aggregations over billions of rows | ClickHouse, BigQuery (columnar) |
| Full-text search, facets, relevance | Elasticsearch / OpenSearch |
| Vector similarity | pgvector, Qdrant, Pinecone (see `18-ai-backend.md`) |

**The senior stance in 2026: start with Postgres.** It does JSON (JSONB with GIN indexes), full-text search,
vectors (pgvector), queues (SKIP LOCKED), geospatial (PostGIS) and time series (TimescaleDB). Introducing
a second engine means introducing a consistency problem between two sources of truth. **Do it when the
access pattern genuinely demands it, not because it's trendy.**

> **Card** · **When:** when starting a service or when you notice the current engine doesn't fit ·
> **Pattern:** start with Postgres; add engines only when the access pattern demands it ·
> **Anti-pattern:** choosing NoSQL "to scale" with 10,000 users ·
> **Limits:** every extra engine is another source of truth to sync and operate ·
> **How it fails:** two stores holding the same data end up disagreeing, and nobody knows which one wins ·
> **Decision:** do you need multi-entity transactions and ad-hoc queries? Relational ·
> **Trade-off:** schema flexibility vs integrity guarantees ·
> **Related:** CAP, sharding, vector databases `[08, 18]`

---

## Data modeling

**Normalization** (1NF → 3NF): every piece of data lives in exactly one place. Avoids update anomalies.
**Denormalization**: you duplicate on purpose to avoid joins. You pay with consistency and with having to
update in several places.

**The rule:** *normalize until it hurts, denormalize until it works.* And when you denormalize, make sure there is
a single source of truth and everything else is derived (materialized view, computed field maintained by a trigger, projection
updated by events).

**Relationships:**
- **1:N** → foreign key on the N side. Trivial.
- **N:M** → join table (`users_roles`). Put the relationship's attributes there (`assigned_at`).
- **1:1** → usually it's the same table; split it only if there are huge columns or different permissions.
- **Hierarchies** → adjacency list (`parent_id`, simple, recursive queries with `WITH RECURSIVE`),
  materialized path, or nested sets. For shallow trees, adjacency list and you're done.

**Decisions that will haunt you for years:**
- **Primary keys:** auto-increment `BIGINT` (compact, ordered, but reveals volume and complicates
  sharding) vs **UUIDv4** (distributed but random → **fragments the B-tree index and wrecks write
  locality**) vs **UUIDv7/ULID** (time-ordered: the best of both). **In 2026, the
  default answer is UUIDv7.**
- **Soft delete** (`deleted_at`): keeps history but **pollutes every query** and breaks
  `UNIQUE` constraints. If you use it, do it with views or with a default filter in the ORM, and use partial indexes.
- **Money:** `NUMERIC`/`DECIMAL` or integer cents. **Never `FLOAT`.** `0.1 + 0.2 != 0.3`.
- **Time:** `TIMESTAMPTZ` always, store in UTC, convert at the edge. Storing `TIMESTAMP` without a time zone
  is a bug waiting for the next daylight saving change.
- **Enums:** native enum type (rigid: adding values requires a migration) vs lookup table (flexible,
  with an FK) vs `TEXT` with a `CHECK`. For values that change with the business, a table.

> **Card** · **When:** before the first migration; afterwards it's expensive ·
> **Pattern:** UUIDv7 as the key, `TIMESTAMPTZ` in UTC, money as integers or `DECIMAL` ·
> **Anti-pattern:** `FLOAT` for money, `TIMESTAMP` without a time zone, and UUIDv4 as PK (fragments the B-tree) ·
> **Limits:** soft delete pollutes every query and breaks `UNIQUE` constraints ·
> **How it fails:** `0.1 + 0.2 != 0.3` quietly throws the books off for months ·
> **Decision:** normalize until it hurts, denormalize until it works ·
> **Trade-off:** integrity (normalized) vs read speed (denormalized) ·
> **Related:** multi-tenancy, migrations `[17]`

---

## Indexes

**What an index is:** an ordered structure (usually a B-tree) that avoids reading the whole table. It speeds up
reads, **slows down writes** (every INSERT/UPDATE maintains all the indexes) and takes up disk.

**Types in PostgreSQL:**

| Type | What for |
|---|---|
| **B-tree** | 95% of cases: `=`, `<`, `>`, `BETWEEN`, `ORDER BY`, `LIKE 'abc%'` prefixes |
| **Hash** | equality only; rarely worth it |
| **GIN** | content "inside" something: JSONB, arrays, full-text search |
| **GiST** | geospatial, ranges, nearest neighbours |
| **BRIN** | huge **naturally ordered** tables (logs by date); tiny index |
| **Partial index** | `WHERE active = true` — smaller and faster |
| **Expression index** | `ON users (lower(email))` for case-insensitive lookups |
| **Covering / INCLUDE** | adds columns to the index to get an **index-only scan** |

**The rules you need to be able to state:**

1. **Leftmost prefix rule.** An index on `(a, b, c)` works for `WHERE a`, `WHERE a AND b`,
   `WHERE a AND b AND c` — **but not for `WHERE b`**. Column order is the key decision.
2. **Column order:** equality first, then range, then the `ORDER BY` columns. An index on
   `(status, created_at)` works for `WHERE status='x' ORDER BY created_at`; the other way round, it doesn't.
3. **Selectivity.** Indexing a boolean column with a 50/50 split is useless: the planner will prefer the scan.
   That's where a *partial* index does pay off.
4. **An unused index is pure cost.** `pg_stat_user_indexes` tells you which ones have `idx_scan = 0`.
5. **Functions kill indexes.** `WHERE DATE(created_at) = '2026-01-01'` doesn't use the index on `created_at`;
   `WHERE created_at >= '2026-01-01' AND created_at < '2026-01-02'` does. Same with `WHERE field + 0 = 5`
   or with a different type that forces an implicit cast.
6. **In production, `CREATE INDEX CONCURRENTLY`.** A plain `CREATE INDEX` **blocks writes** on the
   whole table. On large tables that's an outage.

**Reading a plan:**
```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```
Look for: `Seq Scan` on large tables (missing index), a big gap between estimated and actual `rows`
(stale statistics → `ANALYZE`), `Nested Loop` with many iterations, and `Sort` with
`external merge Disk` (raise `work_mem`).

> **Card** · **When:** with every filter, join or sort order you expose ·
> **Pattern:** column order = equality first, then range, then `ORDER BY` ·
> **Anti-pattern:** `WHERE DATE(created_at) = ...` — a function on the column defeats the index ·
> **Limits:** every index slows down writes and takes up disk ·
> **How it fails:** `CREATE INDEX` without `CONCURRENTLY` **blocks writes** on the whole table ·
> **Decision:** leftmost prefix rule: `(a,b,c)` doesn't work for `WHERE b` ·
> **Trade-off:** read speed vs write and storage cost ·
> **Related:** query optimization, pagination `[03, 09]`

---

## Transactions and ACID

- **Atomicity** — all or nothing.
- **Consistency** — invariants (constraints, FKs) hold before and after.
- **Isolation** — concurrent transactions don't step on each other (up to the level you choose).
- **Durability** — a confirmed commit = it survives a power cut (WAL + fsync).

### Isolation levels and their anomalies

| Level | Dirty read | Non-repeatable read | Phantom read | Write skew |
|---|---|---|---|---|
| Read Uncommitted | possible | possible | possible | possible |
| **Read Committed** (Postgres default) | no | possible | possible | possible |
| **Repeatable Read** (MySQL/InnoDB default) | no | no | no* | possible |
| **Serializable** | no | no | no | no |

- **Dirty read:** you read something that hasn't been committed. Postgres never allows it.
- **Non-repeatable read:** you read the same row twice within a transaction and it has changed.
- **Phantom read:** you repeat a range query and new rows show up.
- **Write skew:** two transactions read the same state, decide separately and together break an invariant.
  The canonical example: two on-call doctors sign off at the same time; each one reads "there are 2 on call", both
  leave, and the hospital is left with nobody. **No level below Serializable prevents it.**

\* In Postgres, Repeatable Read uses snapshot isolation and prevents classic phantoms, but **not** write skew.

**How it's solved in practice without paying for Serializable:**
- `SELECT ... FOR UPDATE` — a pessimistic lock on the rows you read.
- A `UNIQUE` or a `CHECK` that makes the invalid state impossible (let the DB enforce the invariant).
- **Optimistic locking**: a `version` column, and `UPDATE ... WHERE version = $1`; if it affects 0 rows, someone
  got there first → 409 to the client.

**Golden rules for transactions:**
- **Keep them short.** A transaction left open while you call an external API is how a connection pool gets exhausted
  and how never-ending locks show up.
- **Never do external I/O inside a transaction** (HTTP calls, sending emails). Use the
  **outbox pattern** (`08-distributed-systems.md`).
- **Consistent ordering** when touching several rows, so you don't cause deadlocks.

> **Card** · **When:** whenever two writes must happen together or not at all ·
> **Pattern:** short transactions; critical invariants as DB constraints ·
> **Anti-pattern:** calling an external API inside an open transaction ·
> **Limits:** Read Committed (the Postgres default) does **not** prevent write skew ·
> **How it fails:** two transactions read the same state and together break an invariant ·
> **Decision:** is a `UNIQUE` or a `CHECK` enough? Then you don't need Serializable ·
> **Trade-off:** strong isolation (correct, slow, more aborts) vs weak (fast, anomalies) ·
> **Related:** locks, outbox, sagas `[08]`

---

## Locks and deadlocks

- **Row locks** (`FOR UPDATE`, `FOR NO KEY UPDATE`) vs **table locks** (taken by DDL).
- **MVCC:** Postgres doesn't block reads. Each transaction sees a snapshot; **readers never block
  writers and vice versa**. The price is **vacuum**: the old versions (dead tuples) have to be
  cleaned up, and if autovacuum can't keep up the table swells (**bloat**) and queries degrade.
- **Deadlock:** Postgres detects it and kills one of the two transactions with an error. **Your application must
  retry** that transaction: it's not a DB bug, it's the expected behaviour.
- **The lock queue trap:** an `ALTER TABLE` waiting for a lock **blocks every query that arrives
  behind it**, even if those queries don't conflict with each other. That's why migrations run with a
  short `lock_timeout` and retries.
- **`SELECT ... FOR UPDATE SKIP LOCKED`:** how you implement a **job queue inside Postgres**
  without Redis or Kafka. Several workers grab different rows without blocking each other. Knowing this is a real plus.

> **Card** · **When:** with concurrent writes on the same rows ·
> **Pattern:** consistent acquisition order + `SELECT ... FOR UPDATE SKIP LOCKED` for queues ·
> **Anti-pattern:** an `ALTER TABLE` at peak time: it blocks everything that arrives behind it ·
> **Limits:** MVCC keeps readers and writers from blocking each other, and generates dead tuples in exchange ·
> **How it fails:** autovacuum can't keep up, the table swells (bloat) and everything degrades ·
> **Decision:** deadlocks are expected: **your application must retry the transaction** ·
> **Trade-off:** pessimistic lock (serializes, safe) vs optimistic (concurrent, with retries) ·
> **Related:** idempotency, queues in Postgres `[08]`

---

## Migrations

**The principle that governs everything: in production, the old code and the new code coexist for a few minutes (or days,
if you do canary). The migration must be compatible with both.**

**Expand / contract (the only safe pattern):**
1. **Expand:** add the new column as *nullable*, without touching the old one. Deploy code that writes to both.
2. **Backfill:** fill it in batches (`UPDATE ... WHERE id BETWEEN` in batches with pauses), never all at once.
3. **Migrate:** deploy code that reads from the new one.
4. **Contract:** once nobody uses the old one, drop it (in a separate deployment).

**Dangerous operations in Postgres (they lock):**
- Adding a column **with a non-volatile default** → since PG 11 it no longer rewrites the table (it used to). Even so,
  adding `NOT NULL` without a default on a table that has data fails.
- `ALTER COLUMN TYPE` → rewrites the whole table. With millions of rows, that's downtime.
- Adding an FK → takes a strong lock and validates everything. Do it in two steps: `NOT VALID` and then
  `VALIDATE CONSTRAINT` (which doesn't block writes).
- `CREATE INDEX` without `CONCURRENTLY`.

**Operational rules:** migrations versioned in the repo, idempotent, **always with a rollback thought through**
(even if it's "can't be done, we have to restore"), tested against a copy with production-sized data, and
separated from the code deployment so you can revert one without the other.

> **Card** · **When:** every schema change in production ·
> **Pattern:** expand/contract across separate deployments, with a batched backfill ·
> **Anti-pattern:** adding a column, migrating the data and dropping the old one in the same deployment ·
> **Limits:** during a rolling update **two versions of the code coexist** ·
> **How it fails:** `ALTER COLUMN TYPE` rewrites the whole table: downtime with millions of rows ·
> **Decision:** new FKs as `NOT VALID` and then `VALIDATE`, so you don't lock ·
> **Trade-off:** several coordinated deployments in exchange for zero downtime ·
> **Related:** deployment strategies, rollback `[14]`

---

## Replication, sharding and scaling

**Replication**
- **Synchronous:** the commit waits for the replica. Zero data loss, higher latency, and if the replica goes down
  you can end up blocking writes.
- **Asynchronous:** immediate commit, the replica trails behind (**replication lag**). It's the default.
- **The classic bug:** you write and immediately read from a replica → the user doesn't see their own change.
  Fixes: read from the primary after writing ("read-your-writes"), per-session stickiness for N seconds,
  or wait for the LSN.

**Read replicas**: they scale reads, not writes. And they aren't a backup (a `DELETE` replicates instantly).

**Partitioning (within one DB):** splitting a large table by range (date), list or hash. Huge
advantage: deleting old data is a `DROP PARTITION` (instant) instead of a massive `DELETE` that generates bloat.

**Sharding (across DBs):** spreading the data by a **shard key**. What you lose: cross-shard joins,
global transactions, global `UNIQUE` and aggregations. What you gain: write scaling.
- **Choosing the shard key is the most irreversible decision there is.** It must spread load evenly and align
  with your query pattern (usually `tenant_id` or `user_id`).
- **Hotspots:** if one tenant is 40% of the traffic, you've built a bottleneck with extra steps.
- **Re-sharding** is a project, not a task. Consistent hashing makes it less painful.
- **Senior rule:** *sharding is the last resort.* Before that: indexes, caching, read replicas, partitioning,
  archiving cold data, and bigger hardware. A single well-tuned Postgres instance can handle far
  more than people think.

> **Card** · **When:** when a single instance can no longer cope ·
> **Pattern:** vertical → read replicas → partitioning → archiving → **and only then** sharding ·
> **Anti-pattern:** sharding before you've added indexes and a cache ·
> **Limits:** replicas scale reads, never writes; sharding takes away joins and global `UNIQUE` ·
> **How it fails:** you write and then read from the replica: the user doesn't see their own change ·
> **Decision:** the shard key is the most irreversible decision you'll make ·
> **Trade-off:** write scale vs loss of guarantees and operational complexity ·
> **Related:** eventual consistency, CAP `[08, 19]`

---

## Query optimization

**The process:**
1. **Measure, don't guess.** `pg_stat_statements` sorted by `total_exec_time` tells you which queries really
   eat your resources — often it's a fast query executed a million times, not the slow one.
2. `EXPLAIN (ANALYZE, BUFFERS)` on the top 5.
3. An index, a rewrite or a model change.

**The recurring problems:**

- **N+1.** You load 100 orders and then run 1 query per order to fetch the customer. Fix: `JOIN`, `IN (...)`,
  or your ORM's eager loading (`select_related`/`joinedload`/`includes`). **It's the number one performance
  bug in any app with an ORM.**
- **`SELECT *`** pulls in large columns you don't use and prevents index-only scans.
- **Large `OFFSET`** — use keyset pagination (`03-apis.md`).
- **Exact `COUNT(*)` on huge tables** — it's a scan. Use an estimate from `pg_class.reltuples`,
  a maintained counter, or say "more than 10,000" like Google does.
- **`LIKE '%text%'`** doesn't use a B-tree index. You need GIN with `pg_trgm` or full-text search.
- **`OR` across different columns** often prevents index use; sometimes `UNION ALL` is faster.
- **Stale statistics** → the planner chooses badly. Run `ANALYZE` and check autovacuum.

> **Card** · **When:** when `pg_stat_statements` points at the culprit ·
> **Pattern:** measure by **total time**, not average time — the winner is usually a fast query executed a million times ·
> **Anti-pattern:** adding indexes blindly without reading the plan ·
> **Limits:** `EXPLAIN` without `ANALYZE` is an estimate, not reality ·
> **How it fails:** **N+1** is the number one performance bug in any app with an ORM ·
> **Decision:** if estimated and actual rows differ a lot, the problem is the statistics ·
> **Trade-off:** denormalizing speeds up reads and adds consistency work ·
> **Related:** indexes, caching, profiling `[09]`

---

## Connection pooling

Every Postgres connection is **an operating system process** with its own memory. A thousand connections isn't
"lots of concurrency", it's a server dying from context switching.

- **Application pool** (HikariCP, SQLAlchemy pool, pgx): reuses connections within the process.
- **External pooler** (**PgBouncer**, the standard; Supavisor and PG 18's native pooling as alternatives):
  multiplexes thousands of clients over a few real connections.
- **PgBouncer modes:** `session` (one connection per client session), **`transaction`** (the connection goes back to the
  pool at the end of each transaction — **the one that gives you real multiplexing and the one everyone uses**), `statement` (very
  restrictive).
- **The `transaction` mode trap:** it breaks anything that depends on the session — prepared statements, `SET`,
  advisory locks, `LISTEN/NOTIFY`, temp tables. Many ORMs need specific configuration.
- **Ballpark numbers:** a low `max_connections` in Postgres (100-200) *because* you have a pooler in front.
  The app pool size is closer to `cores × 2 + disk spindles` than to "the more the better".
- **An aggressive `idle_in_transaction_session_timeout`**: kills hung transactions that block the pool and
  vacuum. It's one of the settings that prevents the most incidents.
- **Serverless + Postgres = a classic problem:** every invocation wants its own connection. You need an external
  pooler, no exceptions (or an HTTP driver).

> **Card** · **When:** from day one, and mandatory in serverless ·
> **Pattern:** PgBouncer in `transaction` mode + an app pool sized by cores ·
> **Anti-pattern:** growing the pool "to go faster" — past the optimum, throughput **drops** ·
> **Limits:** `transaction` mode breaks prepared statements, `SET`, `LISTEN/NOTIFY` and temp tables ·
> **How it fails:** a hung transaction exhausts the pool and everything shows up as latency, not as errors ·
> **Decision:** an aggressive `idle_in_transaction_session_timeout`, always ·
> **Trade-off:** multiplexing (more clients) vs session features you can no longer use ·
> **Related:** Little's law, serverless `[09, 13]`

---

## Redis (the essentials)

Single-threaded for commands (so every command is atomic), in-memory, with optional persistence
(RDB snapshots / AOF).

- **Structures:** strings, hashes, lists (queues), sets, **sorted sets** (leaderboards, priority queues,
  sliding-window rate limiting), streams (append-only log with consumer groups), HyperLogLog (approximate
  unique counting), bitmaps.
- **Real-world uses:** cache, sessions, rate limiting, distributed locks, simple queues, pub/sub, leaderboards.
- **Careful:** `KEYS *` blocks the entire server — use `SCAN`. The `maxmemory` policies (`allkeys-lru`
  vs `noeviction`) decide whether Redis drops data or starts returning errors when it fills up.
- **Distributed locks:** `SET key value NX PX 30000` and delete only if the value is yours (Lua script).
  Redlock exists but is disputed; for strict correctness, a lock in Postgres is safer.

> **Card** · **When:** cache, sessions, rate limiting, simple queues, leaderboards ·
> **Pattern:** everything with a TTL; native structures (sorted sets) instead of serialized JSON ·
> **Anti-pattern:** `KEYS *` in production — it blocks the entire server (use `SCAN`) ·
> **Limits:** single-threaded: one slow command blocks all the others ·
> **How it fails:** once `maxmemory` is reached, it either evicts data you thought was persistent or starts returning errors ·
> **Decision:** does the data need to survive? Then Redis is not the source of truth ·
> **Trade-off:** sub-millisecond latency vs durability and RAM cost ·
> **Related:** caching, distributed locks `[08, 09]`

---

## Queries: joins, aggregations and how to read them

**Join types**, which come up constantly:

```sql
-- INNER: only the rows that match in both tables
SELECT o.id, c.email FROM orders o INNER JOIN customers c ON c.id = o.customer_id;

-- LEFT: every row from the left; NULL where there is no match
SELECT c.email, o.id FROM customers c LEFT JOIN orders o ON o.customer_id = c.id;
--   ^ the pattern for "customers WITHOUT orders": LEFT JOIN + WHERE o.id IS NULL

-- CROSS: Cartesian product. Almost always a bug (a forgotten ON)
```

**Aggregations and the rule everybody breaks:** in a `GROUP BY`, every column in the `SELECT` must be
grouped or aggregated. `WHERE` filters **before** grouping; `HAVING`, **after**.

```sql
SELECT c.country,
       COUNT(*)                      AS order_count,
       SUM(o.total_cents)            AS revenue,
       AVG(o.total_cents)::int       AS avg_ticket
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.created_at >= now() - interval '30 days'  -- filters rows (uses the index)
GROUP BY c.country
HAVING COUNT(*) > 100                             -- filters groups (no index)
ORDER BY revenue DESC;
```

**Window functions** — aggregating *without* collapsing rows. This is what separates people who know SQL from people who suffer it:

```sql
-- The latest order for each customer, without correlated subqueries
SELECT * FROM (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS n
  FROM orders o
) t WHERE n = 1;

-- Running total per day
SELECT day, SUM(amount) OVER (ORDER BY day) AS running_total FROM daily_sales;
```

**CTEs and recursion** for hierarchies (org charts, nested categories, comment threads):

```sql
WITH RECURSIVE tree AS (
  SELECT id, name, parent_id, 1 AS level FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, t.level + 1
  FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree ORDER BY level;
```

**How a join is executed** (and why it's sometimes painfully slow): *nested loop* (good if one side is tiny
and the other has an index), *hash join* (good for large unsorted tables; needs memory) and *merge
join* (if both sides arrive sorted). The planner chooses based on statistics; **if it chooses badly, it's almost always
because the statistics are stale**.

> **Card** · **When:** in any query that crosses tables or summarizes data ·
> **Pattern:** window functions instead of correlated subqueries; `EXISTS` instead of `IN` with a large subquery ·
> **Anti-pattern:** `SELECT *` with joins (name collisions and columns you don't use), and aggregating in the
> application what the DB aggregates better · **Limits:** `HAVING` doesn't use indexes; a large hash join spills to disk ·
> **How it fails:** forgetting the `ON` produces a Cartesian product that looks like a hang ·
> **Decision:** if the aggregation is expensive and repeated, a materialized view `[09]` ·
> **Trade-off:** doing the work in the DB (fast, couples you to it) vs in the app (portable, moves more data) ·
> **Related:** indexes, query optimization, EXPLAIN `[09]`

---

## Implementations: what changes between engines

| | PostgreSQL | MySQL / InnoDB | MongoDB | Redis |
|---|---|---|---|---|
| Default isolation | Read Committed | **Repeatable Read** | per operation / multi-doc transactions | atomic commands |
| Indexes | B-tree, GIN, GiST, BRIN, partial, expression | B-tree, fulltext | B-tree, compound, TTL | n/a (structures) |
| JSON | **JSONB with GIN indexes** | JSON (less powerful) | native | strings |
| Concurrency | MVCC, readers don't block | MVCC + gap locks | per document | single-thread |
| Horizontal scaling | replicas, partitions, extensions | replicas, Vitess | native sharding | Cluster |
| Strong at | integrity, complex queries, extensions | simple reads at large scale, ecosystem | flexible schema, documents | minimal latency |
| Trap | bloat and autovacuum | **gap locks** cause unexpected deadlocks | no real joins; lax consistency by default | not a source of truth |

**MySQL:** the default isolation is stricter than Postgres's, but Repeatable Read's *gap locks*
lock ranges you don't expect and cause surprising deadlocks. Its historical `utf8`
**is not real UTF-8** — you have to use `utf8mb4` or emojis break the insert.

**MongoDB:** no real joins (`$lookup` exists and is expensive). You model by embedding what's read together, with
a hard limit of **16 MB per document**. Multi-document transactions have existed since 4.0 but
are expensive: if you need them often, the document model wasn't the right fit.

> **Card** · **When:** when inheriting a system on another engine or evaluating a migration ·
> **Pattern:** know the default isolation **of that specific engine** before reasoning about concurrency ·
> **Anti-pattern:** assuming Postgres SQL behaves the same in MySQL ·
> **Limits:** 16 MB per document in Mongo; MySQL's `utf8` is not UTF-8 ·
> **How it fails:** a locking pattern that worked in Postgres produces deadlocks in MySQL ·
> **Decision:** Postgres by default, unless there's a concrete, measured reason ·
> **Trade-off:** ecosystem and familiarity vs engine capabilities ·
> **Related:** transactions, isolation levels `[08]`

---

## Failure modes: a database

| Failure | Symptom | What you do |
|---|---|---|
| **Exhausted pool** | high latency without high CPU | acquisition timeout, `idle_in_transaction_timeout` |
| **Deadlock** | aborted-transaction error | **retry** the transaction in the app |
| **Bloat / lagging autovacuum** | slow, progressive degradation | make autovacuum more aggressive, `VACUUM FULL` in a maintenance window |
| **Transaction ID wraparound** | the database goes read-only | watch `age(datfrozenxid)` before you get there |
| **Replication lag** | the user doesn't see their write | read from the primary after writing |
| **Disk full** | writes fail, WAL doesn't rotate | alert at 70%, archive old partitions |
| **Data corruption** | checksum errors, unreadable pages | enable `data_checksums`, restore from backup + PITR `[10]` |
| **Connection dropped mid-transaction** | ambiguous state for the client | idempotency: the retry must be safe `[08]` |
| **Plan that suddenly changes** | a fast query starts taking seconds | `ANALYZE`, check whether the table grew or the cardinality changed |

**On corruption:** it's rare but real (hardware, file system bugs, power failures).
Postgres detects it if you enable `data_checksums` **when initializing the cluster** — enabling it later is
expensive. Without checksums, silent corruption propagates into your backups and you don't find out until you
read that page. **That's why restoring backups periodically isn't paranoia: it's how you detect this.**

> **Card** · **When:** when setting up database monitoring ·
> **Pattern:** alert on trends (bloat, lag, transaction age, disk) before the hard threshold ·
> **Anti-pattern:** monitoring only the instance's CPU and memory ·
> **Limits:** a replica is **not** a backup: it replicates the `DROP TABLE` too ·
> **How it fails:** silent corruption gets copied into the backups if you never restore them ·
> **Decision:** `data_checksums` enabled from the moment the cluster is created ·
> **Trade-off:** checksums cost some CPU and catch what you would otherwise lose ·
> **Related:** backups, PITR, disaster recovery `[10, 12]`

---

## Interview questions and trade-offs

**Q: A query that used to be fine now takes 8 seconds. How do you investigate?**
`pg_stat_statements` to confirm which one it is → `EXPLAIN (ANALYZE, BUFFERS)` → compare estimated vs
actual rows → check whether the plan changed (stale statistics, a table that grew, an index that stopped being used), whether there's
bloat from insufficient autovacuum, or whether it's lock contention. *Signal:* you first ask **what changed**
(volume, deployment, data) instead of jumping straight to adding an index.

**Q: What is write skew and which isolation level prevents it?**
Two transactions read the same state, write different rows and together violate an invariant. Only
Serializable prevents it. *Signal:* you give the two on-call doctors example and add that in practice
it's solved more cheaply with `SELECT FOR UPDATE` or with a constraint that makes the invalid state impossible.

**Q: UUID or auto-increment as the primary key?**
UUIDv7 (time-ordered): it avoids UUIDv4's index fragmentation and doesn't reveal business volume
the way auto-increment does. *Signal:* you explain **why** UUIDv4 hurts — random inserts into the B-tree,
worse locality, bigger indexes — and that in a distributed system generating IDs on the client saves you
a round trip.

**Q: How do you add a NOT NULL column to a 500-million-row table without downtime?**
Expand/contract: add it as nullable → deploy code that writes to both → backfill in batches → add the
constraint as `NOT VALID` and then `VALIDATE` → contract. *Signal:* you mention `lock_timeout`, that the
backfill runs in batches with pauses so it doesn't saturate replication, and that the old and new code coexist.

**Q: You have 2,000 connections to Postgres and the server is crawling. What do you do?**
PgBouncer in transaction mode, lower `max_connections`, size the app pool based on cores, and
set `idle_in_transaction_session_timeout`. *Signal:* you explain that each connection is a process and that more
connections ≠ more throughput — past the optimal point, performance *drops*.

**Q: When would you shard?**
Almost never; first indexes, cache, read replicas, partitioning and archiving. *Signal:* you talk about the
shard key as an irreversible decision, about per-tenant hotspots, and about what you lose (joins, global
transactions, global uniqueness).

**Core trade-off of this box:** *consistency and ease of querying (relational, a single instance)
vs write scale and availability (distributed, denormalized)*. Every step towards scale takes away
guarantees that your code will have to reimplement by hand — worse, and with more bugs than the database.

---

## Sources

- [PostgreSQL docs](https://www.postgresql.org/docs/current/) — MVCC, isolation levels, indexes, `EXPLAIN`.
- *Designing Data-Intensive Applications* (Martin Kleppmann) — the reference on storage, replication and consistency.
- [Use The Index, Luke](https://use-the-index-luke.com/) — how B-tree indexes work in practice.
- [PgBouncer docs](https://www.pgbouncer.org/config.html) — pooling modes and their limitations.
- [PostgreSQL Connection Pooling in 2026: PgBouncer vs built-in pooling](https://postgresqlhtx.com/postgresql-connection-pooling-in-2026-when-to-use-pgbouncer-vs-built-in-pooling/)
