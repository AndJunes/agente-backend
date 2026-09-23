---
title: Market Research
domain: market-intelligence
type: process
topics:
  - market research
  - market sizing
  - segmentation
  - exploratory research
  - secondary research
  - focus groups
  - customer insights
source_count: 5
sources: [S058, S073, S056, S059, S041]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Market Research

## What it is for

[S058] (Maven): "Product managers can make informed decisions about **product features, pricing, and
positioning** by gathering and analyzing data about **customers, competitors, and market trends.**"

### Three goals
[S058]:

| Goal | Purpose | Methods it names |
|---|---|---|
| **Identifying customer needs** | "Understanding the needs and preferences of your target audience... **identify gaps in the market and uncover opportunities**" | "Surveys, interviews, and focus groups" |
| **Assessing market opportunities** | "Evaluating a market's **size and growth potential** is crucial for determining the viability of a product idea" | "**Market sizing and trend analysis**" |
| **Analyzing competitors** | "Identify your competitors' strengths and weaknesses and uncover opportunities to differentiate" | "A competitive analysis" — see [competitive-analysis.md](competitive-analysis.md) |

## Market research versus user research

The corpus does not state the distinction explicitly, but it is consistent across sources and worth
making:

| | **Market research** | **User research** |
|---|---|---|
| **Unit of interest** | The market — size, segments, trends, competitors | Individual users — behaviour, needs, motivations |
| **Typical question** | *Is there a market worth entering, and how big is it?* | *What does this person actually need, and why?* |
| **Where treated** | This document; [market-trends.md](market-trends.md); [competitive-analysis.md](competitive-analysis.md) | [../02-discovery/user-research-methods.md](../02-discovery/user-research-methods.md) |

> They overlap heavily in method — interviews, surveys and observation appear in both — and
> [S073] is a *market research* article whose five types are largely user-research activities. The
> distinction is about the **question being asked**, not the technique.

## Techniques

[S058]:

| Technique | What it produces | Caution |
|---|---|---|
| **Surveys and questionnaires** | "Cost-effective for gathering **quantitative** data about customer needs, preferences, and behaviors." "By asking many respondents structured questions, product managers can obtain statistically significant insights" | ⚠ See [../02-discovery/surveys.md](../02-discovery/surveys.md) — [S105] documents in detail why surveys are the most misused research method and when they are the wrong instrument |
| **Interviews** | "Valuable for collecting **qualitative** data... **detailed insights into their target customers' underlying motivations and pain points**" | See [../02-discovery/user-interviews.md](../02-discovery/user-interviews.md) |
| **Focus groups** | Group discussion of "opinions, attitudes, and behaviors" [S045] | ⚠ The corpus contains **no critical treatment** of focus groups' known weaknesses |
| **Observational research** | Named by [S058] | See [../02-discovery/ethnographic-research.md](../02-discovery/ethnographic-research.md) |
| **Secondary research** | Named by [S058] and [S059] — analysis of existing published data | ⚠ **Not explained anywhere in the corpus** |

[S081] adds accessible sources for market sizing: "publicly available **industry reports, business
intelligence platforms, AI tools, Google Trends, and demographic statistics.**"

## Five types of research a product team runs

[S073] (Product School) gives a sequence that maps to product stage:

**1. Exploratory research** — "rarely will you have a properly defined problem statement right off
the bat... **finding out the nature of the problem, whilst also asking yourself if it's
extensive**" [enough to matter].

**2. Competitive analysis** — "**absolutely key before you decide how you're going to approach
development.**" Its cautionary example: building a podcast app MVP, then discovering "most of your
target market listen to podcasts on Spotify."

**3. User insights** — "Before you can begin to build for your customers, you need to know who they
are... **it's not a type of research that you get to perform once and then forget about, it's an
iterative process.**"

**4. Beta testing** — "the first thing you manage to get into users' hands is an MVP or a beta
version... **User insights might have told you that customers are interested in a product like
yours, but an MVP will make sure that you're building it in the right way.**" Also usable "to test
out new features on established products, or to A/B test your homepage."

**5. Segmentation** — "separating your users into specific segments isn't only useful for
marketing. **It's also an extra step into properly understanding your users.**" Dimensions named:
"geography, demographic, or behavior." Benefit: "**allows you to test more effectively, and
communicate with your users in more** [targeted ways]."

> Note the ordering logic: **problem → market → users → validation → differentiation of users.**
> Research type follows from what you do not yet know.

## Segmentation types

[S059] (Maven) gives four dimensions; [S041] gives five. Combined:

| Type | Basis |
|---|---|
| **Demographic** | "Age, gender, income, education" [S041] |
| **Geographic** | "Location, climate, city size" [S041] |
| **Behavioral** | "Buying habits, product usage, brand loyalty" [S041] |
| **Psychographic** | Attitudes, values, lifestyle [S059] |
| *(A fifth type named by [S041] did not extract)* | |

> The corpus offers **no guidance on choosing a segmentation basis**, testing whether segments are
> real, or how many segments a product should serve. Recorded as a gap.

## A four-step process

[S056] (Aha!) gives a compact sequence:
1. *(Step 1 did not extract — presumably defining objectives)*
2. "**Plan and conduct research.** Figuring out where to find the [right respondents]"
3. "**Analyze and share the results.** Once you have gathered your [data]"
4. "**Plan next steps. Market research should inform action.**"

### Questions market research should answer
[S056]:
1. "What problems do potential customers face and how can your [product solve them]?"
2. "Who are the target customers and what do they need?"
3. "Who are your competitors and how can you stand out?"
4. "What market trends and opportunities can you leverage?"
5. *(unextracted)*
6. "How can customers easily access and buy your product?"
7. "**What might prevent customers from adopting your product**?"
8. "How can you gather and use customer feedback for [improvement]?"

> Questions 6 and 7 are the ones product teams most often skip: **distribution and adoption
> barriers.** Question 7 in particular connects to JTBD's *anxiety* and *inertia* forces — see
> [../02-discovery/jobs-to-be-done.md](../02-discovery/jobs-to-be-done.md).

## Understanding the market landscape

[S059] gives a four-part structure:
1. **Conduct market research** — surveys and questionnaires; interviews and focus groups;
   secondary research
2. **Utilise market segmentation** — demographic, behavioural, psychographic, geographic
3. **Analyse competitors** — "Perform a **SWOT Analysis** · Analyze competitor products ·
   **Monitor competitor marketing activities**"
4. **Stay abreast of industry trends** — "**Attend industry events · Follow thought leaders**"

## Analysing the results

[S058] separates the two analysis modes:
- **Quantitative data analysis**
- **Qualitative data analysis**

and then applying findings to "**Positioning and Messaging.**"

[S076] gives the principle: "Achieve a comprehensive understanding by **combining quantitative
metrics with qualitative insights. Qualitative is key here, as it provides more context into the
'why'.**"

## To outsource or not

[S073] raises the question "To Outsource, or Not to Outsource…" — the section did not extract.
Recorded as an unanswered question in the corpus.

## Limitations

- **All sources are training providers or vendors.** [S058] and [S059] are course-platform guides;
  [S073] and [S056] are marketing content.
- **Market sizing is named but never taught.** TAM/SAM/SOM, top-down vs bottom-up estimation, and
  sizing methodology are **entirely absent** despite market sizing being named as a core goal by
  [S058] and required by [S081]. **This is a significant gap.**
- **Secondary research is named but not explained** — no guidance on evaluating source quality,
  which is precisely where secondary research goes wrong.
- **Focus groups appear without criticism** in three sources.
- **No treatment of sampling, representativeness, or research budget.**
- **Pricing research** (willingness to pay, Van Westendorp, conjoint) is absent, though pricing
  appears in every list of what market research informs.
- Much of [S073]'s "market research" content is really **user research**; see the distinction
  above.

## Related concepts

- [competitive-analysis.md](competitive-analysis.md)
- [market-trends.md](market-trends.md)
- [market-needs.md](market-needs.md)
- [../02-discovery/user-research-methods.md](../02-discovery/user-research-methods.md)
- [../02-discovery/surveys.md](../02-discovery/surveys.md)
- [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md)
- [../04-strategy/positioning.md](../04-strategy/positioning.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S058 | Maven — *Market Research Techniques: A Comprehensive Guide for Product Managers* | Course-platform guide | Role and goals of market research, techniques, analysis modes |
| S073 | Product School — *Product Management Skills: Market Research*, updated 11 Sep 2024 | Training-provider blog | Five research types and their sequence |
| S056 | Aha! — *Market Research: How Should PMs Gather Customer Insights?* | Vendor guide | Four-step process, eight guiding questions |
| S059 | Maven — *The Product Manager's Guide to Understanding the Market Landscape* | Course-platform guide | Four-part landscape structure, segmentation types, competitor activities |
| S041 | UXtweak — *How to Identify Market Needs and Create Products to Meet Them* | Vendor guide | Segmentation dimensions |
