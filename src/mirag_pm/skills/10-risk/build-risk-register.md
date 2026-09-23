---
skill: build-risk-register
domain: risk
purpose: Identify and record risks, including the ones that are opportunities
trigger:
  - what could go wrong
  - risk register
  - before committing to a plan
inputs:
  - the plan or the work in question
draws_on:
  - 10-risk/risk-management.md
  - 10-risk/risk-identification.md
  - 10-risk/risk-assessment.md
refuses:
  - a probability figure presented as measured
  - a risk threshold
outputs: a register with each risk assessed
confidence: high
---

## When

During planning, and repeatedly after. This is the corpus's only standards-aligned material
(PMI), which makes it unusually solid.

## Method

1. **Take the PMI definition**, which includes **opportunity**: a risk is an uncertain event
   with a positive *or* negative effect. A register with only threats is half a register.
2. Identify against the six-stage lifecycle and the tools in `risk-identification.md`, and
   check yourself against its **ten barriers** to identification — they explain most of what
   a team fails to see.
3. Assess with probability × impact, and record the **data quality** behind each estimate.
   `risk-assessment.md` treats that as part of the assessment, not a footnote.
4. Route responses to `select-risk-response`.

## Output

A register: risk, category, probability, impact, data quality, owner.

## What this cannot claim

That the probabilities are measured. They are judgments; recording their data quality is what
keeps that visible.
