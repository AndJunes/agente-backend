---
title: Estimation
domain: planning
type: concept
topics:
  - estimation
  - story points
  - planning poker
  - t-shirt sizing
  - velocity
  - effort
  - forecasting
source_count: 8
sources: [S126, S108, S003, S066, E001, E002, E003, E006]
evidence_type: mixed
confidence: medium
corpus_origin: true
external_research: true
verified: partial
phase: 2
provenance:
  primary: [E001, E002, E003]
  interpretation: [S126]
  practice: [S108, S003]
  empirical: [E006]
last_reviewed: 2026-09-16
---

# Estimation

> ## ⚠ This is a documented gap, not a treatment of the topic
>
> **The corpus contains no source about estimation.** Every reference below is a passing mention
> inside a document about something else. Estimation is a core PM/team activity and a direct
> input to three things this knowledge base covers well — prioritization, roadmapping and
> decomposition — yet the corpus supplies **no method, no technique explanation, and no
> discussion of accuracy or bias.**
>
> This document records what exists and specifies precisely what is missing, so that an agent
> relying on this knowledge base knows not to answer estimation questions from it.
> See [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md) — this was a **priority-1 gap.**
>
> **Phase-2 status: partially closed, and not in the direction expected.** External research did not
> supply the missing story-point and planning-poker material. It supplied something more useful:
> **three primary sources that show the mainstream frameworks do not prescribe those techniques at
> all**, one that offers a **different method entirely**, and **one empirical measurement of
> estimation accuracy**. The "What is missing" list below has been updated, not deleted — most of it
> is still missing.

## What the corpus does contain

### Techniques — named only
[S126] (Atlassian), in a single sentence about sprint planning:

> "Another common step in this meeting is to **score the stories based on their complexity or
> time to completion.** Teams use **t-shirt sizes, the Fibonacci sequence, or planning poker** to
> make proper estimations."

That is the entire treatment. **None of the three named techniques is explained anywhere in the
corpus.** The terms *story point* and *velocity* do not appear at all.

### The sizing constraint
[S126]: "**A story should be sized to complete in one sprint**, so as the team specs each story,
they make sure to break up stories that will go over that completion horizon."

[S128] gives a duration: stories "that take longer than a single sprint (**typically two weeks**)
should be broken into smaller stories."

[S127] states the same rule and, uniquely, explains why oversized items are harmful — see
[../06-requirements/epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md).

### Discomfort with time estimates
[S126] records the practice without endorsing it:

> "**Time is a touchy subject. Many development teams avoid discussions of time altogether,
> relying instead on their estimation frameworks.**"

> The corpus never explains *why* teams avoid time estimates, what an "estimation framework"
> substitutes for time, or how relative sizing converts back into forecast dates. This is the
> single largest conceptual hole in this area.

### Estimation as a prioritization input
Effort or cost estimates are required by most of the prioritization frameworks in
[prioritization-frameworks.md](prioritization-frameworks.md) — RICE's *Effort*, value vs effort's
horizontal axis, cost of delay's implementation time, weighted scoring's *Delivery effort*.

Several sources flag estimation quality as the weak link:

| Source | Concern |
|---|---|
| [S066] on value vs effort | "**Estimates** [are imprecise], where a team might think they have more resources than they do. Another drawback is **effort-sizing, which will vary from team to team.** That makes planning more difficult with cross-functional teams that have different resources" |
| [S066] on cost of delay | "If a project manager **underestimates the project size**, the calculations could be inaccurate. **Estimated time requirements may be incorrect as well**" |
| [S066] on RICE | "Methods for determining each evaluation factor can change, making this method **subjective, inconsistent, and potentially misleading**" |
| [S031] on value vs effort | "'Effort' in an AI feature isn't just build cost; it includes **evals, monitoring, run cost, support burden, rollback complexity, and compliance review**" |

> **The consistent theme: prioritization frameworks are only as good as their effort inputs, and
> the corpus says those inputs are unreliable — without saying how to improve them.**

### Use past performance, not intent
Two sources converge on this, and it is the corpus's only actual *guidance*:

[S003]: "A roadmap with aggressive timelines is problematic. It's exacerbated when the team
responsible for actually delivering the deliverables isn't the speedy efficiency machine you've
predicted. **Base your estimate on past performance, so there's a chance of things happening on
time.**"

[S108] (John Cutler) states it more strongly, as a rejection of estimation altogether for
roadmap sizing:

> "**Forget estimation. What has happened in the past?** I see teams pack their roadmaps like
> they're playing Tetris, only to discover — over and over — that they 'don't get to things'. And
> do that over and over. **Stop the charade!**"

[S108]'s alternative is throughput-based: size the roadmap by how many bets historically fit,
not by summed estimates. See [continuous-roadmapping.md](continuous-roadmapping.md).

> **This is a real position, not a gap-filler:** for *planning horizon* questions, historical
> throughput may be more reliable than aggregated estimates. It does not, however, answer
> item-level estimation questions.

### Who estimates
[S031]: bring the "**development team for development effort estimates**" into the scoring
itself, not just the meeting.

[S097]: project managers should be involved in roadmap planning "**to get realistic timeline
estimates and identify potential execution challenges early.**"

[S040]: features on an outcome-based roadmap "have to be **coarse-grained** and are limited to
three to five capabilities per goal" — an implicit argument for estimating at low granularity at
roadmap level.

## Phase 2 — what the primary texts actually say

### Scrum does not define estimation
[E001], the 2020 Scrum Guide, contains **no story points, no velocity, no planning poker, and no
estimation technique of any kind.** Sprint Planning's second topic asks *"What can be done this
Sprint?"* and leaves the method to the Developers.

> **This corrects a very widespread assumption**, including the one [S126] leaves the reader with.
> Story points, planning poker and velocity are **conventions layered on top of Scrum by the
> community**, not rules of it. A team that drops them has not stopped doing Scrum. See
> [../07-execution/scrum.md](../07-execution/scrum.md).

### The Agile Manifesto rules out velocity *as a measure of progress*
[E002], principle 7: **"Working software is the primary measure of progress."**

> Estimates and velocity may still be useful **planning aids**. The principle is about what counts as
> *progress*, and it names running software. A burndown chart trending nicely is not, by this
> principle, evidence of progress. See
> [../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md).

### Kanban offers a different method: probabilistic forecasting
[E003], *Essential Kanban Condensed* — **this is the substantive addition.**

**Its verdict on the dominant approach**, "effort-plus-risk estimating" (decompose, sum effort
estimates, inflate by a risk factor *"of between 2 and 10"*):

> **"This method has often proven spectacularly unsuccessful on all sizes of projects, but
> particularly on large and critical ones. Surprisingly, it still is the dominant method of
> forecasting."** [E003]

**The alternative:** once work flows through a system that records it, forecast from **observed
flow** instead of from estimates.

1. Collect, at minimum: **Lead Time, Delivery Rate, WIP, and cost** [E003].
2. Use **Little's Law** — *average Lead Time = average WIP ÷ average Delivery Rate* — which holds on
   averages in a non-trending system where selected items are delivered.
3. Run a **Monte Carlo** simulation over historical item-size variability, lead times and delivery
   rates to produce a **distribution of completion dates**, quoted at e.g. **50%, 85% and 95%**
   confidence.
4. Where no history exists, [E003] permits **range estimates** until data accumulates.

> **This answers a question the corpus raised and could not answer.** [S108]'s *"Forget estimation.
> What has happened in the past?"* is the same instinct — **[E003] gives it a method, a required
> dataset and a way to state confidence.** [S108] is a practitioner's assertion; [E003] is a
> documented technique resting on standard operations research.
>
> **Provenance caution:** [E003] is published by the organisation that sells Kanban training, and it
> hedges its own comparison — *"some would say more reliable."* **No controlled study comparing the
> two approaches is cited in it or found elsewhere.** What is independently solid is the underlying
> mathematics; the claim of superiority is **[UNVERIFIED]**. See
> [../07-execution/kanban.md](../07-execution/kanban.md).

### One measurement of estimation accuracy
[E006], the METR randomized controlled trial, is not an estimation study, but it measured
forecast-versus-actual on **246 real tasks** and the result bears directly here:

- Pearson correlation between **forecast** and **actual** completion time: **0.64** (AI-allowed) and
  **0.59** (AI-disallowed).
- Yet the same developers were **systematically and confidently wrong about the direction** of AI's
  effect — predicting 24% faster, reporting 20% faster, measuring 19% slower.

> [E006]'s own summary: *"developers are broadly well-calibrated on the relative amount of time that
> issues will take, but their expectations regarding the usefulness of AI assistance are reversed."*
>
> **Two lessons, and they pull in opposite directions — which is the point.**
> **(1)** *Relative* sizing by the people doing the work is **better than its reputation** — a 0.6
> correlation on real tasks is real signal, and it is the empirical support relative estimation has
> always lacked in this corpus. **(2)** The same people were badly wrong about a *systematic factor*
> affecting all their estimates. **Estimation error is not only noise; it can be a shared, confident
> bias** — which is exactly what probabilistic forecasting from history corrects for and what summing
> estimates does not.
>
> **Scope caution:** 16 developers, tasks averaging two hours, their own repositories, 2025. This is
> one measurement, not a literature. See
> [../13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md](../13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md).

## What is still missing

An agent should **not** attempt to answer the following from this knowledge base:

- What story points are, and how relative estimation works
- How planning poker is run
- What velocity is, how it is calculated, and its known misuses
- T-shirt sizing mechanics
- How to forecast a delivery date **from estimates** (forecasting **from flow data** is now covered
  above, from [E003] — these are different methods and should not be conflated)
- Cone of uncertainty
- **How to actually run a Monte Carlo forecast** — [E003] describes the approach and the required
  data, not the procedure, the tooling, or how much history is enough
- #NoEstimates and the arguments for and against estimating at all (beyond [S108]'s remark)
- Estimating discovery or research work
- Common estimation biases (anchoring, optimism bias, planning fallacy)
- Re-estimation policy
- Capacity planning and how estimates relate to team capacity

## Related concepts

- [prioritization-frameworks.md](prioritization-frameworks.md) — where effort estimates are consumed
- [continuous-roadmapping.md](continuous-roadmapping.md) — throughput as an alternative
- [roadmap-communication.md](roadmap-communication.md) — "don't out map your team's capabilities"
- [../06-requirements/epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md) — sprint-fit sizing
- [../07-execution/working-with-engineering.md](../07-execution/working-with-engineering.md)
- [../07-execution/kanban.md](../07-execution/kanban.md) — flow metrics and probabilistic forecasting
- [../07-execution/scrum.md](../07-execution/scrum.md) — what Scrum does and does not prescribe
- [../13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md](../13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) — the calibration measurement

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S126 | Atlassian — *User stories with examples and a template* | Vendor guide | Technique names, sprint sizing, discomfort with time estimates |
| S108 | John Cutler — *TBM 2.1/52: Continuous Roadmapping* | Practitioner newsletter | "Forget estimation" / historical throughput position |
| S003 | ProductPlan — *37 Roadmap Tips to Align Stakeholders* | Vendor guide | Base estimates on past performance |
| S066 | Atlassian — *Six product prioritization frameworks* | Vendor guide | Estimation as the weak input to prioritization |
| **E001** | **The Scrum Guide**, Schwaber & Sutherland, November 2020 | **Primary text** | **Scrum prescribes no estimation technique** |
| **E002** | **agilemanifesto.org — the twelve principles**, 2001 | **Primary text** | Principle 7: working software as the measure of progress |
| **E003** | **Anderson & Carmichael — *Essential Kanban Condensed*, 2016** | **Primary text** | Critique of effort-plus-risk estimating; Little's Law; probabilistic / Monte Carlo forecasting; required flow metrics |
| **E006** | **METR — *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*, July 2025** | **Randomized controlled trial** | Forecast-vs-actual correlations (0.64 / 0.59); systematic bias about AI's effect |
