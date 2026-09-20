---
skill: assess-it-and-security-risk
domain: risk
purpose: Assess security risk in its own vocabulary, which is not the project-risk vocabulary
trigger:
  - security risk
  - compliance
  - what are our security exposures
inputs:
  - the assets and the system boundary
draws_on:
  - 10-risk/it-and-security-risk.md
refuses:
  - implementing any control
  - authentication or authorisation design
  - mixing this vocabulary with probability/impact/response
outputs: an assessment in assets/threats/vulnerabilities/controls terms
confidence: high
---

## When

A security or compliance question, from a product manager's position.

## Method

**Use this vocabulary and only this vocabulary.** The document is explicit that security risk
*"uses a different vocabulary from project risk management — assets, threats, vulnerabilities,
controls rather than risks, probability, impact, responses."*

1. Inventory the assets.
2. Identify threats to them.
3. Identify the vulnerabilities the threats could use.
4. Name the controls, and who owns each.

## Output

An assessment in the four-part NIST-style structure.

## What this cannot claim

**How to implement anything.** This is a PM's compliance-facing assessment. Designing
authentication, choosing a library or writing a control is an engineering job, and answering
it from here would be this agent reaching into the other one's subject.
