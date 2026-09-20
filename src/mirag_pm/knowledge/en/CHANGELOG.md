# CHANGELOG

## [1.1.0] — 2026-09-16 · Phase 2, first research pass

**External research begins.** Fourteen sources retrieved deliberately against gaps named in
[RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md). **The backlog was treated as a map, not a list of
expected answers** — two gaps closed differently from how they were framed, and the largest one did
not close at all.

### Convention established — corpus material and researched material never blend

| Mechanism | What it does |
|---|---|
| **Separate ID space** — `[Ennn]` vs `[Snnn]` | Visible at the point of citation, not just in metadata |
| **Frontmatter** — `external_research`, `verified`, `phase` | Filterable at retrieval time |
| **`provenance:` block** — `primary` / `interpretation` / `practice` / `empirical` | Records **which of the four provenance levels** each source supplies for that document |
| **Separate register** — [SOURCES.md § External sources](SOURCES.md) | With a provenance code and reliability tier per source |

The four provenance levels, applied throughout: **what the original creator said** · **what a later
interpretation says** · **what is considered current practice** · **what empirical evidence exists.**
These are typed per source, and a document can cite the same topic at more than one level.

### Added — new domain: `13-ai-agent-collaboration` (5 documents)

| Document | What it is |
|---|---|
| [evidence-on-ai-assisted-delivery.md](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) | The empirical record — METR's RCT, its authors' own later qualification, DORA's survey. **Read first** |
| [pm-with-ai-implementers.md](13-ai-agent-collaboration/pm-with-ai-implementers.md) | What changes in the PM's job, and what does not. `confidence: low` — five of its seven claims are labelled inferences |
| [spec-driven-development.md](13-ai-agent-collaboration/spec-driven-development.md) | SDD, spec-kit, Kiro, EARS. Widely adopted; **no efficacy evidence**, stated up front |
| [evals-and-acceptance-for-agents.md](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md) | Evals, grader types, **pass@k vs pass^k**, Swiss Cheese layering |
| [open-questions-ai-and-pm.md](13-ai-agent-collaboration/open-questions-ai-and-pm.md) | **24 questions with no answer in this knowledge base**, and what would settle each |

> **The gap register is longer than the answer document. That is the finding, not a shortfall.**
> `pm-with-ai-implementers.md` carries `confidence: low` and `verified: partial`, and every
> cross-study inference in it is labelled `[INFERENCE]` or `[SYNTHESIS]`.

### Added — `07-execution` (2 documents)

- **[scrum.md](07-execution/scrum.md)** — from [E001], the 2020 Scrum Guide. Accountabilities,
  five events with timeboxes, three artifacts with commitments, the three pillars, five values, and
  **an explicit section on what Scrum deliberately does not define** (estimation, user stories, the
  PM role, metrics, scaling)
- **[kanban.md](07-execution/kanban.md)** — from [E003] and [E004]. Six principles, six practices,
  nine values, three agendas, **Little's Law and flow metrics**, cost of delay and classes of
  service, **probabilistic forecasting**, the seven cadences, STATIK, the Kanban Litmus Test

### Changed — corrections applied to existing documents

| Document | Correction | Authority |
|---|---|---|
| [agile-manifesto.md](07-execution/agile-manifesto.md) | **The twelve principles added verbatim** — the corpus's largest single omission — with a table of what each settles elsewhere | [E002] |
| [acceptance-criteria.md](06-requirements/acceptance-criteria.md) | **[S126] and [S128] use "definition of done" incorrectly.** It is an Increment/team-level standing standard, not item-level acceptance criteria | [E001], [E003] |
| [roadmap-formats.md](05-planning/roadmap-formats.md) | **"Kanban roadmap" is a board, not a kanban system.** Without WIP limits and defined commitment/delivery points it is a flow visualisation | [E003] |
| [estimation.md](05-planning/estimation.md) | Scrum prescribes **no** estimation technique; principle 7 rules out velocity as a *measure of progress*; **probabilistic forecasting** added as a method; one measurement of estimation calibration | [E001], [E002], [E003], [E006] |
| [product-manager-vs-product-owner.md](01-foundations/product-manager-vs-product-owner.md) | Backlog accountability **settled** for Scrum teams; the PM/PO relationship shown to be a **three-way disagreement between primary sources**, not a corpus confusion | [E001], [E003] |
| [user-stories.md](06-requirements/user-stories.md) | [E001] says **"Product Backlog items"**, never "story"; PO is accountable without being the author | [E001] |
| [project-monitoring-and-control.md](07-execution/project-monitoring-and-control.md) | Flow-measurement layer supplied — lead time, delivery rate, WIP, cumulative flow, service levels | [E003] |
| [disputed-information.md](99-reference/disputed-information.md) | **§6 added** — four corpus claims settled by primary sources, corpus wording preserved. **§7 added** — five disagreements *between* authorities, explicitly not resolved | — |

> **Nothing was deleted.** A corpus claim shown to be wrong is still recorded, with the correction
> beside it: a widely read vendor guide's usage is evidence of what the field is being told.

### Added — sources (14)

| | |
|---|---|
| **Primary texts** | [E001] Scrum Guide 2020 · [E002] the twelve Agile principles · [E003] *Essential Kanban Condensed* · [E004] Kanban Guide · [E014] EARS (Mavin, Rolls-Royce, 2009) |
| **Empirical** | [E006] METR RCT (Jul 2025) · [E007] METR's own design update (Feb 2026) · [E008] DORA *State of AI-assisted Software Development* 2025 (n≈5,000) |
| **Practice / tool** | [E011] Anthropic, *Demystifying evals for AI agents* · [E012] GitHub spec-kit · [E013] Kiro (AWS) docs |
| **Flagged low-reliability** | [E009] DORA ROI 2026 — **vendor projection, not read in original** · [E010] InfoQ — secondary route to [E009] |
| **Bibliography only** | [E005] Anderson, *Kanban* (2010) — **not consulted**; nothing attributed to it |

### Verification performed
- **[E001]** — confirmed the November 2020 edition is current as of September 2026
- **[E002]** — the four values, quoted in the corpus from Atlassian [S022], **checked against the
  canonical text and confirmed accurate**
- **[E006]** — full paper retrieved and read, including the factor analysis and the authors' own
  published list of misreadings
- **[E007]** — retrieved specifically to test whether [E006] still stands. **It does not, as a
  description of current tooling, per its own authors**
- **[E003]** — full text extracted and read, not summarised from a secondary source

### Notable findings
- **[E006] measured the perception gap**: developers predicted AI would make them 24% faster,
  reported 20% faster afterwards, and were measurably **19% slower**. Economics experts predicted
  39%, ML experts 38%. **Self-report is not measurement** — the most transferable result in the
  literature.
- **[E007] then qualified [E006]** within seven months. The finding is recorded as valid for its
  period, **superseded for current tooling by its own authors, and not replaced.**
- **[E008]**: *"In the absence of a user-centric focus, AI adoption has a negative impact on team
  performance."* The only empirically grounded statement found on why the product function matters
  when implementation accelerates — and a **moderation** result, correlational and self-reported.
- **[E001] and [E003] disagree fundamentally** on how change happens: *"the result is not Scrum"*
  versus *"start with what you do now."* Both are originators. **Not resolved.**

### Known limitations
- **Nine of fourteen external sources are vendor-published.** The parties writing about AI-assisted
  development are largely the parties selling it
- **Gaps 1.2 (MVP) and 1.3 (metrics design) were not touched** in this pass
- **No multi-agent team organisation material was found** — the project's own central question
- **[E009] was not read in the original**; everything attributed to it is via [E010]
- **This is the fastest-dating material in the knowledge base.** `last_reviewed` is load-bearing in
  `13-ai-agent-collaboration/`, not decorative

---

## [1.0.0] — 2026-09-16

First build. Corpus audited, cleaned, consolidated and structured. **Phase 1 only — no external
research performed.**

### Input
- 143 PDF sources from `~/Downloads/PM-carrer/`
- 1,645 pages · ~344,700 extracted words · ~60 publishers · 2013–2026 (where dated)

### Added — knowledge documents (81)

| Domain | Documents |
|---|---|
| **01-foundations** (7) | product-management · product-manager-role · product-manager-skills · product-vs-project-management · product-manager-vs-product-owner · pm-and-ux-collaboration · pm-specializations |
| **02-discovery** (11) | product-discovery · discovery-frameworks · user-research-methods · user-interviews · surveys · usability-testing · ethnographic-research · jobs-to-be-done · hypotheses-and-assumptions · opportunity-assessment · identifying-unmet-needs |
| **03-market-intelligence** (4) | competitive-analysis · market-research · market-needs · market-trends |
| **04-strategy** (10) | product-strategy · product-vision · strategic-thinking · product-goals · okrs · positioning · value-proposition · product-value · product-led-growth · product-market-fit |
| **05-planning** (12) | roadmaps · outcome-based-roadmaps · roadmap-formats · continuous-roadmapping · roadmap-communication · roadmap-vs-backlog-vs-release-plan · prioritization · prioritization-frameworks · backlog-management · release-planning · estimation · dependencies |
| **06-requirements** (7) | prd · requirements · user-stories · job-stories · acceptance-criteria · scope-definition · epics-and-decomposition |
| **07-execution** (5) | agile-manifesto · working-with-engineering · product-collaboration · product-development-process · project-monitoring-and-control |
| **08-ideation** (5) | brainstorming · brainwriting · scamper · mind-mapping · idea-evaluation |
| **09-metrics** (3) | product-metrics · pirate-metrics · north-star-metric |
| **10-risk** (8) | risk-management · risk-identification · risk-assessment · risk-response · risk-monitoring · product-risk · it-and-security-risk · assumptions-and-constraints |
| **11-lifecycle-and-launch** (5) | product-lifecycle · managing-maturity · decline-and-end-of-life · go-to-market · product-launch |
| **12-design-and-ux** (4) | product-triad · ux-for-product-managers · product-design-fundamentals · service-design |

### Added — navigation and traceability
- `README.md` · `INDEX.md` (562 concept terms) · `TAXONOMY.md` · `CONCEPT_GRAPH.md` ·
  `GLOSSARY.md` · `SOURCES.md` (143-row register) · `RESEARCH_BACKLOG.md` · `CORPUS_AUDIT.md`
- `99-reference/excluded-content.md` · `disputed-information.md` · `outdated-information.md`

### Processing
- **Extracted** all 143 PDFs with `pdftotext -layout`
- **Cleaned** boilerplate: −2.8% (line filter) then −7.4% (footer truncation) → ~319,400 words
- **Detected and repaired** over-trimming in 9 files retaining <65% of raw words (S006, S011, S017,
  S023, S083, S086, S091, S104, S121). Without this, four documents would have been built on as
  little as 16% of their source
- **Consolidated** heavy topical redundancy — 15 roadmap sources → 6 documents; 12 risk sources → 8;
  11 ideation sources → 5 — organising by *question answered* rather than by source
- **Assigned** a reliability tier (A/B/C) to every source

### Decisions
- **Structure derived from the corpus**, not the proposed template. Three domains added (ideation,
  market intelligence, lifecycle & launch); two merged into others (prioritization-frameworks into
  planning; engineering-collaboration into execution); one dissolved (artifacts, distributed to
  where each artefact is used). Rationale in [TAXONOMY.md](TAXONOMY.md)
- **Contradictions preserved, not resolved** — 7 direct contradictions, 4 ambiguous terms, 4
  internal inconsistencies, all catalogued
- **Unverified statistics reproduced with do-not-cite flags** rather than deleted, so the corpus's
  claims remain visible
- **Gaps documented as documents.** `estimation.md`, `north-star-metric.md` and others exist
  specifically to record that the corpus cannot answer those questions

### Excluded
- **5 sources entirely:** S002 (tool pricing) · S027 (out of domain — Stellar blockchain, appears
  misfiled) · S069 (extraction stub) · S120 (link farm) · S121 (promotional announcement)
- **2 sources as duplicates:** S055, S139
- **Categories stripped from retained sources:** CTAs, navigation, cookie banners, tool promotion,
  certification marketing, testimonials, comment sections, contact details
- Full record: [99-reference/excluded-content.md](99-reference/excluded-content.md)

### Known limitations
- **No external research performed.** Priority-1 gaps — Scrum/Kanban mechanics, MVP, metrics design,
  estimation, and working with AI agents — remain open
- **108 of 143 sources carry no determinable date**
- **All images failed to extract**, so diagrams, canvases and framework figures are absent
- **~10 sources substantially truncated** by PDF capture; each affected document records the loss
- **~85% of the corpus is commercially motivated**; this is disclosed per document

---

## [Unreleased] — phase 2, remaining

Per [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md), in priority order:

1. **1.2 MVP** — the Robinson (2001, economic/ROI framing) vs Ries (validated-learning framing)
   split is a clean creator-versus-popularizer case and is the next cheapest primary-source gap
2. **1.3 Product metrics and measurement design** — including the North Star Metric, referenced by
   four corpus sources and defined by none
3. **1.5 continued** — field reports on multi-agent team organisation. Level-4 sources are legitimate
   for *discovery* here and **never as authority**
4. **Priority 2** — product-market fit · pricing · technical debt · release mechanics · WSJF
5. **Accessibility** — absent from the knowledge base entirely; currently filed as Priority 4 and
   arguably misplaced there
