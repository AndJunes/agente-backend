---
title: Requirements — Types and Elicitation
domain: requirements
type: concept
topics:
  - requirements
  - functional requirements
  - non-functional requirements
  - requirements gathering
  - requirements elicitation
  - constraints
  - dependencies
source_count: 5
sources: [S085, S084, S086, S097, S127]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Requirements — Types and Elicitation

## What a requirement is in this corpus

The corpus does not define "requirement" abstractly. It defines requirements **by the artefacts
that hold them** — PRDs, user stories, use cases — and by the **categories** they fall into.

The most useful conceptual statement comes from [S127], which treats a requirement as something
larger than any document:

> "A user story represents a requirement, but the written sentence is rarely the whole
> requirement. **The requirement emerges through conversation, examples, rules, sketches, tests,
> and decisions.**"

This has a direct consequence for an agent: *asking "what are the requirements?" as though they
are a retrievable list may be the wrong question.* In agile contexts the requirement is
distributed across a story, its criteria, and the shared understanding of the team.

## Functional versus non-functional requirements

This is the corpus's clearest requirements taxonomy, from [S085]:

### Functional requirements
> "Specify **what the product should do** from a user's perspective, detailing features,
> functionalities, and interactions necessary to meet user needs and expectations. They provide
> a comprehensive breakdown of user stories, use cases, and scenarios, illustrating the actions
> users can perform and the expected outcomes." [S085]

Examples given: "user authentication, data input forms, search functionality, checkout
processes, and account management capabilities."

### Non-functional requirements
> "Focus on the performance, reliability, security, and scalability aspects of the product.
> Unlike functional requirements, which address **what** the product does, non-functional
> requirements cover **how the product performs.**" [S085]

> "These requirements outline the **constraints and quality attributes** the product must adhere
> to, such as response times, system availability, data encryption standards, and compliance
> regulations."

[S084] adds two further categories that are often folded into non-functional requirements but
which it names separately:

| Category | Definition and example [S084] |
|---|---|
| **System & environment requirements** | "Which end-user environments will be supported (such as browsers, operating systems, memory, and processing power)." Example given: *"this product should run on Windows 10 or later, or it should run in Firefox, Chrome and Safari browsers"* |
| **Usability requirements** | Example given: *"one-handed navigation for mobile apps"* |

> **Why the distinction matters operationally.** Non-functional requirements are the ones most
> often left implicit and discovered late. [S084] places them in the PRD as a deliberate
> category precisely so they are stated rather than assumed.

## Assumptions, constraints and dependencies

[S084] treats these as a distinct "final batch of ingredients" and defines each precisely. The
definitions are worth quoting because the three are routinely conflated:

| Term | Definition [S084] | Example [S084] |
|---|---|---|
| **Assumption** | "Anything you **expect to be in place (yet isn't guaranteed)**" | "Assuming that all users will have Internet connectivity" |
| **Constraint** | "Dictate something the eventual implementation **can't require**, be it a budgetary constraint or a technical one" | — |
| **Dependency** | "Any known condition or item **the product will rely on**" | "Depending on Google Maps to add directions for a dog walking app" |

[S086] adds a discipline to the assumptions entry: record "anything that might impact product
development positively or negatively — **along with how you will validate this**" — and any known
dependencies. Pairing each assumption with its validation plan is what connects this section to
[../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md).

[S048] gives a slightly different and **less reliable** framing, treating assumptions as
"points or roadblocks you know you'll meet" and constraints as "unknown external pressures."
That inverts the usual sense of the terms — an assumption is characteristically *not* known.
**Prefer [S084]'s definitions.**

## Elicitation: gathering requirements

[S085]:

> "This involves engaging with stakeholders through **interviews, workshops, and surveys** to
> understand user needs, business objectives, and technical constraints. By involving
> stakeholders from various departments — such as product management, engineering, design, and
> marketing — you ensure a comprehensive understanding of the project scope."

[S097] describes the PM's part: "Product managers **translate user needs into detailed
requirements** that development teams can act on... It requires balancing user requests with
technical feasibility and business constraints."

[S138] adds a practice that changes the quality of what is gathered:

> "When conducting customer interviews, **include a member of the design and development teams
> so they can hear from a customer directly instead of relying on the product owner's notes.**
> It will also give them the chance to probe deeper while the topic is fresh in the customer's
> mind."

### Where requirements come from
Assembling across the corpus, the inputs are:

| Source of requirements | Where treated |
|---|---|
| User research and interviews | [../02-discovery/user-interviews.md](../02-discovery/user-interviews.md) |
| Stakeholder interviews | [../02-discovery/product-discovery.md](../02-discovery/product-discovery.md) |
| Customer feedback and support data | [../02-discovery/identifying-unmet-needs.md](../02-discovery/identifying-unmet-needs.md) |
| Competitive and market analysis | [../03-market-intelligence/competitive-analysis.md](../03-market-intelligence/competitive-analysis.md) |
| Business objectives and strategy | [../04-strategy/product-strategy.md](../04-strategy/product-strategy.md) |
| Regulatory and compliance obligations | [S086], [S085] |
| Technical constraints from engineering | [../10-engineering-collaboration](../07-execution/working-with-engineering.md) |

## The documentation chain

[S084] describes how a requirement moves from statement to verification. This is the clearest
account in the corpus of who produces what:

```
MRD          (market opportunity, customer demand, business case)
  ↓          — product marketing / product management
PRD          (what capabilities the release must include; use cases)
  ↓          — product management
  ├──→ Functional specification   (HOW each item will be implemented)  — engineering
  ├──→ Architectural design doc                                        — engineering
  ├──→ Wireframes and mockups                                          — UX
  └──→ Test plan  ("ensuring every single use case in the PRD can be
                   successfully executed during testing")              — QA
```

> **The boundary that holds this together:** [S084]'s rule that a PRD "may not dictate a
> specific implementation." The PRD owns *what*; the functional specification owns *how*.

## Requirements in agile: the shift

[S138] describes the difference agile makes to requirements work, and it is a difference of
*where the detail lives*, not of whether detail exists:

> "Product owners who don't use agile requirements get caught up with **spec'ing out every
> detail** to deliver the right software (then cross their fingers hoping they've spec'ed out
> the right things). On the other hand, agile requirements also **depend on a shared
> understanding of the customer.**
>
> That shared understanding and empathy for the target customer **unlocks hidden bandwidth for
> product owners. They can focus on higher-level requirements and leave implementation details
> to the development team**, who is fully equipped to do so because of the shared
> understanding."

> **The trade-off is explicit and should not be lost:** agile requirements work *only if* the
> shared understanding actually exists. Reducing documentation without building that
> understanding removes the specification and replaces it with nothing. [S138]'s anti-patterns
> list — see [prd.md](prd.md) — describes what this looks like when it fails.

## Documenting requirements: steps

[S085]'s five-step sequence:

1. **Gather requirements** — stakeholder interviews, workshops, surveys.
2. **Define user stories** — "translating them into user stories... Breaking down requirements
   into user stories helps prioritize features based on their importance to end-users."
3. **Document functional and non-functional requirements** — "ensures that the development team
   has a clear understanding of **what needs to be built and how it should perform.**"
4. **Create wireframes and mockups** — [S085] distinguishes them: wireframes "provide a skeletal
   outline of the user interface, focusing on layout and functionality **without including
   visual design details**"; mockups "are more detailed representations that include visual
   design elements such as colors, typography, and branding."
5. **Define metrics and success criteria** — "By defining clear metrics and success criteria
   upfront, teams can track progress, identify areas for improvement, and ensure alignment with
   business goals."

## Limitations

- **The corpus contains no requirements-engineering source.** There is no coverage of
  requirements elicitation techniques as a discipline (observation, document analysis, prototyping
  as elicitation, JAD sessions), no requirements traceability, no requirements prioritization
  method specific to requirements (MoSCoW appears only as a feature prioritization framework),
  and no treatment of ambiguity, completeness or consistency checking.
- **Use cases are defined only by contrast with user stories** ([user-stories.md](user-stories.md)),
  with no worked example and no primary source despite [S084] making use cases central to the
  PRD ("a use case is typically included for every item").
- **Non-functional requirements are named but not developed.** The corpus lists categories
  (performance, security, scalability, compliance) without any guidance on how to specify them
  measurably — e.g. what a good performance requirement looks like versus a vague one.
- All sources are product-tooling vendors. No software-engineering or business-analysis
  literature is present.

## Related concepts

- [prd.md](prd.md)
- [user-stories.md](user-stories.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [scope-definition.md](scope-definition.md)
- [epics-and-decomposition.md](epics-and-decomposition.md)
- [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)
- [../07-execution/working-with-engineering.md](../07-execution/working-with-engineering.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S085 | Reforge — *Product Requirements Document: What Is It & How To Write It* | Practitioner blog | Functional/non-functional definitions, five documentation steps, wireframe vs mockup |
| S084 | ProductPlan — *Product Requirements Document* (Glossary) | Vendor glossary | Assumptions/constraints/dependencies definitions, system and usability requirements, documentation chain |
| S086 | Aha! — *What product managers need to know about PRDs* | Vendor guide | Assumptions with validation plans, requirements as PRD component |
| S097 | Atlassian — *Product manager vs. project manager* | Vendor guide | PM's translation role |
| S127 | Mountain Goat Software — *User Stories* | Practitioner guide | Requirement as emergent from conversation |
