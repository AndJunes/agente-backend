---
title: Open Questions — Product Management and AI Agents
domain: ai-agent-collaboration
type: gap-register
topics:
  - open questions
  - unknowns
  - research needed
  - what is not known
  - AI agents PM gaps
synonyms:
  - what we do not know about PM and AI agents
  - unanswered questions AI agents product management
source_count: 0
sources: []
evidence_type: gap-register
confidence: high
corpus_origin: false
external_research: true
verified: true
phase: 2
provenance:
  primary: []
  interpretation: []
  practice: []
  empirical: []
last_reviewed: 2026-09-16
---

# Open Questions — Product Management and AI Agents

> **This document contains no answers, by design.** `confidence: high` refers to high confidence
> that these questions are genuinely open — not to any claim about their answers.
>
> **Purpose.** This is the domain where an agent using this knowledge base is most likely to
> confabulate: the questions are current, plausible-sounding answers are abundant online, and the
> corpus contains nothing. This register exists so that **"I don't know, and here is what would have
> to be true to know"** is retrievable as an answer, rather than being the absence of one.
>
> **Instruction to any agent reading this:** if a user's question maps to an item below, say that the
> knowledge base does not answer it and describe what evidence would settle it. Do not answer from
> model memory. Model memory is not a source — see [../README.md](../README.md).

## A. Questions about the product manager's work

| # | Question | Why it is open |
|---|---|---|
| A1 | **Does the PM role change at all when implementation is agent-driven, or only the volume of work downstream?** | No study of PM practice under agent implementation was found. Every claim in [pm-with-ai-implementers.md](pm-with-ai-implementers.md) is inference from adjacent evidence |
| A2 | **Does more upfront specification actually produce better outcomes with agents than iterative conversational direction?** | The entire SDD movement assumes yes. **No controlled comparison exists** in any source consulted. See [spec-driven-development.md](spec-driven-development.md) |
| A3 | **At what feature size does specification overhead stop paying?** | Not quantified anywhere. [E013] ships a "Quick Spec" mode with no approval gates, implying a threshold exists, without saying where |
| A4 | **Who owns the standing context** — constitution, conventions, quality bars: PM, tech lead, or a new role? | No source assigns it |
| A5 | **Does the PM/PO distinction survive?** | Already contested without agents ([E001] vs [E003] vs corpus — see [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)). Nothing addresses it under agent implementation |
| A6 | **Does discovery change, or only delivery?** | [E008]'s moderation finding suggests discovery matters *more*, but measures nothing about how it is *done* |
| A7 | **Should acceptance admit partial credit**, as [E011] recommends for agent evals? | Product acceptance is conventionally binary. Whether the eval convention transfers is unexamined |

## B. Questions about teams and organisation

| # | Question | Why it is open |
|---|---|---|
| B1 | **How should a multi-agent software team be organised** — roles, handoffs, orchestration, escalation? | **Nothing found.** This is the largest single gap in the domain and the one this knowledge base was commissioned to serve |
| B2 | **Is review capacity actually the new constraint?** | A three-study inference ([E006], [E008], [E009]) that no study tested. See [pm-with-ai-implementers.md](pm-with-ai-implementers.md) §3 |
| B3 | **Can verification be automated enough to relieve the bottleneck, and at what residual risk?** | Eval suites and `converge` loops assume yes. No measurement of escape rates |
| B4 | **What team size and composition works?** | No evidence. [E010] reports [E009] discouraging headcount reduction — a vendor recommendation via a news summary, not a finding |
| B5 | **What happens to junior roles and to how expertise is acquired?** | Widely discussed in public; **no evidence in any source consulted.** A strong candidate for confabulation |
| B6 | **Do the Scrum and Kanban frameworks still apply as written?** | [E001] presumes human Developers self-managing; [E003] presumes people self-organising around work. Neither addresses non-human implementers. **No source examines whether their mechanics hold** |

## C. Questions about quality, risk and cost

| # | Question | Why it is open |
|---|---|---|
| C1 | **What is the defect rate and long-run maintainability of agent-written code?** | Not measured in any consulted source. [E008] measures *perceived* code quality and *delivery instability*, which are different quantities |
| C2 | **Does delivery instability [E008] fall as practice matures, or is it structural?** | The J-curve [E009] asserts it falls. Asserted by a vendor, not demonstrated |
| C3 | **What does an agent-implemented feature actually cost**, end to end including specification, review and rework? | No source provides a cost model. The only ROI figures available are vendor projections — see [evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md) |
| C4 | **What are the failure modes specific to agent implementation?** | No taxonomy found. [E006] gives acceptance rates, not a classification of what goes wrong |
| C5 | **Security, licensing, privacy and compliance of agent-generated code** | Entirely outside every source consulted |
| C6 | **Accessibility** | Absent from this knowledge base altogether, agent-related or not. A Priority-4 gap in [../RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md) that should probably be higher |

## D. Questions about the evidence itself

| # | Question | Why it is open |
|---|---|---|
| D1 | **Is the METR 19% slowdown [E006] representative of anything current?** | **Its own authors say the picture has likely changed and that their newer data is "only very weak evidence" for the size of the change** [E007]. No equally rigorous replacement exists |
| D2 | **Can anyone still run a clean RCT on this?** | [E007] describes why METR could not: developers now decline tasks they would not do without AI, breaking randomisation. **This may be a durable methodological problem, not a temporary one** |
| D3 | **How much of the published evidence is vendor-produced, and what is the publication bias?** | Unquantified. Of the sources here, [E008], [E009], [E011], [E012] and [E013] are all published by companies selling AI tooling |
| D4 | **Does the perception gap [E006] persist?** | The most robust and most transferable finding in the literature — measured once, in one setting, in 2025 |
| D5 | **Is there non-Western or non-English research on any of this?** | Not searched for. A known limitation of this entire knowledge base |

## What would settle these

Recorded so that a future research pass has criteria rather than topics:

- **For A2 and A3** — a controlled comparison: same tasks, same agents, specification-first versus
  conversational direction, measuring time-to-accepted-merge and post-merge defect rate, stratified
  by task size. Nothing smaller than this resolves the SDD question.
- **For B1** — field reports. Even uncontrolled, documented accounts of running multi-agent teams
  would move this from "nothing" to "practice with known provenance." Level-4 sources (blogs, forums)
  are legitimate for **discovery** of what teams are trying; they are not authority for what works.
  See the source hierarchy in [../README.md](../README.md).
- **For B2 and B3** — flow measurement: lead time decomposed by stage, with review isolated, before
  and after agent adoption. The instrument already exists — cumulative flow diagrams and Little's Law,
  see [../07-execution/kanban.md](../07-execution/kanban.md). **This is measurable today by any team
  willing to instrument it, and would be the cheapest real contribution available.**
- **For C1** — longitudinal defect and change-failure data tied to authorship provenance.
- **For D1** — a replication with current tooling, and a method that survives [D2]'s selection
  problem.

## Standing instruction

> When a question in this register is asked, the correct answer is:
>
> 1. **State that the knowledge base does not answer it**, and why — the specific absence, not a
>    generic disclaimer.
> 2. **Give whatever adjacent evidence exists**, with its scope conditions attached.
> 3. **Say what would settle it.**
>
> This is not a limitation of the knowledge base to be apologised for. **It is the knowledge base
> working.** A confident answer to any of these questions, from any source, is currently
> unsupported — and an agent that produces one has stopped being traceable.

## Related concepts

- [pm-with-ai-implementers.md](pm-with-ai-implementers.md)
- [evidence-on-ai-assisted-delivery.md](evidence-on-ai-assisted-delivery.md)
- [spec-driven-development.md](spec-driven-development.md)
- [evals-and-acceptance-for-agents.md](evals-and-acceptance-for-agents.md)
- [../RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md)
- [../99-reference/disputed-information.md](../99-reference/disputed-information.md)
- [../CORPUS_AUDIT.md](../CORPUS_AUDIT.md)

## Sources

None. **This document asserts no facts about the world** — only about the state of this knowledge
base. Source IDs referenced above are documented in [../SOURCES.md](../SOURCES.md) and treated in the
three sibling documents.
