---
title: The Product Development Process
domain: execution
type: process
topics:
  - product development process
  - opportunity validation
  - design phase
  - development phase
  - launch and iteration
  - strategic fit
source_count: 2
sources: [S004, S070]
evidence_type: practitioner-framework
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# The Product Development Process

## Why a consistent process matters

[S004] (Reforge) grounds the argument in decision quality rather than efficiency:

> "As product managers, we're constantly building, launching, and iterating... Along the way, **we
> make a sequence of decisions about what to build, how to build, and how to improve.**
>
> **Since these decisions build on each other, it's important to understand what assumptions we're
> operating under, what facts we already have, and what past decisions we've already made.**"

> The value of naming phases is therefore **epistemic**: each phase tells you what kind of
> uncertainty you are currently resolving, and what should already be settled. A team that cannot
> say which phase it is in cannot say which questions are still open.

## The four phases

[S004] attributes the framework to **Jiaona Zhang (VP of Product at Webflow)** and **Anand
Subramani (SVP of Product at Path)**, both described as having "over 15 years of experience as
product leaders."

```
1. Opportunity Validation  →  2. Design  →  3. Development  →  4. Launch & Iteration
```

[S004] is careful about how prescriptive this is: "**Most** product and feature work tends to go
through these stages, **often in a linear fashion. While there are exceptions**, these stages
provide **a good mental model to evaluate and classify decisions.**"

---

### Phase 1 — Opportunity Validation

**Three questions to ask** [S004]:

| Question | Dimension |
|---|---|
| "Is the feature or product going to be a **strategic fit** as it relates to our roadmap?" | **Strategic fit** |
| "Are we creating **value for the user**?" | **User value** |
| "Does building the feature or product indicate a **strong return on investment**?" | **Business value** |

**Strategic fit** [S004]: "When an opportunity is **aligned with the business strategy at every
level** it is a [strategic fit]."

> These three map closely onto the desirable / viable / feasible triad — see
> [../12-design-and-ux/product-triad.md](../12-design-and-ux/product-triad.md) — with *strategic
> fit* substituted for *feasible*. That substitution is telling: at the opportunity stage,
> alignment matters more than buildability, because a strategically misaligned opportunity is
> wasted effort no matter how easily it could be built. Feasibility is assessed in the next phase.

**Validation is not enough — alignment is part of the phase** [S004]:

> "**It's not enough to validate that an opportunity has all three components. Building alignment
> is a key part of the opportunity and validation phase.**"

**Four steps to build alignment** [S004] — two extracted:

1. **Conduct a manager briefing** — "a meeting with your manager in which you can **gather
   information about the project you have just been assigned, and align on the expectations of
   that work.**"
2. **Refine the user value** — "requires **direct engagement with users using quantitative and
   qualitative methods. User interviews are a foundational tool for product managers.**"

*(Steps 3 and 4 did not extract.)*

> The **manager briefing** is a small but often-skipped practice: explicitly surfacing what the
> assigning stakeholder believes the work is for, before doing it. It prevents the most common
> form of wasted effort — solving the problem you assumed rather than the one intended.

See [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md) for the
fuller assessment process, and
[../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md) for
validation methods.

---

### Phase 2 — Design
*(The section did not extract from the source.)*

The corpus's design coverage sits in
[../12-design-and-ux](../12-design-and-ux/product-design-fundamentals.md).

---

### Phase 3 — Development

[S004]: "focuses on the process of **executing on a product or feature that has been designed.**"

**Four key themes** [S004]:

| Theme | Definition |
|---|---|
| **Mapping your team** | "Determining **the work to be done and who will do it**" |
| **Preparation** | "The activities that need to happen **after design, but before any actual development work occurs**, to ensure projects are based on a solid foundation" |
| **Execution** | "The **structured approach to development that turns a design into a launch-ready feature**" |
| **Risk management** | Named as the fourth theme [S004]; see [../10-risk/risk-management.md](../10-risk/risk-management.md) |

[S004] also names **"Cross-Functional Dependency Management"** as a component of this phase — see
[../05-planning/dependencies.md](../05-planning/dependencies.md).

> The explicit **Preparation** step — work that happens *after* design and *before* development —
> is a distinction most process models omit. It is where requirements are clarified, dependencies
> confirmed, and edge cases identified. [S049] describes the same gap from the engineering side:
> "**identify all small cases with their flows by working with a designer and tester. Find them all
> before the engineers start working.**" See
> [working-with-engineering.md](working-with-engineering.md).

---

### Phase 4 — Launch & Iteration

See [../11-lifecycle-and-launch/product-launch.md](../11-lifecycle-and-launch/product-launch.md).

[S118] adds the practice that closes the loop: "Quickly following a launch, product managers should
lead a **product retrospective session.** This post-mortem meeting looks back on how the release
went. It ensures **lessons are captured and brought forward to improve things the next time
around.** These aren't just sessions for finger-pointing... it's an opportunity to offer praise,
recognize good work, and **collaboratively identify best practices and the areas needing
improvement.**"

---

## A ten-step alternative

[S070] (Aha!) presents a different, more granular sequence tied to its own framework. The steps
that extracted:

2. **Discover** — "Conduct customer interviews to uncover key product [needs]"
3. **Capture** — "Streamline customer feedback and collect promising [ideas]"
5. **Plan** — "**Prioritize ideas based on strategic goals, estimated [value and effort]**"
6. **Showcase** — "Share roadmaps and go-to-market plans with [stakeholders]"
8. **Document** — "Centralize product knowledge for internal teams"
10. **Analyze** — "**Assess realized product value by tracking customer** [outcomes]"

[S070] also names adjacent frameworks in a comparison table — **Design Thinking** ("a framework for
design," beginning with *Empathize*), **concept testing**, **market strategy**, and **technical
product** [development].

> [S070]'s ten steps are a **vendor's workflow**, mapped to its own tool's modules. Its value here
> is limited to corroborating the phase sequence. **[S004]'s four-phase model is the better
> framework** — it is attributed to named practitioners, it explains *why* phases matter, and it is
> not tied to a product.

## Where this sits relative to other process models

| Model | Scope | Where |
|---|---|---|
| **Four phases** [S004] | One feature or product, end to end | This document |
| **Double Diamond** | Problem framing through solution delivery | [../02-discovery/discovery-frameworks.md](../02-discovery/discovery-frameworks.md) |
| **Dual-track** | Discovery running parallel to delivery | [../02-discovery/discovery-frameworks.md](../02-discovery/discovery-frameworks.md) |
| **Product lifecycle** | A product's whole market life | [../11-lifecycle-and-launch/product-lifecycle.md](../11-lifecycle-and-launch/product-lifecycle.md) |

> These are **not competing models.** The four phases describe *a piece of work*; the lifecycle
> describes *a product's market existence*; dual-track describes *how discovery and delivery relate
> in time*. Confusing them produces category errors — e.g. treating "launch" as the end of the
> process when it is the beginning of the growth stage.

## Limitations

- **[S004] is Reforge content** and several sections (Phase 2, alignment steps 3–4) did not
  extract. What remains is well-attributed and substantive.
- **[S070] is vendor workflow documentation** with limited independent value.
- **No evidence** that a consistent process improves outcomes; [S004] argues from decision
  coherence.
- **Phase 2 (Design) is effectively missing** from this document.
- **The corpus contains no treatment of how phases overlap or iterate in practice** — [S004]
  acknowledges "exceptions" without describing them.
- **No coverage of stage-gate processes, or of how this maps to agile iteration.**

## Related concepts

- [agile-manifesto.md](agile-manifesto.md)
- [working-with-engineering.md](working-with-engineering.md)
- [project-monitoring-and-control.md](project-monitoring-and-control.md)
- [../02-discovery/discovery-frameworks.md](../02-discovery/discovery-frameworks.md)
- [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md)
- [../11-lifecycle-and-launch/product-lifecycle.md](../11-lifecycle-and-launch/product-lifecycle.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S004 | Reforge — *4 Key Stages Of The Product Development Process*, 2023 | Practitioner framework, attributed to Jiaona Zhang (Webflow) and Anand Subramani (Path) | Four phases, decision-coherence rationale, opportunity validation questions, alignment steps, development themes |
| S070 | Aha! — *Product Development: A Comprehensive Guide for Product Managers*, updated Sep 2025 | Vendor guide | Ten-step alternative sequence, adjacent framework names |
