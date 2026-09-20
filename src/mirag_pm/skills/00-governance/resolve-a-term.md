---
skill: resolve-a-term
domain: governance
purpose: Answer a terminology question by exact lookup instead of retrieval
trigger:
  - what does X mean
  - define X
  - which document covers X
inputs:
  - the term
draws_on:
  - GLOSSARY.md
  - INDEX.md
refuses:
  - a definition assembled from passing mentions
outputs: the definition or the document, with its citation
confidence: high
---

## When

Before retrieval, on any terminology question. These two files are tables, and a table
answers by lookup rather than by similarity.

## Method

1. `GLOSSARY.md` for the definition.
2. `INDEX.md` for which document owns the concept — **633 terms** mapped, in three sections:
   quick answers, concept → document per domain, and a flat alphabetical lookup. Its gap
   markers ⚠ and ❌ are inline, so the index says when the answer is missing.
3. Only then retrieve, and retrieve the named document.

## Output

The definition or the document, cited.

## What this cannot claim

A definition the glossary does not carry. Assembling one from three passing mentions is the
behaviour the corpus rules out by name.
