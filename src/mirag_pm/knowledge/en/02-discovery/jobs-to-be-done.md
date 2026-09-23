---
title: Jobs to be Done (JTBD)
domain: discovery
type: framework
topics:
  - jobs to be done
  - JTBD
  - struggling moments
  - progress-making forces
  - push pull anxiety inertia
  - job story
  - competing alternatives
source_count: 3
sources: [S054, S053, S110]
evidence_type: practitioner-framework
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Jobs to be Done (JTBD)

## Core claim

> "People don't buy products; they hire them to get a job done." [S054]

[S054] elaborates: "when someone purchases your product, they're not just acquiring a set of
features or capabilities — **they're seeking to make progress in their lives**."

The formulation most often quoted, attributed by [S054] to Bob Moesta: *"People don't want a
quarter-inch drill; they want a quarter-inch hole."*

## Attribution

| Figure | Role as reported |
|---|---|
| **Clayton Christensen** | Harvard Business School professor who "popularized" JTBD and "applied it in the context of disruptive innovation" [S110]. Source of the milkshake study [S054] |
| **Bob Moesta** | CEO of the ReWired Group, "an early pioneer of Jobs to be Done — as he collaborated often with Clayton Christensen" [S054] |
| **Jim Kalbach** | Author of *The Jobs to Be Done Playbook* [S110] |
| **Alan Klement / Paul Adams / Intercom** | [S053] attributes the **Job Story** format specifically to this lineage rather than to Christensen — see [Job Stories](#the-job-story-format) |

> **No primary JTBD source is in the corpus.** Christensen's, Moesta's and Kalbach's own
> writing is absent. All attributions here are second-hand.

## The milkshake example

[S054]: "Christensen found that people didn't just buy milkshakes from a particular fast-food
restaurant because they liked the taste or the price. Instead, they were 'hiring' milkshakes to
do a specific job: **staving off boredom during a long morning commute and keeping them full
until lunchtime.**"

The consequence — and the reason the example is famous — is a redefinition of competition:
"Instead of competing with other milkshakes or snacks, they realized they were competing with
anything that could solve the same job — from bagels to bananas… and boredom-busting activities
like listening to the radio." [S054]

> **Verification status: UNVERIFIED in this corpus.** This is one of the most-repeated stories
> in product management and the corpus contains no primary account of the study, its method, or
> its sample.

## Key concepts

### Struggling moments
[S054]: "the moments when customers realize that their current solution is no longer working
and need to find a better way."

Why they matter: "Struggling moments are crucial because they trigger the search for a new
solution. They create a sense of urgency and motivation that propels the customer forward in
their journey. And they provide a wealth of insights into the customer's context, constraints,
and criteria for success."

Moesta, as quoted: "The moment you realize you have to do something different, that's the
struggling moment. And that's where we find innovation."

**How to find them** [S054]: "look for the gaps between the customer's current reality and
their desired outcome" — through in-depth interviews with customers who have recently purchased
your product or a competitor's, asking them to walk through their decision step by step.

### The four progress-making forces

This is the most operationally useful part of the framework. [S054] describes four forces
acting on a switching decision:

| Force | Direction | Description [S054] |
|---|---|---|
| **Push** | Toward change | "The negative aspects of the customer's current reality that drive them to seek out a new solution" |
| **Pull** | Toward change | "The positive aspects of the new product or service that attract customers and make them believe it can solve their problem" |
| **Anxiety** | Against change | Worry "about the cost, the complexity, or the risk of making a change" — anxiety about the *new* solution |
| **Inertia / habit** | Against change | "Customers get stuck in their current situation, even if it's not ideal" — from "familiarity, sunk costs, or simply the effort required to make a change" |

[S054]: "anxiety and inertia can keep pushing people back to the current situation (and away
from your product)... it's a powerful force that can keep customers from switching, even when a
better solution is available."

**Why this matters for product decisions:** the model implies that increasing *pull* (adding
features, improving the product) is only one of four levers, and often not the binding one.
Reducing anxiety (trials, guarantees, migration support) and reducing inertia (import tools,
low switching cost) act on forces that product teams routinely ignore.

### Functional, emotional and social dimensions
[S054]: JTBD "helps you uncover the functional, emotional, and social dimensions that drive
people to seek a solution."

Illustration given: "When people buy a luxury car... the real job they're hiring is likely not
just to get from point A to point B. They're also likely hiring it to feel successful,
sophisticated, and admired by others."

## JTBD interviews

Covered in detail in [user-interviews.md](user-interviews.md). Summary of the four
distinguishing properties [S054]:

1. Focus on a **purchase decision**, not general feedback or usability
2. Probe **emotional and social** aspects, not just functional requirements
3. Recruit customers who have **recently purchased** (yours, a competitor's, or a substitute)
4. Follow a structure designed to **uncover causality and context**

Length: 60–90 minutes.

**Probing questions given** [S054]: "Can you tell me more about that?" · "What was going through
your mind at that point?" · "How did that make you feel?" · "What alternatives did you consider,
and why did you ultimately choose this one?" · "What was happening in your life or work at that
time that led you to seek a solution?" · "Can you walk me through the steps you took to evaluate
your options?" · "What ultimately tipped the scales and convinced you to purchase?"

## The Job Story format

[S054] gives the synthesis artefact:

> **"When [situation], I want to [motivation], so I can [expected outcome]."**

Example given: *"When I'm managing a complex project with a distributed team, I want to have a
centralized hub for communication and task tracking to ensure everyone is aligned and working
efficiently."*

The Job Story's relationship to — and contrast with — the User Story is treated in
[../06-requirements/job-stories.md](../06-requirements/job-stories.md).

## What JTBD changes in practice

### It redefines the competitive set
[S054]: "the most significant competition for a product isn't another similar product but
rather the status quo or alternative solutions that customers use to get the job done."

Its example: a new mobile game's competition may not be other mobile games. "If the primary
reason is to provide a few minutes of distraction during a subway commute," the competitive set
is anything that fills that gap.

This has a direct consequence for competitive analysis — see
[../03-market-intelligence/competitive-analysis.md](../03-market-intelligence/competitive-analysis.md),
which independently identifies "substitute solutions and 'do nothing' competitors" as a
category.

### It reframes roadmap anchoring
[S054]: "By anchoring your roadmap around the key jobs your customers are trying to get done,
you can ensure that every feature and initiative is aligned with their needs... It means
prioritizing features and capabilities that directly address customers' struggling moments and
desired outcomes rather than just adding bells and whistles."

## Reported cases

**Basecamp** [S054]: JTBD interviews revealed "their customers weren't just hiring Basecamp to
manage projects — they were hiring it to reduce communication chaos, create a sense of
accountability, and ultimately achieve a feeling of control and calm in their work lives. This
insight led Basecamp to reframe how they thought about their product... This led to features
like the 'Work Can Wait' filter, which allows users to pause notifications during off-hours."

**Intercom** [S054]: interviews uncovered an unmet need — "the ability to provide fast,
personalized customer support at scale. While plenty of help desk and live chat tools were on
the market, none fully satisfied the job of making customers feel truly valued and understood."
This is reported as leading to a product called Respond.

> **Verification status: UNVERIFIED.** Both accounts are the author's, without company sources.
> [S054] also notes that a Basecamp feature was "likely inspired" by the same insight — the
> author's own inference, explicitly hedged.

## Common pitfalls

[S054] names four. These are the document's most valuable content for an agent, because they
are failure modes rather than instructions.

| Pitfall | Description and correction |
|---|---|
| **Confusing the job with your solution** | "It's easy to fall into the trap of assuming that your product is the only way to solve the customer's problem or that your features define the job to be done." Correction: "The job is the progress the customer is trying to make, while your product is just one possible way to achieve that progress." Example: for a meal delivery service, the job is not "ordering meals online" but possibly "feeding my family healthy meals without the hassle of cooking." |
| **Focusing only on functional aspects** | Neglecting emotional and social dimensions. Correction: probe with "How did you want to feel when using this product?" or "What did you hope this product would say about you to others?" |
| **Treating JTBD as a one-time event** | "Customers' jobs are always evolving, and your understanding of those jobs will always be incomplete." |
| **Failing to align the organization** | "It's not enough to conduct interviews and create job stories — you also need to ensure that everyone in the company understands and buys into the jobs framework," across marketing, sales and customer success. |

## When it fits

[S110]: when teams "need to uncover the deeper motivations behind customer behavior and
identify opportunities for innovation"; when shifting "from feature-centric development to
user-centric design"; "in industries where customers have complex needs that aren't fully
addressed by existing solutions"; when a team is "struggling to understand why customers use
their product or how to differentiate their offering in a competitive market."

## Limitations and assumptions

- **It assumes a discrete purchase or switching decision exists** to interview about. [S054]'s
  entire interview method depends on recruiting people who "recently made a purchase decision
  in your market." For free products, internal tools, mandated software, or infrastructure with
  no user-side choice, the core instrument does not apply as described. The corpus does not
  address this.
- **It is interpretive, not measurable.** A "job" is an inference from stories. The corpus
  offers no reliability check — [S054] itself notes two people can read the same interview and
  reach different conclusions.
- **Cost.** 60–90 minute interviews across a diverse recruit, analysed for patterns, is
  substantially more expensive than most discovery methods.
- **No primary sources and no comparative evidence.** Nothing in the corpus measures whether
  JTBD-derived decisions outperform alternatives.
- **JTBD is not one thing.** The corpus hints at this — [S053] attributes the Job Story format
  to a different lineage than Christensen's — but does not address the well-known divergence
  between JTBD schools (e.g. Christensen's "jobs" versus Ulwick's outcome-driven innovation).
  [S031] separately references "Opportunity scoring (Anthony Ulwick)" without connecting it.
  **Recorded as a gap.**
- [S054] is written by the Head of Product Evangelism for Pendo and Mind the Product, and
  several examples double as promotion for the author's own conference. The framework content
  is separable from that.

## Related concepts

- [user-interviews.md](user-interviews.md)
- [discovery-frameworks.md](discovery-frameworks.md)
- [identifying-unmet-needs.md](identifying-unmet-needs.md)
- [../06-requirements/job-stories.md](../06-requirements/job-stories.md)
- [../06-requirements/user-stories.md](../06-requirements/user-stories.md)
- [../03-market-intelligence/competitive-analysis.md](../03-market-intelligence/competitive-analysis.md)
- [../04-strategy/value-proposition.md](../04-strategy/value-proposition.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S054 | Mind the Product, Mike Belsito — *Jobs to be done for Product Managers* | Practitioner essay | Core claim, forces, struggling moments, interviews, job story, cases, pitfalls |
| S053 | Learning Loop — *Job Story (JTBD): What it is, How it Works, Examples* | Practitioner glossary | Job Story origin and format (see job-stories.md) |
| S110 | Product School — *The Definitive Guide to Product Discovery and Frameworks* | Training-provider guide | Attribution, application steps, fit conditions |
