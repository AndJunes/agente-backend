# 16 · Integrations

> Integrating with a third party means **accepting its failures as your own** in the eyes of the user. Everything in this box
> boils down to one idea: *assume the external service will fail, will be slow and will change without telling you.*


**Covers from the syllabus:** `external_apis` · `webhooks` · `oauth` · `email` · `notifications` · `storage` · `implementations` · `failure_modes` · `tradeoffs`

---

## Principles for consuming third-party APIs

**1. Wrap it in an adapter.** Never call a provider's SDK from your business logic. An
interface of your own (`PaymentGateway`, `EmailSender`) lets you switch providers, test without a network, and keeps
their odd types from infecting your domain. It is the *anticorruption layer* from `05-architecture.md`.

**2. Timeout, retry with backoff, circuit breaker.** Always all three (`10-reliability.md`). A slow provider
without a timeout takes your service down.

**3. Anything that isn't essential to responding goes to a queue.** The user should not have to wait for
your email provider to respond in order to complete a sign-up.

**4. Idempotency in both directions.** Send idempotency keys and treat their webhooks as potentially duplicated.

**5. Cache aggressively whatever rarely changes** (catalogs, exchange rates, configuration) and have a default
value for when they are unavailable.

**6. Observe the integration as if it were your own:** latency, error rate and quota metrics per provider,
with their own alerts. When a provider degrades, you want to find out yourself before you hear it on Twitter.

**7. Isolate credentials per environment** and keep separate sandbox keys. The classic incident is sending
test emails to real customers.

> **Card** · **When:** every external dependency ·
> **Pattern:** your own adapter + timeout + retry + breaker + per-provider metrics ·
> **Anti-pattern:** calling the provider's SDK from business logic ·
> **Limits:** you accept its failures as your own in the eyes of the user ·
> **How it fails:** the provider changes its API and your domain, coupled to its types, breaks entirely ·
> **Decision:** anything that isn't essential to responding goes to a queue ·
> **Trade-off:** an adaptation layer (hours today) vs a rewrite the day you switch providers ·
> **Related:** anticorruption layer, breakers `[05, 10]`

---

## Handling external API failures

| Situation | Correct response |
|---|---|
| Timeout / 5xx | retry with backoff + jitter, breaker if it persists |
| 429 rate limited | honor `Retry-After`, **enqueue**, your own throttling |
| Validation 4xx | **do not retry**; it's your bug, log it with context |
| 401/403 | refresh credentials once; if it persists, alert (key rotated or revoked) |
| Unexpected response | validate against a schema and fail in a controlled way |
| Provider completely down | degrade (`10-reliability.md`), queue for later, or manual mode |

**Your own outbound rate limiting:** if the provider limits you to 100 req/s, implement your own token
bucket **before** calling. It is much better to regulate yourself than to burn your quota on retries and get
blocked. With several replicas, the counter lives in Redis.

**The outbound queue pattern:** for non-interactive operations (syncing a CRM, sending
notifications), don't call directly: enqueue. You get retries, pacing control, visibility and
resilience to provider outages, all for free.

> **Card** · **When:** integrating any provider ·
> **Pattern:** classify the error (transient / permanent / quota) and respond differently to each ·
> **Anti-pattern:** retrying a validation 400 ·
> **Limits:** a timeout doesn't tell you whether the operation ran on the other side ·
> **How it fails:** you burn your quota on retries and the provider blocks you ·
> **Decision:** implement your own rate limit **before** calling, not after you get limited ·
> **Trade-off:** regulating yourself (slower) vs exhausting the quota ·
> **Related:** rate limiting, idempotency `[03, 08]`

---

## OAuth for integrations (you as the client)

When your app accesses a user's account on another service (Google Drive, Slack, GitHub):

- **Authorization Code + PKCE** (`06-security.md`). Store the `access_token` (short-lived) and the **`refresh_token`
  (long-lived and sensitive: encrypted in the database, never in logs)**.
- **Refresh:** renew **before** it expires, not when it fails. And guard against concurrent refresh
  (two workers refreshing at the same time invalidate each other's token): a lock or an atomic
  `UPDATE ... RETURNING`.
- **Revocation:** the user can disconnect the app at any time. Handle the permanent 401:
  mark the connection as broken and **ask the user to reconnect** in the UI, instead of retrying in a loop.
- **Minimal scopes.** Asking for more permissions than you need lowers conversion and increases risk.
- **Multiple accounts:** a user may connect two accounts from the same provider. Model the connection as
  an entity of its own from the start; converting it later is painful.

> **Card** · **When:** accessing a user's account on another service ·
> **Pattern:** Authorization Code + PKCE; proactive refresh with a lock ·
> **Anti-pattern:** storing the refresh token unencrypted, or refreshing only when it fails ·
> **Limits:** the user can revoke the connection at any time ·
> **How it fails:** two workers refresh at the same time and invalidate each other's token — intermittent and extremely hard to diagnose ·
> **Decision:** on a permanent 401, mark the connection as broken and ask to reconnect in the UI ·
> **Trade-off:** broad scopes (less friction later) vs minimal ones (more trust, less risk) ·
> **Related:** OAuth2, secrets `[06]`

---

## Incoming webhooks (you as the receiver)

This is the other half of `03-apis.md` and the most frequently asked topic in integrations.

```python
@app.post("/webhooks/provider")
def receive(request):
    verify_signature(request.raw_body, request.headers["X-Signature"])   # 1
    event = json.loads(request.raw_body)
    if already_processed(event["id"]):                                   # 2
        return 200
    enqueue(event)                                                       # 3
    return 200                                                           # 4
```

1. **Verify the HMAC signature over the raw body** and check the timestamp (anti-replay).
   Constant-time comparison (`06-security.md`).
2. **Deduplicate by event ID** — delivery is at-least-once.
3. **Enqueue and process in the background.**
4. **Respond 200 fast** (within seconds). If you are slow, the provider retries and you get cascading duplicates.

**Also:**
- **Tolerate out-of-order delivery**: events may arrive in a different order from the one they happened in. Base the logic on
  state, not on sequence.
- **Reconcile periodically** against the provider's API: **webhooks get lost**. A job that compares
  states is your safety net.
- **Store the raw event** before processing it. When something goes wrong, you will want to reprocess.
- **Public endpoint with no user authentication**: protect it with rate limiting and don't leak information
  in errors.

> **Card** · **When:** every provider that notifies you of events ·
> **Pattern:** signature → dedupe → enqueue → fast 200, plus periodic reconciliation ·
> **Anti-pattern:** processing synchronously inside the handler ·
> **Limits:** at-least-once, no guaranteed ordering, and **webhooks get lost** ·
> **How it fails:** you are slow to respond, the provider retries and you get cascading duplicates ·
> **Decision:** store the raw event before processing it, so you can reprocess ·
> **Trade-off:** real time (webhooks) vs reliability (polling and reconciliation) ·
> **Related:** HMAC signatures, idempotency `[06, 08]`

---

## Email

- **Providers:** SendGrid, Postmark, SES, Resend. **Don't run your own SMTP**: deliverability is an
  IP-reputation problem that takes years to build.
- **Deliverability (what sets apart those who have suffered through this):** **SPF** (which servers may send on behalf of your
  domain), **DKIM** (cryptographic signature of the message) and **DMARC** (what to do if they fail and where to report).
  Without all three, you end up in spam.
- **Transactional vs marketing:** separate them onto **different domains or subdomains**. If your marketing
  campaign burns the reputation, you don't want password-reset emails to go down with it.
- **Bounces and complaints:** process the bounce webhooks. Continuing to send to addresses that bounce destroys
  your reputation. Keep a **suppression list** and honor it.
- **Always asynchronous**, with retries. And **idempotency**: record which email was sent for which event, or a
  job retry sends the user three copies.
- **Versioned templates**, with plain text as well as HTML, and links with single-use, expiring tokens.

> **Card** · **When:** verification, recovery, notifications, invoices ·
> **Pattern:** managed provider + SPF, DKIM and DMARC + separate domains ·
> **Anti-pattern:** running your own SMTP; mixing transactional and marketing on the same domain ·
> **Limits:** deliverability is accumulated reputation, not configuration ·
> **How it fails:** continuing to send to addresses that bounce destroys your reputation ·
> **Decision:** process the bounce webhooks and keep a suppression list ·
> **Trade-off:** one domain (simple) vs separate ones (protects what is critical) ·
> **Related:** queues, idempotency `[08]`

---

## SMS and push

**SMS** (Twilio, MessageBird):
- Expensive per message, with per-country rules (registered sender IDs, approved templates, allowed hours).
- **SMS pumping fraud:** an attacker abuses your "send code" to generate traffic
  to premium numbers and drains your budget. **Rate limiting per number, per IP and per account, geo-blocking
  and CAPTCHA** are mandatory on any endpoint that triggers an SMS.
- Not suitable for high-security MFA (SIM swapping), but it is still the most accessible option.

**Push** (APNs for iOS, FCM for Android):
- Device tokens **expire and get invalidated**: process the unregistration responses and clean up, or
  you waste quota sending to dead devices.
- A user has several devices; model `user → N tokens`.
- **Don't put sensitive data in the payload**: it shows up on the lock screen.
- Respect preferences and quiet hours: push is the easiest channel to burn.

**Cross-cutting rule for notifications:** centralize in a **notification service** with per-user and per-channel
preferences, templates, deduplication and grouping (*digest*). If every module sends on its own,
you end up sending five notifications for the same event.

> **Card** · **When:** verification, alerts, mobile notifications ·
> **Pattern:** multi-level rate limiting (number, IP, account) and spend control ·
> **Anti-pattern:** a "send code" endpoint with no limits ·
> **Limits:** per-country rules, registered sender IDs, push tokens that expire ·
> **How it fails:** **SMS pumping** — fraud that generates traffic to premium numbers and drains your budget ·
> **Decision:** clean up invalid push tokens or you waste quota on dead devices ·
> **Trade-off:** friction (CAPTCHA, limits) vs the cost of fraud ·
> **Related:** rate limiting, cost `[03, 13]`

---

## Maps, social login and cloud storage

**Maps** (Google Maps, Mapbox): **cache aggressively** — geocoding the same address a thousand times is throwing
money away (and their terms often forbid it, sometimes restricting how results may be stored: read them).
Watch the quota, have a plan for when it runs out, and don't put an API key with broad permissions in the client.

**Social login** (Google, Apple, GitHub): use **OIDC**, validate the `id_token` against the JWKS, and decide your
**account linking** policy — if someone signed up with email and later logs in with Google using the
same email, is it the same account? **Automatically linking by email is an account-takeover
vector if the provider doesn't verify the email** (check the `email_verified` claim). "Sign in with Apple"
can also hide the real email behind a relay.

**The user's cloud storage** (Drive, Dropbox): APIs with aggressive quotas, cursor-based pagination and change
webhooks with their own model. Bidirectional sync is a distributed consistency problem
with real conflicts — underestimating it is a classic planning mistake.

**CRMs and analytics** (Salesforce, HubSpot, Segment): low API limits, so **batching and queues**.
And be careful about sending PII to analytics tools: it is a legal matter, not just a technical one.

> **Card** · **When:** common product integrations ·
> **Pattern:** cache expensive results (geocoding) and validate `email_verified` in social login ·
> **Anti-pattern:** **automatically linking accounts by email** without checking that the provider verified it ·
> **Limits:** some terms of service restrict storing results: read them ·
> **How it fails:** account takeover if someone registers a provider with someone else's unverified email ·
> **Decision:** define the account linking policy from the start ·
> **Trade-off:** user convenience vs takeover risk ·
> **Related:** OIDC, quota costs `[06]`

---

## Designing an integration layer that ages well

```
domain  →  own interface  →  adapter  →  HTTP client with policies  →  provider
                                           (timeout, retry, breaker,
                                            rate limit, metrics, logs)
```

- **A shared HTTP client with the policies already in place**, so you don't depend on every dev remembering them.
- **A provider registry and feature flags** so you can switch providers or turn one off on the fly.
- **Sandbox / fake mode** for development and tests, selectable through configuration.
- **Store the requests and responses** (redacted) of critical integrations: when the provider
  says "we never received that", you will have the evidence.
- **Contract verified periodically** (`11-testing.md`): a scheduled test against the real sandbox detects
  provider changes before your users do.

> **Card** · **When:** from the second integration onwards ·
> **Pattern:** a shared HTTP client with the policies in place + a fake mode for tests ·
> **Anti-pattern:** each integration implementing its own retries in its own way ·
> **Limits:** storing requests and responses takes space: redact and set retention ·
> **How it fails:** the provider says "we never received that" and you have no evidence ·
> **Decision:** store redacted request/response pairs for critical integrations ·
> **Trade-off:** a common abstraction vs using provider-specific features ·
> **Related:** adapters, contract testing `[05, 11]`

---

## Failure modes: an integration

| Failure | Symptom | Mitigation |
|---|---|---|
| **Provider down** | cascading errors in your API | breaker + fallback + queue `[10]` |
| **Provider slow** | your workers exhausted | aggressive timeout (slow is worse than down) |
| **Rate limit** | mass 429s | your own throttling before calling |
| **Quota exhausted** | failures in the middle of the month | usage alerts, degradation plan |
| **Lost webhook** | state silently out of sync | periodic reconciliation |
| **Duplicate webhook** | effect applied twice | dedupe by `event_id` |
| **Revoked token** | permanent 401 in a loop | mark the connection as broken, ask to reconnect |
| **Concurrent refresh** | intermittent disconnections | lock or atomic update when refreshing |
| **Unannounced API change** | new parsing errors | schema validation + scheduled contract test |
| **Deprecation** | works until it stops working | watch for notices and `Sunset` headers `[03]` |
| **Unexpected data** | null fields that are "never" null | validate the response, don't trust it |

**The rule that sums up the box:** *treat every provider as if it were going to fail today.* The three defenses that
prevent the most incidents are the **timeout** (which keeps it from dragging you down), the **queue** (which absorbs its outage)
and **reconciliation** (which detects what got lost without anyone noticing).

**Inherited reliability budget:** your availability cannot exceed that of the dependencies that
sit on your critical path. If your payment gateway promises 99.9% and you call it synchronously during
checkout, your checkout **cannot** be more reliable than that — unless you make it asynchronous or have an
alternative (`[10]`).

> **Card** · **When:** adding any provider to the critical path ·
> **Pattern:** calculate the inherited reliability and decide whether that dependency can be synchronous ·
> **Anti-pattern:** promising an SLO better than that of your synchronous dependencies ·
> **Limits:** you don't control their availability, only your reaction ·
> **How it fails:** a third party's outage becomes your outage in the eyes of the user ·
> **Decision:** can it wait? Then a queue. Can't it? Then it needs a fallback ·
> **Trade-off:** rich functionality (more dependencies) vs reliability ·
> **Related:** SLOs, degradation, queues `[08, 10]`

---

## Interview questions and trade-offs

**Q: Your payment provider starts taking 20 seconds. What happens and what do you do?**
Without a timeout, I exhaust workers and go down. With a timeout + breaker, I fail fast, enqueue the attempt and show
"processing" to the user. *Signal:* you mention that you will have to reconcile afterwards, because some of those
calls that timed out **did execute** at the provider: hence the idempotency key.

**Q: How do you guarantee a webhook isn't processed twice?**
Signature + deduplication by `event.id` in the same transaction as the effect + idempotent logic.
*Signal:* you add that you have to tolerate out-of-order delivery and that periodic reconciliation covers lost events,
which is the part almost nobody mentions.

**Q: A user says they aren't receiving your emails. Where do you start?**
Status at the provider (delivered, bounced, marked as spam), the suppression list, and the domain's
SPF/DKIM/DMARC configuration. *Signal:* you talk about IP/domain reputation and separating transactional from
marketing — it shows real experience.

**Q: How do you store your users' OAuth refresh tokens?**
Encrypted in the database (at field level), never in logs, with proactive refresh and handling of the
"revoked by the user" case. *Signal:* you mention concurrent refresh as a real bug, one that breaks the connection
intermittently and is extremely hard to diagnose.

**Q: How do you stop someone from draining your SMS budget?**
Multi-level rate limiting (number, IP, account), geo-restrictions, CAPTCHA and spend alerts. *Signal:*
you know the term *SMS pumping* and that it is an active fraud, not a hypothesis.

**Core trade-off of this box:** *coupling vs delivery speed*. Using the provider's SDK
directly is super fast today and extremely expensive the day you switch providers, they fail, or they change their API. The adaptation layer
costs a few hours up front and is what lets you survive deprecation, outages and
price renegotiation without rewriting the product.

---

## Sources

- [Stripe — Webhooks best practices](https://docs.stripe.com/webhooks/best-practices) and [GitHub — Securing webhooks](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- [RFC 9700 — OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html)
- [SPF, DKIM and DMARC](https://www.rfc-editor.org/rfc/rfc7489.html) — email deliverability.
- [Twilio — SMS pumping fraud](https://www.twilio.com/docs/verify/preventing-toll-fraud)
- [AWS Builders' Library — Avoiding fallback in distributed systems](https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/)
