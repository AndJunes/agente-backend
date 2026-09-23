---
skill: map-dependencies
domain: planning
purpose: Identify what blocks what, and treat each dependency as a risk
trigger:
  - what is blocking this
  - we have cross-team dependencies
inputs:
  - the planned work and the teams involved
draws_on:
  - 05-planning/dependencies.md
refuses:
  - critical path analysis
  - scheduling
outputs: a dependency list, each entry routed into the risk register
confidence: medium
---

## When

During planning, before commitments are made on someone else's behalf.

## Method

1. List what this work needs from elsewhere.
2. **Convert each into a risk** and hand it to `build-risk-register`. A dependency with no
   owner and no response is a risk that has not been written down.
3. `dependencies.md` is a declared gap — say so rather than filling it.

## Output

A dependency list that feeds the risk register.

## What this cannot claim

Scheduling or critical-path analysis. Neither is in this corpus.
