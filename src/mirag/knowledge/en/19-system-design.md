# 19 · System Design

> The system design interview doesn't assess whether you know the answer: it assesses **how you think when the problem
> is ambiguous**. You are judged on whether you ask the right questions, whether you back your choices with numbers and
> whether you acknowledge the trade-offs of your own solution.


**Covers from the syllabus:** `requirements` · `capacity` · `architecture` · `bottlenecks` · `failure_scenarios` · `tradeoffs` · `decisions` · `diagrams`

---

## The script for a 45-minute interview

| Phase | Time | What you do |
|---|---|---|
| 1. Requirements | 5-8 min | ask questions and narrow the scope |
| 2. Estimates | 3-5 min | numbers that justify the decisions |
| 3. API and data model | 5-8 min | the contract and the entities |
| 4. High-level design | 10 min | the drawing with the pieces |
| 5. Deep dive | 10-15 min | the interviewer picks a point |
| 6. Bottlenecks and failures | 5 min | what breaks first and how you mitigate it |

**Mistake number one: starting to draw boxes in minute one.** A senior spends the first few minutes
narrowing the scope. The problem is always deliberately ill-defined to see whether you notice.

> **Card** · **When:** every design interview ·
> **Pattern:** requirements → estimates → API and data → high level → deep dive → failures ·
> **Anti-pattern:** starting to draw boxes in minute one ·
> **Limits:** 45 minutes isn't enough for everything: say out loud what you are leaving out ·
> **How it fails:** you run out of time on the part they were really assessing ·
> **Decision:** the problem is always ill-defined on purpose, to see whether you notice ·
> **Trade-off:** breadth vs depth ·
> **Related:** requirements, communication `[05]`

---

## 1. Requirements

**Functional — what it does.** Narrow it down aggressively: *"Do we include comments and likes, or do I focus on
posting and reading the feed?"* Leaving things out explicitly is correct and desirable.

**Non-functional — the ones that shape the architecture.** These are the questions that set a senior apart:
- **Scale:** daily active users? reads vs writes? peaks?
- **Target latency:** a p99 of 100ms or of 2 seconds? It changes the entire design.
- **Consistency:** must users see their own change instantly? And everyone else?
- **Availability:** what happens if it's down for 10 minutes? Is that acceptable?
- **Durability:** can a piece of data be lost? (A "like", maybe. A bank transfer, never.)
- **Multi-region, regulation, retention, cost.**

**The most valuable question you can ask:** *"What is it that **must not** fail here?"* The answer tells
you where to spend consistency and redundancy, and where you can go cheap.

> **Card** · **When:** the first 5-8 minutes, always ·
> **Pattern:** narrowed functional requirements + concrete non-functional ones (latency, consistency, scale) ·
> **Anti-pattern:** silently assuming requirements ·
> **Limits:** without target numbers, no later decision can be justified ·
> **How it fails:** you design for 1M users when there were 10,000, or the other way round ·
> **Decision:** the most valuable question is **"what is it that must NOT fail here?"** ·
> **Trade-off:** narrowing (you deliver something complete) vs covering everything (more ground, but superficial) ·
> **Related:** SLOs, consistency `[10]`

---

## 2. Estimates (capacity planning)

It's not about precision, it's about **orders of magnitude that justify decisions**.

**Reference numbers worth memorising:**
```
1 day ≈ 86,400 s ≈ 10^5 s        →  1M events/day ≈ 12/s  (far less than people think)
1 million active users, 10 actions/day ≈ 115 RPS on average
Peak ≈ 2-5× the average (or 10× if there are one-off events)
1 KB per row × 1,000M rows = 1 TB
A well-tuned Postgres: thousands of simple queries/s on a single instance
Redis: ~100,000 ops/s per node
A 1 Gbps NIC ≈ 125 MB/s
```

**The typical calculation:**
```
10M daily active users · 20 reads = 200M reads/day ≈ 2,300 RPS on average, ~10,000 at peak
Read/write ratio 100:1  →  ~23 writes/s  ← a single primary absorbs that without breaking a sweat
Storage: 200M posts/year · 2 KB = 400 GB/year
```

**The conclusion that impresses most:** *"With these numbers, a single Postgres instance with read
replicas will do. We don't need sharding, and I save myself all its complexity."* Designing for a scale you don't
have is the most common and most expensive mistake — and recognising it shows judgement, not a lack of ambition.

> **Card** · **When:** before choosing technology ·
> **Pattern:** orders of magnitude that **justify** decisions, not precision ·
> **Anti-pattern:** jumping to sharding without calculating whether it fits on one instance ·
> **Limits:** they are estimates: say so and state the margin ·
> **How it fails:** 1M events a day is 12/s — lots of people treat it as if it were thousands ·
> **Decision:** calculate the read/write ratio: it decides caches and replicas ·
> **Trade-off:** designing for 10× (prudent) vs for 100× (over-engineering) ·
> **Related:** scaling, cost `[09, 13]`

---

## 3. API and data model

Define the contract before the infrastructure: it forces you to pin down the behaviour.

```
POST /posts            {content}            → 201 {id}
GET  /feed?cursor=...&limit=20              → 200 {items, next_cursor}
POST /posts/{id}/likes                      → 204   (idempotent)
```

Then the entities, the relationships and **the dominant access pattern**, which is what decides the model:
*"99% of the traffic is reading a user's feed, so I optimise for that even if writes become more expensive."*

This is where the decisions from `04-databases.md` come in: keys, indexes, partitioning and what gets denormalised.

> **Card** · **When:** before drawing the infrastructure ·
> **Pattern:** defining the contract forces you to pin down the behaviour ·
> **Anti-pattern:** choosing a database before knowing the access pattern ·
> **Limits:** the model constrains everything else and is the most expensive thing to change ·
> **How it fails:** a model that doesn't support the dominant query forces a complete redesign ·
> **Decision:** optimise for the access pattern that dominates the traffic ·
> **Trade-off:** normalised vs denormalised depending on reads/writes ·
> **Related:** data modeling, indexes `[04]`

---

## 4. High-level design

```
Client → CDN → LB/API Gateway → Services (stateless)
                                     ├── Cache (Redis)
                                     ├── Primary DB + replicas
                                     ├── Queue → Workers
                                     └── Object storage
```

Start simple and **evolve it out loud**: *"This handles X. When we reach Y, the bottleneck will
be Z, and then I'd add W."* That narrative is worth more than drawing the final architecture in one go.

**The pieces and when you justify them:**
- **CDN** — static assets and cacheable responses; global latency.
- **Load balancer** — distribution and health checks (`09-performance.md`).
- **Stateless services** — so you can scale horizontally (`09-performance.md`).
- **Cache** — when the read/write ratio is high (`09-performance.md`).
- **Queue** — when something can be asynchronous or there are peaks to absorb (`08-distributed-systems.md`).
- **Read replicas** — to offload the primary, accepting lag.
- **Sharding** — only when writes don't fit on one machine.

> **Card** · **When:** the centre of the conversation ·
> **Pattern:** start simple and **evolve it out loud** ("this handles X; at Y the bottleneck will be Z") ·
> **Anti-pattern:** drawing a mature company's final architecture from minute one ·
> **Limits:** every piece you add is one you'll have to justify ·
> **How it fails:** adding Kafka, Kubernetes and microservices without any requirement calling for them ·
> **Decision:** justify each component with the requirement that forces it ·
> **Trade-off:** simplicity vs readiness to grow ·
> **Related:** architecture, components `[05]`

---

## 5. Deep dive: the patterns that keep coming up

**Fan-out on write vs on read** (the feed/timeline classic):
- **On write (push):** when someone posts, you write into every follower's timeline. Instant reads; extremely
  expensive writes for accounts with millions of followers (*the celebrity problem*).
- **On read (pull):** when reading, you query the posts of the people you follow and merge them. Cheap writes,
  expensive reads.
- **Hybrid (the real answer):** push for normal users, pull for celebrities, merging at
  read time. **Knowing that the answer is hybrid is the signal.**

**Other recurring patterns:**
- **Distributed unique ID generation:** Snowflake (timestamp + machine + sequence) or UUIDv7 — time-ordered,
  generated without coordination (`04-databases.md`).
- **Distributed rate limiting:** token bucket in Redis (`03-apis.md`).
- **Search:** a separate inverted index (Elasticsearch), fed by events from the source of truth.
  It is never the same database.
- **Notifications:** queue + workers + preferences + deduplication (`16-integrations.md`).
- **Deduplication and idempotency:** in everything that retries (`08-distributed-systems.md`).
- **Scheduled jobs at scale:** a queue with a visibility timeout, not one cron per server.

> **Card** · **When:** when the interviewer picks a point ·
> **Pattern:** hybrid fan-out, distributed IDs, rate limiting, search with a separate index ·
> **Anti-pattern:** pure on-write fan-out without considering the celebrity problem ·
> **Limits:** each pattern solves one case and creates new work ·
> **How it fails:** an account with 50M followers makes fan-out on write unfeasible ·
> **Decision:** for feeds the answer is almost always **hybrid** ·
> **Trade-off:** write cost vs read cost ·
> **Related:** caching, queues, sharding `[04, 08, 09]`

---

## 6. Bottlenecks, failures and cost

**Identify the bottleneck before they ask you about it.** *"Here the limit is writes on the
primary; beyond N writes/s we'd have to partition by tenant."*

**Failure scenarios — walk through every piece:**

| If this goes down... | What happens? How do I mitigate it? |
|---|---|
| An app instance | the LB takes it out; stateless, no impact |
| The cache | **thundering herd** against the DB → single-flight, TTL with jitter, and sizing to survive a while without the cache |
| The primary | failover to a replica; window of lost writes = replication lag |
| The queue | the producer must buffer locally or reject gracefully |
| An external service | breaker + fallback + degradation (`10-reliability.md`) |
| An entire AZ | multi-AZ from the start |

**And cost**, which almost nobody mentions and always earns points: *"This comes to about X € a month; 70% of it goes on
the database. If cost were a problem, I'd move cold data to cheap storage with
lifecycle rules and cut the log retention."*

> **Card** · **When:** the last few minutes, and get ahead of it ·
> **Pattern:** walk through every piece asking "what happens if this one goes down?" ·
> **Anti-pattern:** presenting a design without naming its limit ·
> **Limits:** you can't eliminate failures, only bound their blast radius ·
> **How it fails:** if the cache goes down, 100% of the traffic hits the DB: you have to size for that ·
> **Decision:** mention the approximate cost and what you'd do if it were a problem ·
> **Trade-off:** redundancy vs cost ·
> **Related:** degradation, thundering herd `[09, 10]`

---

## How to communicate (what they actually score)

- **Think out loud.** Silence can't be assessed.
- **Give a recommendation, not a catalogue.** *"I'd use Postgres because X"*, not *"we could use Postgres,
  Mongo, Cassandra or DynamoDB"*.
- **Name the trade-off you are accepting.** Every decision has a cost; naming it shows you know
  what you're buying.
- **Take the hints.** If the interviewer keeps pushing on something, it's because they want to see you there. Don't dig in.
- **Correct yourself if you're wrong.** Backtracking out loud is a positive signal, not a negative one.
- **Say what you don't know** and how you'd find out. Making things up is spotted instantly.

> **Card** · **When:** throughout the whole interview ·
> **Pattern:** think out loud, recommend instead of listing, name the trade-off you accept ·
> **Anti-pattern:** long silences, or listing four options without choosing ·
> **Limits:** you can't know everything; what's assessed is how you reason when you don't know ·
> **How it fails:** making things up is spotted instantly and costs more than saying "I don't know, I'd check it like this" ·
> **Decision:** take the interviewer's hints: they point at what they want to see ·
> **Trade-off:** confidence in your statements vs honesty about uncertainty ·
> **Related:** trade-offs, ADRs `[05]`

---

## Decisions: ADRs and how to justify them

A design without recorded decisions is a design nobody will be able to question or change later, because
nobody will know **why** it is the way it is.

**Architecture Decision Record** — half a page, in the repo, next to the code:

```markdown
# ADR-014: Cursor pagination in the orders API

## Status
Accepted · 2026-09-15 · Supersedes ADR-006

## Context
The API paginates with OFFSET. With 40M orders, page 2000 takes 4s and clients
see duplicates when rows are inserted while they paginate.

## Considered options
1. Keep OFFSET and cap it at 100 pages — does not fix the duplicates
2. Cursor/keyset on (created_at, id) — constant performance, no jumping to page N
3. Precompute pages in Redis — high complexity and memory for little benefit

## Decision
Option 2. The real use case is infinite scroll; nobody jumps to page 2000.

## Consequences
+ Constant latency regardless of depth
+ No duplicates on insert
- Cannot show "page 7 of 340"; the back office will use a separate endpoint
- Breaking change: v1 keeps OFFSET until its sunset (2027-03)
```

**The three parts people skip, which are the important ones:** the **discarded options** (so that
nobody repeats the analysis), the **negative consequences** (an ADR without downsides is marketing, not a
decision), and the **date with status** (so you know whether it still applies).

**How to justify a decision out loud**, which is what they assess in the interview:

1. **Which non-functional requirement forces it?** Latency, consistency, cost, compliance `[05]`.
2. **Is it reversible?** Spend the analysis on the ones that aren't (data schema, shard key, language).
3. **What does being wrong cost, and how do I detect it early?**
4. **What would have to happen for me to change my mind?** If you can't answer that, you haven't decided: you've
   picked by default.

> **Card** · **When:** every decision that is expensive to reverse ·
> **Pattern:** a short ADR in the repo, with discarded options and negative consequences ·
> **Anti-pattern:** deciding in a meeting and leaving no trace ·
> **Limits:** an ADR documents the decision; it doesn't guarantee it was a good one ·
> **How it fails:** two years later nobody dares change something because nobody knows why it's that way ·
> **Decision:** distinguish one-way doors (irreversible) from two-way doors ·
> **Trade-off:** time spent documenting vs the cost of re-deriving the context later ·
> **Related:** trade-offs, architecture `[05]`

---

## Diagrams: what to draw and at what level

**The C4 model** gives you the vocabulary to avoid mixing levels, which is the most common mistake when drawing:

| Level | What it shows | For whom |
|---|---|---|
| **1 · Context** | your system, its users and the external systems | business and onboarding |
| **2 · Containers** | deployable processes: API, worker, DB, queue | **the most useful level day to day** |
| **3 · Components** | modules inside a container | when designing a service |
| **4 · Code** | classes | almost never worth it |

**Containers** — the one you draw in an interview:

```
                        ┌──────────┐
     browser ──HTTPS──► │   CDN    │
                        └────┬─────┘
                             ▼
                      ┌─────────────┐        ┌──────────────┐
                      │ API (x3)    │───────►│ Postgres     │
                      │ FastAPI     │        │ primary      │
                      └──┬───────┬──┘        └──────┬───────┘
                         │       │                  │ replication
                    ┌────▼──┐ ┌──▼────┐      ┌──────▼───────┐
                    │ Redis │ │ Kafka │      │ read replica │
                    └───────┘ └───┬───┘      └──────────────┘
                                  ▼
                            ┌──────────┐      ┌─────────┐
                            │ Workers  │─────►│   S3    │
                            └──────────┘      └─────────┘
```

**Sequence diagram** — for flows where **order** and failures are what matter (a charge,
an OAuth login, a saga). It's the one that really explains an asynchronous system:

```
Client            API      Postgres         Stripe      Queue     Worker
  │ POST /payments │           │               │          │          │
  ├───────────────►│  INSERT   │               │          │          │
  │                ├──────────►│ (pending attempt)        │          │
  │                ├── create PaymentIntent ──►│          │          │
  │                │◄───── client_secret ──────┤          │          │
  │ ◄── 201 ───────┤           │               │          │          │
  │                │           │               │          │          │
  │      webhook payment_intent.succeeded      │          │          │
  │                │◄──────────────────────────┤          │          │
  │                ├──────────►│ dedupe + transition      │          │
  │                ├───────────── outbox ────────────────►│          │
  │                │           │               │          ├─────────►│ send email
```

**Rules for a diagram to be useful:** a legend if you use different shapes · arrows indicate
**who initiates**, not which way the data flows · label the protocol (HTTPS, gRPC, AMQP) · mark
**synchronous vs asynchronous**, which is the information that gets lost most often · and at most ~10 boxes per diagram:
if it doesn't fit, you need two levels.

**Keep them in the repo as text** (Mermaid, PlantUML, D2) and not as loose images: that way they get reviewed
in the PR and don't go stale the moment someone changes something.

> **Card** · **When:** when designing, when onboarding and in every system design interview ·
> **Pattern:** C4 level 2 for the structure, sequence diagrams for flows where order matters ·
> **Anti-pattern:** a single diagram with 40 boxes mixing infrastructure and classes ·
> **Limits:** a diagram shows structure, not behaviour under failure ·
> **How it fails:** diagrams as images go stale within weeks and mislead more than they help ·
> **Decision:** diagrams as versioned text, reviewed in the PR ·
> **Trade-off:** detail vs readability — an unreadable diagram communicates nothing ·
> **Related:** ADRs, architecture, onboarding `[05]`

---

## Interview questions and trade-offs

**Q: Design a URL shortener.**
The essentials: ID generation (a base62 counter or a hash with collision handling), read-dominated traffic
(ratio of 100:1 or more → aggressive caching and a CDN), 301 vs 302 redirects (**302 if you want to keep counting
clicks**; the browser caches the 301 and you lose the analytics), and simple key-value storage.
*Signal:* you calculate that writes are few and reads are very many, and you design accordingly.

**Q: Design a social network feed.**
Hybrid fan-out, a timeline cache, cursor pagination, and an explicit limit (*"only the last 1,000
posts"*). *Signal:* you identify the celebrity problem on your own and propose the hybrid.

**Q: Design a chat system.**
WebSocket with a backplane (Redis pub/sub) so that users connected to different replicas can see each other,
message persistence ordered per conversation, delivery receipts, and presence with a TTL. *Signal:* you talk
about connection state and what happens during a deployment (everyone reconnects at once: you need
staggered reconnection).

**Q: Design a distributed rate limiter.**
Token bucket in Redis with an atomic Lua script, keyed by user/API key, informative headers and a
fail-open/fail-closed decision. *Signal:* you explain why it can't live in process memory (each replica
would allow the full limit).

**Q: The system must handle 10× more traffic next month. What do you do?**
Measure where the current limit is, scale the stateless parts horizontally, cache, move work to queues, and
only then consider structural changes. *Signal:* you start by measuring instead of redesigning, and you mention
a load test to find the real limit before touching anything (`11-testing.md`).

**Core trade-off of this box:** *designing for today vs designing for the imagined scale*. Over-design
kills more products than under-design: it costs money, slows the team down and adds failure modes for
traffic that may never arrive. What gets valued is **designing for 10× the current traffic, while making clear what
you would change at 100×**.

---

## Sources

- [The System Design Primer](https://github.com/donnemartin/system-design-primer) — the reference repository.
- Jeff Dean, *Latency Numbers Every Programmer Should Know* — the basis of every estimate `[01]`.
- [C4 Model](https://c4model.com/) — diagram levels without mixing them.
- [ADR — Architecture Decision Records](https://adr.github.io/) · [Mermaid](https://mermaid.js.org/) for diagrams as text.
- [5 Backend System Design Patterns Every Engineer Should Understand (2026)](https://medium.com/@naishasaxena2310/5-backend-system-design-patterns-every-engineer-should-actually-understand-3a9bfcb48115)
