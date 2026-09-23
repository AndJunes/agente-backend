---
title: User Stories
domain: requirements
type: artifact
topics:
  - user stories
  - card conversation confirmation
  - story template
  - story splitting
  - story mapping
  - backlog refinement
  - epic
  - story vs task
source_count: 3
sources: [S127, S126, S128]
evidence_type: professional-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# User Stories

## Definition

[S127] (Mountain Goat Software / Mike Cohn — the most authoritative source in the corpus on
this topic): "A user story is a short description of desired functionality told from the
perspective of someone who wants or needs that functionality."

It immediately widens the frame beyond "user": "Most stories are written from the perspective of
a user or customer. Some are written from the perspective of a **stakeholder, another system, or
someone else who benefits** from the work. What matters is that the story points toward a
**meaningful outcome, not just an internal task**."

[S126] (Atlassian) adds the agile positioning: "A user story is the **smallest unit of work** in
an Agile framework. It's an **end goal, not a feature**, expressed from the software user's
perspective."

[S128] (ProductPlan): "a small, self-contained unit of development work designed to accomplish a
specific goal within a product."

## The central claim: a story is a promise of a conversation

This is the point on which the corpus's best source is most emphatic, and it is what
distinguishes a user story from a requirement.

> "That sentence is **a reminder to have a conversation**; the full requirement emerges through
> the conversation that follows." [S127]

> "The most useful part of a story is the **shared understanding** created as the product owner,
> developers, testers, designers, stakeholders, and others discuss what is needed, what matters
> most, and what must be true when the work is finished." [S127]

[S126] agrees the story is not a requirement: "It's tempting to think that user stories are,
simply put, software system requirements. **But they're not.**"

### Why deferring detail is deliberate
[S127] explains the mechanism rather than asserting a preference:

> "Traditional requirements documents often try to capture everything up front. That can create
> a **false sense of certainty**. Teams write more detail, but misunderstandings still appear
> once development starts. Stories deliberately defer some detail until the team is closer to
> doing the work. That gives the team room to learn, ask better questions, and **avoid
> documenting things that may change or never be built.**"

## The 3 C's: Card, Conversation, Confirmation

Attributed by [S127] to **Ron Jeffries**.

| C | What it is |
|---|---|
| **Card** | "The short written description. Today it might be a physical card, a sticky note, or a backlog item in Jira, Azure DevOps, Trello, or another tool." [S127] |
| **Conversation** | "Where understanding grows. The team discusses user goals, tradeoffs, edge cases, business rules, design options, and implementation concerns." [S127] |
| **Confirmation** | "How the team knows the story is complete. This might be expressed as acceptance criteria, examples, tests, sketches, rules, or notes that clarify what must be true when the story is done." [S127] |

> **"A useful story combines all three."** [S127]

[S126] corroborates: "Applying the 3 C's ensures that user stories are clear, collaborative, and
testable."

## The template

The common form, with minor variation between sources:

- [S127]: *"As a [type of user], I [need/want/am required] to [do something], so that [reason or benefit]."*
- [S126]: *"As a [persona], I [want to], [so that]."*
- [S128]: *"As [a user persona], I want [to perform this action] so that [I can accomplish this goal]."*

### What each part is for

[S126] breaks it down with unusual care:

| Part | What it must do [S126] |
|---|---|
| **"As a [persona]"** | "We're not just after a job title, we're after the **persona** of the person... Our team should have a shared understanding of who Max is. We've hopefully interviewed plenty of Max's. We understand how that person works, how they think and what they feel." |
| **"Wants to"** | "Here we're describing their **intent — not the features they use**. This statement should be **implementation free** — if you're describing any part of the UI and not what the user goal is you're missing the point." |
| **"So that"** | "How does their immediate desire to do something fit into their bigger picture? What's the overall benefit they're trying to achieve? What is the big problem that needs solving?" |

[S128] notes the persona "does not need to be limited to a person's job title" — its example, *"the
leader of a remote team,"* "could be a department manager, company vice president, the CEO of a
small startup, or any number of other roles."

### The template is a tool, not a rule
[S127] is explicit and this matters:

> "The template is helpful **when it improves the conversation**, but it should not become a
> ritual. Some backlog items read better without it. Some teams use job stories. Some technical
> work is clearer as a technical backlog item. **The form matters less than whether the team can
> have the right conversation about the work.**"

[S126] says the same: "This structure is not required, but it is helpful for defining done. We
encourage teams to define their own structure, and then to stick to it."

## Weak versus strong stories

[S127]'s worked comparisons are the clearest teaching material in the corpus on this topic.

**Weak:**
> *As a user, I want reports so that I can see information.*

[S127]: "That story may be enough to remind someone of a conversation, but it does not give the
team much to work with. The user is vague. The goal is vague. The reason is vague."

**Stronger:**
> *As a regional sales manager, I need to compare monthly revenue by territory so that I can
> identify where coaching or support is needed.*

[S127]: "That version does not specify every field, filter, graph, permission, or export option.
It does something more useful at this stage: **it gives the team a user, a goal, and a decision
the user is trying to make.**"

**A second pair:**

| | Story |
|---|---|
| Weak | *As a product owner, I need a dashboard so that I can see metrics.* |
| Better | *As a product owner, I need to see which recently released features are used least so that I can decide whether to improve, promote, or remove them.* |

[S127]: "The better version identifies **the decision the product owner is trying to make**.
That gives the team room to discuss whether a dashboard is the best solution or **merely one
possible solution.**"

> **The reusable heuristic:** a strong story names a *decision or outcome*; a weak story names a
> *solution artefact*.

## What makes a good story: four qualities

[S127]:

### 1. Clear value
"Someone should care whether the story is completed. That value might be for a user, customer,
stakeholder, business, or product. **Some stories reduce risk. Some improve compliance. Some
support a future capability.** But the team should understand why the story matters."

### 2. Small enough to finish
"A story that cannot be finished in a sprint is usually too large."

[S127] describes the failure mode precisely: "Large stories create the **illusion of progress**.
Everyone is busy, but by the end of the sprint the work is still almost done. The backend is
finished, but the UI is not. The happy path works, but important rules are missing. The feature
exists, but no one is comfortable calling it complete."

### 3. Testable
"The team should be able to tell whether the story is done. That does not mean every acceptance
criterion must be known the moment the story is written. Detail can be added later. But **before
the story is brought into a sprint**, the team should understand what must be true for the item
to be considered complete."

### 4. Leaves room for conversation
"If the story dictates every screen, field, database table, exception, and design choice before
the team discusses the work, the team may lose the benefit of collaboration."

## How much detail, and when

[S127] gives a scaling rule rather than a fixed standard:

> "A story should have enough detail for **the team's current decision.** ... Stories near the
> top of the backlog need more clarity because the team may work on them soon. Stories lower in
> the backlog can stay larger and less detailed because priorities, users, and solutions may
> change."

**The test:**
> "Does the team understand this story well enough to believe it can be completed in a sprint?"
> If yes, it has enough detail for now. If no, "add detail through product backlog refinement,
> conversation, examples, acceptance criteria, or story splitting." [S127]

## Three supporting practices

[S127]:

| Practice | What it does |
|---|---|
| **Product backlog refinement** | "Helps the team add the right amount of understanding at the right time. It is where vague ideas become clearer stories, large stories are split, risks surface, and acceptance criteria emerge." |
| **Story splitting** | "Helps the team break large stories into smaller stories that **still represent meaningful progress**. The goal is not to create more backlog items. The goal is to help the team finish work and get feedback." |
| **Story mapping** | "Helps teams see how stories fit together across a user journey, workflow, product area, or significant objective. A story map can reveal **missing steps, alternatives, assumptions, and release options** that are hard to see in a flat backlog." |

How they combine [S127]: "Story mapping helps teams see the larger picture. Refinement helps
teams decide what is clear enough and valuable enough to do soon. Story splitting helps teams
turn large ideas into work that can be finished."

**When to use story mapping** [S127]: "when the team needs a shared picture of a product,
workflow, user journey, or significant new capability... most helpful when there are many
related stories and the team needs to understand sequence, alternatives, priorities, and release
options."

## Six common mistakes

[S127]. Note the framing: "Most user story problems are **not caused by the template**. They are
caused by using stories for the wrong purpose or at the wrong level of detail."

| # | Mistake | Why it's a problem |
|---|---|---|
| 1 | **Treating the written story as the requirement** | "The written story is a reminder. The real requirement emerges through conversation, examples, rules, sketches, tests, and decisions." |
| 2 | **Writing stories that are too large** | "Large stories hide complexity and make progress hard to see." |
| 3 | **Splitting stories into tasks** | "Tasks organize work. Stories describe useful outcomes." |
| 4 | **Writing every story from the product owner's perspective** | "The product owner is important, but is often not the user." |
| 5 | **Adding too much detail too soon** | "Detail is useful when it supports a near-term decision." |
| 6 | **Using the template without thinking** | "The user story template is a thinking tool, not a guarantee." |

## The readiness checklist

[S127]'s questions to answer before bringing a story into a sprint. This is directly actionable:

> - Who benefits from this story?
> - What outcome, capability, decision, or behavior does the story support?
> - Why does that outcome matter now?
> - Is the story small enough to finish in a sprint?
> - **Has the team avoided splitting the story only by technical layer?**
> - Does the story leave room for conversation and better design choices?
> - Does the team understand what must be true for this item to be considered complete?

"Use those questions to find the **next conversation the team needs to have.**" [S127]

## Definitions of adjacent terms

From [S127]'s FAQ:

| Term | Definition |
|---|---|
| **Epic** | "An epic is **a large story**. Epics are useful when the team wants to remember an important capability before knowing all the details. As the epic gets closer to development, it should be split into smaller stories the team can finish." |
| **Task** | "A story describes a useful outcome from the perspective of someone who benefits from the work. A task describes **work the team performs** to deliver that outcome." Example: *"As a customer, I can save a payment method so that checkout is faster next time"* is a story; *"Create payment-token database table"* is probably a task. |
| **Technical story** | "Sometimes technical work can be described from a meaningful user, business, product, risk, or operational perspective. Other times it is better treated as a **technical backlog item, spike, chore, or task. Do not force everything into user story form.**" |

[S126] gives a different, hierarchical framing: "User stories are also the building blocks of
larger Agile frameworks, such as **epics and initiatives**. Epics are large work items broken
down into a set of stories, and multiple epics comprise an initiative."

> **Note the difference.** [S127] treats an epic as *the same kind of thing, larger*; [S126]
> treats it as *a distinct tier in a hierarchy*. Both are in common use. See
> [epics-and-decomposition.md](epics-and-decomposition.md).

## Who writes user stories

The corpus agrees on substance and differs on emphasis.

- [S126]: "Generally a story is written by the product owner, product manager, or program
  manager and submitted for review."
- [S128]: "In many agile organizations, the product owner takes primary responsibility... In
  reality, though, this is a shared responsibility among the entire cross-functional product
  team." It gives the reason: stories are written in plain language "free of any development
  jargon or technical detail" so that "anyone on either the business or the technical side of
  the team" can contribute. A contributor "only needs to have an understanding of the specific
  user-persona problem they are hoping to solve. They do **not** need to know how the
  development team will actually code that solution."
- [S127] is the sharpest: "**Anyone can write a story.** The product owner is accountable for
  the product backlog, but that does not mean the product owner should personally write every
  item... **What matters most is not who typed the first sentence. What matters is who
  participates in the conversation.**"

## User story vs use case

[S128], citing **Ivar Jacobson**, "who is credited with developing the use-case concept":
use cases "document both a user's goal **and the functional requirements of the system**...
designed to capture much more detail than a user story about the process a user goes through."

A use case typically adds:
- The **preconditions** required before the use case can begin
- The **main flow** (basic flow) — the user's step-by-step path to completing an action
- **Alternate and exception flows** — variant paths to the same or similar goal
- Possibly a **visual diagram** of the entire workflow

> The corpus contains **no primary source on use cases** and no worked use-case example. This is
> a gap — see [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Why teams use stories at all

[S126]'s four benefits:
- **"Stories keep the focus on the user."** "A to-do list keeps the team focused on tasks that
  need to be checked off, but a collection of stories keeps the team focused on solving problems
  for real users."
- **"Stories enable collaboration."** "With the end goal defined, the team can work together to
  decide how best to serve the user and meet that goal."
- **"Stories drive creative solutions."**
- **"Stories create momentum."** "With each passing story, the development team enjoys a small
  challenge and a small win."

[S128] adds a framing worth keeping: stories "help your team... **from becoming enamored with a
UX you believe is elegant but that isn't actually structured in a way your users prefer to
work.**"

## How stories flow through execution

[S126]:
- **In Scrum:** "user stories are added to sprints and 'burned down' over the duration of the
  sprint."
- **In Kanban:** "teams pull user stories into their backlog and run them through their
  workflow."
- **Estimation:** at sprint planning, "Teams use **t-shirt sizes, the Fibonacci sequence, or
  planning poker** to make proper estimations. **A story should be sized to complete in one
  sprint**, so as the team specs each story, they make sure to break up stories that will go
  over that completion horizon."
- **On time estimates:** "Time is a touchy subject. Many development teams avoid discussions of
  time altogether, relying instead on their estimation frameworks."

> **Phase-2 note.** [E001], the 2020 Scrum Guide, confirms [S127]'s distinction: the **Product Owner
> is accountable** for the Product Backlog, and [E001] does **not** require them to author every item
> personally. It also never uses the word "story" — it says **"Product Backlog items."** The
> user-story format is an independent practice, not a Scrum rule. See
> [../07-execution/scrum.md](../07-execution/scrum.md).


> Estimation is named here but nowhere explained in the corpus. See
> [../05-planning/estimation.md](../05-planning/estimation.md) for what little exists and the
> gap record.

## Limitations

- **INVEST is referenced but never defined.** [S052] mentions "INVEST-ready stories" in
  promotional copy; the acronym's meaning (Independent, Negotiable, Valuable, Estimable, Small,
  Testable) **does not appear anywhere in the corpus.** [S127]'s four qualities overlap with it
  but are not the same list. Recorded as a gap.
- **Story splitting techniques are named but not taught.** [S127] tells us splitting matters and
  warns against splitting by technical layer, but the actual patterns (by workflow step, by
  business rule, by data variation, etc.) are in linked articles not in the corpus.
- **Story mapping is described at the level of purpose, not method.** No worked map exists in
  the corpus.
- [S127] is the strongest source here — a practitioner guide by Mike Cohn's organisation, updated
  July 2026, with a genuinely critical treatment of the technique. [S126] and [S128] are vendor
  content and partially promotional. Where they conflict, prefer [S127].

## Related concepts

- [job-stories.md](job-stories.md) — the alternative format and when to prefer it
- [acceptance-criteria.md](acceptance-criteria.md)
- [epics-and-decomposition.md](epics-and-decomposition.md)
- [prd.md](prd.md) — stories as a PRD alternative
- [requirements.md](requirements.md)
- [../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md)
- [../05-planning/backlog-management.md](../05-planning/backlog-management.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S127 | Mountain Goat Software (Mike Cohn) — *User Stories*, last updated 12 Jul 2026 | Practitioner guide from a primary authority on the technique | Definition, 3 C's, template critique, weak/strong examples, four qualities, detail scaling, splitting/refinement/mapping, six mistakes, readiness checklist, epic/task/technical-story definitions |
| S126 | Atlassian (Max Rehkopf) — *User stories with examples and a template* | Vendor guide | Smallest-unit definition, template breakdown, benefits, scrum/kanban flow, estimation practices, epic/initiative hierarchy |
| S128 | ProductPlan — *User Story* (Glossary) | Vendor glossary | Definition, persona flexibility, who writes stories, user story vs use case (Jacobson) |
