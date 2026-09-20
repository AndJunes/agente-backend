---
title: Product-Market Fit
domain: strategy
type: concept
topics:
  - product-market fit
  - PMF
  - Sean Ellis test
  - PMF expansion
  - validation
source_count: 5
sources: [S005, S076, S111, S110, S090]
evidence_type: fragmentary
confidence: low
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Product-Market Fit

> **Coverage warning.** Product-market fit is referenced constantly across the corpus and
> **defined properly nowhere.** No source treats it directly. This document consolidates the
> fragments and flags the contradictions. **This is a priority gap** —
> see [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## The definitions available

| Source | Definition | Problem with it |
|---|---|---|
| [S005] | "**When your value proposition meets a real, underserved need, you have product-market fit**" | Circular — "underserved need" is not independently defined, and "meets" is not operationalised |
| [S076] | "a product that **your target market is willing to pay for**" | Willingness to pay is necessary but not obviously sufficient; says nothing about retention or scale |
| [S005], on the Osterwalder canvas | "**More overlap means you're closer to product-market fit**" | Treats PMF as a continuum rather than a threshold, which conflicts with the binary usage elsewhere |
| [S111] | Treats PMF as a **stage a product reaches**, after which feature, growth and scaling work apply, and which can later be **expanded** | The most structurally useful framing, but assumes PMF is identifiable without saying how |

> **These are not compatible.** Is PMF a threshold you cross, a degree of overlap, or a market
> condition you can measure? The corpus uses all three senses interchangeably.

## The one measurable test in the corpus

[S005]'s **Sean Ellis 40% test** is the only operational definition available:

> Ask users: **"How would you feel if you could no longer use this product?"**
> "**If 40% answer 'very disappointed' to your main benefit, you have the right product-market
> fit.**"

**Attribution** [S005]: "Benchmark popularized by **Sean Ellis**; also cited in **Croll &
Yoskovitz, *Lean Analytics*, O'Reilly, 2013**."

Covered in full, including what to do below 40% and the Superhuman survey, in
[value-proposition.md](value-proposition.md).

> **Caveats that must travel with this number.** The corpus contains no primary evidence for the
> 40% threshold, no information about sample requirements, no discussion of which users to survey
> (all users? active users? recent signups?), and no validation that the threshold predicts
> anything. It is a widely used heuristic with a named originator — not a measured constant. It is
> also an **attitudinal** measure, subject to all the cautions in
> [../02-discovery/surveys.md](../02-discovery/surveys.md).

## PMF as a stage, and PMF expansion

[S111] (Reforge) supplies the most useful structural framing in the corpus:

> "A product will hit **initial product-market fit**. Then, through feature work, growth work, and
> scaling work, the team works hard to fulfill and incrementally expand the potential of the
> initial PMF. **But, at some point growth of the product slows down as it hits some type of
> saturation.**
>
> **PMF expansion is increasing the ceiling on PMF in a non-incremental way** to expand into an
> adjacent market, adjacent product, or both."

This yields a sequence:

```
Pre-PMF          → find a market that wants the product
Initial PMF      → the threshold
  ├─ Feature work   → extend functionality into adjacent areas
  ├─ Growth work    → capture more of the existing market
  └─ Scaling work   → remove bottlenecks to shipping
Saturation       → growth slows
PMF expansion    → raise the ceiling non-incrementally
```

> **Why this matters for a PM agent:** the *type of product work that is appropriate depends on
> where the product sits in this sequence.* Growth tactics applied pre-PMF accelerate churn.
> Feature work applied at saturation produces the "6.4% adoption" problem [S031] describes. See
> [../01-foundations/pm-specializations.md](../01-foundations/pm-specializations.md).

## PMF as a hiring and staffing signal

[S097] names PMF validation as a condition that calls for a product manager rather than a project
manager: "A product manager should be your priority **if you're validating product-market fit**,
conducting user research, or defining your core value proposition."

[S111] describes the **Innovation PM** specialization as existing either as "the first product
hire, or co-founder, who helps the product reach initial PMF" or as part of an innovation team —
with key skills including "**PMF discovery and ability to pivot without attachment to ideas.**"

## PMF as a prioritization variable

[S081] uses PMF status to decide how much validation a decision needs:

> Skip a full opportunity assessment when "**you already have strong product-market fit and you're
> expanding features within a validated niche**" — in that case "lean on internal prioritization
> frameworks like RICE." Conversely, run one when building a net new product, because "you need to
> validate there's a real market gap and that your solution has a nice product-market fit."

[S031] applies the same logic to MoSCoW: reserve *Must* classifications for "legal, security,
privacy, evaluability, and truly **PMF-critical enablers**."

## What discovery contributes

[S110]: "Before you spend precious time and resources building something, **it's absolutely key to
find your product-market fit. What's the point of building something that no one wants?**"

[S076] connects it to ongoing measurement: "Achieving product-market fit... **will ensure continued
relevance, from the product discovery process all the way through iterations post-launch.**" Its
named inputs: interviewing customers, sending regular surveys, and assessing competitor products.

[S076] adds an observation worth keeping: "Your valued customer might not complain to you about a
feature they need not being offered; instead, **they may have gone out of their way to develop
their own hacked together solution for that need.**"

> Workarounds are evidence of unmet need — a behavioural signal, not an attitudinal one. See
> [../02-discovery/identifying-unmet-needs.md](../02-discovery/identifying-unmet-needs.md).

## What is missing

An agent should **not** answer the following from this knowledge base:

- A rigorous definition of product-market fit
- How to measure PMF other than the 40% survey
- Retention-curve-based PMF signals (flattening curves, cohort retention)
- Leading indicators of approaching PMF
- How PMF differs by market type (B2B vs B2C, enterprise vs SMB)
- Whether PMF can be lost, and how to detect that
- Marc Andreessen's and other canonical formulations
- The relationship between PMF and problem-solution fit
- How long PMF validation should take *(only [S106] gives an estimate in passing — "it probably
  takes 12-18 months to make a conclusive call on product/market fit" — offered as one founder's
  working assumption, not as guidance)*

## Related concepts

- [value-proposition.md](value-proposition.md) — the 40% test in full
- [product-led-growth.md](product-led-growth.md)
- [product-value.md](product-value.md)
- [../01-foundations/pm-specializations.md](../01-foundations/pm-specializations.md) — four types of product work relative to PMF
- [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md)
- [../02-discovery/product-discovery.md](../02-discovery/product-discovery.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S005 | Tempo — *4 product value proposition models* | Vendor guide | 40% test; value-proposition definition of PMF |
| S076 | Productboard — *Product Management Data for Discovery* | Vendor blog | Willingness-to-pay definition; workarounds as signal |
| S111 | Reforge — *The Growing Specialization of Product Management* | Practitioner framework | PMF as a stage; PMF expansion |
| S110 | Product School — *The Definitive Guide to Product Discovery* | Training-provider guide | PMF as a discovery objective |
| S090 | Aha! — *Product strategy frameworks* | Vendor guide | PMF referenced as a strategy topic |
