---
title: Competitive Analysis
domain: market-intelligence
type: process
topics:
  - competitive analysis
  - competitor research
  - direct and indirect competitors
  - substitutes
  - do nothing competitor
  - SWOT
  - positioning map
  - differentiation
source_count: 4
sources: [S025, S079, S117, S026]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Competitive Analysis

## Definition

[S025]: "Competitive analysis in product management is **a structured evaluation of competing and
alternative products to understand how they solve similar problems, where they perform well, and
where gaps exist in the market.** It looks at **product capabilities, positioning, pricing, user
experience, and customer perception.**"

### The three questions it answers
[S025]:
1. "**What problems do competing products solve, and for whom**"
2. "**Where do competitors perform strongly or fall short**"
3. "**What opportunities exist for meaningful differentiation**"

## Three related activities that are not the same thing

[S025] makes a distinction the corpus needs, because these terms are used interchangeably:

| Activity | Focus | Purpose | How product teams use it |
|---|---|---|---|
| **Competitor research** | "Individual competitors and their activities" | "Gather basic information about specific competitors" | "Track launches, features, pricing updates, and announcements" |
| **Market research** | "Market size, trends, and customer behavior" | "Understand demand, segments, and overall market direction" | "Validate opportunities and identify target segments" |
| **Competitive analysis** | "**Comparative evaluation** of products and positioning" | "Identify **strengths, gaps, differentiation, and risks**" | "Inform roadmap decisions, positioning, and product strategy" |

> [S025]'s summary: "**Competitor research collects raw information. Market research explains the
> broader landscape. Competitive analysis connects both and translates insights into product
> decisions.**"

See [market-research.md](market-research.md) and [market-trends.md](market-trends.md).

## The most important caution: this is not about copying

[S025] states it directly, and it is the failure mode most worth guarding against:

> "Competitive analysis for product managers **supports differentiation rather than imitation.
> Copying competitor features without understanding context often leads to feature-heavy products
> that lack clarity and direction.**"

What it should produce instead:
- "Understand **table-stakes capabilities** expected by users"
- "Identify **gaps that competitors have overlooked**"
- "Recognize strengths worth **countering or differentiating from**"
- "Spot **shifts in positioning, pricing, or user experience**"

> "Instead of **chasing feature parity**, teams gain clarity on where they can create meaningful
> value." [S025]

[S117] independently names a related failure: "**Ignoring Customer Feedback: Overlooking customers'
wants**" while watching competitors.

## Categorising competitors correctly

[S025] argues most teams analyse the wrong set: "They either study only **well-known brands** or
track **every tool in the category** without clear relevance."

### The four categories

**1. Direct competitors** — "solve the **same core problem for the same audience**. They often
appear in customer evaluations, comparison searches, and sales conversations. **These are the
products users actively compare** before making a decision."

*How to identify them* [S025]: "Win and loss notes from sales or user interviews · Comparison of
keywords users search for · Review platforms where users evaluate similar tools."

**2. Indirect competitors** — "address the **same outcome but through a different approach or
workflow**." Example: "a project management tool may compete indirectly with **collaboration
platforms, documentation tools, or workflow automation products.**"

*Why they matter* [S025]: "helps product managers understand **how users evaluate solutions beyond
traditional category boundaries.** It also reveals emerging expectations and potential shifts in
user behavior."

**3. Substitute solutions and "do nothing" competitors** — this is the category most often omitted
and, per [S025], often the most important:

> "Some of the **strongest competition** comes from tools or workflows that **replace the need for
> a dedicated product.** These substitutes often include **spreadsheets, internal dashboards, email
> threads, shared documents, or manual coordination processes.**
>
> **In many cases, the real competitor is the existing workflow rather than another software
> product.** Understanding **why users continue with current methods** helps product managers
> identify barriers to adoption."

> This converges exactly with JTBD's claim that "the most significant competition for a product
> isn't another similar product but rather **the status quo**" [S054], and with [S005]'s Lean
> Canvas "existing alternatives" section. **Three independent traditions in this corpus identify
> non-consumption as the primary competitor.** See
> [../02-discovery/jobs-to-be-done.md](../02-discovery/jobs-to-be-done.md).
>
> It also connects to the **inertia** force in JTBD — see
> [../02-discovery/jobs-to-be-done.md](../02-discovery/jobs-to-be-done.md) — and to [S076]'s
> observation that customers often build "their own hacked together solution."

**4. Shortlisting** [S025]: "**Reviewing too many competitors leads to shallow insights.**"

*How to shortlist:* "Analyze win and loss data to see which products appear most often · Review
customer interviews and onboarding feedback · Check review platforms and comparison pages ·
Monitor recurring competitor mentions in sales conversations."

> **Select five to seven competitors across direct, indirect, and substitute categories.** [S025]

## Process

[S025]'s five steps (the source continues beyond step 5; the remainder did not extract):

### Step 1 — Define your objective and scope
"**Every competitive analysis should support a specific decision**, such as roadmap prioritization,
positioning clarity, pricing updates, or feature validation. Write down what you are trying to
decide and **set boundaries around what you will evaluate.** ... **A clear objective keeps the
analysis focused and prevents unnecessary research.**"

### Step 2 — Choose competitors
Five to seven, across all three categories. "**Depth matters more than quantity. Studying a smaller
set thoroughly yields deeper insights than scanning a long list superficially.**"

### Step 3 — Decide comparison criteria
"**Before collecting data**, define what you want to compare. Consistent criteria make the analysis
easier to interpret and share."

Common areas [S025]: "Features and workflows · Pricing and packaging · Integrations and ecosystem ·
**Onboarding experience** · Positioning and messaging."

**Choose criteria based on your objective:** "if the goal is adoption, focus more on **onboarding
and usability** than on advanced features."

### Step 4 — Collect data
Sources [S025]: "competitor websites, pricing pages, documentation, and product demos. **Use free
trials when possible to experience workflows directly.**"

And the higher-signal sources: "**Customer reviews and community discussions often reveal recurring
strengths and pain points that product pages do not highlight. Release notes and changelogs also
help identify where competitors are investing.**"

> Changelogs as an investment signal is a good, concrete technique — it reveals competitors'
> *priorities*, not just their current state.

[S081] adds named review platforms: "**G2, Trustpilot, or Capterra** — to pinpoint recurring user
complaints, gaps in current offerings, and unmet expectations."
[S079] adds "Customer reviews (**G2, Capterra, App Store, Reddit**)."

### Step 5 — Analyse patterns, not details
"Focus on **patterns rather than isolated details.**" Look for:
- "**Table-stakes capabilities** present across most products"
- "**Recurring user frustrations or limitations**"
- "**Gaps that competitors have not addressed**"
- "Differences in positioning and target audience"

## When to run it

[S025] treats this as conditional rather than continuous-by-default:

| Trigger | Why |
|---|---|
| **Before building or launching a new feature** | "Helps validate whether the problem has existing solutions and how those solutions approach it... **avoid building redundant capabilities**" |
| **When entering a new market or segment** | "Different expectations, pricing sensitivities, and workflow preferences" |
| **During repositioning or pricing changes** | "How similar products **structure pricing tiers, highlight differentiators, and justify cost**... reduces the risk of pricing changes that create confusion" |
| **As an ongoing habit** | "**Regular reviews help product managers stay aware of these shifts without reacting impulsively to every update.** Maintaining lightweight, ongoing competitive analysis ensures that insights remain current" |

> The fourth entry contains the balance point: **stay aware without reacting impulsively.** A
> competitive analysis that generates a roadmap change on every competitor release has become the
> imitation trap it was meant to avoid.

## Frameworks

[S079] names three structuring tools:
- **SWOT analysis** (Strengths, Weaknesses, Opportunities, Threats)
- **Positioning map**
- *(a third framework named in the source did not extract)*

[S081] recommends "a **SWOT analysis for key competitors** to identify strengths, weaknesses,
overlooked market opportunities, and threats posed by evolving customer preferences, technologies,
or regulatory changes."

[S059] (Maven) lists competitor analysis activities: "Perform a **SWOT Analysis** · Analyze
competitor products · **Monitor competitor marketing activities**."

[S090] lists **Porter's 5 forces** among business models useful in strategy work.

> **SWOT is the only framework the corpus explains**, and it does so in a *risk* context — see
> [../10-risk/risk-identification.md](../10-risk/risk-identification.md) for its four quadrants.
> Positioning maps, Porter's Five Forces and competitive feature matrices are **named but never
> described.** Recorded in [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Why it matters for product decisions

[S025]: "Most products address similar problems, so **users prioritize clarity, usability, trust,
and value over features.** ... By reviewing messaging, onboarding, features, and feedback, teams
can identify unique strengths, refine positioning, and **avoid generic value propositions.**"

[S079] frames the downside as "**The Cost of Ignoring Competitive Intelligence.**"

Its process steps [S079], which broadly match [S025]'s: define your goal and scope → identify your
real competitors (naming "Direct competitors (Harvest, Toggl)" and "Indirect competitors
(spreadsheets, Notion)") → choose a framework → collect data from multiple sources.

> Note that [S079]'s example of indirect competitors is **spreadsheets and Notion** — i.e. it
> folds substitutes into "indirect." [S025]'s three-way split is the more useful taxonomy.

## Limitations

- **All sources are vendor or training-provider content.** [S025] is the most substantial and is
  the backbone of this document.
- **No evidence** that competitive analysis improves outcomes.
- **The frameworks are largely unexplained** (see above).
- **Steps 6 onward of [S025]'s process did not extract** — including "what to include in a
  competitive analysis report" and "common competitive analysis mistakes to avoid."
- **No treatment of competitive intelligence ethics or legal boundaries.**
- **No treatment of how competitive analysis feeds pricing decisions**, despite pricing appearing
  in every comparison-criteria list — pricing is a corpus-wide gap.
- **[S026] (ProductPlan) and [S117] (airfocus) contributed little**; both were heavily truncated in
  extraction.
- [S025] is dated 13 Feb 2026; competitive landscapes are inherently time-sensitive, but the
  *method* is durable.

## Related concepts

- [market-research.md](market-research.md)
- [market-trends.md](market-trends.md)
- [market-needs.md](market-needs.md)
- [../04-strategy/positioning.md](../04-strategy/positioning.md)
- [../04-strategy/value-proposition.md](../04-strategy/value-proposition.md)
- [../02-discovery/jobs-to-be-done.md](../02-discovery/jobs-to-be-done.md) — the status quo as competitor
- [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md)
- [../10-risk/risk-identification.md](../10-risk/risk-identification.md) — SWOT explained

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S025 | *Competitive analysis for product managers: A complete guide* (Sneha Kanojia), 13 Feb 2026 | Vendor guide | Definition, three-activity distinction, anti-imitation argument, four competitor categories, shortlisting, five-step process, when to run |
| S079 | Product School — *Product Manager's Power Move: Competitor Analysis*, updated 6 May 2025 | Training-provider guide | Frameworks named, process steps, data sources |
| S117 | airfocus (Adam Thomas) — *The Role of Competitive Analysis in Effective Product Strategy* | Vendor guide (truncated) | Customer-feedback caution |
| S026 | ProductPlan — *Conduct an Effective Competitive Analysis Everytime* | Vendor guide (truncated) | Social media as a source |
