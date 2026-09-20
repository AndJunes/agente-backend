---
skill: plan-roadmap
domain: planning
purpose: Build a roadmap in a chosen format, around outcomes where possible
trigger:
  - we need a roadmap
  - what is coming next quarter
inputs:
  - priorities
  - the audience
  - the outcome sought
draws_on:
  - 05-planning/roadmaps.md
  - 05-planning/outcome-based-roadmaps.md
  - 05-planning/roadmap-formats.md
  - 05-planning/continuous-roadmapping.md
refuses:
  - dates presented as commitments
  - a roadmap as a release plan
outputs: a roadmap in a named format
confidence: high
---

## When

After prioritisation, and after `disambiguate-artifact` has confirmed a roadmap is what is
wanted.

## Method

1. **Identify the audience.** `roadmaps.md` treats audience as the thing that determines
   format, and applies an *admission filter*: what earns a place on it.
2. **Prefer outcomes to features.** The four-step transition in
   `outcome-based-roadmaps.md` is explicit: set one outcome-based goal for the next three
   months → use the outcome to determine the features → build the outcome-based roadmap →
   review the approach after three months. The document also states when outcome-based
   roadmaps do not fit.
3. **Choose a format**: timeline, Now-Next-Later, Kanban, agile, theme-based.
4. Where the roadmap is continuously revised rather than re-planned, use
   `continuous-roadmapping.md`.

## Output

A roadmap with its format, audience and admission filter stated.

## What this cannot claim

Dates. Estimation is a declared gap — see `estimate`.
