---
title: Risk Monitoring and Control
domain: risk
type: process
topics:
  - risk monitoring
  - risk triggers
  - risk register updates
  - reserve analysis
  - audits
  - earned value
  - proactive monitoring
source_count: 3
sources: [S043, S068, S125]
evidence_type: standards-aligned
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Risk Monitoring and Control

## Purpose

[S043]: "you can **never fully anticipate or control risks** during a project's lifecycle. However,
as a project manager, it may be helpful to **identify risk trigger events** and use the Monitor Risk
process to prepare for **both threats and opportunities.**"

What the process covers [S043]:
> "**identify and track risks, monitor for risk triggers, design and implement response plans,
> react when new risks occur, and measure your effectiveness to improve risk management
> processes.**"

> Note the last clause: monitoring includes **evaluating the risk process itself**, not only the
> risks.

## Inputs, tools and outputs

[S043] gives the PMI structure:

| Inputs | Tools & Techniques | Outputs |
|---|---|---|
| Project management plan | Data analysis | Work performance information |
| Risk management plan | **Technical performance analysis** | Change requests |
| Project documents | **Reserve analysis** | PM plan updates |
| Work performance data | **Audits** | Project document updates |
| Work performance reports | Meetings | Organizational process asset updates |

## The three core documents

[S043]:

| Document | Role |
|---|---|
| **Risk management plan** | "Your guide to dealing with project risks." Should outline: "risk management approaches, tools, and methodologies · **roles and responsibilities** for team members dealing with risks · **how to create time and cost contingencies** in your plans to manage risks · project-specific risk categories" |
| **Risk register** | "Created during the Identify Project Risks process and **updated throughout the project lifecycle.** Besides listing any known project risks, this document contains other information like **probability, impact, and risk triggers**" |
| **Risk report** | "**A snapshot of identified risks, responses, and owners at a given time.** It should include **who will take control of implementing a risk response plan and the agreed-upon risk response they will implement if a risk event occurs**" |

> The risk report answers a question the register often does not: **who acts, and what exactly do
> they do, when this fires.** A response without a named owner and a trigger is an intention, not a
> plan.

## Risk triggers

A **trigger** is the observable signal that a risk is materialising. [S043] lists them as content
of the risk register and names "monitor for risk triggers" as a core monitoring activity.

> The corpus does not define triggers further, but their function follows from [S106]'s treatment
> of **latency** in
> [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md): where there is a
> delay between a decision going wrong and that becoming visible, a trigger is the intermediate
> signal that closes the gap. [S106]'s recommendation — "identifying these latencies and putting in
> place **systems to proactively monitor** how a decision is progressing" — is exactly this
> practice.

## Performance data used in monitoring

[S043] lists earned-value metrics as risk-related performance inputs:

- **Earned value (EV)** · **Planned value (PV)**
- **Schedule variance (SV)** · **Cost variance (CV)**
- **Estimate at completion (EAC)** · **Estimate to complete (ETC)**
- **To-complete performance index (TCPI)**

> ⚠ **These are named only.** The corpus contains **no explanation of earned value management**,
> no formulas, and no guidance on interpretation. An agent should not attempt to compute or
> interpret EVM measures from this knowledge base. Recorded in
> [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Reassessing risks

[S043]: "**Regularly reviewing and reassessing your risk register** can help you determine if any
risk information has changed or evaluate the status of risk triggers. **Risks can become
irrelevant, their probability or priority levels could change, or new risks may arise** as your
project progresses."

> Three distinct outcomes of reassessment — a risk can *disappear*, *change score*, or be *newly
> discovered*. A reassessment that only ever adds risks is not being done properly.

[S051] gives the cadence rule: reassessment frequency scales with project scope, and "updating the
risk register is a good reminder to update the corresponding risk assessment." See
[risk-assessment.md](risk-assessment.md).

## Outputs

[S043]: "Potential outputs of this process include **document and plan updates, performance
reports, change requests**, and more."

[S100] frames the consequence plainly: "**you can't monitor and control risks if you haven't
identified any!** Ongoing monitoring and control are crucial to ensure that **identified, residual,
and new risks** don't threaten your project and deliverables."

> The mention of **residual risk** is important — see [risk-response.md](risk-response.md).
> Mitigated risks do not leave the register.

## Proactive versus reactive monitoring

[S068] (Mitti) frames monitoring as a posture rather than a checkpoint, describing it as a way to
"proactively manage risks and mitigate losses." Its stated benefits include **enhanced
decision-making** and providing "a structured" approach to recurring risk.

[S125] states the underlying argument: "**Anticipating risks and taking proactive steps to mitigate
them is essential**... By thoroughly analyzing each potential risk, you can implement preventative
measures that **reduce your chances of being surprised and having to react in haste.**"

> [S068] is a safety/GRC vendor guide oriented to workplace and compliance risk; its substantive
> content beyond this framing did not extract usefully. Its checklists and compliance-risk
> categories are outside the scope of product management.

## Where this connects to delivery monitoring

Risk monitoring overlaps with general project monitoring and control. [S020] lists **risk
identification** as an element of the project monitoring and control process alongside monitoring
KPIs, requests, and scope. See
[../07-execution/project-monitoring-and-control.md](../07-execution/project-monitoring-and-control.md).

## Limitations

- **[S043] is PMP exam-preparation material**; its inputs/tools/outputs table is faithful to PMI
  structure but the techniques (data analysis, reserve analysis, audits, technical performance
  analysis) are **named without explanation.**
- **Earned value management is entirely unexplained** (see above).
- **No treatment of risk burndown, risk trend reporting, or how to communicate risk status to
  stakeholders** — despite [S003] recommending that roadmaps "acknowledge the risks."
- **No agile equivalent.** How a team without a risk register or project manager monitors risk is
  absent. The nearest analogue in this knowledge base is continuous assumption validation —
  [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md).
- [S068]'s content is largely workplace-safety oriented and contributed little.

## Related concepts

- [risk-management.md](risk-management.md)
- [risk-identification.md](risk-identification.md)
- [risk-assessment.md](risk-assessment.md)
- [risk-response.md](risk-response.md)
- [product-risk.md](product-risk.md)
- [../07-execution/project-monitoring-and-control.md](../07-execution/project-monitoring-and-control.md)
- [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md) — latency and monitoring systems

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S043 | Project Management Academy (Erin Aldridge) — *How to Monitor Risks in Project Management* | PMI Authorized Training Partner | Monitor Risk process, inputs/tools/outputs, three core documents, reassessment, performance data |
| S068 | Mitti (by SafetyCulture) — *Risk Monitoring: Proactively Manage Risks and Mitigate Losses* | Vendor topic guide | Proactive monitoring framing |
| S125 | Mitti (by SafetyCulture) — *Understanding Project Risk Management* | Vendor topic guide | Proactive vs reactive argument; register currency |
