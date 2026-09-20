---
title: Prioritization Frameworks
domain: planning
type: framework-catalogue
topics:
  - RICE
  - Kano model
  - MoSCoW
  - value vs effort
  - opportunity scoring
  - cost of delay
  - weighted scoring
  - WSJF
  - prioritization matrix
source_count: 4
sources: [S066, S031, S032, S067]
evidence_type: practitioner-framework
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Prioritization Frameworks

## What a prioritization framework is

[S066]: "A product prioritization framework is a **methodology that helps teams weigh their
opportunities against various constraints**, such as business goals, customer value, product
requirements, and available resources. It provides a set of consistent principles and strategies
that help teams decide what to work on next."

Its stated purpose is to remove "guesswork from the product management decision-making process."

> **Read that claim carefully.** Every framework below converts judgments into numbers. It does
> not remove the judgment — it relocates it into the inputs. [S066] itself concedes this for
> RICE: "Methods for determining each evaluation factor can change, making this method
> subjective, inconsistent, and potentially misleading."

---

## RICE

**What it is** [S066]: four factors used to evaluate a product idea.

| Factor | Definition [S066] |
|---|---|
| **Reach** | "The number of people or events over time, such as transactions per quarter or conversions per month" |
| **Impact** | "Whether an idea achieves business goals or meets customer needs" |
| **Confidence** | "The team's confidence level in executing ideas with a percentage scale of **high (100%), medium (80%), and low (50%)**" |
| **Effort** | "The time it will take the team to execute the idea" |

**Calculation** [S031]: "scoring each on Reach, Impact, Confidence, and development effort, then
**dividing the product of the first three by the fourth.**"

**Attribution** [S031]: "**Intercom designed RICE** to compare project ideas using explicit
assumptions."

**Strengths** [S066]: "enables product managers to gauge whether items are feasible. Data
gathered from this calculation helps **justify decisions to stakeholders.**"

**Weaknesses** [S066]: "can be **time-consuming and cumbersome** to apply, particularly if
multiple items require data and validation from multiple sources. Methods for determining each
evaluation factor can change, making this method **subjective, inconsistent, and potentially
misleading.**"

### A specific correction: eligible reach
[S031] identifies a failure mode worth taking seriously:

> "Where RICE quietly breaks is **'reach.' Most teams plug in their total user base, which is
> usually wrong. The right input is *eligible reach*: the number of users who can actually use
> the feature given their plan, role, integration, and onboarding status.**
>
> A feature usable by 100% of users on a paid integration, inside a product where only 12% of
> users have that integration, has **12% eligible reach, not 100%.** Plug the wrong number in and
> the RICE framework ranks the feature roughly **8x too high.**"

**When to use RICE** [S031]: "RICE is good at '**of these comparable items, which goes first?**'
and bad at '**of these very different bets, which deserves capacity?**' Use it **inside a chosen
area, not across the whole roadmap.**"

---

## Value vs Effort matrix

**What it is** [S066]: "prioritizes features based on their probable value and the effort
necessary to implement them. A 2x2 matrix, measuring value on one axis and effort on the other."

**How to read the quadrants.** The two sources label them differently; both are in use:

| Quadrant | [S066] label | [S031] label |
|---|---|---|
| High value, low effort | "**Do first** — a guaranteed quick win" | "**Quick wins** — ship these first" |
| High value, high effort | "**Do second**" | "**Major projects** — plan, sequence, fund them properly" |
| Low value, low effort | "**Do last** — best to wait until the value increases" | "**Fill-ins** — address only if time allows" |
| Low value, high effort | "**Avoid** — not worth your team's time" | "**Thankless tasks** — drop or repackage them" |

**Defining the axes** [S066]: "To determine value, consider how it affects users and impacts the
bottom line. **Effort is the complexity of implementation.**"

**Strengths** [S066]: "no complicated calculations, which makes decisions easier... Because it's
visual, the team can quickly see which tasks bring high value for the lowest effort."

**Weaknesses** [S066]: "Values can be **imprecise** with this method, which primarily uses
instinct. The same goes for estimates, where a team might think they have more resources than
they do. Another drawback is **effort-sizing, which will vary from team to team.** That makes
planning more difficult with cross-functional teams that have different resources."

### A proposed correction
[S031] argues both axes hide costs: "'Effort' in an AI feature isn't just build cost; it includes
**evals, monitoring, run cost, support burden, rollback complexity, and compliance review.**"
Its fix: "Rename the horizontal axis to '**total cost to deliver and learn**' and the vertical
axis to '**expected outcome lift for the eligible user segment.**' That single rename changes
which features land in the quick wins quadrant."

---

## MoSCoW

**What it is** [S066]: "a four-step process for prioritizing product requirements around their
return on investment."

| Bucket | Definition [S066] |
|---|---|
| **Must have (M)** | "The requirements needed for the project's success" |
| **Should have (S)** | "Important requirements for the project but **not necessary**" |
| **Could have (C)** | "'Nice to have.' But don't have as much impact as the others" |
| **Won't have (W)** | "These requirements aren't a priority for the project" |

**Attribution** [S031]: "developed by **DSDM Consortium**."

**Strengths** [S066]: "easy to implement and practice. Project managers can use it to help
**resolve disputes with stakeholders.**"

**Weaknesses** [S066]: "The **lack of clarity in the 'will not have' requirements** is a flaw...
especially around whether they should be part of the backlog. **Criteria for a 'must have' or a
'should have' can also be hard to determine.** If there is no consensus among stakeholders, then
prioritization becomes ineffective and subjective."

### The guardrail almost everyone ignores
[S031] surfaces a rule attributed to the framework's originators:

> "**DSDM is explicit about a guardrail that almost everyone ignores: Must-have items should
> consume no more than roughly 60% of effort, with a healthy pool (often around 20%) reserved
> for Could-haves as delivery contingency.**
>
> Most teams I see inflate Musts to 90%+ and lose all contingency. When the inevitable surprise
> lands mid-sprint, the only thing left to cut is something already labeled mission-critical,
> which is **how the prioritization process eats itself.**"

> This is the single most actionable correction in the corpus's prioritization material. It is
> **UNVERIFIED against DSDM's own documentation**, which is not in the corpus — but it is a
> specific, falsifiable claim about a named source, which makes it worth checking rather than
> discarding. See [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

**Scope of applicability** [S031]: MoSCoW "is **strongest as a release-planning tool and weakest
as a portfolio-ranking tool. Use it after you've already decided what to work on, not to decide
what to work on.**"

---

## Kano model

**What it is** [S066]: "a customer satisfaction-based prioritization framework." Attributed to
"Researcher **Noraki Kano**" *(the standard spelling is Noriaki Kano; the corpus's spelling is
reproduced here with this correction noted)*.

| Category | Definition [S066] | Example [S066] |
|---|---|---|
| **Basic features** | "Customers **expect** these essential functions" | "The ability to share a post on a social network" |
| **Performance features** | "Increase customer satisfaction and make your product more enjoyable to use" | "Faster load times" |
| **Delighters** | "**Unexpected** features [that] make customers happy" | "Whimsical in-app messaging or the ability to use GIFs in posts" |

[S031] adds the scaling behaviour: performance features are "satisfiers that scale linearly with
quality"; basics are "table stakes, get them right or the product is broken."

**Strengths** [S066]: "prevents a team from building features that won't appeal to customers. It
also identifies areas where the product may need improvement."
[S031]: "Used well, **Kano stops you from over-investing in delight at the expense of
reliability.**"

**Weaknesses** [S066]: "highly quantitative and potentially time-consuming, requiring heavy data
research and analysis. It can also be a **very manual process with the use of surveys.**"

### A re-categorization argument for AI products
[S031]: "**reliability, controllability, privacy, and explainability are basic features now, not
delighters.** Treat them as table stakes. Score richer generation, autonomy, or multi-step
reasoning as performance features or delight **only after the basics are fully funded.**"

Its reasoning: "This re-categorization is what stops product teams from shipping a GenAI feature
with an impressive demo and a 20% hallucination rate. **A pretty demo wins the launch
presentation, but a hallucination loses the renewal conversation.**"

> **Note the general principle underneath, which outlives any AI framing:** Kano categories are
> **not fixed properties of a feature.** They move over time and by market as expectations rise.
> A delighter becomes a performance feature becomes a basic. Treating a Kano classification as
> permanent is a misuse of the model.

---

## Opportunity scoring

**What it is** [S066]: "identifies features that are important to customers but underperform.
Customers rate both a feature's importance and their satisfaction."

**Attribution** [S031]: "developed by **Anthony Ulwick**."

**The formula.** [S066] gives it in two forms, which is a problem:

> "This equation goes beyond normal gap analysis, giving **twice as much weight to importance
> scores as satisfaction scores.**
>
> Here's the weighted equation: `Importance + Max(Importance - Satisfaction, 0) = Opportunity`
>
> Here is the opportunity algorithm formula, where customers use a 1-to-10 to quantify the
> importance and satisfaction of an outcome: `Importance + (Importance - Satisfaction) = Opportunity`"

> **Discrepancy flagged.** These are not the same formula. The first floors the gap at zero (a
> feature people are *more* satisfied with than they consider important contributes nothing
> extra); the second allows a negative contribution. [S066] presents both without acknowledging
> the difference. **The first form is the one consistent with the stated intent** ("high
> importance combined with low satisfaction marks the highest-priority opportunity"), but this is
> an inference. Verify against Ulwick's own work before relying on either. Recorded in
> [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

**Interpretation** [S066]: "Features with **high importance but low satisfaction** are an
opportunity for improvement."

**Strengths** [S031]: "the most **customer-centric** of the classic frameworks... it forces you
to triangulate user feedback against **revealed dissatisfaction**, not just feature requests.
Customer requests alone are notoriously incomplete because **users ask for what they can name.
Opportunity scoring surfaces what's quietly broken but unnamed.**"

**Weaknesses** [S066]: "Scoring models aren't perfect... they only provide a **limited view** of
each idea's scope. Scoring can be **rigid**, especially when quantifying an abstract concept. But
mostly, **scoring can't forecast how the market will respond** to any changes in the product."

[S031] adds a precondition: "you need **meaningful response volume** to make the math work... If
you're piecing answers together from sales calls and CS Slack threads, **you're not running
Opportunity Scoring; you're running anecdote-scoring with a numbered scale on top.**"

---

## Cost of Delay

**What it is** [S066]: "prioritizes projects based on their **economic value**. This method
determines the ongoing costs that result from postponing items on the backlog."

**How to calculate** [S066]:
1. "Estimate a new project's ROI in revenue per unit of time (monthly recurring revenue, for
   example)."
2. "Estimate the time it will take to implement the project."
3. "Divide the profit number by the time estimate."

"The final number is **the cost to the company for not pursuing the project.**"

**Strengths** [S066]: "results in more accurate value and cost estimates... **it doesn't focus on
negative reasons for postponement.** Knowing what has better ROI also eases the burden of
resource allocation."

**Weaknesses** [S066]: "If a project manager underestimates the project size, the calculations
could be inaccurate. **Estimated time requirements may be incorrect as well.**"

> **Note on WSJF.** Weighted Shortest Job First — the SAFe prioritization method built on cost of
> delay — **does not appear anywhere in the corpus**, despite being one of the most widely used
> frameworks in scaled agile environments. [S066]'s cost-of-delay description is structurally
> related but is not WSJF. **Recorded as a gap.**

---

## Weighted scoring

Named by [S031] as its recommended primary method for portfolio decisions: "in practice it's the
most flexible because **the criteria are adaptable to your product stage.**"

[S031] proposes a 15-criterion template organised into three buckets, where **Benefits and Costs
are weighted and scored, while Gates are non-negotiable preconditions** — "a failed gate kills
the item regardless of its score."

| Bucket | Criterion | What to capture | Weight |
|---|---|---|---|
| Metadata | Outcome | The business or product outcome this item is meant to move | — |
| Metadata | Primary user stream | Human, agent, or both | — |
| Metadata | Target segment / eligibility | "Who can realistically use it now; **define the denominator precisely**" | — |
| Benefit | Problem severity | "How acute and frequent is the job or pain?" | 12 |
| Benefit | Eligible reach / task volume | "Eligible human users or eligible agent task volume, **not total user base**" | 10 |
| Benefit | Expected outcome lift | "Retention, activation, conversion, revenue, cost, or task-success improvement" | 15 |
| Benefit | Strategic differentiation | "Table stakes, parity, or true differentiator" | 8 |
| Benefit | Value-capture probability | "Likelihood the value translates into revenue, retention, or defensibility" | 8 |
| Benefit | Discoverability / adoption readiness | "How likely people or agents are to find and successfully use it without heavy friction" | 10 |
| Cost | Data readiness | "Data quality, access, labels, permissions, and instrumentation readiness" | 8 |
| Cost | Evalability / observability | "Can quality be evaluated, traced, monitored, and rolled back?" | 8 |
| Cost | Ongoing run cost | "Inference, support, moderation, vendor, and maintenance cost" | 7 |
| Cost | Delivery effort | "Build cost to first useful release" | 7 |
| Cost | Reversibility | "Ease of rollback or containment if adoption or quality disappoints" | 7 |
| **Gate** | **Safety / privacy / compliance** | "Regulatory, security, privacy, explainability, or brand risk" | **Hard gate** |
| Metadata | Kill condition | "**When to repackage, pause, or sunset the feature**" | — |

**How to use a score responsibly** [S031]:
- "**The score is a decision aid, not truth**, so run sensitivity checks before treating the
  number as a decision: **does the ranking flip if I change two weights by 10%?**"
- "**Confidence bands matter more than precision**, because a feature scoring 78 with high
  confidence usually beats a feature scoring 82 with weak evidence."
- "The safety, privacy, and compliance gate deserves its own callout. **Treat it as a
  precondition, not a tradeable attribute. If the gate fails, no score gets you out of it.**"

> These three cautions apply to **every** scoring framework on this page, not only to weighted
> scoring.

---

## 4D roadmapping

A fourth approach, from [S067] (Sachin Rekhi, Founder & CEO at Notejoy):

> "Unlike traditional frameworks such as **voting-based or RICE scoring-based prioritization,
> which tend to prioritize low-impact work**, 4D roadmapping provides a structured approach to
> prioritizing needle-moving work by using **four lenses (strategy, vision, customer, and
> business)**. It involves prioritizing at **two levels: the objective level and the initiative
> level**, and then laying out the roadmap."

> **Partial source.** [S067] is member-gated content; only the overview extracted. The four
> lenses and the two-level structure are recorded; **the method itself is not in the corpus.**
> Its critique — that scoring frameworks systematically favour low-impact work — is a serious
> claim that the corpus cannot evaluate. Recorded as a gap.

---

## Choosing a framework

### The simple version
[S066]: "Consider the **project's goals, the complexity of the product, the team's expertise, and
the available data.** For instance, if the project aims to improve customer satisfaction,
opportunity scoring may work well. But if the **team is relatively new** and still building their
skills, value vs. effort might be a better choice."

### The layered version
[S031] argues no single framework survives a real roadmap, and proposes using four in sequence,
each doing a different job:

| Stage | Framework | Job |
|---|---|---|
| **Discovery** | Opportunity Solution Tree | "Start with the business outcome, map the customer opportunities under it, generate three candidate solutions per opportunity, and define assumption tests before you build anything. OSTs keep the team **outcome-led rather than feature-led**" |
| **Portfolio** | Weighted Scoring | Deciding which very different bets deserve capacity |
| **Sequencing** | RICE (with eligible reach) | "Of these comparable items, which goes first?" — **only after** weighted scoring has narrowed the set |
| **Delivery scoping** | MoSCoW (with the 60% Must cap) | "This is the layer where political fights happen... **The 60% rule turns Must-have inflation into a math problem you can point at on a whiteboard**" |

Kano remains "in the toolkit as a **qualitative balance check at the end**: are we over-investing
in delight at the expense of basic features? If yes, re-fund the basics first."

[S031] also mentions **McKinsey's Three Horizons** as a portfolio-balancing layer "if your
prioritization tension is across time horizons rather than across candidates" — allocating
between "immediate needs (Horizon 1), emerging opportunities (Horizon 2), and future-focused bets
(Horizon 3)." *(Three Horizons is named only; not described further in the corpus.)*

## The general steps of applying any framework

[S066]:
1. **Identify tasks** — "based on a few criteria, such as customer value and business needs"
2. **Define criteria** — "these criteria will help you determine which tasks are feasible to
   pursue"
3. **Assign scores**
4. **Rank items** — "order tasks based on urgency and highest impact"

**Review cadence** [S066]: "Your team should review its priorities regularly... You should also
**re-evaluate your prioritization framework if business objectives change. A different framework
might work better than the one you've been using.**"

[S031] argues for a faster cadence: "**Re-rank weekly** — that's build-measure-learn applied to
prioritization — **because the data from the last shipped feature is the best input you have for
the next one.**"

## Limitations of this document

- **Vendor bias throughout.** [S066] is Atlassian promoting Jira Product Discovery and mentions
  it in nearly every framework section; [S031] is Userpilot and its examples are Userpilot
  workflows. Framework descriptions have been retained; tool claims excluded.
- **No primary sources.** Kano's, Ulwick's, Intercom's and DSDM's own documentation are all
  absent. Attributions, formulas and thresholds here are second-hand and should be verified
  before being treated as authoritative — particularly the opportunity-scoring formula
  discrepancy and the MoSCoW 60% rule.
- **WSJF is entirely missing** (see above).
- **No framework is evaluated empirically.** Pros and cons are practitioner judgment.
- **[S031] is a strongly opinionated 2026 source** whose statistics (Pendo's 6.4% feature
  adoption, the 2024 DORA figures, Gartner's 40% agentic-AI cancellation prediction) are
  vendor-reported, time-sensitive, and not independently verifiable from the corpus. They are
  recorded in [../99-reference/outdated-information.md](../99-reference/outdated-information.md)
  and should not be cited as established facts.

## Related concepts

- [prioritization.md](prioritization.md) — the practice, including its failure modes
- [roadmaps.md](roadmaps.md)
- [backlog-management.md](backlog-management.md)
- [estimation.md](estimation.md) — effort inputs
- [../02-discovery/discovery-frameworks.md](../02-discovery/discovery-frameworks.md) — Opportunity Solution Tree
- [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md)
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S066 | Atlassian — *Six product prioritization frameworks and how to pick the right one* | Vendor guide | Definitions, pros/cons and formulas for RICE, Kano, MoSCoW, value vs effort, opportunity scoring, cost of delay; selection guidance; application steps |
| S031 | Userpilot (Abrar Abutouq) — *Feature Prioritization Matrix for Product Teams — Is it Still Valid in 2026?*, updated 31 Aug 2026 | Vendor blog, strongly opinionated practitioner content | Eligible-reach fix, MoSCoW 60% cap, Kano re-categorization, opportunity-scoring precondition, 15-criterion weighted scoring template, layered framework model, scoring cautions |
| S032 | Aha! — *Feature Prioritization: How to Prioritize the Right Features*, updated Feb 2025 | Vendor guide | Prioritization framing |
| S067 | Sachin Rekhi (Notejoy) — *Prioritize your roadmap with 4D roadmapping* | Practitioner content (member-gated; partial extraction) | 4D roadmapping overview and its critique of scoring frameworks |
