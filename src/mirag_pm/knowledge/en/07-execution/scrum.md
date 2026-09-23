---
title: Scrum
domain: execution
type: framework
topics:
  - scrum
  - sprint
  - product owner
  - scrum master
  - developers
  - sprint planning
  - daily scrum
  - sprint review
  - sprint retrospective
  - product backlog
  - sprint backlog
  - increment
  - definition of done
  - product goal
  - sprint goal
synonyms:
  - scrum framework
  - scrum ceremonies
  - scrum events
source_count: 1
sources: [E001]
evidence_type: primary-text-quoted
confidence: high
corpus_origin: false
external_research: true
verified: true
phase: 2
provenance:
  primary: [E001]
  interpretation: []
  practice: []
  empirical: []
last_reviewed: 2026-09-16
---

# Scrum

> **Phase-2 document.** Built from the **primary text** — the Scrum Guide itself — not from
> second-hand descriptions. The original corpus referenced Scrum across at least six sources and
> defined it in none; see [../CORPUS_AUDIT.md](../CORPUS_AUDIT.md).
>
> **Source:** [E001] *The Scrum Guide*, Ken Schwaber and Jeff Sutherland, **November 2020**.
> Verified current as of September 2026 — the 2020 edition remains the latest; no 2025 or 2026
> revision exists.

## Definition

> "**Scrum is a lightweight framework that helps people, teams and organizations generate value
> through adaptive solutions for complex problems.**" [E001]

The Guide describes the framework in four steps: a Product Owner orders work into a Product
Backlog; the Scrum Team turns a selection of that work into an Increment during a Sprint; the team
and its stakeholders inspect the result and adjust; the cycle repeats.

### What Scrum is not
The Guide states its own boundary explicitly:

> "**Scrum is free and offered in this Guide. The Scrum framework, as outlined herein, is
> immutable. While implementing only parts of Scrum is possible, the result is not Scrum.**" [E001]

> This sentence is the basis for the "cargo cult agile" critique documented in
> [agile-manifesto.md](agile-manifesto.md). A team running stand-ups without a Product Owner, or
> Sprints without a Sprint Goal, is doing something — but by the Guide's own definition, not Scrum.

## Theory: empiricism and lean thinking

> "Empiricism asserts that **knowledge comes from experience and making decisions based on what is
> observed.**" [E001]

The framework rests on **three pillars**:

| Pillar | [E001] |
|---|---|
| **Transparency** | "The emergent process and work must be **visible to those performing the work as well as those receiving the work**" |
| **Inspection** | "The Scrum artifacts and the progress toward agreed goals must be **inspected frequently and diligently to detect potentially undesirable variances**" |
| **Adaptation** | "If any aspects of a process **deviate outside acceptable limits**... the process being applied or the materials being produced **must be adjusted**" |

> The three pillars explain *why* the events exist. Each event is an inspect-and-adapt opportunity;
> removing one removes a feedback loop, which is why the Guide treats the framework as immutable.

## The five values

> "**Commitment, Focus, Openness, Respect, and Courage**" [E001]

The team commits to goals and to supporting one another; focuses on the Sprint's work; is open
about the work and its challenges; respects members as capable, independent people; and has the
courage to do the right thing and work on hard problems.

## The Scrum Team

**One Scrum Master, one Product Owner, and Developers** — "typically 10 or fewer people." The team
is **cross-functional** and **self-managing**, with **no hierarchies and no sub-teams.**

### The three accountabilities

| Accountability | Responsible for [E001] |
|---|---|
| **Developers** | Creating the **Sprint Backlog plan** · maintaining quality by adhering to the **Definition of Done** · **adapting their plan each day** toward the Sprint Goal · holding each other accountable as professionals |
| **Product Owner** | **Maximizing the value of the product.** Developing and explicitly communicating the **Product Goal** · creating and clearly communicating **Product Backlog items** · **ordering** the Product Backlog · ensuring it is transparent, visible and understood |
| **Scrum Master** | Establishing Scrum as defined in the Guide; helping everyone understand Scrum theory and practice. Serves **the team** (coaching self-management, removing impediments, ensuring events are productive and within timebox), **the Product Owner** (techniques for Product Goal definition and backlog management, stakeholder collaboration) and **the organization** (training, adoption planning, removing barriers) |

### Two facts about the Product Owner that settle corpus disputes

1. > "**The Product Owner is one person, not a committee.**" [E001]

2. **The Product Owner is accountable for the Product Backlog — not necessarily its author.** The
   Guide assigns the accountability without requiring personal authorship, which is exactly the
   distinction [S127] drew in
   [../06-requirements/user-stories.md](../06-requirements/user-stories.md): *"The product owner is
   accountable for the product backlog, but that does not mean the product owner should personally
   write every item."*

> **Resolves a corpus ambiguity.** [S064] found PMs and UX professionals disagreeing about who
> "maintains the product backlog." The Guide answers it for teams running Scrum: **the Product
> Owner is accountable.** It does not, however, say how a *Product Manager* relates to a Product
> Owner — that relationship is outside Scrum's scope, which is why
> [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)
> remains genuinely contested.

## The five events

The **Sprint** is a container for the other four.

| Event | Purpose [E001] | Timebox (one-month Sprint) |
|---|---|---|
| **The Sprint** | "**Sprints are the heartbeat of Scrum, where ideas are turned into value.**" Fixed length, **one month or less**, to create consistency | — |
| **Sprint Planning** | Lays out the work to be performed | **8 hours max** |
| **Daily Scrum** | "**Inspect progress toward the Sprint Goal and adapt the Sprint Backlog as necessary**" | **15 minutes**, same time and place, for the Developers |
| **Sprint Review** | "**Inspect the outcome of the Sprint and determine future adaptations**" — with stakeholders | **4 hours max** |
| **Sprint Retrospective** | "**Plan ways to increase quality and effectiveness**" | **3 hours max** |

All timeboxes are **proportionally shorter for shorter Sprints.**

### Sprint Planning — the three topics
The whole Scrum Team collaborates on:

1. **Why is this Sprint valuable?** → the **Sprint Goal**
2. **What can be done this Sprint?** → Developers select Product Backlog items
3. **How will the chosen work get done?** → Developers decompose items into a plan

### Rules that hold during a Sprint
[E001]: **no changes are made that would endanger the Sprint Goal**; **quality does not decrease**;
the Product Backlog is refined as needed; and **scope may be clarified and renegotiated with the
Product Owner** as more is learned.

> That last clause matters for scope discussions — see
> [../06-requirements/scope-definition.md](../06-requirements/scope-definition.md). Scrum does not
> freeze scope; it protects the *Goal* and permits scope around it to be renegotiated.

### The Sprint Retrospective — what it actually inspects
[E001]: the team inspects "**individuals, interactions, processes, tools, and their Definition of
Done**," identifies the most helpful changes, and may add them to the next Sprint Backlog.

> **This is the corpus's biggest single omission now closed.** The only retrospective described
> anywhere in the original 143 sources was a *launch* retrospective ([S118]) — see
> [../11-lifecycle-and-launch/product-launch.md](../11-lifecycle-and-launch/product-launch.md).

## The three artifacts and their commitments

Each artifact has a **commitment** — a thing that makes it measurable and focused.

| Artifact | Definition [E001] | Commitment |
|---|---|---|
| **Product Backlog** | "An **emergent, ordered list of what is needed to improve the product**." The single source of work for the team. Refinement "breaks down items into smaller, more precise pieces" | **Product Goal** — "describes a **future state of the product** which can serve as a target for the Scrum Team to plan against." Long-term; must be fulfilled (or abandoned) before taking the next |
| **Sprint Backlog** | "Composed of the **Sprint Goal (why)**, the set of Product Backlog items selected for the Sprint **(what)**, as well as an actionable plan for delivering the Increment **(how)**" | **Sprint Goal** — "**the single objective for the Sprint**." It "creates coherence and focus, encouraging the Scrum Team to work together" |
| **Increment** | "A **concrete stepping stone toward the Product Goal**." Additive to prior Increments, **thoroughly verified, and usable.** Multiple Increments may be created within a Sprint | **Definition of Done** — "a **formal description of the state of the Increment when it meets the quality measures required for the product**" |

### Definition of Done — resolving a corpus error

> **Work cannot be considered part of an Increment unless it meets the Definition of Done.** [E001]

> **[CORRECTION to the original corpus.]** [S126] and [S128] both used "definition of done" to mean
> **story-level acceptance criteria**. The primary text is unambiguous: the Definition of Done is a
> **product-level quality standard applied to the Increment** — a commitment attached to the
> Increment artifact, not to an individual backlog item.
>
> The two are complementary, not interchangeable:
> - **Acceptance criteria** — item-specific; *did we build the right thing?*
> - **Definition of Done** — team- or product-wide; *is it releasable?*
>
> This correction is applied in
> [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md) and
> recorded in [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

## What Scrum deliberately does not say

The Guide is short by design, and its silences matter as much as its content. **Scrum does not
define:**

- **Estimation.** No story points, no velocity, no planning poker. These are widely-used
  *complements* to Scrum, not part of it. See
  [../05-planning/estimation.md](../05-planning/estimation.md)
- **User stories.** The Guide says "Product Backlog items," never "stories." The user-story format
  is an independent practice — see [../06-requirements/user-stories.md](../06-requirements/user-stories.md)
- **The Product Manager role**, or how it relates to the Product Owner
- **Backlog refinement mechanics** — it names refinement as an ongoing activity, without prescribing
  a meeting or a cadence
- **Roadmaps, releases or release planning**
- **Metrics** of any kind
- **How teams scale** beyond one Scrum Team

> **These are not gaps in the Guide — they are deliberate exclusions.** Scrum is described as
> "lightweight" and "purposefully incomplete." Practices layered on top (story points, refinement
> meetings, velocity charts) are conventions, and treating them as Scrum rules is a common error.

## Limitations

- **This document reflects one primary source.** It states what Scrum *is* by definition, not
  whether Scrum *works*, nor how it behaves in practice when partially adopted.
- **No empirical evidence** is presented here that Scrum improves outcomes. The Guide makes no such
  claim, and none was researched for this document. **[EMPIRICAL: not established in this knowledge
  base.]**
- **The Guide is prescriptive about structure and silent about technique.** It will not tell a team
  how to write a Sprint Goal well, how to run a useful retrospective, or how to order a backlog.
- **Scaling frameworks** (SAFe, LeSS, Nexus) are outside the Guide and outside this document.
- **The 2020 edition removed** material present in earlier editions (notably the three Daily Scrum
  questions). Descriptions of Scrum written before November 2020 — which includes several corpus
  sources — may reflect superseded guidance.

## Related concepts

- [agile-manifesto.md](agile-manifesto.md) — the values and twelve principles Scrum implements
- [kanban.md](kanban.md) — the main alternative, with a different theory of change
- [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)
- [../06-requirements/user-stories.md](../06-requirements/user-stories.md)
- [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md) — corrected by this document
- [../05-planning/backlog-management.md](../05-planning/backlog-management.md)
- [../05-planning/estimation.md](../05-planning/estimation.md)

## Sources

| ID | Source | Type | Provenance | Used for |
|---|---|---|---|---|
| E001 | **The Scrum Guide**, Ken Schwaber & Jeff Sutherland, November 2020 — [scrumguides.org](https://scrumguides.org/scrum-guide.html) | **Primary text by the framework's creators** | `PRIMARY` | Entire document. Verified as the current edition, September 2026 |
