---
title: Release Planning
domain: planning
type: process
topics:
  - release plan
  - release criteria
  - milestones
  - launch readiness
  - release notes
source_count: 5
sources: [S035, S076, S084, S048, S124]
evidence_type: professional-practice
confidence: low
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Release Planning

> **Coverage warning.** Release planning is **one of the thinnest areas in the corpus.** No
> source treats it directly; the material below is assembled from scattered mentions across
> roadmap and PRD sources, and the two definitions available **contradict each other on a
> basic point.** This is a high-priority gap — see [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Definition — and a contradiction

| Source | Definition | Carries dates? |
|---|---|---|
| [S035] | "The **execution-level plan of how you'll deliver the work that you've decided to do and the timeframe when that work will be completed.**" | **Yes** — timeframe is part of the definition |
| [S076] | "Many products are not one-and-done in terms of their development. SaaS products or even consumer mobile apps are expected to improve with successive versions. A release plan is a good way to **plot these milestones at a high level *without committing to a particular timeframe*.**" | **No** — explicitly decoupled |

> **Unresolved.** Both usages are in circulation. When the term appears, establish which is meant
> before acting. The difference is not cosmetic: one is a schedule, the other is a sequence.
> Recorded in [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

## Where a release plan sits

[S035] places it one layer below the roadmap: "**product roadmaps sit one layer above release
plans.**" See
[roadmap-vs-backlog-vs-release-plan.md](roadmap-vs-backlog-vs-release-plan.md).

[S084] places the PRD at the release level: a PRD "will contain **everything that must be
included in a release to be considered complete**, serving as a guide for subsequent documents in
the release process."

It also lists the artefacts clustered at this level: "**Release Plan, Release Notes, Product
Launch, Minimum Viable Product.**"

## Release criteria

[S048] is the only source giving a definition:

> "Identify the criteria that will determine whether **your product is customer-ready. This might
> include notes on functionality, usability, and reliability.** Once you check off these release
> criteria boxes, you can feel confident that you're launching a quality product."

[S086] lists **Performance: success metrics** as a PRD section, and [S113] lists
**Timeline/Release Planning: "What's the overall schedule you're working towards?"**

> **Release criteria are distinct from acceptance criteria.** Acceptance criteria gate an item;
> release criteria gate a shipment. See
> [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md).

## What a release plan is used for

Assembled from mentions across the corpus:

| Use | Source |
|---|---|
| **Coordinating go-to-market activity.** "Sales and marketing are also critical stakeholders to share the product roadmap with **to plan out their go-to-market activities for key releases and major new functionality**" | [S119] |
| **Setting downstream expectations.** Engineer-facing roadmaps "often focus on **features, releases, sprints, and milestones**" | [S119] |
| **Anchoring the PRD.** The PRD defines what must be in "a product release to be considered complete" | [S084] |
| **Structuring a launch.** A product launch plan includes "**Timeline and launch date**" among its components | [S124] |

## Release planning as an agile activity

The corpus covers sprint-level commitment but not release-level planning:

[S126]: "During a **sprint or iteration planning meeting**, the team decides what stories they'll
tackle that sprint. Teams now discuss the requirements and functionality that each user story
requires... Another common step in this meeting is to **score the stories based on their
complexity or time to completion.**"

[S130] describes a **Classic Sprint-Based Agile Roadmap** that "lays out objectives and
deliverables for each sprint."

> **There is no material in the corpus on release planning across multiple sprints** — no release
> burndown, no scope-vs-date trade-off mechanics, no guidance on fixed-date versus fixed-scope
> releases.

## Related topics that *are* covered

Where the corpus is thin on release *planning*, it is more substantial on the adjacent
activities:

- **Product launch** — [../11-lifecycle-and-launch/product-launch.md](../11-lifecycle-and-launch/product-launch.md)
- **Go-to-market** — [../11-lifecycle-and-launch/go-to-market.md](../11-lifecycle-and-launch/go-to-market.md)
- **Post-launch retrospective** — [S118]: "Quickly following a launch, product managers should
  lead a **product retrospective session.** This post-mortem meeting looks back on how the release
  went... **These aren't just sessions for finger-pointing and blaming others for what went
  wrong.** Instead, it's an opportunity to offer praise, recognize good work, and collaboratively
  identify best practices and the areas needing improvement."
- **MoSCoW as a release-scoping tool** — [S031]: MoSCoW "is **strongest as a release-planning tool
  and weakest as a portfolio-ranking tool.** Use it after you've already decided what to work on."
  See [prioritization-frameworks.md](prioritization-frameworks.md).

## What the corpus does not cover

- Release cadence decisions (continuous deployment vs scheduled releases vs trains)
- Fixed-date versus fixed-scope release strategies
- Release burndown, scope trading, or cut-line management
- Feature flags, staged rollouts, canary releases, dark launches
- Rollback planning — though [S031] names "**reversibility**" as a prioritization criterion:
  "ease of rollback or containment if adoption or quality disappoints"
- Release notes and versioning
- Coordinating releases across dependent teams

## Related concepts

- [roadmap-vs-backlog-vs-release-plan.md](roadmap-vs-backlog-vs-release-plan.md)
- [roadmap-formats.md](roadmap-formats.md) — release plan roadmap
- [dependencies.md](dependencies.md)
- [../06-requirements/prd.md](../06-requirements/prd.md)
- [../06-requirements/scope-definition.md](../06-requirements/scope-definition.md)
- [../11-lifecycle-and-launch/product-launch.md](../11-lifecycle-and-launch/product-launch.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S035 | Productboard — *Guide: How to Build a Product Roadmap* | Vendor guide | Release plan as execution-level plan with timeframe |
| S076 | Productboard — *Product Management Data for Discovery* | Vendor blog | Release plan without timeframe commitment |
| S084 | ProductPlan — *Product Requirements Document* (Glossary) | Vendor glossary | PRD at release level; related artefacts |
| S048 | Notion — *How to write a PRD in 7 simple steps* | Vendor blog | Release criteria |
| S124 | ProductPlan — *Ultimate Guide to Product Launch* | Vendor guide | Launch plan components |
