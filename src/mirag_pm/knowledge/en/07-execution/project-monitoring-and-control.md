---
title: Project Monitoring and Control
domain: execution
type: process
topics:
  - project monitoring
  - project control
  - KPIs
  - change requests
  - corrective action
  - scope monitoring
source_count: 2
sources: [S020, S043]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Project Monitoring and Control

## Definition

[S020]: "Project monitoring and control is **a process used to gauge and measure the project's
performance.** The process involves **referring to the overall project plan, checking progress,
identifying any problems that get in the way, finding solutions to the problems, and applying any
necessary changes** to the overall project."

Its position: "**part of the execution phase** of the project."

Its core operation: "**comparing the project's current state with the original plan. And if there
are any lapses and issues, the process also involves applying corrective actions.**"

## Monitoring versus control — a distinction worth keeping

[S020] separates them clearly, and the difference determines who does what:

| | **Monitoring** | **Control** |
|---|---|---|
| **What it is** | "The act of **collecting and reporting data and project information**" | "All the **measures in place to make sure that the project is going according to schedule**" |
| **Output** | "Project managers get **a bird's eye view of the project's progress** while also **reporting relevant information to other stakeholders**" | Corrective action |
| **Relationship** | Produces the information | "**Controls are made based on the information from the project monitoring team**" |

> **Monitoring without control is reporting; control without monitoring is guessing.** The two must
> be coupled — which is exactly [S106]'s point about latency: detecting that a decision is going
> off course is only useful if something changes as a result. See
> [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md).

## What the process focuses on

[S020]:
- "**Comparing actual performance to planned performance**"
- "**Assessing the project's state to find any potential issues**"
- "Keeping timely and accurate information about the project"
- "**Delivering forecasts**"
- "Monitoring implementation of different corrections for various issues"

## Key steps

[S020] names five elements of the control process:

| Element | [S020] |
|---|---|
| **Monitoring KPIs** | "There need to be **key performance indicators** — metrics that show whether or not teams are performing as expected. Monitoring KPIs makes it easier for project managers to **find any lapses and apply corrective actions promptly.** Teams can also run a project health assessment to translate monitoring data into **clear go/no-go insights**" |
| **Monitoring requests** | "**Whenever projects go off course or deviate from the plan, requests are filed regarding the changes.** When monitoring a project, it's important to **track all these requests** and implement solutions right away" |
| **Monitoring project scope** | Named as a distinct element — see [../06-requirements/scope-definition.md](../06-requirements/scope-definition.md) |
| **Risk identification** | Named as an element — see [../10-risk/risk-identification.md](../10-risk/risk-identification.md) |
| **Monitoring dependencies** | [S020] references tracking "dependencies between tasks **to avoid bottlenecks**" — see [../05-planning/dependencies.md](../05-planning/dependencies.md) |

> Note that **change requests** and **risk identification** are treated as *monitoring* activities,
> not as separate processes. Deviation from plan is expected and is handled through a tracked
> request flow rather than silently absorbed. The corpus contains **no description of a change
> control process**, however.

## Why it matters

[S020]: "**The ultimate goal of project monitoring and control is to ensure that the project is
always on track.** ... monitoring and control play a big role when it comes to **finishing the
project on time and according to the original plan.** That way, teams can **take advantage of
different opportunities, correct issues right away, and make adjustments to the overall project
portfolio as necessary.**"

Its stated aim: "**discover problems and apply solutions before they make larger impacts** on the
overall project success."

> The framing — *"according to the original plan"* — reveals the assumption: this is a
> **plan-driven** control model. It presumes a baseline that deviation is measured against. That
> presumption is exactly what [S130] identifies as the difference between traditional and agile
> roadmaps, and what [S138] rejects in requirements ("be Agile in your evolution of requirements").
> See [../05-planning/roadmap-formats.md](../05-planning/roadmap-formats.md).
>
> **Both models are legitimate; they answer to different contract structures.** See
> [../06-requirements/scope-definition.md](../06-requirements/scope-definition.md) on who bears the
> cost of being wrong.

## Relationship to risk monitoring

[S043]'s Monitor Risk process shares inputs and outputs with this process: work performance data,
work performance reports, change requests, and plan updates all appear in both. In PMI's structure
they are distinct processes within the same monitoring-and-controlling process group.

See [../10-risk/risk-monitoring.md](../10-risk/risk-monitoring.md).

## Limitations

- **[S020] is a vendor topic guide** (Mitti/SafetyCulture, 16 Jul 2026) from a safety and
  operations software company; it is generic project management, not software product management,
  and closes with a product pitch.
- **Best practices section did not extract** — [S020] has a section headed "What Are the Best
  Practices for Project Monitoring and Control?" whose content is not in the corpus.
- **No metrics.** Beyond "KPIs," no specific project-health measures are named. [S043] names
  earned-value metrics but does not explain them. See
  [../10-risk/risk-monitoring.md](../10-risk/risk-monitoring.md).
- **No change control process** described.
- **No agile equivalent in the corpus** — burndown charts, velocity tracking, cumulative flow and
  cycle time are all absent from the original 143 sources. [S048] mentions "Kanban boards, Gantt
  charts, or burndown charts" in one clause without explanation.
  **Partially closed in Phase 2 from a primary source:** [E003] supplies the flow-measurement layer —
  **Lead Time, Delivery Rate, WIP and cost** as the minimum dataset, **Little's Law** relating them,
  the **Cumulative Flow Diagram**, and **probabilistic (Monte Carlo) forecasting** as an alternative
  to effort-plus-risk estimating. It also distinguishes **Service Level Expectation / Capability /
  Agreement / Fitness Threshold**, four terms routinely conflated. See
  [kanban.md](kanban.md) and [../05-planning/estimation.md](../05-planning/estimation.md).
  **Still absent:** burndown charts, velocity, earned-value mechanics.
- **No treatment of status reporting** to stakeholders, despite [S119] and [S039] both requiring
  ongoing roadmap communication.

## Related concepts

- [product-development-process.md](product-development-process.md)
- [working-with-engineering.md](working-with-engineering.md)
- [../10-risk/risk-monitoring.md](../10-risk/risk-monitoring.md)
- [../06-requirements/scope-definition.md](../06-requirements/scope-definition.md)
- [../05-planning/dependencies.md](../05-planning/dependencies.md)
- [../01-foundations/product-vs-project-management.md](../01-foundations/product-vs-project-management.md)
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md)
- [kanban.md](kanban.md) — flow metrics, Little's Law, cumulative flow diagrams

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S020 | Mitti (by SafetyCulture), Leon Altomonte — *A Short Guide to Project Monitoring and Control*, 16 Jul 2026 | Vendor topic guide | Definition, monitoring vs control distinction, focus areas, process elements |
| S043 | Project Management Academy — *How to Monitor Risks in Project Management* | PMI Authorized Training Partner | Shared inputs and outputs with risk monitoring |
