---
title: Choosing a User Research Method
domain: discovery
type: decision-framework
topics:
  - user research
  - research methods
  - qualitative vs quantitative
  - attitudinal vs behavioral
  - method selection
  - triangulation
source_count: 5
sources: [S105, S017, S074, S114, S110]
evidence_type: empirical-and-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Choosing a User Research Method

## The core decision rule

The corpus's most useful contribution on research is not a list of methods — it is a
**two-question test for choosing one**, from [S105] (Nielsen Norman Group):

> 1. **Is the research question quantitative or qualitative?**
>    Quantitative deals with "how many or how much of something." Qualitative deals with
>    "why something occurs or how to fix something."
> 2. **Is the research question behavioral or attitudinal?**
>    Behavioral is "concerned with what people do." Attitudinal is "concerned with what
>    people say."

These two axes form the map that [S017] uses to place 20 research methods.

### Worked example 1 — a survey is correct [S105]
*"Your stakeholders want to know the percentage of users who, after submitting their tax
returns using your software, feel confident that they have done it correctly."*

- **Quantitative?** Yes — "the word 'percentage' clearly indicates a quantitative research
  question. We will need a large sample."
- **Behavioral or attitudinal?** Attitudinal — "confidence is tricky to objectively observe,
  and we often instead rely upon self-reported scales of confidence."

→ Quantitative + attitudinal = **survey**. [S105]: "there can be no other method better suited."

### Worked example 2 — a survey is wrong [S105]
*"The analytics team has noticed a large number of people abandoning their carts prior to
checking out. They want you to figure out why."*

- **Quantitative?** No — "'Why' questions are best answered using qualitative methods."
- **Behavioral or attitudinal?** Behavioral — "the abandonment of a cart is a behavior, and
  one that can be observed."

→ Qualitative + behavioral. [S105]: "it is likely that **usability testing** would fit our
needs best."

### The structural insight
[S105] notes that on the 20-method map, **surveys sit alone in the quantitative/attitudinal
corner**: "surveys are, in fact, the only method that can be categorized as both quantitative
and attitudinal." This is why survey misuse is so common — there is no near-neighbour method
to fall back on, so teams reach for surveys whenever they want numbers, regardless of whether
the question is attitudinal.

## Qualitative and quantitative are both fallible

[S074] makes a point worth preserving because it cuts against the common assumption that data
settles arguments:

> "Both qualitative data and quantitative data can lie. The numbers don't always tell the
> truth, but then again neither do customers!" [S074]

Its example: Gibson Biddle, former VP of Product at Netflix, on the DVD-rental era —
customers said that having the newest releases as soon as possible was of utmost importance.
"When Netflix spent millions of dollars acquiring extra DVDs to provide customers with what
they asked for, the result was… minimal change in retention. Customers claimed to know what
they wanted, even though, in the end, they didn't."

> **Classification: reported anecdote.** [S074] attributes this to Biddle's talks; the corpus
> contains no primary source or retention figures. The *lesson* — stated preference does not
> reliably predict behaviour — is corroborated in principle by [S045], which quotes cultural
> anthropologist Margaret Mead: "What people say, what people do, and what people say they do
> are entirely different things."

This is the practical reason the behavioral/attitudinal axis matters: **attitudinal methods
measure what people report, not what they do.**

## Method summaries from the corpus

### User interviews
[S074]: one-on-one conversations, in person or by video call. "Come ready with a script, and
be prepared to ask follow up questions."
- **Pros:** "Allows for more personal connection, can be conducted at any time in the
  development process."
- **Cons:** "Time intensive" — "very time and resource intensive, more so than other methods."

Treated in depth in [user-interviews.md](user-interviews.md).

### Usability testing
[S074] frames it as answering four questions about the product:
1. Is it easy to learn?
2. Is it fast to use?
3. What common mistakes do users make while using it?
4. How does it feel to use this product?

- **Pros:** "Covers a lot of bases"; gives "a good mix of qualitative and quantitative
  feedback."
- **Cons:** "Resource heavy, involves getting a prototype out to testers."
- **When:** "especially essential in the early stages of development as it allows you to
  validate your prototype," and worth repeating "if/when you make significant changes to your
  UI."

Treated in depth in [usability-testing.md](usability-testing.md).

### Card sorting
[S074]: participants organise pre-made cards of categories "in the way that feels most
logical," revealing how the user group processes information — used to inform information
architecture.
- **Pros:** "Chance of identifying criticalities."
- **Cons:** "Can be hard to consolidate findings into usable insights" — "you run the risk of
  everyone giving you a different answer, making the data hard to process."
- In-person card sorting allows follow-up on *why* choices were made; online tools do not.

### A/B testing
[S074]: "rolling out two different versions of your product, landing, or feature, and seeing
what the response is." Can test "basic styling like fonts, colors, and graphics, to the entire
layout of your UI."

> The corpus's treatment of A/B testing is **thin** — a few sentences, with no coverage of
> sample sizing, statistical significance, test duration, novelty effects, or the risks of
> peeking. [S122] separately names hypothesis testing as a PM skill without depth. Recorded as
> a gap.

### Diary studies
[S028] and [S044]: "a longitudinal research method in which a participant submits multiple
logs (or diary entries) over a period, documenting discrete behaviors or interactions with a
product or service." [S044] notes survey questionnaires are commonly used to collect the
entries — "a user may be asked to complete the same survey every day at a specific time for
2 weeks."

### Field studies and ethnography
See [ethnographic-research.md](ethnographic-research.md).

### Surveys
See [surveys.md](surveys.md) — including when **not** to run one.

### Focus groups
Named by [S058] and [S045] as a method for gathering group opinions and attitudes. The corpus
contains **no critical treatment** of focus groups' well-known weaknesses (dominant speakers,
groupthink, stated-preference bias). Noted as a gap rather than presented as a neutral option.

## Practice guidance on running research well

[S074] gives four rules for data collection:

1. **Know your data protection obligations.** "Data protection compliance isn't the most
   exciting aspect of building a product, but you're going to need it."
2. **Figure out the answers you need before asking your questions.** [S074] flags the common
   failure: "it's actually a very common mistake for product teams to lead with questions, and
   then end up with answers that aren't actually that useful."
3. **Collaborate with the rest of the team.** "Don't assume that one set of data will work for
   everyone" — different roles need different information.
4. **Conduct a mix of quantitative and qualitative research.**

[S076] adds a related principle: "Achieve a comprehensive understanding by combining
quantitative metrics with qualitative insights. Qualitative is key here, as it provides more
context into the 'why'."

## Triangulation

[S105] recommends triangulation specifically as a defence against stakeholders cherry-picking:

> "If possible, use triangulation to tell a consistent and cohesive story with your multiple
> sources of data, to avoid your stakeholder's temptation to cherry-pick the data that
> supports their preexisting assumptions." [S105]

[S028] describes the same technique for discovery: survey data "can be triangulated with
qualitative insights from other methods."

## Limitations

- **[S017] is the source that would most directly answer "which method when" — and it did not
  extract.** The captured PDF of NN/g's *A Guide to Using User-Experience Research Methods*
  contains only the title, authors (Kelley Gordon and Christian Rohrer, 21 Aug 2022) and
  summary; the 20-method chart mapping methods across three dimensions and across the product
  development process is an image that produced no text. **The full method map is therefore
  not in this knowledge base.** [S105] preserves the two main axes. Recovering the third
  dimension and the per-method placements is a research task.
- The corpus covers **method selection** well and **method execution** unevenly — interviews
  and surveys in depth, A/B testing and focus groups barely.
- No coverage of research operations, participant recruitment at scale, consent and ethics
  beyond a single mention of data protection, or research repositories.

## Related concepts

- [product-discovery.md](product-discovery.md)
- [user-interviews.md](user-interviews.md)
- [surveys.md](surveys.md)
- [usability-testing.md](usability-testing.md)
- [ethnographic-research.md](ethnographic-research.md)
- [../03-market-intelligence/market-research.md](../03-market-intelligence/market-research.md)
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S105 | Nielsen Norman Group, Maddie Brown — *Should You Run a Survey?*, 23 Feb 2024 | UX research organization | Two-axis decision rule, worked examples, triangulation |
| S017 | Nielsen Norman Group, Kelley Gordon & Christian Rohrer — *A Guide to Using User-Experience Research Methods*, 21 Aug 2022 | UX research organization | Existence and framing of the 20-method map (content not extractable — see Limitations) |
| S074 | Product School — *Product Management Skills: User Research*, updated 3 Jan 2025 | Training-provider blog | Method pros/cons, data-collection rules, Netflix anecdote |
| S114 | Maze — *The Product Manager's Guide to User Research* | Vendor guide | Research planning framing |
| S110 | Product School — *The Definitive Guide to Product Discovery* | Training-provider guide | Qual/quant balance in discovery |
