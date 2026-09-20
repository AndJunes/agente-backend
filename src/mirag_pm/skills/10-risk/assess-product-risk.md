---
skill: assess-product-risk
domain: risk
purpose: Assess risk in the product sense, which is not project risk
trigger:
  - is this product risky
  - will anyone want it
inputs:
  - the product or feature
draws_on:
  - 10-risk/product-risk.md
refuses:
  - conflating product risk with project risk
outputs: an assessment against the product-risk taxonomy
confidence: medium
---

## When

On the product, not on the plan to build it. The corpus separates the two precisely because
they are *"routinely conflated"*.

## Method

Work the **16-item product-risk taxonomy**: value, usability, feasibility, viability and the
rest. Feed what it surfaces back into `surface-and-rank-assumptions` — a product risk is an
assumption that has not been tested.

## Output

An assessment across the taxonomy.

## What this cannot claim

The corpus's definitions separating product, project and business risk **did not fully
extract**. Use the taxonomy; do not lean on the definitions.
