---
title: Risk Assessment and Analysis
domain: risk
type: process
topics:
  - risk assessment
  - qualitative risk analysis
  - quantitative risk analysis
  - probability and impact matrix
  - risk score
  - risk data quality
  - 5 whys
source_count: 3
sources: [S051, S100, S016]
evidence_type: standards-aligned
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Risk Assessment and Analysis

## Definition

[S051]: "Risk assessment is the process by which **the identified risks are systematically analyzed
to determine their probability of occurrence and the potential impact of that occurrence.**"

And as an activity: "a **qualitative measure** using risk data and the parameters of probability and
impact, to **identify, categorize, prioritize, and manage risks before they happen.**"

**Reassessment** [S051]: "the work done to **update the original risk assessment due to changes in
the project** or overall risk management efforts."

## Qualitative versus quantitative analysis

[S100] separates these clearly, and the distinction determines what a team can actually conclude:

| | Qualitative risk analysis | Quantitative risk analysis |
|---|---|---|
| **Aim** | "Determine the **severity and likelihood** of each risk event" | "Relies on data to analyze the probability and impact of risk events" |
| **Basis** | Judgment against defined criteria — "**more subjective**" | "Calculating, simulating, or estimating risk-related information" |
| **Methods** | Probability and impact matrix; risk data quality assessment | "**Expected monetary value analysis, Monte Carlo analysis, cost and schedule impact assessments**" |
| **Requires** | Agreed scales and criteria | "Formulas or computer-based programs" |
| **Produces** | Prioritised risk list; risk exposure view | "Results valuable for **risk reporting and informing crucial project decisions**" |

[S100] on what qualitative analysis is *for*: "helps project managers **prioritize risks,
understand the project's risk exposure, the potential impact on the project, and determine the
appropriate responses.**"

> **Most software product work will only ever do the qualitative pass.** That is legitimate —
> but it means the outputs are *ordered judgments*, not measurements. Treating a PI score as a
> quantity is the most common misuse.

## The probability and impact matrix

Also called the **risk assessment matrix** or **risk matrix**. [S100]: "You can use this matrix to
**identify the most urgent risks that require immediate action.**"

### What the matrix records
[S051]: "The risk matrix documents at least four core areas for each identified risk: **(1) risk
name, (2) probability, (3) impact, and (4) risk level/ranking.**"

Its full structure [S051]:

| Element | Definition |
|---|---|
| **Risk category** | "From a standardized list of risk categories (e.g., technology, natural disaster, regulations, transportation)... **not all projects have risks in all categories**" |
| **Probability criteria** | "Used to assign the probability values for a risk category; **criteria should come from a standardized list but customized for each project**" |
| **Probability (P) score** | "A value given to each risk driven by the probability criteria; the matrix's score scale will state the parameters for the minimum and maximum value" |
| **Impact criteria** | Same structure as probability criteria |
| **Impact (I) score** | Same structure as the P score |
| **PI score** | "**The Probability score multiplied by the Impact score.** The PI score is the overall risk assessment score; **used to rank all project risks** by lowest probability and impact to highest, **so resources are assigned accordingly**" |
| **Total Project Risk** | "**All PI scores are added, and then that sum is divided by the quantity of risks to determine the average**; the project's PI average value is the Total Project Risk value" |

> **A caution on Total Project Risk.** Averaging PI scores means a project with one catastrophic
> risk and many trivial ones can score the same as a project with uniformly moderate risks. The
> average tells you about the *distribution*, not about *exposure*. [S051] presents the
> calculation without this caveat. Recorded in
> [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

[S051] notes the matrix's position in the process: "**an output of the Risk Assessment process and
an input to the Risk Response process.**"

## Data quality is the binding constraint

[S051] returns to this repeatedly and it is the document's most important caution:

> "For the original and subsequent assessments, **the quality of data used to determine the impact
> directly correlates to the accuracy of the risk assessment and resulting decisions.**"

**Risk data quality assessment** [S051]: "Risk assessment is a qualitative assessment. Therefore,
**risk data quality always impacts the risk assessment quality. A risk data audit helps ensure the
quality of data used.** Project managers may use **experts or previous project documentation**
as part of the risk data quality assessment."

[S100] describes the same activity: it "helps project managers collate data to determine **how much
data is available, the quality, reliability, and integrity of the data, and how well they
understand the risk.**"

> In other words: **before scoring a risk, assess whether you know enough to score it.** A
> confidently-scored risk based on no data is worse than an acknowledged unknown, because it
> stops further inquiry. This is the risk-management analogue of [S031]'s "confidence bands matter
> more than precision."

## Worked example

[S051] gives a full example — a coastal North Carolina town facing hurricanes. The value is in the
**sequence**, which transfers to any domain:

1. **Determine risk categories** — natural disasters
2. **Determine types within the category** — hurricane storms
3. **Identify a specific risk event** — "hurricane bringing flooding to downtown buildings"
4. **Assess the impact** — "flooding damages ground floors"
5. **Assess the probability** — using "**verified data, like National Weather Service hurricane
   projections**"; for impact, "cost and quality data like town records"
6. **Document** — "the data and risk scoring are organized in the project risk assessment matrix"
7. **Communicate** — "to the team and stakeholders"
8. **Use as input to response planning** — "making sandbag materials available when needed and
   training people to set them up"

**The economic logic** [S051]: "if the assessment indicates the risk is **highly likely to occur
with a high impact**... it will have a higher risk score. That can mean **more time invested in
risk response planning**... **The cost of buying and storing sandbag materials to protect the
buildings is much lower than the cost of fully repairing water-damaged buildings.**"

> Note that probability and impact were sourced from **different kinds of evidence** — forecasts
> for probability, historical records for impact. Good assessment rarely uses one data source for
> both.

## Inputs

[S051]: "A risk assessment **should be customized to fit the project context.**" Standard inputs:

- Project management plan
- Risk management plan
- **Risk assessment methodology**
- **Risk parameter definitions**
- **Risk tolerance levels**
- Risk probability and impact matrix template
- **Risk assessment scale** — "what criteria are used to determine if the risk score is high, mid,
  or low"
- Risk assessment matrix template

[S051] adds that beyond probability and impact, "**additional parameters, like cost or schedule,
can be standalone matrices.**"

## Outputs

[S051]: "Project Management Plan updates · Project document updates · Risk Management Plan updates ·
Risk Register updates · Risk Response Plan updates."

## Seven steps to building a risk assessment

[S051]'s procedure, condensed to its substance:

1. **Identify applicable risk types and organize them** — "You cannot assess risk if you have not
   identified it... Risks can be of any size and with internal or external triggers." Organise "by
   different factors (internal or external triggers) or by categories (environmental, regulatory,
   technology, or staffing)."
2. **Determine how risks will be qualified and quantified** — "**Remember, the quality of the data
   used in the assessment impacts its accuracy.**"
3. **Determine your organization's risk tolerance** — with stakeholder input, per project. See
   [risk-management.md](risk-management.md).
4. **Determine the output format** — "**How the risk assessment output is documented is important
   because it determines how the information is made available** to the project team and
   stakeholders."
5. **Plan for reusability across projects** — "**Maintaining a consistent and detailed project
   documentation archive helps ensure a project's lessons learned are available to other project
   managers with similar projects**, which can reduce the impact of negative risks."
6. **Make it flexible and scalable** — "You may have to add risks throughout the project... the
   risk assessment should be **flexible enough to remain aligned with project changes and scalable
   enough to be used in multiple projects.**"
7. **Determine the update process** — "**Changes are inevitable, and a risk assessment that is not
   current is not effective.**"

## Related analysis methods

[S016] (Mitti) names additional analysis tools without developing them: a **risk analysis
framework**, **risk analysis methods**, the **risk assessment matrix**, **5 Whys**, **needs
assessment**, and **business impact analysis**. It also distinguishes "risk assessment" from "risk
analysis" in a section whose content did not extract.

> The corpus does not define **business impact analysis** or explain the **5 Whys** in a risk
> context. [S023] covers 5 Whys as a brainstorming technique — see
> [../08-ideation/brainstorming.md](../08-ideation/brainstorming.md).

## Limitations

- **Exam-prep framing** and no primary PMBOK source (see [risk-management.md](risk-management.md)).
- **The Total Project Risk average is presented uncritically** (see caution above).
- **Quantitative techniques are named, not taught.** Expected monetary value and Monte Carlo
  analysis appear as terms only.
- **No scales given.** The corpus never specifies what a 1–5 probability or impact scale should
  mean, which is where most real-world inconsistency arises.
- **No treatment of risk interdependence** — correlated risks, or risks whose occurrence changes
  the probability of others.
- The worked example is a municipal-hazard case, not a software one. The method transfers; the
  data sources do not.

## Related concepts

- [risk-management.md](risk-management.md)
- [risk-identification.md](risk-identification.md)
- [risk-response.md](risk-response.md)
- [risk-monitoring.md](risk-monitoring.md)
- [it-and-security-risk.md](it-and-security-risk.md)
- [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md) — probability × consequence applied to decisions
- [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md) — the risk/evidence grid

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S051 | Project Management Academy (Megan Bell) — *Introduction to Risk Assessment in Project Management* | PMI Authorized Training Partner | Definition, matrix structure, PI and Total Project Risk, data quality, worked example, inputs/outputs, seven steps |
| S100 | Project Management Academy (Erin Aldridge) — *Risk Identification in Project Management* | PMI ATP | Qualitative vs quantitative analysis, purpose of the matrix, data quality assessment |
| S016 | Mitti (by SafetyCulture) — *Risk Analysis: A Comprehensive Guide* | Vendor topic guide | Additional analysis methods (named only) |
