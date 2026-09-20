---
title: North Star Metric
domain: metrics
type: concept
topics:
  - north star metric
  - guiding metric
  - metric alignment
source_count: 4
sources: [S003, S080, S108, S098]
evidence_type: fragmentary
confidence: low
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# North Star Metric

> ## ⚠ This is a documented gap
>
> The North Star Metric is referenced by **four separate sources** in the corpus as something a
> product organization should have — and **not one of them defines it.** No source explains what
> qualifies as a North Star Metric, how to choose one, what distinguishes it from a KPI, or what
> the known failure modes are.
>
> This document records what exists so that an agent knows the term's *function* in the corpus
> without overstating what is actually known. See [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md) —
> priority 1.

## What the corpus asserts about it

### It is a roadmap alignment device
[S003]: "**If your organization already has a North Star metric, then your roadmap should be fully
reflective of that. The concepts presented in the roadmap should all directly or indirectly support
efforts to improve that metric. Make sure you can draw a clear line from each item to how it
directly impacts the North Star.**"

> This is the clearest statement of its function: **a single metric that every roadmap item must be
> traceable to.** It is a *filter*, not just a measure.

### It is the antidote to vanity metrics
[S080]: among common OKR mistakes, "**Setting vanity metrics**" — with the best practice being
"**Connect your OKRs to your Product's North Star to make sure there is a purpose behind your
goals.**"

### Its example in the corpus is not a metric
[S080] gives one example, and it is instructive that it is **qualitative**:

> "**Basecamp's Product North Star: make project management more of a joy and less of a chore.**
> When creating a progress tracking feature, your team might think about ways to increase
> simplicity, ease of use, and delighters."

> ⚠ **That is a product principle or mission statement, not a metric.** It cannot be measured as
> stated. Either [S080] is using "North Star" loosely, or it is conflating the North Star *Metric*
> with a North Star *statement*. **The corpus cannot resolve which.** Recorded in
> [../99-reference/disputed-information.md](../99-reference/disputed-information.md).
>
> Note the adjacent confusion documented in
> [../04-strategy/product-vision.md](../04-strategy/product-vision.md): [S094] uses "north star"
> metaphorically for the **product vision** — "A good product vision serves as the North Star for
> the product organization." **The term is used for at least three different things across this
> corpus: a vision, a principle, and a metric.**

### It grounds a roadmap in strategy
[S108] (John Cutler): "Note how I use a **North Star Metric and Inputs** to ground the roadmap in
our strategy, and introduce the idea of **persistent goals.**"

> "**Inputs**" here implies a structure — a top-level metric with contributing sub-metrics — which
> is consistent with [S019]'s primary/secondary KPI split in
> [product-metrics.md](product-metrics.md). But [S108] does not explain it, and the referenced
> diagram did not extract.

### It appears in growth contexts
[S124] (ProductPlan, on launch): "Many products have **North Star metrics and KPIs.**" — naming the
two as distinct without saying how.

## What can be safely inferred

From the four references together, the corpus supports only these claims:

1. **It is singular** — organizations have *a* North Star, not several.
2. **It is a top-level alignment device** — work is justified by its contribution to it.
3. **It is meant to counter vanity metrics** by supplying a purpose against which metric choices
   can be judged.
4. **It has contributing inputs** [S108], though their structure is unspecified.

Everything else — how to select one, whether it should be leading or lagging, how it relates to
revenue, its known failure modes — **is not in this knowledge base.**

## What is missing

- A definition
- Selection criteria, and what makes a candidate metric a poor North Star
- The distinction between a North Star Metric, a KPI, an OKR key result, and a product principle
- The input-metric tree structure [S108] alludes to
- Worked examples of real North Star Metrics (the one example given is not a metric)
- Known critiques — single-metric optimisation, Goodhart effects, and the risk of a North Star that
  is measurable but not meaningful
- How often it should change, if ever

## Related concepts

- [product-metrics.md](product-metrics.md)
- [pirate-metrics.md](pirate-metrics.md)
- [../04-strategy/okrs.md](../04-strategy/okrs.md)
- [../04-strategy/product-vision.md](../04-strategy/product-vision.md) — the vision is also called a "north star"
- [../05-planning/roadmap-communication.md](../05-planning/roadmap-communication.md)
- [../05-planning/continuous-roadmapping.md](../05-planning/continuous-roadmapping.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S003 | ProductPlan — *37 Roadmap Tips to Align Stakeholders* | Vendor guide | Roadmap traceability to the North Star |
| S080 | Product School — *Product OKRs* | Training-provider guide | Vanity-metric antidote; Basecamp example (flagged) |
| S108 | John Cutler — *TBM 2.1/52: Continuous Roadmapping* | Practitioner newsletter | North Star Metric and Inputs grounding a roadmap |
| S098 | Product School — *Product-Led Growth Strategy* | Training-provider guide | Growth-metric context |
