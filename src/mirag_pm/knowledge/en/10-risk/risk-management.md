---
title: Risk Management — Foundations
domain: risk
type: concept
topics:
  - risk management
  - risk definition
  - risk register
  - risk management plan
  - risk tolerance
  - project risk
  - positive risk
source_count: 4
sources: [S100, S051, S125, S065]
evidence_type: standards-aligned
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Risk Management — Foundations

## Definition of risk

The corpus contains a **standards-body definition**, which is rare in this material and should be
treated as the anchor:

> "Project Management Institute defines risk as **'an uncertain event or condition that, if it
> occurs, has a positive or negative effect on a project's objectives.'**" [S100]

[S065] quotes the same definition with "one or more project objectives."

### Two properties that follow, and are routinely missed

1. **Risk is about uncertainty, not about bad things.** A risk that has occurred is no longer a
   risk — it is an issue.
2. **Risk can be positive.** [S100]: "Potential risks include external, internal, technical, or
   unforeseeable **threats *and opportunities*** to your project and deliverables." This is why
   [S065] lists response strategies for both negative and positive risk — see
   [risk-response.md](risk-response.md).

> Most practitioner material in this corpus treats risk as purely negative. **The PMI-aligned
> sources do not**, and the distinction matters: "our competitor delays their launch" and "demand
> exceeds forecast" are risks requiring planned responses, not windfalls to be improvised around.

## What risk management is

[S125]: "Project risk management **identifies, assesses, and controls** potential risks. It's **an
ongoing practice** that helps prevent surprise events or setbacks from damaging or derailing the
project. The goal is **to understand which risks could occur during different stages of a project
and then work out how to counter them if they do happen.**"

Claimed benefits [S125]: "help complete projects **on time, reduce costs, and improve customer
satisfaction by averting problems before they cause large-scale disruption.**"

## The process

Assembled from [S100] and [S051], which follow the PMI process groups:

```
IDENTIFY RISKS          → produces the risk register
       ↓
QUALITATIVE ANALYSIS    → probability × impact; prioritisation
       ↓
QUANTITATIVE ANALYSIS   → data-driven modelling (EMV, Monte Carlo)   [not always performed]
       ↓
PLAN RESPONSES          → per risk: avoid / transfer / mitigate / accept / escalate
       ↓                  (exploit / share / enhance for positive risk)
MONITOR & CONTROL       → track, identify new risks, execute responses
       ↓
   (loop — reassessment throughout the project)
```

[S051] is explicit that this is not a one-pass activity: "Risk identification should happen early
in the project, closely followed by the risk assessment. **Project teams should conduct risk
reassessment throughout the life of a project.**"

### Reassessment cadence
[S051]: "The project's scope and risk management plan will inform how frequently the reassessment
should be conducted (**projects of bigger scope should have more reassessments; similarly, smaller
scope requires fewer**)."

A practical trigger [S051]: "**Updating the risk register is a good reminder to update the
corresponding risk assessment.**"

## Who does it

[S125]: "project risk management is **consistent across all projects yet can change depending on
the size and type of project**... But, **project managers regularly monitor risk management during
a project** to ensure its successful completion."

**Scaling the effort** [S125]: "It is essential to devote extra attention to managing and
minimizing risks for large projects. Conversely, **developing an ordered list of the high, medium,
and low-risk priorities is sufficient for smaller projects.**"

> This is useful permission: a three-tier priority list *is* risk management for a small project.
> The full apparatus is not always warranted.

## The core artefacts

| Artefact | Purpose |
|---|---|
| **Risk management plan** | [S125]: "should define your **method for assessing and organizing risks**, along with your team's **risk tolerance**, response plans, communication strategies, etc. ... **the time spent in the planning phase can be well worth it since it provides a framework that will help direct the project during execution**" |
| **Risk register** | [S100]: "**the primary output of risk identification** — a document compiling all known project risks and other relevant information about them." [S125] notes it is "also called a risk matrix. It can be a standalone or incorporated into the risk management plan" |
| **Risk report** | Named by [S043] as an output of monitoring |
| **Risk assessment matrix** | See [risk-assessment.md](risk-assessment.md) |

**Why the register must stay current** [S125]: "**Keeping this document up-to-date is vital to
ensure you always have an accurate snapshot of potential issues that can arise. As this information
is continuously updated and accessible to stakeholders, everyone can understand the project's
current state.**"

## How to state a risk properly

This is the most immediately useful technique in the corpus's risk material, and it corrects a
very common error.

[S125]:

> "**Too often, people miscalculate viewing risk solely by its possible results instead of the
> actual risk event.** For example, '**missing a deadline**' is seen as a project risk without
> understanding that **it's not the risk; instead, it's just one consequence.**
>
> To properly assess and handle risks... consider using this format:
> **Should X happen, Y may be triggered, which will cause Z impact.**"

PMI's own template, via [S100]:

> "**Because of [cause], [event] could occur during [time window], which could lead to [impact]
> with an [effect on project objective].**"

> **Why this matters:** you cannot mitigate "missing a deadline," because it names no mechanism.
> You *can* mitigate "because our only backend engineer is also on the migration project, a
> two-week delay could occur during Q3, which could lead to the launch slipping past the
> conference." The stated cause is where the response attaches.

## Risk tolerance

[S051] treats this as a required input, not a vague attitude:

> "**Every organization has a risk tolerance level, with variances due to the type of risk, the
> specific stakeholders of a project, and the scope of the project.** Additionally, there are
> **industries with negligible risk tolerance (such as health care) and others with an acceptance
> of some level of risk (like software development).** While every organization has a risk
> tolerance level, the project manager should **get stakeholder input to determine risk tolerance
> for each project.**"

> Risk tolerance is what makes *accept* a legitimate response rather than negligence. It must be
> established before responses are chosen, not inferred afterwards.

## Common types of project risk

[S125]:

| Type | Description and example |
|---|---|
| **Environment, safety and health** | "Current weather conditions, stock markets, and more. Given the risk of more frequent extreme weather... it's essential to have this risk assessment when planning large-scale building projects" |
| **Strategic or competitive** | "**Any big business decision has the potential for strategic risk**... Though you may have made the right decision based on all the information available, **things can still turn out badly.** For example, a competitor could launch a similar product before your project has even made progress" |
| **Scheduling and cost** | "If you have pre-arranged services or rental equipment, costs can skyrocket if your project doesn't go as planned" |
| **Third-party** | "Working with partners such as SaaS companies, suppliers, or fulfillment companies carries certain risks. For instance, the credit card data of a payment processor's clients may be compromised through a hack. **A hosting company's data center failure... could also mean your website being offline for hours**" |
| **Loss of support** | "Projects and organizations primarily funded by a few external sources can be prone to losing backing. **If your main sponsor or VIP customer suddenly stops funding**, it could leave your project lacking the necessary financial support" |

> The **strategic risk** entry restates, in risk language, the same principle as [S106]'s
> definition of a good decision: a sound decision can still produce a bad outcome. See
> [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md).

## Being proactive

[S125]: "Anticipating risks and taking proactive steps to mitigate them is essential... **By
thoroughly analyzing each potential risk, you can implement preventative measures that reduce your
chances of being surprised and having to react in haste.**"

## Limitations

- **The strongest sources here — [S100], [S051], [S065], [S043] — are from Project Management
  Academy, a PMI Authorized Training Partner.** They are written as **PMP exam preparation**, which
  makes them faithful to PMI terminology but also oriented toward certification rather than
  practice. **The PMBOK Guide itself is not in the corpus**; all PMI definitions here are quoted
  second-hand.
- **[S125] and the other Mitti/SafetyCulture sources are vendor content** from a safety and
  GRC software company. Their framing is generic operational risk rather than software product
  risk, and each ends in a product pitch.
- **No agile risk management material.** How risk is handled in short iterations, or by teams
  without a project manager, is absent. The nearest equivalents are assumption mapping
  ([../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md))
  and product risk ([product-risk.md](product-risk.md)).
- **No treatment of risk in decision-making under deep uncertainty**, or of risk appetite as a
  strategic choice rather than a constraint.

## Related concepts

- [risk-identification.md](risk-identification.md)
- [risk-assessment.md](risk-assessment.md)
- [risk-response.md](risk-response.md)
- [risk-monitoring.md](risk-monitoring.md)
- [product-risk.md](product-risk.md)
- [assumptions-and-constraints.md](assumptions-and-constraints.md)
- [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)
- [../07-execution/project-monitoring-and-control.md](../07-execution/project-monitoring-and-control.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S100 | Project Management Academy (Erin Aldridge, PMP, PMI-ACP, CSPO) — *Risk Identification in Project Management* | PMI Authorized Training Partner; exam-prep | PMI risk definition, risk statement template, register as output |
| S051 | Project Management Academy (Megan Bell) — *Introduction to Risk Assessment in Project Management* | PMI ATP; exam-prep | Reassessment cadence, risk tolerance, process placement |
| S125 | Mitti (by SafetyCulture), Rob Paredes — *Understanding Project Risk Management*, 16 Jul 2026 | Vendor topic guide | Definition of the practice, scaling by project size, artefacts, risk-event framing, risk types |
| S065 | Project Management Academy (Megan Bell) — *PMP Exam Strategies for Risk Response* | PMI ATP; exam-prep | PMI risk definition (corroboration) |
