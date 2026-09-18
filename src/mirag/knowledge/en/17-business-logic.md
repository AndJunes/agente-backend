# 17 · Business Logic

> The least glamorous box, and the one where the product's real value lives. There are no frameworks to save you here:
> **modeling the business wrong produces bugs that no infrastructure can fix.**


**Covers from the syllabus:** `concepts` · `entities` · `workflows` · `state_machines` · `permissions` · `multi_tenancy` · `audit` · `failure_modes`

---

## Users, organizations and multi-tenancy

**Separate three concepts that people mix up and then cannot untangle:**
- **Identity** — who the person is (email, credentials, MFA).
- **Account/User** — their profile in your system.
- **Membership** — their belonging to an organization, **with a role**.

**The golden rule:** a user can belong to **several** organizations with different roles.
Modeling it as `user.organization_id` and `user.role` looks simpler today and is a painful migration
a year from now. The `memberships(user_id, organization_id, role)` table from day one costs the same.

**Multi-tenancy strategies:**

| Model | Isolation | Cost | When |
|---|---|---|---|
| **Shared row** (`tenant_id` in every table) | logical | low | **the default**: SaaS with many customers |
| **Schema per tenant** | medium | medium | tens or hundreds of large customers |
| **Database per tenant** | strong | high | enterprise, regulatory requirements, data residency |

With a shared `tenant_id`, **the risk is leaking data between customers**. Don't leave it to the discipline of
each developer:
- **Postgres Row-Level Security**, or
- a **base repository that injects the `tenant_id`** into every query automatically, or at the very least
- **tests that explicitly verify** that tenant A sees nothing of tenant B.

A forgotten `WHERE tenant_id` in a new endpoint is the classic SaaS incident, and it is one of the kind that
ends up in the press.

> **Card** · **When:** day one of any B2B SaaS ·
> **Pattern:** identity, user and **membership** as separate entities ·
> **Anti-pattern:** `user.organization_id` — the decision everyone regrets ·
> **Limits:** with a shared `tenant_id`, isolation is logical, not physical ·
> **How it fails:** a forgotten `WHERE tenant_id` in a new endpoint leaks data between customers ·
> **Decision:** enforce the scope in the data layer (RLS or repository), not in each endpoint ·
> **Trade-off:** strong isolation (DB per tenant, expensive) vs shared (cheap, riskier) ·
> **Related:** IDOR, RLS `[04, 06]`

---

## Roles and permissions

Conceptual basis in `06-security.md`. Here, the modeling side:

- **Predefined roles** (owner, admin, member, viewer) cover 90% of cases and are understandable to the user.
  **Custom roles** with granular permissions are an enterprise feature that is expensive to build and to
  explain: don't build it "just in case".
- **Permission = action + resource** (`invoices:read`, `users:invite`). Name them consistently from the
  start.
- **Hierarchy and inheritance:** a folder's permissions are inherited by its documents. It is convenient for the
  user and **expensive to compute**: with deep hierarchies you need to materialize the transitive closure or use a
  Zanzibar-style engine.
- **Edge cases that always show up late:** the last owner cannot be removed or demoted; a
  pending invitation is not a membership; what happens to what someone created when they leave the organization?
- **Effective permissions:** when there are roles, direct permissions and inheritance, you need a single function that
  answers *"can X do Y on Z?"* and **a debugging endpoint that explains why**. Without that,
  every customer question becomes a manual investigation.

> **Card** · **When:** as soon as there is more than one type of user ·
> **Pattern:** predefined roles that cover 90% + permissions named `resource:action` ·
> **Anti-pattern:** custom roles "just in case" before a customer asks for them ·
> **Limits:** hierarchical inheritance is expensive to compute with deep trees ·
> **How it fails:** late edge cases: the last owner, pending invitations, the person who leaves and leaves resources behind ·
> **Decision:** a single `can(actor, action, resource)` function **and an endpoint that explains why** ·
> **Trade-off:** granularity vs understandability for whoever does the configuring ·
> **Related:** RBAC/ABAC, authorization `[06]`

---

## State machines

**The highest-return pattern in this box.** Any entity with a lifecycle (order, subscription, shipment,
request, ticket, document) should be an explicit state machine.

```python
TRANSITIONS = {
    "draft":           {"pending_payment", "cancelled"},
    "pending_payment": {"paid", "cancelled", "expired"},
    "paid":            {"preparing", "refunded"},
    "preparing":       {"shipped", "refunded"},
    "shipped":         {"delivered", "returned"},
    "delivered":       {"returned"},
    # final states: cancelled, expired, refunded, returned
}

def transition(order, new, actor, reason=None):
    if new not in TRANSITIONS.get(order.status, set()):
        raise InvalidTransition(f"{order.status} -> {new}")
    record(order, from_=order.status, to=new, actor=actor, reason=reason, at=now())
    order.status = new
```

**Why this matters so much:**
- **Impossible states cease to exist.** An order cannot be "shipped" without having been "paid".
- **Loose booleans are the anti-pattern.** `paid`, `shipped`, `cancelled` as three booleans allow
  eight combinations, five of which make no sense — and the code ends up full of defensive `if`s.
- **Every transition is a natural point** to fire events, notifications and audit log entries.
- **It documents the business** better than any wiki: the diagram *is* the code.
- **Concurrency:** the transition must be atomic —
  `UPDATE orders SET status='paid' WHERE id=$1 AND status='pending_payment'` and check the affected rows.
  Otherwise, two simultaneous webhooks perform the same transition twice.

> **Card** · **When:** every entity with a lifecycle ·
> **Pattern:** declared legal transitions + a record of every change with actor and reason ·
> **Anti-pattern:** loose booleans (`paid`, `shipped`, `cancelled`) ·
> **Limits:** the model must account for the intermediate states a saga produces `[08]` ·
> **How it fails:** two concurrent events apply the same transition twice ·
> **Decision:** `UPDATE ... WHERE status = 'previous'` and check the affected rows ·
> **Trade-off:** rigidity vs eliminating impossible states by construction ·
> **Related:** payments, audit logs `[07]`

---

## Workflows

Multi-step business processes that span services, people and time (onboarding, expense approval,
returns, vendor registration).

- **Steps with persisted state**, not in-memory variables: a workflow can last for days and has to survive
  deployments and crashes.
- **Human waits** (approvals) and **timed waits** (a reminder after 3 days, expiry after 7) are
  part of the model, not a cron job held together with duct tape.
- **Resumable and idempotent:** if the worker dies at step 4, it resumes without repeating the effects of
  steps 1-3.
- **Compensations** when a late step fails (`08-distributed-systems.md`).
- **When to use a workflow engine** (Temporal, Step Functions, the Workflow DevKit): when there are many
  steps, long waits and a need for durable retries. For three steps, a state machine and a
  queue are more than enough — bringing in an engine for that is over-engineering.
- **Mandatory visibility:** a screen where support can see which step each instance is at and why it is
  stuck. Without it, every customer query becomes a hand-written database query.

> **Card** · **When:** multi-step processes with human or timed waits ·
> **Pattern:** persisted state per step, resumable and idempotent ·
> **Anti-pattern:** keeping progress in in-memory variables ·
> **Limits:** a workflow can last for days and must survive deployments ·
> **How it fails:** the worker dies at step 4 and, when resuming, repeats the effects of steps 1-3 ·
> **Decision:** with 3 steps, a state machine and a queue; a workflow engine only if there are many steps and long waits ·
> **Trade-off:** durable engine (powerful, one more piece to operate) vs hand-rolled ·
> **Related:** sagas, background jobs `[08, 15]`

---

## Inventory, orders and invoicing

**Inventory** (details in `07-payments.md`):
- **Physical vs available vs reserved.** Available stock is `physical − reserved`. Modeling it with a single
  number is what causes overselling.
- Reservations **have a TTL** and must be released. A job that expires orphaned reservations is mandatory.
- **Movements, not just a balance:** one record per inbound/outbound movement, with a reason. The balance is the sum. That way you can
  audit, reconcile and explain any discrepancy. It is accounting applied to stock.

**Orders:**
- **Immutable once confirmed**, with a snapshot of prices, taxes and shipping details.
- Later modifications are **new documents** (credit note, replacement order), not edits.
- Returns and partial refunds need to be modeled at the **line** level, not the order level.

**Invoicing:** **gapless sequential** numbering per series and fiscal year (a legal requirement in many
countries — and watch out: a Postgres `SEQUENCE` **leaves gaps** on rollback, so you need a different
strategy), immutability, and legal retention for years that has to coexist with the right to erasure
(`15-files-data.md`).

> **Card** · **When:** any finite resource or legal document ·
> **Pattern:** **movements, not just a balance** — stock is the sum of inbound and outbound movements ·
> **Anti-pattern:** a single stock number that gets overwritten ·
> **Limits:** invoice numbering must be sequential **with no gaps** (a `SEQUENCE` leaves them on rollback) ·
> **How it fails:** a discrepancy nobody can explain because there is no trail of the changes ·
> **Decision:** orders are immutable once confirmed; corrections are new documents ·
> **Trade-off:** more rows and complexity vs auditability and the ability to reconcile ·
> **Related:** payments, money, audit `[07]`

---

## Notifications

- **Preferences per user, per channel and per event type.** Not a global boolean.
- **Deduplication and batching:** if something generates 50 events in a minute, send a digest. Without this you burn out
  the channel and the user turns everything off.
- **Versioned templates**, with i18n and the recipient's time zone (don't send a push at 4 in the
  morning).
- **Idempotency:** store which notification was sent for which event; a job retry must not send a duplicate.
- **A central service**, not every module sending on its own (`16-integrations.md`).

> **Card** · **When:** as soon as you notify a user of anything ·
> **Pattern:** a central service with per-channel and per-type preferences, deduplication and batching ·
> **Anti-pattern:** every module sending on its own ·
> **Limits:** the recipient's time zone and language, not yours ·
> **How it fails:** 50 events generate 50 notifications and the user turns everything off ·
> **Decision:** store what was sent for which event: a job retry must not send a duplicate ·
> **Trade-off:** immediacy vs batching into a digest ·
> **Related:** email, push, idempotency `[08, 16]`

---

## Audit logs

**Who did what, when, to what, and from where.** A regulatory requirement in many sectors and the
tool that most often saves an investigation.

```
{actor_id, actor_type (user|system|api_key), action, resource_type, resource_id,
 before, after, ip, user_agent, request_id, tenant_id, occurred_at}
```

- **Append-only.** If it can be edited, it is not an audit log. Ideally in a separate store with different
  permissions, so that whoever compromises the app cannot erase their tracks.
- **Keep it distinct from application logs:** the audit log is a **product for the user and the auditor**
  (it gets queried, exported and kept for years), not debugging material.
- **Record reads as well** for sensitive data if your sector requires it (healthcare, finance).
- **Automate it in the data layer** (ORM hooks, triggers) instead of relying on every endpoint to
  remember it.

> **Card** · **When:** mandatory with third-party data or regulatory requirements ·
> **Pattern:** append-only, in a separate store, with actor, action, before/after and context ·
> **Anti-pattern:** confusing it with application logs ·
> **Limits:** if it can be edited, it is not an audit log ·
> **How it fails:** whoever compromises the app can erase their tracks if they share permissions ·
> **Decision:** automate it in the data layer (hooks or triggers), not endpoint by endpoint ·
> **Trade-off:** volume and cost vs being able to answer "who did this and when" ·
> **Related:** compliance, observability `[06, 12]`

---

## Business rules: where they live

**The problem:** business rules get scattered across the frontend, the controllers, the services, the database
triggers and the jobs. Nobody knows which one wins.

**Principles:**
- **A single source of truth per rule.** The frontend may *duplicate* a validation to provide good UX,
  but **the server always has the final say**.
- **Invariant rules go in the database** as constraints (`CHECK`, `UNIQUE`, FK). It is the only
  layer nobody can bypass — not a script, not a migration, not a concurrency bug.
- **Domain rules go in the domain**, expressed in the language of the business
  (`is_refundable()`, not `if status == 3 and days < 30`).
- **Configuration vs code:** whatever changes per customer or per campaign (limits, percentages, deadlines) goes into
  configuration or a table; whatever is structural goes into code. **Don't build a generic rules engine
  unless the business genuinely asks for it** — you end up writing a worse programming language, with no
  tests and no debugger.
- **Dates, deadlines and time zones** are a bottomless source of bugs: "3 business days" depends on the country,
  "end of month" on the calendar, and the user's midnight is not yours. Centralize those calculations in a
  single module with exhaustive tests.

> **Card** · **When:** when deciding where to put each validation ·
> **Pattern:** invariants as DB constraints; domain rules in the domain ·
> **Anti-pattern:** a generic rules engine built "just in case" ·
> **Limits:** the database is the only layer that **nobody** can bypass ·
> **How it fails:** the same rule is implemented in three places and the three versions drift apart ·
> **Decision:** what changes per customer or campaign goes into configuration; what is structural, into code ·
> **Trade-off:** configurable (flexible, more possible states) vs hard-coded (rigid, predictable) ·
> **Related:** validation, constraints `[03, 04]`

---

## Entities and aggregates

The vocabulary from `[05]`, applied here: **an entity has an identity that persists** (an `Order` is still
the same order even if every one of its fields changes); a **value object** is defined by its value and is
immutable (`Money`, `Email`, `Address`).

**Use more value objects.** An `Email` type validated in its constructor eliminates an entire family of bugs,
because from that point on **it is impossible** to have an invalid email circulating through the system:

```python
@dataclass(frozen=True)
class Email:
    value: str
    def __post_init__(self):
        if "@" not in self.value or len(self.value) > 254:
            raise ValueError(f"invalid email: {self.value}")

@dataclass(frozen=True)
class Money:
    cents: int
    currency: str
    def __add__(self, other):
        if self.currency != other.currency:            # impossible to add EUR + USD
            raise ValueError("different currencies")
        return Money(self.cents + other.cents, self.currency)
```

**The aggregate** is the group of objects with a **root** that is the only entry point, and it defines the
**boundary of transactional consistency**:

```
Order (root)                      <- loaded and saved as a whole
├── OrderLine       (internal)    <- nobody modifies it from outside the Order
├── ShippingAddress (value object)
└── customer_id                   <- reference by ID to ANOTHER aggregate, not the object
```

**The two rules that make this work:**

1. **A transaction modifies a single aggregate.** If you need to change two, one of them is updated via an event
   with eventual consistency (`[08]`).
2. **Aggregates reference each other by ID**, never by object. That way the aggregate loads in full without
   dragging half the system along with it, and the boundary is real.

**How to choose the size of the aggregate:** as small as possible while still upholding its invariants. If the rule
is *"the order total is the sum of its lines"*, then lines and order go together. If it is
*"a customer cannot have more than 5 active orders"*, that invariant **crosses aggregates** and is solved
with eventual consistency and compensation, not with a giant transaction.

> **Card** · **When:** when modeling any domain with rules of its own ·
> **Pattern:** aggregate root as the only entry point; references by ID between aggregates ·
> **Anti-pattern:** huge aggregates that drag half the database along on every load ·
> **Limits:** invariants that cross aggregates **cannot** be guaranteed in a single transaction ·
> **How it fails:** an aggregate that is too large produces lock contention and long transactions `[04]` ·
> **Decision:** the aggregate boundary is a good candidate for a service boundary `[05]` ·
> **Trade-off:** large aggregate (easy invariants, little concurrency) vs small (scales, eventual consistency) ·
> **Related:** DDD, service boundaries, sagas `[05, 08]`

---

## Business inconsistencies: how the logic fails

The failures in this box don't produce errors: they produce **data that doesn't add up**.

| Inconsistency | Origin | Defense |
|---|---|---|
| Negative stock | check-then-act | conditional atomic update `[07]` |
| Order paid with no recorded charge | lost webhook | reconciliation `[07]` |
| Charge with no order | the PSP was called before persisting | persist the intent first |
| Sum of lines ≠ total | only part of it was updated | invariant inside the aggregate + constraint |
| User with no organization | the org was deleted without a cascade | FK with an explicit `ON DELETE` |
| Last owner removed | the rule is missing | constraint or check in the transition |
| Impossible state | loose booleans | state machine |
| Ghost permission | role deleted but memberships still live | FK and periodic review |
| Invoice with a gap in the numbering | `SEQUENCE` with rollback | your own transactional counter |
| Duplicate notification | job retry | dedupe by event |
| Another tenant's data | the filter is missing | scope in the data layer |

**How they are detected:** none of these fire a technical alert. You need **invariant
checks** run periodically, which are the business equivalent of a health check:

```python
async def check_invariants():               # daily cron, alert if something doesn't add up
    mismatches = await db.fetch(
        "SELECT o.id FROM orders o "
        "JOIN order_lines l ON l.order_id = o.id "
        "GROUP BY o.id, o.total_cents "
        "HAVING SUM(l.subtotal_cents) <> o.total_cents")
    if mismatches:
        alert("orders with a mismatched total", ids=[m["id"] for m in mismatches])
```

> **Card** · **When:** every domain with money, inventory or permissions ·
> **Pattern:** invariants verified by a periodic job, with alerting ·
> **Anti-pattern:** trusting that the code will always uphold them ·
> **Limits:** detecting is not preventing; prevention belongs in constraints and transactions ·
> **How it fails:** the discrepancy is discovered months later, in an audit or by a customer ·
> **Decision:** every critical invariant needs a defense (constraint) **and** detection (verification) ·
> **Trade-off:** cost of verifying vs finding out late and being unable to reconstruct what happened ·
> **Related:** reconciliation, audit logs, constraints `[04, 07, 12]`

---

## Interview questions and trade-offs

**Q: How do you model users and organizations in a B2B SaaS?**
Identity, user and membership kept separate; a user in several organizations with different roles.
*Signal:* you say that `user.organization_id` is the decision everyone regrets, and you explain the
migration you avoid by modeling it properly from the start.

**Q: How do you guarantee isolation between tenants?**
`tenant_id` in every table, applied automatically (RLS or a base repository), and explicit leak
tests. *Signal:* you say that relying on every developer to remember it **always fails** and that the defense
has to live in the data layer.

**Q: Why state machines instead of booleans?**
Because they eliminate impossible states, document the business, provide natural points for events and auditing, and
allow atomic transitions. *Signal:* you mention the conditional transition in SQL to stop two
concurrent webhooks from applying it twice.

**Q: Where do you put validation: frontend, API or database?**
In all three, with different purposes: UX, authority and last-resort invariant. *Signal:* you say that the database
is the only layer nobody can bypass, and that is why critical invariants go there as
constraints, not only in the code.

**Q: What do you store in an audit log and how is it different from regular logs?**
Actor, action, resource, before/after and context; append-only, with long retention, designed for auditors and
users, not for debugging. *Signal:* you propose storing it separately with different permissions, because if the
attacker can delete it, it is worthless.

**Core trade-off of this box:** *configurable flexibility vs understandable simplicity*. Every rule
you make configurable multiplies the system's possible states, the combinations to test and the
ways a customer can configure something incoherent. The senior stance is to **hard-code the rules until
a real customer pays for the flexibility**, and then make it explicit and bounded.

---

## Sources

- Eric Evans, *Domain-Driven Design* — entities, value objects and aggregates.
- Vaughn Vernon, [Effective Aggregate Design](https://kalele.io/blog-posts/effective-aggregate-design/) — the sizing rules and referencing by ID.
- [Martin Fowler — State Machine](https://martinfowler.com/bliki/StateMachine.html) and [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [PostgreSQL — Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) for multi-tenant isolation.
