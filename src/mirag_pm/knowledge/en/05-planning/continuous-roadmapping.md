---
title: Continuous Roadmapping
domain: planning
type: technique
topics:
  - continuous roadmapping
  - big-batch planning
  - bets
  - premature convergence
  - rolling planning
  - north star metric
source_count: 1
sources: [S108]
evidence_type: practitioner-opinion
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Continuous Roadmapping

## The problem it addresses

[S108] (John Cutler, *The Beautiful Mess*, 7 Jan 2021) identifies a failure mode in how roadmaps
are produced rather than in what they contain:

> "How many roadmaps are the result of **rushed, big-batch planning efforts?** Lots.
>
> You've got four weeks at the end of the year (or ten days at the end of the quarter) to get it
> right. Quick! Quick! Imagine the amount of money invested this way. And the dollars wasted
> because of **premature convergence.**"

It names the opposite failure too, and rejects it equally:

> "The flip side is **playing whack-a-mole… doing whatever is hot at the moment.** Who needs a
> stinkin' roadmap or strategy anyway? This is costly as well."

> **The framing is the contribution.** Most roadmap guidance treats "have a roadmap" versus
> "don't have one" as the choice. [S108] identifies a third option: the problem is not the
> roadmap's existence but the **batching of the decisions that produce it.**

## The mechanism

[S108] proposes sizing the roadmap by throughput rather than by calendar:

> "Say our bets take, on average, **six weeks** to put in motion. To have a year's worth of work
> 'ready', we'd need **eight bets on the board.**"

### The board structure

| Stage | Count | Detail required |
|---|---|---|
| **In Progress** | 1 | Detailed — "outcome-oriented one-pagers that leave room for creative solutions" |
| **Up Next** | 1 | Detailed, plus "some discovery and research with our team" |
| **Ideas / Options** | 6 | "High-level options" |

> "**Only two of our bets — the single item in Up Next, and the single item in In Progress — need
> detail.**" [S108]

This is the same progressive-detail principle that [S127] applies to backlog items — detail is
added as work approaches, not in advance. See
[../06-requirements/user-stories.md](../06-requirements/user-stories.md).

### How it runs
> "When we finish something, we **pull in the next item from Up Next** (and pick the next
> idea/option to start thinking about)...
>
> The important point here is that we try to **keep this board filled at all times with eight
> cards.** Eight cards! That's manageable. **As new information becomes available, we swap in
> cards as necessary.**" [S108]

### Grounding it in strategy
[S108]: "Note how I use a **North Star Metric and Inputs** to ground the roadmap in our strategy,
and introduce the idea of **persistent goals**."

*(The referenced diagram did not extract; "Inputs" and "persistent goals" are named but not
defined in the corpus. See [../09-metrics/north-star-metric.md](../09-metrics/north-star-metric.md)
for what the corpus contains on North Star Metrics — which is very little.)*

## Objections and answers

[S108] pre-empts three, and the answers carry most of the argument.

### "That's a year's worth of planned work!"
> "I don't see it that way. **That would be the case if the work was all committed and promised.**
> Instead, I see this as a **current snapshot of where the team imagines the product is going.**
> We avoid the rush to 'fill' the roadmap at the most inopportune times."

> The distinction between *a snapshot of current thinking* and *a commitment* is exactly the
> roadmap/release-plan boundary in
> [roadmap-vs-backlog-vs-release-plan.md](roadmap-vs-backlog-vs-release-plan.md).

### "But what if we change our strategy each year?"
> "**At least you'll be able to discuss the delta between your current mental model, and the new
> mental model.**"

> This reframes the roadmap as a **record of assumptions** whose value partly survives being
> wrong — you learn from the difference.

### "But 8 items seems too few!" / "Our team releases 25 features a year!"
> "**Forget estimation. What has happened in the past?** I see teams **pack their roadmaps like
> they're playing Tetris, only to discover — over and over — that they 'don't get to things'.**
> And do that over and over. **Stop the charade!**"
>
> "Try to **go up a level and think beyond features. What are the actual missions?**"

> Two distinct arguments here: (1) use **historical throughput** rather than estimates to size
> the board; (2) if the board seems too small, the items may be at the wrong altitude — twenty-five
> features probably roll up to a much smaller number of missions.

## The test it proposes

> "**What would it take for you to have an always up-to-date roadmap?**" [S108]

This is a useful diagnostic question. If the honest answer involves a multi-week planning cycle,
the roadmap will be stale between cycles by construction — which is the condition [S119]
identifies as actively harmful: "An outdated roadmap only leads to confusion and false
expectations."

## Limitations

- **Single source, and a short one.** [S108] is a ~570-word newsletter post. It is a proposal
  sketch, not a method. Several referenced elements (the diagram, "Inputs", "persistent goals")
  are not recoverable from the corpus.
- **No evidence.** The cost claims ("I bet it is billions of dollars") are explicitly the
  author's speculation, phrased as such.
- **The six-week bet duration is an example, not a finding.** The structure depends entirely on
  a team knowing its own historical cycle time — which [S108] assumes is knowable and most of
  the corpus never addresses.
- **It assumes a single-team, single-stream context.** How eight bets work across a portfolio, or
  with dependencies between bets, is not addressed. See [dependencies.md](dependencies.md).
- **Dated January 2021.** The argument is structural rather than technology-dependent, so it
  ages better than most, but it predates the material in [S031] on AI-accelerated delivery
  cycles — which, if accurate, would change the bet-duration input substantially.

## Related concepts

- [roadmaps.md](roadmaps.md) — keeping roadmaps current
- [outcome-based-roadmaps.md](outcome-based-roadmaps.md) — "outcome-oriented one-pagers"
- [roadmap-formats.md](roadmap-formats.md) — Now-Next-Later, which shares the staged structure
- [roadmap-vs-backlog-vs-release-plan.md](roadmap-vs-backlog-vs-release-plan.md)
- [estimation.md](estimation.md) — "forget estimation" as a position
- [../09-metrics/north-star-metric.md](../09-metrics/north-star-metric.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S108 | John Cutler — *TBM 2.1/52: Continuous Roadmapping*, 7 Jan 2021 | Named practitioner newsletter | Entire document |
