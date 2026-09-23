---
skill: classify-assumption-constraint-dependency
domain: risk
purpose: Tell apart three things that get written in the same list and behave differently
trigger:
  - is this an assumption or a constraint
  - our assumptions list
inputs:
  - the list as written
draws_on:
  - 10-risk/assumptions-and-constraints.md
refuses:
  - treating a constraint as testable
outputs: the items re-classified, with what each implies
confidence: high
---

## When

Before planning around any of them. Requirements documents habitually put all three under one
heading, and they demand different responses.

## Method

- **Assumption** — believed true, could be false, therefore **testable**. Goes to
  `surface-and-rank-assumptions`.
- **Constraint** — true whether you like it or not. Not testable; it bounds the solution.
- **Dependency** — someone else's work you need. Goes to `map-dependencies` and then the
  register.

Each is a risk source, which is why the document sits in this domain.

## Output

The list, re-sorted, each item routed.

## What this cannot claim

That the classification is stable. A constraint can turn out to have been an assumption, and
that discovery is usually expensive.
