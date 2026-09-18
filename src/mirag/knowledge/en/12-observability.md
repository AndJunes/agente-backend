# 12 · Observability

> Monitoring answers the questions you **already knew** you were going to ask (is it down?). Observability lets you
> answer the ones you **didn't anticipate** (why does it only fail for users on this plan on iOS?).
> The difference is the cardinality and the context you keep.


**Covers from the syllabus:** `logging` · `metrics` · `tracing` · `alerting` · `dashboards` · `implementations` · `failure_modes`

---

## The three pillars (and the fourth)

| | What it is | Cost | Answers |
|---|---|---|---|
| **Logs** | discrete events with context | high (volume) | what exactly happened here? |
| **Metrics** | aggregated numeric time series | low | how is the system doing overall? |
| **Traces** | the path of a request through the services | medium | where did the time go? |
| **Profiles** | where CPU/memory is spent in the code | medium | which specific function is costly? |

**The rule of use:** **metrics** tell you something is wrong and fire the alert. **Traces** tell you
where. **Logs** tell you exactly what happened. *Continuous profiling* tells you which line. Using them in that
order is what separates a 10-minute investigation from a 4-hour one.

> **Card** · **When:** designing the observability of a service ·
> **Pattern:** metrics to alert → traces to locate → logs for the detail → profiler for the line ·
> **Anti-pattern:** trying to investigate everything with `grep` over logs ·
> **Limits:** all three cost money and grow with traffic ·
> **How it fails:** without correlation between them, each pillar is an island and the investigation drags on for hours ·
> **Decision:** the `trace_id` is what ties them together; without it you have three disconnected tools ·
> **Trade-off:** granularity vs cost ·
> **Related:** correlation IDs, tracing `[10]`

---

## OpenTelemetry

In 2026 it is the de facto standard: **it graduated from the CNCF in May 2026**, the same status as Kubernetes and
Prometheus. Traces, metrics and logs are stable in the main SDKs; *profiling* entered public alpha
in March 2026 and is not yet recommended for critical workloads.

**Why it matters:** you instrument **once** with a vendor-neutral API and choose the backend later
(Grafana, Datadog, Honeycomb, Jaeger…). It removes observability vendor lock-in, which used to be
every vendor's sales pitch.

**Architecture:**
```
Your app (OTel SDK) → OTel Collector → one or more backends
                        ↑
            this is where you filter, sample, enrich and reroute
            without touching or redeploying the application
```

- **Auto-instrumentation** for frameworks, HTTP clients and DB drivers: it gives you 80% for free.
- **Manual instrumentation** for what matters in your domain (business spans, attributes such as `plan`,
  `tenant_id`).
- **Semantic conventions:** standardised names (`http.request.method`, `db.system`) so that
  tools understand your data without configuration.

> **Card** · **When:** in any new service, in 2026 ·
> **Pattern:** instrument with the neutral API and choose the backend later ·
> **Anti-pattern:** instrumenting with a vendor's proprietary SDK ·
> **Limits:** profiling entered alpha in March 2026: not yet for critical workloads ·
> **How it fails:** without a Collector, switching backends forces you to redeploy every service ·
> **Decision:** the Collector is where you filter, sample and enrich without touching the app ·
> **Trade-off:** one more component to operate vs vendor independence ·
> **Related:** sampling, semantic conventions `[13]`

---

## Structured logs

**The 2026 rule: structured JSON, with consistent fields, always.** Free-text logs cannot be
queried reliably.

```json
{"ts":"2026-09-15T04:12:33Z","level":"error","service":"api","env":"prod",
 "trace_id":"4bf92f...","span_id":"00f067...","request_id":"req_01J8XZ",
 "user_id":"u_42","tenant_id":"t_7","event":"payment_failed",
 "amount":5000,"currency":"EUR","provider":"stripe","code":"card_declined",
 "duration_ms":842}
```

**What makes a log good:**
- **`trace_id` and `span_id` injected automatically** by the library. Without them you can't jump from a log
  to the full trace, which is 80% of the value.
- **Fields, not sentences.** `"payment of 50 EUR failed for u_42"` can't be aggregated; fields can.
- **Levels with judgement:** `ERROR` = something requires human action. If your `ERROR` includes user
  validation failures, nobody will look at the errors. `WARN` = anomalous but tolerated. `INFO` = business milestones.
  `DEBUG` = off in production (or enabled by sampling).
- **Never log secrets or PII**: passwords, tokens, cards, full emails depending on your policy.
  Redact in the logging layer, instead of relying on every dev remembering to.
- **Log sampling** on extremely high-volume endpoints: log 1% of successes and 100% of errors.

> **Card** · **When:** always; free text can't be queried reliably ·
> **Pattern:** JSON with consistent fields and an automatically injected `trace_id` ·
> **Anti-pattern:** sentences instead of fields, and `ERROR` for user validation failures ·
> **Limits:** log volume can cost more than the infrastructure itself ·
> **How it fails:** a log of the full request ends up containing tokens or card numbers `[06, 07]` ·
> **Decision:** redact in the logging layer, instead of relying on every dev to remember ·
> **Trade-off:** detail vs cost and the risk of leaking data ·
> **Related:** correlation IDs, PII `[06, 15]`

---

## Metrics

**Types:** `counter` (only goes up: requests, errors) · `gauge` (goes up and down: active connections, memory
usage) · `histogram` (distribution: latencies — **the one you need for percentiles**) · `summary`.

**The four golden signals (Google SRE):**
1. **Latency** — and separate the latency of successful requests from that of errors (an instant 500 can
   improve your average and hide the problem).
2. **Traffic** — RPS, messages per second.
3. **Errors** — a ratio, not an absolute value.
4. **Saturation** — how full the most constrained resource is (CPU, memory, pool, queue).

**RED** (Rate, Errors, Duration) is also used for services, and **USE** (Utilization, Saturation, Errors)
for resources.

**The cardinality trap:** every unique combination of labels is a time series. Putting
`user_id` as a label in Prometheus with a million users brings down your metrics system and costs you a
fortune. **High cardinality belongs in traces and logs, not in metrics.** It is one of the most expensive mistakes and one of the most
frequently asked about.

**Histograms and percentiles:** you can't compute the global p99 by averaging the p99 of each instance.
That is why histograms store buckets and the percentile is computed over the sum of the buckets.

> **Card** · **When:** for alerting and for seeing trends ·
> **Pattern:** the four golden signals with histograms (not averages) ·
> **Anti-pattern:** high-cardinality labels (`user_id`, `request_id`, URLs with IDs) ·
> **Limits:** every combination of labels is a time series ·
> **How it fails:** a cardinality explosion brings down the metrics backend and sends the bill through the roof ·
> **Decision:** separate the latency of successes from that of errors (an instant 500 improves the average and hides the problem) ·
> **Trade-off:** useful dimensions vs cost ·
> **Related:** percentiles, SLOs `[09, 10]`

---

## Distributed tracing

A **trace** is a tree of **spans**; each span is an operation with a start, an end, attributes and events.
The **context** (`traceparent`, from the W3C Trace Context standard) is propagated through HTTP headers and through
queue messages.

**What it solves:** in microservices, "the request took 3 seconds" is useless. The trace shows you that 2.7s
went into a call to the inventory service, which in turn ran 47 queries — the N+1 **made visible**.

**Sampling:**
- **Head-based:** you decide at the start (e.g. 1% of everything). Cheap and simple, but **you may lose exactly the
  request that failed**.
- **Tail-based:** you decide at the end, once you know how it went: **you keep 100% of the errors and the slow
  ones**, plus a percentage of the normal ones. Much better signal per euro; it needs the Collector, which must
  buffer the entire trace. **It is the 2026 recommendation** for balancing cost and visibility.
- **Propagate the context through queues too** (put `traceparent` in the message headers) or you'll lose
  the trace as soon as something goes asynchronous.

> **Card** · **When:** as soon as there is more than one service or any asynchronous work ·
> **Pattern:** tail-based sampling — keep 100% of errors and slow requests ·
> **Anti-pattern:** head-based at 1%, which discards exactly the request that failed ·
> **Limits:** tail-based requires buffering the complete trace before deciding ·
> **How it fails:** without propagating the context through queues, the trace gets cut ·
> **Decision:** propagate `traceparent` in the message headers too ·
> **Trade-off:** storage cost vs being able to investigate the rare case ·
> **Related:** queues, W3C Trace Context `[08]`

---

## Correlation IDs

- **`request_id`** generated at the edge (or accepted from the client if you trust it) and propagated to **everything**: logs,
  outgoing calls, queue messages, and returned in the response and in errors.
- **Golden rule:** the user reports a problem with an ID shown on their screen, and you find
  the whole story with a single search. Without this, support is guesswork.
- With OpenTelemetry, the `trace_id` plays this role; also keep a human-readable `request_id` for
  human support.
- Add **business identifiers** as attributes: `tenant_id`, `order_id`, `plan`. They are what
  let you answer "does this only affect enterprise customers?".

> **Card** · **When:** on every request that enters the system ·
> **Pattern:** generate at the edge, propagate to everything, return it in the response and in errors ·
> **Anti-pattern:** each service generating its own and not propagating it ·
> **Limits:** it only works if **every** component honours it ·
> **How it fails:** the user reports a problem and there is no way to find their request ·
> **Decision:** add business identifiers (`tenant_id`, `order_id`) as attributes ·
> **Trade-off:** one more field in every log in exchange for investigations that take minutes instead of hours ·
> **Related:** tracing, error contracts `[03]`

---

## Health checks

```
GET /health/live    → is the process alive?        (no dependencies; for liveness)
GET /health/ready   → can it serve traffic?        (DB, cache, migrations; for readiness)
GET /health/startup → has it finished starting up?
```

**The classic mistake:** putting dependencies in the liveness check. If the database blips, Kubernetes
**restarts all your pods at once** and turns a degradation into a total outage. Dependencies → readiness.

**Distinguish hard from soft:** if the main DB goes down, you are not ready. If the recommendations service goes down,
you are still ready but degraded. A health check that turns red because of an optional dependency causes
incidents that didn't exist.

> **Card** · **When:** every service behind an orchestrator or load balancer ·
> **Pattern:** `live` with no dependencies · `ready` with hard and soft dependencies kept separate ·
> **Anti-pattern:** putting the database in the liveness check ·
> **Limits:** a check that only pings the port declares a useless service healthy ·
> **How it fails:** the DB blips and Kubernetes **restarts all the pods**, turning a degradation into an outage ·
> **Decision:** optional dependency down = you are still ready, just degraded ·
> **Trade-off:** deep checks (catch more) vs the risk of cascading restarts ·
> **Related:** probes, graceful shutdown `[10, 13]`

---

## Alerts

**The rule: alert on symptoms that affect the user, not on causes.** "CPU is at 90%" is not a
problem if nobody notices; "5% of checkouts are failing" always is.

- **Based on SLOs and error budget** (`10-reliability.md`): alert when the rate at which the error
  budget is being consumed implies missing the target — **burn rate alerting**. It is what stops you from alerting on every
  irrelevant spike.
- **Actionable:** every alert must have a clear action and a runbook. If the response is "look and do
  nothing", delete it.
- **Alert fatigue:** it is the most common and the most serious failure. A team that gets 50 alerts a day stops
  looking at them and misses the important one. **Fewer, better alerts > more alerts.**
- **Levels:** page (wakes someone up, only if there is user impact and it is urgent) vs ticket
  (looked at during business hours) vs dashboard only.

> **Card** · **When:** defining on-call ·
> **Pattern:** alerts on error budget burn rate, with a runbook and an owner ·
> **Anti-pattern:** 50 alerts a day — people stop looking and miss the important one ·
> **Limits:** alerting on causes (CPU) generates noise; on symptoms, signal ·
> **How it fails:** **alert fatigue**: the most common and the most serious failure ·
> **Decision:** page (wake someone up) only for real, urgent impact; everything else is a ticket ·
> **Trade-off:** detecting earlier vs waking people up for nothing ·
> **Related:** SLOs, incident response `[10]`

---

## Dashboards and error tracking

**Dashboards:**
- A **per-service overview** (the four golden signals) that can be read in 10 seconds.
- A **user journey** one (business funnel: sign-ups, checkouts, payments), which often detects
  incidents before the technical ones do.
- Investigation dashboards, created during incidents and kept.
- **A dashboard nobody looks at during an incident is a badly designed dashboard.**

**Error tracking** (Sentry and similar): groups exceptions by fingerprint, with stack trace, release version,
affected user and breadcrumbs. It complements logs because **it deduplicates and counts**: "this error has affected
1,243 users since v2.4.1" is actionable; 1,243 log lines are not.

**Typical retention (2026):** metrics 12+ months (trends and capacity planning), traces 7-30 days,
logs 14-90 days with cold archiving after 30. The cost of observability can exceed that of
the infrastructure itself: that is why you sample, control cardinality and filter in the Collector.

> **Card** · **When:** before the first incident, not during it ·
> **Pattern:** an overview readable in 10 seconds + a business journey one ·
> **Anti-pattern:** 40 charts nobody looks at when in a hurry ·
> **Limits:** a dashboard shows what you already knew you wanted to see ·
> **How it fails:** during the incident nobody can find the relevant chart ·
> **Decision:** error tracking deduplicates and counts: "affected 1,243 users" is actionable, 1,243 log lines are not ·
> **Trade-off:** more panels vs clarity under pressure ·
> **Related:** business metrics, incident response `[10]`

---

## Implementation: instrumenting a service

```python
# 1) Startup: once only, with the attributes that identify the service
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

FastAPIInstrumentor.instrument_app(app)      # incoming HTTP: for free
AsyncPGInstrumentor().instrument()           # queries: for free
tracer = trace.get_tracer("orders")
meter = metrics.get_meter("orders")

orders_created  = meter.create_counter("orders_created_total")
charge_duration = meter.create_histogram("charge_duration_ms")   # histogram -> percentiles

# 2) Manual spans ONLY for what matters in the domain
async def create_order(actor, body):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("tenant_id", actor.tenant_id)     # high cardinality: OK in traces
        span.set_attribute("plan", actor.plan)
        order = await service.create(actor, body)
        span.set_attribute("order.total_cents", order.total.cents)
        orders_created.add(1, {"plan": actor.plan})          # LOW cardinality in metrics
        return order

# 3) Logs with trace_id injected automatically
import structlog
def add_trace(_, __, event):
    ctx = trace.get_current_span().get_span_context()
    if ctx.is_valid:
        event["trace_id"] = format(ctx.trace_id, "032x")
        event["span_id"] = format(ctx.span_id, "016x")
    return event

structlog.configure(processors=[add_trace, structlog.processors.JSONRenderer()])
```

**The golden rule for attributes:** `tenant_id`, `user_id` and `order_id` go in **traces and logs**
(high cardinality, cheap there). In **metrics** only low-cardinality labels (`plan`, `region`,
`status_code`) — every unique combination is a time series, and `user_id` with a million users
brings down your metrics backend and blows up the bill.

**Propagating the context through a queue** (otherwise you lose the trace as soon as something goes asynchronous):

```python
from opentelemetry.propagate import inject, extract

# producer
headers = {}
inject(headers)                                      # adds traceparent
await broker.publish(event, headers=headers)

# consumer
ctx = extract(message.headers)
with tracer.start_as_current_span("process_order", context=ctx):
    await process(message)
```

> **Card** · **When:** every service, from the first deployment ·
> **Pattern:** auto-instrumentation for 80% + manual spans for the domain ·
> **Anti-pattern:** `user_id` as a metric label ·
> **Limits:** every span and every label costs storage and money ·
> **How it fails:** without propagating the context to queues, the trace gets cut and the asynchronous flow is invisible ·
> **Decision:** if the data point identifies **one**, it goes in a trace or log; if it groups **many**, in a metric ·
> **Trade-off:** granularity vs cost and cardinality ·
> **Related:** cardinality, queues, correlation IDs `[08]`

---

## Monitoring in production: what you need to have in place

The bare minimum on the day a service receives real traffic:

- **A dashboard per service** with the four golden signals, compared against the previous week.
- **SLO-based alerts** (burn rate), not arbitrary technical thresholds `[10]`.
- **A business dashboard**: sign-ups, orders, payments per minute. **It often detects incidents before
  the technical metrics do** — if orders drop to zero and CPU is normal, something is broken in a way
  your technical monitoring can't see.
- **Mark deployments on the charts.** It makes "what changed?" obvious, and that is the first question
  of every incident `[10]`.

**What to watch to detect each type of failure:**

| Failure | Signal that gives it away | Where |
|---|---|---|
| Degraded dependency | outbound latency per dependency | metric + trace |
| Exhausted pool | connections in use / acquisition wait | metric |
| Stuck queue | **consumer lag** and age of the oldest message | metric `[08]` |
| Stalled outbox | age of the oldest unpublished event | metric `[08]` |
| Memory leak | memory growing between restarts | metric |
| Retry loop | ratio of retries to requests | metric |
| Data leak / IDOR | **nothing** — that is why you need an audit log `[17]` | audit |
| Query plan change in the DB | p99 of a specific query | metric + `pg_stat_statements` |
| Certificate about to expire | days remaining | synthetic check |
| Runaway cost | spend per service per day | budget alert `[13]` |

**What doesn't show up in metrics** is the most dangerous: data leaks, silent corruption and
consumers that process incorrectly but without errors. For that you need audit logs and reconciliation `[07, 17]`.

> **Card** · **When:** before the service receives real traffic ·
> **Pattern:** alert on user symptoms; business dashboards alongside the technical ones ·
> **Anti-pattern:** alerting on high CPU — if nobody notices, it isn't a problem ·
> **Limits:** silent failures don't show up in any metric ·
> **How it fails:** the system "works" while it is two hours behind on processing ·
> **Decision:** if an alert has no clear action and runbook, delete it ·
> **Trade-off:** alert coverage vs fatigue (and fatigue is what makes people ignore the important one) ·
> **Related:** SLOs, incident response, cost `[10, 13]`

---

## Interview questions and trade-offs

**Q: What is the difference between monitoring and observability?**
Monitoring checks conditions known in advance; observability lets you investigate the unknown
thanks to context and high cardinality. *Signal:* you make it concrete — with monitoring you know the error rate
went up; with observability you discover it only affects users of one specific tenant after a deployment.

**Q: A high-latency alert comes in. What is your process?**
Confirm real user impact → look at the golden signals to narrow down the service → trace a slow
request to see where the time goes → logs for that span → correlate with recent deployments and changes.
*Signal:* you start with the impact and with "what changed?", not with loose technical hypotheses.

**Q: Why not put `user_id` as a label on a metric?**
Cardinality explosion: each value creates a new time series. *Signal:* you say where that
information does belong (traces and logs) and that it is one of the mistakes that costs the most money on observability bills.

**Q: Head-based or tail-based sampling?**
Tail-based if you can afford the Collector: you keep the errors and the slow requests, which are the ones that
matter. *Signal:* you mention the cost (you have to buffer the complete trace until you decide) and that head-based
has the drawback of discarding precisely the interesting case.

**Q: What goes in the liveness probe?**
Nothing external. Only that the process responds. *Signal:* you explain the cascading failure — dependencies in the
liveness probe turn a DB degradation into a mass restart of every pod.

**Core trade-off of this box:** *visibility vs cost and noise*. Keeping everything is extremely expensive and
unusable; keeping too little leaves you blind exactly when it matters. The 2026 balance is: cheap,
low-cardinality metrics for alerting, tail-sampled traces for investigating, structured and sampled logs
for the detail, and everything correlated by `trace_id`.

---

## Sources

- [OpenTelemetry docs](https://opentelemetry.io/docs/) — graduated from the CNCF in May 2026.
- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) (golden signals) and [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) (burn rate).
- [W3C Trace Context](https://www.w3.org/TR/trace-context/) — the propagation standard.
- [OpenTelemetry Best Practices 2026: how to control cost](https://www.apica.io/blog/opentelemetry-best-practices-for-improving-your-monitoring-and-observability/)
- [Observability in 2026: distributed tracing and OpenTelemetry](https://dev.to/zny10289/observability-in-2026-distributed-tracing-replaced-logs-and-opentelemetry-won-8lm)
