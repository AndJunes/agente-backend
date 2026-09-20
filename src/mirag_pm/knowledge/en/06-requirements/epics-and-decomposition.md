---
title: Decomposition — Initiatives, Epics, Stories and Tasks
domain: requirements
type: concept
topics:
  - epic
  - initiative
  - decomposition
  - story splitting
  - task
  - work breakdown
  - hierarchy
source_count: 4
sources: [S126, S127, S054, S097]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Decomposition — Initiatives, Epics, Stories and Tasks

## Two competing models

**The corpus contains two genuinely different models of decomposition. They are not
reconcilable and should not be merged.**

### Model A — a tiered hierarchy
[S126] (Atlassian):

> "User stories are also the building blocks of larger Agile frameworks, such as **epics and
> initiatives**. **Epics are large work items broken down into a set of stories, and multiple
> epics comprise an initiative.**"

```
Initiative
   └── Epic
        └── Story
             └── Task
```

[S126] gives the purpose of the tiering: "These larger structures ensure that the day-to-day
work of the development team contributes to the organizational goals built into epics and
initiatives."

### Model B — one kind of thing at different sizes
[S127] (Mountain Goat Software):

> "**An epic is a large story.** Epics are useful when the team wants to remember an important
> capability before knowing all the details. As the epic gets closer to development, it should
> be split into smaller stories the team can finish."

In this model there is no separate *epic* artefact type — an epic is a story that has not been
split yet. The only genuine type distinction [S127] draws is between **stories and tasks**:

> "A story describes a **useful outcome** from the perspective of someone who benefits from the
> work. A task describes **work the team performs** to deliver that outcome."

Its example:
- **Story:** *"As a customer, I can save a payment method so that checkout is faster next time"*
- **Task:** *"Create payment-token database table"*

### Which to use
Model A is embedded in tooling (Jira's issue hierarchy) and is useful for **portfolio-level
roll-up and reporting**. Model B is a **working discipline** that prevents the hierarchy from
becoming an end in itself.

They can coexist: a team can use Jira's tiers while treating an epic as "a story we haven't
split yet." What an agent should *not* do is assume a questioner's "epic" means the same thing
in both senses — the tooling sense implies a permanent container, the Cohn sense implies a
temporary state.

## The rule that governs splitting

Across both models, one constraint recurs:

> **A story should be small enough to finish in a sprint.**

- [S126]: "A story should be sized to complete in one sprint, so as the team specs each story,
  they make sure to break up stories that will go over that completion horizon." And: "stories
  that might take weeks or months to complete should be broken up into smaller stories or should
  be considered their own epic."
- [S127]: "A story that cannot be finished in a sprint is usually too large."
- [S128]: "User stories that take longer than a single sprint (typically two weeks) should be
  broken into smaller stories."

### Why oversized items are harmful
[S127] gives the mechanism rather than just the rule:

> "Large stories create the **illusion of progress**. Everyone is busy, but by the end of the
> sprint the work is still almost done. The backend is finished, but the UI is not. The happy
> path works, but important rules are missing. The feature exists, but no one is comfortable
> calling it complete."

And separately: "Large stories **hide complexity** and make progress hard to see."

## The splitting anti-pattern

[S127] names one specific failure in its pre-sprint readiness checklist:

> **"Has the team avoided splitting the story only by technical layer?"**

Splitting a story into "build the API", "build the UI", "write the migration" produces items
that are individually finishable but **none of which delivers a useful outcome**. It converts
stories into tasks while keeping the story label — which is [S127]'s mistake #3: "Splitting
Stories Into Tasks. **Tasks organize work. Stories describe useful outcomes.**"

[S127]'s criterion for a good split: smaller stories that "**still represent meaningful
progress**. The goal is not to create more backlog items. The goal is to help the team finish
work and get feedback."

## Decomposition is progressive, not up-front

This is the point that connects decomposition to the rest of product work.

[S127]: "A story should have enough detail for the team's current decision... **Stories near the
top of the backlog need more clarity** because the team may work on them soon. **Stories lower in
the backlog can stay larger and less detailed** because priorities, users, and solutions may
change."

The implication: **an item's position in the backlog determines how decomposed it should be.**
Decomposing everything up front is waste, because "priorities, users, and solutions may change"
— the same argument [S127] makes against traditional requirements documents.

The mechanism for progressive decomposition is **product backlog refinement** — "where vague
ideas become clearer stories, large stories are split, risks surface, and acceptance criteria
emerge." [S127]

## Seeing the whole before splitting: story mapping

[S127]: story mapping "helps teams see how stories fit together across a user journey, workflow,
product area, or significant objective. A story map can reveal **missing steps, alternatives,
assumptions, and release options** that are hard to see in a flat backlog."

The three practices work as a set [S127]:
> "**Story mapping** helps teams see the larger picture. **Refinement** helps teams decide what
> is clear enough and valuable enough to do soon. **Story splitting** helps teams turn large
> ideas into work that can be finished."

## What sits above an epic

The corpus is thin here. [S126]'s "initiative" is the only named tier above epic, and it is
defined only as "multiple epics."

What the rest of the knowledge base supplies to fill the gap:

| Level | What determines it | Where treated |
|---|---|---|
| **Outcome / goal** | Product strategy and OKRs | [../04-strategy/okrs.md](../04-strategy/okrs.md) |
| **Opportunity** | Discovery — a problem or unmet need that, if addressed, advances the outcome | [../02-discovery/discovery-frameworks.md](../02-discovery/discovery-frameworks.md) (Opportunity Solution Tree) |
| **Initiative / solution** | Prioritization among candidate solutions to an opportunity | [../05-planning/prioritization.md](../05-planning/prioritization.md) |
| **Roadmap item** | What the team communicates it is pursuing | [../05-planning/roadmaps.md](../05-planning/roadmaps.md) |
| **Epic → Story → Task** | Decomposition, progressively, as work approaches | this document |

> **Caution: this table is a synthesis, not a model any single source states.** The Opportunity
> Solution Tree ([S110]) and the epic/story hierarchy ([S126]) come from different traditions and
> the corpus never connects them. The table is offered as a reasoning aid, and the connection
> between the "opportunity" and "initiative" levels in particular is an inference.
> See [../CONCEPT_GRAPH.md](../CONCEPT_GRAPH.md), where the same caveat applies.

## Not everything should be a story

[S127] is explicit that forcing the form is a mistake:

> "Sometimes technical work can be described from a meaningful user, business, product, risk, or
> operational perspective. Other times it is better treated as a **technical backlog item, spike,
> chore, or task. Do not force everything into user story form.** Use the form that helps the
> team have the best conversation about the item."

[S052] offers the same flexibility across formats: mix user stories and job stories in the same
backlog. See [job-stories.md](job-stories.md).

## Limitations

- **Splitting patterns are absent.** [S127] establishes *that* splitting matters and names one
  anti-pattern, but the actual techniques — splitting by workflow step, business rule, data
  variation, interface, effort, or acceptance criterion — are in linked articles **not in the
  corpus**. This is the most practically significant gap in this document.
- **No worked decomposition example.** Nothing in the corpus takes one initiative and follows it
  down to tasks.
- **"Initiative" is defined in one clause by one vendor.** It is a tooling concept here, not a
  documented practice.
- **No treatment of work breakdown structures**, despite the corpus containing project-management
  sources; [S097] mentions only that project managers "break large initiatives into smaller,
  manageable tasks and identify dependencies between different work streams."
- **No coverage of how decomposition interacts with estimation** beyond the sprint-fit rule.

## Related concepts

- [user-stories.md](user-stories.md)
- [job-stories.md](job-stories.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [scope-definition.md](scope-definition.md)
- [../05-planning/backlog-management.md](../05-planning/backlog-management.md)
- [../05-planning/estimation.md](../05-planning/estimation.md)
- [../05-planning/roadmaps.md](../05-planning/roadmaps.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S126 | Atlassian — *User stories with examples and a template* | Vendor guide | Initiative→epic→story hierarchy, sprint-sizing rule |
| S127 | Mountain Goat Software (Mike Cohn) — *User Stories* | Practitioner guide | Epic as large story, story vs task, splitting rules and anti-pattern, progressive detail, story mapping, not-everything-is-a-story |
| S054 | Mind the Product — *Jobs to be done for Product Managers* | Practitioner essay | Anchoring work to jobs rather than features |
| S097 | Atlassian — *Product manager vs. project manager* | Vendor guide | Project manager's decomposition and dependency identification |
