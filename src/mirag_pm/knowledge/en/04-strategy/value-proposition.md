---
title: Value Proposition
domain: strategy
type: framework-catalogue
topics:
  - value proposition
  - crossing the chasm template
  - value proposition canvas
  - lean canvas
  - product vision board
  - Sean Ellis test
  - 40% rule
source_count: 3
sources: [S005, S036, S095]
evidence_type: practitioner-framework
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Value Proposition

## Definition

[S005]: "A product value proposition — also called a **customer value proposition** — is a concise
statement that communicates two things: **the benefits your product delivers to users, and why
they should choose you over the alternatives.**"

"In practical terms, it answers: **What problem does your product solve, for whom, and what makes
your approach better?**"

[S036] frames it from the customer's side: a value proposition should answer "**What is the
problem you're solving?**" and "**How will this solution benefit your customer?**"

## The dual use — and the failure mode

[S005] makes an argument that raises the value proposition above marketing copy:

> "When it's done well, it works both ways — **for customer-facing messaging and as an internal
> compass for product decisions.**"

> "**Many PMs write them once — and never look at them again. That's a mistake. Building without a
> product thesis leaves you making decisions based on whoever argues loudest, whether that's a CEO
> or an edge-case user who doesn't represent your target customer.**"

And its roadmap function: "A product value proposition **doubles as an internal reference for
roadmap decisions — especially if a new request threatens to pull the product away from its core
buyer.**"

> **This is the most decision-relevant claim about value propositions in the corpus:** a written,
> agreed value proposition is a *defence against arbitrary prioritization*. It gives the PM a
> stated basis for declining requests that serve someone other than the core customer — the same
> capability [S040] calls for in
> [../05-planning/outcome-based-roadmaps.md](../05-planning/outcome-based-roadmaps.md).

Its second internal use [S005]: "When you share your value proposition with developers and
designers, you give them the '**why**' behind what they're building. That context builds user
empathy."

## Relationship to product-market fit

[S005]: "**When your value proposition meets a real, underserved need, you have product-market
fit.**"

> This is stated as a definition but functions as an equivalence claim, and it is looser than it
> looks — see [product-market-fit.md](product-market-fit.md), where the corpus's PMF material is
> thin and inconsistent.

## Four models

[S005] compares four, and its comparison table is more useful than any individual description
because it shows what each **omits**:

| Model | Best for | Format | Covers competitors | Covers user pains/gains |
|---|---|---|---|---|
| **Crossing the Chasm** | "Concise internal alignment on product thesis" | Text template (one paragraph) | **Yes** | Partial — "need statement only" |
| **Pichler Canvas** | "Boardroom buy-in from execs and investors" | Visual canvas (business lens) | **Yes** | Partial — "needs, not split into pains/gains" |
| **Osterwalder Canvas** | "Deep customer understanding across use cases" | Two-sided visual canvas | **No** | **Yes** — "pains, gains, and jobs to be done" |
| **Lean Canvas** | Full picture in one document for executive review | Single canvas | Indirect — via "existing alternatives" | Via "top problems" |

---

### Crossing the Chasm template

**Template** [S005]:
> *For **[target customer]** who **[need statement]**, the **[product/brand name]** is a
> **[product category]** that **[key benefit]**. Unlike **[primary competitor alternatives]**,
> **[product/brand name]** **[primary differentiation statement]**.*

**Worked example** [S005]:
> *"For work teams who need a better workflow, Slack is a team communications tool that integrates
> apps and lets users search through files, calls, messages, and colleagues. Unlike Microsoft
> Teams, Slack has better options for third-party integrations and is easier to deploy."*

**How to use it** [S005]: "Your product, your users, your competitors — all in one paragraph. **Use
it as the summary after you've worked through one of the other models.**"

> Note the sequencing advice: this is a *compression* format, not a discovery format. Filling the
> blanks without prior customer work produces a well-formed sentence with no evidence behind it.

---

### Roman Pichler's extended Product Vision Board

**Lens** [S005]: "looks at the value proposition **from the business lens rather than the user
lens.**"

Questions it asks:
- "Is it technically **feasible** to build this product?"
- "How does it **benefit the company**?"
- "What are the product's **business goals**?"
- "How does it **generate revenue**?"
- "What are the **costs** to develop, market, sell, and support it?"

**Strength** [S005]: "Pichler's model **directly addresses competitors, which many canvases skip
entirely.**"

**Stated gap** [S005]: "it **doesn't separate user needs into pains and gains.** Specific pain
points can get lost in the broader 'needs' bucket."

---

### Alexander Osterwalder's Value Proposition Canvas

**Lens** [S005]: "the **most user-centric** model here... digs into customer **pains, gains, and
jobs to be done**, then maps those to your product's **pain relievers and gain creators.**"

**Structure** [S005]: "It visualizes alignment between **your product (left side)** and **your
target customer (right side)** by showing where the two overlap. **More overlap means you're
closer to product-market fit.**"

**Process** [S005]:
1. **Start with the customer profile on the right.** "List your user's everyday tasks and problems
   — **including emotional and social drivers, not just functional ones.**"
2. "Record the specific **frustrations** users run into while trying to complete those tasks,
   **including pain points from competing solutions. Rank by frequency and severity.**"
3. "Describe what customers **expect or want**: better performance, cost savings, social proof, or
   moments of delight."
4. **Then move to the value proposition side.** "Map your **pain relievers and gain creators** to
   the user's pains and gains."

**Stated gap** [S005]: "Osterwalder's canvas **doesn't address competitors directly. Pair it with
the Crossing the Chasm template to cover that gap.**"

> The pains/gains/jobs structure connects directly to
> [../02-discovery/jobs-to-be-done.md](../02-discovery/jobs-to-be-done.md) — and the instruction
> to include "emotional and social drivers" matches JTBD's functional/emotional/social dimensions.

---

### Ash Maurya's Lean Canvas

[S005]: "adapts the Business Model Canvas with added sections useful for stakeholder
presentations: **revenue streams, cost structure, and key metrics.** There's also a section for
'**existing alternatives**' — **how your users currently solve their problems, with or without
competitors** — which is an indirect but useful way to address the competitive space."

**The value proposition quadrant has two parts** [S005]:
1. "A single, clear, compelling message that states **why you're different and worth attention**"
2. "A **high-level concept explanation — your 'X for Y' analogy** (e.g., YouTube = Flickr for
   videos)"

**Why the layout matters** [S005]: "Place that next to your user's top problems and your competitor
alternatives **in the same canvas**, and it's easy to see whether your proposition actually
addresses those needs in a better way."

> The "existing alternatives" framing is the strongest of the four on competition, because it
> includes **non-consumption and workarounds** rather than only named competitors — consistent
> with [S054]'s JTBD claim that the real competitor is often the status quo. See
> [../03-market-intelligence/competitive-analysis.md](../03-market-intelligence/competitive-analysis.md).

---

## Validating a value proposition: the 40% test

[S005] presents a specific, falsifiable test:

> **Ask users: "How would you feel if you could no longer use this product?"**
> "**If 40% answer 'very disappointed' to your main benefit, you have the right product-market
> fit.**"

**Attribution** [S005]: "Benchmark popularized by **Sean Ellis**; also cited in **Croll &
Yoskovitz, *Lean Analytics*, O'Reilly, 2013**."

> This is one of the few places in the entire corpus where a **specific benchmark is given with a
> named originator and a book citation.** That is worth noting — but the citation is to a
> secondary source, and the corpus contains **no primary evidence for the 40% threshold's
> validity**. It is a widely used heuristic, not a measured constant. Treat it as "a commonly used
> threshold attributed to Sean Ellis," not as an established finding.

### What to do below 40%
[S005]: "adjust your product thesis. **Ask your 'very disappointed' users what the main benefit
they get from you is** — or how they'd want you to improve the product. **That main benefit needs
to show up clearly in your proposition.**"

> Note the method: the signal comes from the *segment that already values the product*, not from
> the dissatisfied majority. This is a non-obvious and useful instruction.

### The Superhuman four-question survey
[S005] reports, citing a First Round Review case study, the four questions Superhuman used:

1. "How would you feel if you could no longer use Superhuman? **A) Very disappointed B) Somewhat
   disappointed C) Not disappointed**"
2. "**What type of people do you think would most benefit** from Superhuman?"
3. "**What is the main benefit you receive** from Superhuman?"
4. "**How can we improve** Superhuman for you?"

> Question 2 is the clever one: it asks users to identify the target segment, rather than assuming
> it.

## Writing a stronger value proposition

[S036]'s three tests:
1. **Speak directly to your customer** — in their terms, not the company's.
2. **Pass the "so what" test.**
3. Answer: "What is the problem you're solving?" and "How will this solution benefit your
   customer?"

[S005]'s durability point: "A PM who stays **single-minded about the value proposition turns it
into must-haves in the product. And that turns into users who trust the product because you
delivered what you promised.**"

## Limitations

- **All four models are described second-hand.** Moore's *Crossing the Chasm*, Pichler's Vision
  Board, Osterwalder's canvas and Maurya's Lean Canvas are **not in the corpus** as primary
  sources. Attributions should be verified.
- **[S005] is vendor content** (Tempo) and closes with a product catalogue; the framework
  comparison is nonetheless substantive and its stated gaps per model are unusually honest.
- **The 40% benchmark lacks primary evidence** (see above).
- **No guidance on value propositions for multi-sided products** (marketplaces, platforms) where
  different sides need different propositions.
- **No treatment of how often a value proposition should be revisited**, or what triggers a
  revision.
- **No coverage of pricing** as an element of value, despite [S090] listing pricing among the
  strategy types and [S077] listing it among PM responsibilities.

## Related concepts

- [positioning.md](positioning.md) — closely related and often confused
- [product-value.md](product-value.md)
- [product-market-fit.md](product-market-fit.md)
- [product-strategy.md](product-strategy.md)
- [../02-discovery/jobs-to-be-done.md](../02-discovery/jobs-to-be-done.md)
- [../03-market-intelligence/competitive-analysis.md](../03-market-intelligence/competitive-analysis.md)
- [../02-discovery/surveys.md](../02-discovery/surveys.md) — survey method cautions apply to the 40% test

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S005 | Tempo — *4 product value proposition models for product managers* | Vendor guide | Definition, dual use, four models with stated gaps, 40% test, Superhuman questions |
| S036 | ProductPlan — *How Product Managers Can Write More Compelling Value Propositions* | Vendor guide | Writing tests, customer-framed questions |
| S095 | Product School — *Product Vision: How to Create One* | Training-provider guide | Value proposition as a step in vision creation |
