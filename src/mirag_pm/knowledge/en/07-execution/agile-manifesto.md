---
title: The Agile Manifesto
domain: execution
type: primary-text
topics:
  - agile manifesto
  - agile values
  - twelve principles
  - Snowbird
  - faux agile
  - cargo cult agile
source_count: 3
sources: [S022, S121, E002]
evidence_type: primary-text-quoted
confidence: high
corpus_origin: true
external_research: true
verified: true
phase: 2
provenance:
  primary: [E002]
  interpretation: [S022]
  practice: []
  empirical: []
last_reviewed: 2026-09-16
---

# The Agile Manifesto

> **Source note.** [S022] is the only document in the corpus that **quotes a primary text
> verbatim** — the four values of the Manifesto and its signatory list. That makes this the most
> directly citable content in this knowledge base. The surrounding commentary is Atlassian's.

## The four values

> **Manifesto for Agile Software Development**
>
> We are uncovering better ways of developing software by doing it and helping others do it.
> Through this work we have come to value:
>
> **Individuals and interactions** over processes and tools
> **Working software** over comprehensive documentation
> **Customer collaboration** over contract negotiation
> **Responding to change** over following a plan
>
> **That is, while there is value in the items on the right, we value the items on the left more.**

### The final sentence is the most misused part of the document

"While there is value in the items on the right, we value the items on the left more" states a
**preference under trade-off**, not an elimination. The Manifesto does not say documentation is
worthless, or that plans should not exist — only which side wins when the two conflict.

> This matters directly to several debates elsewhere in this knowledge base. [S086] cites value 2
> (*working software over comprehensive documentation*) as the core tension making PRDs
> problematic — see [../06-requirements/prd.md](../06-requirements/prd.md). Read correctly, the
> value does not prohibit a PRD; it says a PRD that impedes working software has its priorities
> inverted. [S138] reaches the same conclusion by recommending **"informative-but-brief"**
> requirements rather than none.

## The signatories

[S022] reproduces all 17:

> Kent Beck · Mike Beedle · Arie van Bennekum · Alistair Cockburn · Ward Cunningham ·
> Martin Fowler · James Grenning · Jim Highsmith · Andrew Hunt · Ron Jeffries · Jon Kern ·
> Brian Marick · Robert C. Martin · Steve Mellor · **Ken Schwaber** · **Jeff Sutherland** ·
> Dave Thomas

> Schwaber and Sutherland are the originators of Scrum; Beck of Extreme Programming; Jeffries is
> the source of the *card, conversation, confirmation* framing of user stories quoted in
> [../06-requirements/user-stories.md](../06-requirements/user-stories.md). Cunningham is
> credited with the concept of technical debt — **which the corpus does not cover.**

## Origin

[S022]: "In **early 2001**, against the backdrop of the Wasatch Mountains, in **Snowbird, Utah, 17
people** met to discuss the future of software development."

**The problem they identified:** "companies were so focused on **excessively planning and
documenting their software development cycles that they lost sight of what really mattered —
pleasing their customers.**"

**Why it was surprising that they agreed** — Ian Buchanan, Principal Solutions Engineer for DevOps
at Atlassian, quoted in [S022]:

> "The Manifesto itself was born out of a need to **find a common ground among scrum, Extreme
> Programming, Crystal Clear, and other frameworks.** ... 'They were starting to see that there was
> something common that they were doing. But **at the time, they were very much competitors, at
> least competitors in thought.** When you put that into context, **the fact that they could agree
> on some set of anything is kind of profound.**'"

[S022] notes the document's brevity — "**just 68 words**" — and that "the Agile Manifesto site has
changed minimally, if at all" since.

## The twelve principles

[S022] states that "**The Twelve Principles of Agile Software**, also a product of the Snowbird
summit, expand on the handful of sentences that make up the values."

> **Phase-2 addition.** [S022] referenced the principles without reproducing them — the single
> largest omission in the original corpus. They are reproduced below **verbatim from the primary
> source**, [E002] `agilemanifesto.org/principles.html`, retrieved September 2026.

> **Principles behind the Agile Manifesto**
>
> We follow these principles:
>
> 1. **Our highest priority is to satisfy the customer through early and continuous delivery of
>    valuable software.**
> 2. **Welcome changing requirements, even late in development. Agile processes harness change for
>    the customer's competitive advantage.**
> 3. **Deliver working software frequently, from a couple of weeks to a couple of months, with a
>    preference to the shorter timescale.**
> 4. **Business people and developers must work together daily throughout the project.**
> 5. **Build projects around motivated individuals. Give them the environment and support they need,
>    and trust them to get the job done.**
> 6. **The most efficient and effective method of conveying information to and within a development
>    team is face-to-face conversation.**
> 7. **Working software is the primary measure of progress.**
> 8. **Agile processes promote sustainable development. The sponsors, developers, and users should be
>    able to maintain a constant pace indefinitely.**
> 9. **Continuous attention to technical excellence and good design enhances agility.**
> 10. **Simplicity — the art of maximizing the amount of work not done — is essential.**
> 11. **The best architectures, requirements, and designs emerge from self-organizing teams.**
> 12. **At regular intervals, the team reflects on how to become more effective, then tunes and
>     adjusts its behavior accordingly.**

### What the principles add that the four values do not

The values state preferences; the principles state **operating commitments**, several of which
resolve or sharpen debates elsewhere in this knowledge base.

| Principle | What it settles |
|---|---|
| **1 — early and continuous delivery of valuable software** | The stated purpose is *customer satisfaction*, not speed. This is the Manifesto's own outcome-over-output claim, predating the roadmap literature in [../05-planning/outcome-based-roadmaps.md](../05-planning/outcome-based-roadmaps.md) by two decades |
| **2 — welcome changing requirements, even late** | Directly contradicts the "requirements freeze" model described in [../06-requirements/scope-definition.md](../06-requirements/scope-definition.md). Note the justification is **competitive advantage**, not developer convenience |
| **3 — deliver frequently, weeks rather than months** | The origin of fixed short iterations. Scrum's "one month or less" Sprint ([scrum.md](scrum.md)) is one implementation of this principle, not its source |
| **4 — business people and developers work together *daily*** | The strongest statement in any primary text of what [working-with-engineering.md](working-with-engineering.md) describes. **Daily** is a much higher bar than the "regular stakeholder syncs" most corpus sources recommend |
| **5 — build projects around motivated individuals... trust them** | The empowerment claim [S040] makes, in the primary text |
| **6 — face-to-face conversation is the most efficient method** | The basis for [S127]'s *card, conversation, confirmation* framing of user stories. **Also the principle most obviously stressed by distributed work and by AI implementers** — see the limitation below |
| **7 — working software is the primary measure of progress** | Rules out story points, velocity and burndown as *measures of progress*; they may be planning aids, but the principle names running software as the measure. See [../05-planning/estimation.md](../05-planning/estimation.md) |
| **8 — sustainable pace, indefinitely** | The direct textual basis for [S022]'s "burnout-rate pacing" diagnostic below |
| **9 — continuous attention to technical excellence** | The only principle touching **technical debt** — the concept Ward Cunningham (a signatory) coined. Still not treated in this knowledge base |
| **10 — maximizing the amount of work *not* done** | The Manifesto's own prioritization principle: the goal is descoping, not throughput. Relevant to everything in [../05-planning/prioritization.md](../05-planning/prioritization.md) |
| **11 — architectures and requirements emerge from self-organizing teams** | Says **requirements emerge from the team**, not from a PM handing them down. The strongest primary-text challenge to the PRD-as-specification model in [../06-requirements/prd.md](../06-requirements/prd.md) |
| **12 — reflect at regular intervals and adjust** | The principle Scrum implements as the Sprint Retrospective |

### Provenance caution

These twelve principles are **what the original authors wrote in 2001.** They are *not*:

- **a description of current practice** — most organizations calling themselves agile do not
  practice principle 4 (daily business/developer collaboration) or principle 8 (constant pace
  indefinitely), which is precisely [S022]'s "faux agile" complaint below;
- **empirically validated** — the Manifesto presents no evidence, and none is claimed here.
  **[EMPIRICAL: not established in this knowledge base.]**

## The debate about what agile became

This is [S022]'s most valuable content, and it is unusually self-critical for vendor material.

### Spread beyond software
[S022]: "there's **SAFe**. There's **LeSS**. There are applications of agile that **don't have
anything to do with software development**, even though the Manifesto starts off by saying: 'We are
uncovering better ways of **developing software**.'"

It reports Dave West, CEO of Scrum.org, citing "a research team that's using agile to develop a
cure for genetic blindness using viruses," and concludes: "**embracing agile outside the realm of
software has caught on, but it's not necessarily what the Manifesto's originators intended.**"

Buchanan, quoted: "**It's not that it can't be interpreted, but it takes a deeper understanding to
make sure the ideas are translated with fidelity.** That deeper understanding isn't always available
— **even within software development.**"

### "Faux agile," "dark agile," "cargo cult agile"

[S022] names the phenomenon and its alleged cause:

> "Many argue that '**faux agile**,' as it's also called, and its evil twin '**dark agile**,' are
> exacerbated by **the monetization of agile education and consulting.** Some even go as far as
> calling the organizations behind this monetization '**The Agile Industrial Complex.**'"

Buchanan's definition of cargo cult agile:

> "**There's cargo cult agile where you're doing and saying the right things, but you don't
> understand the fundamental principles. You're not getting the results.**"

### The named symptoms

[S022] lists what these subversions look like in practice — this is a **diagnostic list**:

> "**micromanagement, burnout-rate pacing, lack of delivery, and adherence to process over
> principles** register as the most egregious — **even if their practitioners come with a
> certificate.**"

And the consequence: "these dark agile experiences **cause some people to swear off agile
altogether.**"

### Atlassian's own admission
[S022] is candid about its author's position:

> "**Some, and many do, consider Atlassian a culprit of this since our tools enable agile
> frameworks like scrum and kanban. But our belief is that agile is a cultural value**, and teams
> should be empowered to work how they best see fit. **Agile frameworks work alongside cultural
> values, but if you don't have the cultural default, then what you do could turn out flawed from
> the get-go.**"

> **The operative claim — "agile is a cultural value, not a process" — is the corpus's clearest
> statement of why adopting ceremonies without changing decision-making produces nothing.** It is
> the same structure as [S040]'s empowerment diagnostic: the process fails when the underlying
> authority relationship is unchanged. See
> [../05-planning/outcome-based-roadmaps.md](../05-planning/outcome-based-roadmaps.md).

## What the corpus does NOT contain

This is the largest single gap in the knowledge base and must be stated plainly.

| Missing from the corpus | Status after Phase 2 |
|---|---|
| **The twelve principles** | ✅ **Closed.** Reproduced above from [E002] |
| **The Scrum Guide or any primary Scrum source** | ✅ **Closed.** See [scrum.md](scrum.md), written from [E001], the 2020 Scrum Guide |
| **Kanban** | ✅ **Closed.** See [kanban.md](kanban.md) |
| **Sprint planning, standups, retrospectives** | ✅ **Closed** by [scrum.md](scrum.md). The corpus itself still contains only [S118]'s launch retrospective |
| **SAFe, LeSS** | Named once each, in this document, as examples of proliferation |
| **Extreme Programming, Crystal Clear** | Named once, as inputs to the Manifesto |
| **Technical debt** | Named as a roadmap and risk concern ([S119], [S087]); never defined or treated |

> **Status.** As of Phase 2, the agile-mechanics gap is closed **from primary sources**:
> [scrum.md](scrum.md) and [kanban.md](kanban.md) are written from the Scrum Guide and from David J.
> Anderson's Kanban Method respectively, and the twelve principles are reproduced above. **What the
> original corpus contained has not changed** — these are external additions, marked as such. SAFe,
> LeSS, Extreme Programming and technical debt remain uncovered; see
> [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Limitations

- **[S022] is written by Atlassian's Head of Product Marketing**, and the company sells agile
  tooling. It handles that conflict openly (see above), but the framing — agile as culture,
  tools as neutral enablers — is convenient for the publisher.
- **The four values were quoted from a secondary source** ([S022]); they have since been checked
  against the canonical text at agilemanifesto.org [E002] and match. The twelve principles come
  directly from [E002].
- **Principle 6 (face-to-face conversation) was written in 2001** for co-located human teams. The
  Manifesto's authors could not have been addressing distributed teams at today's scale, and
  certainly not non-human implementers. **Anyone applying principle 6 to an AI-agent team is
  extrapolating beyond the source.** See
  [../13-ai-agent-collaboration/](../13-ai-agent-collaboration/).
- **No dates or version history** for SAFe, LeSS or other frameworks.
- **[S121] (Atlassian, *Tips for agile product management*, 14 May 2015) is an announcement post**
  with no substantive content; it is excluded from the knowledge base. See
  [../99-reference/excluded-content.md](../99-reference/excluded-content.md).

## Related concepts

- [scrum.md](scrum.md) — the framework two signatories originated
- [kanban.md](kanban.md) — the alternative flow-based method
- [working-with-engineering.md](working-with-engineering.md)
- [product-development-process.md](product-development-process.md)
- [../06-requirements/user-stories.md](../06-requirements/user-stories.md) — card, conversation, confirmation
- [../06-requirements/prd.md](../06-requirements/prd.md) — the documentation value in dispute
- [../05-planning/roadmap-formats.md](../05-planning/roadmap-formats.md) — agile roadmaps
- [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S022 | Atlassian (Claire Drumond) — *Agile Manifesto* | Vendor guide **quoting the primary text** | The four values verbatim, signatory list, Snowbird origin, the agile debate, faux/dark/cargo-cult agile, named symptoms |
| S121 | Atlassian (John Wetenhall) — *Tips for agile product management*, 14 May 2015 | Blog announcement | **Excluded — no substantive content** |
| **E002** | **agilemanifesto.org — *Principles behind the Agile Manifesto*** (Beck, Beedle, van Bennekum, Cockburn, Cunningham, Fowler, Grenning, Highsmith, Hunt, Jeffries, Kern, Marick, Martin, Mellor, Schwaber, Sutherland, Thomas, 2001) | **Primary text by the original authors** | The twelve principles verbatim; verification of the four values. Retrieved September 2026 |
