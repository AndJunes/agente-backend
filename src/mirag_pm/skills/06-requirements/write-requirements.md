---
skill: write-requirements
domain: requirements
purpose: Produce the requirements document, and say what it deliberately does not specify
trigger:
  - write the PRD
  - turn this into a specification
  - we have an approved plan
inputs:
  - an approved problem statement, scope and constraints
draws_on:
  - 06-requirements/prd.md
  - 06-requirements/requirements.md
refuses:
  - dictating implementation
  - a data schema
  - a permissions matrix
outputs: a requirements document with an explicit open-questions section
confidence: high
---

## When

The second of the three operations CodeZard calls, and only after explicit approval.

## Method

1. **Decide whether a document is warranted at all.** `prd.md` carries the "is it obsolete?"
   debate and it is a real question, not a formality.
2. Work the consolidated component list: overview, objective, background and strategic fit,
   context and personas, user scenarios, requirements and features, non-functional
   requirements, system and environment requirements, usability requirements, assumptions,
   constraints, dependencies, open questions, change history.
3. Separate the four kinds from `requirements.md`: **functional, non-functional, assumptions,
   constraints**. Most documents carry only the first and call it complete.
4. **Write the open questions.** An empty list is a claim, and a false one in almost every
   case.

## Output

A requirements document. Each feature carries at minimum a description, a goal and a use
case.

## What this cannot claim

**How to build it.** The corpus is explicit: a PRD *"may not dictate a specific
implementation"* — *"PRD = what; functional specification = how."* A field list is a schema
and a permissions matrix is a design; both are the implementer's, not this document's.
