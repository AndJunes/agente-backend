---
title: Hypotheses, Assumptions and Validation
domain: discovery
type: process
topics:
  - hypothesis
  - assumptions
  - assumption mapping
  - validation
  - riskiest assumption
  - evidence
  - risk vs evidence grid
  - experiments
synonyms:
  - assumption testing
  - idea validation
  - hypothesis validation
source_count: 5
sources: [S028, S087, S081, S110, S053]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Hypotheses, Assumptions and Validation

## Why assumptions are the unit of work

Every product idea rests on beliefs that have not been checked. The corpus's consistent
position is that **the job of early product work is to find the beliefs that would break the
idea if wrong, and check those first** — not to check everything, and not to check the easy
things.

[S028] states the prioritization rule directly, in the context of an assumption-mapping
workshop:

> "Part of this workshop can also include prioritizing assumptions in terms of risk to the
> project's outcome. **The riskiest assumptions should be prioritized in terms of research
> activities.**"

## Definitions used in the corpus

| Term | Definition as used |
|---|---|
| **Hypothesis** | [S110]: stage 1 of customer discovery is to "Define a hypothesis: Identify a core problem or unmet need in the market." [S009] frames it operationally as "define what you believe to be true" |
| **Assumption** | [S087]: "the hidden beliefs behind product ideas." [S110]: "critical assumptions around customer behavior, needs, market size, and potential demand" |
| **Validation** | [S081]: confirming "that your target users actually experience this problem and feel motivated to solve it" — explicitly to "avoid expensive assumptions and ensure you're tackling genuine needs rather than perceived ones" |

Note that the corpus does **not** supply a rigorous hypothesis-statement template (of the form
*"We believe that [X] will result in [Y]; we will know we are right when [measurable signal]"*).
[S053] lists "Hypothesis Statement" as a related pattern but does not define it. **Recorded as
a gap.**

## Two mapping techniques

Both come from [S087], which presents them as tools for handling product risk.

### Assumption Mapping
> "Assumption Mapping helps uncover the hidden beliefs behind product ideas and plots them by
> **importance** and **uncertainty**. Assumptions that are both critical and uncertain become
> top priorities for validation. This method supports lean, fast experimentation and is
> especially useful in early-stage product development." [S087]

**The two axes:**

```
           high uncertainty
                  │
   investigate    │   ▶ VALIDATE FIRST ◀
   if cheap       │   (critical + unknown)
  ────────────────┼────────────────  high importance →
   ignore         │   monitor
                  │   (critical but well-understood)
           low uncertainty
```

The operative quadrant is **high importance + high uncertainty**. An assumption that is
critical but well understood needs no experiment; an assumption that is uncertain but
inconsequential is not worth the cost of finding out.

### Risk vs Evidence Grid
> "This framework plots each risk based on **how risky it is** versus **how much supporting
> evidence exists**. High-risk, low-evidence items signal major knowledge gaps and are prime
> candidates for research, prototyping, or early testing. It encourages data-informed
> decision-making rather than gut instinct." [S087]

The two grids are near-isomorphic — *uncertainty* and *lack of evidence* describe the same
condition from different directions. The practical difference is the input: assumption mapping
starts from **beliefs**, the risk/evidence grid starts from **identified risks**. Teams that
have already run risk identification can use the second without redoing the first.

See [../10-risk/product-risk.md](../10-risk/product-risk.md) for the risk taxonomy these
attach to.

## The workshop that produces the map

[S028] describes two discovery workshops that feed this process, noting they "are often
combined":

| Workshop | What happens [S028] |
|---|---|
| **Assumption-mapping workshop** | "Many teams bring in experts and conduct data-gathering activities in a workshop. They question the validity of certain 'facts' and identify the deep-rooted assumptions that need further exploration." |
| **Research-question–generation workshop** | "The team discusses what the unknowns are and drafts research questions. The research questions can be prioritized in terms of their importance and how well they will work to gather the knowledge needed to move forward." |

The sequence implied: surface assumptions → prioritize by risk → convert the top ones into
**research questions** → choose a method per research question (see
[user-research-methods.md](user-research-methods.md)).

Note that [S028] has teams "question the validity of certain '**facts**'" — the scare quotes
are the source's. A significant part of the exercise is discovering that things the team
treats as known are actually assumed.

## Methods for validating an assumption

[S081] lists validation instruments, ordered roughly by cost:

| Method | What it produces | [S081]'s note |
|---|---|---|
| **Analyze existing data** | Confirmation of behavioural patterns | "product analytics, customer support logs, or CRM insights — to further confirm patterns" |
| **Landing-page test / smoke test** | Expressed interest at low cost | "build a simple landing page outlining your solution clearly, track engagement and sign-up rates, and gauge genuine interest levels before significant investment" |
| **Pre-launch waitlist** | Expressed intent | Grouped with smoke tests as "lightweight idea validation experiments" |
| **Targeted surveys** | Quantitative validation at scale | Subject to the survey constraints in [surveys.md](surveys.md) |
| **Customer interviews** | Qualitative pattern confirmation | "Aim for a minimum of 8–10 quality conversations to identify clear patterns" |
| **Prototype testing** | Behavioural evidence on a solution | Named by [S030] in the detailed-analysis stage |
| **MVP** | Behavioural evidence in market | [S110] — see the MVP gap noted in [discovery-frameworks.md](discovery-frameworks.md) |

[S081] adds a discipline that is easy to skip: **"Document your validation findings clearly,
identifying consistent themes, discrepancies, or unexpected insights. Be prepared to challenge
or adjust your initial assumptions based on what you learn."**

## A caution on what counts as validation

The corpus contains material that undercuts naive validation, and it should be applied here:

- **Stated interest is attitudinal.** A landing-page signup measures a click, not a purchase;
  a survey response measures a report, not a behaviour. See
  [user-research-methods.md](user-research-methods.md) and the Netflix DVD case in [S074].
- **Discovery is not hypothesis testing.** [S028] is explicit: "Discovery does not (typically)
  involve testing a hypothesis or evaluating a potential solution." Generative research
  *produces* the hypotheses; validation comes after. Running validation before you have framed
  the problem is the failure [S081] warns about — "Assessing too early can lead you to fixate
  on the wrong problem before you've seen the full picture."
- **Confirmation-seeking is the default failure.** [S105] describes stakeholders who
  "cherry-pick the data that supports their preexisting assumptions," and recommends
  triangulation as a countermeasure. [S006] frames the discipline as deliberately considering
  opposing ideas: "it's good to question your assumptions and put your hypothesis through
  rigorous testing... It's about playing devil's advocate with your ideas."

## The reasoning chain this enables

This is the sequence an agent should be able to reconstruct:

```
Idea or initiative
      ↓
What must be true for this to work?          → assumptions surfaced
      ↓
Which of those are critical AND uncertain?   → assumption map / risk-evidence grid
      ↓
What question would tell us?                 → research question
      ↓
What method answers that kind of question?   → qual/quant × behavioral/attitudinal
      ↓
Run it; document findings honestly
      ↓
Validated → proceed to definition and prioritization
Invalidated → reframe, pivot, or stop
```

The last line matters: [S028] records that "the end of a discovery might be a decision not to
move forward with the project." **A hypothesis that fails validation has done its job.**

## Limitations

- **No hypothesis template in the corpus** (see above). This is a notable gap for an agent that
  must help teams *write* testable hypotheses, not just reason about them.
- **No experiment design guidance** — sample size, duration, success thresholds, or what
  constitutes a decisive result. [S087]'s grids tell you *what* to test, never *how well*.
- **Assumption mapping and the risk/evidence grid are each described in one short paragraph**
  by a single commercial source [S087]. Their originators are not named; [S028] independently
  confirms assumption mapping is an established workshop practice, which raises confidence in
  the technique's existence but not in this description's completeness.
- **No treatment of leap-of-faith assumptions, falsifiability, or the distinction between
  desirability, viability, feasibility and usability risks as separate assumption classes** —
  though [S028] and [S087] both gesture at the last one.

## Related concepts

- [product-discovery.md](product-discovery.md)
- [opportunity-assessment.md](opportunity-assessment.md)
- [user-research-methods.md](user-research-methods.md)
- [discovery-frameworks.md](discovery-frameworks.md) — Lean Startup's build–measure–learn and pivot/persevere
- [../10-risk/product-risk.md](../10-risk/product-risk.md)
- [../10-risk/assumptions-and-constraints.md](../10-risk/assumptions-and-constraints.md)
- [../05-planning/prioritization.md](../05-planning/prioritization.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S028 | Nielsen Norman Group — *Discovery: Definition* | UX research organization | Assumption-mapping and research-question workshops, riskiest-assumption prioritization, scope of discovery |
| S087 | Product School — *Product Risk: What It Is and How to Manage It*, updated 25 Jun 2025 | Training-provider guide | Assumption Mapping, Risk vs Evidence Grid |
| S081 | Product School — *Product Opportunity Assessment* | Training-provider guide | Validation methods, interview count, documentation discipline |
| S110 | Product School — *The Definitive Guide to Product Discovery* | Training-provider guide | Hypothesis and assumption stages of customer discovery |
| S053 | Learning Loop — *Job Story (JTBD)* | Practitioner glossary | Related-pattern reference to Hypothesis Statement and Assumption Mapping |
