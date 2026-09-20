---
title: Usability Testing
domain: discovery
type: technique
topics:
  - usability testing
  - user testing
  - moderated testing
  - unmoderated testing
  - think-aloud protocol
  - test tasks
  - facilitation
  - five users
source_count: 3
sources: [S099, S013, S074]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Usability Testing

## Definition

[S099] (Nielsen Norman Group): "In a usability-testing session, a researcher (called a
'facilitator' or a 'moderator') asks a participant to perform tasks, usually using one or more
specific user interfaces. While the participant completes each task, the researcher observes
the participant's behavior and listens for feedback."

[S013] (Maze): "Usability testing helps teams evaluate how users interact with a product so
they can spot friction, improve design decisions, and build better experiences."

## What it answers

[S074] frames usability testing around four questions about the product:

1. Is it easy to learn?
2. Is it fast to use?
3. What common mistakes do users make while using it?
4. How does it feel to use this product?

Its stated value: "It'll help you to catch errors and issues with workflows, because it puts
your product in the hands of people who haven't been working on it for months on end! What
might make complete sense to you might be completely baffling to your target customers."

## Where it fits in method selection

Usability testing is a **qualitative, behavioral** method — it observes what people *do*. This
is why [S105] selects it for the "why are users abandoning their carts?" question rather than
a survey. See [user-research-methods.md](user-research-methods.md).

## The three pillars

[S099]'s study guide is organised around three named pillars of a valid usability test. Even
in a resource list, this structure is the substantive claim:

| Pillar | [S099]'s framing |
|---|---|
| **1st pillar — Typical users** | "Why having realistic ('typical') users is critical to your research" |
| **2nd pillar — Appropriate tasks** | "Why task instructions are so important" |
| **3rd pillar — Skilled facilitator** | "Why it's important to have an experienced facilitator run the test" |

Any usability test that compromises one of these three is compromised as evidence.

## Participants

[S099] indicates NN/g's recommendation: **"conducting qualitative usability testing with about
5 participants per user group."** The guide points to three separate resources explaining the
logic (design process, ROI criteria, information foraging), indicating this is a reasoned
position rather than a rule of thumb — but **the reasoning itself is not in the corpus**, only
the recommendation.

> **Scope warning.** This number applies to *qualitative* usability testing, per user group.
> It is not a general sample-size rule and should not be transferred to surveys, interviews,
> or quantitative usability studies.

[S099] also flags two participant questions organisations commonly face:
- **Employees as participants** — "When it's okay to use coworkers as usability-test
  participants" (the corpus preserves that the question is conditional, not the conditions).
- **Reusing participants** across multiple studies.

## Tasks

[S099] treats task writing as a distinct skill with its own failure modes:

- Tasks must be derived from user goals — "How to decide which tasks you might want to write"
  via turning user goals into task scenarios.
- **Task writing differs between qualitative and quantitative studies.**
- **Task wording changes behaviour.** [S099] cites eyetracking evidence: "An illustration of
  how the exact way you write your task will influence your user's behavior." This is the
  strongest methodological caution in the document — the instrument alters the measurement.
- **Stepped user tasks** — "starting with open-ended tasks and then moving to directed,
  focused tasks" — is named as a strategy to maximise insight.

## Facilitation

[S099] lists the facilitation concerns as:

- Encouraging participants to think out loud — **"Thinking Aloud: The #1 Usability Tool"**
- "How to communicate with participants without influencing or distracting them from the
  study"
- **Handling observers** — two separate resources address this, including "Team Members
  Behaving Badly During Usability Tests" and avoiding observers who "distract and bias the
  study participants"

## Moderated versus unmoderated, in person versus remote

[S099] defines the two remote modes precisely:

| Mode | Definition [S099] |
|---|---|
| **Remote moderated** | "Conducted synchronously. The participant and facilitator meet virtually, often using video conferencing apps like Zoom." |
| **Remote unmoderated** | "Conducted asynchronously — the researcher sets up the tasks and instructions in a testing platform, and the participant performs the tasks on their own while recording a video." |

[S099] indicates each has conditions under which it is preferable ("When it's a good idea to
use moderated instead of unmoderated") but **the corpus does not contain those conditions** —
only that they exist.

## Method list

[S013] names seven usability testing methods: **lab testing, contextual inquiry, guerrilla
testing, video interviews, session recording, tree testing, and A/B testing.**

Its selection criterion: "Choosing the right method depends on factors like budget, timeline,
and whether you need moderated, unmoderated, in-person, remote, qualitative, or quantitative
data."

[S013] also frames three format dimensions that cut across all UX research: **qualitative or
quantitative; moderated or unmoderated; in-person or remote.**

> **Extraction limitation.** [S013] was captured as a single page (~180 words). Only the
> summary and the opening of the methods section extracted; the per-method detail is **not in
> this knowledge base.**

## Trade-offs

[S074]:
- **Pros:** "Covers a lot of bases, answers the most important questions"; gives "a good mix
  of qualitative and quantitative feedback."
- **Cons:** "Resource heavy, involves getting a prototype out to testers."

**When to run it** [S074]: "especially essential in the early stages of development as it
allows you to validate your prototype," and worth repeating "if/when you make significant
changes to your UI."

## Important limitation of this document

[S099] is a **study guide** — a curated index of ~40 NN/g articles, videos and reports, not a
tutorial. It reliably tells us **what the important sub-topics are** and **what NN/g's
positions are at headline level**, but the underlying instruction lives in linked resources
that are not in the corpus.

Consequently this knowledge base can support an agent in **knowing what a rigorous usability
test requires** and **recognising when one is being done badly**, but cannot support
**executing one**. Recovering the linked material is a research task — see
[RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

Additionally:
- The corpus has **no quantitative usability testing** content beyond the existence of the
  distinction.
- Accessibility testing is entirely absent.
- The related tool-comparison source [S002] was excluded as commercial and time-sensitive —
  see [../99-reference/excluded-content.md](../99-reference/excluded-content.md).

## Related concepts

- [user-research-methods.md](user-research-methods.md)
- [surveys.md](surveys.md) — SEQ and SUS, administered within usability tests
- [product-discovery.md](product-discovery.md)
- [../12-design-and-ux/ux-for-product-managers.md](../12-design-and-ux/ux-for-product-managers.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S099 | Nielsen Norman Group, Kate Moran — *Qualitative Usability Testing: Study Guide*, 20 Jul 2023, last reviewed 24 Jul 2024 | UX research organization, curated index | Definition, three pillars, participants, tasks, facilitation, remote modes |
| S013 | Maze — *7 Essential usability testing methods for UX insights* | Vendor guide chapter (partially extracted) | Method list, format dimensions, selection criteria |
| S074 | Product School — *Product Management Skills: User Research* | Training-provider blog | Four questions, pros/cons, when to run |
