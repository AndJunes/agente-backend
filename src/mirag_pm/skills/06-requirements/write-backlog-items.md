---
skill: write-backlog-items
domain: requirements
purpose: Write stories or job stories that are ready to be worked on
trigger:
  - write user stories
  - is this story ready
  - job story
inputs:
  - a requirement or a scoped feature
draws_on:
  - 06-requirements/user-stories.md
  - 06-requirements/job-stories.md
  - 06-requirements/acceptance-criteria.md
refuses:
  - the template as a ritual
  - sizing
outputs: items with acceptance criteria and a readiness check
confidence: high
---

## When

After requirements exist, per item.

## Method

1. **Choose the form.** User story when the persona matters, job story when the situation
   matters more than who is in it — `job-stories.md` says when to prefer them.
2. Use the template, and hold the corpus's own scepticism about it: it *"is helpful when it
   improves the conversation, but it should not become a ritual… the form matters less than
   whether the team can have the right conversation about the work."*
3. Remember card, conversation, confirmation — the story is a placeholder for a conversation,
   not a specification.
4. Write acceptance criteria per `acceptance-criteria.md`.
5. Run the **readiness checklist** before the item is taken into work. The corpus calls it
   *"directly actionable"*, which it says of very little.

## Output

Items with criteria, each passing the readiness check.

## What this cannot claim

A size. Sizing belongs to the gap `estimate` refuses.
