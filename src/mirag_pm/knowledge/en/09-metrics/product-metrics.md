---
title: Product Metrics
domain: metrics
type: concept
topics:
  - product metrics
  - KPI
  - churn
  - retention
  - conversion
  - activation
  - NPS
  - CSAT
  - CES
  - vanity metrics
  - outcomes over outputs
source_count: 6
sources: [S141, S044, S076, S080, S003, S031]
evidence_type: fragmentary
confidence: low
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Product Metrics

> **Coverage warning.** Metrics are referenced in almost every document in this knowledge base and
> **treated properly in almost none.** The corpus contains one article listing five metrics with
> short definitions, one NN/g article defining survey instruments, and scattered mentions
> elsewhere. There is **no source on measurement design, instrumentation, cohort analysis,
> statistical interpretation, or metric selection.** This is a **priority-1 gap** — see
> [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## The definitions the corpus does contain

### Behavioural / business metrics
From [S141]:

| Metric | Definition [S141] |
|---|---|
| **Churn rate** | "The number of customers or subscribers who **cut ties with your service or company, divided by the total number of customers during a given time period.** It's a vital performance metric for SaaS products because it is **inversely correlated with revenue**" |
| **User retention rate** | "The ability of a product to **retain its users over a specific period of time while keeping them engaged.**" Crucially: "**The retention rate varies with the industry of the product. Social media platforms may look into the daily user retention rate, while a SaaS product may look into the weekly rate**" |
| **Product adoption** | "A process by which customers **hear about a new product or a service and become recurring users of it.** It is a crucial aspect of customer health" |
| **Conversion rate** | "**The number of specific conversions divided by the total number of visitors.**" Worked example: "if an e-commerce site receives 200 visitors in a month and has 50 sales, the conversion rate would be 50 divided by 200, or **25%**." [S141] notes "a conversion can refer to any [defined action]" |

> The retention-rate note is the most useful line here: **the measurement period must match the
> product's natural usage frequency.** A weekly retention metric on a product used monthly measures
> nothing.

### Attitudinal / survey instruments
From [S044] (Nielsen Norman Group) — these are defined more rigorously than the behavioural metrics
above:

| Instrument | Definition [S044] | Caveat stated |
|---|---|---|
| **NPS** (Net Promoter Score) | "Respondents are asked to **rate their likelihood of recommending** a product or service to someone else... aggregated to produce a single score which **ranges from -100% to 100%**" | "**While the NPS does not directly address or assess the usability of a system**, it has been shown to correlate with usability decently well... **However, it should never be the only metric** used to assess the usability of a system" |
| **CSAT** (Customer Satisfaction) | "A 1-question survey... **typically administered after the completion of a journey or transaction.** The CSAT score represents **the percentage of respondents who rated their satisfaction as a 4 or a 5 (out of 5)**" | — |
| **CES** (Customer Effort Score) | "Similar to CSAT, but rather than asking about overall satisfaction, **it targets the ease of a particular action.** The CES is **the percentage of respondents who select the highest 3 options on a 1–7 ease scale**" | — |
| **SUS** (System Usability Scale) | "A **10-question survey** that has been used **since the 1980s** to assess the overall usability of a system" | Advantage: "it has **established reliable benchmarks for acceptable scores across industries and contexts**" |
| **SEQ** (Single Ease Question) | "Typically asks users to **rate the task on a 7-point scale from very difficult to very easy**" — administered post-task in usability testing | — |

[S141] also defines NPS: "a **loyalty measurement** taken by asking your users how likely they are
to recommend your product to other people **on a scale of zero to ten**."

> **These are attitudinal instruments.** They measure what people report, not what they do — see
> [../02-discovery/user-research-methods.md](../02-discovery/user-research-methods.md). All the
> survey cautions in [../02-discovery/surveys.md](../02-discovery/surveys.md) apply to them.

## Metric categories named across the corpus

Not defined, but repeatedly referenced — recorded so an agent knows the vocabulary exists:

| Category | Where referenced |
|---|---|
| **Acquisition, activation, retention, referral, revenue** | [pirate-metrics.md](pirate-metrics.md) |
| **CAC, ARPU, LTV** | [S111] (Growth PM skills), [S081] (ROI calculation: "customer acquisition costs, churn rates, market penetration, and lifetime value") |
| **Engagement, session duration** | [S080] (Netflix KPI example), [S031] |
| **Time to Value (TTV)** | [S098], [S104] ("Average trial TTV") |
| **Earned value metrics (EV, PV, SV, CV, EAC, ETC, TCPI)** | [S043] — named only; see [../10-risk/risk-monitoring.md](../10-risk/risk-monitoring.md) |
| **Feature adoption rate** | [S031] |

## Principles the corpus does establish

These are the durable parts, and they are worth more than the metric definitions.

### 1. Outcomes over outputs
[S080]: "**Stop thinking:** We succeeded because we launched 3 new features. **Start thinking:** We
succeeded because we reduced customer churn by 5%."

Its definitions: **outcome-focused** means "concentrating on the desired results or changes you want
to achieve"; **output-focused** "places the emphasis on producing deliverables, features, or
completing tasks, **regardless of whether they directly contribute to meaningful results.**"

See [../04-strategy/okrs.md](../04-strategy/okrs.md).

### 2. Avoid vanity metrics
[S003]: "**Link everything on your roadmap to how it advances crucial metrics. Make sure the ones
you're selecting are meaningful and not just for boosting egos or press release fodder. Pick ones
directly tied to customer satisfaction and business success and leave the rest on the cutting room
floor.**"

[S080] gives the antidote: "**Connect your OKRs to your Product's North Star to make sure there is
a purpose behind your goals.**"

[S087] names the failure as a product risk: "**If teams aren't tracking the right metrics, they
can't tell if the product is actually working. You risk celebrating vanity metrics while missing
signs of real trouble.**"

### 3. Fewer metrics, ranked
[S019]: "**Don't come up with a sea of KPIs. You will hypnotize yourself and your stakeholders. Try
splitting the primary and secondary KPIs.**" Its method: identify the primary KPI from the goal,
then "**look for secondary KPIs that directly contribute to the primary metric.**"

### 4. Check the data before trusting it
[S019]: "**Do check for data sanity and accuracy. There is no point of surfacing data that has
errors baked in.**"

[S051] makes the same point about risk assessment: "**the quality of data used... directly
correlates to the accuracy of the assessment and resulting decisions.**"

### 5. Combine quantitative with qualitative
[S076]: "Achieve a comprehensive understanding by **combining quantitative metrics with qualitative
insights. Qualitative is key here, as it provides more context into the 'why'.**"

[S074]: "**Both qualitative data and quantitative data can lie. The numbers don't always tell the
truth, but then again neither do customers!**" See
[../02-discovery/user-research-methods.md](../02-discovery/user-research-methods.md).

### 6. Define success metrics before building
Required by the PRD in [S085], [S086], [S113] and [S048]; by opportunity assessment in [S081]; and
by outcome-based roadmaps in [S040] and [S062]. [S085]: "**By defining clear metrics and success
criteria upfront, teams can track progress, identify areas for improvement, and ensure
alignment.**"

### 7. Two user streams may need two metric sets
[S031] argues that products used by both humans and AI agents need separate measurement:

| Stream | Unit of value [S031] |
|---|---|
| **Human** | "Time to first use, repeat use, depth of use, step-level drop-off rate, retention lift" |
| **Agent** | "**Task completion** — intent resolution rate, tool-call accuracy, authentication success, latency, fallback rate, human-intervention rate" |

Its warning: "**when an agent calls a tool 50 times in 30 seconds instead of clicking a button once,
the dashboard quietly under-reports.**"

> **Single vendor source, 2026, unverified** — but directly relevant to the intended use of this
> knowledge base. See [../05-planning/prioritization.md](../05-planning/prioritization.md).

## What is missing

An agent should **not** answer the following from this knowledge base:

- How to choose which metrics to track for a given product
- Leading versus lagging indicators
- Cohort analysis and retention curves
- Funnel analysis and conversion mathematics beyond a single division
- Statistical significance, sample sizing, confidence intervals
- A/B test design, duration, or interpretation
- Metric instrumentation and event taxonomy design
- Goodhart's law and metric gaming — despite "vanity metrics" being named repeatedly
- Benchmarks for any metric in any industry
- Dashboard and reporting design
- HEART, AARRR alternatives, or other metric frameworks beyond pirate metrics
- **North Star Metric** — see [north-star-metric.md](north-star-metric.md), which documents how
  little exists

## Related concepts

- [pirate-metrics.md](pirate-metrics.md)
- [north-star-metric.md](north-star-metric.md)
- [../04-strategy/okrs.md](../04-strategy/okrs.md)
- [../04-strategy/product-goals.md](../04-strategy/product-goals.md)
- [../02-discovery/surveys.md](../02-discovery/surveys.md) — where NPS, CSAT, CES and SUS are administered
- [../02-discovery/user-research-methods.md](../02-discovery/user-research-methods.md)
- [../05-planning/prioritization.md](../05-planning/prioritization.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S141 | *Why UX is Essential for PMs* (guest author), updated Jan 2024 | Practitioner blog | Churn, retention, adoption, NPS, conversion definitions |
| S044 | Nielsen Norman Group — *How to Run Surveys at Every Stage of the Design Cycle* | UX research organization | NPS, CSAT, CES, SUS, SEQ definitions and caveats |
| S076 | Productboard — *Product Management Data for Discovery* | Vendor blog | Quantitative/qualitative combination |
| S080 | Product School — *Product OKRs* | Training-provider guide | Outcomes over outputs; vanity-metric antidote |
| S003 | ProductPlan — *37 Roadmap Tips* | Vendor guide | Avoiding vanity metrics |
| S031 | Userpilot — *Feature Prioritization Matrix... 2026* | Vendor blog | Two-stream measurement (human vs agent) |
