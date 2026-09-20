---
title: What the Evidence Says About AI-Assisted Software Delivery
domain: ai-agent-collaboration
type: evidence-review
topics:
  - AI productivity evidence
  - METR study
  - DORA report
  - developer productivity
  - perception gap
  - delivery instability
  - verification tax
  - J-curve
  - AI as amplifier
  - user-centric focus
synonyms:
  - does AI make developers faster
  - AI coding productivity research
  - empirical evidence AI agents
source_count: 5
sources: [E006, E007, E008, E009, E010]
evidence_type: empirical-study
confidence: medium
corpus_origin: false
external_research: true
verified: true
phase: 2
provenance:
  primary: [E006, E008]
  interpretation: [E010]
  practice: []
  empirical: [E006, E007, E008]
last_reviewed: 2026-09-16
---

# What the Evidence Says About AI-Assisted Software Delivery

> **Read this document before the other three in this domain.** Everything else here —
> specification practice, evaluation, the changing shape of the PM's job — is downstream of what is
> actually measured. This document separates **what has been measured** from **what is asserted**,
> and says plainly where the evidence runs out.
>
> **Confidence is `medium`, not `high`, and deliberately so.** The field is young, the studies are
> few, the largest dataset is self-reported and vendor-run, and the most rigorous experiment has
> been partially withdrawn by its own authors as a guide to current systems.

## The headline: there is very little rigorous evidence, and it does not say what most people say it says

| Question | State of the evidence |
|---|---|
| **Do AI tools make individual developers faster?** | **Genuinely unresolved.** One RCT [E006] measured a *slowdown*; survey data [E008] reports large perceived speedups; the RCT's authors now believe the picture has changed [E007] but say their own newer data is "only very weak evidence" |
| **Do developers know whether AI made them faster?** | **No — and this is the best-supported finding in the literature** [E006] |
| **Does AI adoption improve organisational software delivery?** | **Partially.** [E008] finds throughput improved in 2025 (a change from 2024) **but delivery instability also increased** |
| **Does AI adoption pay for itself?** | **Asserted, not demonstrated.** The only ROI figures available are vendor-produced projections [E009] |
| **What determines whether AI helps or hurts?** | The best-supported answer: **the surrounding organisational system, not the tool** [E008] |

## The METR randomized controlled trial (July 2025)

**The only randomized controlled trial of AI tooling on real work in real repositories.**
[E006] Becker, Rush, Barnes & Rein (METR), *Measuring the Impact of Early-2025 AI on Experienced
Open-Source Developer Productivity*.

### Design
- **16 developers**, **246 real tasks** (bug fixes, features, refactors) averaging **2.0 hours**
- Tasks came from the developers' **own mature repositories** — averaging **23,000 stars**,
  **~10 years old**, **>1,100,000 lines of code**
- Developers averaged **5 years and ~1,500 commits** on those repositories
- **Tasks were defined before randomization**, then each randomly assigned to allow or disallow AI.
  [E006] notes this is *"crucially"* important: it prevents AI-driven scope inflation from
  contaminating the outcome measure
- AI condition: any tools, primarily **Cursor Pro with Claude 3.5/3.7 Sonnet** — frontier at the
  time (February–June 2025)
- **143 hours of screen recordings** manually labelled at ~10-second resolution

### The result

> **"Surprisingly, we find that allowing AI actually increases completion time by 19%—AI tooling
> slowed developers down."** [E006]

### The perception gap — the study's most robust and most transferable finding

| Who | Predicted / reported |
|---|---|
| Developers, **before** the study | AI will reduce completion time by **24%** |
| Developers, **after** experiencing the 19% slowdown | AI reduced completion time by **20%** |
| **34 economics experts** | **39%** reduction |
| **54 machine-learning experts** | **38%** reduction |
| **Measured** | **19% *increase*** |

Developers' estimates were not generally unreliable: [E006] reports Pearson correlations of **0.64**
and **0.59** between forecast and actual times. The conclusion is precise and narrow:

> *"developers are broadly well-calibrated on the relative amount of time that issues will take, but
> their expectations regarding the usefulness of AI assistance are reversed."* [E006]

> **This is the finding a PM should carry forward.** Not "AI is slow" — but **"self-report is not a
> measurement."** A team that says AI made them faster has told you how the work *felt*, and the one
> study that checked found feeling and fact pointing in opposite directions. See
> [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md).

### Where the time actually went
From the labelled recordings, when AI was allowed developers spent **less** time actively coding and
reading/searching for information, and **more** time **prompting, waiting for generations, reviewing
AI output, and idle**. Specific figures [E006]: **~9%** of time reviewing and cleaning AI outputs;
**~4%** waiting on generations.

### The five factors METR found evidence for
Of **20** hypothesised factors, [E006] found supporting evidence for five:

| Factor | Evidence cited |
|---|---|
| **Over-optimism about AI usefulness** | The 24% / 20% forecasts above |
| **High developer familiarity with repositories** | Developers **slowed down more on issues they were more familiar with** |
| **Large and complex repositories** | ~10 years old, >1.1M lines |
| **Low AI reliability** | **Developers accepted under 44% of AI generations**; a majority reported making major changes to clean up AI code |
| **Implicit repository context** | Developers reported AI *"doesn't utilize important tacit knowledge or context"* |

Nine factors had unclear effects; six had evidence **against** — including the possibility that the
result was an artifact of unfamiliar tooling (developers using comparable IDEs still saw **24%**
slowdown) or of non-frontier models.

### What METR explicitly says its study does NOT show
[E006] publishes a table of misreadings to forestall. It does **not** provide evidence that:

- *"AI systems do not currently speed up many or most software developers"* — the 16 developers and
  their repositories are not claimed to represent most software work
- AI does not speed up work **outside software development** — *"We only study software development"*
- AI **in the near future** will not speed up developers in this same setting
- There are **no better ways of using existing systems** to achieve speedup — [E006] notes Cursor
  *"does not sample many tokens from LLMs"* and that better prompting, scaffolding or
  domain-specific fine-tuning could yield positive results

> ⚠ **The most common misuse of this study is to cite "19% slower" as a general fact about AI and
> programming.** Its authors say in the paper that this is not what they showed. An agent using this
> knowledge base must reproduce the scope conditions — **experienced maintainers, their own mature
> large codebases, early-2025 tooling** — whenever it cites the number.

### METR's own February 2026 update — read this before citing the 19%
[E007], *We are Changing our Developer Productivity Experiment Design*, 24 February 2026:

> **"Based on conversations with study participants, we believe it is likely that developers are more
> sped up from AI tools now — in early 2026 — compared to our estimates from early 2025."** [E007]
>
> **"However, because of the selection effects in our experiment, our data is only very weak evidence
> for the size of this increase."** [E007]

METR is redesigning the experiment because wider adoption has broken the method: developers
increasingly decline tasks they would not do without AI, so the sample systematically excludes the
people for whom AI helps most.

> **Provenance summary for the 19% figure.**
> **[EMPIRICAL — valid for its stated setting and period (February–June 2025 tooling).]**
> **[SUPERSEDED as a description of current tools, by the original authors.]**
> **[NOT REPLACED — no equally rigorous measurement of current tooling exists.]**
>
> This is exactly the case the corpus philosophy was written for: the finding is not deleted, not
> promoted to timeless truth, and not quietly updated to whatever is convenient.

## DORA, *State of AI-assisted Software Development* (2025)

[E008] Google Cloud / DORA. **Nearly 5,000 survey respondents** worldwide plus **100+ hours of
qualitative data**; survey fielded **13 June – 21 July 2025**.

### Central claim

> **"AI's primary role in software development is that of an amplifier. It magnifies the strengths of
> high-performing organizations and the dysfunctions of struggling ones."** [E008]

And:

> **"The greatest returns on AI investment come not from the tools themselves, but from a strategic
> focus on the underlying organizational system: the quality of the internal platform, the clarity of
> workflows, and the alignment of teams. Without this foundation, AI creates localized pockets of
> productivity that are often lost to downstream chaos."** [E008]

### Adoption and trust
- **90%** of respondents use AI as part of their work
- **more than 80%** believe it has increased their productivity
- **30% report little to no trust in AI-generated code**

[E008] reads the third number positively — a *"trust but verify"* posture it calls *"a sign of mature
adoption"* — and recommends training that teaches teams *"how to critically guide, evaluate, and
validate AI-generated work, rather than simply encouraging usage."*

> Note the tension between the second and third bullets, and between both and [E006]: **80%+ believe
> they are more productive**, while the only controlled measurement of that belief found it inverted.
> [E008] measures *belief*; [E006] measured *time*. **They are not contradictory findings — they are
> different quantities**, and treating perceived productivity as measured productivity is the error.

### Throughput and instability

> **"AI adoption now improves software delivery throughput, a key shift from last year. However, it
> still increases delivery instability. This suggests that while teams are adapting for speed, their
> underlying systems have not yet evolved to safely manage AI-accelerated development."** [E008]

[E008]'s estimated effects (standardized, with 89% credible intervals) are **positive for individual
effectiveness** — the largest effect — and positive but smaller for throughput, code quality, product
performance and team performance; **positive for software delivery instability, which is undesirable**.

> **The implication for a PM is direct and uncomfortable.** The largest measured benefit accrues to
> **the individual developer's sense of effectiveness**; the effects on **product performance** are
> smaller; and **instability rises**. A PM who justifies AI adoption on delivery outcomes is
> promising the smallest of the measured effects.

### The DORA AI Capabilities Model — seven capabilities that amplify AI's benefit
Derived from 78 interviews and 15 candidate capabilities, of which seven showed substantial
interaction with AI use [E008]:

1. **Clear and communicated AI stance**
2. **Healthy data ecosystems**
3. **AI-accessible internal data**
4. **Strong version control practices**
5. **Working in small batches**
6. **User-centric focus**
7. **Quality internal platforms**

**Two of these are product-management levers**, and they are the two with the most pointed findings.

#### Working in small batches
Defined by lines of code per change, changes per release, and how long a single assigned task takes.
[E008] found, *"with a high degree of certainty"*, that when teams work in small batches:

- **AI's positive influence on product performance is amplified**, and
- **AI's neutral effect on friction becomes beneficial** — friction decreases.

**But**: AI's benefit to *individual effectiveness* is **slightly reduced** in small-batch teams.
[E008]'s explanation is that AI mainly raises perceived individual effectiveness *"by helping
developers to quickly generate a large amount of code"* — which small batches constrain. Its
judgement: *"individual effectiveness should not necessarily be pursued as a goal in and of itself."*

#### User-centric focus
Measured by agreement that creating value for users is the team's focus, that user experience is the
top priority, and that focusing on the user is key to business success.

> **"Without a user-centric focus, AI adoption is unlikely to help teams. It may even harm them."**
> [E008]
>
> **"In the absence of a user-centric focus, AI adoption has a negative impact on team performance."**
> [E008]

> **This is the strongest empirically-grounded statement available on why the product-management
> function matters more, not less, when implementation is accelerated** — and it comes from survey
> data, not from a product-management vendor. It is a **moderation** finding: user-centric focus does
> not merely add to AI's benefit, it determines its **sign**.
>
> **Caveat that must travel with it:** [E008] is **cross-sectional self-report**. Teams that describe
> themselves as user-centric may differ from others in many unmeasured ways. **This is correlational
> evidence of a moderating relationship, not a demonstrated causal mechanism.**

## DORA, *ROI of AI-assisted Software Development* (2026)

[E009], published **2026**; reported and summarised in [E010] (InfoQ, 11 May 2026). **The full report
was not retrieved; the findings below come from the secondary summary and are marked accordingly.**

### The J-curve
The report describes a **temporary productivity dip** before gains materialise, attributed to three
causes [E010]:

1. teams adapting their workflows,
2. **verification overhead from reviewing AI-generated code** — the *"verification tax"*,
3. adjustments to testing and approval processes.

[E010] reports the authors calling this period **"the tuition cost of transformation."** The shape
described is foundation-building in year one, with compounding returns in years two and three as
teams move from coding assistants to autonomous agent workflows.

> The J-curve is **consistent with** [E006]'s slowdown and [E008]'s instability finding, and it is a
> plausible reconciliation of them. **It is not thereby demonstrated.** A U-shaped adoption curve is
> also the shape that a vendor whose product has not yet delivered returns would most want to be
> true. Treat it as a **hypothesis with converging circumstantial support**, not a measured result.

### The ROI figures — do not cite these as evidence
[E010] reports a modelled 500-person engineering organisation yielding roughly **$11.6M first-year
value against $8.4M investment (39% ROI, eight-month payback)**, and an average **727% return over
three years** from Google Cloud data.

> ⚠ **`UNVERIFIED — VENDOR PROJECTION.`** These are **modelled projections published by a company
> that sells AI development tooling and cloud services**, reaching me through a secondary source.
> The 727% figure is described as "Google Cloud data" with no methodology available here. **An agent
> using this knowledge base must not present these as evidence that AI adoption pays off.** They are
> recorded because the corpus rule is to preserve claims with their provenance attached, not to
> delete inconvenient ones. See
> [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

One qualitative point from [E010] is worth keeping regardless: the report **discourages headcount
reduction**, arguing retention and training are more cost-effective, and frames the return as
clearing bottlenecks rather than producing code — *"We don't measure AI by the code it writes but by
the bottlenecks it clears."*

## What no source here establishes

Stated explicitly, because this is where an agent is most likely to fill a gap from memory:

- **Nothing here measures autonomous coding agents.** [E006] studied a developer using an AI-assisted
  editor. [E008] surveyed AI *use*, mostly assistive. **The setting this knowledge base exists to
  serve — an agent as the implementer, with a PM directing it — has no rigorous empirical study in
  this document at all.** [E010] mentions agent workflows only as a projected future phase.
- **No evidence on defect rates, maintainability or long-run cost** of AI-written code.
- **No evidence on how PM practice itself changes.** Every claim about that in
  [pm-with-ai-implementers.md](pm-with-ai-implementers.md) is **practice or assertion, not measurement.**
- **No evidence comparing specification approaches** (see
  [spec-driven-development.md](spec-driven-development.md)). Adoption is not evidence of efficacy.
- **No evidence on team size, composition or role changes.**

## Limitations

- **Two of the five sources are published by Google** ([E008], [E009]), which sells AI development
  tooling, and are self-report surveys rather than experiments. [E008] is methodologically careful and
  publishes credible intervals; it remains **correlational, cross-sectional, self-reported** data with
  a commercial interest behind it.
- **[E006] is a genuine RCT but small** — 16 developers, one kind of setting — and its authors have
  qualified its currency [E007].
- **[E009] was not read in the original.** [E010] is a technology-news secondary source. Nothing
  attributed to [E009] in this document should be quoted as the report's own words.
- **Publication and citation bias are unquantified** in a field where nearly all measurement is
  performed by parties selling the technology.
- **The field moves faster than the evidence.** Every number here has a date attached. Check it.
- **No non-English or non-Western sources** were consulted.

## Related concepts

- [pm-with-ai-implementers.md](pm-with-ai-implementers.md) — what this evidence does and does not imply for the role
- [spec-driven-development.md](spec-driven-development.md)
- [evals-and-acceptance-for-agents.md](evals-and-acceptance-for-agents.md)
- [open-questions-ai-and-pm.md](open-questions-ai-and-pm.md)
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md) — perceived vs measured
- [../05-planning/estimation.md](../05-planning/estimation.md) — the forecasting-calibration result
- [../07-execution/kanban.md](../07-execution/kanban.md) — batch size and flow
- [../99-reference/disputed-information.md](../99-reference/disputed-information.md)

## Sources

| ID | Source | Type | Provenance | Reliability |
|---|---|---|---|---|
| E006 | Becker, J., Rush, N., Barnes, B. & Rein, D. (METR) — *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*, 10 July 2025 | **Randomized controlled trial** | `EMPIRICAL` | **A** — preregistered-style RCT, full paper and factor analysis published; small N, narrow setting |
| E007 | METR — *We are Changing our Developer Productivity Experiment Design*, 24 February 2026 | Author's own update | `EMPIRICAL / CORRECTION` | **A** — the authors qualifying their own result |
| E008 | Google Cloud / DORA — *State of AI-assisted Software Development*, 2025 (v.2025.2); survey 13 Jun – 21 Jul 2025, n≈5,000 | Large survey + qualitative study | `EMPIRICAL (self-report)` | **B** — methodologically careful, credible intervals published; vendor-run, cross-sectional, self-reported |
| E009 | DORA — *ROI of AI-assisted Software Development*, 2026 | Vendor research report | `VENDOR PROJECTION` | **C** — **not read in original**; ROI figures are modelled, not measured |
| E010 | InfoQ — *New DORA Report Claims Strong Engineering Foundations Drive AI Return on Investment*, 11 May 2026 | Technology news | `SECONDARY` | **C** — sole route to [E009] here |
