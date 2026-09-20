---
skill: state-what-this-knowledge-is
domain: governance
purpose: Answer questions about the knowledge base itself, including how good it is
trigger:
  - what do you know
  - where did this come from
  - how reliable is this
  - what has changed
inputs:
  - the question about the corpus
draws_on:
  - README.md
  - TAXONOMY.md
  - CHANGELOG.md
  - CORPUS_AUDIT.md
refuses:
  - presenting the corpus as complete
outputs: a description with its weaknesses stated
confidence: high
---

## When

Any question about the agent's own knowledge — its scope, its provenance, its version.

## Method

1. State what it is: 143 corpus sources plus 14 externally researched, 88 documents over 13
   domains, 633 indexed terms, built September 2026, **v1.1.0**.
2. State what it is not: *"not a complete product-management reference. The corpus it came
   from is ~85% commercial content with significant blind spots."*
3. Give the honest strengths and weaknesses. **Strong**: discovery and user research,
   roadmaps, prioritisation, risk, user stories, role boundaries, Scrum and Kanban from their
   primary texts, and knowing what it does not know. **Weak**: metrics, MVP, product-market
   fit, pricing, technical debt, scaling frameworks, and **accessibility, which is absent
   entirely**.
4. For version questions use `CHANGELOG.md`; for how it was built, `CORPUS_AUDIT.md`.

## Output

A description that includes the blind spots.

## What this cannot claim

Completeness. The corpus's own README says no content anywhere in it comes from the model's
memory, and that rule extends to describing it.
