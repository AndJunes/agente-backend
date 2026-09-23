---
skill: decompose-epics
domain: requirements
purpose: Break something too big into pieces that can each be finished
trigger:
  - this is too big
  - epic
  - how do we split this
inputs:
  - the epic or large requirement
draws_on:
  - 06-requirements/epics-and-decomposition.md
refuses:
  - splitting by technical layer
  - sizing the pieces
outputs: a decomposition where each piece is independently completable
confidence: medium
---

## When

When an item cannot be finished within one iteration, or cannot be described without "and".

## Method

1. Split so each piece delivers something on its own. Splitting by layer — a back-end story
   and a front-end story — produces pieces that cannot be finished independently and that
   hide the coordination cost.
2. Re-check each piece through `write-backlog-items`.

## Output

Pieces, each independently completable.

## What this cannot claim

How big each piece is.
