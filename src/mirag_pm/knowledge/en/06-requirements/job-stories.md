---
title: Job Stories and When to Prefer Them Over User Stories
domain: requirements
type: artifact
topics:
  - job story
  - user story vs job story
  - trigger motivation outcome
  - JTBD
  - backlog item format
source_count: 3
sources: [S052, S053, S054]
evidence_type: professional-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Job Stories and When to Prefer Them Over User Stories

## Definition and format

A job story describes a need by its **situation** rather than by its **actor**.

> **"When [trigger/situation], I want to [motivation], so I can [expected outcome]."**

The three parts [S053]:

| Part | What it captures |
|---|---|
| **Trigger (situation)** | "The situation that causes the customer to want to complete the task or achieve the goal. **It should be specific and contextual.**" |
| **Motivation** | "The customer's underlying need or desire for completing the task. It should be focused on the customer's **emotional and functional** needs." |
| **Outcome** | "The desired result or benefit that the customer is trying to achieve. **It should be specific and measurable.**" |

**Example** [S053]: *"When I have an important meeting, I want to easily access my presentation
materials on my phone, so I can deliver a polished and professional presentation."*

Further examples [S053]:
- *When I start a new project, I want to be able to easily collaborate with my team and track our progress, so that we can stay organized and meet our deadlines*
- *When I receive an email with an attachment, I want to be able to save the attachment to the correct folder, so that I can stay organized and easily access the file later*

## Origin

[S053]: "The term 'job story' was coined by **Alan Klement**, a product designer and
Jobs-to-be-Done practitioner. Klement first introduced the concept of job stories in his 2014
book *When Coffee and Kale Compete*."

[S052] (Mountain Goat Software / Mike Cohn) gives a complementary attribution: "Job stories
**originated at Intercom** and were best explained by Alan Klement."

> Two independent corpus sources agree on Klement's central role. **Klement's book is not in the
> corpus**, so the attribution is second-hand but doubly corroborated.

## The difference from user stories, demonstrated

[S052] is the most valuable source here because it argues the case with worked pairs rather than
asserting a preference. Mike Cohn — closely associated with user stories — nonetheless makes the
case *for* job stories in specific circumstances.

### Example 1 — duplicate order warning

| Format | Story |
|---|---|
| **Job story** | *When an order is submitted, I want to see a warning message so I can avoid resubmitting the order.* |
| **User story** | *As a customer, I want to be shown a message telling me not to submit an order twice so that I don't place a duplicate order.* |

[S052] gives **two reasons the job story is superior here**:

1. **The actor is uninformative.** "This story applies to everyone making a purchase on the
   site. So it's not important to know the person doing this is a customer. (In fact, calling
   the person a customer **could be misleading** because the person may not be a customer until
   this order has been placed.)"
2. **The user story omits *when*, and that omission is exploitable.** "Look carefully at the
   user story and you'll notice that **it never tells us when this message is displayed. The
   team could 'successfully' implement the user story by adding an item on an FAQ page** warning
   against double submitting orders. That is almost certainly not what the product owner wants."

> This second point is the strongest argument in the corpus for job stories: **a missing trigger
> creates a gap between a satisfiable story and a satisfied need.**

### Example 2 — postal code validation

| Format | Story |
|---|---|
| **Job story** | *When searching by US ZIP code, I want to be required to enter a 5- or 9-digit code so I don't waste time searching for a clearly invalid postal code.* |
| **User story** | *As a user, I want to be required to enter a 5- or 9-digit postal code so I don't waste time searching for a clearly invalid postal code.* |

[S052]'s observation: "These two stories highlight that **the difference between user and job
stories exists in the first part of the templates.** The *when…* and *As a …* clauses differ but
in this example, the remainder of each story is identical."

And the diagnostic: the user story here reads "As a user…" — generic — "which is why" the actor
adds nothing.

## Decision rule: which format to use

[S052] states it cleanly, and this is the most decision-relevant content in this document:

> **"If your product has users and those users' needs differ in important ways, I suggest user
> stories.** The additional emphasis a user story puts on who is performing the action can lead
> to insights about user behavior.
>
> **If, however, your product's users do not differ in significant ways, job stories are likely
> the better approach."**

### The practical smell test
> "If you've ever written a lengthy set of user stories and started each with 'As a user…',
> you've encountered this problem. **When a large set of user stories all begin with 'As a
> user…' you've got a set of stories for whom the user is not very important.**" [S052]

> **Operational heuristic:** *Start by writing job stories any time you are tempted to write a
> batch of stories all beginning with "As a user…"* [S052]

### They are not mutually exclusive
[S052]: "each is great and has its own advantages. During the course of any week, I will write
some user stories and some job stories. **The two techniques are quite compatible and there's no
reason to view them as mutually exclusive.** A good starting point is to **mix user and job
stories in the same product backlog.**"

## Combining the strengths of both

[S052] shows that the two formats converge when you patch each one's weakness.

**Add an actor to a job story:**
> *When searching by postal code, **a buyer wants** to be required to enter a valid code so **the
> buyer doesn't** waste time searching for a clearly invalid postal code.*

**Add a trigger to a user story:**
> *As a user **who is searching by postal code**, I want to be required to enter a valid postal
> code so I don't waste time searching for a clearly invalid postal code.*

[S052]'s conclusion: "The modified user and job stories are **semantically the same**. Which you
choose is entirely up to you. **I personally prefer the modified user story** over the modified
job story because it keeps the story in first person."

> Note this is stated as a personal preference by the author, explicitly labelled as such — not
> as a recommendation.

## A second, different comparison

[S053] draws the distinction differently, and the difference is worth preserving because it
does not fully agree with [S052].

| | Job stories [S053] | User stories [S053] |
|---|---|---|
| **Basis** | "Rooted in research and specific context, allowing for a deeper understanding of the user's situation" | "Commonly written based on **assumptions and generalizations** about the user, such as their goals, preferences, and behaviors" |
| **Focus** | "The outcome the customer is trying to achieve, rather than the specific product features they need" | "A feature or requirement from the perspective of the end user"; "more task focused" |
| **Best phase** | "The **discovery phase** of a project when the team is trying to understand customer needs and design effective solutions" | "More mature products with existing problem-solution fit, **or** more immature environments where product owners and stakeholders are more task and output focused than outcome focused" |

### Where the two sources disagree
[S053] claims "job stories are often **preferred** in product development, as they lead to more
effective and relevant solutions." [S052] makes no such general claim and instead conditions the
choice on whether users differ meaningfully.

> **Treat [S052]'s conditional rule as the better-grounded position.** It is argued with worked
> examples by an author with no stake in promoting JTBD; [S053]'s preference claim is asserted
> without evidence, in a glossary that sells JTBD workshop materials.

### A caveat [S053] adds that is worth keeping
> "However, the research practices of the product team must follow with the use of job stories.
> **Job stories without research do not just represent assumptions, but untested hypotheses.**"

This matters: the claim that job stories are "rooted in research" is **conditional on actually
doing the research**. A job story invented at a desk has all the weaknesses [S053] attributes to
user stories, plus false authority.

## Why teams use job stories

[S053]'s stated benefits:

- **Focused on customer needs** — "shift the focus away from the product and towards the
  customer's desired outcome"
- **Provides context** — "around *why* a customer is trying to achieve a specific goal"
- **Easy to understand** — "simple and clear language"
- **Aligns the team on context, motivation, and research**
- **Avoids feature-based thinking** — "focus on the customer's desired outcome, not specific
  product features"

## Who writes them

[S053]: "written in collaboration by the product team, which typically includes a **product
manager, lead designer, and a lead engineer**. If possible, stakeholders should join in as
well... it's a collaborative effort where everyone within the product team and outside the
product team can suggest stories."

Role contributions named: designers create "user interface designs that support the job story";
engineers "build the product and ensure that it meets the technical requirements necessary to
support the job story."

## Turning a job story into a testable hypothesis

[S053] describes a use for job stories that has no equivalent for user stories, and it connects
this artefact to validation:

> "The **trigger** in a job story describes the situation and context that prompts the user to
> perform a particular job or task. This is exactly what we need to craft a testable hypothesis."

**Template:** *If [trigger happens] then [desired outcome will happen].*

**Worked example** [S053]: if the trigger is "a customer needing to purchase a product quickly
before leaving for vacation, a testable hypothesis could be that customers are more likely to
make a purchase if they are presented with a time-sensitive offer or discount at checkout. To
test this hypothesis, the product team could implement a feature that presents a time-limited
offer to customers at checkout, and **measure the impact on the conversion rate.**"

### Feeding assumption mapping
[S053] connects job stories to **David Bland's assumptions mapping exercise**: "Job stories can
be a valuable input for this exercise, as they provide a clear understanding of the user's
specific needs and tasks, which can help to identify and validate the assumptions being made."

Its example: a job story about finding and purchasing an item on an e-commerce site generates
assumptions "about the user's preferences for search functionality, the layout of the website,
and the checkout process," which can then be tested "using the job story as a basis for the
testing scenario."

See [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md).

## Metrics associated with job stories

[S053] names candidate measures: "Time to complete the task, accuracy of the completed task,
customer satisfaction ratings, cost savings or revenue generated, and employee engagement and
satisfaction levels."

## Limitations

- **[S053] is a glossary entry** that sells workshop card decks; its comparative claims about
  job stories being generally preferable are unsupported.
- **Klement's primary text is not in the corpus.** Neither is Intercom's original account.
- **No guidance on writing job stories badly or well** beyond "specific and contextual." There
  is no job-story equivalent of [S127]'s weak/strong analysis in
  [user-stories.md](user-stories.md).
- **The corpus does not address** how job stories interact with estimation, splitting, or
  acceptance criteria — all of which are documented for user stories.
- [S052]'s examples are both validation/messaging behaviours where the actor genuinely does not
  matter. Whether the rule generalises to richer feature work is not demonstrated.

## Related concepts

- [user-stories.md](user-stories.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [../02-discovery/jobs-to-be-done.md](../02-discovery/jobs-to-be-done.md) — the framework job stories come from
- [../02-discovery/hypotheses-and-assumptions.md](../02-discovery/hypotheses-and-assumptions.md)
- [prd.md](prd.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S052 | Mountain Goat Software (Mike Cohn) — *Job Stories Offer a Viable Alternative to User Stories*, last updated 11 Jul 2024 | Practitioner guide; author is a primary authority on user stories arguing for the alternative | Worked comparisons, the decision rule, the "As a user…" smell test, combining both formats |
| S053 | Learning Loop — *Job Story (JTBD): What it is, How it Works, Examples* | Practitioner glossary | Format and parts, Klement origin, benefits, authorship, hypothesis derivation, assumption mapping link, metrics |
| S054 | Mind the Product (Mike Belsito) — *Jobs to be done for Product Managers* | Practitioner essay | Job story as JTBD synthesis artefact |
