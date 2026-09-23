---
title: Dependencies
domain: planning
type: concept
topics:
  - dependencies
  - blockers
  - cross-team dependencies
  - third-party dependencies
  - dependency management
  - critical path
source_count: 6
sources: [S084, S097, S130, S004, S119, S047]
evidence_type: fragmentary
confidence: low
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Dependencies

> **Coverage warning.** No source in the corpus is about dependency management. Dependencies are
> mentioned across roadmap, PRD, project-management and product-development sources, always in
> passing. What follows is a consolidation; the method is missing. See
> [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Definition

[S084]: "**Dependencies are any known condition or item the product will rely on**, such as
depending on Google Maps to add directions for a dog walking app."

[S048]: "Dependencies are **the factors your project relies on. You can't launch without them.**"

> Note the difference in strength. [S084] says *relies on*; [S048] says *cannot launch without*.
> The second is the stricter, more useful test — it distinguishes a dependency from a mere
> relationship.

### Distinguished from assumptions and constraints
[S084] defines all three together, and the distinctions matter:

| Term | Definition [S084] |
|---|---|
| **Assumption** | "Anything you expect to be in place (yet isn't guaranteed)" |
| **Constraint** | "Dictate something the eventual implementation **can't require**" |
| **Dependency** | "Any known condition or item the product **will rely on**" |

See [../06-requirements/requirements.md](../06-requirements/requirements.md).

## Types named in the corpus

| Type | Example / source |
|---|---|
| **Third-party / external** | [S084]: "depending on Google Maps." [S087]: "Dependency on a single platform or partner" is named as a product risk. [S119]: mature products have "third-party integrations to maintain" |
| **Cross-team / internal** | [S097]: project managers "identify dependencies between different work streams." [S081]: assess "dependencies on other internal teams or third-party providers" |
| **Cross-functional** | [S004]: "**Cross-Functional Dependency Management**" is named as a component of the product development process |
| **Technical / legacy** | [S119]: mature products have "a legacy to worry about... and regression issues to contend with" |
| **Between backlog items** | [S020]: monitoring "dependencies between tasks to avoid bottlenecks" |

## Where dependencies are surfaced

### In the PRD
[S084] places Assumptions, Constraints and Dependencies together as "the final batch of
ingredients for a PRD." [S086] requires documenting "any known dependencies" alongside
assumptions. [S048] notes dependencies help determine other PRD sections: "Use this section to
help you determine other headings you'll add to the document, like release criteria, features, or
scope of work."

### On the roadmap
[S047] (Mind the Product) names "**Highlight dependencies**" as a way to get more value from a
roadmap. [S119] identifies dependency burden as one of four ways roadmaps differ by product
maturity.

### In opportunity assessment
[S081]: a feasibility review should "perform a high-level resource audit: realistically assess
budget requirements, timelines, personnel availability, **and dependencies on other internal
teams or third-party providers.**"

### During execution
[S020] lists dependency monitoring within project monitoring and control. [S097] assigns
dependency identification to the project manager: they "break large initiatives into smaller,
manageable tasks and **identify dependencies between different work streams.**"

## The trade-off: rigid sequencing vs flexible prioritization

[S130] frames dependencies as a defining difference between roadmap styles, and it is the
corpus's sharpest observation on the topic:

> "**Traditional roadmaps often rely on a strict sequence of dependencies, where delays in one
> area can cascade into others.** Agile roadmaps embrace prioritization based on immediate needs
> and value delivery. This allows teams to work on what matters most **without being constrained
> by rigid interdependencies.**"

> **Read this carefully — it is easy to misread as "agile removes dependencies."** It does not.
> It describes a choice about *how the plan responds to them*: a dependency-sequenced plan buys
> predictability at the cost of cascade risk; a value-sequenced plan buys resilience at the cost
> of sometimes working on things that later block. The dependencies are the same either way.

## Reducing dependencies

The corpus offers one piece of advice, from [S019]:
> minimise "as many dependencies as possible to make your [work independent]" *(the sentence is
> truncated in the source)*.

[S111] gives an organizational observation rather than a technique: platform PMs work on
"internal platforms and services" whose "customers are **internal stakeholders and other product
teams**" — i.e. one structural response to cross-team dependencies is to treat the dependency
provider as a product with internal customers. See
[../01-foundations/pm-specializations.md](../01-foundations/pm-specializations.md).

## A failure signal

[S049] observes that "dependencies go silent" — the failure mode in which a dependency is agreed
but the providing team stops communicating. The corpus does not develop a response.

## What the corpus does not cover

- **Dependency mapping or visualisation** techniques
- **Critical path analysis**
- Negotiating and tracking cross-team commitments
- Dependency risk assessment (though see
  [../10-risk/risk-identification.md](../10-risk/risk-identification.md) for general risk
  identification techniques that could be applied)
- Architectural decoupling as a dependency strategy
- Vendor and platform dependency risk management
- Handling a dependency that slips
- Scaled-agile dependency mechanisms (PI planning, dependency boards)

## Related concepts

- [../06-requirements/requirements.md](../06-requirements/requirements.md) — assumptions, constraints, dependencies
- [../06-requirements/prd.md](../06-requirements/prd.md)
- [roadmaps.md](roadmaps.md)
- [release-planning.md](release-planning.md)
- [../10-risk/risk-management.md](../10-risk/risk-management.md)
- [../07-execution/working-with-engineering.md](../07-execution/working-with-engineering.md)
- [../07-execution/project-monitoring-and-control.md](../07-execution/project-monitoring-and-control.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S084 | ProductPlan — *Product Requirements Document* (Glossary) | Vendor glossary | Definition; distinction from assumptions and constraints |
| S097 | Atlassian — *Product manager vs. project manager* | Vendor guide | Dependency identification as project-manager work |
| S130 | Product School — *What Are Agile Roadmaps* | Training-provider guide | Rigid sequencing vs flexible prioritization trade-off |
| S004 | Reforge — *4 Key Stages of the Product Development Process* | Practitioner blog | Cross-functional dependency management as a process component |
| S119 | ProductPlan — *The Ultimate Guide to Product Roadmaps* | Vendor guide | Dependency burden by product maturity |
| S047 | Mind the Product — *How to get the most value out of your product roadmap* | Practitioner post | Highlighting dependencies on the roadmap |
