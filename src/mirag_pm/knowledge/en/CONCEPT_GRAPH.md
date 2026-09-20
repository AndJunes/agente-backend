# CONCEPT GRAPH

Relationships between concepts, so that an agent can reason about **what follows from what** rather
than only retrieving definitions.

> ## How to read this document
>
> Every relationship below is labelled with its status:
>
> - **[CORPUS]** — the relationship is stated by a source. The source is named.
> - **[SYNTHESIS]** — the relationship is an inference this knowledge base draws by combining
>   sources. It is defensible but **no single source states it.**
> - **[DISPUTED]** — sources disagree about the relationship. Both positions are given.
> - **[INFERENCE]** — *(added in Phase 2)* a relationship drawn across sources **that were not
>   designed to support it** — typically an empirical study plus a practice document. **Weaker than
>   [SYNTHESIS]** and always flagged where it is used.
>
> Citations prefixed `[E]` are **Phase-2 external research**, resolvable in the separate register in
> [SOURCES.md](SOURCES.md).
>
> **The corpus does not contain a single, agreed model of how product concepts relate.** Different
> traditions in it — UX discovery, PMI project management, agile delivery, growth — use different
> vocabularies and were never reconciled by their authors. The graphs below are the best available
> reconstruction, not a standard.

---

## 1. The main chain: from strategy to shipped work

```
        COMPANY STRATEGY / ANNUAL OBJECTIVES
                    │
                    ▼
            PRODUCT VISION                    the destination            [S080, S094]
                    │
                    │  "The product vision, combined with the annual company
                    │   objectives, drives the product strategy."  [S094]
                    ▼
            PRODUCT STRATEGY                  the route                  [S090, S080]
                    │
                    │  strategy states: users · needs · business benefits
                    │  · standout features                                [S040]
                    ▼
            GOALS / OKRs                      the road signs             [S080, S104]
                    │
                    │  "After setting goals and initiatives, that is when
                    │   you can start product planning and building out a
                    │   roadmap."                                         [S104]
                    ▼
            INITIATIVES / THEMES              broad efforts              [S090, S119]
                    │
                    ▼
         ┌──── PRIORITIZATION ────┐           what deserves capacity     [S119, S066]
         │                        │
         ▼                        ▼
    ROADMAP                   BACKLOG          direction / candidates    [S035, S032]
         │                        │
         │                        │  refinement: detail added as work approaches  [S127]
         │                        ▼
         │              STORIES / JOB STORIES                            [S127, S052]
         │                        │
         │                        ▼
         │              ACCEPTANCE CRITERIA                              [S127]
         ▼                        ▼
    RELEASE PLAN ─────────→ SPRINT / DELIVERY                            [S035, S126]
                                  │
                                  ▼
                            LAUNCH  →  METRICS  →  learning              [S124, S118]
                                  │                    │
                                  └────────────────────┘
                                       feeds back into strategy
```

**Status: [SYNTHESIS].** Each individual link is stated by the cited source; **the full chain is
not stated by any source.** In particular, the corpus disagrees about one link — see §2.

---

## 2. The disputed link: does the roadmap draw from the backlog, or filter it?

**[DISPUTED]**

| Position A — the roadmap draws from the backlog | Position B — the outcome filters the backlog |
|---|---|
| [S119]: "dive into the backlog and see which items **match up with those larger themes** before engaging in a prioritization exercise" | [S040]: "**Start by removing any backlog items which are not required to create the desired outcome. Delete or archive them.**" |
| The backlog is the **source** of roadmap candidates | The outcome is a **filter** applied to the backlog |
| Bottom-up: what could we do, and which of it serves our themes? | Top-down: what must be true to hit this outcome, and what in the backlog serves it? |

> **Both are real working models.** Position A suits teams with an established product and a large
> candidate pool; Position B suits teams transitioning to outcome-based planning, where the backlog's
> existing contents are the problem being solved. An agent should establish which model a team is
> using before advising on either.

---

## 3. Discovery: from uncertainty to a validated opportunity

```
  UNKNOWNS blocking progress  /  team not aligned on what to achieve        [S028]
                    │
                    ▼
            DISCOVERY (Discover + Define of the Double Diamond)            [S028]
                    │
        ┌───────────┼───────────────┬─────────────────┐
        ▼           ▼               ▼                 ▼
  exploratory  stakeholder     assumption        research-question
   research    interviews       mapping            generation              [S028]
        │           │               │                 │
        └───────────┴───────┬───────┴─────────────────┘
                            ▼
              ASSUMPTIONS prioritised by
              importance × uncertainty                                      [S087, S028]
                            │
                            │  "The riskiest assumptions should be
                            │   prioritized in terms of research activities" [S028]
                            ▼
              RESEARCH QUESTION  →  choose method                           [S105]
                            │        (qual/quant × behavioral/attitudinal)
                            ▼
                      VALIDATION
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        validated                   invalidated
              │                           │
              ▼                           ▼
      PROBLEM STATEMENT            reframe · pivot · STOP                   [S028]
      + desired outcomes
              │
              ▼
        IDEATION (at the END of discovery, not the start)                   [S028]
              │
              ▼
        OPPORTUNITY  →  assessment (if the bet is large)                    [S081]
              │
              ▼
        PRIORITIZATION
```

**Status: [CORPUS] for each step; [SYNTHESIS] for the sequence.**

**The two most consequential claims in this graph:**

1. **Ideation belongs at the end of discovery.** [S028] places the ideation workshop last; [S018]
   places SCAMPER in *Develop*, after *Define*; [S136] says skip brainstorming if you "haven't done
   basic research." **Three independent sources agree.**
2. **"Stop" is a legitimate output.** [S028]: "the end of a discovery might be a decision not to
   move forward with the project because, for example, there isn't a user need."

---

## 4. The reasoning chains a PM agent should be able to run

These are the inferences this knowledge base is built to support. Each is grounded in the sources
indicated.

### 4.1 An unvalidated problem should not become a committed feature

```
The problem is not validated
        → the assumption "users have this problem" is critical AND uncertain   [S087]
        → therefore it is a priority for validation, not for building          [S028]
        → validation requires a research question and a fitting method         [S105]
        → until then, the item belongs in discovery, not on a roadmap
          as a dated commitment                                                [S119]
```
**[SYNTHESIS]**, each link [CORPUS].

### 4.2 A prioritized initiative is not yet executable work

```
Prioritized initiative
        → still needs decomposition into epics and stories                     [S126, S127]
        → stories need enough detail for the team's CURRENT decision           [S127]
        → detail is added progressively, through refinement                    [S127]
        → before a sprint: who benefits, what outcome, why now, small enough,
          not split by technical layer, what must be true to be done           [S127]
```
**[CORPUS]** — [S127] states this directly.

### 4.3 A roadmap and a backlog do different jobs

```
Roadmap  = direction and why       → audience: everyone, tailored             [S119]
Backlog  = prioritized candidates  → audience: the delivery team              [S032]
Release plan = the schedule        → highest commitment                       [S035]

∴ "Is X on the roadmap?" and "Is X in the backlog?" are different questions,
  and an item can be in one and not the other without contradiction.
```
**[SYNTHESIS]** — see
[05-planning/roadmap-vs-backlog-vs-release-plan.md](05-planning/roadmap-vs-backlog-vs-release-plan.md).

### 4.4 A good decision is not the same as a good outcome

```
Every decision involves risk; we cannot know the future                        [S106]
        → a good decision balances risk and reward,
          it is not one that happened to work out                              [S106]
        → therefore judging decisions by outcomes will punish sound reasoning
          and reward luck
        → therefore: record the reasoning, assess success AND failure cases
          independently, and define a kill condition before you start          [S106, S031]
```
**[CORPUS]** for the premise; **[SYNTHESIS]** for the resulting practice.

### 4.5 Delivering the thing is not the same as succeeding

```
Project risk  = threats to schedule, cost, scope, quality                      [S100]
Product risk  = the product doesn't work the way people need                   [S087]

∴ a project can succeed while the product fails
  (on time, on budget, to spec — and unused)                                   [S087's example]
∴ project monitoring will not detect product risk
∴ outcome metrics, not delivery metrics, are the test                          [S080]
```
**[SYNTHESIS]**, each link [CORPUS].

### 4.6 The real competitor is often not a competitor

```
JTBD: "the most significant competition ... is the status quo"                 [S054]
Competitive analysis: substitutes and "do nothing" competitors                 [S025]
Lean Canvas: "existing alternatives ... with or without competitors"           [S005]
JTBD forces: inertia and anxiety act AGAINST switching                         [S054]

∴ a feature-parity roadmap addresses the wrong opponent
∴ reducing switching cost and anxiety may beat adding capability
```
**[SYNTHESIS]** — three independent traditions converge.

### 4.7 If you cannot say no, the problem is not your process

```
Outcome-based roadmapping requires declining requests that don't serve
  the goal                                                                     [S040]
        → "If you cannot decline a feature request, you lack the necessary
           level of empowerment to do an effective product management job"     [S040]
        → cf. "agile is a cultural value" — ceremonies without changed
           decision rights produce cargo cult agile                            [S022]

∴ methodology failures are often authority failures in disguise
```
**[SYNTHESIS]** from two sources that never reference each other.

---

## 5. Cross-domain bridges

Concepts that appear in more than one tradition, with different names or emphases.

| Concept | Appears as | In |
|---|---|---|
| **Assumption risk** | *assumption analysis* (PMI) · *assumption mapping* (product) · *assumption-mapping workshop* (UX discovery) | [S100] · [S087] · [S028] |
| **Probability × impact** | *risk assessment matrix* · *probability & consequence 2×2* in decision-making | [S051] · [S106] |
| **Reversibility** | *one-way / two-way doors* (decisions) · *reversibility* (prioritization criterion) · *rollback* (product risk) | [S106] · [S031] · [S087] |
| **Divergence then convergence** | *Double Diamond* · *generate then evaluate* (ideation) · *exploratory then focused* (discovery) | [S110] · [S136] · [S028] |
| **Desirable / viable / feasible** | *DVF* (product triad) · *valuable/usable/feasible* (Cagan) · *business/tech/UX* (Eriksson) · *strategic fit/user value/business value* (opportunity validation) | [S115] · [S140] · [S140] · [S004] |
| **Functional / emotional / social** | *JTBD dimensions* · *market needs types* · *Osterwalder customer profile* | [S054] · [S041] · [S005] |
| **Written, anonymous ideation** | *brainwriting / 6-3-5* · *Delphi technique* (risk) · *nominal group technique* | [S010] · [S100] · [S125] |
| **Affinity grouping** | *affinity mapping* (ideation) · *affinity-diagramming workshop* (discovery) · *affinity diagram* (risk identification) | [S136] · [S028] · [S125] |
| **Stopping work** | *kill condition* (prioritization) · *shared vision enables stopping* (collaboration) · *decision not to proceed* (discovery) · *end-of-life* (lifecycle) | [S031] · [S008] · [S028] · [S134] |
| **"North star"** | *the product vision* · *a metric* · *a product principle* | [S094] · [S003], [S108] · [S080] — **[DISPUTED]**, see [99-reference/disputed-information.md](99-reference/disputed-information.md) |
| **A standing, team-level quality bar** | *Definition of Done* (Scrum, Increment commitment) · *explicit policy* (Kanban) · *constitution* (spec-kit, per project) · *release criteria* (PRD) | [E001] · [E003] · [E012] · [S048] — **[SYNTHESIS]**: four traditions, same structural role |
| **Ordering the input queue** | *Product Owner ordering the Product Backlog* · *Service Request Manager at the Replenishment Meeting* · *prioritization* | [E001] · [E003] · [S066] — [E003] names **Product Manager and Product Owner as alternative titles for one function**; **[DISPUTED]**, see [99-reference/disputed-information.md §7.1](99-reference/disputed-information.md) |
| **Small units of work** | *story sized to one sprint* · *small batches* · *limit WIP* · *"maximizing the amount of work not done"* (principle 10) | [S126] · [E008] · [E003] · [E002] — four independent arguments for the same lever |
| **Do not specify the how** | *outcome-based roadmaps* · *"grade outputs, not step sequences"* (agent evals) · *"requirements emerge from self-organizing teams"* (principle 11) | [S040] · [E011] · [E002] — **[SYNTHESIS]**: same failure mode, three implementers |
| **Layered controls, no single guarantee** | *risk response strategies* · *Swiss Cheese model* (evals) · *feedback loops / seven cadences* (Kanban) · *inspect and adapt* (Scrum's three pillars) | [S051] · [E011] · [E003] · [E001] |
| **Forecast from history, not from intent** | *"base your estimate on past performance"* · *"forget estimation — what has happened in the past?"* · *probabilistic forecasting from flow data* | [S003] · [S108] · [E003] — **[E003] supplies the method the corpus sources only gestured at** |

---

## 6. Where the graph breaks — links the corpus does not make

These are missing connections, recorded so an agent does not invent them.

| Missing link | Why it matters |
|---|---|
| **Opportunity Solution Tree ↔ epic/story hierarchy** | The OST ([S110]) and the initiative→epic→story model ([S126]) come from different traditions and are never connected. The mapping in [06-requirements/epics-and-decomposition.md](06-requirements/epics-and-decomposition.md) is an explicit inference |
| **Estimation ↔ prioritization** | Every prioritization framework consumes effort estimates; the corpus never explains how to produce them. **Phase 2 partially bridged this** — [E003]'s probabilistic forecasting produces *dates from flow*, not *effort scores per item*, so the specific input RICE and value/effort need is **still missing**. See ⚠ [05-planning/estimation.md](05-planning/estimation.md) |
| **Metrics ↔ decisions** | Metrics are named everywhere and taught nowhere. The link from a measurement to a product decision is asserted, never demonstrated |
| **Discovery ↔ delivery cadence** | Dual-track is described ([S110]) but how far discovery should run ahead of delivery is never stated |
| **Technical debt ↔ anything** | Named as a roadmap concern [S119], a product risk [S087], and something engineers want to prioritize [S049]. **Never defined or connected to a practice** |
| **Pricing ↔ value** | The Value-Price-Cost framework is introduced [S092] and pricing is never treated. Value cannot be fully reasoned about without it |
| **AI agents ↔ product management** | **Partially bridged in Phase 2** by [13-ai-agent-collaboration/](13-ai-agent-collaboration/), and the bridge is thin. **No source studies the PM role under agent implementation**; five of the connections drawn are labelled **[INFERENCE]**. The corpus still contains only [S031], on agents as *users* |
| **Agent implementation ↔ team structure** | ❌ **Not bridged at all.** Nothing found on how a multi-agent software team is organised — roles, handoffs, orchestration. **This is the project's own reason for existing.** See [13-ai-agent-collaboration/open-questions-ai-and-pm.md](13-ai-agent-collaboration/open-questions-ai-and-pm.md) §B1 |
| **Agile frameworks ↔ non-human implementers** | [E001] presumes human Developers self-managing; [E003] presumes people self-organising around work; [E002] principle 6 names face-to-face conversation. **No source examines whether any of this holds when the implementer is an agent.** Do not assume it does, and do not assume it does not |
| **Review capacity ↔ flow** | [E006]'s <44% acceptance rate, [E008]'s instability finding and [E009]'s "verification tax" converge on review as a constraint — but **no study tested it**, and [E003]'s flow apparatus that would measure it has not been applied to the question. **[INFERENCE]**, and the cheapest one to test |

---

## 7. The provenance dimension — added in Phase 2

A relationship's **status** ([CORPUS] / [SYNTHESIS] / [INFERENCE] / [DISPUTED]) says how firmly it is
established here. It does **not** say where the underlying claims come from. That is a second,
independent question, and conflating the two is the most likely reasoning error in this knowledge
base:

| | What the creator said | What a later reading says | What is current practice | What has been measured |
|---|---|---|---|---|
| **Scrum** | [E001] | [S078], [S118], [S126] | story points, velocity — **not in [E001]** | ❌ nothing here |
| **Kanban** | [E003], [E004] | [S130], [S048] — **as a board** | [E003]'s own practice sections | ❌ nothing here |
| **Agile** | [E002] | [S022] | [S022]'s "faux agile" diagnosis | ❌ nothing here |
| **MVP** | ❌ not obtained | [S110], [S106], [S072] | ❌ | ❌ |
| **AI-assisted delivery** | — | [E010] | [E011], [E012], [E013] | **[E006], [E007], [E008]** |

> **Read the last column.** For three of the four framework rows it is empty. **This knowledge base
> can tell you precisely what Scrum, Kanban and Agile *are*, and cannot tell you whether they
> *work*.** Stating the first as though it established the second is the error this table exists to
> prevent.
>
> Conversely, the AI row is the only one with real empirical entries and the only one whose
> creator column is empty — there is no originator to appeal to, which is why
> [13-ai-agent-collaboration/](13-ai-agent-collaboration/) leans on measurement and labels everything
> else.

---

## Related

- [INDEX.md](INDEX.md) — concept → document retrieval
- [TAXONOMY.md](TAXONOMY.md) — how the domains are organised
- [GLOSSARY.md](GLOSSARY.md) — term definitions
- [99-reference/disputed-information.md](99-reference/disputed-information.md) — where sources conflict
- [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) — the missing links, as research tasks
