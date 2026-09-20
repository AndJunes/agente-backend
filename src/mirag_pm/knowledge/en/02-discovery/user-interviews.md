---
title: User Interviews and Interview Guides
domain: discovery
type: technique
topics:
  - user interviews
  - interview guide
  - discussion guide
  - semistructured interview
  - probing questions
  - open-ended questions
  - critical incident method
source_count: 3
sources: [S142, S074, S054]
evidence_type: professional-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# User Interviews and Interview Guides

## Definition

[S142] (Nielsen Norman Group): in the discovery phase of product development, user interviews
"capture important information about users: their backgrounds, beliefs, motivations, desires,
or needs."

Interviews at this stage are typically **semistructured** — "referred to as 'depth interviews'
by market researchers" — meaning "they generally have a predefined structure, but also allow
the interviewer the flexibility to follow up on significant statements made by participants."

## Guide versus script — a distinction that matters

[S142] separates two artefacts that are often conflated:

| Artefact | Used in | Property |
|---|---|---|
| **Interview script** | Structured interviews | Followed as written |
| **Interview guide** (also *discussion guide*) | Semistructured interviews | "Can be used flexibly: interviewers can ask questions in any order they see fit, omit questions, or ask questions that are not in the guide" |

## Why a guide is necessary

[S142] names the two specific risks of interviewing without one:

- **Asking leading questions** "as you try to think of questions on the spot"
- **Not covering topics relevant to your research questions** in each interview

> "Ultimately, without an interview guide, you are in danger of compromising the validity of
> your data." [S142]

It also sets a realistic expectation on effort: "Constructing a good interview guide can be
tricky and time-consuming. **It's not uncommon to spend a full day crafting one.**"

## Process: building an interview guide in seven steps

This is [S142]'s procedure, reproduced with its reasoning intact.

### Step 1 — Write your research questions
Research questions come **before** interview questions and shape them. They are not the same
thing. Examples given:
- What are users' expectations in this situation?
- How do users make a decision in this situation?
- How have users managed to solve this problem in the past?
- What aspects of this product do users care most about, and why?

### Step 2 — Brainstorm interview questions
"Note down all interview questions that come to mind. It doesn't matter whether they are good
or poor — you'll deal with that later." Mind maps, whiteboards or a list all work. If further
*research* questions surface here, add them to the list from Step 1.

### Step 3 — Broaden your questions
[S142] predicts what Step 2 produces: "It's typical after step 2 to have a long list of mostly
closed questions." Closed questions are a problem because they "won't allow for unanticipated
stories and statements to emerge and can limit your ability to build rapport."

The test to apply to each question: **"is there a broader, more open-ended version of that
question that you can ask instead?"**

**Worked example** [S142] — these four closed questions in an employee interview:
- Do you work in an office?
- Is the work mostly desk-based or paper-based?
- Do you have to attend meetings during the workday?
- Do you work in a team?

…can all be replaced by asking the participant to **describe a typical day at work**. Anything
not covered can be asked as a follow-up.

**Recall-prompting questions.** [S142] notes these are "similar to those used in the
critical-incident method" and "are excellent for gathering stories and unanticipated
statements." Example set, for research on cooking at home:
- Tell me about the last time you cooked at home.
- Tell me about a time where you cooked something new.
- Tell me about a time when you cooked something that turned out well.
- Tell me about a time when you cooked something that didn't turn out as you hoped.
- Tell me about a time when you were thinking about cooking something but decided to get
  takeout instead.

### Step 4 — Fill in for unaccounted research questions
"Align each interview question to your research questions. If you have research questions that
are not addressed by any of your interview questions, fill in the gap." Then repeat Step 3 on
the new questions.

[S142] notes some researchers display the research questions at the top of the guide or
alongside the interview questions as a reminder of the aims.

### Step 5 — Arrange your questions
Order for natural flow:
- **Chronological order** works when discussing an experience people have had.
- If the experience has set phases — "such as discover, choose, purchase, use, review" — that
  you have documented in a user-journey map, service blueprint or experience map, align the
  questions to those phases.
- **Warm-up questions** should be open-ended and easy to answer, to build rapport.
  "Tell me a little about yourself" is given as a typical opener.
- **Questions requiring reflection go later.** [S142] gives the reason: "introducing them too
  early could be overwhelming and you might get stereotypical responses, as participants
  haven't had a chance to recall events, feelings, and form judgments."

### Step 6 — Prepare probing and follow-up questions
Prepared in advance, per question, so you remember to ask them.

- **Follow-up** (detail and clarification): "Where were you when this happened?", "When did
  that happen?", "Tell me why you did that?"
- **Probing** (depth): "Tell me more about that", "Tell me why you felt that way", "Why is
  that important to you?"

### Step 7 — Pilot your guide
Piloting reveals:
- Questions you should ask but haven't included
- Questions that need rewording
- Whether the question order works
- Whether you will have time for all your questions

"It's okay to make updates to your guide throughout your interviews, but the point of piloting
your guide is to fix any glaring issues before commencing research." [S142]

## JTBD interviews are a different instrument

[S054] identifies four ways a Jobs-to-be-Done interview differs from a general user interview.
**These are not interchangeable techniques.**

1. **Focus is a purchase decision**, not general feedback or usability issues. "The goal is to
   understand the full context and timeline of the decision-making process, from first thought
   to final purchase."
2. **Goes deep into emotional and social aspects**, not just functional requirements — probing
   "the underlying anxieties, aspirations, and influences."
3. **Conducted with customers who have recently made a purchase**, rather than any product
   user — "This ensures the insights are grounded in real, recent experiences rather than
   hypotheticals."
4. **Follows a specific structure to uncover causality and context** — "the chain of events
   and reasoning that led to the purchase."

**Length:** [S054] states JTBD interviews "typically last 60-90 minutes" — "likely much longer
than the typical user interviews you may have conducted." Bob Moesta's framing, as reported:
"you must act as if you're a documentary filmmaker and need the time to uncover the true
story."

**Structure** [S054]: background questions → the specific purchase story (timeline, key events,
emotional states) → reflective questions on satisfaction and remaining unmet needs.

See [jobs-to-be-done.md](jobs-to-be-done.md).

## Conduct during the interview

[S054] on running the session:
- Start with "a warm introduction, explaining the purpose of the interview, and assuring the
  participant that there are no right or wrong answers."
- Practise active listening; dig deeper "into interesting or surprising responses."
- **"Focus on capturing the customer's story in their own words without injecting your own
  opinions or assumptions."**
- "Avoid leading or yes/no questions that can bias the response."
- Ideally have a dedicated note-taker; otherwise record the session **with the participant's
  agreement**.

[S074] adds: record and transcribe, then "create a data visualization like a mind map or a
word cloud" to turn interviews into actionable information.

## Synthesis

[S054] describes synthesis as pattern-finding across stories, looking for:
- Similar triggering events or struggling moments
- Common criteria used to evaluate options
- Shared anxieties or hesitations
- **Recurring language or phrases** used to describe needs or desired outcomes

It raises a failure mode rarely mentioned elsewhere:

> "You may be surprised that your interview assessment may contrast with somebody else's —
> even though you both were a part of the same session and read the same interview notes. It's
> important to talk openly about your findings and any potential discrepancies." [S054]

For discovery-wide synthesis, [S028] describes **affinity-diagramming workshops** — see
[product-discovery.md](product-discovery.md).

## Limitations and trade-offs

- **Cost.** [S074]: interviews are "very time and resource intensive, more so than other
  methods."
- **Attitudinal.** Interviews capture what people *say*. See
  [user-research-methods.md](user-research-methods.md) for why this matters and when
  behavioural methods should be preferred.
- **Sample.** The corpus gives **no guidance on how many user interviews constitute enough**
  for discovery. [S081] suggests "a minimum of 8–10 quality conversations to identify clear
  patterns" for opportunity validation, and [S099] cites NN/g's recommendation of ~5
  participants per user group for *qualitative usability testing* — a different method. These
  numbers should not be transferred between methods.
- **Interviewer skill is a variable the corpus treats lightly.** [S064] documents concern that
  "UX Research done by non-researchers often does not meet our quality or process standards."
- No coverage of participant compensation, consent, recruitment screening, or interviewing
  across languages and cultures.

## Related concepts

- [user-research-methods.md](user-research-methods.md)
- [jobs-to-be-done.md](jobs-to-be-done.md)
- [product-discovery.md](product-discovery.md)
- [surveys.md](surveys.md) — stakeholder surveys as an asynchronous substitute for stakeholder interviews
- [identifying-unmet-needs.md](identifying-unmet-needs.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S142 | Nielsen Norman Group, Maria Rosala — *Writing an Effective Guide for a UX Interview*, 28 Feb 2021 | UX research organization | Guide vs script, seven-step process, question design, ordering rationale, piloting |
| S054 | Mind the Product, Mike Belsito — *Jobs to be done for Product Managers* | Practitioner essay | JTBD interview differences, length, structure, conduct, synthesis |
| S074 | Product School — *Product Management Skills: User Research* | Training-provider blog | Interview pros/cons, recording and visualization |
