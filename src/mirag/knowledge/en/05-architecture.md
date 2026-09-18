# 05 · Architecture

> Architecture is the set of decisions that are expensive to change later. That's why in a senior
> interview nobody asks you for definitions: they ask **what you chose, what you ruled out and why**.


**Covers from the syllabus:** `concepts` · `patterns` · `implementations` · `boundaries` · `dependencies` · `constraints` · `failure_modes` · `tradeoffs`

---

## Layered Architecture

The classic three layers: **presentation → application/domain → data**.

```
HTTP handler  →  Service  →  Repository  →  DB
```

- **Rule:** dependencies point downward. A repository doesn't call a controller.
- **Why it's still the most widely used:** everyone understands it without documentation.
- **Where it breaks:** when the "Service" turns into a 3,000-line file that orchestrates everything
  (*anemic domain model*: entities with nothing but getters and setters, and all the logic outside them). At
  that point you no longer have layers, you have a long script with folders.

> **Card** · **When:** the sensible default for almost any service ·
> **Pattern:** dependencies in one direction only, always downward ·
> **Anti-pattern:** *anemic domain model* — entities with only getters and all the logic in a 3,000-line Service ·
> **Limits:** it says nothing about how to split things *within* each layer ·
> **How it fails:** the service layer becomes a junk drawer nobody dares to touch ·
> **Decision:** if the domain is CRUD, this is enough; don't bring in hexagonal because it's trendy ·
> **Trade-off:** universal simplicity vs coupling the domain to the framework ·
> **Related:** hexagonal, DDD, repository `[01]`

---

## Clean / Hexagonal / Ports & Adapters

They're the same idea under different names: **the domain doesn't know about the infrastructure.**

```
        HTTP        CLI         Cron
          \          |          /
           [    inbound adapters    ]
                     |
              ┌──────────────┐
              │    DOMAIN    │   ← pure business rules, no framework imports
              │  (entities,  │
              │  use cases)  │
              └──────────────┘
                     |
           [   outbound adapters    ]
          /          |          \
     Postgres      Stripe      S3
```

- **Port** = an interface defined by the domain (`SavesOrders`, `ChargesPayments`).
- **Adapter** = a concrete implementation (`PostgresOrders`, `StripePayments`).
- **Dependency inversion:** the domain defines the interface; the infrastructure implements it. That's why the
  arrows point *inward*.

**What you really gain:** you can test all the business logic without spinning anything up, and switching payment
provider or database touches one file, not fifty.

**What it costs:** lots of boilerplate and mapping layers (domain entity ↔ persistence model ↔ DTO).
**In a CRUD app, this is pure over-engineering.** The honest senior take: apply hexagonal where there's real,
complex business logic; in modules that only read and write, a direct repository is enough.

> **Card** · **When:** modules with complex business logic and swappable providers ·
> **Pattern:** the domain defines the interface (port); the infrastructure implements it (adapter) ·
> **Anti-pattern:** applying it to a CRUD — 40 files to read a user ·
> **Limits:** it requires mapping layers (domain ↔ persistence ↔ DTO) that have to be maintained ·
> **How it fails:** the "ports" end up with the exact shape of the ORM and you haven't decoupled anything ·
> **Decision:** hexagonal where there are real business rules; a direct repository where there's only reading/writing ·
> **Trade-off:** testability and portability vs boilerplate ·
> **Related:** dependency inversion, repository, DDD `[11]`

---

## SOLID

| Principle | What it really means | What it looks like in a backend |
|---|---|---|
| **S**ingle Responsibility | one class, **one reason to change** | separate `PriceCalculator` from `InvoiceSender` |
| **O**pen/Closed | extend without modifying | add a new payment provider by implementing the interface |
| **L**iskov Substitution | a subclass must be able to replace the base class without surprises | if `SquareRectangle.setWidth` changes the height, you've broken it |
| **I**nterface Segregation | small, specific interfaces | separate `Reader` and `Writer` instead of a 30-method `Repository` |
| **D**ependency Inversion | depend on abstractions, not concretions | the service receives `SendsEmails`, not `SendGridClient` |

**The nuance that matters:** SRP isn't "a class does one thing", it's **"a class answers to a single actor"**.
If the finance team and the marketing team can both request changes to the same class, it has two reasons to
change and it has to be split.

**And the warning:** SOLID applied without judgment produces 40 files to read a user from the database.
The goal is to make changing your mind cheap, not to collect interfaces.

> **Card** · **When:** when reviewing code that's going to change a lot ·
> **Pattern:** SRP understood as "one reason to change" = **a single actor** requesting changes ·
> **Anti-pattern:** one interface per class "just in case" ·
> **Limits:** they're heuristics, not laws; applying them without judgment multiplies files ·
> **How it fails:** violating Liskov breaks things when you swap one implementation for another in production ·
> **Decision:** can two departments request changes to the same class? Split it ·
> **Trade-off:** future flexibility vs the number of indirections you have to read today ·
> **Related:** DI, design patterns, rule of three `[01]`

---

## DDD (Domain-Driven Design)

**Strategic** (what really matters and almost nobody applies):
- **Ubiquitous language:** the code uses the same words as the business. If they say "policy", your
  class isn't called `InsuranceRecord`.
- **Bounded context:** a model is valid *within a context*. "Customer" means different things in
  Sales, Billing and Support — **and it's fine for them to be three different models.** Forcing a single
  `Customer` entity shared by the whole company is where the unmaintainable monolith comes from.
- **Context map:** how the contexts relate to each other (shared kernel, customer/supplier, anticorruption layer).
- **Anticorruption layer:** a translation layer so the ugly model of an external (or legacy) system doesn't
  leak into yours.

**Tactical:**
- **Entity:** has an identity that persists (an `Order` with its ID).
- **Value object:** defined by its value, immutable (`Money`, `Email`, `Address`). Use them more: an `Email`
  type validated in the constructor eliminates an entire class of bugs.
- **Aggregate:** a group of objects with a **root** that is the only entry point, and which defines the
  **boundary of transactional consistency**. The rule: *one transaction modifies a single aggregate*; across
  aggregates, eventual consistency via domain events.
- **Domain event:** "something relevant happened" (`OrderPaid`). The piece that connects DDD with event-driven
  architecture.
- **Repository:** a collection of aggregates; one per aggregate root, not one per table.

**Where DDD's real value lies:** in deciding **the boundaries**. The rest (entities, VOs) is good modeling
practice you can apply without calling it DDD.

> **Card** · **When:** domains with rich business rules and their own vocabulary ·
> **Pattern:** bounded contexts + ubiquitous language + aggregates as the transactional boundary ·
> **Anti-pattern:** a single `Customer` entity shared by the whole company ·
> **Limits:** the value is in strategic DDD (the boundaries), not in the tactical catalog ·
> **How it fails:** applying entities and value objects without defining contexts = more ceremony, same mess ·
> **Decision:** one transaction modifies **a single aggregate**; across aggregates, events ·
> **Trade-off:** a model faithful to the business vs the team's learning curve ·
> **Related:** service boundaries, event-driven, aggregates `[08, 17]`

---

## Modular monolith vs microservices

**The consensus position in 2026: start with a modular monolith.** The industry has already been through the
hangover of premature microservices.

**Modular monolith:** one deployment, but modules with real boundaries — each module has its own schema
or at least its own tables, they communicate through explicit public interfaces (or in-process events),
and **joining directly against another module's tables is forbidden**. If the boundaries are real, extracting
a module into a service later is mechanical.

| | Modular monolith | Microservices |
|---|---|---|
| Deployment | one | N pipelines |
| Transactions | **native ACID** | sagas, eventual consistency |
| Refactoring boundaries | one commit | migration coordinated across teams |
| Debugging | stack trace | **distributed tracing is mandatory** |
| Scaling | everything together | per service |
| Failures | everything goes down | partial failures (and more failure modes) |
| Operational cost | low | **high: a platform team is required** |

**When microservices make sense:** large teams blocking each other in the same repo, radically different
scaling needs (a video transcoding service vs a CRUD), isolation requirements (PCI, health data), or
justified differences in tech stack.

**When NOT:** "to scale" when you have 10,000 users, "because Netflix", or to fix an organizational
problem. **Conway:** your architecture will end up copying your org chart; if the org chart can't support
microservices, neither can the architecture.

**The worst anti-pattern:** the **distributed monolith** — N services that share a database and call each other
in a synchronous chain. You get all the costs of distribution and none of its benefits.

> **Card** · **When:** the most expensive structural decision you'll make ·
> **Pattern:** a modular monolith with automatically verified boundaries ·
> **Anti-pattern:** **distributed monolith** — N services sharing a database ·
> **Limits:** microservices demand tracing, per-service CI, service discovery and on-call ·
> **How it fails:** a typical feature touches three services and needs three coordinated deployments ·
> **Decision:** do teams block each other in the same repo? Only then split ·
> **Trade-off:** coordination cost (monolith) vs operational and consistency cost (distributed) ·
> **Related:** Conway, sagas, service boundaries `[08, 19]`

---

## Service boundaries

How to draw boundaries well:

- **By business capability**, not by technical layer. `Billing`, `Inventory`, `Shipping` — never a
  "database service" or a "validation service".
- **By transactional boundary.** If two things *have to* change atomically, they go together. Splitting them
  across services dooms you to sagas.
- **By rate of change.** What changes together lives together.
- **By data ownership.** Each piece of data has **a single owner** that writes it; everyone else reads copies or
  asks. Two services writing to the same table is a badly drawn boundary.
- **The boundary test:** if a typical feature requires touching three services and coordinating three deployments,
  the boundaries are wrong.

> **Card** · **When:** when extracting a service or splitting a module ·
> **Pattern:** by business capability, by transactional boundary and by data ownership ·
> **Anti-pattern:** boundaries by technical layer ("validation service", "database service") ·
> **Limits:** what must change atomically can't be separated without paying for a saga ·
> **How it fails:** two services writing to the same table = a badly drawn boundary, incidents guaranteed ·
> **Decision:** each piece of data has **a single owner** that writes it; everyone else reads copies ·
> **Trade-off:** team autonomy vs consistency and latency ·
> **Related:** aggregates, sagas, event-driven `[08]`

---

## CQRS

Separate the **write** model (commands) from the **read** model (queries).

```
Command → write model (normalized, validations) → events
                                                    ↓
                        read model (denormalized, ready to render)
```

- **Lightweight CQRS:** same store, different models/DTOs for reading and writing. Cheap, and usually enough.
- **Full CQRS:** separate stores, synchronized via events → **eventual consistency** (the reader
  sees the change 200ms later). Your UI has to be designed for that.
- **When it's worth it:** reads and writes with radically different loads or shapes (a feed that's read
  a million times and written a thousand).
- **Event sourcing** (storing the events as the source of truth instead of the state) gets mentioned alongside
  CQRS, but it's a separate and much more expensive decision: event versioning, replays, snapshots, and explaining
  to everyone why you can't just run a simple `UPDATE`. **Excellent for domains with real auditing needs
  (banking, trading); dead weight for a CRUD.**

> **Card** · **When:** reads and writes with radically different shapes or loads ·
> **Pattern:** start with lightweight CQRS (same store, different models) ·
> **Anti-pattern:** separate stores without the UI being designed for eventual consistency ·
> **Limits:** the reader lags behind the writer; always ·
> **How it fails:** the user saves, reloads and doesn't see their change ·
> **Decision:** CQRS and event sourcing are **separate** decisions; don't adopt them together out of inertia ·
> **Trade-off:** read performance vs complexity and lag ·
> **Related:** event-driven, eventual consistency `[08]`

---

## Event-driven architecture

Services publish facts; others react. Messaging details are in `08-distributed-systems.md`.

- **Event notification:** "something happened, go fetch the details". Minimal payload, low coupling, more
  network chatter.
- **Event-carried state transfer:** the event carries the data. The consumer doesn't need to call you; in
  exchange, you duplicate state and have to version the event schema carefully.
- **Benefits:** temporal decoupling (the consumer can be down), extensibility (you add a
  new consumer without touching the producer), and absorbing spikes.
- **Real costs:** the flow stops being readable in the code (to know what happens when an order is paid you have
  to search the whole repo for who's listening), debugging is hard without tracing, **ordering and duplicates**
  have to be handled, and event schemas turn into a public API that nobody versions.

**Rule of thumb:** events to *notify past facts* across contexts; synchronous calls to
*ask for something you need right now*. Mixing up those two criteria is how you end up with event chains
that are impossible to follow.

> **Card** · **When:** between bounded contexts, to notify facts that have already happened ·
> **Pattern:** events to notify; synchronous calls to ask for something you need now ·
> **Anti-pattern:** event chains where nobody can explain what happens when an order is paid ·
> **Limits:** the event schema is a public API that almost nobody versions ·
> **How it fails:** the flow stops being readable in the code; without tracing it's undebuggable ·
> **Decision:** *event notification* (minimal payload) if you want low coupling; *state transfer* if
> you want the consumer not to have to call you · **Trade-off:** decoupling vs traceability ·
> **Related:** queues, outbox, sagas `[08, 12]`

---

## Dependency injection

Pass dependencies in instead of building them inside.

```python
# bad: coupled, untestable without network access
class OrderService:
    def __init__(self):
        self.payments = StripeClient(api_key=os.environ["STRIPE_KEY"])

# good: injected, testable with a test double
class OrderService:
    def __init__(self, payments: PaymentGateway):
        self.payments = payments
```

- **Constructor injection** is the default form: dependencies are explicit and the object is born valid.
- **You don't need a DI framework.** In dynamic languages, passing arguments plus a `build_app()` function
  that wires up the graph at startup (*composition root*) is enough and far more readable.
- **The anti-pattern:** *service locator* (a global container that every class pulls what it needs from).
  It hides dependencies and turns configuration errors into runtime failures.

> **Card** · **When:** whenever something depends on I/O or configuration ·
> **Pattern:** constructor injection + a `composition root` that wires up the graph at startup ·
> **Anti-pattern:** *service locator* — a global container that every class pulls whatever it wants from ·
> **Limits:** you don't need a DI framework; in dynamic languages, passing arguments is enough ·
> **How it fails:** hidden dependencies turn configuration errors into runtime failures ·
> **Decision:** if you can't test the class without network access, the dependency isn't injected ·
> **Trade-off:** explicitness vs verbose constructors ·
> **Related:** hexagonal, testing with test doubles `[11]`

---

## Design patterns you'll actually use

- **Repository** — abstracts persistence. Careful: if your repository returns the ORM's `QuerySet`, you haven't
  abstracted anything.
- **Unit of Work** — groups changes and commits them in a single transaction. It's what SQLAlchemy's `session`
  or EF's `DbContext` does.
- **Strategy** — an interchangeable algorithm (payment providers, pricing policies).
- **Adapter / Anticorruption layer** — wraps what's external.
- **Decorator / Middleware** — logging, auth, retry, caching, without touching the core. The entire modern HTTP
  stack is this.
- **Factory / Builder** — complex or configuration-dependent construction.
- **Observer / Pub-Sub** — decouples the producer from its consumers.
- **Circuit breaker, Bulkhead, Retry** — resilience patterns (`10-reliability.md`).
- **Saga / Outbox / Inbox** — distributed patterns (`08-distributed-systems.md`).
- **State machine** — for any entity with a lifecycle (order, subscription, shipment).
  See `17-business-logic.md`. Modeling the states and the legal transitions explicitly eliminates an
  entire family of bugs.

> **Card** · **When:** when you recognize the problem, not before ·
> **Pattern:** Repository, Unit of Work, Strategy, Adapter, Decorator, State machine ·
> **Anti-pattern:** Singleton as a global in disguise; patterns applied by name rather than by problem ·
> **Limits:** a badly chosen pattern is harder to remove than to add ·
> **How it fails:** a "Repository" that returns the ORM's `QuerySet` abstracts nothing ·
> **Decision:** the rule of three — abstract on the third case ·
> **Trade-off:** shared vocabulary vs unnecessary indirection ·
> **Related:** resilience, distributed patterns, state machines `[08, 10, 17]`

---

## Trade-offs: how to reason out loud

A senior doesn't say "I'd use microservices". They say: **"it depends on X; with this data I'd pick Y, and I'd
change it if Z happened."** The mental framework:

1. **What are the real non-functional requirements?** Target latency, volume, availability,
   consistency, regulatory compliance, team size and maturity.
2. **What's reversible and what isn't?** (Jeff Bezos: one-way vs two-way doors.) Choosing the language or
   the DB schema is almost irreversible; choosing a logging library isn't. Spend your decision time
   where things are irreversible.
3. **What does it cost to get it wrong, and how do I find out early?**
4. **Document the decision with an ADR.** Half a page in the repo. Two years from now someone
   —probably you— will want to know why. The template and how to justify it are in `[19]`.

**The tensions that always come back:**

| Tension | When it falls on each side |
|---|---|
| Strong consistency ↔ availability | money and stock → strong; feeds and counters → eventual |
| Coupling ↔ duplication | duplicating a little code across services beats sharing a library that couples them |
| Simplicity ↔ flexibility | unused flexibility is just complexity |
| Now ↔ later | technical debt is a loan: useful if you know when you'll pay it back |
| Build ↔ buy | build what differentiates you; buy the rest (auth, payments, email) |

> **Card** · **When:** in every structural decision and every design interview ·
> **Pattern:** tell reversible decisions apart from irreversible ones and spend the time on the latter ·
> **Anti-pattern:** listing options without recommending any ·
> **Limits:** you almost never have the data you'd like; decide anyway and write down why ·
> **How it fails:** two years later nobody remembers why that was chosen and nobody dares to change it ·
> **Decision:** document every decision that's expensive to reverse with an ADR `[19]` ·
> **Trade-off:** decision speed vs analysis; overanalysis has a cost too ·
> **Related:** ADRs, system design `[19]`

---

## Coupling and cohesion

The two concepts underlying **everything** else in this box, and that almost nobody can define.

**Cohesion** (high = good): how much the things that sit together actually belong together. A `billing` module
that calculates, issues and numbers invoices has high cohesion. A `utils` module with 40 unrelated functions
has zero cohesion.

**Coupling** (low = good): how much one module needs to know about another in order to work. It's not binary,
it's a spectrum:

| Type of coupling | Example | Severity |
|---|---|---|
| **Data** | passing an `id` as an argument | ✅ the unavoidable minimum |
| **Stamp** | passing a whole object when you only use one field | 🟡 acceptable |
| **Control** | passing a flag that changes the other module's behavior (`run(x, fast=True)`) | 🟠 smells bad |
| **Common** | two modules read and write the same global or the same table | 🔴 serious |
| **Content** | one module touches the other's internal structures | 🔴 serious |
| **Temporal** | A must be called before B and nothing enforces it | 🔴 invisible until it breaks |

**The rule:** *high cohesion inside, low coupling outside.* It's literally the criterion used to
decide what goes in which module and where a service boundary goes.

**Conway's law:** the architecture will end up copying the organization's communication structure.
The *inverse Conway maneuver* is reorganizing the teams to get the architecture you want —
and it's the reason migrations to microservices fail if the org chart doesn't change.

> **Card** · **When:** when deciding where to put a module or draw a boundary ·
> **Pattern:** what changes together lives together; what changes for different reasons gets separated ·
> **Anti-pattern:** the `utils`/`common`/`shared` module that ends up coupling the whole system ·
> **Limits:** reducing coupling usually increases duplication: you have to choose ·
> **How it fails:** temporal and common coupling don't raise errors, just weird, intermittent bugs ·
> **Decision:** does a typical change touch three modules? The boundaries are wrong ·
> **Trade-off:** little duplication (couples) vs independence (duplicates) — across services, **duplicate** ·
> **Related:** service boundaries, bounded contexts, Conway `[19]`

---

## Implementation: what it looks like in the file tree

**Modular monolith** — the boundaries are folders with an explicit public API:

```
src/
├── modules/
│   ├── billing/
│   │   ├── api.py            # THE ONLY thing other modules may import
│   │   ├── domain/           # entities, value objects, rules
│   │   ├── infrastructure/   # repositories, HTTP clients
│   │   └── tests/
│   ├── orders/
│   │   ├── api.py
│   │   └── ...
│   └── inventory/
├── platform/                 # cross-cutting concerns: db, logging, config, auth
│   ├── db.py
│   └── observability.py
└── main.py                   # composition root: wires up the dependency graph
```

**The rule that makes it work:** `orders` can import `billing.api`, **never**
`billing.domain`. And no SQL joins against another module's tables. Without automated verification this
degrades within weeks, so it's checked in CI:

```python
# tests/test_architecture.py — fails the build if someone crosses a boundary
import ast, pathlib

def test_modules_only_talk_through_api():
    for path in pathlib.Path("src/modules").rglob("*.py"):
        own = path.relative_to("src/modules").parts[0]
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                if parts[0] == "modules" and parts[1] != own:
                    assert parts[2:3] == ["api"], f"{path} imports the internals of {parts[1]}"
```

**Hexagonal** — the domain at the center, with no framework imports:

```
src/
├── domain/           # zero imports of fastapi, sqlalchemy, stripe
│   ├── order.py      # entities and rules
│   └── ports.py      # interfaces: SavesOrders, ChargesPayments
├── application/      # use cases that orchestrate the domain
├── adapters/
│   ├── inbound/      # http/, cli/, queue consumers
│   └── outbound/     # postgres/, stripe/, s3/
└── main.py
```

**The test that proves hexagonal is real:** `grep -r "import sqlalchemy\|import fastapi" src/domain/`
must return **zero lines**. If it returns anything, what you have is pretty folders and a regular layered architecture.

> **Card** · **When:** when starting a project or modularizing an existing one ·
> **Pattern:** boundaries verified by architecture tests in CI ·
> **Anti-pattern:** documenting the rules in a wiki and trusting discipline ·
> **Limits:** the folder structure doesn't prevent anything on its own; the language almost never enforces it ·
> **How it fails:** six months later there are cross-imports everywhere and nobody knows when it started ·
> **Decision:** if you're going to extract services someday, start with an `api.py` per module today ·
> **Trade-off:** rigidity (blocks legitimate shortcuts) vs erosion (blocks everything, later) ·
> **Related:** coupling, service boundaries, CI `[14]`

---

## Constraints: what actually decides the architecture

Diagrams don't choose the architecture; these four things do.

| Constraint | How it shapes the architecture |
|---|---|
| **Team size and maturity** | 4 people can't run 12 microservices: there's no on-call rotation. Conway rules |
| **Budget** | multi-region costs more than double; Kubernetes costs a part-time person, permanently |
| **Real scale (not the imagined one)** | at 100 RPS, one instance with read replicas is more than enough |
| **Legacy** | you rarely start from scratch: there's a database other systems read, and an ERP nobody touches |
| **Regulation** | PCI, GDPR or data residency can **force** you to isolate a service or a region `[07]` |
| **Deadline** | a correct architecture delivered late can be worse than a simple one delivered on time |

**To live with legacy**, two patterns:
- **Anticorruption layer** — a translation layer so the old system's model doesn't leak into the new one.
- **Strangler fig** — the new system intercepts the traffic and absorbs functionality route by route,
  until the old one is no longer used. It's the **realistic** way to migrate: never the big bang.

> **Card** · **When:** before drawing the first box ·
> **Pattern:** strangler fig to migrate; ACL to isolate what you don't control ·
> **Anti-pattern:** the full rewrite that "this time will actually work out" ·
> **Limits:** you can't choose an architecture your team can't operate at 3 a.m. ·
> **How it fails:** the ideal architecture is abandoned halfway through the migration and **two** systems coexist forever ·
> **Decision:** pick the simplest thing that meets the real scale and compliance requirements ·
> **Trade-off:** technical ambition vs the team's operational capacity ·
> **Related:** Conway, system design, cost `[14, 19]`

---

## Failure modes: an architecture

Not with an error: with a degradation nobody ever declares.

| Symptom | What it means |
|---|---|
| A small change touches 5 modules | **badly drawn boundaries** |
| Nobody touches a certain file | coupling and missing tests: structural fear |
| Deployments have to be coordinated | **distributed monolith** |
| Everything goes through a central service | single point of failure and organizational bottleneck |
| "Only Ana knows that" | bus factor of 1 |
| Every feature adds an `if` to the same function | a missing abstraction (now it's justified: there are three cases) |
| Tests take 40 minutes | coupling to the infrastructure |
| Nobody knows what happens when an order is paid | an event chain with no orchestration or tracing |

**Architectural debt** differs from code debt in that **you don't pay it off by refactoring a file**:
it requires migrating data, coordinating teams and deploying in several phases. That's why it piles up: every
individual step looks too expensive.

> **Card** · **When:** in retrospectives and when planning quarters ·
> **Pattern:** measure symptoms (lead time, number of modules per PR, CI time) instead of trading opinions ·
> **Anti-pattern:** "we'll fix it when there's time" — there never is ·
> **Limits:** architectural debt doesn't show up in any production metric ·
> **How it fails:** the team's velocity drops gradually and nobody can point to the cause ·
> **Decision:** if a typical change crosses three modules, the boundary is the work, not the feature ·
> **Trade-off:** shipping today vs being able to ship a year from now ·
> **Related:** coupling, DORA, ADRs `[14, 19]`

---

## Interview questions and trade-offs

**Q: Monolith or microservices for a new product with 6 engineers?**
A modular monolith, with serious internal boundaries. *Signal:* you mention Conway, the operational cost (tracing,
per-service CI/CD, service discovery, on-call), and that well-drawn boundaries make a later extraction
mechanical. A candidate who says "always microservices" has never operated any.

**Q: How do you decide where the boundary between two services goes?**
By business capability, by transactional boundary and by data ownership. *Signal:* you say that if two
things must change atomically they shouldn't be separated, because the price is a saga with compensations.

**Q: What is an aggregate and why does it matter?**
A group of objects with a root that is the boundary of transactional consistency. It matters because it defines
what can change atomically and what needs eventual consistency. *Signal:* you connect it to service
design: aggregate boundaries are good candidates for service boundaries.

**Q: Your teammate wants event sourcing for the users module. What do you say?**
That the cost (event versioning, replays, snapshots, learning curve, no way to do a simple UPDATE)
is rarely justified in a CRUD, and that if what they want is auditing, an audit log table
solves 90% of it for 5% of the cost. *Signal:* you separate event sourcing from CQRS, which a lot of people confuse.

**Q: How do you keep a modular monolith from degenerating into a big ball of mud?**
Automatically verified boundaries: architecture tests that fail if a module imports another module's internals,
separate DB schemas, review of PRs that cross modules. *Signal:* you say that discipline without
automated enforcement always loses within six months.

**Core trade-off of this box:** *coordination cost (monolith: everyone in the same codebase) vs operational and
consistency cost (distributed: everyone on the same network)*. Microservices don't eliminate the
complexity, they move it from the compiler to the network — where there are no types, no stack traces and
failures are partial.

---

## Sources

- *Domain-Driven Design* (Eric Evans) and *Implementing DDD* (Vaughn Vernon) — bounded contexts and aggregates.
- *Clean Architecture* (Robert C. Martin) — the dependency rule.
- Alistair Cockburn, [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) — the original.
- [Martin Fowler — Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html), [Microservice Trade-Offs](https://martinfowler.com/articles/microservice-trade-offs.html)
- *Building Microservices* (Sam Newman) — when NOT to split.
- [ADR — Architecture Decision Records](https://adr.github.io/)
