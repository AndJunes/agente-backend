---
skill: write-agent-executable-spec
domain: ai-collaboration
purpose: Write a specification an agent can implement without asking a follow-up question
trigger:
  - hand this to the implementer
  - spec-driven development
  - write the spec
inputs:
  - an approved requirements document
draws_on:
  - 13-ai-agent-collaboration/spec-driven-development.md
  - 13-ai-agent-collaboration/pm-with-ai-implementers.md
refuses:
  - that spec-driven development is proven
  - how to organise a multi-agent team
outputs: a specification fit for an implementer that cannot ask
confidence: medium
---

## When

At the hand-off from this agent to an implementer. **This is the bridge between the two
agents**, and the corpus's own framing is the right one: the artifact spec-driven development
makes central *"is the PRD, restated for a reader that cannot ask a follow-up question in the
hallway."*

## Method

1. Start from `write-requirements` output, not from the idea.
2. Remove everything that depends on shared context: an implementer that cannot ask will
   either guess or stop.
3. Make acceptance machine-checkable where possible — see `define-acceptance-for-agent-work`.
4. Keep the *what*/*how* line. The specification still does not dictate implementation.

## Output

A specification with no unstated dependencies on context.

## What this cannot claim

**That this works.** The document's own warning comes before its content: the practice *"has
no empirical evidence base in this knowledge base. Adoption is not efficacy."* And on
organising a multi-agent team the corpus has **nothing** — `pm-with-ai-implementers.md` is
`confidence: low` and mostly inference, and states that no claim in it may be presented as
established.
