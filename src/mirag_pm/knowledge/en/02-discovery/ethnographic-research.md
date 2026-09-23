---
title: Ethnographic Research and Contextual Observation
domain: discovery
type: technique
topics:
  - ethnography
  - ethnographic research
  - contextual inquiry
  - field research
  - participant observation
  - observer bias
  - say-do gap
source_count: 2
sources: [S029, S045]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Ethnographic Research and Contextual Observation

## Definition

[S029]: "Ethnographic research is a type of qualitative research methodology that involves
studying people in their natural environment rather than in a formal research setting. The aim
is to gain insights into how people interact with their environment and the products or
services within it. This is achieved by observing and sometimes participating in people's
daily lives."

[S045]: "Ethnography is defined as a qualitative study of social interactions, behaviors, and
perceptions that occur within groups, teams, organizations, and communities."

**Origin.** Both sources agree the method comes from anthropology. [S029]: "The term
'ethnography' comes from the field of anthropology, where it was used to describe the detailed
study of cultures." [S045] adds it is "also known as field research, site visits, contextual
inquiry, to mention a few."

## The problem it exists to solve

[S045] quotes cultural anthropologist Margaret Mead:

> "What people say, what people do, and what people say they do are entirely different things."

This is the methodological justification: attitudinal methods (interviews, surveys) capture
reports of behaviour; ethnography captures behaviour. It is the sharpest statement in the
corpus of the **say–do gap**, and it connects directly to the
behavioral/attitudinal axis in [user-research-methods.md](user-research-methods.md).

[S045] also quotes Ken Anderson, Intel Research's anthropologist, from Harvard Business Review:

> "Our goal is to see people's behavior on their terms, not ours. While this observational
> method may appear inefficient, it enlightens us about the context in which customers would
> use a new product and the meaning that product might hold in their lives."

## Defining characteristics

[S029] names two:

- **Focus on context.** "The researcher observes how people behave in their natural
  environment, rather than in a controlled setting. This can provide a more accurate and
  nuanced understanding of user behavior."
- **Inductive approach.** "Rather than starting with a hypothesis, the researcher collects
  data and then derives insights and theories from that data. **This allows for unexpected
  findings to emerge.**"

The inductive property is what distinguishes ethnography from usability testing or
experimentation, which evaluate a predetermined question.

## Types

[S029] names three, by the researcher's degree of participation:

| Type | Definition [S029] |
|---|---|
| **Realist ethnography** | "The traditional form... where the researcher observes without participating" |
| **Critical ethnography** | "Involves the researcher actively participating in the culture or community being studied" |
| **Autoethnography** | "Involves the researcher studying their own culture or community" |

## Process

[S045] gives five steps:

1. **Define research objectives** — "What are the key questions you need to answer? This step
   is crucial as it guides the entire ethnography research process."
2. **Select research methods** — participant observation, in-depth interviews, focus groups,
   surveys. "Each method has its strengths and weaknesses."
3. **Recruit participants** — "Whether through random sampling or purposive sampling, ensure
   that your participants are representative of your target audience."
4. **Conduct fieldwork** — "Collect data through observations, interviews, and other methods
   by spending time with participants in their natural environments, such as their homes,
   workplaces, or communities."
5. **Analyze data** — "using techniques like coding, theme identification, and data
   visualization."

[S029] adds a conduct rule for the fieldwork stage: **"The researcher should be as unobtrusive
as possible to avoid influencing the behavior of the participants. They should also be
open-minded and flexible, as unexpected findings often emerge."**

### Planning detail [S029]
"The research site should be a place where the behavior of interest naturally occurs, and the
participants should be people who engage in this behavior."

## Documented examples

These are the corpus's most concrete illustrations of insight that other methods would have
missed.

**Adidas** [S045]. The company was "creating performance sports shoes and apparel based on the
assumption that what was desirable to performance athletes would ultimately also be attractive
to consumers," and struggled in the fitness segment. "Ethnographic studies made by the company
revealed a compelling truth — that the priorities of consumers differed significantly from
those of athletes. For instance, consumers expected their clothes and shoes to be aesthetically
pleasing, a feature athletes typically did not care about. This was the foundation of Adidas
making sweeping changes in its product strategy."

**The screwdriver indentation** [S045]. Ethnographers followed electricians and plumbers at
work. "It was observed that some handyman stored their screwdrivers in a tool belt for easy
access. When up a ladder, they would reach for a tool and sometimes pick out the Phillips
screwdriver when they were looking for the one with a flat blade. It was this observation that
led ethnographers to suggest creating tools with an indentation on top to indicate the nature
of the tip — an (x) for the Phillips and a (-) for the slotted end." [S045]'s own framing of
why this matters: it was "a fact that could have slipped through numerous interviews and focus
group conversations."

**Netflix** [S045]. "Netflix partnered with cultural anthropologist Grant McCracken to witness
how their users behaved and lived in their own homes to gain a better understanding of the
meaning and importance of binge-watching. Insights from this study formed the base of strategic
decisions to release episodes in bulk to boost viewership."

> **Verification status: UNVERIFIED.** All three examples are recounted by a UX agency's blog
> without citation to company sources or published research. They are illustrative, not
> evidentiary. The Adidas and Netflix stories in particular are widely circulated industry
> anecdotes whose primary documentation is not in the corpus.

## Advantages

[S045]:
- First-hand observation of users interacting with technology in their natural environment
- **"Identify unexpected issues that you might not have encountered in a usability test"**
- Accounts for the complexity of group behaviors
- Reveals interrelationships among multifaceted dimensions of group interactions
- Provides context for behaviors

## Limitations and trade-offs

This is the section that matters most for deciding whether to use the method. Both sources are
explicit.

| Limitation | Description |
|---|---|
| **Time and resources** | [S029]: "requires the researcher to spend a significant amount of time in the field... This can be a challenge for product managers who are often juggling multiple responsibilities." Analysis is also "complex and time-consuming." [S045]: "Requires sustained efforts and engagement in terms of budget." |
| **Observer effect** | [S045]: "Shorter sprints may result in skewed data as users aware of the researchers may behave differently." This is a direct trade-off against the time limitation — *shortening* the study to save resources undermines the data. |
| **Researcher bias** | [S029]: "The researcher's own beliefs and assumptions can influence their observations and interpretations." [S045] lists "possibility of observer bias" independently. |
| **Difficulty generalizing** | [S029]: "Because ethnographic research involves studying a small group of people in a specific context, it can be difficult to apply the findings to other groups or contexts." |
| **Depends on team and participant diversity** | [S045] names this as a constraint on validity. |

### Mitigations offered
[S029] names two techniques against researcher bias:
- **Triangulation** — "using multiple sources of data to confirm findings."
- **Reflexivity** — "reflecting on their own beliefs and assumptions and how they might be
  influencing the research."

### A reframe on generalizability
[S029] argues the generalization limitation is partly a category error: "the goal of
ethnographic research is not to generalize, but to gain a deep understanding of a specific
behavior in a specific context."

> This is a defensible methodological position, but it should not be used to wave away the
> limitation. **If a decision requires knowing how widespread a behaviour is, ethnography is
> the wrong instrument** — pair it with a quantitative method.

## A claim requiring caution

[S045] states: "Research suggests that higher empathy towards users leads to stronger financial
performance, better customer satisfaction, greater creativity, and even healthier employees."

> **Classification: UNVERIFIED.** No study is cited, no effect size given, and the causal
> direction is asserted rather than demonstrated. [S045] also claims ethnography "provides a
> more accurate and in turn better ROI for a business" without evidence. Both are marketing
> claims by a UX agency and should not be repeated as established findings.

## Related concepts

- [user-research-methods.md](user-research-methods.md) — why observed behaviour differs from reported behaviour
- [user-interviews.md](user-interviews.md)
- [product-discovery.md](product-discovery.md)
- [identifying-unmet-needs.md](identifying-unmet-needs.md)
- [../12-design-and-ux/service-design.md](../12-design-and-ux/service-design.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S029 | LaunchNotes Glossary — *Ethnographic Research: Definition, Examples & Uses* | Vendor glossary | Definition, characteristics, types, process, limitations, bias mitigations |
| S045 | Koru UX (Bansi Mehta) — *How to Use B2B Product Ethnography in Product Development* | UX agency blog | Definition, Mead and Anderson quotes, examples, advantages/disadvantages, process steps |
