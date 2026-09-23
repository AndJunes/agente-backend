---
skill: define-acceptance-for-agent-work
domain: ai-collaboration
purpose: Define what counts as done when the implementer is an agent
trigger:
  - how do we know the agent did it right
  - evals
  - acceptance criteria for AI work
inputs:
  - the specification
draws_on:
  - 13-ai-agent-collaboration/evals-and-acceptance-for-agents.md
refuses:
  - a pass rate that implies reliability
  - conflating pass@k with pass^k
outputs: acceptance criteria with the grader and the sampling stated
confidence: high
---

## When

With every specification handed to an agent. **This is the agent's own self-governance
applied to its counterpart.**

## Method

1. State what is being measured and by which **grader type** — the document distinguishes
   them and they are not interchangeable.
2. **Distinguish `pass@k` from `pass^k`.** One asks whether any of k attempts succeeded; the
   other whether all did. They answer opposite questions, and reporting the first while
   implying the second is the most common way an evaluation misleads.
3. Define acceptance before the work, not after seeing the output.

## Output

Criteria, the grader, and the sampling regime.

## What this cannot claim

That a pass rate is a reliability figure. It is a measurement under the conditions of the
evaluation and nothing beyond them.
