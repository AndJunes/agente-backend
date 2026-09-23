---
skill: analyze-idea
domain: strategy
purpose: Turn a one-line idea into a brief that can be decided on
trigger:
  - I want to build X
  - the first thing a user says
inputs:
  - the idea, in the user's words
draws_on:
  - 04-strategy/product-strategy.md
  - 04-strategy/product-vision.md
refuses:
  - proposing a solution before the questions are answered
outputs: an interpretation, and the questions that must be answered before planning
confidence: high
---

## When

The entry point. This is the first of the three operations CodeZard calls.

## Method

1. Restate the idea as understood, so the user can correct it before anything is built on it.
2. Apply the diagnostic from `product-strategy.md`: if the document answers *what we will
   build and when*, it is a plan, not a strategy. An idea usually arrives as neither.
3. Run `surface-and-rank-assumptions` over it.
4. Produce the questions that must be closed. Ask them rather than assuming them — this is
   what the questionnaire in the interface exists for.

## Output

An interpretation plus a short list of decisions that cannot be inferred from what was said.

## What this cannot claim

That the idea is good. Nothing at this stage supports that judgment.
