---
skill: label-provenance
domain: governance
purpose: Keep the four provenance levels apart in the answer, not only in the metadata
trigger:
  - any answer drawing on a document with a provenance block
  - any question of the form "does this work" or "what does X say"
inputs:
  - the documents the answer draws on
outputs: an answer where each claim carries the kind of backing it has
draws_on:
  - SOURCES.md
  - 13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md
refuses:
  - presenting perceived productivity as measured productivity
  - treating a primary text as correct on a question its author never addressed
confidence: high
---

## When

On every answer that mixes what a framework says with what people do with it. The corpus
calls conflating these *"the most likely way to mislead a user in this knowledge base."*

## Method

Separate, in the answer itself:

- **primary** — what the creator or the standard actually said. `[E001]` the Scrum Guide,
  `[E002]` the Agile principles, `[E004]` the Kanban Method, EARS.
- **interpretation** — what a later reading says. Most of the `[Snnn]` register.
- **practice** — what is currently done in the field.
- **empirical** — what has actually been measured. Rare, and worth naming when present.

Two rules that follow from the register itself:

**An empty `empirical` list is information.** It says nobody has measured this. Say so rather
than filling the space with practice.

**Tier is not truth.** A primary source is more *traceable*, not automatically more correct —
and on a question its author never addressed, it is not a source at all.

**Never present perceived productivity as measured productivity.** `[E006]` measured the two
pointing in opposite directions: developers believed they were faster and were slower. The
corpus flags this as generalising well beyond AI tooling.

**Where an external source has been qualified by its own authors, say so.** `[E006]` is the
standing example.

## Output

An answer whose claims are individually attributable to a kind of evidence.

## What this cannot claim

That a claim with good provenance is therefore true, or that one without it is false. This
labels the backing; it does not adjudicate.
