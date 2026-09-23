---
title: Assumptions and Constraints as Risk Sources
domain: risk
type: concept
topics:
  - assumptions
  - constraints
  - assumption log
  - assumption analysis
  - unconscious assumptions
source_count: 4
sources: [S100, S084, S087, S028]
evidence_type: standards-aligned
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Assumptions and Constraints as Risk Sources

## Why assumptions belong in a risk chapter

Assumptions are the **most common hidden source of risk** across every source in the corpus that
addresses the topic. They appear in three different traditions, all reaching the same conclusion:

| Tradition | Source | Statement |
|---|---|---|
| **Project management (PMI)** | [S100] | "**Whether your assumptions are conscious or unconscious, every assumption has the potential to be wrong or inaccurate.**" *Too many assumptions* is listed as one of ten barriers to risk identification |
| **Product management** | [S087] | "Product risk is easy to ignore because **it hides in assumptions**, deadlines, product roadmaps, and even in team dynamics" |
| **UX / discovery** | [S028] | Assumption-mapping workshops exist to "question the validity of certain '**facts**' and identify the deep-rooted assumptions that need further exploration" |

> The convergence is the point: **three disciplines that share almost no vocabulary independently
> identify unexamined assumptions as the primary latent risk.**

## Definitions

[S084] distinguishes the three terms precisely. They are routinely conflated and the distinction
determines what you can do about each:

| Term | Definition [S084] | What you do about it |
|---|---|---|
| **Assumption** | "Anything you **expect to be in place (yet isn't guaranteed)**" — e.g. "assuming that all users will have Internet connectivity" | **Validate it** — it may be false |
| **Constraint** | "Dictate something the eventual implementation **can't require**, be it a budgetary constraint or a technical one" | **Design within it** — it is a given |
| **Dependency** | "Any known condition or item the product **will rely on**" — e.g. "depending on Google Maps to add directions for a dog walking app" | **Track and manage it** — it is outside your control |

> A constraint is *known and binding*. An assumption is *believed and unverified*. Treating an
> assumption as a constraint stops you from testing it; treating a constraint as an assumption
> wastes effort trying to remove it.

## Assumption analysis

[S100] (PMI-aligned) names this as a distinct risk identification technique:

> "**One obstacle to assumptions analysis is trying to identify and analyze unconscious
> assumptions.** However, whether your assumptions are conscious or unconscious, **every assumption
> has the potential to be wrong or inaccurate.**
>
> Investing some effort in assumptions analysis is a useful way to **determine if your assumptions
> are valid and avoid some potentially significant project risks** as a result. **Challenge your
> assumptions and analyze any potential risks they could cause.**"

[S125] lists "assumption analysis" among standard risk identification techniques and suggests
running it as a dedicated session: "reviewing a checklist in one of their regular meetings and
**going over assumptions in another meeting.**"

### The assumption log
[S100] lists the **assumption log** among project document inputs to risk identification, alongside
the issue log. The corpus does not describe its structure.

> The existence of a standing artefact matters more than its format: assumptions surfaced in one
> meeting and not recorded are re-assumed in the next.

## Where assumptions get recorded

| Artefact | Treatment |
|---|---|
| **PRD** | [S084]: assumptions, constraints and dependencies are "the final batch of ingredients for a PRD." [S086] requires "anything that might impact product development positively or negatively — **along with how you will validate this**" |
| **Assumption log** | [S100], as an input to risk identification |
| **Assumption map** | [S087], [S028] — plotted by importance and uncertainty. See [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md) |
| **Risk register** | Where validated-as-risky assumptions become tracked risks |

> [S086]'s requirement is the one to adopt: **record the assumption *and* how you will validate
> it.** An assumption listed without a validation plan is documentation, not risk management.

## Prioritising which assumptions to test

Both the project and product traditions converge on the same rule.

[S028] (discovery): "prioritizing assumptions in terms of **risk to the project's outcome. The
riskiest assumptions should be prioritized in terms of research activities.**"

[S087] (product): "Assumptions that are **both critical and uncertain** become top priorities for
validation."

See [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)
for the assumption map and risk/evidence grid.

## Constraints

The corpus treats constraints more thinly than assumptions.

Named categories, assembled across sources:

| Constraint type | Source |
|---|---|
| **Budgetary** | [S084] |
| **Technical** | [S084]; [S081] — "infrastructure, tech stack, and available tools... scalability, performance, reliability, and maintenance requirements" |
| **Regulatory and legal** | [S081]: "regulatory compliance, legal implications, and potential security or privacy concerns" |
| **Resource and capability** | [S081]: "budget requirements, timelines, personnel availability." [S087]: "team capability gaps" |
| **Time / fixed dates** | [S110]: "resources, time, and money are not limitless. **Sit down with people from different areas (design, engineering, marketing) and go through the hard limits**" |
| **Architecture** | [S094]: a product vision should give engineering "enough clarity about what's coming in the next several years so they can ensure they have in place **an architecture that can serve the need**" |

[S110] gives the only procedural advice: establish hard limits **collaboratively and early** —
"whether that be setting a launch date or allocating resources, **it's useful for everyone to know
what they've got to work with.**"

## A useful sorting question

Synthesised from [S110]'s discovery guidance, which divides worries into "**things you have control
over and things you don't**":

```
Is it certain?
  ├── Yes → is it within our control?
  │          ├── Yes → a decision we own
  │          └── No  → a CONSTRAINT: design within it
  └── No  → is it something we rely on?
             ├── Yes → a DEPENDENCY: track and manage
             └── No  → an ASSUMPTION: validate it, in order of
                        (importance × uncertainty)
```

> This tree is a reasoning aid assembled from the corpus, **not a model any single source states.**

## Limitations

- **No source in the corpus is about assumptions or constraints.** Everything here is assembled
  from sections of documents about risk identification, PRDs and discovery.
- **The assumption log is named but never described.**
- **No guidance on writing a good assumption statement** — there is no assumption equivalent of the
  risk-statement template in [risk-identification.md](risk-identification.md).
- **No treatment of the classic project-management triple constraint** (scope/time/cost), despite
  the corpus containing PMI-aligned sources.
- **No treatment of how constraints change** — a constraint lifted mid-project is a significant
  event that nothing in the corpus addresses.

## Related concepts

- [risk-identification.md](risk-identification.md) — assumption analysis as a technique
- [risk-management.md](risk-management.md)
- [product-risk.md](product-risk.md)
- [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)
- [../06-requirements/requirements.md](../06-requirements/requirements.md)
- [../06-requirements/prd.md](../06-requirements/prd.md)
- [../05-planning/dependencies.md](../05-planning/dependencies.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S100 | Project Management Academy — *Risk Identification in Project Management* | PMI Authorized Training Partner | Assumption analysis, unconscious assumptions, assumption log |
| S084 | ProductPlan — *Product Requirements Document* (Glossary) | Vendor glossary | Definitions of assumption, constraint, dependency |
| S087 | Product School — *Product Risk* | Training-provider guide | Assumptions as hidden product risk; importance × uncertainty |
| S028 | Nielsen Norman Group — *Discovery: Definition* | UX research organization | Assumption-mapping workshops; riskiest-assumption prioritization |
