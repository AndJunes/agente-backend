---
title: Product Discovery
domain: discovery
type: concept
topics:
  - product discovery
  - discovery phase
  - problem space
  - problem framing
  - double diamond
  - desirable viable feasible
  - continuous discovery
synonyms:
  - discovery
  - customer discovery
  - discovery phase
source_count: 5
sources: [S028, S110, S076, S081, S064]
evidence_type: professional-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Product Discovery

## Definition

The corpus contains two definitions that emphasise different things. **Both are kept
because they are not interchangeable.**

**The design/research definition** [S028] (Nielsen Norman Group):

> "Discovery is a preliminary phase in the UX-design process that involves researching the
> problem space, framing the problem(s) to be solved, and gathering enough evidence and
> initial direction on what to do next."

[S028] adds the unifying criterion: "all discoveries strive to achieve consensus on a problem
to be solved and its desired outcomes."

**The product-management definition** [S110]:

> "Product discovery is the process of finding and validating product opportunities... the
> process of figuring out what needs to be built."

### The difference that matters
[S028] frames discovery as **a bounded phase that converges on a problem statement**.
[S110] frames it as **opportunity identification and validation**, and elsewhere in the same
source describes *continuous* discovery running alongside delivery. An agent should not
assume "discovery" means the same thing to every stakeholder — clarify whether the
speaker means a time-boxed phase or an ongoing practice.

## What a discovery should produce

[S028] states four required understandings. This is the most precise account in the corpus
and is worth treating as a completion checklist:

| Outcome | What it means [S028] |
|---|---|
| **Understanding of users** | Who the users are, how they are affected by the problem, and what they need, desire and value from a solution — **and why** |
| **Understanding of the problems and opportunities** | How and why the problems occur, what effect they have on users *and on the organization*, the magnitude of the problem, and the size of the opportunity |
| **Understanding of existing constraints** | Current business processes, existing solutions, and available compatible technologies — so the team can identify *feasible* solutions to explore |
| **Shared vision** | Agreement with stakeholders on overarching business objectives and desired outcomes: "What do we want to achieve?" / "What does success look like?" — including **what to measure going forward** |

[S028]'s summary of why this matters: "Well-done discoveries ensure that any solutions
proposed later are desirable to users, viable for the organization, and feasible with the
available technology."

Note the correspondence with the desirable/viable/feasible triad — see
[../12-design-and-ux/product-triad.md](../12-design-and-ux/product-triad.md).

## The three questions discovery must answer

[S110] frames the same idea as a gate:

1. **Is the problem worth solving?**
2. **Will your solution work?**
3. **Is it better than anything else out there?**

> "If the answer to any of these questions is 'no', you need to go back to the drawing
> board." [S110]

## When a discovery is needed

[S028]'s general criterion: **"anytime there are many unknowns that stop a team from
moving forward."** The stated risk of skipping it: "Moving forward on only assumptions can
be risky, as the team may end up solving a problem that doesn't really matter — wasting
time, money, and effort."

A second trigger: **"when the team is not aligned with what it wants to achieve."**

### Specific instigators [S028]

| Instigator | What the discovery focuses on |
|---|---|
| **New-market opportunities** | Researching a new audience, competitive reviews, and whether the size of the opportunity warrants entering the market |
| **Acquisitions or mergers** | Common problems faced by each organization, in order to find a common consolidated solution for systems, processes and tools |
| **New policy or regulation** | Studying the populations affected, reviewing the regulation, and assessing how business operations must change |
| **New organization strategy** | Internally driven change. [S028] gives a first-hand example: a UK Government-wide 'digital by default' strategy prompted discoveries across departments to understand user needs and the extent of paper-based processing |
| **Chronic organizational problems** | Low sales or low satisfaction over several quarters. [S028] warns that organizations "often find themselves simply focusing on symptoms (e.g., adding webchat), rather than on causes" |

## Common activities

### Exploratory (generative) research
[S028]: "This type of research is known as generative or exploratory because it generates
new, open-ended insights."

A critical scoping statement: **"Discovery does not (typically) involve testing a hypothesis
or evaluating a potential solution."**

The research topic starts extremely broad and narrows "on those aspects of the problem
space that have the most unknowns or present the greatest opportunities." Common methods
named: **user interviews, diary studies, field studies**. Surveys "can also be used to gather
data from a larger group of users; the data can be triangulated with qualitative insights
from other methods."

### Stakeholder interviews
[S028] argues these are not a formality. Interviewing key people yields:

- Key business objectives of the organization, individuals, or teams — "helpful to determine
  if and how these broader goals tie-in to the goals of the project"
- Data about how user-facing problems impact **backstage work** (inquiry type and volume,
  additional processing)
- **Solutions they've tried before** that did or didn't work, how they were implemented,
  what other problems they caused, and why they were removed

It notes a second-order benefit: including stakeholders "not only facilitates further
buy-in, it also provides more insights."

### Workshops
[S028] lists six, with distinct purposes:

| Workshop | Purpose |
|---|---|
| **Kickoff** | Align on the objective of the discovery and when it will be complete; agree roles and responsibilities |
| **Assumption mapping** | Question the validity of certain 'facts' and identify deep-rooted assumptions needing exploration. Can include **prioritizing assumptions by risk to the project's outcome** — "The riskiest assumptions should be prioritized in terms of research activities" |
| **Research-question generation** | Discuss the unknowns and draft research questions, prioritized by importance and by how well they gather the knowledge needed. Often combined with assumption mapping |
| **Affinity diagramming** | After exploratory research, transfer insights to sticky notes and group them "to uncover themes around problems, causes, symptoms, and needs" |
| **Mapping** | Plot insights into a map of the problem space, customer experience, journey, or service — "to create alignment, to identify gaps that need further research, and to highlight major opportunities" |
| **Ideation** | Takes place **at the end** of the discovery. Craft How-Might-We statements from uncovered problems and generate solution ideas to explore going forward |

Note the sequencing: ideation is positioned at the *end* of discovery, not the beginning.

## Who does discovery

[S028] recommends "a small multidisciplinary team," ideally dedicated full-time, and
explicitly sizes it: **"between 3 and 7 members is ideal."**

Key roles [S028]:

- **Someone who can do research** — a UX researcher or UX designer to plan and carry out
  user research.
- **Someone who can facilitate or lead** — "Although self-organizing teams are always best,
  a team leader is helpful when team members are new to discovery or the team is large."
  [S028] explicitly lists multiple possible titles: **product manager, project manager,
  delivery manager, service designer, UX strategist.**
- **A sponsor or owner** — someone from the organization who owns the project, has domain
  expertise, and is "influential enough to get the discovery team access to other people,
  teams, or data."
- **Someone technical** — a developer or technical architect "who understands enough
  technical detail to be able to speak to engineers," to explore available technologies,
  capabilities and constraints.

> **Contested.** [S064] found that "the biggest disagreement" between PMs and UX
> professionals in a 372-person survey was **who should conduct discoveries**. [S110] argues
> ownership should be shared rather than assigned to a specialist function. Treat discovery
> ownership as something to negotiate explicitly, not assume. See
> [../01-foundations/pm-and-ux-collaboration.md](../01-foundations/pm-and-ux-collaboration.md).

## Outputs

[S028] is careful here: **"Discovery isn't about producing outputs for their own sake."**
The following *might* be produced to help organise learning:

- A **finalized problem statement** — "a description of the problem backed up with evidence
  that details how big it is and why it's important"
- Finalized maps, such as a user-journey map or service blueprint
- User-needs statements
- Personas
- High-level concepts or wireframes, for exploring in the next phase

## A legitimate outcome: deciding not to proceed

[S028] states this explicitly and it is easy to overlook:

> "In some cases, the end of a discovery might be a decision not to move forward with the
> project because, for example, there isn't a user need."

A discovery that kills an initiative has succeeded, not failed.

## Where discovery sits: the Double Diamond

[S028] maps discovery onto the UK Design Council's Double Diamond: **discovery covers the
Discover and Define stages.** In Discover, "lines of inquiry diverge as a team explores the
problem space." In Define, "the team aligns on an evidence-based problem statement and on a
vision for the future." Ideating and testing belong to the subsequent Develop stage.

See [discovery-frameworks.md](discovery-frameworks.md) for the full model and its
attribution.

## Why teams skip discovery, and the consequences

[S110] quotes Juan Manuel Agudo Carrizo (Head of Product; formerly Real Madrid and eBay) on
the mechanism:

> "Normally, when discovery doesn't happen, it's because teams feel they don't have
> permission to slow down and explore... Either leadership hasn't prioritized discovery, or
> teams are buried in delivery. They've become output factories." [S110]

[S110] lists consequences of skipping discovery: building a product that doesn't address
actual needs; wasted time and resources on a product that may not gain market acceptance;
overspending and additional budget to rectify mistakes post-launch; negative reviews from
unmet needs; and a product that "tries to serve everyone but doesn't fully satisfy anyone."

> **Evidence note.** These consequences are presented as reasoning and illustrated with
> invented or anecdotal examples (the article's Google Glass reference is not sourced). They
> are plausible and widely held, but the corpus contains **no study measuring the effect of
> discovery on product outcomes.** Recorded as a gap.

## Limitations

- [S028] is written from a **UX-design perspective** and situates discovery in "the UX-design
  process." A product manager reading it should note the framing, though the substance
  applies broadly.
- The corpus contains **no primary source by Teresa Torres or Marty Cagan**, the two authors
  most associated with modern continuous product discovery — only second-hand summaries.
  This is a significant gap given how central their work is to the topic.
- [S110] is a commercial training provider's guide with heavy template promotion; its
  substantive content has been retained and its CTAs excluded.

## Related concepts

- [discovery-frameworks.md](discovery-frameworks.md) — dual-track, Double Diamond, OST, Lean Startup, Design Sprint
- [user-research-methods.md](user-research-methods.md) — choosing a method
- [user-interviews.md](user-interviews.md)
- [hypotheses-and-assumptions.md](hypotheses-and-assumptions.md)
- [opportunity-assessment.md](opportunity-assessment.md)
- [../05-planning/prioritization.md](../05-planning/prioritization.md)
- [../10-risk/product-risk.md](../10-risk/product-risk.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S028 | Nielsen Norman Group, Maria Rosala — *Discovery: Definition*, 15 Mar 2020, last reviewed 2 Aug 2024 | UX research organization, practitioner-authored | Definition, outcomes, instigators, activities, roles, outputs, Double Diamond placement |
| S110 | Product School — *The Definitive Guide to Product Discovery and Frameworks* | Training-provider guide | PM-side definition, three questions, ownership debate, consequences of skipping |
| S076 | Productboard — *Product Management Data for Discovery* | Vendor blog | Data inputs to discovery |
| S081 | Product School — *Product Opportunity Assessment* | Training-provider blog | Placement of assessment within customer discovery |
| S064 | Nielsen Norman Group — *PM and UX Have Markedly Different Views* | Survey research | Evidence that discovery ownership is disputed |
