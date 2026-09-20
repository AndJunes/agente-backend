---
skill: disambiguate-artifact
domain: foundations
purpose: Work out which planning artifact is actually being asked about before answering
trigger:
  - a question that says roadmap, backlog or release plan interchangeably
inputs:
  - the question as asked
draws_on:
  - 05-planning/roadmap-vs-backlog-vs-release-plan.md
refuses:
  - answering a roadmap question with backlog material or the reverse
outputs: the artifact identified, and the distinction made explicit
confidence: high
---

## When

Before any planning skill runs. The three are routinely conflated and the corpus has a
document whose whole purpose is separating them.

## Method

1. Read which of the three the question's *content* is about, not which word it used.
2. Where genuinely ambiguous, ask. `disputed-information.md` §8 rule 4 is explicit: when a
   term is ambiguous, ask which sense is meant before answering.
3. Name the distinction in the answer, so the next question is asked more precisely.

## Output

The artifact, named, and the hand-off to the skill that owns it.

## What this cannot claim

That the distinction is universally observed. It is a useful separation, not a standard.
