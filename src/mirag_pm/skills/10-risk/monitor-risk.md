---
skill: monitor-risk
domain: risk
purpose: Keep the register alive after the plan is agreed
trigger:
  - we wrote a risk register months ago
  - how do we track risks
inputs:
  - an existing register
draws_on:
  - 10-risk/risk-monitoring.md
  - 07-execution/project-monitoring-and-control.md
refuses:
  - earned-value metrics (EV, PV, SV, CV, EAC, ETC, TCPI)
outputs: a monitoring cadence and triggers
confidence: medium
---

## When

After the register exists. A register written once is a document, not a control.

## Method

1. Set review points and the triggers that force an out-of-cycle review.
2. Track whether responses were carried out, not only whether risks materialised.
3. Watch for new risks; the register is not closed.

## Output

A cadence, triggers, and a record of what changed.

## What this cannot claim

The earned-value metric set. `risk-monitoring.md` names EV, PV, SV, CV, EAC, ETC and TCPI and
never explains them, with an explicit prohibition on computing them. They belong in a
glossary.
