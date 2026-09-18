# 11 · Testing

> Tests aren't there to "have coverage". They're there so you can **change the code without fear**. Any
> test that doesn't increase your confidence when deploying is cost with no benefit.


**Covers from the syllabus:** `concepts` · `unit` · `integration` · `e2e` · `contract` · `load` · `implementations` · `failure_scenarios`

---

## The pyramid (and why it's disputed)

```
        /\        E2E            few, slow, brittle, very high confidence
       /  \       Integration    the ones that add the most value in backend
      /____\      Unit           many, fast, cheap
```

**The senior nuance:** the classic pyramid comes from an era when E2E tests were extremely expensive. Today, with testcontainers and
databases in Docker, **integration tests are fast and they're the ones that give the most confidence in backend**
— because 90% of real bugs live at the boundaries (badly written SQL, serialization, transactions,
configuration), not in pure logic.

The shape many people advocate today is the **testing trophy**: a few unit tests (only for complex logic),
**lots of integration tests**, a handful of E2E tests, and a wide base of static analysis (types and linters), which
is the cheapest test there is.

> **Card** · **When:** deciding where to invest testing effort ·
> **Pattern:** testing trophy — a static-analysis base, lots of integration tests, few E2E ·
> **Anti-pattern:** thousands of unit tests with mocks that don't exercise a single real boundary ·
> **Limits:** the classic pyramid dates from when E2E tests were extremely expensive ·
> **How it fails:** green suite and broken production, because nothing ever tested the real SQL ·
> **Decision:** in backend, bugs live at the boundaries: prioritize integration ·
> **Trade-off:** feedback speed vs confidence ·
> **Related:** testcontainers, contract testing `[04]`

---

## Unit tests

They test an isolated unit, with no I/O. They should run in milliseconds.

```python
def test_price_with_volume_discount():
    # Arrange
    cart = Cart([Line(product="A", units=10, price=Money(100, "EUR"))])
    # Act
    total = calculate_total(cart, discounts=[VolumeDiscount(minimum=10, percentage=10)])
    # Assert
    assert total == Money(900, "EUR")
```

**Rules:**
- **Arrange / Act / Assert.** A test that doesn't read as three blocks is doing too much.
- **Test behavior, not implementation.** If renaming a private method breaks 40 tests, those tests
  are coupled to the *how*, not the *what*. They're a brake on refactoring, which is exactly the opposite of their job.
- **One reason to fail per test.** The name should say what broke without opening the file.
- **Deterministic.** No uncontrolled `now()`, `random()` or network: inject a clock and a seed.
- **Where they really pay off:** business logic with many branches — price calculation, taxes, permission
  rules, state machines. For a controller that just calls a service, a unit test with three
  mocks proves nothing useful.

> **Card** · **When:** business logic with many branches ·
> **Pattern:** Arrange/Act/Assert, deterministic, one reason to fail per test ·
> **Anti-pattern:** testing implementation — renaming a private method breaks 40 tests ·
> **Limits:** they catch nothing about integration, serialization or SQL ·
> **How it fails:** tests coupled to structure block refactoring, which is exactly what they were supposed to enable ·
> **Decision:** inject a clock and a seed; never call `now()` or `random()` directly ·
> **Trade-off:** isolation (fast) vs realism ·
> **Related:** property-based, test doubles `[01]`

---

## Integration tests

They test your code **against the real dependencies**: database, cache, broker.

```python
# testcontainers: real Postgres, ephemeral, identical to production
@pytest.fixture(scope="session")
def db():
    with PostgresContainer("postgres:17") as pg:
        apply_migrations(pg.get_connection_url())
        yield pg

def test_order_is_not_duplicated_with_the_same_idempotency_key(db):
    create_order(db, key="abc", amount=100)
    create_order(db, key="abc", amount=100)           # retry
    assert count_orders(db) == 1                      # and there was only one charge
```

**Why they're the most valuable in backend:** they verify what a mock never verifies — that the SQL is valid,
that the unique index exists, that the transaction rolls back, that the ORM generates what you think it does, that the
migration runs.

**Isolation between tests:** each test inside a transaction that's rolled back at the end (fast), or truncate
tables between tests (slower but more realistic). **Never** depend on execution order or on state left behind by another
test: it's the main cause of suites that only fail in CI.

> **Card** · **When:** anything that crosses a boundary (DB, HTTP, queue) ·
> **Pattern:** testcontainers with the **same engine and version** as production, applying the real migrations ·
> **Anti-pattern:** SQLite to test what runs on Postgres in production ·
> **Limits:** slower; state has to be isolated between tests ·
> **How it fails:** dependence on execution order → green locally, red in CI ·
> **Decision:** a transaction rolled back per test, or truncation between tests ·
> **Trade-off:** seconds per test in exchange for catching the bugs that actually happen ·
> **Related:** migrations, fixtures `[04]`

---

## E2E tests

The whole system: real HTTP, real database, simulated external services.

- **Few of them, and only for the critical business paths**: sign-up, login, checkout, the action that makes money.
- **They're brittle and slow.** Every E2E test you add is a toll you pay on every PR, forever.
- **The rule:** if an E2E test fails, it has to mean "the product is broken", not "a selector changed".
- **Data:** each run creates its own with unique identifiers, and cleans up. Relying on a preloaded
  database is how E2E tests start failing at random.

> **Card** · **When:** only the paths that pay the bills ·
> **Pattern:** few of them, with their own data per run and cleanup at the end ·
> **Anti-pattern:** covering all functionality with E2E tests ·
> **Limits:** slow and brittle; each one is a toll on every PR, forever ·
> **How it fails:** they fail because a selector changed and people start ignoring the reds ·
> **Decision:** if an E2E test fails, it must mean "the product is broken" ·
> **Trade-off:** maximum confidence vs maximum maintenance cost ·
> **Related:** flaky tests, test data `[14]`

---

## Contract testing

The problem it solves: service A mocks B with what it *believes* B returns. B changes. A's tests
stay green. Production breaks. **Mocks don't notice that the other side changed.**

- **Consumer-driven contracts (Pact):** the consumer declares what it expects; that contract is verified **against
  the real provider** in the provider's pipeline. If the provider breaks something, its own CI goes red.
- **Schema-based:** validate against the shared OpenAPI/Protobuf on both sides.
- **When it matters:** several services and several teams. In a monolith you don't need it; the compiler already
  does it.

> **Card** · **When:** several services and several teams ·
> **Pattern:** the consumer declares expectations and they're verified in the **provider's CI** ·
> **Anti-pattern:** mocks of the other service that nobody updates when it changes ·
> **Limits:** it verifies shape, not semantics ·
> **How it fails:** the provider changes, the consumer's tests stay green, production breaks ·
> **Decision:** in a monolith you don't need it: the compiler already does it ·
> **Trade-off:** extra infrastructure vs catching breakages before deployment ·
> **Related:** OpenAPI, event schemas `[03, 08]`

---

## API testing

- **Test the contract, not just the happy path:** status codes, error shape, validation,
  authentication **and authorization** (user A must not be able to read B's resource — IDOR tests
  should be mandatory, see `06-security.md`).
- **Snapshot/golden tests** of responses to catch unintended changes to the contract.
- **Validation against the OpenAPI schema** in the tests: if the response doesn't match the spec, it fails. It's the
  only way to keep the spec from lying.
- **Edge cases:** empty payload, extra fields, wrong types, unicode, huge numbers, giant
  arrays, pagination at the boundary.

> **Card** · **When:** every exposed API ·
> **Pattern:** validate responses **against the OpenAPI schema** inside the tests ·
> **Anti-pattern:** testing only the 200 and forgetting the error contracts ·
> **Limits:** a snapshot detects changes but doesn't tell you whether they're correct ·
> **How it fails:** the spec drifts out of sync and nobody notices until a client breaks ·
> **Decision:** cross-user authorization tests are mandatory ·
> **Trade-off:** contract rigidity vs freedom to evolve ·
> **Related:** error contracts, IDOR `[03, 06]`

---

## Load testing and stress testing

They're not the same thing, and confusing them shows:

| Type | Question it answers |
|---|---|
| **Load** | does it handle the expected load at the target latency? |
| **Stress** | where does it break, and **how** does it break? |
| **Soak** (endurance) | does it survive 24h? (memory leaks, unclosed connections, disks filling up) |
| **Spike** | does it survive a sudden spike? (autoscaling, queues, load shedding) |

**Tools:** k6 (JS, very good DX), Locust (Python), Gatling, wrk/vegeta for something quick.

**How to do it right:**
- **Define the target up front:** "1,000 RPS with p99 < 300ms and under 0.1% errors". Without a target number,
  the test has no conclusion.
- **Realistic load:** endpoint mix proportions like production, data with real cardinality (a test
  that always queries the same ID gets a 100% cache hit rate and measures nothing).
- **Warm up first** (JIT, caches, pools) and measure at steady state.
- **Watch the system, not just the client.** The value is in seeing **what** saturates first: CPU, connection
  pool, memory, the DB, an external service.
- **What you're looking for in stress:** graceful degradation (load shedding, 429) instead of collapse. A system that
  returns 429 to 10% of requests at 2× load is healthy; one that runs out of memory and restarts is not.

> **Card** · **When:** before a launch or an anticipated peak ·
> **Pattern:** a numeric target set in advance, realistic load, warm up and measure at steady state ·
> **Anti-pattern:** always querying the same ID (100% cache hits: you measure nothing) ·
> **Limits:** the test environment rarely matches production ·
> **How it fails:** you measure only from the client and can't see **which resource** saturates first ·
> **Decision:** in stress you're looking for it to **degrade gracefully** (429), not to hold up ·
> **Trade-off:** realism vs the cost of setting up the environment ·
> **Related:** backpressure, capacity planning `[09, 19]`

---

## Mocks, stubs, fakes and fixtures

| Double | What it is |
|---|---|
| **Dummy** | filler that isn't used |
| **Stub** | returns canned responses |
| **Spy** | a stub that also records how it was called |
| **Mock** | expects specific calls and fails if they don't happen |
| **Fake** | a real but simplified implementation (an in-memory repository) |

**The practical rules:**
- **Mock the system's boundaries** (external HTTP, payment gateway, email sending), **not your own
  internal code**. Mocking your own classes couples the test to the structure and stops you from refactoring.
- **Prefer fakes over mocks.** An in-memory repository produces tests that are more readable and less brittle than
  five `when(...).thenReturn(...)`.
- **For external HTTP:** record/replay (VCR) or a local server (WireMock, `responses`). And **a separate contract
  test** that periodically verifies the real provider still behaves the same way.
- **Fixtures:** use *factories/builders* with sensible defaults instead of a giant shared
  JSON. `create_user(role="admin")` reads well; a 200-line fixture used by 40 tests turns into
  coupling that nobody dares to touch.

> **Card** · **When:** isolating dependencies in tests ·
> **Pattern:** mock the **system's boundaries**; prefer fakes over mocks ·
> **Anti-pattern:** mocking your own internal classes ·
> **Limits:** a mock never finds out that the other side changed ·
> **How it fails:** five `when(...).thenReturn(...)` that only verify the test knows the implementation ·
> **Decision:** factories with defaults, not a giant shared JSON ·
> **Trade-off:** speed and isolation vs fidelity ·
> **Related:** contract testing, DI `[05]`

---

## Test databases

- **Testcontainers** is the standard: a real, ephemeral Postgres per suite. It eliminates the whole class of
  "it passed on SQLite" bugs.
- **Never use SQLite for testing if you use Postgres in production.** They differ in types, transactions,
  concurrency and SQL. The tests pass and production fails.
- **Apply the real migrations** in the setup: that way you test the migrations too.
- **Parallelism:** one database or one schema per worker.

> **Card** · **When:** any test that touches persistence ·
> **Pattern:** one ephemeral database per suite, with the real migrations applied ·
> **Anti-pattern:** a shared, preloaded database that nobody knows how it was generated ·
> **Limits:** parallelism requires one database or one schema per worker ·
> **How it fails:** tests that depend on data left behind by another test ·
> **Decision:** applying migrations in the setup tests the migrations too ·
> **Trade-off:** startup time vs fidelity and isolation ·
> **Related:** migrations, fixtures `[04]`

---

## Property-based testing

Instead of examples, you declare **properties that must always hold** and the library (Hypothesis, fast-check)
generates hundreds of cases and **shrinks the counterexample to the minimum**.

```python
@given(st.lists(st.integers()))
def test_sorting_is_idempotent(xs):
    assert sort(sort(xs)) == sort(xs)
```

**Typical properties in backend:** round-trip (`parse(serialize(x)) == x`), invariants (the total is never
negative), idempotency (applying twice = applying once), and equivalence with a naive but obviously correct
implementation.

**Where it shines:** parsers, serialization, financial calculations, state machines. It finds the edge
cases nobody would have written by hand (the empty list, zero, the weird unicode, the overflow).

> **Card** · **When:** parsers, serialization, financial calculation, state machines ·
> **Pattern:** invariants — round-trip, idempotency, equivalence with a naive implementation ·
> **Anti-pattern:** using it for logic with lots of side effects ·
> **Limits:** it generates cases; it doesn't guarantee correctness ·
> **How it fails:** it finds a counterexample that turns out to be an undocumented requirement ·
> **Decision:** if the bug would be silent and would corrupt data, invest here ·
> **Trade-off:** slower and non-deterministic vs finds what nobody would have written ·
> **Related:** fundamentals, fuzzing `[01]`

---

## Coverage and the overall strategy

- **Coverage measures what was executed, not what was verified.** A test with no asserts gives you 100% coverage.
- A minimum (60-80%) avoids completely dark areas; chasing 100% produces junk tests for getters.
- **Mutation testing** does measure real quality: it introduces bugs on purpose and checks whether any test
  catches them. Expensive, but revealing on critical modules.
- **Coverage of what matters > global coverage.** The billing module deserves 95%; the date-formatting one,
  whatever it ends up with.

**What to do when a bug shows up:** first write a test that reproduces it and fails, then fix it.
That way the test proves the fix works **and** protects you from regression. It's the most cost-effective way to
build a suite: every test corresponds to a real failure that actually happened.

> **Card** · **When:** setting the repo's quality policy ·
> **Pattern:** high coverage where failure is expensive; mutation testing on critical modules ·
> **Anti-pattern:** chasing 100% — it produces junk tests for getters ·
> **Limits:** coverage measures what was **executed**, not what was verified ·
> **How it fails:** a test with no asserts gives 100% coverage ·
> **Decision:** when a bug appears, first a test that reproduces it and fails ·
> **Trade-off:** suite run time vs protection against regressions ·
> **Related:** flaky tests, CI `[14]`

---

## Failure scenarios and adversarial cases

What separates a suite that gives confidence from one that only gives coverage: **testing what goes wrong.**

**By category, what you need to have tested:**

| Category | Cases that must exist |
|---|---|
| **Boundaries** | empty, one, the maximum, the maximum + 1, zero, negative, null |
| **Text** | unicode, emoji, RTL, 10,000-character string, empty string, whitespace only |
| **Numbers** | 0, negatives, decimals with many digits, overflow, currencies without decimals `[07]` |
| **Time** | DST changes, leap year, time zones, end of month, future dates |
| **Concurrency** | two simultaneous requests on the same resource `[01]` |
| **Authorization** | user A trying to read, edit and delete user B's data |
| **Retries** | the same request twice with the same idempotency key |
| **Dependencies** | the provider returns 500, times out, returns a malformed response, or takes 30s |
| **Data** | a row that no longer exists, a broken FK, a null field that "never is" |

**The adversarial tests that should be mandatory in backend:**

```python
def test_user_a_cannot_read_user_b_data(client, user_a, user_b):
    order_b = create_order(user_b)
    r = client.get(f"/v1/orders/{order_b.id}", headers=auth(user_a))
    assert r.status_code == 404            # 404, not 403: we don't reveal that it exists [06]

def test_same_payment_with_same_key_charges_only_once(client, user):
    headers = {**auth(user), "Idempotency-Key": "abc-123"}
    r1 = client.post("/v1/payments", json={"order_id": "p1"}, headers=headers)
    r2 = client.post("/v1/payments", json={"order_id": "p1"}, headers=headers)
    assert r1.json()["id"] == r2.json()["id"]
    assert count_charges_at_psp() == 1

def test_cannot_escalate_privileges_via_the_body(client, user):
    client.patch("/v1/users/me", json={"role": "admin"}, headers=auth(user))
    assert reload(user).role == "member"         # mass assignment [03]

def test_if_the_provider_is_too_slow_we_degrade(client, slow_provider):
    r = client.get("/v1/product/1")              # recommendations take 30s
    assert r.status_code == 200                  # the page still works
    assert r.json()["recommendations"] == []     # degraded, not down [10]
```

**Fuzzing** for parsers and endpoints that receive external data: generate random and malformed inputs
and check that they **never** cause a 500 or a hang. 4xx responses are fine; 5xx responses are bugs.

> **Card** · **When:** on every public endpoint and every integration ·
> **Pattern:** a table of failure categories, and at least one test per row ·
> **Anti-pattern:** testing only the happy path in the provider's sandbox ·
> **Limits:** you can't enumerate every adversarial case; fuzzing covers what you didn't imagine ·
> **How it fails:** IDOR and field leaks produce no errors: they pass every happy-path test ·
> **Decision:** if the failure would be **silent**, the test is mandatory ·
> **Trade-off:** suite run time vs entire classes of bugs caught ·
> **Related:** IDOR, idempotency, degradation `[03, 06, 10]`

---

## Interview questions and trade-offs

**Q: How much test coverage should a project have?**
Enough to deploy without fear, and high in the critical code. *Signal:* you explain why the metric is
misleading (executed ≠ verified) and mention mutation testing as a real way to measure quality.

**Q: Unit or integration tests in backend?**
Integration for almost everything that crosses a boundary (DB, HTTP, queues), unit tests for complex business
logic. *Signal:* you argue that real backend bugs live at the boundaries and that testcontainers
removed the historical excuse that integration tests are slow.

**Q: Your suite has tests that fail at random. What do you do?**
Treat them as high-priority bugs: isolate them, fix the cause (ordering, shared state, time, network,
concurrency) and quarantine them in the meantime. *Signal:* you say the real cost of a flaky test isn't the
time, it's that **people stop believing the reds**, and from then on the suite no longer protects anything.

**Q: How do you test that your Stripe integration works?**
Tests with the library mocked for the logic, plus the provider's test environment for the real flow, plus
tests of your webhook handler with signed sample events. *Signal:* you mention testing the webhook's
**idempotency and duplicates**, which is where the real bugs are (`07-payments.md`).

**Q: What is contract testing and when do you need it?**
Verifying that the consumer's expectations hold against the real provider, in the provider's CI.
You need it with several services and several teams. *Signal:* you explain the concrete failure it prevents — mocks
that silently go stale — because that's the pattern's reason for existing.

**Core trade-off of this box:** *confidence vs feedback speed*. The more real the test, the more
confidence it gives and the longer it takes. Designing a good suite comes down to **putting each check at the cheapest
level that still catches it**, and reserving the expensive levels for the paths that really pay the bills.

---

## Sources

- Martin Fowler, [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) and [Test Double](https://martinfowler.com/bliki/TestDouble.html)
- Kent C. Dodds, [The Testing Trophy](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- [Testcontainers](https://testcontainers.com/) · [Hypothesis](https://hypothesis.readthedocs.io/) · [k6](https://k6.io/docs/)
- [Pact — consumer-driven contract testing](https://docs.pact.io/)
