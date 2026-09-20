# PM Knowledge Base

A structured, traceable knowledge base on product and project management, built from a corpus of
**143 source documents** and extended with **14 externally researched sources**, designed to be
retrieved by an AI agent acting as a Product Manager.

| | |
|---|---|
| **Documents** | 88, across 13 domains |
| **Sources** | **143 corpus** (`[Snnn]`, 138 cited) + **14 external** (`[Ennn]`), each resolvable |
| **Concept index** | 633 terms |
| **Built** | 16 September 2026 · **v1.1.0** |
| **Phase** | **2, first research pass complete** — priority-1 gaps 1.1 closed, 1.4 and 1.5 partially closed; 1.2 and 1.3 open |

---

## What this is, and what it is not

**It is** a consolidation of what 143 product-management articles actually say, organised by the
question each piece of knowledge answers, with every claim traceable to its source and every
weakness stated.

**It is not** a complete product-management reference. The corpus it came from is ~85% commercial
content with significant blind spots. **Where the corpus is thin, this knowledge base says so rather
than filling the gap from memory.** See [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md).

**Since v1.1.0 it also contains external research**, kept strictly separate from corpus material —
different citation prefix, different register, explicit frontmatter flags. See
[Provenance](#provenance) below.

---

## Start here

| You want to… | Go to |
|---|---|
| Find the document that answers a question | **[INDEX.md](INDEX.md)** |
| Understand how the knowledge is organised | [TAXONOMY.md](TAXONOMY.md) |
| See how concepts relate and reason across them | [CONCEPT_GRAPH.md](CONCEPT_GRAPH.md) |
| Look up a term | [GLOSSARY.md](GLOSSARY.md) |
| Resolve a `[Snnn]` **or** `[Ennn]` citation | [SOURCES.md](SOURCES.md) — two separate registers |
| Understand PM work with AI agent implementers | **[13-ai-agent-collaboration/](13-ai-agent-collaboration/)** — start with [the evidence](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) |
| Know what is missing | [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) |
| Know what to distrust | [99-reference/disputed-information.md](99-reference/disputed-information.md) |
| Know what has expired | [99-reference/outdated-information.md](99-reference/outdated-information.md) |
| See how this was built | [CORPUS_AUDIT.md](CORPUS_AUDIT.md) |

---

## The domains

```
01-foundations/          What the discipline is, and who does it
02-discovery/            Understanding the problem before solving it
03-market-intelligence/  The market and the competition
04-strategy/             Direction, and the reasoning behind it
05-planning/             Deciding what to do, and communicating it
06-requirements/         Specifying what gets built
07-execution/            Getting it built
08-ideation/             Generating and converging on options
09-metrics/              Knowing whether it worked
10-risk/                 What could go wrong, and what to do about it
11-lifecycle-and-launch/ The product's life in the market
12-design-and-ux/        The experience, and who owns it
13-ai-agent-collaboration/  PM work when the implementer is an agent  [PHASE 2 — external research]
99-reference/            Traceability of what was set aside
```

The structure was **derived from the corpus**, not imposed on it. See
[TAXONOMY.md](TAXONOMY.md) for why each domain exists and how it differs from the original plan.

---

## How to read a document

Every document has the same shape, so that retrieval is predictable.

### Frontmatter — for metadata filtering

```yaml
---
title: Product Roadmap
domain: planning
type: artifact              # what kind of answer this contains
topics: [...]               # retrieval keywords
synonyms: [...]             # alternative phrasings
source_count: 7
sources: [S119, S024, ...]  # resolvable in SOURCES.md
evidence_type: professional-practice
confidence: high            # high | medium | low
corpus_origin: true         # derived from the original corpus
external_research: false    # true if it draws on [Ennn] sources
last_reviewed: 2026-09-16
---
```

**Documents touched by Phase-2 research carry three additional fields:**

```yaml
verified: true              # true | partial — was the external claim checked at its source?
phase: 2
provenance:                 # WHICH PROVENANCE LEVEL each source supplies for THIS document
  primary: [E001]           #   what the original creator/standard says
  interpretation: [S022]    #   what a later reading says
  practice: [E012]          #   what is considered current practice
  empirical: [E006]         #   what has actually been measured
```

> **The `provenance` block is the most important retrieval filter added in Phase 2.** A question
> like *"what does Scrum say about X"* should be answered from `provenance.primary`. A question like
> *"does this work"* should be answered from `provenance.empirical` — **and if that list is empty,
> the honest answer is that this knowledge base does not know.**

### Body — a consistent contract

| Section | What it gives you |
|---|---|
| **Definition** | What the thing is, quoted or closely paraphrased from sources |
| **Substantive sections** | Each heading answers one specific question |
| **Decision considerations** | When to use it, when not to — kept separate from definitions |
| **Limitations** | **Always present.** What the sources do not establish, and what the corpus lacks |
| **Related concepts** | Cross-references for retrieval expansion |
| **Sources** | A table mapping each `[Snnn]` to what it was used for |

### The conventions that carry meaning

| Marker | Means |
|---|---|
| `[S042]` | A **corpus** source citation — resolve in [SOURCES.md](SOURCES.md) |
| `[E006]` | An **external, Phase-2** source citation — separate register in the same file |
| **[INFERENCE]** | A conclusion drawn across sources that were not designed to support it — **weaker than [SYNTHESIS]** |
| **[EMPIRICAL: ...]** | An explicit statement of what has or has not been measured |
| `UNVERIFIED` / `VENDOR PROJECTION` | A claim preserved with its provenance, **not for citation as evidence** |
| **⚠** | A warning: disputed, unverified, stale, or a documented gap |
| **[CORPUS]** | A relationship a source states |
| **[SYNTHESIS]** | An inference this knowledge base draws — **no single source says it** |
| **[DISPUTED]** | Sources disagree; both positions given |
| `confidence: low` | Assembled from fragments — the document leads with a coverage warning |
| "**Do not cite**" | An unverified figure reproduced for transparency, not for use |

> **A blockquote beginning with a bolded phrase** (e.g. "> **The reusable principle:**") is
> commentary added by this knowledge base, not by a source. It is always adjacent to the sourced
> material it interprets.

---

## Using this for RAG

The structure was designed for retrieval. Concretely:

### Chunking
**Chunk at `##` and `###` headings.** Each section is written to answer one question and to be
intelligible without the rest of the document. Prepend the document title and `domain` to each chunk
so that a retrieved section carries its context.

Documents are deliberately sized to a single concept — the largest is ~3,500 words, most are
1,500–2,500 — so that retrieving a whole document is viable when a section is not enough.

### Metadata filtering
Frontmatter supports filtering on `domain`, `type`, `confidence` and `evidence_type`.

> **`confidence` and `evidence_type` are the important ones.** An agent answering a question that
> demands rigour should prefer `evidence_type: empirical-survey | standards-aligned |
> primary-text-quoted | academically-referenced` and should treat `confidence: low` documents as
> *maps of what is missing*, not as answers.

### Hybrid search
`topics` and `synonyms` exist so lexical retrieval reaches documents whose titles do not match the
query. [INDEX.md](INDEX.md) provides 633 term → document mappings for direct resolution.

### Retrieval expansion
`## Related concepts` gives curated expansion targets. [CONCEPT_GRAPH.md](CONCEPT_GRAPH.md) gives
reasoning chains for multi-hop questions — see its worked example for
*"roadmap for an unvalidated problem with technical constraints."*

### Reranking
Prefer, in order: **(1)** `evidence_type` rigour, **(2)** `confidence`, **(3)** source **Tier** in
[SOURCES.md](SOURCES.md), **(4)** section specificity.

---

## Rules for an agent using this knowledge base

1. **Cite the source ID.** If a claim carries `[Snnn]`, pass it through. Traceability is the point.
2. **Never state a ⚠ item as settled.** Give both positions and say they differ.
3. **Never cite a figure marked "do not cite."** They are reproduced so the corpus's claims are
   visible, not so they can be repeated.
4. **Where a document says something is a gap, say so.** "This knowledge base does not cover X" is a
   correct and useful answer. It is better than an answer assembled from three passing mentions.
5. **Gap rules, updated at v1.1.0:**
   - **Scrum and Kanban** — ✅ now answerable, **from the primary texts**
     ([scrum.md](07-execution/scrum.md), [kanban.md](07-execution/kanban.md)). Say which text.
   - **Estimation** — 🟨 answerable for *what the frameworks prescribe* (nothing) and for
     *probabilistic forecasting*. **Not** answerable for story points, velocity or planning poker.
   - **AI agents as team members** — 🟨 answerable for the evidence, specification practice and
     evaluation. **Not** answerable for how to organise a multi-agent team.
   - **MVP and metrics design** — ❌ still gaps. Do not answer from here.
   - See [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) §1 for the current status of each.
6. **Distinguish the four provenance levels in the answer**, not just in the metadata: what the
   *creator* said · what a *later interpretation* says · what is *current practice* · what has been
   *measured*. Conflating them is the most likely way to mislead a user in this knowledge base.
7. **Never present perceived productivity as measured productivity.** [E006] measured the two
   pointing in opposite directions. This generalises well beyond AI tooling.
8. **Where an external source has been qualified by its own authors, say so.** [E006] is the
   standing example — see [evidence-on-ai-assisted-delivery.md](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md).
9. **Treat ownership questions as organization-specific.** [S064] provides measured evidence that
   practitioners disagree about who owns discovery, research and the roadmap. Surface the ambiguity;
   do not resolve it by assertion.
10. **Distinguish what is from what to do.** Documents separate *Definition* from *Common practice*
   from *Decision considerations* deliberately. Preserve that distinction in answers.

---

## What this knowledge base is good at, and weak at

**Strong:** discovery and user research (NN/g) · roadmaps · prioritization · risk (PMI-aligned) ·
user stories (Mike Cohn) · role boundaries (survey evidence) · **Scrum and Kanban from their primary
texts** · **and knowing what it does not know.**

**Partial:** estimation (method yes, mechanics no) · **working with AI agents** (evidence and
specification practice yes; team organisation no).

**Weak:** metrics and measurement design · MVP · product-market fit · pricing · technical debt ·
scaling frameworks · **accessibility** (absent entirely).

Full assessment in [CORPUS_AUDIT.md](CORPUS_AUDIT.md) §4.

---

## Provenance

Built from `~/Downloads/PM-carrer/` — 143 browser-printed PDFs, 1,645 pages, ~344,700 extracted
words, captured up to September 2026.

**Phase 2** added **14 external sources** (`[E001]`–`[E014]`), retrieved deliberately against named
gaps — primary texts (the Scrum Guide, the Agile principles, the Kanban Method, EARS), empirical
studies (METR's RCT, DORA's survey) and tool documentation.

**Corpus-derived and researched content never blend silently.** Four mechanisms enforce it:

1. **Separate citation prefix** — `[Snnn]` vs `[Ennn]` — visible at the point of use
2. **Separate register** in [SOURCES.md](SOURCES.md), each external source carrying a provenance
   code and reliability tier
3. **Frontmatter flags** — `corpus_origin`, `external_research`, `verified`, `phase`
4. **A `provenance` block** typing each source by what it supplies: creator · interpretation ·
   practice · empirical evidence

**No content anywhere in this knowledge base comes from the model's own memory.** Where a fact was
needed and could not be retrieved from a source, it is recorded as a gap rather than supplied. Level-4
sources (blogs, forums, vendor comparison articles) were used only to **discover** which primary
sources exist, and **none is cited as authority**.

---

## Next

**Phase 2 continues.** In priority order: MVP (1.2) · product metrics and measurement design (1.3) ·
field reports on multi-agent team organisation (1.5, the project's central unanswered question) ·
Priority-2 gaps · accessibility.

See [CHANGELOG.md](CHANGELOG.md) for what v1.1.0 changed,
[RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) for current gap status, and
[CORPUS_AUDIT.md](CORPUS_AUDIT.md) §6.

The highest-value next action is cheap: **obtain the Scrum Guide and the twelve Agile principles.**
Together they close the single largest gap.
