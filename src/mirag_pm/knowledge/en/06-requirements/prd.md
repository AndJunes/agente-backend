---
title: Product Requirements Document (PRD)
domain: requirements
type: artifact
topics:
  - PRD
  - product requirements document
  - requirements documentation
  - MRD
  - BRD
  - agile documentation
  - specification
synonyms:
  - product spec
  - requirements doc
source_count: 6
sources: [S086, S138, S084, S085, S113, S048]
evidence_type: professional-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Product Requirements Document (PRD)

## Definition

Four corpus definitions, converging but differing in emphasis:

- [S138] (Atlassian): "A product requirements document (PRD) defines the product to be built —
  outlining the product's purpose, features, functionalities, and behavior... providing a
  **single source of truth** for cross-functional teams."
- [S084] (ProductPlan): "an artifact used in the product development process to communicate
  **what capabilities must be included in a product release** to the development and testing
  teams."
- [S085] (Reforge): "a blueprint that outlines all of the necessary features and specifications
  of a new product, including its value proposition, target audience, and benefits."
- [S086] (Aha!): "at its core, a PRD simply contains all the requirements for a product so the
  product development team can understand what that product should do."

A constraint stated by [S084] that matters: "While PRDs may hint at a potential implementation
to illustrate a use case, **they may not dictate a specific implementation.**"

A property stated by [S113], attributed to Minal Mehta, Head of Product at YouTube: "a PRD is a
living document that should be continuously updated according to the product's lifecycle."

## The disputed question: is the PRD obsolete?

**This is the most important thing to know about PRDs, and the corpus contains a genuine
disagreement. It is preserved rather than resolved.**

### The case against
[S086] states the historical position plainly: "almost every product manager today considers
PRDs to be **passé**." It reconstructs the argument:

- PRDs were essential in **waterfall**, which "dominated as the prevailing methodology from the
  1970s up until the 2000s," because "building scalable software products was expensive and
  time-intensive. Development required a strict plan... There was no room for ambiguity,
  inconsistency, or missing information."
- Agile made them "fundamentally at odds with the emerging methodology." [S086] grounds this in
  the Agile Manifesto's four values, particularly *working software over comprehensive
  documentation* and *responding to change over following a plan*, and asks: **"How can a team
  innovate, iterate, and respond to real user feedback when folks are anchored by extensive
  documentation detailing exactly what must be built?"**
- Two further criticisms: PRDs "slowed progress and limited big-picture thinking"; and because
  much PRD content comes "from past market research and historical data, many found these
  documents **backward-looking rather than focused on future possibilities.**"

[S086] also points to *"SVPG: The Waterfall Product Development Process"* as a related
reference — indicating Marty Cagan's critique — though **that source is not in the corpus.**

[S084] independently corroborates the waterfall association: the PRD "is typically used more in
waterfall environments where product definition, design, and delivery happen sequentially, but
may be used in an agile setting as well."

### The case for
[S086]'s own counter-argument: "When you think about it that way, PRDs are not only still
relevant — they are essential. (Even if the format has shifted over time.)"

[S085] asserts PRDs "are crucial in **both** traditional methodologies like waterfall and agile
environments."

[S138] takes a third position — not defending the traditional PRD but **redefining it for
agile**: "Agile PRDs focus on shared understanding, customer needs, and flexibility, **avoiding
overly detailed specs**."

### How to read this disagreement
The sources are not actually describing the same artefact. A 30-page waterfall specification
and Atlassian's one-page Confluence "landing page" share a name and little else. [S086] gives
the reconciling frame: **the question is not whether to have a PRD, but how much detail the
document should carry** — see [How detailed should a PRD be](#how-detailed-should-a-prd-be)
below.

Note also that all four sources arguing for PRD relevance **sell software for writing them**
(Aha!, Atlassian, ProductPlan, Notion). This is a structural bias to account for.

## What a PRD should contain

The corpus offers several component lists. They overlap heavily; differences are noted.

### Consolidated components

| Component | Purpose | Named by |
|---|---|---|
| **Overview / project specifics** | What is being built; participants, status, target release date | S086, S138, S113, S048 |
| **Objective / goals** | Why you are building this and what you hope to accomplish; strategic alignment with organizational goals | S084, S086, S138, S048 |
| **Background and strategic fit** | "The motivation behind the product or feature and how it aligns with broader company goals" [S138] | S138, S086 |
| **Context / personas** | Customer personas, use cases, competitive landscape; the key persona | S086, S113 |
| **User scenarios** | "Full stories about how various personas will use the product in context" [S113] | S113, S084 |
| **Requirements / features** | Each feature with description, goal and use case at minimum | S084, S085, S086, S113, S048 |
| **Non-functional requirements** | Performance, reliability, security, scalability | S085, S084 |
| **System & environment requirements** | Supported browsers, OS, memory, processing power | S084 |
| **Usability requirements** | e.g. "one-handed navigation for mobile apps" [S084] | S084 |
| **Assumptions** | "Anything you expect to be in place (yet isn't guaranteed), such as assuming that all users will have Internet connectivity" [S084] | S084, S086, S138, S048 |
| **Constraints** | "Dictate something the eventual implementation can't require, be it a budgetary constraint or a technical one" [S084] | S084, S048 |
| **Dependencies** | "Any known condition or item the product will rely on, such as depending on Google Maps to add directions for a dog walking app" [S084] | S084, S086, S048 |
| **Scope — and explicitly what is out of scope** | "Keep the team focused on the work at hand by clearly calling out what you're not doing" [S138] | S138, S086, S113, S048 |
| **UX flow & design notes / wireframes** | [S084] warns: "This is not the place for pixel-perfect mockups... instead, it can be used to describe the overall user workflow" | S084, S085, S113, S138 |
| **Success metrics / release criteria** | KPIs, benchmarks, and what makes the product customer-ready | S085, S086, S113, S048 |
| **Open questions** | [S138]: "Create a table of 'things we need to decide or research'" | S086, S113, S138 |
| **Change history** | "Who changed it, when they changed it, and what they changed" [S113] | S113 |
| **Q&A / key decisions** | "A good place to note key decisions" [S113] | S113 |

### The "Features Out" section
[S113] and [S138] both isolate this as a distinct, named section — *"What have you explicitly
decided **not** to do and why"* [S113]. This is one of the few pieces of the PRD that cannot be
replaced by a backlog item, and it is the mechanism by which a PRD prevents scope creep. See
[scope-definition.md](scope-definition.md).

## How detailed should a PRD be?

[S086] gives the governing principle:

> "The level of detail in a PRD depends on factors such as **your product's complexity, your
> team's experience, and the specific needs of your chosen product development process.**
> In the past, PRDs were exhaustive documents packed with every possible requirement. Today's
> PRDs should still cover essential aspects (such as objectives, target users, and core
> functionality), but **without overloading the document with details that could limit
> adaptability.**"

[S086] notes traditional PRDs "can be upward of 30 pages long." [S048] describes a streamlined
PRD as "within a few pages."

[S113] adds a practical permission: "As you write your first draft of the feature requirements
document, **it's ok to leave TBD and placeholder comments for unknowns.**"

## When to write one

[S086] is the only source that treats this conditionally, and it is the most useful guidance:

> "A PRD provides clear, comprehensive documentation that guides development and supports
> alignment across teams. This is **especially true for industries or projects where security,
> compliance, or complex stakeholder needs demand specific, consistent information.**"

Its two named contexts:

- **Highly regulated enterprise software** — "In sectors like healthcare and finance...
  functional groups outside the core product team (think: legal and compliance) might need
  detailed insights into product functionality to complete their work. Legal teams, for
  instance, might not have direct access to product managers and can rely on the PRD instead."
  Customer support may also rely on it.
- **Software development agencies building for other companies** — "Clear documentation helps
  ensure that client expectations are met and project scope is understood. These PRDs typically
  include high-level goals, edge cases, security concerns, and guidelines surrounding client
  validation and testing."

> **The reusable principle:** a PRD earns its cost when **people who cannot attend the
> conversation need the answer.** Where the team is co-located, small, and empowered, the
> conversation may suffice; where legal, compliance, support, or an external client must act on
> the information asynchronously, the document is doing real work.

## PRD versus adjacent documents

| Document | Scope | Audience | Source |
|---|---|---|---|
| **PRD** | "Functionalities, features, and user interactions the product should have" — personas, user stories, functional and non-functional requirements, wireframes, success metrics | "Product managers, designers, developers, and any other member of the development team" | S085 |
| **BRD** (Business Requirements Document) | "Broader business needs and objectives driving the product's development" — business goals, market analysis, competitive landscape, regulatory requirements, budget constraints, stakeholder expectations. "Gives context for **why** the product is being developed" | "Business stakeholders, executives, investors, and other decision-makers" | S085 |
| **MRD** (Market Requirements Document) | "Describes customer demand, market opportunity, and a business case." [S084] is explicit: "The PRD itself **does not touch on market opportunity or revenue** but is instead firmly rooted in use cases and desired functionality" | Product marketing / product management | S084 |
| **Feature description** | "Focuses on a specific aspect of the product... a single feature's purpose, user interaction, and technical requirements" | The team | S086 |

[S084] adds the downstream document chain: from the PRD, "Engineering will create a **functional
specification**, which describes *how* each item in the PRD will be implemented, and they may
also create (or update) an **architectural design document**. UX will create **wireframes and
mockups**, and quality assurance will write a **test plan** ensuring every single use case in
the PRD can be successfully executed during testing."

> **Note the split:** PRD = *what*; functional specification = *how*. [S084]'s rule that a PRD
> "may not dictate a specific implementation" is what preserves this boundary.

## Alternatives to a PRD

[S086] frames the alternatives correctly — not as ways to skip documentation, but as different
instruments answering the same questions. The questions a product development team needs
answered, per [S086]:

> - What is the core objective?
> - Who are we building for?
> - What is the true value of what we are building?
> - How will our users interact with it?
> - What will it look like?
> - How will we ensure success upon launch?

Lightweight alternatives named [S086]:

| Alternative | What it defines |
|---|---|
| **Jobs-to-be-done framework** | "What users need to accomplish with the product" |
| **Prototypes** | "Early models that help teams test and refine features' functionality" |
| **User stories** | "Describe features from the user's perspective, including what they need and why" |
| **User story mapping** | "A visual layout of all your different user stories to map the entire product journey" |
| **Wireframes and mockups** | "Visual representations of the product layout and design" |

### Choosing between them
[S086] explicitly rejects the either/or framing:

> "A PRD is useful for **high-level planning and aligning everyone on the product's overall
> direction.** For more tactical work, such as detailing a specific feature or user interaction,
> user stories or wireframes can be more efficient. **But this is not an either/or scenario.**"

Its worked example — one feature, three audiences:
- **Development team** → user stories, breaking the feature into actionable items
- **Product designers** → wireframes, "to quickly visualize the layout and user flows without
  needing to reference the full PRD"
- **Marketing** → jobs-to-be-done framing, "how the feature fulfills a specific user need"

## Process: how a PRD gets written and agreed

### The sequential/heavyweight version [S084]
1. Consult product marketing to understand the business drivers for the release (assuming an
   MRD exists).
2. Apply existing prioritization methods to identify what is in scope for the release.
3. Author the document from notes and user feedback per feature.
4. Review with the product team, "to ensure as many potential questions have been answered."
5. Circulate among business-side stakeholders "to confirm they're aligned with the objective of
   the release and the features included."
6. Hand to engineering; address "questions, clarifications, and challenges" verbally and update
   the PRD. "The goal is to have a PRD thorough and comprehensive enough so there are **no
   surprises later on.**"
7. Pass to other teams for UX design, functional specifications and test plan definition.

### The review-order version [S113]
1. **First draft** — "start your PRD draft somewhere private"; TBDs are fine.
2. **Get approval** from your supervisor and teammates. "People who have been around longer
   might have insights you don't know about... Plus you don't want to blindside your manager!"
3. **Share with design** — "**engage design before approaching engineering because their
   feedback might affect the project's technical scope.**"
4. **Share with engineering** — "This will help you figure out what's technically feasible and
   define the timeline."

> These two processes disagree on ordering. [S084] puts business stakeholders before engineering
> and treats the PRD as reaching a signed-off state; [S113] puts design before engineering and
> treats the draft as provisional throughout. The second is more compatible with the agile PRD
> that [S138] describes.

### The collaborative version [S138]
[S138] rejects solo authorship outright:

> "**Never write a product requirements document by yourself** — you should always have a
> developer with you and write it together."

Its supporting practices: include design and development in customer interviews "so they can
hear from a customer directly instead of relying on the product owner's notes"; make personas
"a team effort"; make triage and backlog refinement "a team sport."

## Anti-patterns and failure modes

### Process anti-patterns [S138]
> - "The entire project is already spec'd out in great detail before any engineering work begins"
> - "Thorough review and iron-clad sign-off from all teams are required before work even starts"
> - "Designers and developers don't know when requirements have been updated"
> - "Requirements are never updated in the first place (because everyone signed off on them,
>   remember?)"
> - "The product owner writes requirements without the participation of the team"

### Authoring pitfalls
[S113], attributed to Raja Mukesh Krishna Balakrishnan, Group Product Manager at Flipkart:

| Pitfall | Description |
|---|---|
| **Writing a PRD because you're "supposed to"** | "When PMs create them just to tick a box, they are never as effective" |
| **Failing to get input from stakeholders** | "It's never a good feeling to have your PRD template all filled in and ready to go only to find out that the design, marketing, or development team can't meet your timeline" |
| **Uneven balance between engineering-driven and customer-driven** | "Customers are great at telling you what's not working, but they don't necessarily have the best ideas for how to fix it. By the same token, just because a solution is technically impressive doesn't mean it addresses customer pain points" |
| **Lacking a clear objective** | "There are infinite problems to solve and solutions to tack on. The vision behind the product is what keeps teams coming back to their true purpose" |

### Structural challenges
[S138] names two honestly:

- **Documentation goes stale.** "What happens when you implement a story and get feedback and
  then modify the solution? Does someone go back and update the requirements page with the final
  implementation? This is a challenge with any type of documentation, and **it's always worth
  questioning whether such trade-offs are worthwhile.**"
- **Lack of participation.** "'What can I do to encourage people to comment?'... This is a tough
  nut to crack... There may be deeper cultural issues at play here, too."

## Benefits claimed for the lightweight approach

[S138] on Atlassian's one-page model:
1. **One page, one source** — "the 'landing page' for everything related to the set of problems
   within a particular epic."
2. **Extra agility** — "You don't have to follow the same format every time."
3. **Just enough context and detail** — heavy use of links to "abstract out the complexity and
   progressively disclose the information to the reader as needed."
4. **Living stories** — linking backlog items so their current status is visible from the
   requirements page.
5. **Collective wisdom** — "someone from another team jumped into the conversation with a
   comment providing great feedback, suggestions, or lessons learned from similar projects."

Its closing principle: "When requirements are nimble, the product owner has more time to
understand and keep pace with the market. And **keeping them informative-but-brief empowers the
development team to use whatever implementation fits their architecture and technology stack
best.**"

## Limitations

- **Every source is a vendor selling documentation tooling** (Aha!, Atlassian, ProductPlan,
  Notion, Reforge). No neutral or academic treatment of requirements documentation is in the
  corpus.
- **The critique is reported, not presented.** The strongest arguments against PRDs come to us
  second-hand through [S086], a vendor that concludes PRDs are essential. The SVPG/Cagan source
  it cites is **absent from the corpus.** A fair hearing of the anti-PRD position is a research
  gap.
- **No empirical evidence** that PRDs improve outcomes, or that their absence causes failures.
- **[S048] is written by a marketing writer**, not a product practitioner, and conflates PRD
  metrics with project-tracking metrics ("The metrics you set in this step will usually be **due
  dates and productivity levels**") — which contradicts [S085] and [S113], where success metrics
  are product outcomes such as engagement, retention and conversion. **Treat [S048]'s step 7 as
  an error rather than an alternative view.**
- **No treatment of requirements traceability, versioning, or approval workflows** in regulated
  environments, despite [S086] naming regulated industries as a primary PRD use case.

## Related concepts

- [requirements.md](requirements.md) — functional vs non-functional, elicitation
- [user-stories.md](user-stories.md) — the most-cited PRD alternative
- [acceptance-criteria.md](acceptance-criteria.md)
- [scope-definition.md](scope-definition.md)
- [../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md) — the four values [S086] argues the PRD conflicts with
- [../05-planning/release-planning.md](../05-planning/release-planning.md)
- [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S086 | Aha! — *What product managers need to know about PRDs*, updated Aug 2025 | Vendor guide | Waterfall/agile history, the obsolescence debate, components, detail level, when to write, alternatives |
| S138 | Atlassian (Dan Radigan) — *How to create a product requirements document (PRD)* | Vendor guide | Agile PRD definition, 8 sections, anti-patterns, benefits, challenges, collaboration rule |
| S084 | ProductPlan — *Product Requirements Document* (Glossary) | Vendor glossary | Definition, PRD vs MRD, contents, downstream artefacts, authoring process |
| S085 | Reforge — *Product Requirements Document: What Is It & How To Write It*, 7 May 2024 | Practitioner blog | Definition, functional/non-functional split, PRD vs BRD, writing steps |
| S113 | Product School — *The Only PRD Template You Need*, updated 25 Nov 2025 | Training-provider guide | Component list incl. Features Out and Change History, review order, authoring pitfalls |
| S048 | Notion (Maggie Gowland) — *How to write a PRD in 7 simple steps*, 28 Jul 2023 | Vendor blog; **lower reliability** | Seven steps, assumptions/constraints framing. Step 7 flagged as inconsistent with other sources |
