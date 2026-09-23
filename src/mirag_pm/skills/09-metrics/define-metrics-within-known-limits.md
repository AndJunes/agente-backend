---
skill: define-metrics-within-known-limits
domain: metrics
purpose: Say what the corpus defines about metrics, and refuse to design a measurement set
trigger:
  - what should we measure
  - north star metric
  - AARRR
  - define success
inputs:
  - the outcome sought
draws_on:
  - 09-metrics/product-metrics.md
  - 09-metrics/pirate-metrics.md
  - 09-metrics/north-star-metric.md
refuses:
  - designing a metric set
  - a target value
  - a North Star Metric for a product
outputs: definitions, plus an explicit refusal of the design question
confidence: high
---

## When

Any measurement question. **This skill is mostly a boundary.** Metrics and MVP are the two
❌ gaps in this knowledge base; the corpus had two substantive sources on measurement and
says so rather than padding.

## Method

1. Give the definitions that exist: product metrics, and the AARRR / RARRA framing from
   `pirate-metrics.md`.
2. **On the North Star Metric, say what the document says about itself**: four sources
   reference it and none defines it. It is a gap register wearing a concept document's
   frontmatter, and its four safe claims are too thin to design from.
3. Hand the rest to `refuse-with-structure`, with `RESEARCH_BACKLOG.md` §1.3 as what would
   close it.

## Output

What is defined, and a structured refusal of what is not.

## What this cannot claim

How to choose a metric, what value to target, or whether a metric is a good one. Answering
those from model memory is the exact failure the gap register exists to prevent.
