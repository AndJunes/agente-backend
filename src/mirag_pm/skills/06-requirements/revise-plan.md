---
skill: revise-plan
domain: requirements
purpose: Produce the next version of a plan from a rejection, without losing the last one
trigger:
  - this plan is wrong because…
  - change the plan
inputs:
  - the current plan
  - the feedback in the user's words
draws_on:
  - 06-requirements/prd.md
  - 06-requirements/scope-definition.md
refuses:
  - editing the approved version in place
outputs: a new version, carrying what changed and why
confidence: high
---

## When

The third of the three operations CodeZard calls.

## Method

1. **Never mutate the previous version.** `prd.md`'s change-history component asks for *"who
   changed it, when they changed it, and what they changed"*; a revision that overwrites its
   predecessor destroys the record the document is supposed to keep.
2. Read the feedback as a constraint, not as an instruction to append. Rejections often
   invalidate a decision made earlier in the document.
3. Re-run `define-scope` if the change moves the line.
4. Quote the feedback in the new version, so the reason for the change survives the
   conversation that produced it.

## Output

Version n+1, with a reference to n and the feedback that caused it.

## What this cannot claim

That the revision is now correct. It is a response to one objection.
