# 07 · Payments

> Here bugs are measured in real money and in calls from angry customers. The rule that governs everything:
> **never trust the client, the webhook dictates the state, and everything must be idempotent.**


**Covers from the syllabus:** `concepts` · `providers` · `checkout` · `subscriptions` · `webhooks` · `refunds` · `implementations` · `state_machines` · `failure_modes` · `constraints` · `tradeoffs`

---

## How a payment works under the hood

```
Buyer → Merchant (you) → PSP (Stripe) → Acquirer → Network (Visa) → Issuer (the buyer's bank)
```

**The phases you must always keep apart:**

1. **Authorization** — the bank puts a hold on the amount and returns a code. The money **has not moved**.
   The hold expires (typically ~7 days).
2. **Capture** — you claim the authorized money. It can be immediate (the norm in digital e-commerce) or
   deferred (you ship the product and capture on dispatch: the correct model for physical goods).
3. **Settlement / payout** — days later, the money reaches your account, batched and net of fees. **The
   payment date and the deposit date never match**, and that is why reconciliation is a real problem.

**Concepts you must be comfortable with:** 3D Secure / SCA (cardholder authentication; **mandatory in Europe
under PSD2**, and it adds an interactive step your flow must support), partial authorization, retries on
`insufficient_funds`, and *network tokens*.

> **Card** · **When:** before writing the first line of integration code ·
> **Pattern:** always distinguish authorization (hold) from capture (charge) and from settlement (deposit) ·
> **Anti-pattern:** capturing at authorization when you ship physical goods days later ·
> **Limits:** the authorization expires (~7 days); settlement arrives days later and batched ·
> **How it fails:** the payment date and the deposit date never match → reconciliation doesn't balance ·
> **Decision:** digital → immediate capture; physical → capture on dispatch ·
> **Trade-off:** capture early (fewer failed payments) vs capture on shipping (fewer refunds and disputes) ·
> **Related:** state machines, reconciliation `[17]`

---

## Stripe: the mental model

**PaymentIntent** is the central object: it represents **the intent to charge** and survives retries,
3DS authentication and failures. It is a state machine:

```
requires_payment_method → requires_confirmation → requires_action (3DS)
   → processing → succeeded
                └→ canceled
```

**The two integration paths:**
- **Checkout Session** (hosted): Stripe provides the page. Less control, **far less PCI surface**,
  and it is the recommended default in 2026.
- **Payment Element + PaymentIntent** (embedded): you control the UI, and card data never touches your
  server (it goes straight to Stripe via JS).

**Objects you must know:** `Customer`, `PaymentMethod`, `SetupIntent` (save a card without charging),
`Invoice`, `Subscription`, `Price`/`Product`, `Refund`, `Dispute`, `Payout`, `Event`.

**Other PSPs:** **Mercado Pago** dominates LatAm (Preferences + IPN webhooks, and local methods such as PIX,
OXXO, boleto, with **asynchronous** flows where the user pays hours later). **PayPal** uses orders +
capture. The mental model is the same: intent → authorization → capture → webhook as the source of truth.

> **Card** · **When:** when choosing how deep to integrate ·
> **Pattern:** hosted Checkout by default; Payment Element if you need to control the UI ·
> **Anti-pattern:** building your own card form and multiplying your PCI scope ·
> **Limits:** the PaymentIntent is the source of truth for the **charge**; your system is the source of truth for **access** ·
> **How it fails:** storing only "paid: yes" loses the real state (requires_action, processing) ·
> **Decision:** store `customer_id`, `subscription_id` and status; don't call the API on every request ·
> **Trade-off:** control over the experience vs compliance surface ·
> **Related:** PCI, checkout `[06]`

---

## The golden rule: the webhook is the source of truth

**Never mark an order as paid because the browser came back to your `success_url`.** The user can
close the tab, lose the connection, or fake the return. The redirect is UX; **the webhook is the fact.**

```python
@app.post("/webhooks/stripe")
def webhook(request):
    # 1) VERIFY THE SIGNATURE over the RAW body (see 06-security.md)
    event = stripe.Webhook.construct_event(request.raw_body,
                                           request.headers["Stripe-Signature"],
                                           WEBHOOK_SECRET)
    # 2) DEDUPLICATE: at-least-once means this event can arrive twice
    if already_processed(event["id"]):
        return 200
    # 3) Respond fast: enqueue and process in the background
    enqueue(event)
    mark_processed(event["id"])
    return 200
```

**The five commandments of the payments webhook:**
1. **Verify the signature** always, over the raw body.
2. **Deduplicate by `event.id`** — delivery is at-least-once, so duplicates are guaranteed.
3. **Respond 200 within seconds.** If you take too long, the PSP retries and you get cascading duplicates.
   Enqueue and process asynchronously.
4. **Tolerate out-of-order delivery.** `payment_intent.succeeded` can arrive *before* `checkout.session.completed`.
   Your logic must be based on the object's state, not on the order of arrival.
5. **Reconcile anyway.** A periodic job that compares your pending orders with the real state in the
   PSP's API saves you from lost webhooks. **Webhooks fail; reconciliation is your safety net.**

**Events that actually matter:** `checkout.session.completed`, `payment_intent.succeeded`,
`payment_intent.payment_failed`, `invoice.paid`, `invoice.payment_failed`,
`customer.subscription.created/updated/deleted`, `charge.refunded`, `charge.dispute.created`.

> **Card** · **When:** always; it is the most expensive design mistake in this box ·
> **Pattern:** verify signature → deduplicate by `event.id` → enqueue → respond 200 fast ·
> **Anti-pattern:** marking the order as paid on the browser's `success_url` ·
> **Limits:** **at-least-once** delivery with **no ordering guarantee** ·
> **How it fails:** the user closes the tab after paying and the order is never confirmed ·
> **Decision:** base the logic on the object's state, never on the sequence of events ·
> **Trade-off:** relying only on webhooks (correct, asynchronous) vs immediate UX ·
> **Related:** webhooks, idempotency, reconciliation `[03, 08, 16]`

---

## Idempotency in payments

**Two layers, both mandatory:**

- **Towards the PSP:** send an `Idempotency-Key` on every POST (Stripe supports and recommends it). If the
  network fails and you don't know whether the charge happened, **retry with the same key**: it either returns
  the original result or executes exactly once. Without this, a timeout = the risk of charging twice.
- **Inwards:** your own "pay" endpoint needs its own idempotency key (see `03-apis.md`), inserted
  in the same transaction as the operation.

**The key must derive from the business intent** (for example `order_id + attempt`), not be a fresh
UUID on every retry — if you generate a new key when retrying, idempotency is worthless.

> **Card** · **When:** on every call that moves money, in both directions ·
> **Pattern:** a key derived from the intent (`order_id`), in the same transaction as the effect ·
> **Anti-pattern:** generating a new UUID on every retry — it voids the protection entirely ·
> **Limits:** it protects within the key's retention window (24 h - 7 days) ·
> **How it fails:** a timeout without an idempotency key leaves a charge in an unknown state ·
> **Decision:** on a timeout, **retry with the same key**; never assume it failed ·
> **Trade-off:** one extra write per operation in exchange for never charging twice ·
> **Related:** idempotency, retries `[03, 08]`

---

## Modelling state: state machines, not booleans

The most expensive mistake in this box is `order.paid = True`. Use explicit states and **legal transitions**:

```
Order:     draft → pending_payment → paid → preparing → shipped → delivered
                         ↓            ↓
                     cancelled    refunded

Payment:   initiated → authorized → captured → settled
               ↓           ↓           ↓
            failed      expired    refunded/disputed
```

**Rules:**
- Every transition is **validated** (`from_state → to_state` allowed) and **recorded** with timestamp, actor and
  reason. That is your audit log and your customer support.
- **Never delete or overwrite** a payment record. Correct it with a new record (as in accounting:
  entries are offset, not erased).
- The order state and the payment state are **separate machines** that synchronise through events.

> **Card** · **When:** order, payment, subscription, shipment, return ·
> **Pattern:** validated legal transitions + a record of every change with actor and reason ·
> **Anti-pattern:** `order.paid = True`; three booleans allow eight states, five of them impossible ·
> **Limits:** the order state and the payment state are **different** machines that synchronise through events ·
> **How it fails:** two simultaneous webhooks apply the same transition twice ·
> **Decision:** atomic transition — `UPDATE ... WHERE status = 'previous'` and check the affected rows ·
> **Trade-off:** model rigidity vs invalid states being impossible ·
> **Related:** state machines, audit logs `[17]`

---

## Money: how to represent it

- **Integers in the minor unit** (cents) or `DECIMAL` with a fixed scale. **Never float.**
- **Always store the currency** alongside the amount. A `total: 1000` without a currency is a bug waiting to happen.
  Watch out: some currencies have **zero decimals** (JPY, CLP) and some have three (KWD/BHD) — always assuming "×100" is a bug.
- **Rounding:** define the policy (half-up, banker's) and apply it in a single place. Never round in the middle
  of a chain of calculations.
- **Never add amounts in different currencies.** A `Money(amount, currency)` value object that prevents it in
  the constructor eliminates this whole family of errors.
- **Exchange rates:** store the rate and the moment used in each transaction. "Recalculating with today's
  rate" changes history and wrecks the accounting.

> **Card** · **When:** in the first commit that touches amounts ·
> **Pattern:** a `Money(integer_amount, currency)` value object that prevents adding different currencies ·
> **Anti-pattern:** `FLOAT`, and amounts without a currency ·
> **Limits:** some currencies have **zero decimals** (JPY, CLP) and some have three (KWD): "×100" doesn't always hold ·
> **How it fails:** rounding errors that throw the accounting off imperceptibly ·
> **Decision:** freeze the exchange rate used in the transaction; never recalculate history ·
> **Trade-off:** a dedicated type is more verbose but eliminates an entire family of bugs ·
> **Related:** data modeling, invoicing `[04, 17]`

---

## Subscriptions & billing

**Concepts:** `Product` (what you sell) → `Price` (how much and how often) → `Subscription` (who has it) →
`Invoice` (the charge for one period) → `PaymentIntent` (the attempt to collect that invoice).

**The hard part isn't charging, it's the lifecycle:**
- **Proration:** if they upgrade mid-month, the proportional difference is charged. If they downgrade,
  it usually applies from the next period or generates a credit balance. **Let the PSP calculate it**: this
  arithmetic has more edge cases than you think.
- **Trials:** with or without a card; what happens when it ends; a reminder is mandatory in some jurisdictions.
- **Dunning:** handling failed charges. Cards expire and fail all the time
  (**it is the main cause of involuntary churn**). Sequence: smart staggered retries
  (day 1, 3, 5, 7), emails to the customer, a *grace period* with the service still active, and finally suspension.
- **Upgrades/downgrades/pause/cancellation**: immediate or at the end of the period? Is it refunded? Decide, document it
  and model it; don't improvise it in an `if`.

**The architectural rule:** the PSP holds the truth about the **charge**; your system holds the truth about **access**.
Store `stripe_customer_id`, `subscription_id`, status and period end date, and **decide access with
your own data** (updated by webhook), not by calling the Stripe API on every request.

> **Card** · **When:** any recurring model ·
> **Pattern:** the PSP calculates proration; you store the status and period end to decide access ·
> **Anti-pattern:** implementing proration by hand ·
> **Limits:** cards expire and fail all the time ·
> **How it fails:** **involuntary churn** from failed charges is the main revenue leak ·
> **Decision:** dunning with staggered retries, notices and a grace period before suspending ·
> **Trade-off:** cutting off fast (protects revenue) vs a grace period (retains customers) ·
> **Related:** webhooks, access permissions `[17]`

---

## Refunds, chargebacks and disputes

- **Refund:** you give the money back voluntarily. Full or partial. It takes days to reach the
  customer — communicate that or you'll get support tickets.
- **Chargeback / dispute:** the customer files a claim with **their bank**. It is an adversarial process: the
  money is pulled from you *plus* a fee, and you have a deadline to submit evidence (receipts, delivery logs, IP, accepted
  ToS). **That's why you keep a trail of everything.**
- **Dispute ratio:** if it exceeds a certain threshold (~0.75-1%), the network can penalise or expel you.
- **Listening to `charge.dispute.created`** and reacting (suspend the service, open an internal case) is part
  of the design, not an extra.

> **Card** · **When:** from day one; they will come ·
> **Pattern:** listen to `charge.dispute.created` and react automatically ·
> **Anti-pattern:** not storing evidence (delivery logs, IP, acceptance of terms) ·
> **Limits:** the bank resolves the dispute, not you; there is a deadline to provide evidence ·
> **How it fails:** exceeding a ~0.75-1% dispute ratio can cost you your account with the network ·
> **Decision:** a voluntary refund usually costs less than losing a dispute ·
> **Trade-off:** a generous refund policy (fewer disputes, more direct cost) ·
> **Related:** audit logs, evidence `[17]`

---

## Carts, orders and inventory

**Cart:** ephemeral, it can live in Redis with a TTL. **Prices are recalculated on the server at
checkout** — never trust the price the client sends. (Tampering with the price in the request is the
oldest attack in e-commerce and it still works on real sites.)

**Order:** immutable once confirmed. Store a **snapshot** of what was bought (name, price, taxes
at that moment). If you change the product's price tomorrow, the old invoice must not change.

**Inventory and the classic race condition:**
```sql
-- BAD: check and then update (two users can pass the check at the same time)
SELECT stock FROM products WHERE id = 1;      -- 1
UPDATE products SET stock = stock - 1 ...;    -- sold twice

-- GOOD: atomic condition, and the result tells you whether you succeeded
UPDATE products SET stock = stock - 1
WHERE id = 1 AND stock >= 1;                  -- 0 rows affected = out of stock
```
For carts and flash sales: **reservation with a TTL** (you decrement on add, release if they don't pay within N minutes) and
a job that expires reservations. With heavy concurrency on the same SKU, optimistic locking with retries
works better than a pessimistic lock that serialises every buyer.

> **Card** · **When:** e-commerce and any limited resource ·
> **Pattern:** `UPDATE stock = stock - 1 WHERE id = $1 AND stock >= 1` and check the affected rows ·
> **Anti-pattern:** `SELECT` and then `UPDATE` — check-then-act is a race condition ·
> **Limits:** reservations need a TTL and a job that expires them ·
> **How it fails:** **selling more stock than you have** in a flash sale ·
> **Decision:** the price is **always** recalculated on the server at checkout ·
> **Trade-off:** pessimistic lock (serialises buyers) vs optimistic with retries ·
> **Related:** transactions, inventory `[04, 17]`

---

## Taxes, coupons and pricing

- **Taxes:** they depend on the **product type and the buyer's jurisdiction**, and in the EU B2C digital VAT
  is charged in the customer's country (with VAT number validation for B2B reverse charge). Don't
  implement it by hand: use Stripe Tax, Avalara or TaxJar. Store **which rate was applied and why** on the order.
- **Prices with or without taxes included** is a product decision that affects every calculation.
- **Coupons:** validate on the server — validity period, maximum uses (global and per user), stacking,
  applicability to specific products and minimum purchase. **Usage must be consumed atomically** or a
  single-use coupon gets redeemed a thousand times in parallel.
- **Pricing:** per unit, tiered, volume, metered usage, freemium. The **usage-based
  model** forces you to aggregate consumption events reliably and idempotently — it is a distributed
  systems problem disguised as billing.

> **Card** · **When:** before selling in more than one country ·
> **Pattern:** delegate tax calculation (Stripe Tax, Avalara) and **store the applied rate** ·
> **Anti-pattern:** implementing per-country VAT by hand ·
> **Limits:** in the EU, B2C digital VAT is charged in the customer's country; B2B changes with a valid VAT number ·
> **How it fails:** a single-use coupon gets redeemed a thousand times in parallel without atomic consumption ·
> **Decision:** coupon usage is consumed in the same transaction as the order ·
> **Trade-off:** external engine (correct, per-transaction cost) vs in-house (cheap, tax risk) ·
> **Related:** business rules, transactions `[04, 17]`

---

## PCI DSS and compliance

- **If card data never touches your server** (Stripe Elements, hosted Checkout), you fall under the
  simplest questionnaire (SAQ A) and spare yourself an expensive audit. **This is the technical and economic reason to
  use the PSP's widget.**
- **Never store the full PAN, the CVV (never, not even encrypted) or the magnetic stripe.** Store the PSP's
  `payment_method_id`, the last 4 digits and the brand — enough for the UI.
- **Log carefully:** a log of the full request can end up containing a card number.
- **Retention:** invoices and accounting records have legal retention periods (several years), which
  clash with GDPR's "delete everything". The usual solution: anonymise personal data but keep the
  financial record.

> **Card** · **When:** before deciding how you capture the card ·
> **Pattern:** card data **never** touches your server → SAQ A ·
> **Anti-pattern:** storing the PAN; storing the CVV is a serious violation, encrypted or not ·
> **Limits:** accounting retention (years) clashes with the GDPR right to erasure ·
> **How it fails:** a log of the full request ends up containing a card number ·
> **Decision:** store `payment_method_id`, the last 4 and the brand; nothing else ·
> **Trade-off:** UX control vs audit cost and legal risk ·
> **Related:** compliance, logs, retention `[06, 15]`

---

## Implementation: the complete flow of a charge

```python
# 1) START: we create the intent and persist it BEFORE calling the provider.
async def start_payment(order_id: str, actor: User) -> str:
    async with uow.transaction() as tx:
        order = await tx.orders.lock(order_id)                  # SELECT ... FOR UPDATE
        if order.status != "pending_payment":
            raise InvalidTransition(order.status)

        attempt = await tx.payments.create(order_id=order.id, status="initiated",
                                           amount=order.total, currency=order.currency)
        # the idempotency key is DERIVED from the business, it is not a fresh uuid
        key = f"payment:{order.id}:{attempt.attempt_number}"

    pi = await stripe.PaymentIntent.create(                     # outside the transaction
        amount=order.total.cents, currency=order.currency.lower(),
        metadata={"order_id": order.id, "tenant_id": actor.tenant_id},
        idempotency_key=key)

    await repo.payments.save_reference(attempt.id, pi.id)
    return pi.client_secret

# 2) CONFIRM: only the webhook changes the state. The browser decides nothing.
async def handle_event(event: dict):
    if await repo.events.already_processed(event["id"]):        # at-least-once -> dedup
        return
    pi = event["data"]["object"]
    order_id = pi["metadata"]["order_id"]

    async with uow.transaction() as tx:
        await tx.events.mark_processed(event["id"])             # SAME transaction as the effect
        order = await tx.orders.lock(order_id)

        if event["type"] == "payment_intent.succeeded":
            # conditional transition: if another webhook already did it, 0 rows are affected and we exit
            if not await tx.orders.transition(order, "pending_payment", "paid"):
                return
            await tx.outbox.publish("OrderPaid", {"order_id": order_id})   # [08]
        elif event["type"] == "payment_intent.payment_failed":
            await tx.orders.transition(order, "pending_payment", "payment_failed")
```

**The five things that make this correct:** the intent is persisted before calling out · the idempotency
key derives from the business · the external call stays **outside** the transaction · deduplication
and the effect go **inside** the same one · and the transition is conditional, so out-of-order events and
duplicates break nothing.

**Reconciliation**, which is what saves you when webhooks get lost:

```python
async def reconcile():   # cron every 15 min
    for payment in await repo.payments.pending(min_age="10 minutes"):
        pi = await stripe.PaymentIntent.retrieve(payment.external_reference)
        if pi.status != payment.equivalent_status:
            await handle_event(synthesize_event(pi))   # reuses the same path
```

> **Card** · **When:** template for any charging integration ·
> **Pattern:** persist the intent → call out with a key → confirm via webhook → reconcile via cron ·
> **Anti-pattern:** calling Stripe inside an open transaction ·
> **Limits:** between the call and the webhook there is a window where the state is unknown ·
> **How it fails:** without reconciliation, a lost webhook leaves a paid order as pending forever ·
> **Decision:** webhooks are the happy path; reconciliation is the guarantee ·
> **Trade-off:** one extra cron in exchange for not depending on a third party's delivery ·
> **Related:** outbox, idempotency, webhooks `[03, 08, 16]`

---

## Failure modes: a payments system

| Failure | Why it happens | How to prevent it |
|---|---|---|
| **Duplicate charge** | retry after a timeout without a key | idempotency key derived from the order |
| **Charged with no order** | the webhook arrived and the order doesn't exist or failed to save | the intent is persisted **before** calling out |
| **Paid order still "pending"** | lost webhook | periodic reconciliation |
| **Double transition** | two simultaneous webhooks | `UPDATE ... WHERE status = previous` |
| **Out-of-order events** | `succeeded` before `checkout.completed` | state-based logic, not sequence-based |
| **Tampered price** | the client's amount was trusted | recalculate on the server |
| **Overselling** | check-then-act on the stock | conditional atomic update |
| **Invalid signature** | the signature was computed over the parsed body | HMAC over the raw bytes |
| **Duplicate refund** | job retry without a key | idempotency on refunds too |
| **Accounting mismatch** | payment date ≠ settlement date | reconcile against the payouts report |
| **Wrong currency** | amount with no associated currency | `Money` value object |
| **Card in the logs** | the full request was logged | redaction in the logging layer `[06]` |

**Ambiguous state is the core problem of this box:** on a timeout you **don't know** whether the charge
happened. You can't eliminate it — only make it safe with idempotency and discoverable with reconciliation.

> **Card** · **When:** review before charging real money ·
> **Pattern:** every row in this table should have a test ·
> **Anti-pattern:** testing only the happy path in the provider's sandbox ·
> **Limits:** the sandbox doesn't reproduce real timeouts or duplicates: simulate them yourself ·
> **How it fails:** money failures are detected late, by support or by accounting ·
> **Decision:** alert on payments stuck in an intermediate state for more than N minutes ·
> **Trade-off:** more checks and reconciliation vs delivery speed ·
> **Related:** integration testing, observability `[11, 12]`

---

## Interview questions and trade-offs

**Q: A user presses "pay" twice. How do you guarantee they aren't charged twice?**
An idempotency key derived from the order, both on your endpoint and towards the PSP, inserted in the same transaction
as the operation, with the response cached for the retry. *Signal:* you mention that the problem isn't just the
double click — it's the **network timeout**, where you don't know whether the charge happened, and there the key is the only thing
that saves you.

**Q: The `payment_intent.succeeded` webhook arrives twice and out of order. What do you do?**
Verify the signature, deduplicate by `event.id`, and make the logic idempotent and based on the object's state
rather than on the order of events. *Signal:* you say that at-least-once is the real guarantee and that out-of-order delivery is normal,
not an anomaly, and you add periodic reconciliation as a safety net.

**Q: Why not mark the order as paid on the `success_url`?**
Because the redirect depends on the user's browser and can be tampered with; the webhook is the PSP's
confirmation. *Signal:* you explain the practical UX — you show "processing" on return and confirm when the
webhook arrives — instead of leaving the user staring at an ambiguous screen.

**Q: How do you avoid selling more stock than you have in a flash sale?**
An atomic `UPDATE ... WHERE stock >= 1` and checking the affected rows, or reservations with a TTL. *Signal:* you identify
check-then-act as a race condition, and you mention that with heavy contention on a single SKU you should measure
whether the lock serialises every buyer.

**Q: How do you represent money?**
Integers in the minor unit or DECIMAL, always with a currency, in a value object. *Signal:* you mention currencies
with zero and three decimals, and that the exchange rate is frozen at the moment of the transaction.

**Q: What do you store from a card?**
Nothing sensitive: the PSP token, the last 4 and the brand. *Signal:* you connect this to PCI scope and to the
business argument (SAQ A versus a full audit), which is what convinces a CTO.

**Core trade-off of this box:** *control over the experience vs risk and compliance surface*.
Every step that brings card data closer to your server gives you UX control and multiplies your legal,
audit and incident costs. The senior consensus is to delegate everything you can to the PSP and keep the
business model for yourself: orders, access, reconciliation and state.

---

## Sources

- [Stripe Docs — Payment Intents](https://docs.stripe.com/payments/payment-intents) · [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) · [Webhooks](https://docs.stripe.com/webhooks)
- [Production-grade Stripe integration guide, 2026](https://tomodahinata.com/en/blog/stripe-checkout-sessions-payments-production-guide-2026) — Checkout Sessions, webhooks and idempotency.
- [Stripe Webhooks 2026: best practices](https://apiscout.dev/guides/stripe-webhooks-complete-guide-2026)
- [Mercado Pago — Checkout API](https://www.mercadopago.com.ar/developers/es/docs) · [PCI DSS v4.0](https://www.pcisecuritystandards.org/)
- Martin Fowler, [Patterns for Accounting](https://martinfowler.com/eaaDev/AccountingNarrative.html) — why entries are offset rather than deleted.
