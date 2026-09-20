# DISPUTED INFORMATION

Where sources in this corpus **contradict each other**, make **unverifiable claims**, or use the
same term to mean different things.

> **These were not resolved.** Forcing agreement between sources that genuinely disagree would
> destroy information. Each entry states the positions, what can be determined, and how an agent
> should handle it.
>
> **Phase 2 added §6**, where an external primary source **settles** a corpus disagreement or
> **contradicts** a corpus claim, and **§7**, where primary sources disagree with *each other*.
> Nothing was deleted: a corrected corpus claim is still recorded, with its correction beside it.

---

## 1. Direct contradictions between sources

### 1.1 Does a release plan carry dates?

| Position | Source |
|---|---|
| **Yes** — a release plan is "the execution-level plan of how you'll deliver the work that you've decided to do **and the timeframe when that work will be completed**" | [S035] Productboard |
| **No** — "A release plan is a good way to plot these milestones at a high level **without committing to a particular timeframe**" | [S076] Productboard |

**Note:** *both statements come from the same publisher.*

**Handling:** establish which sense is meant before acting. The difference is between a **schedule**
and a **sequence**. → [release-planning.md](../05-planning/release-planning.md)

---

### 1.2 Does the roadmap draw from the backlog, or filter it?

| Position | Source |
|---|---|
| The roadmap **draws from** the backlog: "dive into the backlog and see which items match up with those larger themes" | [S119] ProductPlan |
| The outcome **filters** the backlog: "Start by removing any backlog items which are not required to create the desired outcome. Delete or archive them" | [S040] Roman Pichler |

**Handling:** both are real working models serving different situations. → [CONCEPT_GRAPH.md §2](../CONCEPT_GRAPH.md)

---

### 1.3 How many stages does the product lifecycle have?

| Position | Source |
|---|---|
| **Six** — product development, introduction, growth, maturity, **saturation**, decline | [S072] Aha! |
| **Four/five** — introduction, growth, maturity, decline | [S071] |
| Unnamed progression — pre-launch, growth, retention, decline, end-of-life | [S118] ProductPlan |

[S072] acknowledges the dispute: *"Some people lump saturation in with maturity. But there are
subtle differences that present unique challenges."*

**Handling:** the **saturation** distinction is analytically useful (growth stopped, decline hasn't
started, incremental work has stopped returning) and is retained with the disagreement noted. →
[product-lifecycle.md](../11-lifecycle-and-launch/product-lifecycle.md)

---

### 1.4 Is an epic a large story, or a distinct tier?

| Position | Source |
|---|---|
| "An epic is **a large story**... it should be split into smaller stories" | [S127] Mountain Goat Software (Mike Cohn) |
| "Epics are large work items broken down into a set of stories, and **multiple epics comprise an initiative**" | [S126] Atlassian |

**Handling:** [S127]'s model is a working discipline; [S126]'s is a tooling hierarchy. They coexist,
but "epic" means different things in each. → [epics-and-decomposition.md](../06-requirements/epics-and-decomposition.md)

---

### 1.5 Is the PRD obsolete?

| Position | Source |
|---|---|
| "**Almost every product manager today considers PRDs to be passé**" — then argues they are essential | [S086] Aha! (states both) |
| "Crucial in **both** traditional methodologies like waterfall and agile environments" | [S085] Reforge |
| Neither — redefine it: "Agile PRDs focus on shared understanding... **avoiding overly detailed specs**" | [S138] Atlassian |
| Associated with waterfall: "typically used more in waterfall environments... **but may be used in an agile setting as well**" | [S084] ProductPlan |

**Complication:** all four publishers sell documentation tooling.

**Handling:** the sources are not describing the same artefact. A 30-page specification and a
one-page Confluence landing page share a name and little else. → [prd.md](../06-requirements/prd.md)

---

### 1.6 Is strategic thinking what separates a PM from a product owner?

| Position | Source |
|---|---|
| Yes — "a skill that **separates** the role of a product manager from the role of a product owner" | [S006] Institute of Product Leadership |
| Not established — [S064]'s survey found UX professionals **could not reliably distinguish** PM from PO responsibilities for vision and prioritization | [S064] NN/g (n=372) |

**Handling:** [S006] is an unsupported claim from a training provider; [S064] is measured
disagreement. **Prefer [S064].** → [product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)

---

### 1.7 Does an OKR key result measure outputs?

| Position | Source |
|---|---|
| **No** — "Measuring outputs or feature completions instead of outcomes" is listed as a **mistake** | [S080] Product School |
| **Sometimes yes** — the LinkedIn example uses "an **output-oriented** metric to launch the product by July 31" alongside outcome KRs | [S007] Reforge |
| **Explicitly yes** — NCTs legitimise **deliverable commitments** ("launch new onboarding flow by September 2019") precisely because ambiguous work needs them | [S007] Reforge |

**Handling:** this is a real methodological disagreement, and NCTs exist *because* of it.
→ [okrs.md](../04-strategy/okrs.md) · [product-goals.md](../04-strategy/product-goals.md)

---

## 2. Same term, different meanings

### 2.1 "North Star" means at least three things

| Meaning | Source |
|---|---|
| **The product vision** — "A good product vision serves as the North Star for the product organization" | [S094] Cagan |
| **A metric** — "your roadmap should be fully reflective of that [metric]... draw a clear line from each item to how it directly impacts the North Star" | [S003], [S108] |
| **A product principle** — "Basecamp's Product North Star: **make project management more of a joy and less of a chore**" — which is **not measurable as stated** | [S080] |

**Handling:** ask which is meant. → [north-star-metric.md](../09-metrics/north-star-metric.md)

---

### 2.2 "Definition of Done" is used for acceptance criteria

[S126] and [S128] both use "definition of done" to mean **story-level acceptance criteria**. In
common agile practice, the Definition of Done is a **team-wide standard** applying to every item.

**The corpus never makes this distinction.**

> ✅ **Superseded by [§6.1](#61-definition-of-done--the-corpus-uses-the-term-incorrectly).** Phase-2
> research settled it from two primary texts, which agree independently: the Definition of Done is an
> **Increment/team-level standing standard** ([E001]) and an **explicit policy** ([E003]), not
> item-level acceptance criteria. The corpus usage is preserved here as a record of what these
> sources told their readers. → [acceptance-criteria.md](../06-requirements/acceptance-criteria.md)

---

### 2.3 "Indirect competitor" vs "substitute"

| Position | Source |
|---|---|
| **Three categories** — direct, indirect, and **substitutes / "do nothing"** treated separately | [S025] |
| **Two categories** — substitutes folded into indirect: *"Indirect competitors (spreadsheets, Notion)"* | [S079] |

**Handling:** [S025]'s three-way split is more useful because non-consumption behaves differently
from an adjacent product. → [competitive-analysis.md](../03-market-intelligence/competitive-analysis.md)

---

### 2.4 "Discovery" — a phase or a continuous practice

[S028] frames discovery as a **bounded phase** converging on a problem statement. [S110] frames it
as **continuous opportunity validation** running alongside delivery.

**Handling:** clarify before answering. → [product-discovery.md](../02-discovery/product-discovery.md)

---

## 3. Internal inconsistencies within a single source

### 3.1 The opportunity-scoring formula — [S066] gives two

> "Here's the weighted equation: `Importance + Max(Importance − Satisfaction, 0) = Opportunity`"
>
> "Here is the opportunity algorithm formula: `Importance + (Importance − Satisfaction) = Opportunity`"

**These are not the same.** The first floors the gap at zero; the second permits a negative
contribution. [S066] presents both without acknowledging the difference.

**What can be determined:** the first form is consistent with the stated intent ("high importance
combined with low satisfaction marks the highest-priority opportunity") — **but this is an
inference.** Verify against Ulwick's own work before relying on either.
→ [prioritization-frameworks.md](../05-planning/prioritization-frameworks.md)

---

### 3.2 [S093] — "product vision examples" that are mission statements

[S093] is titled *10 Great Product Vision Examples* and lists corporate slogans: Zoom — "To make
video communication frictionless"; Shopify — "To make commerce better for everyone"; Stripe — "To
grow the GDP of the internet."

**By [S094]'s criteria these are mission statements**, which is exactly the confusion Cagan's article
exists to correct. The corpus therefore contains a live instance of the error it also documents.

**Handling:** useful as **mission** statement examples. Do not use as product-vision templates.
→ [product-vision.md](../04-strategy/product-vision.md)

---

### 3.3 [S048] — success metrics defined as project metrics

[S048]'s step 7, "Set metrics for success," states: *"The metrics you set in this step will usually
be **due dates and productivity levels**, which you can track with systems like Kanban boards, Gantt
charts, or burndown charts."*

This contradicts [S085], [S113] and [S086], where PRD success metrics are **product outcomes**
(engagement, retention, conversion, revenue).

**Handling:** treat [S048]'s step 7 as an **error**, not an alternative view. [S048] is written by a
marketing writer, not a product practitioner. → [prd.md](../06-requirements/prd.md)

---

### 3.4 [S072] — the 1968/1969 date discrepancy *(brainwriting: [S010])*

[S010] states 6-3-5 was published "in a German sales magazine, the *Absatzwirtschaft*, in **1968**,"
while its own reference list cites **Rohrbach, Bernd (1969)**. **Unresolvable from the corpus.**
→ [brainwriting.md](../08-ideation/brainwriting.md)

---

## 4. Unverified claims — do not cite

Reproduced because removing them would hide what the corpus asserts. **None should be repeated as
fact.**

| Claim | Source | Problem |
|---|---|---|
| "**More than 90% of unhappy customers never complain**" | S009 | No source given |
| "Poor customer experiences cost businesses up to **$3.8 trillion globally**. (Decisions Studio)" | S009 | Unidentifiable attribution; no year or method |
| "Only **6.4% of features** drive 80% of click volume" (Pendo 2024 benchmark) | S031 | Vendor-reported, load-bearing for the article's whole argument |
| 2024 DORA figures — AI adoption without small-batch discipline drops throughput ~1.5% and stability ~7.2% | S031 | Second-hand; DORA report not in corpus |
| Gartner: "**over 40% of agentic AI projects will be canceled by the end of 2027**" | S031 | A prediction, cited second-hand |
| "There are almost **9 billion** apps worldwide" | S021 | **Implausible as stated**; likely conflates downloads with apps |
| "**Google allocates 20%** of its time to R&D. Google Maps and Google Chat came out of this!" | S042 | Widely contested industry lore; no source |
| LinkedIn "saw company **revenue increase by 45%** that year" after Sales Navigator, attributed partly to OKR use | S007 | No source; company-wide revenue cannot be attributed to one team's goal framework |
| "**40%** answering 'very disappointed' = product-market fit" | S005 | Named originator (Sean Ellis) and a book citation, but **no primary evidence for the threshold** |
| **DSDM's "60% Must cap"** with ~20% reserved for Coulds | S031 | Specific and checkable, but DSDM documentation is not in the corpus |
| Product management originated at **P&G in the early 1930s** as "brand management" | S132 | Single source, no citation |
| "Research suggests that **higher empathy towards users leads to stronger financial performance**" | S045 | No study named; causal direction asserted |
| "**99% of UX researchers** run surveys at least sometimes" (NN/g 2019) | S105 | Self-reported within NN/g's own respondent pool; not a population estimate |
| ProductPlan 2022 survey: **62%** use live meetings, **11%** refer to the roadmap, **45%** would host a meeting | S116 | Vendor's own survey; sample size and method not stated |
| Adidas, Netflix/McCracken and screwdriver-indentation ethnography cases | S045 | Recounted without company sources |
| Christensen's **milkshake** study | S054 | No primary account of method or sample |
| **Kodak** as the canonical decline case | S071 | Industry lore, no analysis |
| Basecamp and Intercom JTBD outcomes | S054 | Author's account; one conclusion explicitly hedged as "likely inspired" |
| **NIST SP 800-30** published 2002, updated 2012; **WEF Cyber Risk Model** 2015 with Deloitte | S050 | Second-hand dates from a 2026 vendor article; may be superseded |

---

## 5. Claims flagged as advocacy

Substantive, but argued by a party with an interest.

| Claim | Source | Interest |
|---|---|---|
| "OKRs are corporate and full of jargon. **OKRs don't really matter to people like dreams matter to them**" | S007, quoting Jonatan Littke | Littke created Dream Maps |
| "Today's forward-thinking product teams focus on delivering a **Minimum Lovable Product (MLP)**" | S072 | MLP is Aha!'s own term; **MVP is never defined in the corpus, and MLP is never defined either** |
| "**Agile is a cultural value**, and teams should be empowered to work how they best see fit" | S022 | Atlassian sells agile tooling and says so explicitly — **the disclosure is why the claim is still usable** |
| "Job stories are often **preferred** in product development, as they lead to more effective and relevant solutions" | S053 | Sells JTBD workshop materials. [S052] — by a user-story authority — makes only a **conditional** claim |
| "**AI is not meant to create the strategy outright**... Only you as a product manager have the judgment" | S090 | Vendor of PM software, reassuring its audience |
| Purpose-built roadmapping software is necessary; spreadsheets and decks are "a nightmare to maintain" | S119, S116, S024 | Roadmapping vendors |
| "Effective positioning makes it possible to craft meaningful messages" → use our positioning feature | S083 | Vendor |
| "**Everyone is a UXer**" mentality is "disrespectful" | S064, quoting a respondent | A UX respondent in a UX-organisation survey. **The quotation is data about sentiment, not a finding** |

---

## 6. Settled in Phase 2 by an external primary source

> These are the cases where retrieving the primary text produced an answer. **The corpus statement is
> preserved and marked, not removed** — a source that was wrong is still evidence of what a widely
> read vendor guide told its readers.

### 6.1 "Definition of done" — the corpus uses the term incorrectly

| Position | Source |
|---|---|
| Definition of done is **story-level**: "the story is generally 'done' when the user can complete the outlined task" | [S126] Atlassian |
| Definition of done is **story-level**: "decide what 'done' will look like" as step 1 of writing a user story | [S128] ProductPlan |
| **Definition of Done is a commitment attached to the Increment** — *"a formal description of the state of the Increment when it meets the quality measures required for the product"*; **work is not part of an Increment unless it meets it** | **[E001] The Scrum Guide, 2020 — primary** |
| Definition of Done is **one kind of explicit policy**, alongside WIP limits and replenishment policies | **[E003] Essential Kanban Condensed, 2016 — primary** |

**Resolution:** the two primary texts agree, independently. The Definition of Done is a **team- or
product-level standing standard**; acceptance criteria are **item-level**. They are complementary.

**Handling:** answer from the primary texts. If asked what [S126] or [S128] say, report their usage
**and** that it conflicts with both primary sources.
→ [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md) ·
[../07-execution/scrum.md](../07-execution/scrum.md)

---

### 6.2 Who is accountable for the product backlog?

| Position | Source |
|---|---|
| Practitioners **do not agree**; PMs and UX professionals gave conflicting answers | [S064] NN/g, n=372 |
| **The Product Owner is accountable** for the Product Backlog — and is *"one person, not a committee"* | **[E001] — primary** |

**Resolution:** **settled for teams running Scrum.** [E001] also does **not** require the Product
Owner to personally author items, which confirms [S127]'s distinction between accountability and
authorship.

**Limit of the resolution:** it applies to Scrum teams. It says nothing about teams not running
Scrum, and [E001] never mentions the product manager role at all.
→ [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)

---

### 6.3 "Kanban roadmap" / "Kanban board" — a category error

| Position | Source |
|---|---|
| A **Kanban roadmap** is a roadmap format that "visualizes progress using columns like Backlog, In Progress, and Done, similar to a Kanban board" | [S130] Product School |
| **Kanban boards** are a tracking tool alongside Gantt and burndown charts | [S048] Notion |
| **"For it to be a kanban system rather than simply a flow system, the commitment and delivery points must be defined, and WiP Limits must be displayed."** The Kanban Method is a **management method**, not a board | **[E003] — primary** |

**Resolution:** a Backlog/In-Progress/Done board without WIP limits is a **flow visualisation**, not
a kanban system, and not the Kanban Method. The corpus's usage reflects common industry shorthand.

**Handling:** do not correct a user who says "kanban board" meaning a board — that usage is
universal. **Do** distinguish it when the question is about the method, WIP limits, pull systems or
flow.
→ [../07-execution/kanban.md](../07-execution/kanban.md) ·
[../05-planning/roadmap-formats.md](../05-planning/roadmap-formats.md)

---

### 6.4 Are story points, velocity and planning poker part of Scrum?

| Position | Source |
|---|---|
| Implied to be standard Scrum sprint-planning practice: teams "use t-shirt sizes, the Fibonacci sequence, or planning poker" | [S126] Atlassian |
| **[E001] contains no estimation technique of any kind** — no story points, no velocity, no planning poker | **[E001] — primary** |

**Resolution:** these are **community conventions layered on Scrum**, not Scrum rules. [E001] leaves
the method to the Developers.

**Handling:** never state that Scrum requires story points or velocity.
→ [../05-planning/estimation.md](../05-planning/estimation.md)

---

## 7. Disagreements *between* primary sources — not resolvable

> **These are the important ones.** Two authoritative texts disagree. There is no higher source to
> appeal to, and picking one would destroy information.

### 7.1 Product Manager vs Product Owner — a three-way split

| Position | Source | Provenance |
|---|---|---|
| **Product Owner** is a defined accountability inside Scrum. **"Product manager" does not appear in the Guide at all** | [E001] Scrum Guide 2020 | Primary — framework originators |
| **Service Request Manager** — and *"alternative names for the role are **Product Manager, Product Owner**, and Service Manager."* One function, several names. *"There are no required roles in Kanban"* | [E003] Kanban Method | Primary — method originator |
| **Two different roles at different altitudes** — PM strategic, PO tactical and embedded in the team | [S078], [S118], [S006] | Vendor / training guides |
| Practitioners **do not agree** in the field | [S064] | Empirical, n=372 |

**Why this is not an error to fix:** the sources are answering different questions — a framework
accountability, an observed organisational function, and a job-market distinction. **[E003]
explicitly disagrees with the corpus**, not merely differs from it.

**Handling:** state which frame the answer is in. Never assert a single universal difference.
→ [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)

---

### 7.2 Revolutionary versus evolutionary adoption

| Position | Source |
|---|---|
| **"The Scrum framework... is immutable. While implementing only parts of Scrum is possible, the result is not Scrum."** | [E001] |
| **"Start with what you do now"** — understand current processes *as actually practised*, **respect existing roles, responsibilities and job titles**, and improve through **evolutionary change**. Kanban *"should be applied to an existing process or way of working"* | [E003], [E004] |

**Why this is not resolvable:** these are **opposing theories of organisational change**, both stated
by the originators of their respective methods, both internally coherent.

**Handling:** present it as a genuine choice — adopt a defined target state, or improve from the
current one — not as one method being more correct.
→ [../07-execution/scrum.md](../07-execution/scrum.md) · [../07-execution/kanban.md](../07-execution/kanban.md)

---

### 7.3 Perceived productivity gain from AI versus measured productivity

| Position | Source |
|---|---|
| **More than 80%** of ~5,000 respondents believe AI has increased their productivity | [E008] DORA 2025 |
| Developers estimated AI made them **20% faster** after a study in which it measurably made them **19% slower** | [E006] METR RCT, July 2025 |

**These are not contradictory findings — they are different quantities.** [E008] measured *belief*;
[E006] measured *time*. The error is treating the first as evidence for the second.

**Further complication:** METR's own authors [E007] now believe developers are *"likely"* more sped
up in early 2026 than their 2025 estimate, while stating their newer data is *"only very weak
evidence for the size of this increase."*

**Handling:** never cite "19% slower" as a general fact; reproduce its scope conditions. Never cite
perceived productivity as measured productivity.
→ [../13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md](../13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)

---

### 7.4 How much specification should precede implementation?

| Position | Source |
|---|---|
| **"Working software over comprehensive documentation"**; principle 6 names **face-to-face conversation** as the most efficient method of conveying information | [E002] Agile Manifesto, 2001 |
| Corpus consensus: requirements should be **"informative-but-brief"** | [S086], [S138] |
| **"Define what and why before deciding how to build it"** — the specification, not the code, is the source of truth | [E012] GitHub spec-kit |

**Why it is open:** [E002] was written in 2001 for co-located human teams and assumes the
conversational channel exists. SDD's premise is that with an agent implementer it does not. **Neither
position has been tested against the other**; no controlled comparison exists.

**Handling:** present as an open question conditioned on who implements.
→ [../13-ai-agent-collaboration/spec-driven-development.md](../13-ai-agent-collaboration/spec-driven-development.md) ·
[../13-ai-agent-collaboration/open-questions-ai-and-pm.md](../13-ai-agent-collaboration/open-questions-ai-and-pm.md)

---

### 7.5 DORA's AI ROI figures

| Claim | Source | Status |
|---|---|---|
| A modelled 500-person engineering org yields ~**$11.6M first-year value against $8.4M investment (39% ROI, 8-month payback)**; Google Cloud data shows an average **727% return over three years** | [E009] via [E010] | **`UNVERIFIED — VENDOR PROJECTION`** |

**Modelled projections published by a company selling AI development tooling and cloud services,
reaching this knowledge base through a secondary news source.** The full report was not read.

**Handling:** **do not cite as evidence that AI adoption pays off.** Recorded here, per the rule on
preserving claims with provenance rather than deleting inconvenient ones.

---

## 8. How an agent should handle these

1. **Never state a disputed item as settled.** Say that sources differ, and give both.
2. **Never cite a §4 claim as fact.** If it must be mentioned, attribute it and flag it as
   unverified.
3. **Prefer the higher-tier source** when positions conflict — see [SOURCES.md](../SOURCES.md).
4. **When a term is ambiguous (§2), ask which sense is meant** before answering.
5. **Treat §3.3 and §3.2 as errors**, not alternatives — those are cases where the corpus is simply
   wrong by its own standards.
6. **For §6, answer from the primary source** and say the corpus source differs. Do not silently
   present the corrected version as what the corpus said.
7. **For §7, never pick a side.** These are disagreements between authorities. Name the frame the
   question is being asked in, give both positions with their provenance, and say what would settle
   it if anything would.
8. **Tier and provenance are not truth.** A primary source is more *traceable*, not automatically
   more correct — and on questions its author never addressed, it is not a source at all.

---

## Related

- [SOURCES.md](../SOURCES.md) — reliability tiers
- [outdated-information.md](outdated-information.md) — claims that expire rather than conflict
- [excluded-content.md](excluded-content.md) — what was removed
- [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md) — verifying these is priority work
