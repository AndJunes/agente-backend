---
title: Surveys in Product Research
domain: discovery
type: technique
topics:
  - surveys
  - survey design
  - NPS
  - CSAT
  - CES
  - SUS
  - SEQ
  - questionnaire
  - survey misuse
source_count: 2
sources: [S105, S044]
evidence_type: empirical-and-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Surveys in Product Research

## Why this document leads with the warnings

Surveys are the most-used and most-misused research method in the corpus's account.
[S105] reports: "According to a 2019 Nielsen Norman Group study, 99% of UX researchers who
responded said they run surveys 'at least sometimes'." It immediately adds: "Unfortunately,
this frequently used method is often applied incorrectly, resulting in unreliable and useless
data."

An agent advising on research should treat "let's run a survey" as a claim requiring
justification, not a default.

## When a survey is the right method

From the decision rule in [user-research-methods.md](user-research-methods.md): a survey fits
research questions that are **quantitative AND attitudinal**.

[S105]: "surveys are, in fact, the only method that can be categorized as both quantitative
and attitudinal... This is great news for researchers, as it means it should be crystal-clear
when an opportunity lends itself to surveys."

**Conclusion as stated** [S105]: "Ensure research viability by using surveys to answer only
research questions that are quantitative in nature and deal with attitudinal responses."

## Documented criticism of the method

[S105] collects two critiques from named practitioners:

> Erika Hall, in *Just Enough Research*: "Surveys are the most dangerous research tool —
> misunderstood and misused. They frequently blend qualitative and quantitative questions; at
> their worst, surveys combine the potential pitfalls of both."

> Tomer Sharon: "I usually recommend product teams (and most others honestly) to stay as far
> away from surveys as possible. I truly believe surveys are the hardest research method to do
> well (yet the easiest to launch in the next 10 minutes)."

*(Reference given by [S105]: Hall, E. and Stark, K. (2019) Just Enough Research. New York, NY:
A Book Apart.)*

## Genuine benefits

[S105] does not reject surveys. Stated benefits:

- **Cheap** — "relatively cost-effective for collecting quantitative data that can be used to
  make user-focused and research-backed design decisions."
- **Insights from real users in context** — intercept surveys (a popup presented at specific
  places on a site) "allow researchers to glean insights from users during their visits."
- **Combine well with other methods** — "surveys pair well with qualitative research methods,
  allowing researchers to supplement their qualitative insights with quantitative heft — often
  a missing component in convincing skeptical stakeholders."

## Three myths that cause survey misuse

This section is the most decision-relevant content in [S105].

### Myth 1: Surveys are easy to run
> "People often focus on how easily you can get a survey out the door, rather than on how much
> skill and energy you should put into doing one correctly." [S105]

The mechanism: cheap, user-friendly tools offer "the incredibly seductive possibility of
tossing a handful of poorly conceived questions into a survey and blasting it off to your
customer list before you have time to even question what you're doing."

The reality claimed: "survey methodology is, in reality, incredibly complex, combining
elements of both quantitative and qualitative research into a single study. **The smallest
tweaks to a given question may yield vastly different results, or even dramatically decrease
a survey's reliability.**"

The rule derived: only start a survey project "when they have enough runway to do so with
appropriate rigor, which includes sufficient time for the building, running, and analysis."

### Myth 2: Large samples are the only road to reliability
[S105] gives a consultant's account of a recurring request: run 10–12 interviews and 5–7
usability tests, *plus* "a survey with 100 people" because "my CEO doesn't trust small numbers"
and "wants statistical significance to feel confident."

Two stated problems with this:

1. **The research questions often don't suit surveys.** If they are qualitative or behavioral,
   answering them by survey "would require a poorly written survey that will be prohibitively
   costly to analyze in order to get valid and useful results. And even then, because the
   results will be based upon qualitative, open-ended questions, the statistical significance
   the CEO is seeking will continue to elude them." [S105] states the constraint plainly:
   **"Statistical significance can be calculated only using answers that can be assigned a
   numeric value."**
2. **The mixed-methods framing may be a fiction.** "Given that the CEO has already confessed a
   strong preference for quantitative data and high sample sizes, it is (based on my
   experience) unlikely that they will truly consider the qual and quant data in concert.
   Instead, they will toss the valid, valuable data from interviews and usability testing
   aside, and base their decision solely on the flawed survey data."

**Recommended alternative** [S105]: find "more sound ways of scratching the quant-loving CEO's
itch beyond surveys. Is there analytics data you can reference, for example?" and use
triangulation "to avoid your stakeholder's temptation to cherry-pick."

> Note this is framed as the author's consulting experience, not measured. The *reasoning*
> about statistical significance is a methodological fact; the prediction about CEO behaviour
> is a professional judgment.

### Myth 3: Surveys avoid the risk of annoying or offending customers
[S105] describes organizations with a rule forbidding emailing, calling, interviewing or
usability-testing customers while permitting survey invitations, and rejects the logic: "It is
puzzling to think that an emailed invitation to a survey is somehow more acceptable than an
emailed invitation for an interview. And the suggestion that researchers will unintentionally
upset a participant while running a user-research session shows a lack of confidence in the
researchers' skill and competence."

## Survey types by phase of the design cycle

[S044] establishes a premise: surveys are "most commonly associated with the Listen phase of a
project," but "this categorization is not a strict delineation. With proper strategy and
planning, surveys can be used at any phase."

### Discover phase
*Goal [S044]: "gather ample background information about the problem space to confirm they
have correctly identified the problem to solve."*

| Survey type | Purpose | Sample questions [S044] |
|---|---|---|
| **Discovery survey** | "Casting a wide net" to uncover insights about current or potential users. Note: "discovery surveys are frequently run qualitatively" and can surface insights to explore in subsequent interviews | "If you had a magic wand, what would you change about [product/service]?" · "On a scale of 1–7, how well does [product/service] currently meet your needs?" · "What is one problem you wish [product/service] could solve that it doesn't do already?" |
| **Stakeholder survey** | An asynchronous alternative when busy senior stakeholders cannot accommodate interviews | "What is the problem that this effort is designed to solve?" · "What outcome(s) would lead you to describe this effort as a success/failure?" · **"What is definitely not in scope for this project?"** · "Who else should I talk to?" |
| **Diary-study survey** | Collecting longitudinal diary entries — e.g. the same survey daily for two weeks | "Please rate your current mood right now." · "How many times did you [perform a specific action] today?" |

### Explore phase
*Goal [S044]: "gain a deeper understanding of the problem space and to reach alignment on
project scope and user needs."*

| Survey type | Purpose | Sample questions [S044] |
|---|---|---|
| **Competitor-customer survey** | Same as a discovery survey, but targeted at **competitors' customers** — "help you learn about the strengths and weaknesses of your competitors' products" | "On a scale of 1-7, how well does [product/service] currently meet your needs?" · "What is your favorite feature?" · "What is one problem you wish it could solve that it doesn't already?" |
| **Statistical-persona survey** | "The most robust and labor-intensive personas" — initial qualitative research informs a survey sent to a large sample, then "statistical analysis is used to generate persona segments" | "Approximately how many times did you use [product/service] in the past 7 days?" · "What is the primary reason you initially started using it?" · "What is your annual household income?" |

### Test phase
Surveys administered **post-task** or **post-test** within usability testing:

- **Single Ease Question (SEQ)** — the most commonly used post-task survey; "typically asks
  users to rate the task on a 7-point scale from very difficult to very easy."
- **System Usability Scale (SUS)** — the most commonly used post-test questionnaire; "a
  10-question survey that has been used since the 1980s to assess the overall usability of a
  system." [S044] names a specific advantage: "it has established reliable benchmarks for
  acceptable scores across industries and contexts due to its popularity and longevity."

### Listen phase
*Goal [S044]: "user sentiment and experience with a product or service are routinely monitored
to understand current problems and detect new problems early."*

| Instrument | Definition [S044] | Caveats stated |
|---|---|---|
| **Net Promoter Score (NPS)** | "Respondents are asked to rate their likelihood of recommending a product or service to someone else. These responses are then aggregated to produce a single score which ranges from -100% to 100%." | **"While the NPS does not directly address or assess the usability of a system, it has been shown to correlate with usability decently well... However, it should never be the only metric used to assess the usability of a system."** |
| **Customer Satisfaction Score (CSAT)** | A 1-question survey, "typically administered after the completion of a journey or transaction." "The CSAT score represents the percentage of respondents who rated their satisfaction as a 4 or a 5 (out of 5)." | — |
| **Customer Effort Score (CES)** | Similar to CSAT but "targets the ease of a particular action." "The CES is the percentage of respondents who select the highest 3 options on a 1–7 ease scale." | — |
| **Custom listening surveys** | "Frequently deployed through on-site intercept popups, usually at key moments, such as the end of specific user journeys or transactions." Used "to track metrics over long periods in order to catch problems early and assess the impact of design changes." | Sample questions: "How do you feel about the following statement: '[feature/change] has made my job easier'?" · "How has [feature/change] affected the way you use our product?" · "Is there anything you would change about how [feature/change] works?" |

## Limitations of this document

- The corpus contains **no guidance on writing survey questions** — the single largest source
  of survey error according to [S105] itself ("the smallest tweaks to a given question may
  yield vastly different results"). [S044] and [S105] both reference an NN/g course on the
  topic that is not in the corpus. **This is a gap.**
- No coverage of sampling, response rates, non-response bias, or survey length effects.
- NPS is described but not critically evaluated; the substantial published criticism of NPS as
  a metric is absent from the corpus. See
  [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md).
- The 99% figure comes from a 2019 NN/g study not included in the corpus; it is a
  self-reported frequency among NN/g's respondent pool, not a population estimate.

## Related concepts

- [user-research-methods.md](user-research-methods.md) — the decision rule for choosing surveys
- [user-interviews.md](user-interviews.md)
- [usability-testing.md](usability-testing.md) — where SEQ and SUS are used
- [../09-metrics/product-metrics.md](../09-metrics/product-metrics.md)
- [../03-market-intelligence/competitive-analysis.md](../03-market-intelligence/competitive-analysis.md) — competitor-customer surveys

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S105 | Nielsen Norman Group, Maddie Brown — *Should You Run a Survey?*, 23 Feb 2024 | UX research organization | Misuse warnings, three myths, benefits, method-fit rule, cited critiques |
| S044 | Nielsen Norman Group, Maddie Brown — *How to Run Surveys at Every Stage of the Design Cycle*, 24 Nov 2023 | UX research organization | Survey types by phase, sample questions, SEQ/SUS/NPS/CSAT/CES definitions |
