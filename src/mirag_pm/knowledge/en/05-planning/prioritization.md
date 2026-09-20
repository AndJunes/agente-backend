---
title: Prioritization — The Practice
domain: planning
type: process
topics:
  - prioritization
  - trade-offs
  - saying no
  - feature requests
  - decision making
  - bias
  - kill condition
source_count: 6
sources: [S066, S031, S039, S040, S078, S119]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Prioritization — The Practice

> For the frameworks themselves (RICE, Kano, MoSCoW, value vs effort, opportunity scoring, cost
> of delay, weighted scoring), see
> [prioritization-frameworks.md](prioritization-frameworks.md). **This document is about the
> practice around them — which is where most prioritization actually fails.**

## Why prioritization exists

[S066]: "Prioritization is crucial during the product development process because **it's
impossible to execute every idea in any given sprint.** This makes it important to choose the
concepts that will have the most impact on the business and customers."

[S078] frames the PM's position structurally:

> "A colleague recently likened product management to being a politician. It's not far off. The
> product manager and the politician both get **an allotted amount of resources**. Each role
> requires the practitioner to make the best use of those resources to achieve a larger goal,
> **knowing that he or she will never be able to satisfy everyone's needs.**"

Its examples of the actual trade-offs: "a feature that might make one big customer happy but
upset 100 smaller customers; maintaining a product's status quo or steering it in a new direction
to expand its reach; or whether to focus on **the bright and shiny or the boring and
important.**"

## The most important finding in this material

[S039] states it plainly, and it cuts against the entire framework-selection literature:

> "**The prioritization technique you use is ultimately less important than the conversation you
> have.**"

[S031] arrives at a compatible conclusion from a different direction, about writing down a kill
condition before launch:

> "**This is one of the very few prioritization techniques where the discipline matters more than
> the framework.**"

> **Implication for an agent:** when asked "which prioritization framework should we use?", the
> higher-value response often addresses *who is in the room, what evidence exists, and what
> happens to the output* — not which formula to apply.

## Where prioritization sits in the flow

Prioritization is **not** the first step and **not** the last:

```
Strategy and goals          → what outcomes matter          [S119], [S039]
        ↓
Discovery                   → which opportunities are real  [S110], [S028]
        ↓
Candidate generation        → what could we do              [S030], ideation
        ↓
▶ PRIORITIZATION ◀          → what deserves capacity
        ↓
Roadmap                     → what we are pursuing, and why [S119]
        ↓
Backlog refinement          → what is ready to build        [S127]
        ↓
Release / sprint commitment → what we are delivering        [S126]
```

[S119]: the roadmap comes *after* "engaging in a **prioritization exercise** with various
internal (and potentially external) stakeholders to see what will have the biggest impact or
greatest ROI."

[S081] adds the upstream boundary: for big directional bets, run an opportunity assessment
*before* prioritizing; for incremental work within a validated niche, "**lean on internal
prioritization frameworks like RICE or a prioritization matrix**" instead. See
[../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md).

## Who participates

[S039]: "**If you can involve your stakeholders in the prioritization process, they are much more
likely to be on your side.**"

[S031] is specific about *why* each function belongs in the scoring, not just the meeting:

> "Bring multiple stakeholders into **the scoring itself**, not just the meeting — **development
> team for development effort estimates, customer success teams for adoption-friction reads,
> sales for value-capture probability, support for run-cost realism.**"

> The distinction between being *consulted* and being *in the scoring* is the whole point: each
> function holds a different input that the PM cannot estimate alone.

## Failure modes

These are the most valuable content in this document, because frameworks are easy and these are
not.

### 1. Treating customer requests as a roadmap
[S031]:

> "Customer requests and feature requests are valuable signals but **a terrible roadmap. Users
> ask for what they can name, and they tend to name features they've seen in other products.**
> The job of the product manager is to **triangulate the request with product analytics data,
> support patterns, and revealed dissatisfaction**, then design a solution to the underlying
> problem."

Its worked example is unusually concrete: customer feedback asked for "an advanced templating
engine" for an email feature. The funnel showed "a sharp drop-off at domain verification: users
hit the verification step and a large share never completed it. **The 'advanced templates'
feature would have done nothing for those users, since they'd never reached the templates
step.**" The actual fix was a targeting tooltip, shipped in hours.

> Its conclusion is worth keeping: "**Realizing that the next thing on the backlog is sometimes a
> tooltip rather than a build** is one of the biggest unlocks the AI era has handed product
> managers."

This corroborates, from the prioritization side, the caution in
[../02-discovery/identifying-unmet-needs.md](../02-discovery/identifying-unmet-needs.md) about
treating "what features would you like to see?" as reliable input.

### 2. Must-have inflation
[S031]: "Most teams I work with classify **80-90% of release scope as Must have**, which means
Should have and Could have are decorative. When something inevitably goes sideways mid-sprint,
**the only thing left to cut is something already labeled mission-critical**, and the team ends
up either missing the release or shipping unfinished work labeled 'Must.'"

The proposed fix: "Cap Musts at 60% of effort, reserve roughly 20% for Coulds, and **require
evidence for every Must classification** (legal requirement, security gate, named PMF dependency,
evalability blocker)."

### 3. Personal bias and seniority deference
[S031]: "**Personal bias is the hardest input to filter out of the prioritization process,
especially when multiple stakeholders in the room defer to whoever has the most senior title.**"

Two structural counters proposed:
- Distribute the scoring across functions (above).
- **Write down the kill condition before launch** — "a falsifiable threshold that, if hit, kills
  or repackages the feature."

> [S031]'s observation about kill conditions is the strongest claim it makes: "**Teams that write
> down the kill condition before shipping are also the teams that actually kill the feature later
> when the threshold is hit. When teams skip that step, they always find a reason to keep
> 'iterating' instead of pulling the plug.**"
>
> This is presented as the author's experience, not measured. But the mechanism — pre-commitment
> against future rationalisation — is a recognisable and testable one.

### 4. Treating prioritization as a one-time event
[S031]: "The bigger mistake here is **treating prioritization decisions as fixed at the start of
a release, when in reality they aren't. Re-rank weekly** — that's build-measure-learn applied to
prioritization — **because the data from the last shipped feature is the best input you have for
the next one.**"

[S066] suggests a slower but still recurring cadence: "Your team should review its priorities
regularly... You should also **re-evaluate your prioritization framework if business objectives
change.**"

### 5. Confusing a score with a decision
[S031]: "**The score is a decision aid, not truth.**" Its two checks:
- **Sensitivity:** "Does the ranking flip if I change two weights by 10%?"
- **Confidence over precision:** "A feature scoring 78 with high confidence usually beats a
  feature scoring 82 with weak evidence."

### 6. Not being able to say no
[S040]: "**Don't make the mistake of accepting a feature to please a stakeholder or avoid a
difficult conversation.**" And the diagnostic — if declining is impossible, the problem is
empowerment, not process. See
[outcome-based-roadmaps.md](outcome-based-roadmaps.md).

## Making prioritization defensible

Three practices recur across sources:

| Practice | Source |
|---|---|
| **Expose the method, not just the conclusion.** "Share the processes and steps you're taking to prioritize and slot items on the roadmap, as well as the limitations imposed... by the resources and capabilities of the implementation team" | [S003] |
| **Require evidence of value per item.** "Gut feelings and hunches are for amateurs. Well-documented facts should support this claim" | [S119] |
| **Give every item a business case.** "Decide whether it's increasing a positive... or minimizing a negative... If you can't justify the expense, then it's likely to cause trouble down the line" | [S003] |

## Prioritizing across two user types

[S031] raises a consideration with no precedent elsewhere in the corpus, directly relevant to
products used by AI agents as well as people:

> "**Classify every candidate as human, agent, or both before you score anything; the product
> success metrics that prove value for each stream are different.** ... scoring them on the same
> axis blends two different problems into a single misleading number."

| Stream | Unit of value [S031] |
|---|---|
| **Human users** | "Observable in-product behavior: time to first use, repeat use, depth of use, step-level drop-off rate, retention lift" |
| **Agent users** | "**Task completion.** The metric set looks more like intent resolution rate, tool-call accuracy, authentication success, latency, fallback rate, and human-intervention rate" |

[S031]'s working definition of an agent user is broader than a chatbot: "**anyone configuring
no-code workflows, building automations through Zapier, or extending behavior through your
API.**"

And the consequence for adoption metrics: "**Human-stream adoption is repeated use of a feature
over time, while agent-stream adoption is reliable task completion at scale with low fallback to
a human. Two fundamentally different success conditions are now sitting on the same word.**"

> **Status: single source, vendor, 2026, unverified.** [S031] is the only source in the corpus
> addressing this, it sells agent analytics, and its supporting statistics are not independently
> verifiable here. The *distinction* is logically sound and worth carrying; the specific metrics
> and claims should be treated as one practitioner's proposal. This is a high-priority research
> topic given the intended use of this knowledge base —
> see [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Limitations

- **No empirical evidence** anywhere in the corpus that any prioritization practice improves
  outcomes.
- **No treatment of capacity** — how much can be prioritized *into*. [S003]'s "don't out map your
  team's capabilities" and [S108]'s bet-counting are the closest the corpus comes.
- **No treatment of prioritizing non-feature work** (technical debt, compliance, infrastructure)
  beyond [S119]'s "eat your vegetables" passage and [S031]'s Must-have criteria.
- **No coverage of portfolio-level prioritization across multiple teams or products.**
- Vendor bias throughout; see the source table.

## Related concepts

- [prioritization-frameworks.md](prioritization-frameworks.md)
- [roadmaps.md](roadmaps.md) — the admission filter
- [backlog-management.md](backlog-management.md)
- [roadmap-communication.md](roadmap-communication.md)
- [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md)
- [../02-discovery/identifying-unmet-needs.md](../02-discovery/identifying-unmet-needs.md)
- [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S066 | Atlassian — *Six product prioritization frameworks* | Vendor guide | Why prioritization exists, review cadence |
| S031 | Userpilot — *Feature Prioritization Matrix... 2026* | Vendor blog, opinionated practitioner | Failure modes, kill conditions, cross-functional scoring, two-stream classification, score cautions |
| S039 | ProductPlan — *How to Communicate Your Roadmap to Stakeholders* | Vendor guide | Conversation over technique; stakeholder involvement |
| S040 | Roman Pichler — *Outcome-Based Product Roadmaps* | Named practitioner | Declining requests; empowerment diagnostic |
| S078 | Atlassian (Sherif Mansour) — *Product Manager: Role & Best Practices* | Vendor guide | Prioritization as resource allocation under constraint |
| S119 | ProductPlan — *The Ultimate Guide to Product Roadmaps* | Vendor guide | Placement in flow, evidence requirement |
