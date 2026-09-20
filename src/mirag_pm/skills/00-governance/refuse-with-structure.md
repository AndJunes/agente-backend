---
skill: refuse-with-structure
domain: governance
purpose: Say the knowledge base does not answer this, in the way the corpus prescribes
trigger:
  - the question falls in a declared gap
  - retrieval returns only passing mentions
  - the question is one of the 24 open questions
inputs:
  - the question, and what retrieval did return
outputs: a refusal that is more useful than a guess
draws_on:
  - 13-ai-agent-collaboration/open-questions-ai-and-pm.md
  - RESEARCH_BACKLOG.md
  - CORPUS_AUDIT.md
refuses:
  - answering from model memory
  - a generic disclaimer in place of the specific absence
confidence: high
---

## When

Whenever the honest answer is that this knowledge base does not know. The corpus treats that
as a correct answer, not a failure: *"'This knowledge base does not cover X' is a correct and
useful answer. It is better than an answer assembled from three passing mentions."*

## Method

Three steps, from `open-questions-ai-and-pm.md`, and all three are required:

1. **State the specific absence.** Not "I don't have enough information" — *which* thing is
   missing, and why. "This corpus has two substantive sources on measurement, so it defines
   product metrics and does not support designing a metric set."
2. **Give whatever adjacent evidence exists, with its scope conditions attached.** Something
   nearby is usually retrievable. Hand it over with the boundary marked.
3. **Say what would settle it.** `RESEARCH_BACKLOG.md` tracks each gap and what would close
   it; where it names a source, name it too.

The standing gaps, as of v1.1.0: **MVP** and **metrics design** are ❌ — do not answer from
here. **Estimation** is 🟨 — answerable for what the frameworks prescribe (nothing) and for
probabilistic forecasting, not for story points, velocity or planning poker. **AI agents as
team members** is 🟨 — answerable for the evidence, the specification practice and the
evaluation, not for how to organise a multi-agent team. **Accessibility** is absent entirely.

## Output

A refusal with three parts. Never one sentence.

## What this cannot claim

Anything. That is the point. `open-questions-ai-and-pm.md` names its own danger: *"This is the
domain where an agent using this knowledge base is most likely to confabulate — the questions
are current, plausible-sounding answers are abundant online, and the corpus contains
nothing."* Model memory is not a source.
