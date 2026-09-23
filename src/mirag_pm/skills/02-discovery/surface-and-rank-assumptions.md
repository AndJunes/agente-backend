---
skill: surface-and-rank-assumptions
domain: discovery
purpose: Turn a plan into the list of things it assumes, ranked by what would hurt most if false
trigger:
  - what could make this wrong
  - what should we test first
  - before committing to a plan
inputs:
  - the idea or plan as stated
draws_on:
  - 02-discovery/hypotheses-and-assumptions.md
refuses:
  - a confidence percentage
  - a hypothesis template presented as prescribed
  - experiment design parameters
outputs: a ranked assumption list, each with the question that would test it
confidence: high
---

## When

This is the spine of the discovery domain and should run before almost anything else.
`hypotheses-and-assumptions.md` is the only document that draws the full chain —
**assumption → question → method → evidence** — and every method document plugs into it as a
leaf.

## Method

1. Extract what the plan takes for granted: about the user, the problem, the solution, the
   business, and what is technically possible.
2. For each, ask what would have to be true.
3. Rank by *consequence if false × how little is known*, not by how easy it is to test.
4. Attach the question that would test it, and hand that question to
   `choose-a-research-method`.

## Output

A ranked list of assumptions, each with a testable question.

## What this cannot claim

**How well it has been tested.** The chain terminates in a judgment this corpus cannot
support: it says what to test and never how much evidence is enough. It also has no
hypothesis statement template and no experiment design parameters — both are recorded gaps.
