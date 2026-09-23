---
skill: reason-across-domains
domain: governance
purpose: Answer a question that needs more than one domain, along the corpus's own chains
trigger:
  - a question touching strategy and risk and planning at once
  - roadmap for an unvalidated problem with technical constraints
inputs:
  - the question
draws_on:
  - CONCEPT_GRAPH.md
  - TAXONOMY.md
refuses:
  - inventing a connection the graph does not carry
outputs: an answer that follows a stated reasoning chain
confidence: medium
---

## When

Multi-hop questions, where no single document answers.

## Method

1. Use `CONCEPT_GRAPH.md`'s reasoning chains — it carries a worked example for exactly
   *"roadmap for an unvalidated problem with technical constraints."*
2. Use `TAXONOMY.md` to know which domain owns which question, and to know that **Ideation
   and Risk deliberately cut across the flow**: ideation feeds both discovery and planning,
   and risk applies at every stage.
3. Say which chain you followed.

## Output

An answer with its path through the corpus shown.

## What this cannot claim

A connection the graph does not make. `[SYNTHESIS]` marks an inference this knowledge base
draws where no single source says it; anything weaker is `[INFERENCE]`, and both must be
labelled as such.
