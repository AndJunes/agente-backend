---
title: Product Management When the Implementer Is an Agent
domain: ai-agent-collaboration
type: analysis
topics:
  - AI agents as team members
  - PM and AI agents
  - agentic development
  - multi-agent software teams
  - directing agents
  - tacit knowledge
  - verification bottleneck
  - PM role change
synonyms:
  - working with AI agents
  - managing AI agents
  - PM for agentic teams
  - AI agent team member
source_count: 7
sources: [E006, E007, E008, E011, E012, E013, E014]
evidence_type: synthesis
confidence: low
corpus_origin: false
external_research: true
verified: partial
phase: 2
provenance:
  primary: [E012, E013, E014]
  interpretation: []
  practice: [E011, E012, E013]
  empirical: [E006, E008]
last_reviewed: 2026-09-16
---

# Product Management When the Implementer Is an Agent

> **⚠ Read the confidence rating. It is `low`, and `verified: partial`.**
>
> **No source consulted for this knowledge base studies the product manager's job under agent
> implementation.** Not one. The empirical work measures developers ([E006]) and organisations
> ([E008]); the practice literature documents tooling ([E012], [E013]) and evaluation ([E011]).
>
> This document therefore does something the rest of the knowledge base avoids: **it reasons from
> evidence about adjacent questions toward a question nobody has measured.** Every such step is
> marked `[SYNTHESIS]` or `[INFERENCE]`. **An agent using this knowledge base must not present any
> claim in this document as established.** The honest inventory of what is unknown is in
> [open-questions-ai-and-pm.md](open-questions-ai-and-pm.md), and it is longer than this document.
>
> **The alternative — filling the gap with general PM advice relabelled for AI — would be worse.**
> It would be untraceable and unfalsifiable. What follows is deliberately thinner and deliberately
> marked.

## The one thing that is empirically supported

Of everything in this domain, **one finding bears directly on the product-management function**, and
it is the reason this domain exists rather than being a footnote:

> **"In the absence of a user-centric focus, AI adoption has a negative impact on team performance."**
> [E008]
>
> **"Without a user-centric focus, AI adoption is unlikely to help teams. It may even harm them."**
> [E008]

This is a **moderation** result from ~5,000 respondents: user-centric focus does not merely add to
AI's benefit — it determines whether the benefit is positive or negative. [E008] measured it as
agreement that creating value for users is the team's focus, that user experience is the top
priority, and that focusing on the user is key to business success.

**Its limits, stated plainly:** cross-sectional, self-reported, vendor-run, correlational. It
identifies a moderating relationship, **not a causal mechanism, and not a job description.** It does
not say a product manager causes user-centric focus, or that the role is necessary, or what a PM
should do differently. See
[evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md).

> **What it does support:** the claim that **faster implementation does not substitute for knowing
> what to build, and can actively hurt when that is missing.** That is a narrow claim. It is also the
> only one in this document with a number behind it.

## What changes, and what does not

### What does not change

Stated first, because the marketing pressure runs the other way.

- **Discovery.** Nothing in any source suggests agents reduce the need to find out what users need.
  [E008]'s moderation finding points the opposite way.
- **Strategy, positioning, prioritisation.** Cheaper implementation changes the *cost* input to a
  prioritisation decision. It does not supply the value estimate, the strategic fit, or the
  opportunity cost.
- **Stakeholder work.** No source addresses it. No reason to believe it changes.
- **The problem/solution distinction.** [E013]'s Design-First workflow, which derives requirements
  from an architecture, is a **new way to make the old mistake**, not a reason to stop caring about
  it. See [spec-driven-development.md](spec-driven-development.md).

### What plausibly changes

Each of the following is an **inference**, labelled, with the evidence it rests on and the weakness
of that evidence named.

---

#### 1. Written specification carries more weight, because the conversational channel is narrower

**Evidence it rests on:** [E006] found **implicit repository context** — that AI *"doesn't utilize
important tacit knowledge or context"* — among the five factors with evidence of contributing to
slowdown. Agile principle 6 [E002] names face-to-face conversation as the most efficient method of
conveying information within a team. SDD tooling ([E012], [E013]) is built on the premise that the
spec must be self-sufficient.

**The inference `[INFERENCE]`:** a human implementer fills specification gaps from shared context and
by asking. An agent fills them by **choosing something plausible**, and does so silently. The cost of
an ambiguous requirement therefore rises.

**Why this is weaker than it sounds:** [E006]'s tacit-knowledge finding concerns an AI-assisted editor
in a large legacy codebase, not an agent working to a written spec. **The inference could be wrong in
a specific and likely way:** agents can also *ask*, and a well-run agent workflow may recover context
through iteration rather than through a better upfront document. **Nothing consulted measures which
works better.**

**What follows practically** — and this is practice, not evidence:
- **Specify the unwanted behaviour.** EARS's `If <trigger>, then the <system> shall <response>`
  pattern [E014] exists for exactly this, and it is the pattern PMs most often omit.
- **State constraints that a colleague would know** — conventions, systems not to touch, decisions
  already made — because they are not in the model's context unless written.
- **Distinguish "not specified" from "any behaviour is acceptable"**, explicitly.

---

#### 2. Acceptance becomes probabilistic rather than binary

**Evidence:** [E011]'s **pass@k vs pass^k** arithmetic — 75% per-trial success gives **pass^3 ≈ 42%**.

**The inference `[INFERENCE]`:** "it works" as a single successful demonstration is **pass@1 on a
sample of one**. For anything running unattended for users, pass^k is the relevant quantity, and it
degrades fast.

**Weakness:** [E011] is about evaluating agent *products*, not about accepting agent-*built* features.
A feature built once by an agent and then reviewed, tested and merged is a **deterministic artifact
thereafter** — the non-determinism was in the authoring, not the running. **The pass^k framing
applies squarely to agent-in-the-loop products and only loosely to agent-built software.** Treat it
as the right frame for the former and an open question for the latter. See
[evals-and-acceptance-for-agents.md](evals-and-acceptance-for-agents.md).

---

#### 3. Review capacity becomes the plausible constraint

**Evidence:** [E006] — **under 44% of AI generations accepted**, majority reporting major cleanup,
~9% of working time on reviewing and cleaning AI output. [E008] — **AI adoption increases delivery
instability**, and **30% of respondents report little or no trust in AI-generated code**.
[E009]/[E010] — the **"verification tax"** as a named component of the adoption J-curve.

**The inference `[INFERENCE]`:** if generation volume rises while acceptance rates stay well below
100%, the constraint moves **from producing work to verifying it** — and verification is the step
that least obviously scales by adding more agents.

**Why this matters to a PM specifically:** in flow terms ([../07-execution/kanban.md](../07-execution/kanban.md)),
adding capacity upstream of a bottleneck **lengthens the queue without improving delivery**. If review
is the bottleneck, "the agents can build it faster" is not an argument for accepting more work in
progress — it is an argument for **tighter WIP limits**, which is counter-intuitive enough that it
will not happen by default.

**Weakness:** this chains three studies that were not designed to be chained, none of which measured
a bottleneck. **It is a hypothesis worth instrumenting, not a finding.** The obvious refutation:
verification may itself be substantially automatable, which is what eval suites and `converge` loops
([E012]) are for.

---

#### 4. Batch size becomes a lever with measured consequences

**Evidence — this one is stronger.** [E008] found *"with a high degree of certainty"* that when teams
work in small batches, **AI's positive influence on product performance is amplified** and **AI's
neutral effect on friction becomes beneficial**. It also found AI's boost to *individual
effectiveness* **slightly reduced** in small-batch teams, and explained it: AI raises perceived
individual effectiveness largely *"by helping developers to quickly generate a large amount of
code"*, which small batches constrain.

[E008]'s own judgement: *"individual effectiveness should not necessarily be pursued as a goal in and
of itself."*

**Why this is the most directly actionable item here:** batch size is **already a PM decision** —
story slicing, release scoping, how much goes out at once. See
[../06-requirements/epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md) and
[../05-planning/release-planning.md](../05-planning/release-planning.md). [E008] says this existing
lever **changes the sign of AI's effect on friction** and **amplifies its effect on product
performance** — and that the pressure a team will feel to abandon it (developers feel more effective
generating more code at once) is **measuring the wrong thing.**

**Weakness:** still self-reported and cross-sectional. And "small batches" was measured as lines per
change, changes per release, and task duration — **not** as anything specific to agent workflows.

---

#### 5. Standing context becomes a maintained artifact

**Evidence:** [E012]'s **constitution** — project principles on code quality, testing and
maintainability, authored **once per project** and applied to every feature. [E008]'s **"clear and
communicated AI stance"**, the first of its seven capabilities, which it stresses measures *"the
clarity and awareness — not the specific content"* of an organisation's position.

**The inference `[INFERENCE]`:** the standing constraints a human team carries as culture — what
"good" means here, what is out of bounds, what was decided and why — **have to be written down and
maintained** for an implementer that does not accumulate culture. This is a new class of PM artifact:
not a spec for a feature, but **durable context for all features**.

**Its nearest existing relatives** are the Definition of Done ([E001], [E003] — a standing
product-level quality policy) and explicit policies ([E003], practice 4: *"sparse, simple,
well-defined, visible, always applied, and readily changeable"*). **[E003]'s warning transfers
exactly**: policies that are never challenged or changed are a poor application of the practice. A
constitution that ossifies is worse than none.

**Weakness:** whether the PM or the engineering lead owns this is **entirely unaddressed** by any
source. [E012] does not say. Nor does [E008].

---

## What this domain does NOT contain, and must not be used for

- **How to organise a multi-agent software team** — roles, handoffs, orchestration. **Nothing.**
  This is the specific gap the project that commissioned this knowledge base is trying to fill, and
  research did not close it.
- **Whether a PM agent should behave differently from a human PM.** Unaddressed.
- **Cost models.** What an agent-implemented feature costs, or how to make a build/buy or
  scope decision with agent implementation in the mix.
- **Team composition and headcount.** [E010] reports [E009] *discouraging* headcount reduction; that
  is a vendor's recommendation reaching us through a news summary, and nothing more.
- **Failure modes specific to agent implementation** — beyond low acceptance rates and instability.
  No taxonomy of what goes wrong was found.
- **Security, privacy, licensing or compliance** of agent-generated code. See
  [../10-risk/it-and-security-risk.md](../10-risk/it-and-security-risk.md), which predates this
  entirely.
- **Anything about non-software agent work.** [E006] is explicit: *"We only study software
  development."*

## Limitations

- **Confidence `low` is the honest rating.** Five of seven claims above are inferences across studies
  that were not designed to support them.
- **All sources are from 2025–2026**, in a field changing faster than it is measured. [E007] is the
  proof: METR withdrew its own experimental design within seven months.
- **Every vendor source has an interest** in the conclusion that agent-assisted development works and
  needs supporting practices. [E008] and [E011] are the most careful; they are not disinterested.
- **No source is a product manager describing this work.** The absence of practitioner field reports
  is itself notable and may simply mean the practice is too young to have produced any.
- **Selection bias is pervasive and unquantified** — visible in [E007]'s account of why METR had to
  redesign its experiment. The teams most enthusiastic about agent implementation are the ones being
  studied, and the ones publishing.
- **This document will date faster than anything else in this knowledge base.** `last_reviewed` is
  load-bearing here, not decorative.

## Related concepts

- [evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md) — **read first**
- [spec-driven-development.md](spec-driven-development.md)
- [evals-and-acceptance-for-agents.md](evals-and-acceptance-for-agents.md)
- [open-questions-ai-and-pm.md](open-questions-ai-and-pm.md) — **longer than this document, by design**
- [../07-execution/working-with-engineering.md](../07-execution/working-with-engineering.md)
- [../07-execution/kanban.md](../07-execution/kanban.md) — flow, WIP and bottlenecks
- [../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md) — principle 6 and its assumptions
- [../06-requirements/prd.md](../06-requirements/prd.md)
- [../06-requirements/epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md)
- [../05-planning/release-planning.md](../05-planning/release-planning.md)
- [../10-risk/it-and-security-risk.md](../10-risk/it-and-security-risk.md)

## Sources

| ID | Source | Used for | Provenance |
|---|---|---|---|
| E006 | METR RCT, July 2025 | Tacit-context finding; acceptance rate; review time | `EMPIRICAL` |
| E007 | METR design update, Feb 2026 | Currency caveat; selection bias | `EMPIRICAL / CORRECTION` |
| E008 | DORA, *State of AI-assisted Software Development* 2025 | **User-centric focus moderation**; small batches; AI stance; instability; trust | `EMPIRICAL (self-report)` |
| E011 | Anthropic, *Demystifying evals for AI agents*, Jan 2026 | pass@k / pass^k; outcome-based grading | `PRACTICE` |
| E012 | GitHub `spec-kit` | Constitution; converge loop | `PRIMARY (tool)` |
| E013 | Kiro (AWS) documentation | Three-document structure; Design-First trade-off | `PRIMARY (tool)` |
| E014 | Mavin et al., EARS, Rolls-Royce, 2009 | Unwanted-behaviour pattern | `PRIMARY` |

Full source records in [../SOURCES.md](../SOURCES.md).
