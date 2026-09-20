# RESEARCH BACKLOG

What a competent PM agent needs that **this corpus does not adequately supply.**

Each gap below was identified during the build, not guessed at. Every entry states what is missing,
what the corpus *does* have, what to research, and where to look.

> **Phase 2 status — first pass complete, 16 September 2026.**
>
> | Gap | Status |
> |---|---|
> | **1.1 Scrum, Kanban, agile mechanics** | ✅ **CLOSED** from primary texts — [E001], [E002], [E003], [E004] |
> | **1.2 MVP** | ⬜ **Open** — research gathered, not yet written. See the note below |
> | **1.3 Product metrics and measurement design** | ⬜ **Open** — not researched |
> | **1.4 Estimation** | 🟨 **Partially closed** — a *different* method supplied (probabilistic forecasting, [E003]) plus one calibration measurement ([E006]). Story points, velocity and planning poker **still absent** |
> | **1.5 Working with AI agents as team members** | 🟨 **Partially closed** — a new domain, [13-ai-agent-collaboration/](13-ai-agent-collaboration/), built from [E006]–[E014]. **The central question — how to organise a multi-agent software team — remains unanswered; no source was found.** See [open-questions-ai-and-pm.md](13-ai-agent-collaboration/open-questions-ai-and-pm.md) |
>
> **The backlog was treated as a map, not a list of expected answers.** Two gaps closed differently
> from how they were framed:
>
> - **1.4** was written expecting story-point mechanics. The primary texts revealed that **Scrum
>   prescribes no estimation technique at all** and that Kanban offers a **different method** rather
>   than a better version of the same one. The original questions are still listed below because most
>   remain unanswered.
> - **1.5** was written expecting to synthesise. It produced instead **one empirically supported
>   finding** ([E008] on user-centric focus as a moderator), a set of **labelled inferences**, and a
>   **register of open questions longer than the answers** — which is the honest outcome, not a
>   failure of the research.
>
> **Nothing here was closed from model memory.** Where a question could not be answered from a
> retrievable source, it is recorded as open.

---

## Priority 1 — the agent cannot function well without these

### 1.1 Scrum, Kanban and agile execution mechanics — ✅ CLOSED

> **Closed 16 September 2026** from four primary sources: [E001] the 2020 Scrum Guide, [E002] the
> twelve Agile principles, [E003] *Essential Kanban Condensed*, [E004] the Kanban Guide.
> Produced [07-execution/scrum.md](07-execution/scrum.md) and
> [07-execution/kanban.md](07-execution/kanban.md), and rewrote the principles section of
> [07-execution/agile-manifesto.md](07-execution/agile-manifesto.md).
>
> **Every listed question was answered**, including the Definition-of-Done question — which produced
> a **correction to two corpus sources** ([S126], [S128]), recorded in
> [99-reference/disputed-information.md §6.1](99-reference/disputed-information.md).
>
> **Still open from this area:** SAFe, LeSS, Nexus and other scaling frameworks · Extreme Programming
> · technical debt (§2.3) · burndown charts and velocity mechanics · Kanban Maturity Model and
> portfolio Kanban · **whether either framework's mechanics hold when the implementer is an agent**
> (see [13-ai-agent-collaboration/open-questions-ai-and-pm.md](13-ai-agent-collaboration/open-questions-ai-and-pm.md) §B6).

**Why it matters.** Most software product teams work in Scrum or Kanban. An agent advising a PM will
be asked about sprints, backlogs, ceremonies and roles constantly.

**Current coverage.** The Agile Manifesto's four values are quoted verbatim [S022] — and that is
effectively all. **The twelve principles are referenced but not reproduced.** Sprint, product owner,
scrum master, sprint planning, sprint review, retrospective, Kanban, WIP limits and flow are named
across a dozen sources and **defined by none.**

**Questions to research.**
- What are the Scrum accountabilities, events and artefacts, as defined by the Scrum Guide?
- What are the twelve Agile principles?
- What is Kanban — WIP limits, pull, flow metrics — as distinct from Scrum?
- How do sprint planning, daily scrum, sprint review and retrospective actually run?
- What is a Definition of Done at team level, as distinct from story acceptance criteria?

**Sources to obtain.** The **Scrum Guide** (scrumguides.org, current version) · **agilemanifesto.org**
(values and principles) · Anderson, *Kanban* · the Kanban Guide.

**Priority rationale:** the largest single hole. Referenced in
[07-execution/agile-manifesto.md](07-execution/agile-manifesto.md),
[01-foundations/product-manager-vs-product-owner.md](01-foundations/product-manager-vs-product-owner.md),
[05-planning/backlog-management.md](05-planning/backlog-management.md).

---

### 1.2 MVP — definition, scoping and failure modes

**Why it matters.** "How is an MVP defined?" is one of the stated target questions for this
knowledge base.

**Current coverage.** **One sentence** inside a framework summary [S110]. The best content is
incidental: [S106]'s framing that "a good MVP is the least costly way to prove out an idea — the
least costly way to achieve success or **recognize failure**." [S072] asserts a shift to "Minimum
Lovable Product" without defining either term.

**Questions to research.**
- What does "viable" mean, and viable *for what*?
- How is an MVP scoped? What distinguishes it from a prototype, a beta, or a bad product?
- What are the documented failure modes (MVP as an excuse for low quality; MVP that tests nothing)?
- What are the alternatives — concierge, Wizard of Oz, smoke test, MLP — and when does each apply?

**Sources to obtain.** Ries, *The Lean Startup* · Blank, *The Four Steps to the Epiphany* ·
Cagan, *Inspired* on product discovery prototypes.

---

### 1.3 Product metrics and measurement design

**Why it matters.** "How do you measure the success of a product?" is a target question, and metrics
are referenced in nearly every document here.

**Current coverage.** Five metric definitions [S141] and five survey instruments [S044]. **No
measurement design at all.**

**Questions to research.**
- How do you choose which metrics to track for a given product and stage?
- Leading vs lagging indicators; input metrics vs output metrics.
- Cohort analysis and retention curves — including what a flattening curve indicates.
- A/B test design: sample sizing, duration, significance, peeking, novelty effects.
- Event taxonomy and instrumentation design.
- Goodhart's law and metric gaming.
- What is a North Star Metric, how is one chosen, and what are its critiques? *(Referenced by four
  corpus sources and defined by none — see
  [09-metrics/north-star-metric.md](09-metrics/north-star-metric.md))*

**Sources to obtain.** Croll & Yoskovitz, *Lean Analytics* · Google's HEART framework paper ·
Amplitude/Mixpanel measurement guides *(secondary — verify against primary)* · Kohavi, Tang & Xu,
*Trustworthy Online Controlled Experiments*.

---

### 1.4 Estimation — 🟨 PARTIALLY CLOSED

> **What Phase 2 supplied**, in [05-planning/estimation.md](05-planning/estimation.md):
> - **[E001]**: Scrum prescribes **no estimation technique whatsoever** — story points, velocity and
>   planning poker are community conventions, not Scrum rules.
> - **[E002]** principle 7: *"Working software is the primary measure of progress"* — which rules out
>   velocity **as a measure of progress**, though not as a planning aid.
> - **[E003]**: **probabilistic forecasting** — Little's Law, the minimum flow dataset (Lead Time,
>   Delivery Rate, WIP, cost), Monte Carlo simulation producing completion-date distributions at
>   stated confidence levels, and a blunt critique of effort-plus-risk estimating. **This gives
>   [S108]'s "forget estimation" instinct an actual method.**
> - **[E006]**: the only measurement of estimation accuracy available — forecast-vs-actual
>   correlations of **0.64 / 0.59** on 246 real tasks, alongside a **systematic, confident directional
>   bias** about a factor affecting every estimate.
>
> **Still open:** story points and relative estimation mechanics · velocity calculation and misuse ·
> t-shirt sizing · forecasting a date **from estimates** · the cone of uncertainty · estimation biases
> · #NoEstimates stated fairly · **how to actually run a Monte Carlo forecast** (how much history is
> enough, what tooling, what distribution assumptions) — [E003] gives the approach, not the procedure.

**Why it matters.** Every prioritization framework in
[05-planning/prioritization-frameworks.md](05-planning/prioritization-frameworks.md) consumes effort
estimates, and the corpus's own sources say those estimates are the weak link.

**Current coverage.** **One sentence** naming t-shirt sizes, Fibonacci and planning poker [S126].
*Story point* and *velocity* do not appear in the corpus at all. The only actual guidance is
"base your estimate on past performance" [S003] and "forget estimation — what has happened in the
past?" [S108].

**Questions to research.**
- What are story points, and how does relative estimation work?
- Velocity: calculation, legitimate use, and documented misuse.
- How do you forecast a date from estimates? Probabilistic forecasting; the cone of uncertainty.
- Estimation biases: anchoring, optimism bias, the planning fallacy.
- The #NoEstimates argument, fairly stated.

**Sources to obtain.** Cohn, *Agile Estimating and Planning* · Vacanti, *Actionable Agile Metrics
for Predictability* · Magennis, *Forecasting and Simulating Software Development Projects*.

---

### 1.5 Working with AI agents as team members — 🟨 PARTIALLY CLOSED

> **Domain created:** [13-ai-agent-collaboration/](13-ai-agent-collaboration/) — four documents.
> Sources [E006]–[E014].
>
> **What was answered, and how well:**
>
> | Original question | Status |
> |---|---|
> | How does a PM specify work for an agent rather than a human team? | 🟨 **Practice documented, efficacy unmeasured.** Spec-Driven Development ([E012], [E013]) and EARS ([E014]) — see [spec-driven-development.md](13-ai-agent-collaboration/spec-driven-development.md). **No controlled comparison of specification approaches exists** |
> | What do acceptance criteria mean when the implementer is non-deterministic? | 🟨 **pass@k vs pass^k** from [E011] gives the arithmetic — 75% per trial is **~42% over three**. The bridge to product acceptance is marked `[SYNTHESIS]` and is unvalidated |
> | How is quality defined and evaluated? | ✅ **Answered** for agents-as-products: capability vs regression evals, three grader types, outcome-over-trajectory grading, saturation, Swiss Cheese layering — [E011] |
> | How does planning change when build cost collapses but review cost does not? | 🟨 **Named, not measured.** [E006]'s **<44% acceptance rate** and **~9% review time**, [E008]'s instability finding and [E009]'s "verification tax" converge — but **no study tested review as the bottleneck** |
> | What are the failure modes of agent-executed product work? | ❌ **No taxonomy found** |
> | How do discovery and validation change when prototypes are near-free? | ❌ **Unaddressed by every source consulted** |
> | Who owns the outcome when an agent produced the artefact? | ❌ **Unaddressed** |
>
> **The one empirically supported result bearing on the PM function** — [E008], n≈5,000:
> *"In the absence of a user-centric focus, AI adoption has a negative impact on team performance."*
> A **moderation** finding: correlational, self-reported, vendor-run.
>
> **What was NOT found, and matters most:** nothing on **how to organise a multi-agent software team**
> — roles, handoffs, orchestration, escalation. **This is the project's own reason for existing and
> the research did not close it.** Full register:
> [open-questions-ai-and-pm.md](13-ai-agent-collaboration/open-questions-ai-and-pm.md).
>
> **Method note.** The instruction was not to fill this hole with general PM knowledge, and it was
> not. Where the evidence ran out, the documents say so and stop. The gap register is longer than the
> answer document, deliberately.
>
> **Next moves, in cost order:** (1) field reports on multi-agent team organisation — Level-4 sources
> are legitimate for *discovery* here, never as authority; (2) instrument review as a flow stage
> using [E003]'s existing apparatus, which is measurable today by any team willing to do it;
> (3) defect and maintainability data on agent-written code.

**Why it matters.** **This knowledge base exists to support a PM agent operating inside a system of
software agents.** It is the project's own stated purpose, and the corpus barely touches it.

**Current coverage.** [S031] alone, on **agents as users** — the two-stream classification
(human/agent/both), agent-side metrics (intent resolution rate, tool-call accuracy, fallback rate,
human-intervention rate), and the observation that click-based analytics under-report agent
activity. Vendor-sourced, 2026, unverified. **Nothing at all on agents as *team members*.**
[S019]'s "automation-first" design stance is the nearest adjacent material.

**Questions to research.**
- How does a PM specify work for an AI agent rather than a human team?
- What does acceptance criteria mean when the implementer is non-deterministic?
- How is quality defined and evaluated — evals, guardrails, human-in-the-loop thresholds?
- How does estimation and planning change when build cost collapses but review cost does not?
- What are the failure modes of agent-executed product work?
- How do discovery and validation change when prototypes are near-free?
- Roles and accountability: who owns the outcome when an agent produced the artefact?

**Sources to obtain.** This is the **least well-served by existing literature** of any gap here.
Likely sources: AI engineering practice documentation · evaluation-framework literature · primary
documentation from agent-framework vendors · emerging practitioner writing. **Expect to have to
synthesise rather than cite**, and to mark results as provisional.

---

## Priority 2 — significant gaps in core PM work

### 2.1 Product-market fit
**Current:** referenced constantly; defined inconsistently across four sources; one operational test
(the 40% rule) with no primary evidence. → [04-strategy/product-market-fit.md](04-strategy/product-market-fit.md)
**Research:** rigorous definitions; retention-curve signals; leading indicators; whether PMF can be
lost; how it differs by market type.
**Sources:** Andreessen's original formulation · Ellis's own writing · Rahul Vohra on the Superhuman
PMF engine · Olsen, *The Lean Product Playbook*.

### 2.2 Pricing and packaging
**Current:** [S092]'s Value-Price-Cost framework introduces price and then never returns to it.
[S034] gives three bullets. **Pricing appears in eight sources' lists of what a PM influences and is
treated in none.**
**Research:** value-based pricing; willingness-to-pay research (Van Westendorp, conjoint); packaging
and tiering; freemium vs trial economics; price changes and grandfathering.
**Sources:** Ramanujam & Tacke, *Monetizing Innovation* · Price Intelligently / ProfitWell research.

### 2.3 Technical debt
**Current:** named as a roadmap item [S119], a product risk [S087], and something engineers want to
help prioritize [S049]. **Never defined.** Ward Cunningham, who coined it, is a Manifesto signatory
listed in [S022] — the corpus contains the name and not the concept.
**Research:** definition and taxonomy; how to make it visible to non-engineers; how to fund it
against feature work; measurement.
**Sources:** Cunningham's original metaphor · Fowler's technical debt quadrant · Kruchten,
Nord & Ozkaya, *Managing Technical Debt*.

### 2.4 Release planning and delivery mechanics
**Current:** two contradictory sentences. → [05-planning/release-planning.md](05-planning/release-planning.md)
**Research:** release cadence choices; fixed-date vs fixed-scope; feature flags, canary and staged
rollouts; rollback planning; release burndown and cut-line management; versioning and deprecation
policy.

### 2.5 Dependency management
**Current:** scattered mentions; no method. → [05-planning/dependencies.md](05-planning/dependencies.md)
**Research:** dependency mapping and visualisation; critical path; negotiating and tracking
cross-team commitments; scaled-agile mechanisms (PI planning, dependency boards); architectural
decoupling as a dependency strategy.

### 2.6 Backlog management beyond refinement
**Current:** refinement is well covered [S127]; ordering, sizing, hygiene and stale-item policy are
not. → [05-planning/backlog-management.md](05-planning/backlog-management.md)
**Research:** ordering methods; Definition of Ready; backlog age and flow metrics; how defects are
prioritized against features.

### 2.7 WSJF and scaled prioritization
**Current:** **WSJF does not appear anywhere in the corpus**, despite being standard in scaled agile.
Cost of delay is described [S066] without connecting to it.
**Research:** WSJF calculation and its cost-of-delay basis; portfolio-level prioritization across
teams; Three Horizons *(named once by [S031], never explained)*.

### 2.8 Market sizing
**Current:** TAM is named by [S081]; **no method anywhere.**
**Research:** TAM/SAM/SOM; top-down vs bottom-up estimation; common errors; how much precision is
warranted at each stage.

---

## Priority 3 — verify or complete what the corpus asserts

These are **verification tasks**, not discovery tasks. Each concerns a specific, checkable claim.

| Claim to verify | Source | Why it matters |
|---|---|---|
| **DSDM's 60% Must cap** with ~20% reserved for Coulds | S031 | The most actionable prioritization correction in the corpus. Verify against DSDM's own documentation |
| **The opportunity-scoring formula** — [S066] gives two incompatible versions | S066 | Verify against Ulwick's own work |
| **The Sean Ellis 40% threshold** | S005 | Load-bearing for PMF assessment; needs primary evidence, not a secondary citation |
| **Dual-track agile attribution** to Desiree Sy's 2007 paper | S110 | — |
| **SCAMPER's origin** — Osborn's *Applied Imagination* (1953) and its eight prompts; Eberle's reorganisation | S101 vs S018 | The two corpus sources give different attributions |
| **6-3-5 publication date** — 1968 or 1969 | S010 | Internal inconsistency |
| **Levitt, *Exploit the Product Life Cycle*, HBR 1965** | S072 | Specific and checkable |
| **P&G / brand management origin** of product management | S132 | Widely repeated, never sourced |
| **NIST SP 800-30 and WEF Cyber Risk Model versions** | S050 | Standards get revised |
| **Pendo 6.4%, DORA 2024, Gartner 40%** | S031 | Load-bearing for that source's entire argument |
| **MSPOT and V2MOM definitions** | S007 | Named with use cases; definitions lost in extraction |
| **Nominal Group Technique** | S010, S100, S125 | Recommended three times, explained zero times |
| **NN/g's 20-method research map** | S017 | The chart did not extract — the corpus's method-selection map is incomplete |
| **NN/g usability-testing corpus** (~40 linked articles) | S099 | The knowledge base can recognise a bad usability test but not run one |
| **Service blueprint** and frontstage/backstage | S103 | The discipline's primary artefact, named and never explained |

---

## Priority 4 — worth having, not blocking

| Topic | Note |
|---|---|
| **Accessibility** | **Does not appear anywhere in the corpus.** A notable omission for any product team |
| **Use cases** | Defined only by contrast with user stories; no worked example; Jacobson not in corpus |
| **INVEST** | Referenced in promotional copy only; never expanded |
| **Story splitting patterns** | [S127] says splitting matters and names one anti-pattern; the actual patterns are in linked articles not in the corpus |
| **Story mapping method** | Purpose explained; no worked map |
| **Focus groups** | Named by three sources; **no critical treatment** of their known weaknesses |
| **A/B testing** | A few sentences; no design guidance |
| **Business models** | [S090] names lean canvas, Porter's Five Forces, 10Ps as strategy foundations; none is explained |
| **Positioning statement templates** | Both positioning sources truncated before their templates |
| **Persona construction** | Referenced constantly; method absent except statistical personas [S044] |
| **Customer journey mapping** | Named by five sources; method absent |
| **Pre-mortem, Six Thinking Hats, Synectics, TRIZ, Hurson's model** | Named; none explained |
| **Product operations** | Referenced; not treated |
| **Portfolio management** | Only [S134]'s portfolio-fit criterion |
| **Change control** | No change-request process anywhere, despite [S020] naming request monitoring |
| **Earned value management** | Seven metrics named in a table [S043]; none explained |
| **Work Breakdown Structure** | Used as a completeness check by [S100]; never defined |
| **Product designer vs UX designer** | [S069] was an extraction stub — see [99-reference/excluded-content.md](99-reference/excluded-content.md) |
| **Remote/async ideation** | [S129] names a "remote spreadsheet method" and does not describe it |
| **Mind mapping origins** | Buzan not mentioned anywhere |

---

## How to run phase 2

Applying this project's own rules:

1. **Respect the source hierarchy.** Level 1 primary and standards documentation first (Scrum Guide,
   agilemanifesto.org, PMBOK, NIST, DSDM). Level 2 academic and recognised books. Level 3 reputable
   professional publications. **Level 4 — blogs, communities, vendor content — for *discovery* of
   sources only, never as authority.**
2. **Cross-verify anything important.** Statistics, efficacy claims, causal claims and contested
   definitions need more than one independent source.
3. **Document disagreement rather than choosing.** Follow the pattern in
   [99-reference/disputed-information.md](99-reference/disputed-information.md).
4. **Mark provenance.** Any content added from external research must carry
   `source_type: external_research` and `verified: true|false` in its frontmatter, and must appear
   in [SOURCES.md](SOURCES.md) as a phase-2 source. **Never blend external research into corpus-derived
   content without marking it.**
5. **Where evidence remains insufficient, say so.** Use `UNKNOWN`, `UNVERIFIED`,
   `INSUFFICIENT_EVIDENCE`, `DISPUTED`. A recorded gap is more useful than a confident invention.
6. **Do not fill gaps from model memory.** That is the rule this document exists to enforce.

---

## Related

- [SOURCES.md](SOURCES.md) — including primary sources referenced but not held
- [99-reference/disputed-information.md](99-reference/disputed-information.md) — what needs verifying
- [CORPUS_AUDIT.md](CORPUS_AUDIT.md) — how these gaps were found
- [CONCEPT_GRAPH.md](CONCEPT_GRAPH.md) §6 — missing links between concepts
