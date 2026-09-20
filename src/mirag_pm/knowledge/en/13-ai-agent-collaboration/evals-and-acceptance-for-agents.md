---
title: Evals and Acceptance When the Implementer Is an Agent
domain: ai-agent-collaboration
type: practice
topics:
  - evals
  - evaluations
  - capability evals
  - regression evals
  - LLM-as-judge
  - graders
  - pass@k
  - pass^k
  - eval saturation
  - non-determinism
  - acceptance criteria
  - verification
  - Swiss Cheese model
synonyms:
  - evaluating AI agents
  - testing AI agents
  - agent quality assurance
  - how to know if an agent works
source_count: 2
sources: [E011, E006]
evidence_type: professional-practice
confidence: medium
corpus_origin: false
external_research: true
verified: true
phase: 2
provenance:
  primary: [E011]
  interpretation: []
  practice: [E011]
  empirical: [E006]
last_reviewed: 2026-09-16
---

# Evals and Acceptance When the Implementer Is an Agent

> **Scope note.** [E011] is written about **evaluating AI agents as products** — an engineering
> practice for teams building agent systems. This document reports it faithfully and then asks a
> second question the source does not address: **what does it imply for how a PM writes acceptance
> criteria when an agent is the implementer?** Everything in the second category is marked
> `[SYNTHESIS]`.

## Why acceptance changes at all

A deterministic implementation either meets a criterion or does not; you check once. **An agent's
output is non-deterministic.** The same specification run twice can produce two different
implementations, both defensible, one correct. This breaks a silent assumption behind every
acceptance-criteria format in
[../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md): that
**"passes" is a property of the artifact rather than a property of a distribution.**

[E011] makes the consequence concrete, and the arithmetic is the single most useful thing in it.

## pass@k versus pass^k

| Metric | Measures [E011] |
|---|---|
| **pass@k** | The probability of **at least one** success across *k* attempts |
| **pass^k** | The probability that **all** *k* attempts succeed |

[E011]'s worked example: at a **75% per-trial success rate over 3 trials**, **pass^3 ≈ 42%** — while
pass@3 is high. **The two diverge sharply as *k* grows.**

> **The PM reading of this.** *"It works"* is ambiguous in a way it was not before.
>
> - **pass@k is the right frame for a human-in-the-loop workflow** — a developer regenerating until
>   something works, a designer picking from options. You need one good result.
> - **pass^k is the right frame for anything that runs unattended on real users.** A feature that
>   works 75% of the time is not 75% good; across three sequential steps it fails most of the time.
>
> A PM accepting an agent-implemented feature on a single successful demonstration is measuring
> **pass@1 on a sample of one**, and treating it as a guarantee. **`[SYNTHESIS]` — [E011] states the
> arithmetic; the application to feature acceptance is this knowledge base's.**

## What an eval is

> An evaluation is **"a test for an AI system: give an AI an input, then apply grading logic to its
> output to measure success."** [E011]

[E011] orders them by difficulty: single-turn, then multi-turn, then **agent evaluations as the most
complex category, because of tool use across multiple turns.**

## Two kinds, with opposite target pass rates

| Kind | Asks [E011] | Target pass rate |
|---|---|---|
| **Capability evals** | What does the agent do well? Aimed at **difficult** tasks | **Should start LOW** |
| **Regression evals** | Does it still do what it used to? | **Near 100%** — anything else is degradation |

**As capability evals saturate, they graduate into the regression suite.** [E011]

> **This distinction has a direct analogue in product work and the corpus contains no equivalent.**
> An acceptance criterion that everything already passes carries no information; one that nothing
> passes is aspirational. **A well-run product needs both**: criteria that define the current quality
> floor (regression) and criteria that define the frontier being attempted (capability). Conflating
> them — the usual state of a requirements document — hides which is which.
> **`[SYNTHESIS]`.**

## Saturation

[E011]: an eval at a **100% pass rate no longer signals improvement.** It flags **>80%** on
benchmarks as the point where **signal-to-noise degrades for measuring future progress**, citing
frontier models approaching that level on SWE-bench Verified.

> The same logic applies to a product's success metrics — a metric everyone passes has stopped
> measuring. See [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md). **`[SYNTHESIS]`.**

## The three grader types

| Grader | Strengths [E011] | Weaknesses [E011] |
|---|---|---|
| **Code-based** | Fast, cheap, objective, reproducible, easy to debug | **Brittle to valid variations**; lacks nuance |
| **Model-based** (LLM-as-judge) | Flexible, scalable, captures nuance, handles open-ended tasks | **Non-deterministic, expensive, needs calibration** |
| **Human** | Gold-standard quality; matches expert judgement | Expensive, slow, requires expert access |

> **The trade-off is exactly the one behind every acceptance-criteria debate in
> [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md)** —
> automatable-but-rigid versus judgement-based-but-inconsistent. What is new is that the middle
> option now exists and is cheap, **and that it is itself non-deterministic and needs calibrating
> against human judgement before it can be trusted.** A model-based grader is not a shortcut past the
> human; it is a way of **amortising** the human's judgement, and it has to be checked against that
> judgement periodically.

## Grading an agent: outcome, not trajectory

[E011] distinguishes:

- the **transcript** — the complete interaction record, including tool calls
- the **outcome** — the **final environment state**

Its guidance is explicit: **grade outcomes, not step sequences.** Rigid step-checking penalises
creative valid approaches. Agents should receive **partial credit** for partial success. And the
recommendation that costs the most and is skipped the most: **read the transcripts.**

> **This is the same argument as outcome-based roadmaps, arriving from a different direction.** [S040]
> and the material in
> [../05-planning/outcome-based-roadmaps.md](../05-planning/outcome-based-roadmaps.md) argue against
> specifying outputs because it removes the team's problem-solving latitude. [E011] argues against
> specifying step sequences because it penalises valid approaches the evaluator did not anticipate.
> **Same failure, same fix, different implementer.** An acceptance criterion that names the
> implementation is a bug in both worlds. **`[SYNTHESIS]`.**
>
> **Partial credit has no analogue in current PM practice**, where acceptance is binary. Whether it
> should is an open question — see [open-questions-ai-and-pm.md](open-questions-ai-and-pm.md).

## Getting started — [E011]'s roadmap

The advice most worth keeping is the first line, because it contradicts how most teams stall:

> **Start with 20–50 simple tasks drawn from real failures** — do not wait for hundreds. Small sample
> sizes detect meaningful changes early in development. [E011]

Other steps: run in **isolated environments**; **grade outputs rather than step sequences**; **read
transcripts**; watch for **saturation above ~80%**; and give evals **dedicated ownership**.

> **"Drawn from real failures"** is the load-bearing phrase. It is the same instruction as
> [../02-discovery/identifying-unmet-needs.md](../02-discovery/identifying-unmet-needs.md) gives for
> discovery: start from observed problems, not imagined ones.

## The six common mistakes

[E011] names these; they read as a checklist for a PM reviewing anyone's acceptance criteria:

1. **Ambiguous task specifications**
2. **Shared state between trials**, introducing noise
3. **Overly rigid grading** that penalises valid alternatives
4. **Class-imbalanced evaluation sets**
5. **Insufficient environment isolation**
6. **Grading bugs**, and demanding strict reproducibility from stochastic tasks

> **Mistakes 1 and 3 are PM-owned.** Ambiguity in the specification is the failure that
> [spec-driven-development.md](spec-driven-development.md) and EARS exist to reduce; over-rigid
> grading is what happens when acceptance criteria are written as implementation steps.

## The Swiss Cheese model

[E011] borrows the safety-engineering concept:

> **"no single evaluation layer catches every issue. With multiple methods combined, failures that
> slip through one layer are caught by another."** [E011]

The layers it names: **CI/CD evals · production monitoring · A/B testing · transcript sampling.**

> **This is a risk-management model, and the corpus already has the vocabulary for it** — layered
> controls, residual risk, monitoring. See [../10-risk/risk-response.md](../10-risk/risk-response.md)
> and [../10-risk/risk-monitoring.md](../10-risk/risk-monitoring.md). **What is new is the admission
> built into the model: you are not aiming for zero escapes, you are aiming for uncorrelated
> layers.** A PM who asks "how do we guarantee this is correct?" is asking a question the model says
> has no answer.

## The verification burden lands on someone

Two independent findings, from sources with no relationship to each other, point at the same cost:

- **[E006]**: developers **accepted under 44% of AI generations**, a majority reported **making major
  changes to clean up AI code**, and **~9% of total working time** went to reviewing and cleaning AI
  output.
- **[E009]/[E010]**: the *"verification tax"* — review overhead on AI-generated code — is named as one
  of three causes of the adoption **J-curve** dip.

> **`[SYNTHESIS]`, flagged as inference, not finding:** if the volume of generated work rises while
> the acceptance rate stays well below 100%, **review capacity becomes the constraint**, and review
> is exactly the activity that does not scale by adding agents to it. This is a plausible reading of
> two data points from different studies. **It has not been measured, and it is not a claim either
> source makes.** See [../07-execution/kanban.md](../07-execution/kanban.md) — if it holds, review is
> a bottleneck in the flow sense, and adding upstream capacity makes the queue longer, not the
> delivery faster.

## Limitations

- **[E011] is an Anthropic engineering guide**, written by a company selling AI models and agent
  tooling. It is technically specific and publishes its own failure modes, but it is **not
  independent**, and it presents **no controlled evidence** that its recommended practices produce
  better outcomes than alternatives.
- **It is about evaluating agents as systems, not about accepting agent-produced work.** The entire
  bridge to product acceptance in this document is marked `[SYNTHESIS]` and is **this knowledge
  base's reasoning, unvalidated**.
- **No source here describes how a PM should actually run acceptance on an agent-implemented
  feature.** No template, no worked example, no field report was found. This is a genuine gap, not an
  omission.
- **pass@k / pass^k assume independent trials.** Repeated attempts on the same task with the same
  context are **not** independent, so the arithmetic is an idealisation. [E011] does not dwell on
  this; the caveat is this knowledge base's.
- **The 80% saturation threshold is a rule of thumb**, offered without derivation.
- **Nothing here addresses cost** — of running evals, of human review, or of the compute.

## Related concepts

- [pm-with-ai-implementers.md](pm-with-ai-implementers.md)
- [spec-driven-development.md](spec-driven-development.md) — the specification side of the same loop
- [evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md)
- [open-questions-ai-and-pm.md](open-questions-ai-and-pm.md)
- [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md)
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md)
- [../10-risk/risk-response.md](../10-risk/risk-response.md)
- [../10-risk/risk-monitoring.md](../10-risk/risk-monitoring.md)
- [../10-risk/it-and-security-risk.md](../10-risk/it-and-security-risk.md)
- [../07-execution/kanban.md](../07-execution/kanban.md)

## Sources

| ID | Source | Type | Provenance | Reliability |
|---|---|---|---|---|
| E011 | **Anthropic — *Demystifying evals for AI agents*** (Mikaela Grace, Jeremy Hadfield, Rodrigo Olivares, Jiri De Jonghe), **9 January 2026** | Vendor engineering guide | `PRACTICE` | **B** — specific and self-critical; vendor-authored, no controlled evidence |
| E006 | METR — *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*, July 2025 | RCT | `EMPIRICAL` | **A** — used here for the acceptance-rate and review-time figures |
