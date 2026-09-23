---
skill: set-flow-and-batch-policy
domain: execution
purpose: Decide the work-in-progress and batch policy for a team
trigger:
  - everything is in progress and nothing is finished
  - WIP limits
  - Kanban
inputs:
  - current work in flight
  - how work arrives
draws_on:
  - 07-execution/kanban.md
  - 07-execution/project-monitoring-and-control.md
refuses:
  - a WIP number
  - earned-value calculations
outputs: an explicit flow policy
confidence: medium
---

## When

When throughput is the complaint rather than direction.

## Method

1. Make the current policy explicit — most teams have one and have never written it down.
2. Apply the Kanban Method from its primary text: visualise, limit work in progress, make
   policies explicit, improve by agreement.
3. Monitor per `project-monitoring-and-control.md`.

## Output

A written flow policy.

## What this cannot claim

A WIP limit. And **not the earned-value metrics** — EV, PV, SV, CV, EAC, ETC, TCPI appear in
`risk-monitoring.md` named and never explained, with an explicit prohibition on computing
them. They are vocabulary, not a capability.
