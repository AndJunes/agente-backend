---
title: PM and UX Role Boundaries (Survey Evidence)
domain: foundations
type: research-finding
topics:
  - PM and UX
  - role overlap
  - responsibility ambiguity
  - who owns discovery
  - cross-functional boundaries
  - RACI
source_count: 1
sources: [S064]
evidence_type: empirical-survey
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# PM and UX Role Boundaries (Survey Evidence)

## Why this document exists

Most role descriptions in this knowledge base are assertions by vendors or practitioners.
**This one reports measured disagreement.** It is the strongest empirical evidence in the
corpus about how product responsibilities are actually perceived, and it establishes an
important operating principle: *who owns a given product activity is not derivable from the
job title.*

## The study

[S064], Nielsen Norman Group, published 2 May 2021 by Kara Pernice and Raluca Budiu.

- **Sample analysed here:** 372 responses from professionals whose primary role was UX
  (279 people) or PM (93 people). The full survey had more than 500 responses across product
  development roles.
- **Experience mix:** 60% had 3–10 years in PM or UX; 21% under two years; 19% over ten years.
- **Geography:** 54% United States, 27% Europe.
- **Question asked:** "For each of the following activities, which role do you feel should be
  *most responsible*?" — explicitly about final responsibility, not involvement.
- **Statistical treatment:** differences reported are statistically significant at p < 0.05
  unless the source states otherwise.

> Note the sample imbalance: UX respondents outnumber PM respondents roughly 3:1. The source
> does not discuss what effect this has on the comparisons.

## Headline finding

> "Almost all responses about responsibilities were different." [S064]

The authors name the underlying mechanism **appropriation**: "the tendency by PM and UX to
believe that everything was their job."

## Where the disagreement was largest

### Discovery and research
- Both groups mostly assigned **user interviews** and **user testing** to UX, but to
  significantly different degrees.
- **The biggest disagreement was about who should conduct discoveries.**
- Only **46% of PMs** considered user testing a UX activity.

### Ideation and early design
- **Ideation** and **prioritizing user needs in design** were assigned to UX by **more than
  three quarters of UX respondents**, but by **only about a third of PM respondents** — with
  another third of PMs assigning them to PM.
- Also disagreed on: defining task flows, wireframing and sketching.

### Where they agreed (design execution)
- Decide how a design will look and feel — 82% of PMs and 80% of UXers said UX.
- Make UI prototypes — 82% PMs, 88% UXers said UX.
- Create the final visuals in the UI — 79% PMs, 78% UXers said UX.

### Information architecture
- **50% of product managers believed development should be responsible for IA**; only 27%
  thought it was a UX job.
- **75% of UXers believed UX should be responsible for IA.**

[S064] argues the PM view is mistaken: "While code architecture is certainly development's
forte, creating the categorization and hierarchy of information in an app is the work of an
information architect, which is a UX role."

### Communicating design and customer knowledge
- **Communicating the voice of the customer to the product team** was the most fragmented:
  25% of PMs said PM, 29% said CX, 16% said PO, and only **9% of PMs assigned it to UX —
  versus 54% of UX respondents.**
- Explaining the design to leadership: 45% of PMs said PM; next most common PM answer was UX (29%).
- Getting buy-in for the design from stakeholders: 53% of PMs said PM; 23% said UX.

[S064]'s position on this: "it's not a good idea to have someone else other than the designer
pitch a design — the presenter may not properly understand the reasoning behind each decision
and may not accurately convey feedback back to the designer." It further argues the pattern
"robs UX from an opportunity to become visible in the organization and, in the long run, can
decrease the trustworthiness and growth of the UX role."

### Project-management-related tasks
- **Product vision and prioritization:** over 63% of PMs assigned all such tasks to PM; UXers
  split between PM and product owner.
- **Track process to deliver on time:** the only task assigned to PM *more often by UXers
  than by PMs*.
- **Ensure the project meets business requirements:** PMs said PM; UXers said PO. Both
  differences significant.
- **Report product status to leadership:** 72% of PMs said PM vs 53% of UXers; 40% of UXers
  said PO vs 22% of PMs.
- **Understand the product's competitive position:** PMs claimed it; UXers split between PM,
  PO and marketing. Marketing was named by comparable shares (21% PM vs 24% UX, not
  significant).

### Perceived power
Respondents ranked ten roles by influence. Both groups "ranked all roles very similarly."
The **only statistically significant difference** was that product owner was ranked higher by
PM respondents than by UX respondents (Wilcoxon rank test, p < 0.05).

## Why role ambiguity is costly

[S064] identifies concrete consequences rather than treating ambiguity as neutral:

- **Duplicated work, confusion, and dissatisfaction** when the two groups are not aligned.
- **Quality loss when work is done by the unskilled.** A quoted respondent: "UX Research done
  by non-researchers often does not meet our quality or process standards, resulting in user
  testing, findings, and recommendations that are not reflective of actual user behaviors and
  negatively impact the product."
- **Underutilization** of people whose skills go unused.

## The trade-off: skills-based staffing

[S064] reports that some development teams have shifted to hiring for **skills rather than
roles** — a gap analysis may show a team needs "someone who can create a product vision or
can build a high-fidelity prototype" rather than a product manager or a visual designer.

**Stated benefits:** more flexible staffing; individuals can vary their tasks, which "can be
gratifying, stimulate employee growth, and help organizations retain great employees."

**Stated costs** — this list is unusually explicit and worth preserving in full:

| Cost | [S064]'s description |
|---|---|
| Less practice | "Someone may not fully develop a skill if they don't do it frequently, so their output may be of lower quality and take more time to produce." |
| Lack of awareness | "Enjoyment is not a skill. Just because people relish doing something or see a need for it does not mean they are good at it." |
| Missing expertise | UX is nuanced enough that non-UX people "can be difficult... to know when UX work is done well or not." People with little training "often will not know when they did a substandard job." |
| Decreased efficiency | Someone else may do the job better and faster. Example given: "a UXer may be able to workshop and derive a product vision, but a PM may do it more thoroughly and get the right high-level stakeholders involved." |
| Difficult hiring | Varied skill requirements make candidates harder to find. |

## Decision considerations

[S064]'s recommendation is deliberately modest — the authors reject the idea of
standardizing job descriptions globally, on the grounds that the descriptions would be
obsolete before they were finished.

What they recommend instead:

1. **Sync explicitly at the earliest phase of a project**, and say specifically who will do
   discoveries, ideation, early sketching, and design workflows.
2. **Assert task ownership clearly throughout the project**, so each person knows what they
   are responsible for at each point.
3. **Make those responsibilities visible to the rest of the product team**, not just to the
   two people involved.

## Operating principle for a PM agent

Because the disagreement is measured rather than anecdotal, the correct inference is *not*
"UX owns research" or "PM owns vision." It is:

> **Ownership of discovery, ideation, early design, and voice-of-customer communication is
> ambiguous by default and must be established explicitly per organization and per project,
> ideally before work begins.**

An agent asked "who should run the user interviews?" should surface the ambiguity and the
need to agree, rather than assert a single answer.

## Limitations

- Single source; no replication in the corpus.
- Sample skews heavily toward UX respondents (279 vs 93).
- Respondents reported what they thought *should* happen, not what *did* happen.
- Published 2021; the corpus contains no later measurement of the same question.
- The authors are a UX research organization, and several interpretive passages advocate for
  UX ownership. The **numbers** are the evidence; the **interpretations** are NN/g's position.

## Related concepts

- [product-manager-vs-product-owner.md](product-manager-vs-product-owner.md)
- [product-manager-role.md](product-manager-role.md)
- [../02-discovery/product-discovery.md](../02-discovery/product-discovery.md)
- [../12-design-and-ux/product-triad.md](../12-design-and-ux/product-triad.md)
- [../12-design-and-ux/ux-for-product-managers.md](../12-design-and-ux/ux-for-product-managers.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S064 | Nielsen Norman Group, Kara Pernice & Raluca Budiu — *PM and UX Have Markedly Different Views of Their Job Responsibilities*, 2 May 2021 | Empirical survey, n=372, significance-tested | Entire document |
