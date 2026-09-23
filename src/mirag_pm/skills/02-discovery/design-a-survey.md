---
skill: design-a-survey
domain: discovery
purpose: Decide whether to run a survey at all, and only then design one
trigger:
  - let us send a survey
  - we need quantitative data
inputs:
  - the question
  - a method decision
draws_on:
  - 02-discovery/surveys.md
refuses:
  - question wording
  - significance thresholds
  - treating voice-of-customer as ground truth
outputs: a survey, or a documented decision not to run one
confidence: high
---

## When

The corpus's contribution here is mostly a gate. `surveys.md` includes **when not to run
one**, and two NN/g sources treat surveys as the hardest method to do well and the most
frequently misapplied — against one source presenting them as yielding statistically
significant insight. Carry the gate, not the enthusiasm.

## Method

1. Check the skip conditions first.
2. If it survives, design against a stated research question.
3. Treat voice-of-customer as **one attitudinal input, not ground truth**. The specific
   question *"what features would you like to see next?"* is flagged as exactly the
   solution-asking two sources caution against.

## Output

A survey, or a decision not to run one with the reason.

## What this cannot claim

Question wording, sampling design or significance criteria. All recorded gaps.
