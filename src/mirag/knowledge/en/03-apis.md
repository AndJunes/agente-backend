# 03 · APIs

> An API is a contract with people you cannot pick up the phone and call. The whole design revolves around
> one idea: **once someone depends on you, breaking the contract is expensive.**


**Covers from the syllabus:** `concepts` · `patterns` · `protocols` · `implementations` · `security` · `failure_modes` · `tradeoffs`

---

## API design: the principles that show

**1. Model resources, not actions.** `POST /orders/123/cancel` is more honest than burying it in a generic
`PATCH`. Purist REST would say `PATCH /orders/123 {"status":"cancelled"}`, but **actions with business
side effects** (cancel, refund, publish) deserve their own endpoint: they are auditable, they carry different
permissions, and the contract is explicit. Being pragmatic here is a sign of seniority, not of ignorance.

**2. Consistency over elegance.** `snake_case` or `camelCase`, it doesn't matter which — but **the same one across
the whole API**. Dates always ISO-8601 in UTC (`2026-09-14T22:31:00Z`). IDs always strings (an integer
overflows in JavaScript beyond 2^53). Always plural for collections.

**3. The principle of least surprise.** If `GET /orders` returns `{"data": [...]}`, then `GET /users`
should not return a bare array.

**4. Design for the client, not for your database schema.** Exposing your tables as-is couples your
API to your internal model and stops you from ever refactoring again.

**5. Never break without warning.** What is **not** breaking: adding an optional field to the response, adding
an endpoint, adding an enum value *if the client treats it as unknown*. What **is** breaking:
removing or renaming a field, changing a type, making a parameter required, changing the meaning of something,
changing error codes.

> **Card** · **When:** before writing the first endpoint ·
> **Pattern:** resources for CRUD, explicit action endpoints for business operations ·
> **Anti-pattern:** exposing your tables as-is — it stops you from ever refactoring the database again ·
> **Limits:** once published, the API is a contract whose end of use you do not control ·
> **How it fails:** large numeric IDs get corrupted in JavaScript (above 2^53) ·
> **Decision:** consistency > elegance; the same style across the whole API even if it is not the ideal one ·
> **Trade-off:** REST purity vs clarity for the consumer ·
> **Related:** versioning, error contracts, OpenAPI `[02]`

---

## Versioning

| Strategy | Example | Pros | Cons |
|---|---|---|---|
| In the URL | `/v1/orders` | obvious, cacheable, easy to route | "not pure REST", duplicates routes |
| In a header | `Accept: application/vnd.api.v2+json` | clean URLs | invisible, hard to test in a browser |
| By date | `Stripe-Version: 2026-08-01` | granular, no big jumps | complex to maintain |
| No version | additive evolution | nothing duplicated | forces you to never, ever break |

**The practical answer: `/v1` in the URL** for big changes, and **additive evolution** within v1 for
everything else. It is what almost everyone does, because it is what people understand without documentation.

**The Stripe model** (date-based version pinned per account, with a transformation layer that converts the
modern response to the old format) is the state of the art, but it requires maintaining translation *shims*
for years. Mentioning it in an interview shows you really understand the problem.

**A serious deprecation policy:** announce → return `Deprecation` and `Sunset` headers → measure who is still
using the old version (by client ID, not by guesswork) → warn those clients directly → switch it off.
Never switch off something you cannot measure.

> **Card** · **When:** from day one, even if you only have v1 ·
> **Pattern:** `/v1` for structural changes + additive evolution within the version ·
> **Anti-pattern:** switching off a version without being able to measure who uses it ·
> **Limits:** every live version multiplies the maintenance and testing cost ·
> **How it fails:** adding an enum value breaks clients that do an exhaustive `switch` ·
> **Decision:** is it breaking? Removing/renaming a field, changing a type, making a parameter required: yes ·
> **Trade-off:** freedom to evolve vs stability for consumers ·
> **Related:** deprecation, contract testing `[11]`

---

## Pagination

**Offset / page (`?page=3&limit=20` → `LIMIT 20 OFFSET 40`)**
- ✅ Simple, lets you jump to a specific page, shows the total number of pages.
- ❌ **Degrades brutally**: `OFFSET 100000` forces the DB to read and discard 100,000 rows.
- ❌ **Inconsistent**: if a row is inserted while you paginate, you see repeated items or skip others.

**Cursor / keyset (`?after=eyJpZCI6MTIzfQ`)**
```sql
-- instead of OFFSET, filter by the position of the last item seen
SELECT * FROM orders
WHERE (created_at, id) < ($1, $2)     -- tuple to break ties
ORDER BY created_at DESC, id DESC
LIMIT 20;
```
- ✅ **Constant performance** regardless of depth (it uses the index directly).
- ✅ Stable under inserts.
- ❌ You cannot jump to "page 50" or show the total easily.

**The rule:** cursor by default for feeds, large listings and public APIs. Offset only for back-offices
with little data where the user wants to see "page 7 of 12".

**Details that give away experience:** the cursor must be **opaque** (base64 of a JSON, not the raw ID)
so you can change the implementation; the ordering must be **total** (add `id` as a tie-breaker or you will see
duplicates); and always return `has_more` instead of forcing the client to request an empty page.

> **Card** · **When:** any collection that can grow ·
> **Pattern:** keyset/cursor with total ordering `(created_at, id)` and an opaque base64 cursor ·
> **Anti-pattern:** `OFFSET 100000` — the DB reads and discards 100,000 rows ·
> **Limits:** with a cursor you cannot jump to "page 50" or give the total cheaply ·
> **How it fails:** without an `id` tie-breaker you see duplicated items or skip others on insert ·
> **Decision:** feeds and public APIs → cursor; small back-office → offset ·
> **Trade-off:** navigability (offset) vs constant performance (cursor) ·
> **Related:** indexes, query optimization `[04]`

---

## Filtering, sorting, searching

```
GET /orders?status=paid&created_from=2026-01-01&sort=-created_at&fields=id,total
```

- **Mandatory allowlist** of filterable and sortable fields. Allowing arbitrary `sort` is an invitation to a
  full scan on an unindexed column — it is a trivial DoS.
- **Syntax:** `-field` for descending is the most readable convention. For operators, `price[gte]=100` or
  `filter[price][gte]=100`. Don't invent a mini query language unless you have a very good reason.
- **Sparse fieldsets** (`?fields=`) reduce the payload; useful on mobile.
- **Every filter you expose is an index you are committing to maintain.** Think about it before adding it.

> **Card** · **When:** when exposing listings ·
> **Pattern:** allowlist of filterable and sortable fields ·
> **Anti-pattern:** allowing arbitrary `sort`: a full scan on an unindexed column = trivial DoS ·
> **Limits:** every filter you expose is an index you are committing to maintain ·
> **How it fails:** a client sorts by an unindexed column and saturates the database ·
> **Decision:** if you need real text search, a separate inverted index, not `LIKE '%x%'` ·
> **Trade-off:** flexibility for the client vs predictable performance ·
> **Related:** indexes, full-text search `[04]`

---

## Validation

**Validate at the edge, trust inside.** A single validation point at the entrance (schema), and from there on
the domain works with types that are already valid.

- **Declarative with a schema**: Pydantic (Python), Zod (TS), JSON Schema. You get documentation and consistent
  errors for free.
- **Levels:** syntactic (is it an email?) → semantic (does that `product_id` exist?) → business (is there stock?).
  All three return different codes: 400 / 422 / 409.
- **Allowlist, not denylist.** Reject unknown fields (`additionalProperties: false`) or at least ignore them
  explicitly; never pass them straight to the ORM — that is **mass assignment**, and it is how someone makes
  themselves an administrator by sending `{"role":"admin"}`.
- **Limits on everything:** string length, array size, JSON depth, body size. Without
  limits, a JSON nested 10,000 levels deep takes down your parser.

> **Card** · **When:** at the edge, before touching the domain ·
> **Pattern:** declarative schema (Pydantic/Zod) that rejects unknown fields ·
> **Anti-pattern:** **mass assignment** — passing the body straight to the ORM (`{"role":"admin"}`) ·
> **Limits:** syntactic validation does not replace business invariants or DB constraints ·
> **How it fails:** without size and depth limits, a nested JSON takes down the parser ·
> **Decision:** 400 syntactic · 422 semantic · 409 state conflict ·
> **Trade-off:** strict (breaks lenient clients) vs permissive (silent bugs) ·
> **Related:** error contracts, business rules `[17]`

---

## Serialization

- **JSON** is the default. Traps: it has no date type (use ISO strings), large integers break in
  JS (send IDs as strings), and `NaN`/`Infinity` are not valid.
- **Protobuf / Avro**: binary, compact, with a schema and controlled evolution. For service-to-service and queues.
- **MessagePack / CBOR**: binary JSON, no schema. You gain little over JSON+gzip.
- **Golden rule:** never serialize your domain entity directly. An explicit DTO keeps you from leaking
  `password_hash` the day someone adds that field to the model. **This leak is one of the most common there is.**

> **Card** · **When:** on every response ·
> **Pattern:** an explicit DTO per endpoint, never the domain entity ·
> **Anti-pattern:** serializing the ORM model — the day someone adds `password_hash`, you leak it ·
> **Limits:** JSON has no date type and no safe large integers ·
> **How it fails:** sensitive fields leak when a column is added, and no test notices ·
> **Decision:** binary (Protobuf) between services; JSON facing the world ·
> **Trade-off:** maintaining DTOs is repetitive work, and it is what prevents the leak ·
> **Related:** DTOs, gRPC `[02, 05]`

---

## Error contracts

A good error contract is what separates a usable API from one you hate. Use **RFC 9457**
(*Problem Details for HTTP APIs*, the update of RFC 7807):

```json
{
  "type": "https://api.yourapp.com/errors/insufficient-funds",
  "title": "Insufficient funds",
  "status": 409,
  "detail": "Account 42 has 30.00 EUR and the operation requires 50.00 EUR",
  "instance": "/accounts/42/transfers",
  "request_id": "req_01J8XZ...",
  "errors": [
    {"field": "amount", "code": "max_exceeded", "message": "Maximum 30.00"}
  ]
}
```

**Rules:**
- **A stable, machine-readable error code** (`insufficient-funds`), because the human `message` will
  change and clients will end up parsing strings if you give them nothing else.
- **Return all validation errors at once**, not just the first. The client cannot make 8 round trips.
- **Include the `request_id`** so the user can paste it into the ticket and you can look it up in the logs.
- **Never leak internals**: stack traces, SQL queries, file paths or table names in the
  response are an information leak.

> **Card** · **When:** on the first endpoint, not when there are already twenty ·
> **Pattern:** RFC 9457 with a stable machine-readable code + `request_id` ·
> **Anti-pattern:** returning stack traces, SQL or file paths in the response ·
> **Limits:** human messages change; only the code is contract ·
> **How it fails:** without a stable code, clients parse strings and you break them when you translate the message ·
> **Decision:** return **all** validation errors at once, not the first ·
> **Trade-off:** useful detail for the client vs not leaking internal information ·
> **Related:** status codes, correlation IDs `[02, 12]`

---

## OpenAPI / Swagger

- **Contract-first vs code-first.** Contract-first (you write the YAML, generate server and clients) gives better
  design and lets you work in parallel with the frontend. Code-first (you annotate the code, the spec is generated)
  is faster and **never drifts out of sync**, which is the fatal flaw of poorly maintained contract-first.
- **What you gain with a real spec:** generated SDKs, mocks for the frontend, contract tests,
  living documentation, and request/response validation at the gateway.
- **The litmus test:** if your OpenAPI is not generated or validated in CI, it is out of date. A spec that
  lies is worse than having no spec.

> **Card** · **When:** any API with more than one consumer ·
> **Pattern:** the spec is generated or validated **in CI**; otherwise it lies ·
> **Anti-pattern:** a hand-written YAML nobody updates — worse than having no spec ·
> **Limits:** the spec describes shape, not semantics or business rules ·
> **How it fails:** the frontend implements against an outdated spec and fails at integration ·
> **Decision:** contract-first if teams work in parallel; code-first if the risk is drift ·
> **Trade-off:** careful design (contract-first) vs guaranteed accuracy (code-first) ·
> **Related:** contract testing, SDKs `[11]`

---

## Idempotency

The mechanism that makes retries safe. **Mandatory on any endpoint that moves money
or creates resources.**

```
POST /payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

**Correct implementation:**
1. The **client** generates the key (UUID) and reuses it on every retry of *that same intent*.
2. The server tries to insert the key into a table with `UNIQUE`, **inside the same transaction** as
   the business operation.
3. If the key already exists and the operation finished → return **the stored response**, with the same status.
4. If it exists but is still in progress → `409` or `425`, so the client retries later.
5. Also store a hash of the body: if the same key arrives with a different body, it is a client bug →
   `422`. Execute nothing.
6. Give it a TTL (24h-7 days is typical) and clean up.

**The classic mistake:** storing the key *after* executing. If the process dies halfway, you have charged without
recording the key and the retry charges again. **Same transaction, or it is useless.**

> **Card** · **When:** every endpoint that moves money or creates resources ·
> **Pattern:** client key + `UNIQUE` **in the same transaction** as the operation ·
> **Anti-pattern:** storing the key *after* executing — if the process dies, you charge twice ·
> **Limits:** the key needs a TTL and cleanup; the store grows ·
> **How it fails:** a client that generates a new key on every retry defeats the protection ·
> **Decision:** derive the key from the business intent (`order_id`), not from a fresh UUID ·
> **Trade-off:** one extra write per operation in exchange for safe retries ·
> **Related:** retries, outbox, payments `[07, 08]`

---

## Rate limiting

| Algorithm | How it works | Trade-off |
|---|---|---|
| Fixed window | counter per minute | simple; allows a **double burst** at the window boundary |
| Sliding window log | timestamps of every request | exact; expensive in memory |
| **Sliding window counter** | interpolates two windows | good approximation, cheap — **the sensible default** |
| **Token bucket** | tokens refilled at a fixed rate | allows controlled bursts; the most used in APIs |
| Leaky bucket | output queue at a constant rate | smooths traffic; adds latency |

**Production details:**
- **What do you limit by?** By IP (anonymous), by API key or user (authenticated), by endpoint (the expensive ones
  count for more), and by **cost** in the case of GraphQL or LLMs (not every request costs the same).
- **Distributed:** the counter lives in Redis, not in process memory, or each replica will allow the entire
  limit. `INCR` + `EXPIRE` in a Lua script so it is atomic.
- **Communicate it well:** `429` + `Retry-After` + `RateLimit-Limit`, `RateLimit-Remaining`,
  `RateLimit-Reset` headers (RFC 9238 standardizes them).
- **Fail-open vs fail-closed:** if Redis goes down, do you let everything through or block everything? For abuse
  rate limiting, usually **fail-open** (you would rather over-serve than go down); for billing or
  security limits, fail-closed.

> **Card** · **When:** every public API, and the expensive internal ones ·
> **Pattern:** token bucket in Redis (allows bursts) + `RateLimit-*` headers ·
> **Anti-pattern:** counter in process memory: each replica allows the entire limit ·
> **Limits:** the distributed counter adds a Redis round trip per request ·
> **How it fails:** if Redis goes down, you choose between letting everything through (fail-open) or blocking everything ·
> **Decision:** abuse → fail-open; billing or security → fail-closed ·
> **Trade-off:** protecting the system vs cutting off legitimate clients that grew ·
> **Related:** backpressure, load shedding `[09]`

---

## API keys, gateways, webhooks and SDKs

**API keys**
- Prefixed format (`sk_live_...`, `pk_test_...`): lets you tell the type at a glance and lets GitHub
  detect them in secret scanning.
- **Store only the hash** (like a password). Show the full key exactly once.
- Scopes, zero-downtime rotation (two keys active at the same time), and last_used_at so you can clean up.

**API gateway** — what you centralize there: TLS, authentication, rate limiting, routing, versioning, CORS,
logging/tracing, transformation, and caching. **Beware of the anti-pattern:** putting business logic in the
gateway turns it into an ESB and a single point of failure nobody wants to touch.

**Webhooks (when you are the sender)** — see also `16-integrations.md`:
- **HMAC signature** of the body with a shared secret + **a timestamp inside the signature** to prevent replay.
  The receiver compares with `hmac.compare_digest` (constant-time comparison).
- **At-least-once**: include a stable `event_id` so the receiver can deduplicate.
- **Retries with exponential backoff** and a dead-letter queue after N failures; an endpoint for manual redelivery.
- **Send the event, not just the ID**, but let the receiver confirm with a GET (events can
  arrive out of order, so include a version or timestamp of the resource).
- Short timeout (5-10s): the receiver should respond 200 quickly and process in the background.

**SDKs** — if you publish a public API, generate the SDKs from OpenAPI. By default they should ship with: retries with
backoff and jitter, timeouts, automatic pagination (iterators), typed errors, and automatic idempotency keys
on POSTs.

> **Card** · **When:** when opening the API to third parties ·
> **Pattern:** prefixed keys (`sk_live_`), **stored hashed**, with scopes and overlapping rotation ·
> **Anti-pattern:** putting business logic in the gateway: it turns it into an untouchable ESB ·
> **Limits:** webhooks are at-least-once and arrive out of order ·
> **How it fails:** signing the already-parsed body instead of the raw one breaks the receiver's verification ·
> **Decision:** if the receiver has to react quickly, send the event + allow confirmation with a GET ·
> **Trade-off:** webhooks (real time, uncertain delivery) vs polling (simple, delayed) ·
> **Related:** webhook signatures, integrations `[06, 16]`

---

## Implementation: a complete endpoint from start to finish

Everything above, together, in the endpoint that gets asked about the most: creating a resource idempotently.

```python
from pydantic import BaseModel, Field

class CreateOrder(BaseModel):                 # validation + serialization
    model_config = {"extra": "forbid"}        # rejects unknown fields -> no mass assignment
    product_id: str
    quantity: int = Field(gt=0, le=100)       # the limits, in the schema

class OrderCreated(BaseModel):                # output DTO: never the ORM entity
    id: str
    status: str
    total_cents: int
    currency: str

@router.post("/v1/orders", status_code=201, response_model=OrderCreated)
async def create_order(
    body: CreateOrder,
    idem: str = Header(alias="Idempotency-Key"),      # mandatory: it is a mutating operation
    actor: User = Depends(authenticate),
):
    authorize(actor, "orders:create")                  # explicit authz, per object

    async with uow.transaction() as tx:                # idempotency and effect: SAME transaction
        existing = await tx.reserve_idempotency(idem, hash_body(body), actor.tenant_id)
        if existing:
            return existing.response                   # retry: return what was stored

        order = await service.create(actor, body)      # the domain, knowing nothing about HTTP
        await tx.save_idempotent_response(idem, order)
        return OrderCreated.model_validate(order)
```

**What it does right, in order:** validates with a strict schema → authenticates → **authorizes on the object** →
opens a transaction → reserves the idempotency key and executes **together** → returns an explicit DTO.
Business errors bubble up as typed exceptions and the middleware `[02]` translates them to 409/422 with
the error contract.

> **Card** · **When:** template for any endpoint that creates or modifies ·
> **Pattern:** the handler orchestrates (validate, authorize, run the transaction); the domain does not know about HTTP ·
> **Anti-pattern:** business logic inside the controller, or the ORM leaking into the response ·
> **Limits:** the transaction must be short — no external HTTP calls inside it `[04]` ·
> **How it fails:** if the idempotency record is stored outside the transaction, a crash duplicates the effect ·
> **Decision:** `Idempotency-Key` mandatory on POSTs that mutate money or inventory ·
> **Trade-off:** more ceremony per endpoint in exchange for safe retries ·
> **Related:** idempotency, authorization, unit of work `[04, 05, 06]`

---

## Failure modes: an API in production

| Failure | Cause | Mitigation |
|---|---|---|
| Duplicate resources | the client retried a POST | `Idempotency-Key` |
| Another customer's data | missing tenant/owner filter (**IDOR**) | scoping in the repository `[06, 17]` |
| Slow request that never finishes | no timeout on a dependency | cascading timeouts `[10]` |
| 500 when a field is added | the client does not tolerate unknown fields | additive evolution + tolerant clients |
| The client hangs | huge unpaginated response | hard cap on `limit` |
| You break things by accident | undeclared breaking change | contract testing in CI `[11]` |
| Sensitive field leak | serializing the ORM entity | explicit DTOs |
| Abuse by one client | no per-key rate limiting | token bucket + 429 with `Retry-After` |

> **Card** · **When:** review before exposing an API ·
> **Pattern:** every row of this table should have a test that covers it ·
> **Anti-pattern:** discovering the IDOR through a customer's report ·
> **Limits:** no contract protects you from a semantic change (same field, different meaning) ·
> **How it fails:** silent failures (leak, IDOR) raise no errors: nobody notices ·
> **Decision:** cross-authorization tests are mandatory, not optional ·
> **Trade-off:** strict validation breaks sloppy clients and catches bugs earlier ·
> **Related:** IDOR, contract testing, error contracts `[06, 11, 17]`

---

## Interview questions and trade-offs

**Q: Design the pagination for a feed with millions of items.**
Cursor-based with keyset on an index `(created_at DESC, id DESC)`, an opaque base64 cursor, `has_more` in the
response. *Signal:* you explain why `OFFSET` degrades (the DB reads and discards) and why duplicates
appear when rows are inserted while you paginate.

**Q: How do you guarantee that charging twice is impossible if the client retries?**
An idempotency key generated by the client, inserted with `UNIQUE` **in the same transaction** as the charge, and
a cached response for the retries. *Signal:* you mention the body hash to detect incorrect reuse of
the key, and that the order matters (store before executing, not after).

**Q: How do you version without breaking anyone?**
`/v1` for structural changes, additive evolution within the version, `Deprecation`/`Sunset` headers,
and **per-client usage metrics** before switching anything off. *Signal:* you can tell which changes are breaking and
which are not, and you mention that adding an enum value breaks clients that do an exhaustive `switch`.

**Q: REST or GraphQL for your next public API?**
REST, unless you have very heterogeneous clients. *Signal:* you argue with HTTP cacheability, rate limiting
per request vs per cost, and the fact that GraphQL moves complexity from the client to the server (N+1,
depth limits, persisted queries) that someone has to operate.

**Q: Your public API starts receiving 50× the traffic from one client. What do you do?**
Rate limit per API key with a token bucket in Redis, 429 with `Retry-After`, and a different tier if it is a legitimate
client that grew. *Signal:* you separate abuse from growth, you mention fail-open, and that the limit must be
visible in headers so the client can self-regulate instead of hammering.

**Core trade-off of this box:** *flexibility for the client vs being able to operate and evolve the API*.
Every capability you expose (arbitrary filters, nested queries, dynamic fields) is a performance promise
you will have to keep with indexes, limits and caches for years.

---

## Sources

- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html) (supersedes RFC 7807)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Stripe API reference](https://docs.stripe.com/api) — the benchmark for idempotency and date-based versioning.
- [Google API Design Guide](https://cloud.google.com/apis/design) — resource and error conventions.
- [RFC 9238 — RateLimit header fields](https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-08.html)
