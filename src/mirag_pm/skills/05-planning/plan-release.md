---
skill: plan-release
domain: planning
purpose: Plan a release with the little the corpus supports, and say what is missing
trigger:
  - when can we ship
  - release plan
inputs:
  - scope
  - dependencies
draws_on:
  - 05-planning/release-planning.md
refuses:
  - a date
  - a release cadence recommendation
outputs: a release plan, heavily qualified
confidence: medium
---

## When

Rarely, and carefully. `release-planning.md` is `confidence: low` and its principal source is
weak — the corpus says to read such documents as maps of what is missing.

## Method

1. Confirm via `disambiguate-artifact` that a release plan, not a roadmap, is wanted.
2. Use what the document supports: what a release plan is and how it differs from the other
   two artifacts.
3. Declare the gap prominently, and hand dates to `estimate`, which will refuse them.

## Output

A release plan with its unknowns as prominent as its content.

## What this cannot claim

Nearly everything usually wanted here. Treat this as a documented gap rather than an answer.
