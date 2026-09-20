---
title: Product Launch
domain: lifecycle
type: process
topics:
  - product launch
  - launch plan
  - launch types
  - launch metrics
  - post-launch retrospective
  - beta program
source_count: 4
sources: [S124, S072, S118, S034]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Product Launch

## What a launch plan contains

[S124] (ProductPlan) gives a seven-part structure:

| # | Component |
|---|---|
| 1 | **Product launch objectives** |
| 2 | **KPIs and success metrics** |
| 3 | **Timeline and launch date** |
| 4 | **Budget** |
| 5 | **Channels** |
| 6 | **Messaging / creative** |
| 7 | **Key stakeholder approval** |

Plus a **pricing strategy and structure** checklist [S124]:
1. "Business model defined (i.e., **freemium, SaaS, advertising-driven, one-time sale**)"
2. "Agreement on the **cost of goods sold** (if applicable)"
3. "**Competitor pricing understood**"
4. "Pricing (including any **product tiers/options**)"
5. "**Wholesale vs. retail pricing**"

> Item 7 — **key stakeholder approval** — is an artefact of the plan, not an afterthought. It names
> explicitly who must sign off before launch, which is the mechanism that prevents the "we didn't
> know this was shipping" failure. Compare [S113]'s PRD review order in
> [../06-requirements/prd.md](../06-requirements/prd.md).

[S124] also names launch objectives: "**Increase revenue**," "**Operational processes**," and
"**Establishing goals**," and distinguishes **feature launches** from full product launches — "**Many
products have North Star metrics and KPIs. A product launch can** [be measured against them]."

It references a **go-to-market plan** as a component of launch work. See
[go-to-market.md](go-to-market.md).

## Launch is a stage, not an event

[S072] places launch inside the **introduction stage** of the lifecycle and describes what actually
happens there:

> "The introduction stage centers around the go-to-market strategy. This includes **defining product
> positioning, a promotion plan, and timing for a launch event.** Product teams **gauge how well
> they assessed product-market fit during the development stage by analyzing the early market and
> customer feedback. The goal is to identify and act on opportunities to refine** [the offering]."

Its named activities for the stage: "**Fixing bugs and enhancing functionality**" and "**Prioritizing
features on the product roadmap.**"

> **The launch is a measurement opportunity, not a finish line.** Its primary output is evidence
> about whether the product-market fit assumption held. See
> [../04-strategy/product-market-fit.md](../04-strategy/product-market-fit.md).

### Beta programs
[S072]: "Some organizations choose a **beta program, giving a small group of users early access in
exchange for detailed** [feedback]."

[S073] independently names **beta testing** as one of five research types: "the first thing you
manage to get into users' hands is an MVP or a beta version... **User insights might have told you
that customers are interested in a product like yours, but an MVP will make sure that you're
building it in the right way.**"

[S077] adds it to the PM's responsibilities: "**Runs beta and pilot programs during the qualify
phase with almost final products and samples.**"

## After the launch

[S118] is the corpus's clearest statement that launch does not end the work:

> "**After the product ships, product managers don't get to kick up their heels and relax. There's
> still plenty of work to be done.**"

### The post-launch retrospective
> "Quickly following a launch, product managers should lead a **product retrospective session.
> This post-mortem meeting looks back on how the release went. It ensures lessons are captured and
> brought forward to improve things the next time around.**
>
> **These aren't just sessions for finger-pointing and blaming others for what went wrong.
> Instead, it's an opportunity to offer praise, recognize good work, and collaboratively identify
> best practices and the areas needing improvement.**" [S118]

> ⚠ **This is the only description of a retrospective anywhere in the corpus**, and it is a
> *launch* retrospective, not a sprint retrospective. Sprint retrospectives are named by [S062]
> ("Agile Retros") and implied throughout, but **never described.** Recorded as a gap — see
> [../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md).

### The attention shift
[S118] describes how focus moves after launch: "**the focus quickly shifts to growth.** Product
management worries about **scale** while adding functionality that continues to propel growth. **Once
all those new users are onboard, the emphasis transitions to retention.** It's all about what's
required to keep customers happy and minimize churn."

See [product-lifecycle.md](product-lifecycle.md) and
[../09-metrics/pirate-metrics.md](../09-metrics/pirate-metrics.md).

## Launch risk

[S087] names **"weak product launch strategy"** as a distinct product risk:

> "**You have a good product, but it's introduced to the market without the right positioning,
> timing, or internal support. The launch underperforms — not because of the product itself, but
> because it didn't reach the right audience the right way.**"

> This is the failure mode a launch plan exists to prevent, and it is **independent of product
> quality.** See [../10-risk/product-risk.md](../10-risk/product-risk.md).

[S106] adds a decision-quality consideration specific to launches — the **one-way door**:

> "The decision on whether to launch a product at the end of the quarter is typically a **two-way
> door** decision. If we ship the wrong product and people are frustrated, that's OK. **We can
> iterate on it.**
>
> On the other hand, the decision to do a **Product Hunt launch** for that product is a **one-way
> door** decision. If we launch and the product isn't ready, then **we've used up our one shot.**"

> **The same product can present both kinds of launch decision.** Shipping is usually reversible;
> a publicity moment is not. They should be planned and gated differently. See
> [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md).

## Coordination

[S119] names the stakeholders who need lead time: "**Sales and marketing are also critical
stakeholders to share the product roadmap with to plan out their go-to-market activities for key
releases and major new functionality.**"

[S034]'s sixth GTM component — **operating model and enablement** — covers the same ground: who
owns execution, how functions decide together, and "**what enablement do sales and success teams
need to tell the story.**" See [go-to-market.md](go-to-market.md).

## Limitations

- **[S124] is largely a checklist** from a roadmapping vendor; much of the article did not extract
  and what remains is structure without method.
- **No evidence** about what makes launches succeed or fail.
- **No treatment of launch tiers** (soft launch, phased rollout, general availability), despite
  [S042] describing Facebook's hyper-segmented rollouts in the maturity context — see
  [managing-maturity.md](managing-maturity.md).
- **No treatment of feature flags, canary releases, or rollback plans**, though [S031] names
  **reversibility** as a prioritization criterion.
- **No launch communication templates or press/analyst guidance.**
- **Sprint retrospectives remain undocumented** (see above).
- **No treatment of launch for regulated products** requiring approvals.

## Related concepts

- [go-to-market.md](go-to-market.md)
- [product-lifecycle.md](product-lifecycle.md)
- [../05-planning/release-planning.md](../05-planning/release-planning.md)
- [../10-risk/product-risk.md](../10-risk/product-risk.md)
- [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md) — one-way vs two-way door launches
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md)
- [../04-strategy/positioning.md](../04-strategy/positioning.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S124 | ProductPlan — *Ultimate Guide to Product Launch* | Vendor guide | Seven-part launch plan, pricing checklist, launch objectives |
| S072 | Aha! — *Product Lifecycle* | Vendor guide | Launch as the introduction stage; beta programs |
| S118 | ProductPlan — *The Ultimate Guide to Product Management* | Vendor guide | Post-launch retrospective, attention shift after launch |
| S034 | Product School — *Go-to-Market Strategy for Product Marketing Teams* | Training-provider guide | Operating model and enablement |
