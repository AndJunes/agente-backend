# TAXONOMY

How this knowledge base is organised, and why it is organised this way.

## The organising principle

Documents are grouped by **the kind of question they answer**, not by the document they came from
and not by the template this project started with. The structure below **emerged from the corpus**:
domains exist where the corpus had enough material to support them, and the two largest domains
(Planning and Strategy) are large because the corpus was heaviest there.

Two consequences worth stating up front:

- **Some domains are thin because the corpus was thin.** Metrics has 3 documents because the corpus
  had 2 substantive sources on measurement. That is recorded, not hidden.
- **Some domains exist that the original template did not anticipate** — Ideation, Market
  Intelligence, Lifecycle & Launch — because the corpus contained 11, 10 and 12 sources on them
  respectively. Omitting them would have discarded real knowledge.

## The tree

```
pm-knowledge-base/
│
├── 01 · FOUNDATIONS ─────────── What the discipline is and who does it
│   ├── Product management (definition, scope, history, levels)
│   ├── Product manager role (three pillars, responsibilities, craft)
│   ├── Product manager skills (competency map)
│   ├── Product vs project management
│   ├── Product manager vs product owner
│   ├── PM and UX role boundaries        ← survey evidence, n=372
│   └── PM specializations (four types of product work)
│
├── 02 · DISCOVERY ───────────── Understanding the problem before solving it
│   ├── Product discovery (the phase and its outputs)
│   ├── Discovery frameworks (dual-track, Design Sprint, JTBD, Double
│   │                          Diamond, Lean Startup, Opportunity Solution Tree)
│   ├── Choosing a user research method   ← the qual/quant × behavioral/attitudinal rule
│   ├── User interviews and interview guides
│   ├── Surveys (including when NOT to run one)
│   ├── Usability testing
│   ├── Ethnographic research
│   ├── Jobs to be Done
│   ├── Hypotheses, assumptions and validation
│   ├── Opportunity assessment
│   └── Identifying unmet customer needs
│
├── 03 · MARKET INTELLIGENCE ─── Understanding the market and the competition
│   ├── Competitive analysis     ← incl. substitutes and "do nothing" competitors
│   ├── Market research
│   ├── Market needs (functional / emotional / social)
│   └── Market trend analysis
│
├── 04 · STRATEGY ───────────── Direction, and the reasoning behind it
│   ├── Product strategy (and what a strategy is NOT)
│   ├── Product vision (and how it differs from mission)
│   ├── Strategic thinking       ← the decision framework: 6 factors, success vs failure
│   ├── Product goals (OKRs, NCTs, Dream Maps, MSPOTs, V2MOMs)
│   ├── OKRs
│   ├── Positioning
│   ├── Value proposition (4 models + the 40% test)
│   ├── Product value (value / price / cost)
│   ├── Product-led growth (and the four growth models)
│   └── Product-market fit                ⚠ gap
│
├── 05 · PLANNING ───────────── Deciding what to do, and communicating it
│   ├── Roadmaps (definition, audiences, admission filter, ownership)
│   ├── Outcome-based roadmaps            ← incl. the 4-step transition
│   ├── Roadmap formats (timeline, Now-Next-Later, Kanban, agile, theme-based)
│   ├── Continuous roadmapping
│   ├── Roadmap communication and stakeholder alignment
│   ├── Roadmap vs backlog vs release plan
│   ├── Prioritization (the practice and its failure modes)
│   ├── Prioritization frameworks (RICE, Kano, MoSCoW, value/effort,
│   │                              opportunity scoring, cost of delay, weighted)
│   ├── Backlog management                ⚠ partial
│   ├── Release planning                  ⚠ gap
│   ├── Estimation                        ⚠ gap — documented, not answered
│   └── Dependencies                      ⚠ gap
│
├── 06 · REQUIREMENTS ───────── Specifying what gets built
│   ├── PRD (incl. the "is it obsolete?" debate)
│   ├── Requirements (functional / non-functional / assumptions / constraints)
│   ├── User stories                      ← Mike Cohn; card, conversation, confirmation
│   ├── Job stories (and when to prefer them)
│   ├── Acceptance criteria
│   ├── Scope definition and scope creep
│   └── Epics and decomposition
│
├── 07 · EXECUTION ──────────── Getting it built
│   ├── The Agile Manifesto               ← four values + twelve principles, primary text
│   ├── Scrum                             ← from the 2020 Scrum Guide            [E] phase 2
│   ├── Kanban (the Kanban Method)        ← from Anderson & Carmichael           [E] phase 2
│   ├── Working with engineering
│   ├── Cross-functional product collaboration
│   ├── The product development process (4 phases)
│   └── Project monitoring and control
│
├── 08 · IDEATION ───────────── Generating and converging on options
│   ├── Brainstorming (and when to skip it)
│   ├── Brainwriting and 6-3-5            ← best-referenced material in the corpus
│   ├── SCAMPER
│   ├── Mind mapping
│   └── Evaluating and converging on ideas
│
├── 09 · METRICS ───────────── Knowing whether it worked
│   ├── Product metrics                   ⚠ gap — definitions only
│   ├── Pirate metrics (AARRR / RARRA)
│   └── North Star Metric                 ⚠ gap — referenced by four sources, defined by none
│
├── 10 · RISK ──────────────── What could go wrong, and what to do about it
│   ├── Risk management foundations       ← PMI definition; risk includes opportunity
│   ├── Risk identification (10 barriers, 6-stage lifecycle, tools)
│   ├── Risk assessment and analysis (probability × impact, data quality)
│   ├── Risk response (avoid/transfer/mitigate/accept/escalate + positive strategies)
│   ├── Risk monitoring and control
│   ├── Product risk                      ← 16-item product-risk taxonomy
│   ├── IT and security risk
│   └── Assumptions and constraints as risk sources
│
├── 11 · LIFECYCLE & LAUNCH ─── The product's life in the market
│   ├── The product lifecycle (Levitt 1965; six stages; the saturation loop-back)
│   ├── Managing a mature product (feature factory, backlog beast, self-disruption)
│   ├── Decline and end-of-life
│   ├── Go-to-market strategy
│   └── Product launch
│
├── 12 · DESIGN & UX ────────── The experience, and who owns it
│   ├── The Product Triad (Desirable/Viable/Feasible)
│   ├── UX for product managers
│   ├── Product design fundamentals
│   └── Service design
│
├── 13 · AI AGENT COLLABORATION ─ PM work when the implementer is an agent  [E] phase 2
│   ├── What the evidence says about AI-assisted delivery  ← READ FIRST. METR RCT, DORA
│   ├── PM when the implementer is an agent                ⚠ confidence: low — mostly inference
│   ├── Spec-driven development (spec-kit, Kiro, EARS)     ⚠ adopted widely, efficacy unmeasured
│   ├── Evals and acceptance for agents                    ← pass@k vs pass^k, grader types
│   └── Open questions                                     ← 24 questions with no answer here
│
└── 99 · REFERENCE ─────────── Traceability of what was set aside
    ├── excluded-content.md      — what was removed and why
    ├── disputed-information.md  — where sources contradict each other
    └── outdated-information.md  — time-sensitive claims with expiry warnings
```

## Why these boundaries

The structure follows a rough **temporal and logical flow of product work**, which is also how
questions tend to arrive:

```
Who am I and what is this job?              →  01 Foundations
What problem is real?                       →  02 Discovery
What is the market and who else is in it?   →  03 Market Intelligence
Where are we going and why?                 →  04 Strategy
What will we do, in what order?             →  05 Planning
What exactly gets built?                    →  06 Requirements
How does it get built?                      →  07 Execution
Where do options come from?                 →  08 Ideation  (feeds 02 and 05)
Did it work?                                →  09 Metrics
What could go wrong?                        →  10 Risk      (cuts across everything)
What happens over the product's life?       →  11 Lifecycle & Launch
What is the experience, and who owns it?    →  12 Design & UX
```

**Two domains deliberately cut across the flow:**

- **Ideation (08)** feeds both discovery (generating research questions, framing problems) and
  planning (generating solution options). It is separate because its techniques are a coherent body
  of practice in their own right.
- **Risk (10)** applies at every stage. It is separate because the corpus's PMI-aligned risk
  material is structured and substantive enough to stand alone — and because product risk and
  project risk are genuinely different things that are routinely conflated.

## Where this differs from the original template, and why

| Original template | What was done | Reason |
|---|---|---|
| `01-foundations` | Kept, expanded | Corpus had 14 sources on role, skills and specialization |
| `02-discovery` | Kept, expanded | 17 sources; NN/g material is the corpus's evidential core |
| `03-strategy` | Renumbered to **04**; **03 became Market Intelligence** | 10 sources on competitive and market analysis had no home in the template and are distinct from strategy |
| `04-planning` | Renumbered to **05** | — |
| `05-requirements` | Renumbered to **06** | — |
| `06-execution` | Renumbered to **07**; **scope narrowed in Phase 1, restored in Phase 2** | The template assumed Scrum/Kanban/sprint/retrospective coverage. **The corpus had almost none**, so Phase 1 covered only what existed. **Phase 2 added `scrum.md` and `kanban.md` from the primary texts** [E001]–[E004], closing the gap without inventing corpus coverage that never existed |
| `07-prioritization-frameworks` | **Merged into 05-planning** | Frameworks are inseparable from the practice of prioritizing; splitting them would have produced two half-documents |
| `08-metrics` | Renumbered to **09**; **kept small and honest** | Only 2 substantive sources. The domain records what is missing rather than padding |
| `09-risk` | Renumbered to **10**; **expanded** | 11 sources, including the corpus's only standards-aligned material |
| `10-engineering-collaboration` | **Merged into 07-execution** | Only 2 sources; a standalone domain would have been one document |
| `11-artifacts` | **Dissolved** | Artifacts (PRD, roadmap, backlog, release plan) are documented where they are *used*, not in a separate cabinet. A PRD document that did not sit next to requirements would be harder to retrieve |
| — | **08-ideation added** | 11 sources, including the corpus's best-referenced document (6-3-5 brainwriting) |
| — | **11-lifecycle-and-launch added** | 12 sources on lifecycle, maturity, decline, EOL, GTM and launch |
| — | **12-design-and-ux added** | 6 sources, plus NN/g's Product Triad which explains cross-functional ownership |
| — | **13-ai-agent-collaboration added (Phase 2)** | **Not corpus-derived at all.** The corpus contained one source on *agents as users* ([S031]) and nothing on agents as team members. This domain is built entirely from external research and is flagged as such in every document. It sits last because it is the **least settled** material here, not the least important — it is the project's own purpose |
| `99-reference` | Kept | Traceability of excluded, disputed and time-sensitive material |

## Document types

Each document declares a `type` in its frontmatter. This is a retrieval filter — it tells an agent
**what kind of answer the document contains**.

| Type | Means | Example |
|---|---|---|
| `concept` | Defines something and explains its properties | product-management.md |
| `process` | A sequence of steps | risk-identification.md |
| `technique` | A specific method | brainwriting.md |
| `framework` | A named model with defined parts | okrs.md |
| `framework-catalogue` | Several frameworks compared | prioritization-frameworks.md |
| `technique-catalogue` | Several techniques compared | brainstorming.md |
| `artifact` | A document or deliverable | prd.md |
| `comparison` | Distinguishes two or more things | roadmap-vs-backlog-vs-release-plan.md |
| `decision-framework` | Supports making a choice | strategic-thinking.md |
| `practice` | How to do something well, with judgment | working-with-engineering.md |
| `research-finding` | Reports measured evidence | pm-and-ux-collaboration.md |
| `primary-text` | Reproduces a source text | agile-manifesto.md |

## Evidence types

Each document also declares `evidence_type`, which records **what kind of backing the content has**.
This is the field an agent should check before making a strong claim.

| evidence_type | Meaning | Documents |
|---|---|---|
| `empirical-survey` | Measured data, method stated | 1 |
| `empirical-and-practice` | Mixed measured and practitioner | 2 |
| `academically-referenced` | Cites peer-reviewed or primary literature | 2 |
| `standards-aligned` | Quotes a standards body (PMI) | 5 |
| `primary-text-quoted` | Reproduces a primary document | 1 |
| `professional-practice` | Widely held professional practice, asserted | ~30 |
| `practitioner-framework` | A named practitioner's model | ~15 |
| `practitioner-argument` / `practitioner-opinion` | One person's position | ~6 |
| `fragmentary` | Assembled from scattered mentions; **treat with caution** | ~8 |

## Confidence levels

| `confidence` | Means |
|---|---|
| `high` | Multiple sources agree, or a single strong source with stated method |
| `medium` | Substantive but single-sourced, or vendor-sourced without corroboration |
| `low` | Assembled from fragments, or the topic's principal source is weak or truncated. **Documents at this level state their own limits prominently** |

## Phase-2 typing: the provenance axis

Domains organise knowledge by **subject**. Phase 2 added a second, orthogonal axis recording **where
a claim comes from** — declared per document in the `provenance:` frontmatter block:

| Level | Question it answers | Example |
|---|---|---|
| **`primary`** | What did the originator or standard actually say? | [E001] on the Definition of Done |
| **`interpretation`** | What does a later reading say? | [S022] (Atlassian) describing the Manifesto |
| **`practice`** | What is currently done in the field? | [E012] spec-kit's workflow |
| **`empirical`** | What has been measured? | [E006] on developer completion times |

> **These are not a quality ranking.** A primary text is more *traceable*, not automatically more
> correct — and on a question its author never addressed, it is not a source at all. An empirical
> result is bounded by its study conditions. **An empty `empirical` list is meaningful information:
> it says nobody has measured this.**
>
> This axis exists because the four levels routinely disagree, and collapsing them destroys the
> disagreement. See [99-reference/disputed-information.md](99-reference/disputed-information.md)
> §§6–7.

## Related

- [INDEX.md](INDEX.md) — concept → document retrieval map
- [CONCEPT_GRAPH.md](CONCEPT_GRAPH.md) — relationships between concepts
- [README.md](README.md) — how to use this knowledge base
- [CORPUS_AUDIT.md](CORPUS_AUDIT.md) — how the structure was derived
