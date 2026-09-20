---
title: Backlog Management
domain: planning
type: process
topics:
  - product backlog
  - backlog refinement
  - grooming
  - backlog health
  - backlog ownership
source_count: 5
sources: [S032, S127, S138, S042, S019]
evidence_type: professional-practice
confidence: low
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Backlog Management

> **Coverage warning.** No source in the corpus is about backlog management. This document
> assembles what exists across sources on other topics. Refinement is covered well (via [S127]);
> backlog structure, ordering, sizing and hygiene are largely absent. The gaps are recorded
> explicitly below and in [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Definition

[S032]: "A product backlog is a **prioritized inventory of features, defects, or technical work
that has yet to be worked on.** It should be work that is considered valuable from the product
owner's perspective. It can also include **ideas that have been identified and, in some cases,
prioritized** to include in future releases."

Three properties follow from this definition:
1. **Candidates, not commitments.** Backlog items are not promised work.
2. **Heterogeneous.** Features, defects and technical work share the same queue.
3. **Ordered by definition.** "Prioritized" is part of what makes it a backlog rather than a list.

## Ownership

| Source | Position |
|---|---|
| [S078] | The **product owner** "owns team backlog and fulfillment work"; the product manager "owns vision, marketing, ROI" |
| [S127] | "**The product owner is accountable for the product backlog, but that does not mean the product owner should personally write every item.**" Developers, testers, designers, analysts, Scrum Masters, stakeholders, customers and users can all contribute |
| [S128] | "In many agile organizations, the product owner takes primary responsibility... In reality, though, this is a **shared responsibility** among the entire cross-functional product team" |
| [S064] | **Measured disagreement**: PM and UX respondents did not align on who should "maintain the product backlog" |

> The consistent distinction across sources is **accountability vs authorship**. One role is
> answerable for the backlog's order and content; many people contribute items.

## Product backlog vs development backlog

[S042] references separating "the [product] backlog from the development backlog." The corpus
does not develop this, but the distinction is useful and consistent with everything else here:

| | Product backlog | Development backlog |
|---|---|---|
| Holds | Options and candidates | Work the team has taken on |
| Commitment | None | Committed |
| Governed by | Prioritization | Sprint or flow capacity |

## Refinement

This is the best-covered aspect. [S127] (Mountain Goat Software):

> "**Product backlog refinement helps the team add the right amount of understanding at the right
> time.** It is where vague ideas become clearer stories, large stories are split, risks surface,
> and acceptance criteria emerge."

### The governing principle: detail scales with proximity
[S127]:

> "Stories **near the top of the backlog need more clarity** because the team may work on them
> soon. **Stories lower in the backlog can stay larger and less detailed** because priorities,
> users, and solutions may change."

**The test** [S127]: *"Does the team understand this story well enough to believe it can be
completed in a sprint?"* If yes, it has enough detail for now. If no, "add detail through product
backlog refinement, conversation, examples, acceptance criteria, or story splitting."

> The reasoning matters: refining everything up front is waste, because items far down the
> backlog may never be built, and their context may change before they are. This is the same
> argument [S127] makes against comprehensive requirements documents — see
> [../06-requirements/user-stories.md](../06-requirements/user-stories.md).

### Refinement is a team activity
[S138]: "Make **work item triage and backlog grooming a team sport**... These are great
opportunities to make sure everyone is on the same page, and understand **why the product owner
has prioritized work the way they have.**"

> Note the second clause. Refinement is not only about clarifying items; it is a recurring venue
> for making prioritization reasoning visible — which [S039] identifies as the root fix for
> stakeholder friction. See [prioritization.md](prioritization.md).

## Feeding the backlog

[S019] describes the input problem at scale: feedback arrives from "social media, community
support, customer support, direct calls, emails, analytics, meeting notes, leadership steers,
tech ticketing tools." Its recommendation: "**Find a way to create a system of record that serves
as the single source of truth for all needs.**"

And it connects intake to prioritization: "**Don't neglect having a framework to prioritise at
scale. Your prioritization framework and tool should talk to each other** to parse through the
volumes of feedback and ideas to pick up broad patterns, problem statements and needs."

> [S019] is a practitioner guest post and its advice is experiential, not evidenced. The
> underlying observation — that unstructured intake overwhelms prioritization — is corroborated
> by [S031]'s account of having "more candidate features in the backlog than your scorecard can
> rank."

## Backlog pathologies named in the corpus

| Pathology | Source and description |
|---|---|
| **The "backlog beast"** | [S042] names this as a maturity-stage failure, alongside "feature factory" — a backlog that has grown beyond any possibility of being worked |
| **Tetris-packing** | [S108]: "teams pack their roadmaps like they're playing Tetris, only to discover — over and over — that they 'don't get to things'" |
| **Backlog as strategy** | [S003]: "a backlog is no place to plot a path toward achieving major strategic goals and initiatives. **The backlog is the land of details, while the roadmap is the domain of big ideas and themes**" |
| **Too large, too vague, too detailed, too technical** | [S127] addresses its guide to anyone "working with a backlog that has become too large, too vague, too detailed, too technical, or too hard to finish in a sprint" — naming the failure modes without treating them |

## What the corpus does not cover

These are real gaps, not omissions of convenience:

- **Ordering methods.** How a backlog is actually sequenced beyond "prioritized."
- **Backlog size management.** No guidance on how large a backlog should be, or what to do when
  it exceeds that.
- **Stale item handling.** No policy for items that have sat unworked for long periods.
  [S040]'s "start by **removing any backlog items which are not required to create the desired
  outcome. Delete or archive them**" is the only deletion guidance in the corpus, and it is
  specific to an outcome-based transition.
- **Sprint backlog** as a distinct artefact from the product backlog.
- **Definition of Ready.**
- **Backlog metrics** — age, throughput, cycle time, WIP limits.
- **How defects are prioritized relative to features**, despite [S032]'s definition placing them
  in the same queue.

## Related concepts

- [roadmap-vs-backlog-vs-release-plan.md](roadmap-vs-backlog-vs-release-plan.md)
- [prioritization.md](prioritization.md)
- [../06-requirements/user-stories.md](../06-requirements/user-stories.md) — refinement, splitting, readiness
- [../06-requirements/epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md)
- [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S032 | Aha! — *Feature Prioritization* | Vendor guide | Backlog definition |
| S127 | Mountain Goat Software (Mike Cohn) — *User Stories* | Practitioner guide | Refinement, progressive detail, readiness test |
| S138 | Atlassian — *How to create a PRD* | Vendor guide | Refinement as a team activity |
| S042 | ProdPad (Janna Bastow) — *How to Manage the Maturity Stage of Product Life Cycle* | Practitioner blog | "Backlog beast"; product vs development backlog |
| S019 | Product School (guest, Schandre Terblanche) — *The Do's and Don'ts of Scaling Product Management* | Practitioner guest post | Feedback intake at scale, system of record |
