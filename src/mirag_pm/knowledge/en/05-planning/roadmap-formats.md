---
title: Roadmap Formats
domain: planning
type: framework-catalogue
topics:
  - now next later
  - timeline roadmap
  - kanban roadmap
  - sprint roadmap
  - theme-based roadmap
  - agile roadmap
  - roadmap format selection
source_count: 4
sources: [S130, S062, S035, S119]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Roadmap Formats

## How to choose

[S035] states the selection rule: "The types of roadmaps you explore should be driven by **the
nature of the products you're developing, the business outcomes you're pursuing, and the kinds of
stakeholders with whom you'll be collaborating.**"

[S119] reduces this to a single prior step: "**before setting out to build a roadmap, its
audience must be identified** — this way, you can tailor the content, focus, and presentation to
their needs." See the audience table in [roadmaps.md](roadmaps.md).

> **Format is a consequence of audience and uncertainty, not a matter of taste.** A format that
> shows dates makes a promise; a format that shows priority order does not. Choose the one whose
> implicit promise you can keep.

## The formats

### Timeline-based
**What it is** [S062]: "designed around specific deadlines or project milestones."

**Strengths** [S062]: "helpful for aligning cross-functional collaboration and setting clear
expectations on deliverables. **The linear view makes tracking and accountability
straightforward.**"

**Weaknesses** [S062]: "sometimes it's known to become **rigid and challenging to adjust in
fast-changing environments**, especially if customer or market needs shift."

**When it fits:** [S062] names "companies where long-term predictability is essential, such as in
heavily regulated industries" — and recommends a hybrid there, "combining timeline predictability
with outcome goals."

---

### Now-Next-Later
**What it is** [S130]: "breaks down priorities into three simple buckets: **what's happening now,
what's coming next, and what's on the horizon for later.**"

**Strengths** [S130]: "shines by **avoiding rigid timelines and focusing on priorities instead.**
Teams can work at their own pace, adjusting plans as feedback comes in or market conditions
change."

**Weaknesses** [S062]: "While Now-Next-Later roadmaps show *what's* coming up in priority order,
**they don't inherently focus on specific outcomes.** A con... is that they can leave some product
teams lacking outcome orientation. They want to understand *why* something is prioritized and
**what specific results they should aim to achieve.**"

**The recommended combination** [S062]: "use **Now-Next-Later for broad timeframes and an
outcome-based structure to clarify the desired impact** of each initiative within those
timeframes." Worked example: *"Improve onboarding experience"* in the **Now** column, with the
outcome *"increase new user retention by 20%"* attached.

> Now-Next-Later and continuous roadmapping share a structure — staged buckets with decreasing
> detail — but differ in what fixes the size of each bucket. [S108] sizes by historical
> throughput; Now-Next-Later does not constrain bucket size at all, which is how it degrades into
> an unbounded wish list. See [continuous-roadmapping.md](continuous-roadmapping.md).

---

### Outcome-based
Treated in full in [outcome-based-roadmaps.md](outcome-based-roadmaps.md).

[S130]'s summary: "focuses on **what you want to achieve rather than how you'll get there.** It
prioritizes results, like improving user retention, over specific features or tasks... teams can
iterate and adapt as they figure out the best way to achieve their goals."

---

### Goal-oriented
**What it is** [S062]: sets "specific goals like *'Expand into new markets'* or *'Enhance user
security'*, often linking these to strategic company initiatives."

**How it differs from outcome-based** [S062]: "**Close relatives.** Where they differ is in their
**level of specificity around measurable outcomes.** Outcome-based roadmaps go further by
defining clear, trackable product metrics for success, such as 'increase retention in new markets
by 15%'."

---

### Feature-based
**What it is** [S062]: "focus primarily on delivering features."

**Strengths** [S062]: "straightforward and works well for communicating specific product
enhancements to stakeholders, especially in highly structured environments."

**Weaknesses** [S062]: leads to "a **'feature factory' mentality**, where the emphasis is on
building rather than solving strategic problems," and to "**feature creep**, where irrelevant and
unimpactful features find their way to production."

[S040] adds the precondition under which it is legitimate: "Such a plan **might work if there is
little uncertainty, change, and innovation present**, and you can correctly predict what the
product should look like and do."

---

### Classic sprint-based / agile
**What it is** [S130]: "a structured yet flexible way to outline work, often **visualized as
sprints or iterations tied to specific timeframes.** It lays out objectives and deliverables for
each sprint while leaving room for adaptability."

[S035] describes the same thing as a **sprint plan roadmap**: "timeboxed planning sessions where
everyone agrees on the backlog of items to complete. **More appropriate for product and
development teams**, sprint plan roadmaps clarify delivery schedules and keep people aligned."

> Note the audience constraint: this is an *internal delivery* artefact. [S119]'s guidance on
> engineer-facing roadmaps applies — more granular, shorter duration, but "product goals and
> themes should still be a component."

---

### Kanban roadmap
**What it is** [S130]: "visualizes progress using columns like **Backlog, In Progress, and Done**,
similar to a Kanban board."

**Properties** [S130]: "keeps things fluid and transparent. It enables teams to work on what's
most important at any given time. **With no strict deadlines, it's easy to reprioritize tasks as
new information arises.** It's Agile in its purest form: continuous flow, constant iteration."

> ⚠ **Naming correction (Phase 2).** What [S130] describes is a **board**, not a kanban system.
> [E003], the Kanban Method's own condensed guide, states the condition: *"For it to be a kanban
> system rather than simply a flow system, the commitment and delivery points must be defined, and
> WiP Limits must be displayed."* A Backlog / In Progress / Done board with **no WIP limits** is a
> flow visualisation — useful, and not the Kanban Method.
>
> **This matters practically, not pedantically.** [S130] praises the format because *"with no strict
> deadlines, it's easy to reprioritize."* [E003] would identify unlimited reprioritisation into an
> unbounded In Progress column as the **push system** the method exists to replace: work enters
> because it was prioritised, not because capacity freed up. The two documents recommend
> superficially the same artefact for opposite reasons.
>
> See [../07-execution/kanban.md](../07-execution/kanban.md).

---

### Release plan roadmap
[S035]: "Many products are not one-and-done in terms of their development... **A release plan is a
good way to plot these milestones at a high level without committing to a particular
timeframe.**"

See [release-planning.md](release-planning.md) and
[roadmap-vs-backlog-vs-release-plan.md](roadmap-vs-backlog-vs-release-plan.md) — the corpus is
inconsistent about whether a release plan carries dates.

---

### Theme-based
Named by [S119] as what purpose-built tooling enables: "visual, **theme-based roadmaps that
elevate the discussion above specific features and shift the focus to strategic goals.**"

[S003] reinforces the practice: "**Forget features and think about themes.**"

> The corpus never defines a *theme* precisely. It is used consistently to mean a grouping of
> related work under a strategic intent, sitting above features and below goals. Its absence of a
> definition is a small gap.

## What the agile variants share

[S130] characterises agile roadmaps across five properties, which apply to Now-Next-Later, Kanban,
outcome-based and sprint-based alike:

| Property | [S130] |
|---|---|
| **Outcome-oriented** | "Emphasize what you want to achieve rather than when and how every detail will be completed" |
| **Flexible and evolving** | "Not set in stone... designed to change as priorities shift, feedback rolls in, or market conditions evolve" |
| **Focus on short-term goals** | "Often concentrate on near-term objectives, **typically within a quarter or two.** This allows for regular reassessment" |
| **Collaborative by nature** | "A tool for alignment and communication across stakeholders... fosters shared ownership" |
| **Tied to iterative development** | "Align with iterative cycles, such as sprints in Scrum or increments in SAFe. Each iteration feeds into the roadmap" |

## Traditional versus agile: six axes

[S130]'s comparison is the corpus's most systematic. Each axis is a real trade-off, not a
value judgment:

| Axis | Traditional | Agile |
|---|---|---|
| **Detail** | "Granular details about how and when each feature will be implemented" | "High-level product vision and goals, leaving execution details to iterative planning cycles" |
| **Stability** | "Created at the beginning of a project and remain unchanged, even as circumstances evolve" | "Living documents, revisited and updated regularly" |
| **Dependencies** | "Rely on a strict sequence of dependencies, where **delays in one area can cascade into others**" | "Embrace prioritization based on immediate needs and value delivery... **without being constrained by rigid interdependencies**" |
| **Definition of success** | "Completion of tasks or features ('Did we deliver X on time?')" | "Achieving outcomes that provide measurable value ('Did we improve user retention?')" |
| **Direction of authority** | "Top-down approach, serving as a **reporting tool for executives**" | "Designed to **empower teams** by encouraging bottom-up feedback" |
| **Optimised for** | "**Predictability** — they build confidence by outlining exactly what will happen and when" | "**Resilience** — they ensure teams are prepared to respond effectively to changes" |

> **The last axis is the honest summary.** Predictability and resilience are both legitimate
> goals; the format should follow which one the organization actually needs. [S062] is explicit
> that agile/outcome formats are "**less effective for projects that require a strict,
> feature-driven approach or predictable delivery schedules.**"

## Limitations

- **The format lists overlap and are not mutually exclusive.** Outcome-based, Now-Next-Later and
  Kanban can describe the same artefact viewed differently. No source in the corpus organises
  them cleanly.
- **All sources are vendors or training providers**, and several format descriptions double as
  tool marketing.
- **No worked examples extracted.** [S062] and [S130] both reference roadmap images that did not
  survive PDF extraction.
- **No guidance on time horizons per format** beyond [S130]'s "a quarter or two" for agile.
- **Theme is undefined** (see above).

## Related concepts

- [roadmaps.md](roadmaps.md)
- [outcome-based-roadmaps.md](outcome-based-roadmaps.md)
- [continuous-roadmapping.md](continuous-roadmapping.md)
- [roadmap-communication.md](roadmap-communication.md)
- [roadmap-vs-backlog-vs-release-plan.md](roadmap-vs-backlog-vs-release-plan.md)
- [../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md)
- [../07-execution/kanban.md](../07-execution/kanban.md) — what a kanban system actually requires

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S130 | Product School — *What Are Agile Roadmaps and How to Build Them* | Training-provider guide | Agile roadmap properties, six-axis comparison, sprint/Now-Next-Later/outcome/Kanban formats |
| S062 | Product School — *Outcome-Based Roadmaps* | Training-provider guide | Format comparisons and their weaknesses, hybrid recommendations |
| S035 | Productboard — *Guide: How to Build a Product Roadmap* | Vendor guide | Format selection rule, release plan and sprint plan roadmaps |
| S119 | ProductPlan — *The Ultimate Guide to Product Roadmaps* | Vendor guide | Audience-first principle, theme-based roadmaps |
| **E003** | **Anderson & Carmichael — *Essential Kanban Condensed*, 2016** | **Primary text** | **Correction: the kanban-system condition (commitment/delivery points, WIP limits)** |
