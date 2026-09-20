# EXCLUDED CONTENT

What was removed from the corpus on the way to the knowledge base, and why.

> **Principle applied:** nothing was discarded silently. Content was excluded for **noise,
> commercial promotion, redundancy, or being out of domain** — never for brevity, and never because
> it was inconvenient. Where a whole source was excluded, it is named. Where a *category* of content
> was stripped across many sources, the category is described with examples.
>
> **What was NOT excluded:** substantive content that was inconvenient, contradictory, weakly
> sourced, or unflattering. Weak content was kept and **labelled** — see
> [disputed-information.md](disputed-information.md) and the Limitations section of every document.

---

## 1. Whole sources excluded

Five sources contribute nothing to the knowledge base.

| ID | Document | Reason | Detail |
|---|---|---|---|
| **S027** | *Cuentas y wallets en Stellar* | **OUT OF DOMAIN** | Technical documentation on Stellar blockchain accounts, Soroban identity contracts (standard 8004), Friendbot testnet funding and XLM payment flows between agents. Contains **no product-management content whatsoever.** Notably, it describes wallets for "Backend, QA, PM" *agents* in a multi-agent system — it appears to belong to a different project in the same working directory and was swept into the corpus by accident. **Recommendation: move it to the repository it belongs to; it is not waste, it is misfiled.** |
| **S120** | Product School — *The Ultimate Product Management Resources* | **LINK FARM** | A curated list of links to other Product School articles and certifications ("Learning The Ropes", "Get Certified as a Product Manager", "Define Your Product Manager Career Path"). No self-contained knowledge. |
| **S121** | Atlassian — *Tips for agile product management* (14 May 2015) | **PROMOTIONAL ANNOUNCEMENT** | Announces the publication of four other articles. Contains no knowledge itself: *"We've started with four articles from a few of Atlassian's product management experts... Have a read, share them with your team."* |
| **S002** | Maze — *18 Best Usability Testing Tools: Features & Pricing* | **COMMERCIAL + TEMPORAL** | A tool comparison with pricing, led by the publisher's own product: *"If you want an AI-first, end-to-end UX research platform... Maze is what you're looking for."* Tool lists and prices are among the fastest-decaying content possible. Its one general statement ("usability testing tools help you run remote studies on prototypes, live sites, and mobile experiences") is retained in [usability-testing.md](../02-discovery/usability-testing.md). |
| **S069** | IxDF — *Product Design and UX Design Roles: Unveiling the Differences* | **EXTRACTION STUB** | Only the table of contents and a promotional panel extracted (279 words, 1 page). The article's actual subject — the product-designer vs UX-designer distinction — **is therefore not in this knowledge base.** Recorded as a gap, not as a judgment on the source. |

## 2. Sources retained only as duplicates

Two sources were read in full and found to add nothing beyond what better sources already provide.
They are recorded here rather than cited.

| ID | Document | Why |
|---|---|---|
| **S055** | Riskonnect (Spanish) — *Los mejores consejos para una gestión eficaz de los riesgos del proyecto* | ~1,290 words, of which a large share is category navigation. Its risk-management definition ("el proceso de identificar, analizar y responder a cualquier riesgo que surja durante el ciclo de vida de un proyecto") duplicates [S125] and [S100], which are more complete and PMI-aligned. |
| **S139** | Planview — *What is an Agile Product Roadmap* | ~2,800 words heavily interleaved with cookie banners, demo CTAs and a chat widget. Its agile-roadmap content duplicates [S130], which is more structured. |

## 3. Categories of content stripped from retained sources

These were removed from sources that are otherwise cited. The **substance** of each source was kept.

### 3.1 Calls to action and lead capture
Removed across essentially every source.

Examples: *"Enroll now"* · *"Download Template"* · *"Get Yours Now"* · *"Get the Template"* ·
*"Book a demo"* · *"Request a demo"* · *"Start a free trial"* · *"Get started free"* ·
*"Join 315,283 subscribers"* · *"you@company.com Subscribe"* · *"Download your copy"* ·
*"GET THE CHECKLIST"* · *"Reserve your deck!"*

### 3.2 Navigation, footers and site chrome
Product menus, solution/industry/company columns, legal and policy links, social icons, breadcrumb
trails, "Read next" blocks, related-post carousels, author-follow prompts.

At corpus scale this was **~7% of extracted words** (~25,000 words). A footer-truncation pass was
also applied; it over-trimmed 9 files, which were detected and restored.

### 3.3 Cookie and consent banners
Present in most sources, frequently interleaved mid-sentence. Several appeared in Spanish
(*"Rechazarlas todas"*, *"Configuración de cookies"*, *"Política de cookies"*, *"Administrar
preferencias"*) because of the capture locale, creating bilingual noise inside English documents.

### 3.4 Tool and product promotion presented as guidance
Kept where a claim was substantive; removed where the claim resolved to *"use our product."*

| Excluded claim | Source | Why |
|---|---|---|
| Extended argument that purpose-built roadmapping software is necessary, that spreadsheets and slides are "a nightmare to maintain," and that only native tools prevent version drift | S119, S116, S024 | Self-serving. The underlying observation — that stale roadmaps mislead, and versioned static files drift — is **retained** in [roadmaps.md](../05-planning/roadmaps.md) |
| "Use Jira Product Discovery for effective prioritization" and eight further in-line Jira placements | S066 | Framework descriptions retained; tool placements removed |
| Userpilot analytics, MCP Server and Workflows product placements throughout the prioritization argument | S031 | Substantive argument retained; product placements removed |
| Aha! template and Roadmaps placements in strategy and positioning guidance | S090, S083, S104 | Concepts retained |
| Miro/Mural AI-assistant and template placements ("Ask Muriel", "Ask Clark", "Ask Paige", "Ask Hailey", "Ask Leslie", "Hey, I'm Hugo") | S001, S060, S061, S136, S008, S035, S050, S014, S077 | These chat-widget prompts appeared **inside body text** during extraction and were pure noise |

### 3.5 Certification and course promotion
Excluded: the certification lists in [S122] (CPM/AIPMM, CSPO, Google Analytics IQ, UX Design
Institute, Productboard Academy), Product School's nine certifications and ProductCon promotion
across ~20 sources, CareerFoundry's program and tuition-discount offers, Institute of Product
Leadership's programs, HelloPM's bootcamp, Project Management Academy's PMP exam-prep offers,
Reforge's program placements, and Maven's course placements.

> **Where a certification was named as a *fact about the profession* rather than an offer, it was
> kept** — e.g. the observation in [product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)
> that a product owner is a Scrum role.

### 3.6 Author biographies and credentials
Excluded as content; **retained as source attribution** in [SOURCES.md](../SOURCES.md) and in each
document's Sources table, because authorship affects reliability. Example: Ravi Mehta's role history
is recorded because it is why [S106] is Tier A, not because the biography is knowledge.

### 3.7 Testimonials and social proof
Excluded: student reviews, "trusted by" logos, share counts (*"794 Shares"*, *"1,017 Shares"*),
subscriber counts, like/restack counts.

> **Practitioner quotations were NOT excluded** where they carried substance — e.g. Jonatan Littke
> on Dream Maps, Ian Buchanan on cargo cult agile, Crystal Widjaja on platform PMs. These are
> attributed and, where they are advocacy, labelled as such.

### 3.8 Comment sections
Excluded, e.g. [S009]'s four reader comments (2018–2024), none of which discussed the article's
subject.

### 3.9 Contact details and office addresses
Excluded: phone numbers, sales emails, office addresses (e.g. Koru UX's Delaware and Pune
addresses; Step Change's Sydney address).

---

## 4. Content NOT excluded, and why

Recorded so the exclusion policy is auditable in both directions.

| Content | Kept because |
|---|---|
| **Unverified statistics** (Pendo's 6.4% feature adoption, "90% of unhappy customers never complain," "$3.8 trillion," "9 billion apps," Google's 20% time, LinkedIn's 45% revenue growth) | Removing them would hide what the corpus actually claims. **Each is reproduced with an explicit UNVERIFIED flag** and a do-not-cite instruction. See [disputed-information.md](disputed-information.md) |
| **Vendor-favourable framing where it carries an argument** | e.g. Atlassian's "agile is a cultural value, not our tools' fault" is self-serving *and* the corpus's clearest statement of why ceremonies without changed decision rights fail. Kept, with the conflict disclosed |
| **Weakly sourced sources** (S009, S141, S019) | Their techniques overlap with better-sourced material and are useful; they are **labelled low-reliability** and their claims are quarantined |
| **Contradictions between sources** | Preserved deliberately. See [disputed-information.md](disputed-information.md) |
| **Opinions by named practitioners** | Kept and labelled as opinion — e.g. Mike Cohn's stated personal preference for modified user stories over modified job stories |
| **Spanish-language sources** (S014, S143) | Content compared against English equivalents; overlapping material recorded, distinct material (the launch-vs-brand-building GTM distinction) retained |

---

## 5. What excluding this cost

An honest accounting:

- **Nothing of substance was lost from S120, S121, S002 or S055/S139** — these were genuinely
  redundant or empty.
- **S069's exclusion is a real loss.** The product-designer vs UX-designer distinction is a
  reasonable PM question and this knowledge base cannot answer it. The loss is due to **extraction
  failure**, not editorial judgment.
- **S027's exclusion is not a loss to this project** but may be a loss to another — it should be
  filed with the multi-agent/Stellar work it belongs to.
- **Tool-comparison content (S002)** would have been stale within months. Its exclusion is a net
  gain for a knowledge base intended to last.

---

## Related

- [SOURCES.md](../SOURCES.md) — the full source register with disposition
- [disputed-information.md](disputed-information.md) — contradictions preserved rather than resolved
- [outdated-information.md](outdated-information.md) — time-sensitive claims
- [CORPUS_AUDIT.md](../CORPUS_AUDIT.md) — the audit these decisions came from
