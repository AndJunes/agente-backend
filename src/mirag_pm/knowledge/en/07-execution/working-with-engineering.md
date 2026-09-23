---
title: Working with Engineering
domain: execution
type: practice
topics:
  - working with engineers
  - engineering collaboration
  - product manager vs engineering manager
  - technical fluency
  - requirements clarity
  - technical feasibility
source_count: 3
sources: [S049, S046, S008]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Working with Engineering

## Product manager versus engineering manager

[S049] gives the clearest role split in the corpus:

| Product manager | Engineering manager |
|---|---|
| "Answers and expounds **the 'what' and the 'why'** of what needs to be built" | "Defines **the 'how'** of implementing planned work" |
| "Comprehends the product objective from leadership and **plans the product vision and strategy**" | "Plans the **technical strategy** for work and the **long-term technical design**" |
| "Acts as a **connection between the business and technical team**" | "**Determines and manages the resources** needed to build the product" |
| "Creates and owns **the product roadmap**" | "Creates and owns **the technical/technology roadmap**" |

[S049] also notes a scope difference: "a product manager most often works on **one product at a
time**. However, engineering managers can manage the engineering resources for **one or more**
products."

> The existence of a separate **technical roadmap** is worth registering. Engineering has its own
> planning artefact with its own contents (architecture, platform, tooling, debt). A product
> roadmap that ignores it will collide with it. [S119]'s instruction to make room for "scalability,
> cybersecurity, and technical debt" on the product roadmap is the product-side half of the same
> point — see [../05-planning/roadmaps.md](../05-planning/roadmaps.md).

## The mutual expectations

This is the most useful content on the topic, because it is stated **in both directions**.

### What engineers expect from a product manager
[S049]:

| Expectation | What it means |
|---|---|
| **Involve them more** | "**Engineers don't want to feel like coding machines.** Most engineers nowadays want to be involved more and help in **strategy workshops, customer interviews, identifying all cases of the features, and even prioritizing features and technical debt.** Engineers tend to be **one of the most creative assets you have on your team**" |
| **Don't over-engineer the process** | "Engineers want to get to coding and building as soon as possible. **Don't overcomplicate the process and add too many meetings and checklists.** Engineers only want **a clear user story and an organized sprint backlog** to start the implementation right away" |
| **Have clear requirements** | "**Whether you work with user stories or PRDs, engineers don't care.** The only thing engineers care about is **the big picture of the feature and the small details.**" Practically: "explain the big picture... with the aid of tools, like the **user flow** and maybe some **class diagrams**. Also... **identify all small cases with their flows by working with a designer and tester. Find them all before the engineers start working**" |
| **Be available** | "During the sprint, many unexpected questions and concerns will arise. The job of the product manager is to **empower the engineers and be with them during the execution journey**... answering their questions **in a detailed manner, and going above and beyond the expected answer to ensure that the big picture is well-understood**" |

> **"Engineers don't care" whether it's a user story or a PRD** is a useful corrective to the
> format debate in [../06-requirements/prd.md](../06-requirements/prd.md). The artefact is
> instrumental; **clarity about the big picture and the edge cases is the actual requirement.**

### What a product manager expects from engineers
[S049] frames this from the PM's side first: "the product manager has **two goals: to make the
product successful and to make the product team successful.**"

| Expectation | What it means |
|---|---|
| **Keep them informed** | "The product manager wants to know **every single concern or blocker**... The product manager will help unblock the impediment and bottlenecks... **the key to enjoying this privilege is keeping the product manager informed in a continuous manner**" |
| **Challenge their thinking** | "**An effective product manager would want their engineers to challenge their problem statement, thought process, and proposed solution.** In this manner, the product manager will improve their future work significantly and **engineers will contribute more to the strategic success of the product**" |

> The second is the more important and the less common. A PM who is never challenged by engineering
> is not getting the benefit of the team's judgment — which is precisely what [S078] means by
> building "a shared brain."

## Technical fluency: how much is enough

[S046]: "**A PM doesn't need to be an expert coder but must grasp the fundamentals of the project's
technology.** This foundational knowledge enables meaningful dialogues about what can be
realistically achieved within technological constraints, thereby streamlining decision-making."

**Why it matters early** [S046]: "**Early understanding of engineering constraints is crucial to
avoid investing in a design that may not be feasible.**"

This matches the bar set across the corpus:
- [S140]: "There's no point defining what to build if you don't know how it will get built. This
  doesn't mean a Product Manager needs to sit down and code. However, **understanding the
  technology stack and level of effort involved is crucial to making the right decisions.**"
- [S109]: PMs "don't need to be able to code, but they do need **a good handle on the technical
  side of the product development process.** ... **Learn how to speak the developers' language.**"

[S046] names the technical areas a PM should understand: **SDLC (software development life cycle)**;
**Scrum and sprints** — "how most tech teams work"; **estimating development time**; **Git/GitHub**
and "code collaboration"; **CI/CD**.

> ⚠ **[S046] names these topics; the corpus does not explain any of them.** SDLC, Git, CI/CD and
> estimation are all absent as subjects. See [../05-planning/estimation.md](../05-planning/estimation.md)
> and [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Different problem-solving lenses

[S046] describes the structural difference in how the two roles reason, and why it is productive
rather than merely inconvenient:

> "**Engineers tend to view problems through a lens of system capabilities and scalability**,
> focusing on the technical feasibility and optimization of solutions. **On the other hand, Product
> Managers prioritize understanding users' needs**, aiming to ensure that solutions are closely
> aligned with customer requirements and market opportunities.
>
> **This divergence in approaches can sometimes lead to conflicts or differing viewpoints...
> However, it's crucial to acknowledge and value these distinct perspectives.**"

> This is the same *desirable / feasible / viable* tension that
> [../12-design-and-ux/product-triad.md](../12-design-and-ux/product-triad.md) formalises. The
> conflict is the mechanism, not a failure of it: a team where engineering never raises feasibility
> objections has lost one of its three perspectives.

## Communication practices

### Craft clear messages
[S046]: "**Utilizing diagrams, flowcharts, or user stories can translate complex requirements into
tangible, understandable goals.**"

Its paired examples make the point concretely:

| | Good practice | Bad practice |
|---|---|---|
| **UI redesign** | "The PM used **mock-ups and interactive prototypes** to show the engineering team exactly what was needed. Regular brainstorming sessions were held for feedback." → "implemented smoothly, with the final product closely matching the initial vision" | "A vague, **text-only description** without visual aids or follow-up discussions." → "**missed key elements, requiring several costly and time-consuming revisions**" |
| **New feature** | "The PM presented **detailed user stories and flowcharts in a kick-off meeting**, clearly outlining the expected user flow and technical requirements." → "developed efficiently" | "Requested a new analytics dashboard **via email, without detailing how it should work or its purpose, expecting the engineering team to fill in the blanks.**" → "lacked essential features and required significant rework" |

### Regular check-ins
[S046]: "Frequent meetings provide a platform for **airing challenges, brainstorming, and
dynamically adjusting strategies.**"

Its counter-example is instructive: a PM who "decided **against regular check-ins** during a
long-term roadmap planning phase, preferring to rely on email updates" produced "**misaligned
priorities and a roadmap that did not fully account for technical feasibility or market trends.**"

> Note the failure is attributed to the *roadmap*, not to the sprint. **Feasibility input is needed
> at planning time, not only at build time** — which is [S119]'s point about "checking in frequently
> with the implementation team to ensure the prioritized goals and themes of the roadmap are
> feasible and worth the effort."

### Other practices named
[S046] lists, with limited detail: **leveraging collaboration tools**, **encouraging knowledge
sharing** and documentation, **celebrating achievements**, **supporting personal growth**, and
**effective [conflict] resolution**.

[S008] (Productboard) covers product collaboration more broadly — see
[product-collaboration.md](product-collaboration.md).

## Limitations

- **[S046] is a training provider's session summary** (HelloPM) and is heavily interleaved with
  course promotion; several of its sections are headings only.
- **[S049] is a vendor blog** (LogRocket) promoting its own session-replay product.
- **The "engineers want X" claims are assertions**, not survey findings. No source measures what
  engineers actually want from PMs. [S064] is the corpus's only survey of role expectations and it
  covers PM and UX, not PM and engineering.
- **Technical debt is repeatedly named and never treated.** [S049] mentions engineers wanting to
  help prioritise it; [S087] lists underestimating it as a product risk; [S119] says to make room
  for it on the roadmap. **No source defines it or explains how to manage it.** This is a priority
  gap.
- **No treatment of architecture constraints, API design, build-vs-buy, or platform decisions** as
  product concerns, beyond [S111]'s note that platform PMs need "build v buy decision making."
- **No treatment of what to do when engineering says something is infeasible** — how to interrogate
  the claim, or how to negotiate scope against effort.

## Related concepts

- [agile-manifesto.md](agile-manifesto.md)
- [product-collaboration.md](product-collaboration.md)
- [product-development-process.md](product-development-process.md)
- [../01-foundations/product-manager-skills.md](../01-foundations/product-manager-skills.md)
- [../06-requirements/user-stories.md](../06-requirements/user-stories.md)
- [../06-requirements/prd.md](../06-requirements/prd.md)
- [../05-planning/estimation.md](../05-planning/estimation.md)
- [../12-design-and-ux/product-triad.md](../12-design-and-ux/product-triad.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S049 | LogRocket (Shehab Beram) — *How top product managers work with engineers* | Vendor blog | PM vs engineering manager table, mutual expectations in both directions |
| S046 | HelloPM (Akshit Goel) — *How to Work With Engineers: A Guide for Product Managers*, Apr 2024 | Training-provider session summary | Technical fluency bar, problem-solving lenses, communication practices with paired examples, technical topics list |
| S008 | Productboard — *6 Keys to Effective Product Collaboration* | Vendor blog | Collaboration framing (see product-collaboration.md) |
