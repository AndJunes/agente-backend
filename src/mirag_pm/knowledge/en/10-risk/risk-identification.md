---
title: Risk Identification
domain: risk
type: process
topics:
  - risk identification
  - risk register
  - SWOT
  - Delphi technique
  - assumptions analysis
  - root cause analysis
  - barriers to identification
source_count: 3
sources: [S100, S125, S051]
evidence_type: standards-aligned
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Risk Identification

## Purpose and timing

[S100]: "The Identify Risk process is used to **pinpoint any potential opportunities and threats
that could affect elements of a project or its deliverables.**"

**When:** "Risk identification is **especially important during the planning process, but it should
continue throughout the life of a project.** New risks or information about existing risks can come
up as you progress... Having a solid process to identify risks during project execution will help
the project team **avoid schedule overruns, budget overruns, and a volatile stakeholder
relationship.**"

## Ten barriers to identifying risks

[S100] attributes this list to PMI. It is the most useful diagnostic content in the corpus's risk
material — **each barrier is a check you can run on your own process.**

| # | Barrier | [S100] |
|---|---|---|
| 1 | **Identification quality** | "How precise, accurate, applicable, or relevant is the risk you identified?" |
| 2 | **Imagination** | "**What limits your project team's ability to think of all plausible risks?**" |
| 3 | **Inadequate planning approach** | "If your planning approach is not well or fully developed, you may not be able to identify the proper risk areas" |
| 4 | **Lack of knowledge** | "If you and your project team lack or can't access sufficient project, technical, or subject matter expertise... you are likely to struggle" |
| 5 | **Lack of management support** | "**Is your risk identification activity supported from the top down?** Any resistance or lack of support can impede identifying risks" |
| 6 | **Level of detail** | "It can be challenging to determine how detailed your risk exploration and documentation should be. **Too little detail may cause you to overlook some critical risks**" |
| 7 | **One observation** | "**Limiting yourself to a single risk identification activity severely limits the potential risks you can identify**" |
| 8 | **Risk attitude** | "Your project team being **too reckless or too risk-averse** can affect the quality of your risk identification activities" |
| 9 | **Time and cost constraints** | "If you are limited on time or budget, you may not be able to conduct sufficient risk identification activities" |
| 10 | **Too many assumptions** | "You may find yourself making project decisions based on assumptions. **Making too many assumptions complicates your risk analysis and identification activities**" |

> Barriers 2, 7 and 8 are about the *people doing the identifying*, not the project. They are the
> reason risk identification benefits from multiple sessions, diverse participants, and anonymity
> (see the Delphi technique below).

## The risk identification lifecycle

[S100] describes six stages "to ensure you collect consistent and comprehensive information about
every project risk":

### 1. Template specification
"Start by defining **a standard template for your risk statement.** Your risk statement should
include specific information such as the potential event or condition, its consequences, and more."

PMI's example, via [S100]:
> **"Because of [cause], [event] could occur during [time window], which could lead to [impact]
> with an [effect on project objective]."**

### 2. Basic identification
Two questions [S100]:
- "**Why might this risk happen to this project or not?**"
- "**What similar lessons from the past could apply here?**"

"Analyzing your project or organization's strengths, weaknesses, opportunities, and threats can
help you identify '**obvious**' internal or external factors."

### 3. Detailed identification
"Expand your understanding of each risk and identify additional risks... This step will give you a
richer list of '**less obvious**' risks to consider."

### 4. External cross-check
"Once your internal project team has come up with as many potential project risks as possible,
**expand your understanding of project risks beyond the internal team's knowledge and ideas by
leveraging the experience of others.**"

### 5. Internal cross-check
"Check the list **against your scope using your Work Breakdown Structure (WBS).** Take some time to
validate that **each risk corresponds to an element of your WBS and that you have considered each
WBS element from a risk identification standpoint.**"

> This is a genuinely rigorous completeness check — traverse the work breakdown and ask, for each
> element, what could go wrong. It catches the omission that brainstorming misses. *(Note: WBS
> itself is not covered in the corpus — see
> [../06-requirements/epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md)
> for the gap.)*

### 6. Statement finalization
"Check your final list of risks to fill in any missing information in your risk statements to
ensure they are as informative and thorough as possible."

## Tools and techniques

### Documentation review and analysis
[S100]: "**Missing, inaccurate, or incomplete information will make it more challenging for you to
identify and track risks.**" Documents to review:
- "Checklist analysis using risk lists and categories from current or past **risk breakdown
  structures**"
- "**Lessons or analogies from past projects**"
- "Articles, checklists, category lists, or other resources created by industry experts"
- "Organizational process assets"

### Diagramming and root cause analysis
[S100]: "**Influence diagrams, flow charts, and fishbone diagrams** can all help you understand how
internal and external project factors can **contribute or lead to risk events.** ... they can break
complex information down to be more easily understood."

[S016] independently names the **5 Whys** as a risk analysis method. See
[risk-assessment.md](risk-assessment.md).

### SWOT analysis
[S100] defines the four quadrants for risk purposes:
- **Strengths:** "advantages or things your project or organization does well"
- **Weaknesses:** "vulnerabilities or things your project or organization could improve"
- **Opportunities:** "**favorable external factors that you could take advantage of**"
- **Threats:** "potentially harmful factors that pose a hazard"

Method: "Start with a square split into four quadrants. Assign one element to each quadrant, then
**plot each risk in your list in the relevant quadrant.** Using SWOT analysis equips you to **stay
aware of threats and weaknesses while leveraging strengths and opportunities.**"

> Note that SWOT here covers **both** negative and positive risk, consistent with the PMI
> definition.

### Information-gathering techniques
[S100]:

| Technique | Description |
|---|---|
| **Brainstorming** | "Encourage your project team to think together in a **verbal, partly written, or nominal group** brainstorm" |
| **Delphi technique** | "**Consult a group of experts anonymously** by sending them a list of relevant information, compiling their responses, and sending results back for further review" |
| **Expert or stakeholder interviews** | "Allocate time and resources to developing relevant questions and holding more formal conversations" |

> The **Delphi technique** is the corpus's only anonymity-preserving method, and it directly
> addresses barrier 8 (risk attitude) and the seniority-deference problem [S031] names in
> [../05-planning/prioritization.md](../05-planning/prioritization.md). For the mechanics of
> written and nominal-group ideation, see
> [../08-ideation/brainwriting.md](../08-ideation/brainwriting.md).

[S125] gives a compatible, shorter list: "Interviews · Brainstorming · Checklists · Assumption
analysis · Cause and effect diagrams · **Nominal Group Technique (NGT)** · Affinity diagram" — and
recommends combining them: "project managers could use a combination of such methods, like
**reviewing a checklist in one of their regular meetings and going over assumptions in
another.**"

### Assumptions analysis
[S100] singles this out:

> "One obstacle to assumptions analysis is **trying to identify and analyze unconscious
> assumptions.** However, **whether your assumptions are conscious or unconscious, every
> assumption has the potential to be wrong or inaccurate.**
>
> Investing some effort in assumptions analysis is a useful way to determine if your assumptions
> are valid and avoid some potentially significant project risks as a result. **Challenge your
> assumptions and analyze any potential risks they could cause.**"

> This is the direct bridge between project risk management and product discovery. The
> assumption-mapping workshops in
> [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)
> are the same activity performed on product bets rather than project delivery.

## Inputs

[S100] gives an extensive checklist. Condensed:

**From the project management plan:** the risk management plan; **scope and schedule baseline**;
cost, schedule and quality management plans; **human resource management plan** — "people tend to
be unpredictable, so your use of human resources can be a significant source of risks."

**Project documents:** activity cost estimates; activity duration estimates; procurement documents;
stakeholder register; project charter; network diagram; **assumption log**; **issue log**;
performance reports; earned value reports; resource requirements.

**Enterprise environmental factors (EEFs):** "relevant laws, regulations, and policies; operational
environment information; industry or market research; performance benchmarks; studies, white
papers, and other research; **risk attitudes.**"

**Organizational process assets (OPAs):** "established guidelines, policies, or procedures for risk
management; past polls of relevant audiences; historical information or databases published by
other professionals; **lessons learned from previous similar projects; risk registers from past
projects.**"

> The last two — *lessons learned* and *past risk registers* — are the cheapest high-yield inputs
> available, and the most commonly skipped.

## Output

[S100]: "The primary output of risk identification is **the risk register**, a document compiling
all known project risks and other relevant information about them... **This document can be used to
drive the remaining risk processes:** Perform Qualitative Risk Analysis, Perform Quantitative Risk
Analysis, Plan Responses, and Monitor & Control Risks."

## Limitations

- **Exam-preparation framing.** [S100] is written for PMP candidates; it is faithful to PMI
  vocabulary but assumes a formal project-management context with a WBS, charter and baselines —
  artefacts most software product teams do not maintain.
- **PMBOK itself is not in the corpus.** All PMI definitions and lists are second-hand.
- **No guidance on how many risks is enough**, or on when identification has reached diminishing
  returns.
- **Risk breakdown structures** are named but not explained.
- **No agile adaptation** — how risk identification works in a team with no project manager, no
  WBS, and a two-week horizon.

## Related concepts

- [risk-management.md](risk-management.md)
- [risk-assessment.md](risk-assessment.md)
- [risk-response.md](risk-response.md)
- [product-risk.md](product-risk.md)
- [assumptions-and-constraints.md](assumptions-and-constraints.md)
- [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)
- [../08-ideation/brainstorming.md](../08-ideation/brainstorming.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S100 | Project Management Academy (Erin Aldridge) — *Risk Identification in Project Management* | PMI Authorized Training Partner | Ten barriers, six-stage lifecycle, tools and techniques, inputs, outputs |
| S125 | Mitti (by SafetyCulture) — *Understanding Project Risk Management* | Vendor topic guide | Identification technique list, combining methods |
| S051 | Project Management Academy — *Introduction to Risk Assessment* | PMI ATP | Identification as precondition for assessment |
