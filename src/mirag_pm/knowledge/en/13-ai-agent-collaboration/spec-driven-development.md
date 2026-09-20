---
title: Spec-Driven Development
domain: ai-agent-collaboration
type: practice
topics:
  - spec-driven development
  - SDD
  - specification as source of truth
  - spec-kit
  - Kiro
  - EARS
  - requirements syntax
  - constitution
  - vibe coding
  - agent instructions
synonyms:
  - SDD
  - spec-first development
  - specification-driven development
  - writing specs for AI agents
source_count: 4
sources: [E012, E013, E014, E011]
evidence_type: professional-practice
confidence: medium
corpus_origin: false
external_research: true
verified: true
phase: 2
provenance:
  primary: [E012, E013, E014]
  interpretation: []
  practice: [E012, E013]
  empirical: []
last_reviewed: 2026-09-16
---

# Spec-Driven Development

> **Provenance warning, stated first because it matters more than anything below.**
> Spec-Driven Development is **a widely adopted practice with tooling from GitHub, AWS and others.
> It has no empirical evidence base in this knowledge base.** Adoption is not efficacy. Every claim
> in this document about SDD producing better outcomes is **a vendor's or a practitioner's claim**,
> and is marked. See
> [evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md).

## Definition

**Spec-Driven Development (SDD)** is the practice of treating a **written specification, rather than
the code, as the source of truth** — humans author and maintain the spec; agents generate, verify and
update code against it.

The formulation from [E012], GitHub's `spec-kit`:

> **"Define what and why before deciding how to build it."** [E012]

[E012] describes the method as transforming requirements into a specification, a technical plan, and
actionable tasks, then guiding implementation against those artifacts — inverting traditional
development by **crystallising requirements upfront rather than letting them emerge during coding.**

### Why this is a product-management topic, not a tooling topic

The artifact SDD makes central — a precise statement of intended behaviour and its acceptance
conditions — **is the PRD, restated for a reader that cannot ask a follow-up question in the hallway.**
See [../06-requirements/prd.md](../06-requirements/prd.md).

The corpus's PRD material ([S086], [S138]) argued for **"informative-but-brief"** requirements, on the
ground that working software beats comprehensive documentation (Agile value 2; see
[../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md)). **SDD points the other
way**, and the reason is specific rather than ideological: Agile principle 6 assumes *"face-to-face
conversation"* is available to fill in what the document omits. **When the implementer is an agent,
the tacit-knowledge channel that justified brevity is narrower or absent.**

> **This tension is real and unresolved.** It is not that the corpus was wrong and SDD is right. It
> is that the corpus's advice was **conditional on a premise that agent implementation weakens**, and
> neither position has been tested against the other. Recorded in
> [open-questions-ai-and-pm.md](open-questions-ai-and-pm.md).

## GitHub spec-kit — the workflow

[E012], MIT-licensed, `github/spec-kit`. A set of commands layered over an existing coding agent; all
artifacts are **plain markdown committed to the repository**.

| Command | Purpose [E012] | Frequency |
|---|---|---|
| **`/speckit-constitution`** | Establish project principles — code quality, testing, maintainability | **Once per project** |
| **`/speckit-specify`** | Build the specification from requirements | Per feature |
| **`/speckit-plan`** | Create the technical implementation strategy | Per feature |
| **`/speckit-tasks`** | Generate actionable work items | Per feature |
| **`/speckit-implement`** | Execute the planned work | Per feature |
| **`/speckit-converge`** | **Verify the implementation matches the specification** | Per feature, looped |

> [E012]: *"Repeat implement → converge until convergence reports Converged."*

### Three structural observations for a PM

1. **The constitution is a separate, longer-lived artifact than any spec.** It holds the standing
   constraints — quality bars, testing expectations — that a human team would carry as culture.
   **It is the closest thing SDD has to a Definition of Done**, and the comparison is instructive:
   [E001] and [E003] both treat the Definition of Done as a *team-level standing policy* rather than
   per-item criteria. See [../07-execution/scrum.md](../07-execution/scrum.md) and
   [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md).
2. **`converge` is an explicit, named, repeated verification step.** Traditional development has no
   equivalent first-class step for *"does the built thing match what we said?"* — it is distributed
   across code review, QA and acceptance. SDD makes it a loop with a termination condition.
3. **Specs live in version control alongside code.** This makes specification drift **visible as a
   diff** — and it puts the PM's primary artifact under the same review process as the code.

## Amazon Kiro — the three-document structure

[E013], `kiro.dev`. An agentic IDE built around SDD; launched **14 July 2025**. It generates three
files per feature:

| File | Contains [E013] |
|---|---|
| **`requirements.md`** | User stories and acceptance criteria in **EARS notation** (or, for a fix, a bug analysis) |
| **`design.md`** | Technical architecture, sequence diagrams, implementation considerations |
| **`tasks.md`** | A detailed implementation plan of discrete steps |

### Two workflows, and the trade-off between them
[E013] offers both directions, which is an unusually explicit statement of a choice most processes
leave implicit:

- **Requirements-First** — confirm requirements → generate design → generate tasks.
- **Design-First** — confirm architecture → **derive requirements that are feasible given the
  design**. [E013]'s stated benefit: *requirements are guaranteed to be technically feasible because
  they are derived from a validated architecture.*

> **A PM should read Design-First with care.** Guaranteeing feasibility by deriving requirements from
> an architecture is precisely the inversion the discovery literature warns against — solution
> shaping the problem statement. It may be the right trade for well-understood work in a constrained
> system; it is the wrong trade when the problem is not yet understood. See
> [../02-discovery/product-discovery.md](../02-discovery/product-discovery.md) and
> [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md).
> **[E013] does not flag this trade-off; the framing here is this knowledge base's, marked
> `[SYNTHESIS]`.**

[E013] also offers **Quick Spec**, which generates all three files with **no approval gates between
phases** — a deliberate removal of the human checkpoints, appropriate to small or well-understood
work. And it builds a **dependency graph of tasks**, grouping independent tasks into **waves** that
execute concurrently, with waves running sequentially.

> The wave model is a scheduling mechanism with a direct analogue in
> [../05-planning/dependencies.md](../05-planning/dependencies.md). **What is new is that the
> dependency graph is derived from the spec automatically and executed without a human sequencing
> it** — which shifts the PM's dependency work from *sequencing* toward *making dependencies
> expressible in the spec at all.*

## EARS — Easy Approach to Requirements Syntax

[E014] Alistair Mavin and colleagues, **Rolls-Royce plc**, first published **2009**, developed while
analysing airworthiness regulations. **This is a pre-AI requirements-engineering notation** that SDD
tooling adopted; it is not an AI artifact.

### The generic template

> **"While `<optional pre-condition>`, when `<optional trigger>`, the `<system name>` shall
> `<system response>`"** [E014]

### The five patterns

| Pattern | Syntax [E014] | Example [E014] |
|---|---|---|
| **Ubiquitous** | The `<system>` **shall** `<response>` | *The mobile phone shall have a mass of less than XX grams.* |
| **State-driven** | **While** `<precondition>`, the `<system>` **shall** `<response>` | *While there is no card in the ATM, the ATM shall display "insert card to begin".* |
| **Event-driven** | **When** `<trigger>`, the `<system>` **shall** `<response>` | *When "mute" is selected, the laptop shall suppress all audio output.* |
| **Optional feature** | **Where** `<feature is included>`, the `<system>` **shall** `<response>` | *Where the car has a sunroof, the car shall have a sunroof control panel on the driver door.* |
| **Unwanted behaviour** | **If** `<trigger>`, **then** the `<system>` **shall** `<response>` | *If an invalid credit card number is entered, then the website shall display "please re-enter credit card details".* |

**Complex** requirements combine keywords: *While `<precondition>`, When `<trigger>`, the `<system>`
shall `<response>`.*

### Why the keyword discipline is the point
Each keyword marks a **distinct logical relationship** — a standing property, a state, an event, a
configuration, an error condition. Prose requirements blur these; EARS forces a choice, and the
choice is where ambiguity gets found.

> **The "unwanted behaviour" pattern is the one PMs most often omit.** [E011] lists **ambiguous task
> specifications** first among the common mistakes in evaluating agents, and unspecified error
> behaviour is the most common form of that ambiguity. A human implementer asks what should happen
> when the card is invalid; an agent picks something plausible.

### EARS compared with the corpus's formats

| Format | Answers | Best for | Source |
|---|---|---|---|
| **User story** — *As a `<role>` I want `<goal>` so that `<benefit>`* | **Who and why** | Carrying intent; opening a conversation | [../06-requirements/user-stories.md](../06-requirements/user-stories.md) |
| **Job story** — *When `<situation>` I want to `<motivation>` so I can `<outcome>`* | **Context and motivation** | Situations where the role is not the driver | [../06-requirements/job-stories.md](../06-requirements/job-stories.md) |
| **Given/When/Then** | **One testable scenario** | Acceptance tests | [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md) |
| **EARS** | **What the system shall do, under exactly which condition** | **Unambiguous system behaviour, including the unwanted cases** | [E014] |

> **These are complements, not rivals, and the corpus's own logic says why.** [S127]'s *card,
> conversation, confirmation* names three things; a user story is the **card**, EARS is the
> **confirmation**. What changes with an agent implementer is that **the conversation is compressed
> into the written artifact**, so the confirmation has to carry more weight than it did.
> **`[SYNTHESIS]` — this mapping is this knowledge base's, not [E014]'s or [S127]'s.**

## What SDD is reacting against

The practice defines itself in opposition to **"vibe coding"** — prompting an agent conversationally
and accepting what emerges. The stated diagnosis across SDD tooling is that **a vague prompt produces
vague code and a structured spec produces something closer to intent.**

> **`UNVERIFIED`.** This is the field's near-universal working assumption and it is **plausible and
> untested here.** No controlled comparison of specification approaches for agent implementation
> appears in any source consulted. An agent using this knowledge base should present SDD as **the
> current dominant practice**, not as a demonstrated improvement.

## Limitations

- **No empirical evidence of efficacy**, as stated above. The strongest available support is
  convergent adoption by independent vendors, which is weak evidence and partly reflects competitive
  imitation.
- **Sources are tool vendors** ([E012] GitHub, [E013] AWS) documenting their own products. [E014] is
  the exception — an independent pre-AI notation with an academic origin.
- **Specification cost is not accounted for anywhere.** None of these sources quantifies how long a
  good spec takes to write, or at what feature size the overhead stops paying. The **J-curve**
  discussion in [evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md) suggests
  this cost is real and front-loaded.
- **Spec drift is unaddressed.** All three tools describe generating code from a spec. None of the
  material consulted describes what happens when the code is then changed directly — the maintenance
  problem that sank earlier model-driven and CASE approaches.
- **The tooling landscape is volatile.** [E012] and [E013] are actively developed; command names,
  workflows and file structures change. **Verify command syntax against current documentation before
  relying on it.**
- **Nothing here addresses non-functional requirements at scale** — performance, security, privacy,
  accessibility — beyond EARS's ubiquitous pattern. Accessibility in particular remains absent from
  this entire knowledge base.
- **No historical comparison.** SDD's relationship to earlier specification-first movements
  (formal methods, model-driven architecture, RUP) was not researched, and their failure modes are
  likely relevant.

## Related concepts

- [pm-with-ai-implementers.md](pm-with-ai-implementers.md)
- [evals-and-acceptance-for-agents.md](evals-and-acceptance-for-agents.md) — how you check the spec was met
- [evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md)
- [open-questions-ai-and-pm.md](open-questions-ai-and-pm.md)
- [../06-requirements/prd.md](../06-requirements/prd.md)
- [../06-requirements/requirements.md](../06-requirements/requirements.md)
- [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md)
- [../06-requirements/user-stories.md](../06-requirements/user-stories.md)
- [../06-requirements/epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md)
- [../05-planning/dependencies.md](../05-planning/dependencies.md)

## Sources

| ID | Source | Type | Provenance | Reliability |
|---|---|---|---|---|
| E012 | **GitHub — `github/spec-kit`** repository README (MIT licence), retrieved September 2026 | Tool documentation by its maintainer | `PRIMARY (tool)` · `PRACTICE` | **B** — authoritative for what spec-kit does; vendor for claims about why it works |
| E013 | **Kiro (AWS) — official documentation**, `kiro.dev/docs/specs/`, retrieved September 2026. Product launched 14 July 2025 | Tool documentation by its vendor | `PRIMARY (tool)` · `PRACTICE` | **B** — same caveat |
| E014 | **Mavin, A. et al. — EARS (Easy Approach to Requirements Syntax)**, Rolls-Royce plc, first published 2009; patterns from `alistairmavin.com/ears`, retrieved September 2026 | **Primary, by the notation's creator** | `PRIMARY` | **A** — independent of AI tooling, academic origin in requirements engineering |
| E011 | Anthropic — *Demystifying evals for AI agents*, 9 January 2026 | Vendor engineering guide | `PRACTICE` | **B** — used here only for the "ambiguous task specifications" point |
