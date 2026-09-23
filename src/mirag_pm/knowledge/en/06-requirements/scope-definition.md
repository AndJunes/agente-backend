---
title: Scope Definition and Scope Creep
domain: requirements
type: concept
topics:
  - scope
  - out of scope
  - scope creep
  - features out
  - change requests
  - boundaries
source_count: 6
sources: [S048, S138, S113, S086, S097, S044]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Scope Definition and Scope Creep

## Definition

The corpus has no single definition of scope. It is treated consistently as **the boundary
between what a release will and will not include.**

[S048] states the operating rule: "Define what **is and isn't** within the project scope. No
matter the type of project, setting boundaries will help prevent **scope creep** — work that's
outside of the project's reach — and keep the team on track."

[S086] frames the same thing as a PRD section: "**Scope:** What is a current priority and what
will not be included now, but **might go in a future release**."

## The central practice: state what you are not doing

Three independent sources treat the negative statement as a distinct, named artefact rather than
an afterthought. This convergence is the strongest signal in the corpus on this topic.

| Source | Section name | Instruction |
|---|---|---|
| [S138] | **"What we're not doing"** | "Keep the team focused on the work at hand by clearly calling out what you're not doing. **Flag things that are out of scope at the moment, but might be considered at a later time.**" |
| [S113] | **"Features Out"** | "What have you explicitly decided not to do **and why**" |
| [S084] | (within Features) | "Additional details may be helpful or necessary depending on the complexity of the feature, such as **out-of-scope items**" |

> **Why this works.** An unstated exclusion is indistinguishable from an oversight. Writing
> "we are not doing X, because Y" converts a silent omission into a recorded decision — which
> means it can be challenged, revisited, or cited later, rather than quietly re-litigated every
> time someone notices X is missing.

[S113] adds the "why" requirement, which the other two omit. Keeping the rationale is what makes
the exclusion durable: without it, the item returns as soon as the person who made the decision
leaves the conversation.

## Where scope gets decided

[S084] locates the decision before the document is written: "whichever **product prioritization
methods** are already being used should be tapped to identify what is in scope for the release."

This is an important sequencing point. **Scope is an output of prioritization, not an input to
it.** See [../05-planning/prioritization.md](../05-planning/prioritization.md).

## Stakeholder input on scope

[S044] (Nielsen Norman Group) includes a stakeholder survey question that is unusually direct and
worth adopting:

> **"What is definitely not in scope for this project?"**

Asking stakeholders explicitly for exclusions — rather than only for requirements — surfaces
boundary disagreements at the start rather than at delivery. The same survey asks "What is the
problem that this effort is designed to solve?" and "What outcome(s) would lead you to describe
this effort as a success/failure?", which together bound the work from both ends.

See [../02-discovery/surveys.md](../02-discovery/surveys.md).

## Scope change during execution

[S097] describes scope change as a **joint decision** between roles, not a unilateral one:

> "**Plan for scope changes together.** When requirements shift or new information emerges, both
> managers should collaborate on assessing the impact. **Product managers evaluate how changes
> affect user value and business goals, while project managers assess timeline and resource
> implications.** Joint decision-making leads to better outcomes than isolated choices."

[S020] (project monitoring) treats scope as something actively monitored during delivery —
"Monitoring Project Scope" is a named element of the monitoring and control process. See
[../07-execution/project-monitoring-and-control.md](../07-execution/project-monitoring-and-control.md).

## The agile tension

The corpus contains an unresolved tension about how firmly scope should be fixed.

**The case for firm scope** — [S084] on the PRD handoff: "The goal is to have a PRD thorough and
comprehensive enough so there are **no surprises later on.** Once there is an agreement that the
PRD has reached that stage, it is then passed onto other teams."

**The case against** — [S138], from the same kind of source: "Remember, **be Agile in your
evolution of requirements for a project. It's okay to change user stories as the team builds,
ships, and gets feedback.**"

And [S138]'s anti-pattern list names fixed scope as a failure: *"Thorough review and iron-clad
sign-off from all teams are required before work even starts"* and *"Requirements are never
updated in the first place (because everyone signed off on them, remember?)"*

### How to read this
These are not contradictory positions about the same situation — they describe **different
contract structures**. Where an external client, regulator, or fixed budget defines the
obligation ([S086]'s agency and regulated-industry cases), scope stability has real value. Where
the team owns the outcome and can learn from what it ships, fixed scope trades away the main
benefit of iterating.

> **The decision variable is not methodology, it is who bears the cost of being wrong.**
> This inference is consistent with the corpus but is not stated by any single source.

## Scope and the "definition of done" for a release

[S048] connects scope to release criteria: after limiting scope and listing features, "identify
the criteria that will determine whether your product is customer-ready." Scope says *what is
included*; release criteria say *how good it must be to ship*. Both are needed; neither
substitutes for the other.

See [acceptance-criteria.md](acceptance-criteria.md) and
[../05-planning/release-planning.md](../05-planning/release-planning.md).

## Limitations

- **"Scope creep" is named but never analysed.** [S048] defines it in a clause and no source in
  the corpus discusses its causes, early warning signs, or how to handle a legitimate mid-flight
  scope increase. There is no treatment of change control, change request processes, or scope
  baselines.
- **No coverage of scope estimation or the scope/time/cost triangle**, despite the corpus
  containing project-management sources.
- **No guidance on decomposing scope** into releases — i.e. how to decide what belongs in v1
  versus later. This is closely related to the missing MVP material noted in
  [../02-discovery/discovery-frameworks.md](../02-discovery/discovery-frameworks.md).
- This document is assembled entirely from sections of PRD-focused sources. **No source in the
  corpus is about scope.** Its confidence rating reflects that.

## Related concepts

- [prd.md](prd.md) — Scope and Features Out as PRD sections
- [requirements.md](requirements.md) — constraints and dependencies
- [epics-and-decomposition.md](epics-and-decomposition.md)
- [../05-planning/prioritization.md](../05-planning/prioritization.md) — where scope is decided
- [../05-planning/release-planning.md](../05-planning/release-planning.md)
- [../07-execution/project-monitoring-and-control.md](../07-execution/project-monitoring-and-control.md)
- [../10-risk/risk-management.md](../10-risk/risk-management.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S048 | Notion — *How to write a PRD in 7 simple steps* | Vendor blog | Scope definition and scope creep, release criteria link |
| S138 | Atlassian — *How to create a PRD* | Vendor guide | "What we're not doing" section, agile evolution of requirements, anti-patterns |
| S113 | Product School — *The Only PRD Template You Need* | Training-provider guide | "Features Out" with rationale |
| S086 | Aha! — *What product managers need to know about PRDs* | Vendor guide | Scope as current vs future priority |
| S097 | Atlassian — *Product manager vs. project manager* | Vendor guide | Joint scope-change decisions |
| S044 | Nielsen Norman Group — *How to Run Surveys at Every Stage of the Design Cycle* | UX research organization | Stakeholder question on out-of-scope |
