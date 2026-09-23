---
skill: prioritize
domain: planning
purpose: Rank candidates with a named framework, and say what the ranking hides
trigger:
  - what should we do first
  - RICE, Kano, MoSCoW, WSJF
  - prioritise the backlog
inputs:
  - the candidates
  - whatever evidence of value exists
draws_on:
  - 05-planning/prioritization.md
  - 05-planning/prioritization-frameworks.md
refuses:
  - a score presented as objective
  - inventing the inputs a formula needs
outputs: a ranking, with the framework named and its failure mode stated
confidence: high
---

## When

Whenever more is proposed than can be built. The corpus treats prioritisation as a practice
with well-documented failure modes, not as a formula.

## Method

1. **Name the framework and why it fits**: RICE, Kano, MoSCoW, value/effort, opportunity
   scoring, cost of delay, weighted scoring are all in the catalogue with their formulas.
2. **Say where each number came from.** A RICE score built on invented reach and confidence
   is arithmetic performed on guesses, and it launders them into a decision.
3. Read the failure modes in `prioritization.md` and check the ranking against them.
4. Scope follows from this — `define-scope` consumes the ranking, not the other way round.

## Output

A ranking, the framework, the inputs and where they came from.

## What this cannot claim

That the score is objective. Every framework here converts judgments into numbers; the
numbers do not make the judgments better, only more legible.
