---
title: Acceptance Criteria and Definition of Done
domain: requirements
type: artifact
topics:
  - acceptance criteria
  - definition of done
  - confirmation
  - testable requirements
  - release criteria
source_count: 7
sources: [S127, S126, S128, S048, S097, E001, E003]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: true
verified: partial
phase: 2
provenance:
  primary: [E001, E003]
  interpretation: [S126, S128]
  practice: [S127, S048]
  empirical: []
last_reviewed: 2026-09-16
---

# Acceptance Criteria and Definition of Done

## Definition

[S127] (Mountain Goat Software): "Acceptance criteria are details that help the team understand
whether a story has been completed correctly."

Its crucial qualification about form:

> "They may take the form of **examples, rules, tests, or brief notes. The wording matters less
> than the shared understanding they create**: the team knows what must be true for the story to
> be considered complete."

[S126] (Atlassian) places acceptance criteria as the third of the 3 C's: "**Confirmation** is
the acceptance criteria that define when the story is complete."

## Purpose

[S126]: "Including acceptance criteria helps teams understand what success looks like and
**ensures that the story is testable.**"

This connects to [S127]'s third quality of a good story — testability: "The team should be able
to tell whether the story is done."

## When they are needed

[S127] is specific about timing, and this is the point most often got wrong:

> "That does not mean every acceptance criterion must be known the moment the story is written.
> Detail can be added later. **But before the story is brought into a sprint, the team should
> understand what must be true for the item to be considered complete.**"

Acceptance criteria emerge during **product backlog refinement** — [S127] lists it as one of the
things that happens there: "vague ideas become clearer stories, large stories are split, risks
surface, and **acceptance criteria emerge**."

[S052] adds a caution from the same organisation's tooling copy: add "acceptance criteria **only
when it adds value**" — i.e. criteria are not a mandatory field to fill on every item.

## Worked examples

[S127] provides three story/criteria pairs. These are the corpus's only concrete acceptance
criteria and are worth preserving in full.

### Conference website
**Story:** *As a conference attendee, I can save sessions to a personal agenda so that I can plan
which sessions to attend.*

Possible acceptance criteria:
- A logged-in attendee can add a session to a personal agenda.
- A session already on the attendee's agenda is marked as saved.
- The attendee can remove a saved session.
- **If two saved sessions occur at the same time, the attendee is warned of the conflict.**

### E-commerce site
**Story:** *As a returning customer, I want to reorder items from a previous purchase so that I
can quickly buy things I regularly need.*

Possible acceptance criteria:
- A customer can view previous orders.
- A customer can add all available items from a previous order to the cart.
- **Unavailable items are shown but not added automatically.**
- The customer can adjust quantities before checkout.

### Internal business system
**Story:** *As a payroll specialist, I need to see employees with missing time approvals so that
I can resolve payroll issues before processing begins.*

Possible acceptance criteria:
- The list shows employees with at least one unapproved time entry in the current pay period.
- The list can be filtered by department.
- Each employee entry links to the relevant time records.
- **Employees with no missing approvals are excluded.**

> **What to notice in these examples.** Each set covers the happy path *plus* at least one edge
> case, exclusion, or conflict rule (bolded above). None of them specifies UI layout, wording, or
> implementation. They constrain *behaviour*, not *design* — which preserves the room for
> conversation that [S127] identifies as a quality of a good story.

## Definition of done

The corpus treats this loosely and the sources do not fully agree on scope.

- [S126]: "**Definition of done:** The story is generally 'done' when the user can complete the
  outlined task, but make sure to define what that is."
- [S128]: step 1 of writing a user story is "**Decide what 'done' will look like.** In most
  cases, the user story describes an end-state: when the user is able to complete the task or
  achieve the goal described. You need to have this end-state in mind when you write yours, so
  the rest of your team knows when they can mark the development work done."

> ⚠ **CORRECTION — both corpus sources use the term incorrectly.** Phase-2 research settled this
> from the primary texts, and they agree with each other.
>
> **[E001], the 2020 Scrum Guide**, defines the Definition of Done as a **commitment attached to the
> Increment**: *"a formal description of the state of the Increment when it meets the quality
> measures required for the product,"* and states that **work cannot be considered part of an
> Increment unless it meets it.** It is a product- or team-level standard, not an item-level one.
>
> **[E003], *Essential Kanban Condensed***, reaches the same place independently: it names the
> Definition of Done as one kind of **explicit policy**, alongside WIP limits, capacity allocation
> and replenishment policies — a standing rule for work leaving a stage.
>
> **The two concepts are complementary, not interchangeable:**
>
> | | Scope | Question it answers | Changes |
> |---|---|---|---|
> | **Acceptance criteria** | **This item** | *Did we build the right thing?* | Per item |
> | **Definition of Done** | **The team or product** | *Is it releasable?* | Rarely; by team agreement |
>
> **[S126] and [S128] both use "definition of done" to mean story-level acceptance criteria.** That
> usage is not supported by either primary text and an agent should not reproduce it. The corpus
> sources are preserved above rather than deleted, per the knowledge base's rule on disagreement;
> see [../99-reference/disputed-information.md](../99-reference/disputed-information.md).
>
> **[E003] adds a warning the corpus has no equivalent for:** explicit policies must be *"always
> applied, and readily changeable"* — and those two go together. A Definition of Done that is never
> revisited is a poor application of the practice, not a well-run one.
>
> See [../07-execution/scrum.md](../07-execution/scrum.md) and
> [../07-execution/kanban.md](../07-execution/kanban.md).

## Release criteria — a distinct, higher-level concept

[S048] describes criteria at the **release** rather than story level:

> "Identify the criteria that will determine whether your product is **customer-ready**. This
> might include notes on **functionality, usability, and reliability.**"

This is a different altitude from story acceptance criteria: it gates a shipment, not an item.
See [prd.md](prd.md), where release criteria appear as a PRD component, and
[../05-planning/release-planning.md](../05-planning/release-planning.md).

## Who defines them

[S097]: product managers "write user stories, **define acceptance criteria**, and work closely
with designers to ensure everyone understands what needs to be built."

[S127]'s position is broader and more consistent with the 3 C's: criteria emerge from the
conversation among "the product owner, developers, testers, designers, stakeholders, and
others." Testers in particular are named as contributors — "**Testers may suggest important
examples**" — during the detail-adding process.

> The two framings differ in whether acceptance criteria are *authored* by the PM or
> *converged on* by the team. [S127] is the stronger source; its framing also better explains
> why acceptance criteria are listed under *Confirmation* in the 3 C's rather than under *Card*.

## Common failure modes

Derived from [S127]'s six user story mistakes, the two that bear directly on acceptance criteria:

| Failure | Consequence |
|---|---|
| **Adding too much detail too soon** | Criteria written long before the work is scheduled describe a solution that may never be built, and create the "false sense of certainty" [S127] attributes to traditional requirements documents |
| **Treating the written story as the requirement** | Criteria become a substitute for conversation rather than a record of it. [S127]: "The real requirement emerges through conversation, examples, rules, sketches, tests, and decisions" |

A third, implied by [S127]'s readiness checklist: **criteria that do not let the team answer
"what must be true for this item to be considered complete"** are not doing their job, however
many bullet points they contain.

## Limitations

- **The corpus has no coverage of Given/When/Then (Gherkin) or specification by example**, the
  most widely used structured formats for acceptance criteria. [S127] explicitly permits
  "examples, rules, tests, or brief notes" but demonstrates only the rule form.
- **The corpus itself still has no team-level Definition of Done.** The concept above is supplied
  entirely by external primary sources [E001] and [E003]; no document in the original 143 describes
  one, and no corpus source gives an example of what one contains in practice.
- **No treatment of acceptance testing, automated acceptance tests, or the relationship between
  acceptance criteria and QA test plans** — except [S084]'s note that QA "will write a test plan
  ensuring every single use case in the PRD can be successfully executed during testing."
- The topic has **no dedicated source** in the corpus; everything here is assembled from
  sections of documents about user stories and PRDs.

## Acceptance under agent implementation

A separate problem, treated in
[../13-ai-agent-collaboration/evals-and-acceptance-for-agents.md](../13-ai-agent-collaboration/evals-and-acceptance-for-agents.md):
every format on this page assumes **"passes" is a property of the artifact.** When an agent produces
the implementation, it may be a property of a *distribution* instead — [E011] gives the arithmetic.
Nothing in the corpus addresses this.

## Related concepts

- [user-stories.md](user-stories.md) — the 3 C's, testability, readiness checklist
- [job-stories.md](job-stories.md)
- [prd.md](prd.md) — release criteria as a PRD component
- [requirements.md](requirements.md)
- [../05-planning/backlog-management.md](../05-planning/backlog-management.md) — refinement, where criteria emerge
- [../05-planning/release-planning.md](../05-planning/release-planning.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S127 | Mountain Goat Software (Mike Cohn) — *User Stories* | Practitioner guide | Definition, form flexibility, timing, worked examples, emergence in refinement |
| S126 | Atlassian — *User stories with examples and a template* | Vendor guide | Confirmation as the third C, testability, definition-of-done framing |
| S128 | ProductPlan — *User Story* (Glossary) | Vendor glossary | Deciding what done looks like |
| S048 | Notion — *How to write a PRD in 7 simple steps* | Vendor blog | Release criteria |
| S097 | Atlassian — *Product manager vs. project manager* | Vendor guide | PM's role in defining acceptance criteria |
| **E001** | **The Scrum Guide**, Schwaber & Sutherland, November 2020 | **Primary text** | **The Definition of Done as an Increment-level commitment — correcting [S126] and [S128]** |
| **E003** | **Anderson & Carmichael — *Essential Kanban Condensed*, 2016** | **Primary text** | Definition of Done as an explicit policy; the "always applied and readily changeable" warning |
| **E011** | Anthropic — *Demystifying evals for AI agents*, January 2026 | Vendor engineering guide | pass@k / pass^k, referenced in the agent-implementation note |
