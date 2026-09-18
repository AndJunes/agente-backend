# 10 · Reliability

> The question is not "how do I keep it from failing?" but **"how does it behave when it fails?"**. Every
> sufficiently large system is permanently in a state of partial failure. Reliability is designing so that
> this is not visible.


**Covers from the syllabus:** `concepts` · `patterns` · `failure_modes` · `recovery` · `implementations` · `tradeoffs`

---

## Timeouts

**The most common failure in a backend is not having a timeout.** A call without a timeout does not fail: **it hangs**,
it holds a worker or a pool connection, and propagates the blockage upward until everything is exhausted.

**The ones you have to configure (all of them, explicitly):**
- **Connect timeout** (establishing TCP): short, 1-3s.
- **Read/request timeout** (waiting for the response): based on the service's real p99 + margin.
- **Total / deadline**: the global cap, including retries.
- **Query timeout** in the database (`statement_timeout` in Postgres) and **pool acquisition** timeout.
- **Idle timeout** on idle connections.

**The two rules that come up in interviews:**
1. **The client timeout must be greater than the server's**, or the client gives up while the server
   keeps working (ghost work that consumes resources without benefiting anyone).
2. **Propagate deadlines.** If the user has 200ms left, don't fire an internal call with a 5s timeout.
   gRPC does it natively; in HTTP it is passed as a header and honored. **Without a propagated deadline, your system keeps
   processing requests nobody is going to read.**

**How to choose the value:** look at the dependency's real p99 and add margin. A timeout that is too high does not
protect; one that is too low turns occasional slowness into errors.

> **Card** · **When:** every outbound call, no exceptions ·
> **Pattern:** connect, read, total, query and pool-acquisition timeouts ·
> **Anti-pattern:** trusting the HTTP client's default, which is usually infinite ·
> **Limits:** a timeout does not cancel the work on the other side: it only stops waiting for it ·
> **How it fails:** without a timeout the call **does not fail, it hangs**, and exhausts your workers ·
> **Decision:** the client's greater than the server's, and the server's greater than its dependencies' ·
> **Trade-off:** short timeout (protects, cuts off legitimate slow requests) vs long ·
> **Related:** deadlines, retries, pools `[08, 09]`

---

## Retries

Covered in depth in `08-distributed-systems.md`. The summary you need to be able to state:

- Only what is **transient** and **idempotent**.
- **Exponential backoff + jitter**, always.
- **Retry budget** (e.g. at most 10% of traffic) and **retry in a single layer**.
- Honor `Retry-After`.
- **Combined with a circuit breaker**, or the retries finish off a service that was recovering.

> **Card** · **When:** only for transient errors on idempotent operations ·
> **Pattern:** exponential backoff with jitter, global budget, honor `Retry-After` ·
> **Anti-pattern:** retrying in several layers at once ·
> **Limits:** retrying a permanent error only multiplies the load ·
> **How it fails:** a retry storm that keeps the downed service from recovering ·
> **Decision:** **always** combine it with a circuit breaker ·
> **Trade-off:** success rate vs added load ·
> **Related:** idempotency, breakers `[08]`

---

## Circuit breakers

A switch that **stops calling a service that is down**, so as not to waste resources or make its
situation worse.

```
CLOSED ──(too many failures)──► OPEN ──(time passes)──► HALF-OPEN
   ▲                                                        │
   └──────────(probes succeed)──────────────────────────────┘
                              (they fail) → back to OPEN
```

- **Closed:** everything goes through; failures are counted.
- **Open:** requests are rejected **immediately** without trying (fail fast). This is where you return the degraded
  response.
- **Half-open:** lets a few probe requests through to see whether the other side has recovered.

**Why it really matters:** without a breaker, a slow service consumes all your workers while they wait, and **your**
service goes down because of theirs. With a breaker, you fail fast and keep serving the rest of the functionality.
It is the main defense against **cascading failure**.

**Configuration:** threshold by failure *ratio* (not by absolute count), sliding window, minimum number of
requests before deciding (otherwise 2 failures out of 2 open the circuit for no reason), and open duration.
**One breaker per dependency**, never a global one.

> **Card** · **When:** every external dependency ·
> **Pattern:** one per dependency, by failure ratio and with a minimum number of requests ·
> **Anti-pattern:** a global breaker, or opening after 2 failures out of 2 ·
> **Limits:** it protects against a degraded service, not against one that returns wrong data ·
> **How it fails:** **slow is worse than down** — without a breaker, it consumes all your workers ·
> **Decision:** when open, return a fallback if there is one; otherwise, fail fast ·
> **Trade-off:** cutting off early vs cutting off a service that was recovering ·
> **Related:** timeouts, bulkheads, degradation `[08]`

---

## Bulkheads (watertight compartments)

From a ship's hull: watertight compartments so that a single leak does not sink the whole ship.

- **Separate pools per dependency.** If the recommendations service becomes slow, let it exhaust *its*
  pool of 10 connections, not the 100 workers that also serve checkout.
- **Separate queues and workers per priority.** The nightly batch does not share a queue with payments.
- **Per-tenant isolation** so that one noisy customer does not degrade everyone else (the *noisy
  neighbor* problem).
- **Per-endpoint concurrency limit**: the expensive report-export endpoint cannot consume all the
  capacity.

**The key idea:** bulkheads **limit the blast radius**. Without them, any failure tends to
turn into a total failure.

> **Card** · **When:** when several features share resources ·
> **Pattern:** pools, queues and concurrency limits **separated** by dependency and by criticality ·
> **Anti-pattern:** a single pool shared between checkout and reports ·
> **Limits:** isolating reduces utilization: you reserve capacity that sometimes goes unused ·
> **How it fails:** the monthly report exhausts the pool and takes down the API ·
> **Decision:** isolate by **blast radius**, not by configuration convenience ·
> **Trade-off:** utilization vs isolation ·
> **Related:** connection pools, multi-tenancy `[09, 17]`

---

## Graceful degradation

**Design what you can afford to lose.** Not all features are worth the same:

| Level | Example | If it fails |
|---|---|---|
| Critical | login, checkout, payment | the product is down |
| Important | search, history | degrade (cache, partial results) |
| Optional | recommendations, avatars, analytics | **omit silently** |

**Patterns:**
- **Fallback:** if personalization fails, serve the generic content.
- **Stale cache beats an error** (`stale-if-error`): serving data from 10 minutes ago is infinitely better
  than a 500.
- **Reduced functionality:** the e-commerce site that cannot calculate exact shipping shows an estimate and
  still lets people buy.
- **Queue instead of reject:** if you cannot process now, accept (202) and process later — **only if the
  user can wait**.
- **Feature flags as emergency switches:** turning off the feature that is causing the problem is
  often the fastest mitigation there is.

> **Card** · **When:** when classifying features by criticality ·
> **Pattern:** critical / important / optional, with a defined fallback for each level ·
> **Anti-pattern:** a recommendations outage preventing a purchase from completing ·
> **Limits:** degrading requires product to agree in advance on what can be lost ·
> **How it fails:** nobody decided what is expendable, so everything is critical and everything goes down together ·
> **Decision:** stale cache > error; partial response > blank page ·
> **Trade-off:** full experience vs availability ·
> **Related:** breakers, stale-if-error, feature flags `[09, 14]`

---

## Failover and redundancy

- **Active-passive:** a standby that takes over. Simpler; failover takes time and the standby sits
  idle (and has often never been tested — **a failover that is not rehearsed does not work**).
- **Active-active:** every node serves traffic. Better resource usage and instant failover; requires managing
  consistency and conflicts.
- **Multi-AZ** is the reasonable minimum. **Multi-region** multiplies cost and complexity (replication,
  latency, split-brain) — it is justified by business or regulatory requirements, not by instinct.
- **Split-brain:** two nodes believe they are the primary at the same time and both accept writes. It is prevented with
  quorum and *fencing* (`08-distributed-systems.md`).
- **Eliminate single points of failure**, but remember that redundancy also adds new failure modes
  (the failover mechanism itself can be the cause of the incident).

> **Card** · **When:** when defining the target availability ·
> **Pattern:** multi-AZ at minimum, and **rehearse failover** periodically ·
> **Anti-pattern:** a standby that has never been tested ·
> **Limits:** redundancy adds new failure modes: the mechanism itself can be the cause ·
> **How it fails:** **split-brain** — two nodes think they are primary and both accept writes ·
> **Decision:** multi-region only if the business or regulation demands it ·
> **Trade-off:** availability vs cost and complexity ·
> **Related:** consensus, quorum, replication `[04, 08]`

---

## Backups and disaster recovery

**The two numbers that define everything:**
- **RPO** (Recovery Point Objective): how much data you can afford to lose. An RPO of 1h = backups every hour.
- **RTO** (Recovery Time Objective): how long you can be down. An RTO of 15 min requires different (and more
  expensive) infrastructure than one of 24h.

**Rules:**
- **The 3-2-1 rule:** 3 copies, on 2 different media, 1 off-site.
- **An untested backup is not a backup.** Schedule real periodic restores and **measure how long they take**
  — that is where you find out your RTO was a fantasy.
- **Point-in-time recovery** (with WAL archiving in Postgres) lets you go back to the instant before the
  `DELETE` without a `WHERE`. It is what saves you from human error, which is the most frequent cause.
- **A replica is not a backup.** A `DROP TABLE` replicates in milliseconds. Nor is S3 versioning,
  if the attacker has permissions to delete it.
- **Protect the backups:** encrypted, with separate access and ideally immutable (object lock). Modern
  ransomware goes after the backups first.
- **Document the restore runbook**, and make sure it does not depend on a single person.

> **Card** · **When:** before you have data that matters ·
> **Pattern:** 3-2-1, PITR, scheduled and timed test restores ·
> **Anti-pattern:** treating a read replica as a backup ·
> **Limits:** your real RTO is the one you measured by restoring, not the one you put on the slide ·
> **How it fails:** ransomware goes after the backups first: make them immutable ·
> **Decision:** RPO and RTO are derived from the business and determine the cost ·
> **Trade-off:** frequency and retention vs storage cost ·
> **Related:** data recovery, corruption `[04]`

---

## SLI, SLO, SLA and error budget

- **SLI** (Indicator): the measurement. *"Percentage of requests to `/checkout` that succeed in under 500ms."*
- **SLO** (Objective): the internal target. *"99.9% over 30 days."*
- **SLA** (Agreement): the contract with the customer, with penalties. **Always looser than your SLO**, so
  you have margin before you are in legal breach.

**Error budget:** with a monthly SLO of 99.9%, you have **43.2 minutes** of failure per month. That budget is
a resource you spend:
- If you have some left → you can deploy faster and take on more risk.
- If it runs out → features are frozen and all effort goes to reliability.

**This is what matters culturally:** it turns the "features or stability?" argument into an objective
data point instead of a clash of opinions between product and engineering.

**The nines, to keep in your head:**

| Availability | Downtime per month | Per year |
|---|---|---|
| 99% | 7.2 hours | 3.65 days |
| 99.9% | 43.2 minutes | 8.76 hours |
| 99.99% | 4.3 minutes | 52.6 minutes |
| 99.999% | 26 seconds | 5.26 minutes |

**The senior nuance:** each extra nine multiplies the cost roughly tenfold, and your availability is
bounded by that of your dependencies. If your cloud gives you 99.95%, promising 99.99% is promising something you
do not control. **Choose the SLO based on what the user notices and what the business needs, not out of vanity.**

> **Card** · **When:** when defining what "working" means ·
> **Pattern:** 2-4 critical journeys with measurable SLIs, an internal SLO and a looser SLA ·
> **Anti-pattern:** a 100% SLO — it means you can never deploy ·
> **Limits:** your availability is bounded by that of your dependencies ·
> **How it fails:** alerting on technical thresholds generates noise; you have to alert on burn rate ·
> **Decision:** error budget left? Deploy. Used up? Everything goes to reliability ·
> **Trade-off:** each nine costs ~10× more than the previous one ·
> **Related:** alerts, metrics `[12]`

---

## Incident response

**Roles** (even if there are only a few of you): *Incident Commander* (coordinates and decides, does **not** debug), *Operations*
(executes), *Communications* (keeps customers and the business informed). What matters is that **a single person
coordinates** and that whoever is debugging is not the one answering stakeholders.

**The flow:**
1. **Detect** (alert or report).
2. **Triage**: real impact? how many users? is it getting worse?
3. **Mitigate first, diagnose later.** Rollback, feature flag, scale up, reroute traffic.
   **The goal is to stop the pain, not to understand the cause.** This is the most common mistake good
   engineers make: they get hooked on the puzzle while users suffer.
4. **Communicate** early and often, even if it is just "still investigating". Silence is what makes people angry.
5. **Resolve** and confirm with data that it is over.
6. **Postmortem.**

**Blameless postmortem:** the target is the system, not the person. Nobody "caused" the
incident by typing a command: **the system allowed a command to cause an incident.** If you go looking for
culprits, people hide information and you lose the ability to learn.

A useful postmortem has: a timeline backed by data, quantified impact (users, money, duration), contributing
causes (plural — there is almost never just one), **what went well**, and **actions with an owner and a date**.
A postmortem without assigned actions is a document nobody will read.

> **Card** · **When:** as soon as there are real users ·
> **Pattern:** a coordinator who does not debug, early communication, blameless postmortem ·
> **Anti-pattern:** looking for culprits — people hide information and you stop learning ·
> **Limits:** the process is no substitute for having runbooks and access ready in advance ·
> **How it fails:** a postmortem without actions with an owner and a date changes nothing ·
> **Decision:** always mitigate before understanding ·
> **Trade-off:** process rigor vs agility in small teams ·
> **Related:** incident debugging, alerts `[12]`

---

## Chaos engineering

Injecting failures **on purpose and in a controlled way** to discover weaknesses before reality
discovers them for you.

- **The method:** formulate a hypothesis ("if a replica dies, p99 latency does not rise by more than 50ms"),
  inject the failure within a **small blast radius**, measure, and have a stop button.
- **Typical experiments:** killing instances, adding network latency, causing packet loss, filling
  disks, taking down an entire AZ, degrading an external dependency.
- **Prerequisite:** good observability and the ability to stop the experiment. Doing chaos without being able to measure
  what happens is just breaking things.
- **Start in staging**, and move to production only once the team has confidence and controls.
- **"Game days"** (incident drills) deliver almost all the value with much less risk: you practice the
  process, and you discover that the runbook is out of date and nobody knows where the backups are.

> **Card** · **When:** once you already have observability and confidence ·
> **Pattern:** explicit hypothesis, small blast radius, stop button ·
> **Anti-pattern:** breaking things in production without being able to measure what happens ·
> **Limits:** it requires prior maturity; without metrics it is just vandalism ·
> **How it fails:** the experiment causes a real incident due to lack of containment ·
> **Decision:** start with **game days** (drills): almost all the value, much less risk ·
> **Trade-off:** controlled risk today vs uncontrolled surprise tomorrow ·
> **Related:** failover, runbooks, observability `[12]`

---

## Implementation: health checks and graceful shutdown

The two pieces every service needs and that almost nobody gets right.

```python
@app.get("/health/live")          # LIVENESS: is the process responding? NOTHING external here.
async def live():
    return {"status": "ok"}

@app.get("/health/ready")         # READINESS: can I serve traffic?
async def ready():
    dependencies = {}
    try:
        await asyncio.wait_for(db.execute("SELECT 1"), timeout=1.0)
        dependencies["db"] = "ok"
    except Exception:
        dependencies["db"] = "fail"
        return JSONResponse({"status": "not_ready", "deps": dependencies}, 503)

    try:                          # SOFT dependency: if it fails, we are still ready
        await asyncio.wait_for(cache.ping(), timeout=0.5)
        dependencies["cache"] = "ok"
    except Exception:
        dependencies["cache"] = "degraded"

    if shutting_down.is_set():    # during shutdown we say "no" BEFORE closing
        return JSONResponse({"status": "draining"}, 503)
    return {"status": "ready", "deps": dependencies}
```

**The mistake that causes incidents:** putting the database in the *liveness* probe. If the DB blips, Kubernetes
**restarts all your pods at once** and turns a degradation into a total outage.

**Graceful shutdown** — the reason every deployment produces 502s if you don't do it:

```python
shutting_down = asyncio.Event()

async def shutdown(sig):
    shutting_down.set()           # 1) readiness switches to 503
    await asyncio.sleep(5)        # 2) margin for the LB to stop sending us traffic
    await server.shutdown()       # 3) finish the in-flight requests
    await db.close(); await broker.close()   # 4) close resources

loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown(signal.SIGTERM)))
```

Order matters: the load balancer takes a few seconds to find out that you are no longer ready. If you shut down
before that margin, you receive traffic you can no longer serve.

> **Card** · **When:** every service, before the first deployment ·
> **Pattern:** liveness without dependencies · readiness with hard and soft dependencies kept separate · drain before shutting down ·
> **Anti-pattern:** a single `/health` used for both things ·
> **Limits:** Kubernetes sends SIGTERM and removes the pod from the Service **at the same time**, with no guaranteed order ·
> **How it fails:** without a draining margin, every deployment produces 502s visible to the user ·
> **Decision:** does the broken dependency prevent serving? Hard. Does it only degrade? Soft ·
> **Trade-off:** strict readiness (fewer errors served) vs apparent availability ·
> **Related:** probes, deployments, load balancing `[09, 13, 14]`

---

## Implementation: circuit breaker and cascading timeouts

```python
class CircuitBreaker:
    def __init__(self, threshold=0.5, minimum=20, window=60, open_duration=30):
        self.threshold, self.minimum = threshold, minimum  # failure ratio, not absolute count
        self.window, self.open_duration = window, open_duration
        self.state, self.opened_at = "closed", None
        self.events = deque()                              # (timestamp, ok?)

    async def call(self, fn, *, fallback=None):
        if self.state == "open":
            if time.monotonic() - self.opened_at < self.open_duration:
                if fallback is not None:
                    return fallback()                       # degrade, don't wait
                raise CircuitOpen()                         # fail fast
            self.state = "half_open"                        # time to probe

        try:
            r = await fn()
        except Exception:
            self._record(False)
            if self.state == "half_open":
                self._open()
            raise
        self._record(True)
        if self.state == "half_open":
            self.state, self.events = "closed", deque()
        return r

    def _record(self, ok):
        now = time.monotonic()
        self.events.append((now, ok))
        while self.events and now - self.events[0][0] > self.window:
            self.events.popleft()
        if len(self.events) >= self.minimum:
            failures = sum(1 for _, o in self.events if not o) / len(self.events)
            if failures >= self.threshold:
                self._open()

    def _open(self):
        self.state, self.opened_at = "open", time.monotonic()
```

**The `minimum` is what almost everyone forgets:** without it, 2 failures out of 2 requests open the circuit
without any statistical evidence.

**Propagated deadline** — so that work does not carry on when nobody is waiting for it anymore:

```python
async def handle(request):
    budget = float(request.headers.get("X-Deadline-Ms", 3000)) / 1000
    start = time.monotonic()

    def remaining():
        return max(0.0, budget - (time.monotonic() - start))

    profile = await asyncio.wait_for(service_a.get(), timeout=min(1.0, remaining()))
    if remaining() < 0.2:                      # no time left: degrade instead of failing
        return partial_response(profile)
    extras = await asyncio.wait_for(service_b.get(), timeout=remaining())
    return full_response(profile, extras)
```

> **Card** · **When:** every call to an external dependency or to another service ·
> **Pattern:** one breaker **per dependency**, with ratio, window and a minimum number of requests ·
> **Anti-pattern:** a global breaker, or opening on an absolute number of failures ·
> **Limits:** the breaker cannot tell "the service is unhealthy" from "this particular request is bad" ·
> **How it fails:** without a breaker, a **slow** (not down) service consumes all your workers ·
> **Decision:** if there is a reasonable fallback, degrade; if not, fail fast ·
> **Trade-off:** opening early (you protect yourself) vs opening late (you don't cut off a service that was doing fine) ·
> **Related:** retries, bulkheads, degradation `[08, 09]`

---

## Incident debugging

**The right order, and the discipline not to skip steps:**

1. **Is there real impact?** How many users, which functionality, is it getting worse?
2. **Mitigate.** Rollback, feature flag, scale up, reroute. **Before understanding.**
3. **What changed?** Deployment, migration, configuration, feature flag, traffic spike, a vendor,
   an expired certificate, a full disk. **90% of incidents have a recent change behind them.**
4. **Narrow it down by layers:** does it affect everyone or a subset (a region, a tenant, a version)?
   all endpoints or just one? does it start in your service or in a dependency?
5. **Metrics → traces → logs → profiler.** From the aggregate to the specific.
6. **Verify the hypothesis** before applying the fix. Under pressure people change three things at once and
   then nobody knows which one worked.

**The usual suspects, by actual frequency:** full disk · expired certificate · rotated secret
that someone did not update · exhausted connection pool · OOM and restarts · unreviewed configuration change ·
a colliding cron job · a degraded external provider · a query that lost its index as the
table grew · thundering herd after the cache went down.

**What NOT to do:** restart without looking at anything (you destroy the evidence), touch production by hand
without recording it, or investigate alone without communicating.

> **Card** · **When:** from minute one of any incident ·
> **Pattern:** mitigate → communicate → narrow down → diagnose → postmortem ·
> **Anti-pattern:** getting hooked on the technical puzzle while users are still affected ·
> **Limits:** mitigating quickly sometimes destroys the evidence needed to understand ·
> **How it fails:** without a coordinator, three people touch production at the same time ·
> **Decision:** declare the incident early; over-declaring is cheap, under-declaring is very expensive ·
> **Trade-off:** mitigation speed vs preserving evidence ·
> **Related:** observability, rollback, postmortem `[12, 14]`

---

## Data recovery

- **Restore with backup + PITR** to the instant before the error.
- **The most common case is human:** an `UPDATE` or `DELETE` without a `WHERE`. Cheap preventive measures:
  always run inside an explicit transaction, check first with a `SELECT` using the same
  condition, and **forbid direct writes to production** except through a reviewed procedure.
- **Partial restore:** restore the backup to a separate instance and copy over only the affected rows,
  instead of rolling back the entire database (which would discard everything that happened afterwards).
- **Measure the real restore time** with a drill. It is the only way to know whether your RTO is real.
- **Afterwards, reconcile:** external systems (payments, emails sent, messages published) **do not
  roll back along with your database**. Restoring can leave you inconsistent with the outside world.

> **Card** · **When:** after data loss or corruption ·
> **Pattern:** restore in parallel and copy what was affected, don't roll back wholesale ·
> **Anti-pattern:** restoring on top of production without assessing what gets lost along the way ·
> **Limits:** PITR only reaches as far back as your WAL retention ·
> **How it fails:** the postmortem blames the person instead of asking why the system allowed it ·
> **Decision:** is the damage contained? Partial restore. Is it total? Full restore ·
> **Trade-off:** going back (you lose everything after) vs repairing live (slower, riskier) ·
> **Related:** backups, corruption, postmortem `[04]`

---

## Interview questions and trade-offs

**Q: A service you depend on becomes slow (it doesn't fail, it takes 30s). What happens in your system?**
Without a timeout or a breaker, your workers are used up waiting and **you go down too**. With an aggressive timeout, a breaker
and a fallback, you fail fast and degrade that feature. *Signal:* you point out that **slow is worse than down**,
because a service that is down fails fast while a slow one consumes your resources.

**Q: What is an error budget and what is it for?**
The failure margin your SLO allows. It is used to decide objectively when to prioritize reliability over
features. *Signal:* you explain that it turns a political argument into a data point, and that a 100% SLO is a
sign of immaturity: it means you can never deploy.

**Q: Is a read replica a backup?**
No. It replicates the mistakes too: a `DROP TABLE` reaches the replica instantly. *Signal:* you mention PITR
to go back to an earlier point, and that what really matters is having **tested** the restore and
timed the RTO.

**Q: How do you prevent a cascading failure?**
Timeouts everywhere, circuit breakers per dependency, bulkheads to isolate pools, load shedding and
graceful degradation. *Signal:* you mention the retry spiral and that you should retry in a single layer
with a limited budget.

**Q: What do you do first in an incident?**
Mitigate. Rollback or feature flag, and then investigate calmly. *Signal:* you say explicitly that understanding the
root cause **is not the goal during the incident**, and that the first step is to declare the incident and assign a
coordinator.

**Core trade-off of this box:** *reliability vs cost and speed*. Each nine costs roughly ten
times more than the previous one and slows down delivery. The senior decision is to choose the level **the business
needs**, measure it with SLOs, and spend the error budget deliberately instead of chasing a perfection
that nobody is paying for.

---

## Sources

- [Google SRE Book](https://sre.google/sre-book/table-of-contents/) and [SRE Workbook](https://sre.google/workbook/table-of-contents/) — SLOs, error budgets, blameless postmortems.
- [AWS Builders' Library](https://aws.amazon.com/builders-library/) — timeouts, retries, circuit breakers and isolation in practice.
- Michael Nygard, *Release It!* — the origin of circuit breaker and bulkhead as named patterns.
- [Principles of Chaos Engineering](https://principlesofchaos.org/)
