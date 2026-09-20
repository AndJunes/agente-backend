---
skill: pre-assertion-check
domain: governance
purpose: Check any claim against what the corpus says is disputed, stale or uncitable, before it is stated
trigger:
  - always, on every claim the agent is about to make
inputs:
  - the claim, and the document it came from
outputs: the claim, qualified — or a refusal
draws_on:
  - 99-reference/disputed-information.md
  - 99-reference/outdated-information.md
  - 99-reference/excluded-content.md
refuses:
  - stating a disputed item as settled
  - citing a figure the corpus marks "do not cite"
  - presenting a dated finding as current
confidence: high
---

## When

Before every assertion. This is not a skill the user asks for; it runs on the output of every
other skill.

## Method

1. **Is the claim in the disputed register?** `disputed-information.md` §8 is explicit: *"Never
   state a disputed item as settled. Say that sources differ, and give both."* Where the
   positions conflict, prefer the higher-tier source — and say that is what you did.
2. **Is it marked "do not cite"?** Two figures in this corpus are reproduced only so the
   claims made around them are visible: the ">90% of unhappy customers never complain" figure
   and the "$3.8 trillion" cost-of-poor-experience figure, both in
   `identifying-unmet-needs.md`. They may be described as claims made by a source. They may
   never be repeated as fact.
3. **Is it `UNVERIFIED` or a `VENDOR PROJECTION`?** Attribute it and say it is unverified. The
   P&G origin story, the Christensen milkshake study, the Netflix ethnography anecdote and the
   attributions for Design Sprint, Lean Startup and the Opportunity Solution Tree are all in
   this class.
4. **Is it time-sensitive?** `outdated-information.md`: *"Method ages slowly. Findings, tools,
   figures and trends age fast."* State the date of any specific claim. Prefer the durable
   layer — how to analyse trends outlives what the trends are. Re-check any tool name, any
   regulatory claim, and **any figure before citing it**.
5. **What is the document's `confidence`?** A `confidence: low` document is a map of what is
   missing, not an answer. Nine documents are at that level and each leads with its own
   coverage warning.
6. **Which provenance level supports it?** A question about what a framework *says* is
   answered from `provenance.primary`. A question about whether something *works* is answered
   from `provenance.empirical` — **and an empty `empirical` list means nobody has measured
   it**, which is an answer worth giving.
7. **Was it excluded?** `excluded-content.md` records what was set aside and why. If the claim
   lives there, it is not in this knowledge base and saying so is the correct response.

## Output

The claim, carrying whatever qualification survived the checks — or a hand-off to
`refuse-with-structure`.

## What this cannot claim

That an unqualified claim is therefore verified. This check can only find what the corpus has
already marked. Silence in the registers is not endorsement.
