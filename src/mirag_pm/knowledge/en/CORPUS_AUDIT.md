# CORPUS AUDIT

The audit performed before any transformation, and the record of what was done to the corpus.

**Audit date:** 16 September 2026 · **Corpus location:** `~/Downloads/PM-carrer/`

---

## 1. The original corpus

### 1.1 Composition

| | |
|---|---|
| **Files** | **143** — all `.pdf` |
| **Format** | Browser "print to PDF" captures of web articles. **No books, papers, standards documents or original files.** |
| **Structure** | A single flat directory. No subfolders, no naming convention, no metadata |
| **Disk size** | 469 MB (inflated by embedded images; text is ~2 MB) |
| **Pages** | **1,645** |
| **Extracted words** | **~344,700** |
| **Languages** | English (140) · Spanish (3 — S014 Asana, S055 Riskonnect, S143 GTM guide) |
| **Distinct publishers** | ~60 |
| **Date range** | Where determinable: **2013–2026**. **Only 35 of 143 carry a determinable date** |

### 1.2 Size distribution

Highly uneven. The largest file (38 MB, S071) and the smallest (40 KB, S027) differ by three orders
of magnitude, driven almost entirely by embedded imagery rather than content.

| Extracted words | Files |
|---|---|
| Under 500 (stubs) | 7 |
| 500–1,500 | 24 |
| 1,500–3,000 | 62 |
| 3,000–5,000 | 33 |
| Over 5,000 | 17 |

### 1.3 Publisher concentration

**Roughly 85% of the corpus is commercially motivated content** — vendor marketing, training-provider
lead generation, or agency content marketing.

| Publisher | Files | Nature |
|---|---|---|
| Product School | ~20 | Training provider; certification promotion throughout |
| ProductPlan | ~12 | Roadmapping software vendor |
| **Nielsen Norman Group** | ~11 | **UX research organisation — the corpus's evidential core** |
| Aha! | ~8 | PM software vendor |
| Mind the Product | ~7 | Practitioner community (Pendo) |
| Atlassian | ~6 | Software vendor |
| Mitti / SafetyCulture | ~6 | Safety & GRC vendor |
| Productboard | ~5 | PM software vendor |
| Miro / Mural | ~5 | Collaboration vendors |
| **Project Management Academy** | 4 | **PMI Authorized Training Partner — the standards-aligned core** |
| Reforge | 4 | Practitioner education, named contributors |
| IxDF | 4 | Design education (2 usable, 2 stubs) |
| **Mountain Goat Software** | 2 | **Mike Cohn — primary authority on user stories** |
| ~45 others | 1–3 each | Mixed |

---

## 2. Audit findings

Each of the thirteen questions the audit was asked to answer.

### 2.1 What files exist
143 PDFs, listed in full in [SOURCES.md](SOURCES.md) with IDs S001–S143.

### 2.2 What each file contains
Every file was extracted, profiled (title, date, headings, word count) and read in the domain pass.
**No file was assessed from its filename alone.**

### 2.3 Topics covered
Thirteen clusters emerged, which became the domain structure:

| Cluster | Files |
|---|---|
| PM role, skills, career | 17 |
| Roadmaps | 15 |
| Discovery & user research | 13 |
| Risk | 12 |
| Lifecycle, launch & GTM | 12 |
| Ideation & creativity | 11 |
| Strategy, vision, goals | 11 |
| Requirements (PRD, stories) | 11 |
| Market & competitive intelligence | 9 |
| UX & design | 8 |
| Execution & collaboration | 6 |
| Value & positioning | 6 |
| Metrics | 2 |

### 2.4 Duplicates and partial duplicates
**Substantial redundancy.** The largest overlaps:

| Topic | Files | Handling |
|---|---|---|
| Roadmaps | 15 sources covering heavily overlapping ground | **Consolidated into 6 documents** split by *question answered* (definition, formats, outcome-based, continuous, communication, vs-backlog) rather than by source. Distinct perspectives preserved — Pichler's transition process, Cutler's continuous model, and the format taxonomy are genuinely different contributions |
| Risk | 12 sources, 6 of them generic GRC vendor content | Consolidated into 8 documents; PMI-aligned sources given precedence; safety/GRC framing retained only where it added the "best used for" mapping |
| Brainstorming | 11 sources, heavily overlapping technique lists | Consolidated into 5; the academically-referenced 6-3-5 source given its own document |
| PRD | 6 sources | 1 document, preserving the obsolescence debate between them |
| Market research | 9 sources | 4 documents |
| **Full duplicates** | **S055** (Spanish risk tips ≈ S125/S100) · **S139** (Planview agile roadmap ≈ S130) | Read, found to add nothing, recorded in [excluded-content.md](99-reference/excluded-content.md) |

### 2.5 Relevant documents
**136 of 143 are relevant** to product or project management. Two are relevant but redundant; five
are not usable (see 2.6).

### 2.6 Primarily commercial documents
Every Product School, ProductPlan, Aha!, Atlassian, Productboard, Miro, Mural, Maze and Mitti source
carries commercial framing. **Five are commercial to the point of having no extractable knowledge:**

- **S002** — tool comparison with pricing, led by the publisher's own product
- **S120** — link farm to the publisher's other content and certifications
- **S121** — announcement of four other articles
- **S069** — extraction stub (TOC + course panel only)
- **S027** — out of domain entirely (Stellar blockchain; appears misfiled from another project)

### 2.7 Documents containing opinion
Roughly 20 sources are primarily one practitioner's position. **These were kept and labelled**, not
removed — e.g. Littke on Dream Maps, Cohn's stated preference for modified user stories, Cagan's
feature-team qualifier, Atlassian's "agile is a cultural value." Each is marked as advocacy in
[disputed-information.md](99-reference/disputed-information.md) §5.

### 2.8 Documents containing factual information
**Genuinely factual content is scarce.** The corpus contains:

- **1 primary text** reproduced verbatim (the Agile Manifesto, S022)
- **1 empirical survey** with stated method and significance testing (S064, n=372)
- **1 document with peer-reviewed citations** (S010)
- **4 standards-aligned documents** quoting PMI definitions (S043, S051, S065, S100)
- **~11 research-organisation documents** (NN/g) that are method-based rather than assertion-based
- **1 dated citation to an HBR article** (S072 → Levitt 1965)

Everything else is professional assertion. This is recorded in the **Tier** column of
[SOURCES.md](SOURCES.md).

### 2.9 Potentially outdated documents
**35 sources carry determinable dates; 108 do not.** Specific staleness is catalogued in
[outdated-information.md](99-reference/outdated-information.md) — including five sources whose
*titles* promise a year later than their actual update date.

### 2.10 Documents too superficial
**Seven extraction stubs** under 500 words: S002, S013, S069, S102, S121, S135, S137. Of these,
S013, S102, S135 and S137 still contained a usable definition and were cited for that alone;
S002, S069 and S121 were excluded.

**A further ten sources were substantially truncated** by the PDF capture: S017, S015, S033, S037,
S083, S091, S104, S112, S123, S134. Each affected knowledge-base document records what was lost.

### 2.11 Documents with content worth preserving
**All 138 cited sources.** The highest-value, by tier: the NN/g research corpus, the PMI-aligned risk
material, Mountain Goat Software on stories, the Agile Manifesto text, Cagan on vision, Pichler on
outcome roadmaps, Mehta on decisions, Reforge on specializations, and the Wikipedia 6-3-5 article.

### 2.12 Important topics appearing repeatedly
Roadmaps · prioritization · discovery · user research · risk · PM role · requirements · stakeholder
alignment · outcomes-over-outputs · competitive analysis. **The corpus's strengths.**

### 2.13 Important topics absent
**The corpus's weaknesses**, in full in [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md):

Scrum/Kanban mechanics · MVP · metrics and measurement design · estimation · working with AI agents ·
product-market fit · pricing · technical debt · release planning · dependencies · WSJF · market
sizing · accessibility · use cases · story splitting patterns · personas · journey mapping.

> **This audit describes the corpus and is not revised by later work.** Some of the topics above are
> now covered in the knowledge base **from external sources** — they remain absent *from the corpus*,
> which is what this section records. Current coverage status is in
> [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) and [CHANGELOG.md](CHANGELOG.md).

---

## 3. What was done

### 3.1 Process

```
AUDIT      143 PDFs inventoried, profiled, clustered            (no transformation)
   ↓
EXTRACT    pdftotext -layout → 344,700 words
   ↓
CLASSIFY   domain assignment + reliability tier per source
   ↓
CLEAN      boilerplate removal → 319,400 words (−7.3%)
           ⚠ 9 over-trimmed files detected and restored
   ↓
DEDUPLICATE  overlapping sources consolidated by question, not by source
   ↓
ORGANIZE   12 domains derived from the corpus, not the template
   ↓
NORMALIZE  uniform frontmatter, section structure, source tables
   ↓
BUILD      81 documents, ~157,500 words
   ↓
INDEX      562 concept terms → documents
   ↓
TAXONOMY + CONCEPT GRAPH
   ↓
SOURCES    143-row register with per-document traceability
   ↓
GAPS       identified during writing, not guessed
   ↓
BACKLOG    RESEARCH_BACKLOG.md
   ↓
QA         link check · citation check · frontmatter check
```

### 3.2 Cleaning

| Step | Effect |
|---|---|
| Line-level boilerplate filter (nav, CTAs, cookie banners, footers, chat widgets, newsletter forms) | −2.8% of words |
| Footer-block truncation | −7.4% of remaining words |
| **Detected over-trimming** in 9 files (multi-column sidebar layouts) | **Restored from raw** |
| **Net** | 344,700 → **319,400 words** |

> The over-trim detection was a deliberate check: any file retaining under 65% of its raw words was
> re-examined. Nine were found (S006, S011, S017, S023, S083, S086, S091, S104, S121) and restored.
> Without it, four documents — including the entire Aha! PRD treatment — would have been built on
> 16% of their source.

### 3.3 Output

| | |
|---|---|
| **Documents** | **81** across 12 domains |
| **Words** | **~157,500** |
| **Root files** | 9 (README, INDEX, TAXONOMY, SOURCES, GLOSSARY, CONCEPT_GRAPH, RESEARCH_BACKLOG, CHANGELOG, CORPUS_AUDIT) |
| **Reference files** | 3 (excluded, disputed, outdated) |
| **Concept index entries** | **562** |
| **Sources cited** | **138 of 143** |

| Domain | Docs | Words |
|---|---|---|
| 01 Foundations | 7 | 9,900 |
| 02 Discovery | 11 | 18,600 |
| 03 Market Intelligence | 4 | 5,300 |
| 04 Strategy | 10 | 17,600 |
| 05 Planning | 12 | 20,800 |
| 06 Requirements | 7 | 14,300 |
| 07 Execution | 5 | 7,100 |
| 08 Ideation | 5 | 7,500 |
| 09 Metrics | 3 | 3,700 |
| 10 Risk | 8 | 12,000 |
| 11 Lifecycle & Launch | 5 | 6,700 |
| 12 Design & UX | 4 | 5,200 |

> **The corpus shrank from ~319,000 usable words to ~157,500.** That reduction is **redundancy
> removal, not information loss**: fifteen roadmap articles restating the same definition became one
> definition with fifteen traceable sources. Where sources genuinely differed, both positions were
> kept — which is why several documents are longer than any single source.

---

## 4. Quality assessment

### 4.1 What this knowledge base is good at

| Area | Why |
|---|---|
| **Discovery and user research** | NN/g's method-based material is the corpus's strongest content. Method selection, interview construction, survey misuse and usability-test validity are all well covered |
| **Roadmaps** | 15 sources consolidated, with genuine perspectives preserved (traditional, outcome-based, continuous) |
| **Prioritization** | Seven frameworks with stated strengths, weaknesses and fit conditions, plus the practice around them |
| **Risk** | The only standards-aligned material in the corpus; complete identify→assess→respond→monitor cycle |
| **User stories and requirements** | Mike Cohn's guide is a primary authority writing critically about his own technique |
| **Role boundaries** | The only measured evidence in the corpus (S064) |
| **Knowing what it does not know** | Every document states its limitations; gaps are documented rather than filled |

### 4.2 What it is weak at

| Area | Severity **in the corpus** | Knowledge-base status after Phase 2 |
|---|---|---|
| **Agile execution mechanics** (Scrum, Kanban, ceremonies) | 🔴 Critical | ✅ **Covered from primary texts** [E001]–[E004] |
| **Metrics and measurement** | 🔴 Critical | 🔴 **Still a gap** |
| **MVP** | 🔴 Critical | 🔴 **Still a gap** |
| **Estimation** | 🔴 Critical | 🟨 **Partial** — probabilistic forecasting [E003]; story points and velocity still absent |
| **Working with AI agents** | 🔴 Critical — and it is this project's purpose | 🟨 **Partial** — evidence, specification practice and evaluation covered; **multi-agent team organisation still has no source at all** |
| **Product-market fit** | 🟠 Significant | 🟠 Unchanged |
| **Pricing** | 🟠 Significant | 🟠 Unchanged |
| **Technical debt** | 🟠 Significant | 🟠 Unchanged |
| **Release planning, dependencies** | 🟠 Significant | 🟠 Unchanged |
| **Accessibility** | 🟠 Absent entirely | 🟠 **Still absent entirely** |

### 4.3 Contradictions found
**Seven direct contradictions** between sources, **four cases of one term meaning several things**,
and **four internal inconsistencies within single sources** — all catalogued in
[disputed-information.md](99-reference/disputed-information.md). None was resolved by choosing a
side; all are presented with both positions.

### 4.4 Ambiguous concepts
"North Star" (three meanings) · "Definition of Done" (used for acceptance criteria) · "discovery"
(phase vs practice) · "epic" (large story vs hierarchy tier) · "release plan" (with or without
dates) · "indirect competitor" (with or without substitutes) · "theme" (never defined).

### 4.5 Claims requiring external verification
**Seventeen unverified statistics and attributions** are reproduced with do-not-cite flags, plus
**fifteen verification tasks** in [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) §3.

---

## 5. Integrity checks

Applied per the project's rule that nothing be lost for brevity or convenience:

| Check | Result |
|---|---|
| Was anything removed only to save tokens? | **No.** Reductions were redundancy, boilerplate and promotion. Where two sources said different things, both were kept |
| Was model memory used to fill gaps? | **No.** Gaps are documented as gaps. Where a term is widely known but undefined in the corpus (MSPOT, V2MOM, WSJF, INVEST), this is stated and the term is left undefined |
| Was inference presented as fact? | **No.** Every synthesis is labelled `[SYNTHESIS]` or introduced with "this is a synthesis, not a corpus claim" |
| Was uncertainty hidden? | **No.** Every document has a Limitations section; low-confidence documents lead with a coverage warning |
| Were exceptions, limitations and trade-offs preserved? | **Yes, deliberately.** Framework documents preserve "when this does not work" wherever a source supplied it — e.g. outcome-based roadmaps' five stated drawbacks, brainwriting's four "when to avoid" conditions, opportunity assessment's four skip conditions |
| Were weak sources removed or labelled? | **Labelled.** S009, S141, S019 and others are cited with explicit reliability warnings rather than deleted |

---

## 6. Next steps

1. **Run phase 2** against [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md), starting with Priority 1.
2. **Acquire the primary sources** listed in [SOURCES.md](SOURCES.md) § *Primary sources referenced
   but NOT in the corpus* — particularly the Scrum Guide and the twelve Agile principles, which
   would close the largest gap cheaply.
3. **Verify the Priority 3 claims** — these are cheap, checkable, and several are load-bearing.
4. **Relocate S027** (`Cuentas y wallets en Stellar.pdf`) to the project it belongs to.
5. **Build the RAG pipeline.** The structure supports it: per-document frontmatter for metadata
   filtering, section-level headings for chunk boundaries, keywords for hybrid search, and
   cross-references for expansion. See [README.md](README.md).
6. **Re-verify time-sensitive content** on the cadence in
   [outdated-information.md](99-reference/outdated-information.md).

---

## Related

- [SOURCES.md](SOURCES.md) · [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) · [TAXONOMY.md](TAXONOMY.md)
- [99-reference/excluded-content.md](99-reference/excluded-content.md) · [99-reference/disputed-information.md](99-reference/disputed-information.md) · [99-reference/outdated-information.md](99-reference/outdated-information.md)
