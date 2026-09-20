---
title: Outcome-Based Roadmaps
domain: planning
type: framework
topics:
  - outcome-based roadmap
  - goal-oriented roadmap
  - GO Product Roadmap
  - outcomes over outputs
  - feature factory
  - roadmap transition
source_count: 4
sources: [S040, S062, S063, S130]
evidence_type: practitioner-framework
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Outcome-Based Roadmaps

## The core shift

> Rather than asking, **"What are we building next?"** teams ask, **"What impact are we trying
> to achieve?"** [S062]

[S040] (Roman Pichler) states the same inversion: "instead of determining features, you first and
foremost consider **the specific value the product should create — the outcomes it should
achieve**... instead of focussing on **what** needs to be delivered, you ask **why** it is
worthwhile progressing the product."

### Worked contrast

| Traditional / feature-based | Outcome-based |
|---|---|
| "Add notifications" / "improve search function" [S062] | "Increase user engagement by 20%" [S062] |
| "Deliver Payment Gateway Integration by April" [S130] | "Enable seamless payment experiences to boost transaction completion rates by 15%" [S130] |
| "New reporting features" [S062] | "Improving reporting accuracy by 15%" [S062] |
| "Prioritise the search results" / "improve the search algorithm" — [S040] names these as **feature-based goals masquerading as outcomes** | "Increase conversion by 5%" [S040] |

[S040]'s test for whether a goal is genuinely outcome-based: **"Make sure that the goal states
the positive impact you want to make on the users/customers and the business... Think why, not
what."** And it must be "specific and measurable so that you can clearly tell if it has been
met."

### Why the shift changes behaviour
[S062]: from an outcome, "the product team can explore **different ways** to achieve this
outcome — whether it's through notifications, a more intuitive search, or personalized
recommendations."

[S130]: "It motivates teams to find the most effective way to achieve the desired outcome,
whether it's through faster APIs, better user flows, or enhanced security measures."

> **The mechanism:** a feature on a roadmap forecloses the solution space before discovery
> happens. An outcome keeps it open. This is the same argument [S127] makes for user stories
> that name a decision rather than an artefact — see
> [../06-requirements/user-stories.md](../06-requirements/user-stories.md).

## Origin

[S062]: "This approach grew roots in **Lean and Agile methodologies**... which emphasize
adaptability and customer value over rigid planning."

[S040] names a specific template: **the GO Product Roadmap**, which Pichler authored. Its
structure, as described: "places the outcomes at the centre of the roadmap. It uses selected
features. But these must help meet the goals. Additionally, they have to be **coarse-grained and
are limited to three to five capabilities per goal.**"

> The constraint — *3–5 coarse-grained capabilities per goal* — is the only concrete sizing rule
> for roadmap content in the corpus.

## Why a feature-based roadmap is risky

[S040] states the failure condition precisely, and is careful to say when it does *not* apply:

> "A traditional roadmap is essentially a list of features, which are mapped onto a timeline.
> **Such a plan might work if there is little uncertainty, change, and innovation present, and
> you can correctly predict what the product should look like and do.** But in today's
> fast-changing digital product space, that's hardly ever the case. Using a feature-based
> roadmap that fixes the product functionality for the next, say, twelve months therefore risks
> creating a product that **offers the wrong functionality and creates little value.**"

[S062] names the organizational pathology: a feature-based roadmap "can lead to what's called a
**'feature factory' mentality**, where the emphasis is on building rather than solving strategic
problems," and to "**feature creep**, where irrelevant and unimpactful features find their way to
production."

## Process: transitioning an organization that expects features

This is the most useful content in the corpus on this topic, because it treats adoption as the
hard part. [S040]'s four steps address the situation where "management and business stakeholders
can be very attached to feature-based plans."

### Step 1 — Set one outcome-based goal for the next three months
- **A single goal.** Not a roadmap. Example: "increase conversion by 5%."
- Involve **key stakeholders and development team representatives** in setting it — "This helps
  you leverage their knowledge, it creates transparency."
- The aim is a state where "**nobody involved in the goal-setting process has any meaningful
  objections against the goal.**"
- Run it as a collaborative workshop, onsite or online. "Ask a **skilled facilitator** to run the
  session especially when the attendees don't know each other well and the level of trust is low.
  This frees you from having to facilitate and allows you to focus on setting the right goal."

### Step 2 — Use the outcome to determine the features
This step is where the discipline actually bites:

- **"Start by removing any backlog items which are not required to create the desired outcome.
  Delete or archive them."**
- Then ask what must change to meet the goal: "Does the user experience have to be adapted? Do
  you have to add or change any functionality? Do you have to meet new or enhanced
  **non-functional requirements including compliance standards**? Are **bug fixes and
  architecture refactoring** work required to achieve the outcome?"
- **"Decline any feature requests that do not help you meet the goal. Use the outcome as your
  decision tool and stick to it — unless it becomes invalid."**

[S040] anticipates the failure: "**Don't make the mistake of accepting a feature to please a
stakeholder or avoid a difficult conversation. Saying no is part and parcel of a product
person's job.**"

And it adds a diagnostic that reframes the whole problem:

> "**If you cannot decline a feature request, you lack the necessary level of empowerment to do
> an effective product management job.**" [S040]

> This is worth holding onto. An inability to run outcome-based roadmaps is often not a
> methodology problem but an **authority** problem. See
> [../01-foundations/product-manager-role.md](../01-foundations/product-manager-role.md) on
> owning outcomes without owning authority.

### Step 3 — Review the approach after three months
Questions [S040] poses: "What went well and what didn't? **Did you manage to meet the goal?** How
beneficial was using the agreed outcome to determine the product features? To what extent do
management and business stakeholders support an outcome-based roadmap?"

**If partially successful or support is still low:** repeat steps 1 and 2 with a new three-month
goal. [S040]'s prompts for doing it better: "Should you, for example, involve the stakeholders
more closely in the goal-setting process? Should you do a better job of focusing everyone on the
outcome? **Should you be more ruthless and decline feature requests that don't fit the goal?**"

### Step 4 — Build the outcome-based roadmap
Only now: "set outcomes for the next **six to twelve months** and build an outcome-based product
roadmap."

**Precondition** [S040]: "before you build your outcome-based roadmap, **ensure that a valid
product strategy exists.** Such a strategy should state the users and customers who will benefit
from the product, the needs the product will address, the business benefits it will offer, and
the standout features which will set it apart from competing offerings."

**Two ways to derive roadmap outcomes from strategy** [S040]:
1. "Derive the roadmap goals **directly from the needs and business goals** by breaking them into
   subgoals."
2. "Use your **key performance indicators (KPIs)** to discover outcomes such as increasing
   engagement and reducing churn — as long as these are aligned with the needs and business goals
   in the strategy."

> **Why the staging matters.** Steps 1–3 build evidence and trust with one three-month goal
> before asking stakeholders to accept a twelve-month plan with no feature list. The sequence is
> the method; skipping to step 4 is how the transition fails.

## Relationship to OKRs and Scrum

[S040] maps the concepts explicitly:
- "If you use objectives and key results, OKRs, then you can **view the goal as an objective.**"
- "If you apply a Scrum-based process, you can **regard the outcome as a product goal.**"

[S062] recommends OKRs as the organising framework: "Use a framework like OKRs (Objectives and
Key Results) to organize objectives and outcomes. This will make them easier to track and
measure."

See [../04-strategy/okrs.md](../04-strategy/okrs.md).

## Advantages

[S062]:
- **Aligns teams with strategic goals** — "each team understands how their work contributes to
  broader business objectives"
- **Enhances flexibility in fast-changing markets** — "enable teams to pivot strategies as market
  conditions shift"
- **Provides clearer success metrics** — "define desired results upfront... makes it easier to
  track and measure success"
- **Encourages a user-centric approach** — "centering on solving real customer problems"
- **Supports cross-functional collaboration** — "everyone aligns toward achieving specific
  outcomes. This breaks down silos"

## Limitations and when outcome-based roadmaps do not fit

[S062] is unusually candid here, and this section should not be compressed.

| Limitation | Description [S062] |
|---|---|
| **Requires high-level strategy and buy-in** | "Without a clear understanding of strategic objectives from leadership, teams may struggle to set outcomes. This leads to misaligned efforts and wasted time. **If buy-in is lacking, teams may revert to feature-driven plans**, which dilutes the roadmap's focus" |
| **Resource-intensive to maintain** | "Defining, tracking, and revising outcomes demands product analysis and feedback loops, which adds complexity. **Smaller teams or those with limited resources may find it challenging to maintain this data-driven focus**" |
| **Hard to break large goals down** | "Translating broad outcomes into actionable tasks can be difficult, especially for teams new to outcome-based approaches. This can lead to costly delays as teams struggle to connect daily tasks with high-level objectives" |
| **May misalign with stakeholder expectations** | "**Stakeholders who expect concrete deliverables or timelines may feel uncertain if the roadmap lacks specific deadlines.** This can create communication challenges... potentially impacting stakeholder trust" |
| **Does not suit all project types** | "**Less effective for projects that require a strict, feature-driven approach or predictable delivery schedules. In regulated industries or projects with fixed deadlines, this type of roadmap may lack precision.**" |

> **The honest summary:** outcome-based roadmapping requires strategic clarity from leadership,
> analytical capacity to measure outcomes, and stakeholder tolerance for date ambiguity. Where
> any of the three is missing, it degrades — and [S062] notes the specific degradation mode:
> teams quietly revert to feature lists.

[S062] offers the hybrid for regulated or deadline-bound contexts: "a hybrid approach that
combines **timeline predictability with outcome goals** might work best."

## Distinguishing outcome-based from its near-relatives

[S062] separates four roadmap types that are often conflated. The distinctions are subtle but
real:

| Type | What it organises around | How it differs from outcome-based [S062] |
|---|---|---|
| **Feature-based** | Deliverables | "Straightforward and works well for communicating specific product enhancements... in highly structured environments," but risks feature-factory and feature creep |
| **Timeline-based** | Deadlines and milestones | "The linear view makes tracking and accountability straightforward. However, sometimes it's known to become rigid and challenging to adjust in fast-changing environments" |
| **Now-Next-Later** | Priority buckets | "Similar... in its flexibility," but "**they don't inherently focus on specific outcomes.** A con is that they can leave some product teams lacking outcome orientation" |
| **Goal-oriented** | High-level objectives ("Expand into new markets") | "**Close relatives.** Where they differ is in their level of specificity around measurable outcomes." Outcome-based "goes further by defining clear, trackable product metrics" |

### The recommended combination
[S062] on Now-Next-Later specifically: "many product teams find success by combining these two
approaches. They use **Now-Next-Later for broad timeframes and an outcome-based structure to
clarify the desired impact** of each initiative within those timeframes." Example: list "Improve
onboarding experience" in *Now*, and add "increase new user retention by 20%" as its outcome.

## Limitations of this document

- [S040] is the strongest source here — a named practitioner (Roman Pichler) writing about his
  own coaching practice, with a specific dated publication (10 June 2024) and a concrete
  template. But it is also **promotional for his book, workshop and template**; its four-step
  process is the substance and has been retained separately from that.
- [S062] is a training-provider guide. Its pros list is generic; **its cons list is its valuable
  contribution** and is preserved in full above.
- **No evidence** that outcome-based roadmaps produce better outcomes than feature-based ones.
  Both [S040] and [S062] argue from reasoning and experience.
- [S062]'s three roadmap examples are attributed (Jason Doherty in *The Startup*; Itamar Gilad)
  but the images did not extract, so the examples' structure is described rather than shown.

## Related concepts

- [roadmaps.md](roadmaps.md)
- [roadmap-formats.md](roadmap-formats.md)
- [continuous-roadmapping.md](continuous-roadmapping.md)
- [../04-strategy/okrs.md](../04-strategy/okrs.md)
- [../04-strategy/product-goals.md](../04-strategy/product-goals.md)
- [../04-strategy/product-strategy.md](../04-strategy/product-strategy.md) — the precondition
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S040 | Roman Pichler — *How to Get Started with Outcome-Based Product Roadmaps*, 10 Jun 2024 | Named practitioner, coach and author | Traditional vs outcome-based, four-step transition, goal-setting rules, GO Product Roadmap, strategy precondition, empowerment diagnostic |
| S062 | Product School — *Outcome-Based Roadmaps: Mapping Impact, Not Features* | Training-provider guide | Definition, examples, pros, **cons and non-fit conditions**, roadmap-type comparisons, creation steps |
| S063 | ProductPlan — *Outcome-Driven Roadmapping* | Vendor guide | Outcome-driven framing (content largely promotional) |
| S130 | Product School — *What Are Agile Roadmaps and How to Build Them* | Training-provider guide | Traditional vs agile roadmap contrast, worked example |
