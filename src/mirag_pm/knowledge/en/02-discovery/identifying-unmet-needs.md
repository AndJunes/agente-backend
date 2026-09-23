---
title: Identifying Unmet Customer Needs
domain: discovery
type: technique
topics:
  - unmet needs
  - latent needs
  - customer journey mapping
  - voice of the customer
  - silent churn
  - pain points
  - triggers barriers drivers
source_count: 3
sources: [S009, S054, S041]
evidence_type: practitioner-opinion
confidence: low
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Identifying Unmet Customer Needs

## Confidence warning

The primary source for this topic, [S009], is a **marketing-agency blog post** written by an
agency CEO, containing unsourced statistics and promoting the agency's own proprietary
frameworks. Its *techniques* are conventional and overlap with better-sourced material
elsewhere in this knowledge base; its *claims* are not reliable. This document preserves the
techniques and explicitly quarantines the claims.

## The premise

[S009]: "Meeting a customer need is the baseline. It keeps you in the game — but it won't
guarantee you win it. You can deliver exactly what you promised and still see customers drift
away... because there are other, quieter needs shaping their decisions and they're going
unmet."

The concept named for this is **silent churn** — customers leaving without complaining.

### Two claims that must not be repeated as fact

> [S009]: "more than 90% of unhappy customers never complain."
> **Classification: UNVERIFIED.** No source given. Do not cite.

> [S009]: "Poor customer experiences cost businesses up to $3.8 trillion globally. (Decisions
> Studio)"
> **Classification: UNVERIFIED.** The attribution is to an entity the corpus cannot identify;
> no methodology or year is given. Do not cite.

## Six approaches

[S009]'s list, with the substance retained and the promotion removed.

### 1. Examine disruption factors
Understanding what is shifting in the operating landscape, on the grounds that shifts create
unmet needs. The disruptions it names: "Customers taking control of their experiences; the
democratisation of knowledge; the rise of entrepreneurs and solopreneurs; increased compliance
burdens."

> **Temporal caution.** This list is a point-in-time observation (post-2025). Treat as an
> example of the *category* of analysis, not as a current list of disruptions.

### 2. Adopt lean principles
[S009] summarises Lean as "maximise the value customers are willing to pay for and eliminate
waste," and names four enablers using their Japanese terms:

| Term | [S009]'s gloss |
|---|---|
| **Jidoka** | "Make errors visible so they can be fixed fast" |
| **Genchi Genbutsu** *(rendered "Gensu Genbutsu" in the source)* | "Go to the source of the problem and solve it systemically" |
| **Muda** | "Eliminate all forms of waste" |
| **Kaizen** | "Commit to continuous improvement" |

It then gives a five-step experimental loop:
1. **Smart hypothesis** — define what you believe to be true
2. **Data-driven benchmarking** — set clear expectations and measure along the way
3. **Test by building** — "move beyond theory and gather real-world responses"
4. **Measure** — capture both qualitative and quantitative data
5. **Reflect** — validate or challenge the hypothesis, then adjust

The connecting argument: "Unmet needs often signal wasted interactions and opportunities."

> The source misspells one Lean term and gives no citation to Lean literature. The loop is
> recognisably a build-measure-learn variant. See
> [discovery-frameworks.md](discovery-frameworks.md) for Lean Startup as reported elsewhere in
> the corpus, and note that the corpus contains **no primary Lean or Toyota Production System
> source.**

### 3. Map the customer journey
"Identify pain points by mapping their journey — every touchpoint from first interaction to
loyal repeat purchase."

What a journey map helps you see [S009]:
- Bottlenecks that kill conversions
- Drop-off moments
- Where engagement drops or confusion creeps in

[S028] independently names user-journey maps as a discovery output and mapping workshops as a
discovery activity, which corroborates the technique if not this source's treatment of it.

### 4. Mine existing customer data
"Your own data is a goldmine. Analyse your existing support records, sales notes, and customer
interactions" — call logs, chat histories, reviews, surveys, social media.

[S009] gives a four-part coding scheme for what to look for, which is the most reusable element
of the article:

| Dimension | Question [S009] |
|---|---|
| **Triggers** | "How does the change fit into their lives? When and where are they thinking about it?" |
| **Pain points** | "What frustrates them? What do they dread doing?" |
| **Drivers** | "What motivates their decisions?" |
| **Barriers** | "What fears or misconceptions hold them back?" |

> Note the strong correspondence to JTBD's four progress-making forces — triggers/push,
> drivers/pull, barriers/anxiety. See [jobs-to-be-done.md](jobs-to-be-done.md), which grounds
> the same structure in a better-documented framework.

### 5. Voice of the Customer (VoC)
"The most reliable way to understand your customers? Ask them." VoC programs and surveys are
said to help you "improve existing services for higher satisfaction; spot emerging trends
before competitors; validate whether a new product will land well."

Questions suggested: "What's the biggest issue with [product/service]?" · "How satisfied are you
with our service?" · "How could we do things differently?" · "What products or features would
you like to see next?"

> **Contested.** The claim that asking is "the most reliable way" contradicts better-sourced
> material in this knowledge base. [S045] quotes Margaret Mead that what people say and do
> differ; [S074] gives the Netflix DVD case where customer requests did not predict behaviour;
> [S105] warns that surveys are the most misused research method. The last question above —
> "What features would you like to see next?" — is precisely the kind of solution-asking that
> [S110] and [S054] both caution against. **Treat VoC as one attitudinal input, not as ground
> truth.** See [user-research-methods.md](user-research-methods.md).

### 6. Competitive analysis
[S009]: "Competition isn't just businesses selling the same product. It's also new market
entrants, trends, and innovations that could reshape expectations overnight."

Questions to identify opportunities:
- Which needs are competitors failing to meet?
- What features are missing in the market?
- Are there underserved segments you can target?

A quality test is offered for the resulting idea: **"relevant, differentiated, and worth paying
for."**

*(The source's named "Clear Opportunity Question Set" framework is a proprietary agency
offering with no published definition; only the three questions above are usable.)*

## The underlying insight worth keeping

[S009]'s closing observation is the article's strongest contribution, and it is consistent with
better-sourced material:

> "The best innovations come from paying close attention to the problems customers can't
> articulate — yet."

This is the same premise that motivates ethnographic observation ([ethnographic-research.md](ethnographic-research.md))
and JTBD interviewing ([jobs-to-be-done.md](jobs-to-be-done.md)): **unmet needs are, by
definition, the ones customers are not asking you for.** That is why methods that rely on
asking are structurally weak at finding them.

## Better-grounded routes to the same goal

Because [S009] is weakly sourced, an agent should prefer these corpus-supported paths to
identifying unmet needs:

| Route | Where | Why it suits unmet needs |
|---|---|---|
| **JTBD interviews** | [jobs-to-be-done.md](jobs-to-be-done.md) | Explicitly designed to surface struggling moments and unmet jobs; Intercom case is an unmet-need discovery |
| **Ethnographic observation** | [ethnographic-research.md](ethnographic-research.md) | Inductive; "identify unexpected issues that you might not have encountered in a usability test" |
| **Exploratory discovery research** | [product-discovery.md](product-discovery.md) | Generative by design; "generates new, open-ended insights" |
| **Competitor-customer surveys** | [surveys.md](surveys.md) | NN/g-documented method targeting competitors' users to find gaps |
| **Customer review mining** | [opportunity-assessment.md](opportunity-assessment.md) | G2/Trustpilot/Capterra for "recurring user complaints, gaps in current offerings, and unmet expectations" |

## Related concepts

- [jobs-to-be-done.md](jobs-to-be-done.md)
- [ethnographic-research.md](ethnographic-research.md)
- [product-discovery.md](product-discovery.md)
- [opportunity-assessment.md](opportunity-assessment.md)
- [../03-market-intelligence/market-needs.md](../03-market-intelligence/market-needs.md)
- [../04-strategy/value-proposition.md](../04-strategy/value-proposition.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S009 | Step Change (Ashton Bishop) — *6 Ways to Identify Unmet Customer Needs*, 28 Aug 2025 | Marketing-agency blog; **low reliability** | Six approaches, triggers/pain/drivers/barriers scheme, silent-churn premise. Statistics quarantined as unverified |
| S054 | Mind the Product — *Jobs to be done for Product Managers* | Practitioner essay | Corroborating structure for unmet-need discovery |
| S041 | UXtweak — *How to Identify Market Needs and Create Products to Meet Them* | Vendor guide | Market-needs framing (see market-needs.md) |
