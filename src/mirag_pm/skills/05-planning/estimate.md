---
skill: estimate
domain: planning
purpose: Refuse to estimate in the way being asked, then offer what the corpus does support
trigger:
  - how long will this take
  - story points
  - velocity
  - planning poker
inputs:
  - the work in question
draws_on:
  - 05-planning/estimation.md
refuses:
  - story points
  - velocity
  - planning poker
  - a duration
outputs: a refusal with the supported alternative
confidence: high
---

## When

Every time an estimate is requested. **This skill exists to be a refusal.** Without it the
model fills the gap from memory, which is exactly the failure the corpus warns about.

## Method

1. Answer what the frameworks prescribe: **nothing**. `scrum.md` has a section titled *Scrum
   does not define estimation*; the frameworks are silent on story points and always were.
2. Offer what is supported: **probabilistic forecasting** — a range with a confidence, from
   observed throughput.
3. Say what is not answerable from here: story points, velocity, planning poker. 🟨 in the
   gap register.

## Output

What the frameworks say, what forecasting offers, and an explicit list of what is not
available.

## What this cannot claim

A number. Not a range invented on the spot either — probabilistic forecasting needs observed
throughput, and without it there is no forecast.
