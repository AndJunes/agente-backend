# SOURCES

Register of every source this knowledge base draws on. **Two registers, two ID spaces, kept
separate on purpose:**

| ID form | Register | Origin |
|---|---|---|
| **`[Snnn]`** — S001–S143 | [The corpus register](#the-register) | The **143 source documents** of the original corpus (browser-printed PDFs) |
| **`[Ennn]`** — E001–E014 | [The external register](#external-sources-phase-2) | **Phase-2 external research**: primary texts, empirical studies and tool documentation retrieved deliberately to close identified gaps |

**Every factual claim in this knowledge base carries a source ID that resolves to a row in one of
these two tables.** A statement without a source ID is either a cross-reference, an explicitly
flagged synthesis, or an explicitly flagged gap.

> **Why the ID spaces are separate.** Corpus material and researched material must never blend
> silently. A document's frontmatter declares `corpus_origin` and `external_research` independently,
> and Phase-2 documents additionally carry `verified` and a `provenance` block. The `[S]` / `[E]`
> prefix makes the distinction visible at the point of citation, not just in metadata.

## How to read this table

- **ID** — the citation key used throughout the knowledge base.
- **Date** — publication or last-updated date **as stated in the document itself**. `—` means the
  captured document carried no determinable date. **Dates were never inferred.** 35 of 143 sources
  carry a determinable date; this is a limitation of the corpus, not of the audit.
- **Size** — pages and extracted words. A high word count can reflect navigation chrome rather than
  substance.
- **Tier** — reliability assessment made during the audit:

| Tier | Meaning | Count |
|---|---|---|
| **A** | Primary text quoted, empirical research with stated method, academic or standards citation, or authored by a recognised originator on that specific topic | 22 |
| **B** | Professional practitioner or vendor content — substantive but assertion-based and commercially motivated | 102 |
| **C** | Low reliability — unsourced statistics, extraction stubs, link farms, or content whose substance is promotional | 19 |

- **Disposition** — the domain the source feeds, or the reason for exclusion.
- **Used in** — the knowledge-base documents that actually cite it.

> **Tier is not a measure of correctness.** A Tier-C source may state something true; a Tier-A source
> may be wrong. Tier records **how far a claim can be traced**, and therefore how much weight it can
> carry without further verification.

## Corpus at a glance

| | |
|---|---|
| Source documents | **143** — all PDFs, all browser-printed web articles |
| Total pages | **1,645** |
| Extracted words | **~344,700** raw → **~319,400** after boilerplate removal |
| Sources feeding the knowledge base | **138** |
| Sources excluded entirely | **5** |
| Sources retained only as duplicate evidence | **2** |
| Languages | English (140), Spanish (3 — S014, S055, S143) |
| Distinct publishers | ~60 |
| **External sources added in Phase 2** | **14** (E001–E014) — see [below](#external-sources-phase-2) |

## The register

| ID | Original document | Publisher | Date | Size | Tier | Disposition | Used in |
|---|---|---|---|---|---|---|---|
| **S001** | 10 Brainstorming Techniques for Idea Generation   Mural | Mural | — | 15p / 2632w | B | 08-ideation | `08-ideation/brainstorming.md` · `08-ideation/idea-evaluation.md` · `08-ideation/mind-mapping.md` |
| **S002** | 18 Best Usability Testing Tools  Features & Pricing   Maze | Maze | — | 1p / 230w | C | **EXCLUDED** — TOOLS / TEMPORAL | `02-discovery/usability-testing.md` |
| **S003** | 37 Roadmap Tips to Align Stakeholders   ProductPlan | ProductPlan | — | 10p / 2736w | B | 05-planning | `04-strategy/product-value.md` · `05-planning/backlog-management.md` · `05-planning/estimation.md` · `05-planning/prioritization.md` · `05-planning/roadmap-communication.md` · `05-planning/roadmap-formats.md` · `09-metrics/north-star-metric.md` · `09-metrics/product-metrics.md` · `10-risk/risk-monitoring.md` |
| **S004** | 4 Key Stages Of The Product Development Process   Reforge Blog | Reforge | — | 11p / 3110w | B | 07-execution | `05-planning/dependencies.md` · `07-execution/product-development-process.md` |
| **S005** | 4 Value Proposition Models for Product Managers   Tempo | Tempo | — | 12p / 2082w | B | 04-strategy | `03-market-intelligence/competitive-analysis.md` · `03-market-intelligence/market-needs.md` · `04-strategy/positioning.md` · `04-strategy/product-market-fit.md` · `04-strategy/product-value.md` · `04-strategy/value-proposition.md` |
| **S006** | 4 Ways to Develop Your Strategic Thinking Skills in Product Management | Productside/PS | — | 4p / 1458w | C | 01-foundations | `01-foundations/product-manager-vs-product-owner.md` · `02-discovery/hypotheses-and-assumptions.md` · `04-strategy/strategic-thinking.md` |
| **S007** | 5 Frameworks for Setting Better Product Goals   Reforge Blog | Reforge | — | 18p / 5663w | B | 04-strategy | `04-strategy/okrs.md` · `04-strategy/product-goals.md` |
| **S008** | 6 Keys to Effective Product Collaboration   Productboard | Productboard | — | 7p / 1578w | B | 07-execution | `07-execution/product-collaboration.md` · `07-execution/working-with-engineering.md` |
| **S009** | 6 Ways to Identify Unmet Customer Needs | StepChange | — | 10p / 1533w | C | 02-discovery | `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/identifying-unmet-needs.md` · `03-market-intelligence/market-needs.md` · `03-market-intelligence/market-trends.md` · `08-ideation/idea-evaluation.md` · `12-design-and-ux/service-design.md` |
| **S010** | 6-3-5 Brainwriting - Wikipedia | Wikipedia | — | 3p / 1140w | A | 08-ideation | `08-ideation/brainstorming.md` · `08-ideation/brainwriting.md` · `08-ideation/idea-evaluation.md` · `08-ideation/mind-mapping.md` · `08-ideation/scamper.md` |
| **S011** | 7 Effective Growth Strategies and How to Apply Them | ProductSchool | July 17, 2025 | 18p / 3219w | B | 04-strategy | `04-strategy/product-led-growth.md` |
| **S012** | 7 Risk Mitigation Strategies for Businesses   Mitti (by SafetyCulture) | Mitti | — | 9p / 1453w | B | 10-risk | `10-risk/risk-response.md` |
| **S013** | 7 Usability Testing Methods for UX Insights   Maze | Maze | — | 1p / 183w | C | 02-discovery | `02-discovery/usability-testing.md` |
| **S014** | 9 pasos para diseñar una estrategia de Go-to-Market [2026] • Asana | Asana(ES) | — | 18p / 4595w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/go-to-market.md` |
| **S015** | A 10-Step Checklist For the End-of-Life of Your Product   ProductPlan | ProductPlan | — | 6p / 1554w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/decline-and-end-of-life.md` |
| **S016** | A Guide to Risk Analysis  Example & Methods   Mitti (by SafetyCulture) | Mitti | — | 13p / 1902w | B | 10-risk | `08-ideation/brainstorming.md` · `10-risk/risk-assessment.md` · `10-risk/risk-identification.md` |
| **S017** | A Guide to Using User-Experience Research Methods - NN G | NNg | — | 7p / 615w | A | 02-discovery | `02-discovery/user-research-methods.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S018** | A Guide to the SCAMPER Technique for Design Thinking | IxDF | Apr 10, 2015 | 15p / 2167w | B | 08-ideation | `08-ideation/scamper.md` |
| **S019** | A PM’s Perspective - The Do's and Don’ts of Scaling Product Management | ProdPad? | April 25, 2024 | 12p / 1950w | C | 01-foundations | `05-planning/backlog-management.md` · `05-planning/dependencies.md` · `07-execution/product-collaboration.md` · `09-metrics/north-star-metric.md` · `09-metrics/product-metrics.md` |
| **S020** | A Short Guide to Project Monitoring Control   Mitti (by SafetyCulture) | Mitti | — | 8p / 1270w | B | 07-execution | `05-planning/dependencies.md` · `06-requirements/scope-definition.md` · `07-execution/project-monitoring-and-control.md` · `10-risk/risk-monitoring.md` |
| **S021** | AARRR vs RARRA  Pirate Metrics Explained | MindTheProduct | — | 11p / 1908w | B | 09-metrics | `04-strategy/product-led-growth.md` · `09-metrics/pirate-metrics.md` |
| **S022** | Agile Manifesto for Software Development   Atlassian | Atlassian | — | 8p / 2113w | A | 07-execution | `07-execution/agile-manifesto.md` |
| **S023** | Brainstorming Techniques  How To Generate New Product Ideas | Aha! | March 2024 | 14p / 2550w | B | 08-ideation | `08-ideation/brainstorming.md` · `08-ideation/mind-mapping.md` · `10-risk/risk-assessment.md` |
| **S024** | Building Your First Product Roadmap from Scratch in 4 Steps   ProductPlan | ProductPlan | — | 8p / 2304w | B | **EXCLUDED** — DUPLICATE | — |
| **S025** | Competitive analysis for product managers  A complete guide | Zeda? | — | 25p / 4678w | B | 03-market-intelligence | `03-market-intelligence/competitive-analysis.md` · `03-market-intelligence/market-needs.md` · `03-market-intelligence/market-trends.md` |
| **S026** | Conduct an Effective Competitive Analysis Everytime   ProductPlan | ProductPlan | — | 6p / 2309w | B | 03-market-intelligence | `03-market-intelligence/competitive-analysis.md` |
| **S027** | Cuentas y wallets en Stellar | - | — | 2p / 860w | C | **EXCLUDED** — OUT-OF-DOMAIN | — |
| **S028** | Discovery  Definition - NN G | NNg | — | 9p / 2284w | A | 02-discovery | `02-discovery/discovery-frameworks.md` · `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/identifying-unmet-needs.md` · `02-discovery/product-discovery.md` · `02-discovery/user-interviews.md` · `02-discovery/user-research-methods.md` · `05-planning/prioritization.md` · `08-ideation/brainstorming.md` · `08-ideation/idea-evaluation.md` · `08-ideation/scamper.md` · `10-risk/assumptions-and-constraints.md` · `10-risk/product-risk.md` · `12-design-and-ux/product-triad.md` · `12-design-and-ux/service-design.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S029** | Ethnographic Research  Definition, Examples & Uses | Glossary | — | 9p / 1519w | B | 02-discovery | `02-discovery/ethnographic-research.md` |
| **S030** | Evaluating Ideas and Opportunities  Definition & Examples | Glossary | — | 12p / 2417w | B | 02-discovery | `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/opportunity-assessment.md` · `03-market-intelligence/market-needs.md` · `05-planning/prioritization.md` · `08-ideation/idea-evaluation.md` |
| **S031** | Feature Prioritization Matrix for Product Teams - still valid in 2026  | Userpilot? | August 31, 2026 | 18p / 5223w | B | 05-planning | `02-discovery/jobs-to-be-done.md` · `03-market-intelligence/market-trends.md` · `04-strategy/product-market-fit.md` · `04-strategy/product-value.md` · `04-strategy/strategic-thinking.md` · `05-planning/backlog-management.md` · `05-planning/continuous-roadmapping.md` · `05-planning/estimation.md` · `05-planning/prioritization-frameworks.md` · `05-planning/prioritization.md` · `05-planning/release-planning.md` · `07-execution/product-collaboration.md` · `08-ideation/idea-evaluation.md` · `09-metrics/product-metrics.md` · `10-risk/it-and-security-risk.md` · `10-risk/risk-assessment.md` · `10-risk/risk-identification.md` · `11-lifecycle-and-launch/managing-maturity.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S032** | Feature Prioritization  How to Prioritize the Right Features | Aha! | February 2025 | 7p / 1515w | B | 05-planning | `05-planning/backlog-management.md` · `05-planning/prioritization-frameworks.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` |
| **S033** | Go-to-Market Strategy Guide for Product Managers     Pragmatic Institute | Pragmatic | — | 10p / 3018w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/go-to-market.md` |
| **S034** | Go-to-Market Strategy for Product Marketing Teams | ProductSchool | January 7, 2026 | 24p / 5024w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/go-to-market.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S035** | Guide  How to Build a Product Roadmap   Productboard | Productboard | — | 11p / 3013w | B | 05-planning | `05-planning/release-planning.md` · `05-planning/roadmap-formats.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `05-planning/roadmaps.md` |
| **S036** | How Product Managers Can Write More Compelling Value Propositions   ProductPlan | ProductPlan | — | 6p / 1695w | B | 04-strategy | `04-strategy/value-proposition.md` |
| **S037** | How solo Product managers can own go-to-market strategy in lean teams | MindTheProduct | — | 12p / 1664w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/go-to-market.md` |
| **S038** | How to Become a Product Manager  No Experience  No Problem  | ProductSchool | January 22, 2026 | 26p / 3551w | B | 01-foundations | `01-foundations/product-manager-skills.md` |
| **S039** | How to Communicate Your Roadmap to Stakeholders   ProductPlan | ProductPlan | — | 8p / 2296w | B | 05-planning | `05-planning/backlog-management.md` · `05-planning/prioritization.md` · `05-planning/roadmap-communication.md` · `07-execution/project-monitoring-and-control.md` |
| **S040** | How to Get Started with Outcome-Based Product Roadmaps   Roman Pichler | RomanPichler | — | 7p / 1707w | A | 05-planning | `04-strategy/okrs.md` · `04-strategy/product-strategy.md` · `04-strategy/value-proposition.md` · `05-planning/backlog-management.md` · `05-planning/estimation.md` · `05-planning/outcome-based-roadmaps.md` · `05-planning/prioritization.md` · `05-planning/roadmap-communication.md` · `05-planning/roadmap-formats.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `05-planning/roadmaps.md` · `07-execution/agile-manifesto.md` · `07-execution/product-collaboration.md` · `09-metrics/product-metrics.md` |
| **S041** | How to Identify Market Needs and Create Products to Meet Them   UXtweak | UXtweak | — | 27p / 4516w | B | 03-market-intelligence | `02-discovery/discovery-frameworks.md` · `02-discovery/identifying-unmet-needs.md` · `03-market-intelligence/market-needs.md` · `03-market-intelligence/market-research.md` |
| **S042** | How to Manage the Maturity Stage of Product Life Cycle | ProdPad | — | 11p / 2891w | B | 11-lifecycle-and-launch | `05-planning/backlog-management.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `11-lifecycle-and-launch/managing-maturity.md` · `11-lifecycle-and-launch/product-launch.md` · `11-lifecycle-and-launch/product-lifecycle.md` |
| **S043** | How to Monitor Risk in Project Management | PMAcademy | — | 6p / 1647w | A | 10-risk | `07-execution/project-monitoring-and-control.md` · `09-metrics/product-metrics.md` · `10-risk/risk-management.md` · `10-risk/risk-monitoring.md` · `10-risk/risk-response.md` |
| **S044** | How to Run Surveys at Every Stage of the Design Cycle - NN G | NNg | — | 14p / 1755w | A | 02-discovery | `02-discovery/surveys.md` · `02-discovery/user-research-methods.md` · `03-market-intelligence/market-needs.md` · `06-requirements/scope-definition.md` · `09-metrics/product-metrics.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S045** | How to Use Ethnographic Research in Product Development   Koru UX | KoruUX | — | 17p / 2090w | B | 02-discovery | `02-discovery/ethnographic-research.md` · `02-discovery/identifying-unmet-needs.md` · `02-discovery/user-research-methods.md` · `03-market-intelligence/market-research.md` |
| **S046** | How to Work With Engineers  A Guide for Product Managers - HelloPM | HelloPM | — | 9p / 2093w | B | 07-execution | `07-execution/working-with-engineering.md` · `12-design-and-ux/product-design-fundamentals.md` |
| **S047** | How to get the most value out of your product roadmap | MindTheProduct | — | 9p / 1460w | B | 05-planning | `05-planning/dependencies.md` · `05-planning/roadmap-communication.md` |
| **S048** | How to write a PRD in 7 simple steps | Notion | July 28, 2023 | 8p / 1330w | B | 06-requirements | `04-strategy/product-goals.md` · `05-planning/dependencies.md` · `05-planning/release-planning.md` · `06-requirements/acceptance-criteria.md` · `06-requirements/prd.md` · `06-requirements/requirements.md` · `06-requirements/scope-definition.md` · `07-execution/project-monitoring-and-control.md` · `09-metrics/product-metrics.md` |
| **S049** | How top product managers work with engineers - LogRocket Blog | LogRocket | — | 12p / 1702w | B | 07-execution | `05-planning/dependencies.md` · `07-execution/product-collaboration.md` · `07-execution/product-development-process.md` · `07-execution/working-with-engineering.md` |
| **S050** | IT Risk Assessment  Identify and Reduce IT Risks   Hyperproof | Hyperproof | — | 22p / 4596w | B | 10-risk | `10-risk/it-and-security-risk.md` |
| **S051** | Introduction to Risk Assessment in Project Management | PMAcademy | — | 8p / 3549w | A | 10-risk | `09-metrics/product-metrics.md` · `10-risk/risk-assessment.md` · `10-risk/risk-identification.md` · `10-risk/risk-management.md` · `10-risk/risk-monitoring.md` |
| **S052** | Job Stories Offer a Viable Alternative to User Stories - Mountain Goat Software | MountainGoat | — | 6p / 1948w | A | 06-requirements | `06-requirements/acceptance-criteria.md` · `06-requirements/epics-and-decomposition.md` · `06-requirements/job-stories.md` · `06-requirements/user-stories.md` |
| **S053** | Job Story (JTBD). What it is, How it Works, Examples  | LearningLoop | — | 11p / 2641w | B | 06-requirements | `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/jobs-to-be-done.md` · `06-requirements/job-stories.md` |
| **S054** | Jobs to be done for Product Managers | MindTheProduct | — | 20p / 4839w | B | 02-discovery | `02-discovery/discovery-frameworks.md` · `02-discovery/identifying-unmet-needs.md` · `02-discovery/jobs-to-be-done.md` · `02-discovery/user-interviews.md` · `03-market-intelligence/competitive-analysis.md` · `03-market-intelligence/market-needs.md` · `04-strategy/product-value.md` · `04-strategy/value-proposition.md` · `06-requirements/epics-and-decomposition.md` · `06-requirements/job-stories.md` |
| **S055** | Los mejores consejos para una gestión eficaz de los riesgos del proyecto · Riskonnect | Riskonnect(ES) | — | 3p / 1386w | C | **EXCLUDED** — DUPLICATE | — |
| **S056** | Market Research  How Should PMs Gather Customer Insights  | Aha! | — | 8p / 1616w | B | 03-market-intelligence | `03-market-intelligence/market-research.md` |
| **S057** | Market Trend Analysis  Definition, Examples & Uses | Glossary | — | 8p / 1360w | B | 03-market-intelligence | `03-market-intelligence/market-trends.md` |
| **S058** | Maven  Market Research Techniques  A Comprehensive Guide for Product Managers | Maven | — | 7p / 1421w | B | 03-market-intelligence | `02-discovery/user-research-methods.md` · `03-market-intelligence/market-research.md` |
| **S059** | Maven  The Product Manager's Guide to Understanding the Market Landscape | Maven | — | 7p / 1182w | B | 03-market-intelligence | `03-market-intelligence/competitive-analysis.md` · `03-market-intelligence/market-research.md` · `03-market-intelligence/market-trends.md` |
| **S060** | Mind Mapping Techniques  Boost Productivity & Organize Ideas   Miro | Miro | — | 9p / 1794w | B | 08-ideation | `08-ideation/mind-mapping.md` |
| **S061** | Mind Maps  How to Organize & Connect Your Ideas   Mural | Mural | — | 12p / 2112w | B | 08-ideation | `08-ideation/mind-mapping.md` |
| **S062** | Outcome-Based Roadmaps  Mapping Impact, Not Features | ProductSchool | October 30, 2025 | 17p / 2948w | B | 05-planning | `04-strategy/okrs.md` · `05-planning/outcome-based-roadmaps.md` · `05-planning/roadmap-formats.md` · `09-metrics/product-metrics.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S063** | Outcome-Driven Roadmapping  The Secret to a Focused Product Strategy   ProductPlan | ProductPlan | — | 6p / 1747w | B | 05-planning | `05-planning/outcome-based-roadmaps.md` |
| **S064** | PM and UX Have Markedly Different Views of Their Job Responsibilities - NN G | NNg | — | 20p / 5045w | A | 01-foundations | `01-foundations/pm-and-ux-collaboration.md` · `01-foundations/product-manager-vs-product-owner.md` · `01-foundations/product-vs-project-management.md` · `02-discovery/product-discovery.md` · `02-discovery/user-interviews.md` · `05-planning/backlog-management.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `05-planning/roadmaps.md` · `07-execution/product-collaboration.md` · `07-execution/working-with-engineering.md` · `12-design-and-ux/product-design-fundamentals.md` · `12-design-and-ux/product-triad.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S065** | PMP Exam Strategies for Risk Response  Mitigate Risk, Avoid, or Transfer | PMAcademy | — | 6p / 1678w | A | 10-risk | `10-risk/risk-management.md` · `10-risk/risk-response.md` |
| **S066** | Prioritization frameworks   Atlassian | Atlassian | — | 10p / 2175w | B | 05-planning | `05-planning/estimation.md` · `05-planning/prioritization-frameworks.md` · `05-planning/prioritization.md` · `08-ideation/idea-evaluation.md` |
| **S067** | Prioritize your roadmap with 4D roadmapping | Notejoy/Rekhi | — | 3p / 355w | C | 05-planning | `05-planning/prioritization-frameworks.md` |
| **S068** | Proactive Risk Monitoring to Mitigate Losses   Mitti (by SafetyCulture) | Mitti | — | 11p / 1457w | B | 10-risk | `10-risk/risk-monitoring.md` |
| **S069** | Product Design and UX Design Roles  Unveiling the Differences   IxDF | IxDF | — | 1p / 279w | C | **EXCLUDED** — STUB | `12-design-and-ux/product-design-fundamentals.md` |
| **S070** | Product Development  A Comprehensive Guide for Product Managers | Aha! | September 2025 | 10p / 2001w | B | 07-execution | `07-execution/product-development-process.md` |
| **S071** | Product Life Cycle Decline Stage  How to Handle It | Railsware? | — | 19p / 4396w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/decline-and-end-of-life.md` · `11-lifecycle-and-launch/product-lifecycle.md` |
| **S072** | Product Lifecycle  What PMs and Teams Need To Know | Aha! | September 2024 | 15p / 3365w | A | 11-lifecycle-and-launch | `11-lifecycle-and-launch/go-to-market.md` · `11-lifecycle-and-launch/managing-maturity.md` · `11-lifecycle-and-launch/product-launch.md` · `11-lifecycle-and-launch/product-lifecycle.md` |
| **S073** | Product Management Skills  Market Research | ProductSchool | September 11, 2024 | 11p / 1768w | B | 03-market-intelligence | `03-market-intelligence/market-research.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S074** | Product Management Skills  User Research | ProductSchool | January 3, 2025 | 10p / 1917w | B | 02-discovery | `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/identifying-unmet-needs.md` · `02-discovery/usability-testing.md` · `02-discovery/user-interviews.md` · `02-discovery/user-research-methods.md` · `08-ideation/mind-mapping.md` · `09-metrics/product-metrics.md` · `10-risk/it-and-security-risk.md` |
| **S075** | Product Management's Role at Every Phase of the Product Lifecycle   ProductPlan | ProductPlan | — | 7p / 1918w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/product-lifecycle.md` |
| **S076** | Product Manager Data for Discovery   Productboard | Productboard | — | 7p / 1355w | B | 02-discovery | `02-discovery/product-discovery.md` · `02-discovery/user-research-methods.md` · `03-market-intelligence/competitive-analysis.md` · `03-market-intelligence/market-research.md` · `04-strategy/product-market-fit.md` · `05-planning/release-planning.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `09-metrics/product-metrics.md` · `11-lifecycle-and-launch/decline-and-end-of-life.md` |
| **S077** | Product Manager Roles And Responsibilities   Productside   Product Management Courses & Training | Productside | — | 8p / 1413w | B | 01-foundations | `01-foundations/product-manager-role.md` · `01-foundations/product-manager-skills.md` · `04-strategy/product-value.md` · `04-strategy/value-proposition.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S078** | Product Manager  Role & Best Practices for Beginners   Atlassian | Atlassian | — | 10p / 2205w | B | 01-foundations | `01-foundations/product-management.md` · `01-foundations/product-manager-role.md` · `01-foundations/product-manager-skills.md` · `01-foundations/product-manager-vs-product-owner.md` · `05-planning/backlog-management.md` · `05-planning/prioritization.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `07-execution/agile-manifesto.md` · `07-execution/product-collaboration.md` · `07-execution/working-with-engineering.md` |
| **S079** | Product Manager’s Power Move  Competitor Analysis | ProductSchool | May 6, 2025 | 18p / 3736w | B | 03-market-intelligence | `03-market-intelligence/competitive-analysis.md` |
| **S080** | Product OKRs  Driving Outcomes Over Outputs | ProductSchool | April 3, 2025 | 17p / 3211w | B | 04-strategy | `04-strategy/okrs.md` · `04-strategy/product-goals.md` · `04-strategy/product-strategy.md` · `04-strategy/product-vision.md` · `09-metrics/north-star-metric.md` · `09-metrics/product-metrics.md` |
| **S081** | Product Opportunity Assessment  Expert Tips & Tricks | ProductSchool | June 2, 2025 | 19p / 3807w | B | 02-discovery | `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/opportunity-assessment.md` · `02-discovery/product-discovery.md` · `02-discovery/user-interviews.md` · `03-market-intelligence/competitive-analysis.md` · `03-market-intelligence/market-needs.md` · `03-market-intelligence/market-research.md` · `03-market-intelligence/market-trends.md` · `04-strategy/product-market-fit.md` · `05-planning/dependencies.md` · `05-planning/prioritization.md` · `08-ideation/idea-evaluation.md` · `09-metrics/product-metrics.md` · `10-risk/assumptions-and-constraints.md` · `10-risk/it-and-security-risk.md` |
| **S082** | Product Positioning 101  Expert Insights, Examples, and Tips | ProductSchool | September 16, 2024 | 23p / 5094w | B | 04-strategy | `04-strategy/positioning.md` |
| **S083** | Product Positioning  Finding the Right Approach | Aha! | October 2025 | 9p / 1687w | B | 04-strategy | `04-strategy/positioning.md` |
| **S084** | Product Requirements Document   Glossary   ProductPlan | ProductPlan | — | 5p / 1424w | B | 06-requirements | `05-planning/dependencies.md` · `05-planning/release-planning.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `06-requirements/acceptance-criteria.md` · `06-requirements/prd.md` · `06-requirements/requirements.md` · `06-requirements/scope-definition.md` · `10-risk/assumptions-and-constraints.md` · `12-design-and-ux/product-design-fundamentals.md` |
| **S085** | Product Requirements Document  What Is It & How To Write It [With 7 Templates]   Reforge Blog | Reforge | — | 8p / 1539w | B | 06-requirements | `06-requirements/prd.md` · `06-requirements/requirements.md` · `09-metrics/product-metrics.md` · `12-design-and-ux/product-design-fundamentals.md` |
| **S086** | Product Requirements Documents  Best Practices for PMs | Aha! | August 2025 | 9p / 1879w | B | 06-requirements | `05-planning/dependencies.md` · `05-planning/release-planning.md` · `06-requirements/prd.md` · `06-requirements/requirements.md` · `06-requirements/scope-definition.md` · `07-execution/agile-manifesto.md` · `09-metrics/product-metrics.md` · `10-risk/assumptions-and-constraints.md` · `10-risk/it-and-security-risk.md` · `12-design-and-ux/product-design-fundamentals.md` |
| **S087** | Product Risk  What It Is and How to Manage It | ProductSchool | June 25, 2025 | 18p / 3538w | B | 10-risk | `02-discovery/discovery-frameworks.md` · `02-discovery/hypotheses-and-assumptions.md` · `05-planning/dependencies.md` · `07-execution/agile-manifesto.md` · `07-execution/working-with-engineering.md` · `08-ideation/idea-evaluation.md` · `09-metrics/product-metrics.md` · `10-risk/assumptions-and-constraints.md` · `10-risk/it-and-security-risk.md` · `10-risk/product-risk.md` · `11-lifecycle-and-launch/product-launch.md` · `12-design-and-ux/service-design.md` |
| **S088** | Product Roadmap 2025 Guide with Examples & Templates | ProductSchool | August 5, 2025 | 31p / 5668w | B | 05-planning | `05-planning/roadmaps.md` |
| **S089** | Product Roadmap definition and examples | ProductSchool | — | 7p / 1169w | C | 05-planning | `05-planning/roadmaps.md` |
| **S090** | Product Strategy  How a Clear One Leads to Success | Aha! | August 2026 | 21p / 3748w | B | 04-strategy | `02-discovery/discovery-frameworks.md` · `03-market-intelligence/competitive-analysis.md` · `04-strategy/positioning.md` · `04-strategy/product-goals.md` · `04-strategy/product-market-fit.md` · `04-strategy/product-strategy.md` · `04-strategy/product-vision.md` · `04-strategy/value-proposition.md` · `11-lifecycle-and-launch/go-to-market.md` · `11-lifecycle-and-launch/product-lifecycle.md` |
| **S091** | Product Value  Core Concepts for PMs | Aha! | — | 7p / 1715w | C | 04-strategy | `04-strategy/product-value.md` |
| **S092** | Product Value  How to Define and Increase   Railsware Blog | Railsware | September 16, 2025 | 16p / 3805w | B | 04-strategy | `03-market-intelligence/market-needs.md` · `04-strategy/product-value.md` |
| **S093** | Product Vision Examples  10 Great Vision Statements   ProdPad | ProdPad | — | 11p / 2814w | B | 04-strategy | `04-strategy/product-vision.md` |
| **S094** | Product Vision vs. Mission - Silicon Valley Product Group   Silicon Valley Product Group | SVPG/Cagan | — | 6p / 1103w | A | 04-strategy | `04-strategy/product-vision.md` · `09-metrics/north-star-metric.md` · `10-risk/assumptions-and-constraints.md` |
| **S095** | Product Vision  How to Create One for Success in 2026 | ProductSchool | January 22, 2026 | 20p / 3807w | B | 04-strategy | `04-strategy/positioning.md` · `04-strategy/product-vision.md` · `04-strategy/value-proposition.md` |
| **S096** | Product design fundamentals every product manager should know | MindTheProduct | — | 12p / 1708w | B | 12-design-and-ux | `12-design-and-ux/product-design-fundamentals.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S097** | Product manager vs. project manager  Key differences explained   Atlassian | Atlassian | — | 11p / 2449w | B | 01-foundations | `01-foundations/product-vs-project-management.md` · `04-strategy/product-market-fit.md` · `05-planning/dependencies.md` · `05-planning/estimation.md` · `06-requirements/acceptance-criteria.md` · `06-requirements/epics-and-decomposition.md` · `06-requirements/requirements.md` · `06-requirements/scope-definition.md` |
| **S098** | Product-Led Growth Strategy for Product Managers | ProductSchool | January 21, 2026 | 22p / 3595w | B | 04-strategy | `04-strategy/product-led-growth.md` · `09-metrics/north-star-metric.md` · `09-metrics/pirate-metrics.md` · `09-metrics/product-metrics.md` |
| **S099** | Qualitative Usability Testing  Study Guide - NN G | NNg | — | 8p / 1537w | A | 02-discovery | `02-discovery/usability-testing.md` · `02-discovery/user-interviews.md` |
| **S100** | Risk Identification in Project Management - Project Management Academy Resources | PMAcademy | — | 8p / 2545w | A | 10-risk | `08-ideation/brainstorming.md` · `08-ideation/brainwriting.md` · `08-ideation/idea-evaluation.md` · `10-risk/assumptions-and-constraints.md` · `10-risk/risk-assessment.md` · `10-risk/risk-identification.md` · `10-risk/risk-management.md` · `10-risk/risk-monitoring.md` |
| **S101** | SCAMPER Design Thinking Technique  Complete Guide & Examples | Miro? | — | 17p / 2755w | B | 08-ideation | `08-ideation/scamper.md` |
| **S102** | Service Design - Design is Not Just for Products   IxDF | IxDF | — | 1p / 273w | C | 12-design-and-ux | `12-design-and-ux/service-design.md` |
| **S103** | Service Design 101 - NN G | NNg | — | 10p / 1572w | A | 12-design-and-ux | `12-design-and-ux/service-design.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S104** | Setting Product Goals  A Guide for PMs | Aha! | November 2025 | 9p / 1627w | B | 04-strategy | `04-strategy/product-goals.md` · `09-metrics/product-metrics.md` |
| **S105** | Should You Run a Survey  - NN G | NNg | — | 8p / 1833w | A | 02-discovery | `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/identifying-unmet-needs.md` · `02-discovery/surveys.md` · `02-discovery/usability-testing.md` · `02-discovery/user-research-methods.md` · `03-market-intelligence/market-research.md` |
| **S106** | Strategic Thinking for Product Managers | RaviMehta | — | 18p / 4230w | A | 04-strategy | `04-strategy/product-market-fit.md` · `04-strategy/product-strategy.md` · `04-strategy/strategic-thinking.md` · `07-execution/project-monitoring-and-control.md` · `08-ideation/brainstorming.md` · `10-risk/it-and-security-risk.md` · `10-risk/product-risk.md` · `10-risk/risk-management.md` · `10-risk/risk-monitoring.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S107** | Strategic thinking skills for product managers | MindTheProduct | — | 12p / 2069w | B | 04-strategy | `04-strategy/strategic-thinking.md` |
| **S108** | TBM 2.1 52  Continuous Roadmapping - by John Cutler | JohnCutler | — | 3p / 574w | A | 05-planning | `05-planning/backlog-management.md` · `05-planning/continuous-roadmapping.md` · `05-planning/estimation.md` · `05-planning/prioritization.md` · `05-planning/roadmap-communication.md` · `05-planning/roadmap-formats.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `05-planning/roadmaps.md` · `09-metrics/north-star-metric.md` |
| **S109** | The 12 Top Product Manager Skills You'll Need in 2025 | CareerFoundry | — | 14p / 3343w | B | 01-foundations | `01-foundations/product-management.md` · `01-foundations/product-manager-skills.md` · `03-market-intelligence/market-trends.md` · `07-execution/working-with-engineering.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S110** | The Definitive Guide to Product Discovery and Frameworks | ProductSchool | January 22, 2026 | 26p / 5403w | B | 02-discovery | `02-discovery/discovery-frameworks.md` · `02-discovery/hypotheses-and-assumptions.md` · `02-discovery/identifying-unmet-needs.md` · `02-discovery/jobs-to-be-done.md` · `02-discovery/opportunity-assessment.md` · `02-discovery/product-discovery.md` · `02-discovery/user-research-methods.md` · `04-strategy/product-market-fit.md` · `05-planning/prioritization.md` · `06-requirements/epics-and-decomposition.md` · `07-execution/product-collaboration.md` · `10-risk/assumptions-and-constraints.md` · `12-design-and-ux/service-design.md` |
| **S111** | The Growing Specialization of Product Management   Reforge Blog | Reforge | — | 18p / 4891w | B | 01-foundations | `01-foundations/pm-specializations.md` · `01-foundations/product-management.md` · `01-foundations/product-manager-skills.md` · `04-strategy/product-led-growth.md` · `04-strategy/product-market-fit.md` · `05-planning/dependencies.md` · `07-execution/working-with-engineering.md` · `09-metrics/pirate-metrics.md` · `09-metrics/product-metrics.md` · `11-lifecycle-and-launch/managing-maturity.md` · `11-lifecycle-and-launch/product-lifecycle.md` · `12-design-and-ux/service-design.md` |
| **S112** | The Move From Product to a Service Mindset | MindTheProduct | — | 8p / 979w | B | 12-design-and-ux | `12-design-and-ux/service-design.md` |
| **S113** | The Only PRD Template You Need (with Example) | ProductSchool | November 25, 2025 | 11p / 1565w | B | 06-requirements | `05-planning/release-planning.md` · `06-requirements/prd.md` · `06-requirements/scope-definition.md` · `09-metrics/product-metrics.md` · `11-lifecycle-and-launch/product-launch.md` · `12-design-and-ux/product-design-fundamentals.md` |
| **S114** | The Product Manager's Guide to User Research   Maze | Maze | — | 11p / 2426w | B | 02-discovery | `02-discovery/user-research-methods.md` |
| **S115** | The Product Triad  Design’s Role - NN G | NNg | — | 7p / 1876w | A | 12-design-and-ux | `12-design-and-ux/product-triad.md` |
| **S116** | The Product Trust Communication Curve   ProductPlan | ProductPlan | — | 5p / 1082w | B | 07-execution | `05-planning/roadmap-communication.md` · `05-planning/roadmaps.md` · `07-execution/product-collaboration.md` |
| **S117** | The Role of Competitive Analysis in Effective Product Strategy (With Steps and Templates)   airfocus by Lucid | airfocus | — | 11p / 2374w | B | 03-market-intelligence | `03-market-intelligence/competitive-analysis.md` |
| **S118** | The Ultimate Guide to Product Management   ProductPlan | ProductPlan | — | 9p / 3456w | B | 01-foundations | `01-foundations/pm-specializations.md` · `01-foundations/product-management.md` · `01-foundations/product-manager-role.md` · `01-foundations/product-manager-vs-product-owner.md` · `01-foundations/product-vs-project-management.md` · `05-planning/release-planning.md` · `05-planning/roadmaps.md` · `07-execution/agile-manifesto.md` · `07-execution/product-development-process.md` · `11-lifecycle-and-launch/decline-and-end-of-life.md` · `11-lifecycle-and-launch/product-launch.md` · `11-lifecycle-and-launch/product-lifecycle.md` · `12-design-and-ux/service-design.md` |
| **S119** | The Ultimate Guide to Product Roadmaps   ProductPlan | ProductPlan | — | 10p / 3570w | B | 05-planning | `04-strategy/product-goals.md` · `04-strategy/product-value.md` · `05-planning/continuous-roadmapping.md` · `05-planning/dependencies.md` · `05-planning/prioritization.md` · `05-planning/release-planning.md` · `05-planning/roadmap-communication.md` · `05-planning/roadmap-formats.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `05-planning/roadmaps.md` · `07-execution/agile-manifesto.md` · `07-execution/project-monitoring-and-control.md` · `07-execution/working-with-engineering.md` · `08-ideation/idea-evaluation.md` · `11-lifecycle-and-launch/go-to-market.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S120** | The Ultimate Product Management Resources for Product Managers | ProductSchool | May 6, 2024 | 9p / 1487w | C | **EXCLUDED** — LINK-FARM | — |
| **S121** | Tips for agile product management | Atlassian | — | 4p / 419w | C | **EXCLUDED** — PROMOTIONAL | `07-execution/agile-manifesto.md` |
| **S122** | Top Product Manager Skills for Success   Productboard | Productboard | — | 18p / 5340w | B | 01-foundations | `01-foundations/product-management.md` · `01-foundations/product-manager-role.md` · `01-foundations/product-manager-skills.md` · `02-discovery/user-research-methods.md` · `03-market-intelligence/market-trends.md` · `04-strategy/product-value.md` · `10-risk/product-risk.md` · `12-design-and-ux/product-design-fundamentals.md` · `12-design-and-ux/product-triad.md` |
| **S123** | UX for Product Managers  Building Better Products   Figma | Figma | — | 12p / 1735w | C | 12-design-and-ux | `12-design-and-ux/product-design-fundamentals.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S124** | Ultimate Guide to Product Launch   ProductPlan | ProductPlan | — | 9p / 2731w | B | 11-lifecycle-and-launch | `05-planning/release-planning.md` · `09-metrics/north-star-metric.md` · `11-lifecycle-and-launch/go-to-market.md` · `11-lifecycle-and-launch/product-launch.md` |
| **S125** | Understanding Project Risk Management  A Guide   Mitti (by SafetyCulture) | Mitti | — | 9p / 1401w | B | 10-risk | `08-ideation/brainstorming.md` · `08-ideation/brainwriting.md` · `08-ideation/idea-evaluation.md` · `08-ideation/mind-mapping.md` · `10-risk/assumptions-and-constraints.md` · `10-risk/risk-identification.md` · `10-risk/risk-management.md` · `10-risk/risk-monitoring.md` |
| **S126** | User Stories With Examples and a Template   Atlassian | Atlassian | — | 8p / 1792w | B | 06-requirements | `05-planning/estimation.md` · `05-planning/prioritization.md` · `05-planning/release-planning.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `06-requirements/acceptance-criteria.md` · `06-requirements/epics-and-decomposition.md` · `06-requirements/user-stories.md` · `07-execution/agile-manifesto.md` |
| **S127** | User Stories  What They Are, How to Write Them, and Examples - Mountain Goat Software | MountainGoat | — | 10p / 2945w | A | 06-requirements | `04-strategy/product-value.md` · `05-planning/backlog-management.md` · `05-planning/continuous-roadmapping.md` · `05-planning/estimation.md` · `05-planning/outcome-based-roadmaps.md` · `05-planning/prioritization.md` · `05-planning/roadmap-vs-backlog-vs-release-plan.md` · `06-requirements/acceptance-criteria.md` · `06-requirements/epics-and-decomposition.md` · `06-requirements/job-stories.md` · `06-requirements/requirements.md` · `06-requirements/user-stories.md` |
| **S128** | User Story   Glossary   ProductPlan | ProductPlan | — | 6p / 1491w | B | 06-requirements | `05-planning/backlog-management.md` · `05-planning/estimation.md` · `06-requirements/acceptance-criteria.md` · `06-requirements/epics-and-decomposition.md` · `06-requirements/user-stories.md` |
| **S129** | Using Brainwriting For Rapid Idea Generation — Smashing Magazine | Smashing | — | 11p / 2442w | B | 08-ideation | `08-ideation/brainstorming.md` · `08-ideation/brainwriting.md` |
| **S130** | What Are Agile Roadmaps and How to Build Them | ProductSchool | March 31, 2025 | 20p / 2805w | B | 05-planning | `05-planning/dependencies.md` · `05-planning/outcome-based-roadmaps.md` · `05-planning/release-planning.md` · `05-planning/roadmap-communication.md` · `05-planning/roadmap-formats.md` · `05-planning/roadmaps.md` · `07-execution/agile-manifesto.md` · `07-execution/project-monitoring-and-control.md` |
| **S131** | What Does a Product Manager Actually Do  Daily Life as a PM | ProductSchool | July 2, 2025 | 17p / 3052w | B | 01-foundations | `01-foundations/product-manager-role.md` |
| **S132** | What Is Product Management  Everything You Need to Know | ProductSchool | December 18, 2025 | 28p / 5055w | B | 01-foundations | `01-foundations/product-management.md` |
| **S133** | What Is Product Positioning Strategy    Productside | Productside | — | 7p / 998w | B | 04-strategy | `04-strategy/positioning.md` · `11-lifecycle-and-launch/go-to-market.md` |
| **S134** | What Is an End-of-Life Product  Key Facts to Consider | ProductSchool | March 26, 2025 | 18p / 3299w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/decline-and-end-of-life.md` · `11-lifecycle-and-launch/managing-maturity.md` · `11-lifecycle-and-launch/product-lifecycle.md` |
| **S135** | What are Mind Maps  — updated 2026   IxDF | IxDF | — | 1p / 182w | C | 08-ideation | `08-ideation/mind-mapping.md` |
| **S136** | What is Brainstorming  Techniques and Methods   Miro | Miro | — | 21p / 7644w | B | 08-ideation | `08-ideation/brainstorming.md` · `08-ideation/idea-evaluation.md` · `08-ideation/mind-mapping.md` · `08-ideation/scamper.md` · `12-design-and-ux/product-design-fundamentals.md` |
| **S137** | What is Brainwriting — updated 2026   IxDF | IxDF | — | 1p / 327w | C | 08-ideation | `08-ideation/brainwriting.md` |
| **S138** | What is a Product Requirements Document (PRD)  | Atlassian | — | 10p / 2198w | B | 06-requirements | `05-planning/backlog-management.md` · `06-requirements/prd.md` · `06-requirements/requirements.md` · `06-requirements/scope-definition.md` · `07-execution/agile-manifesto.md` · `07-execution/project-monitoring-and-control.md` · `12-design-and-ux/product-design-fundamentals.md` |
| **S139** | What is an Agile Product Roadmap, its Benefits, how to build Agile Roadmap & more - Planview | Planview | — | 10p / 3200w | C | **EXCLUDED** — DUPLICATE | — |
| **S140** | What, exactly, is a Product Manager  | MindTheProduct | — | 9p / 985w | B | 01-foundations | `01-foundations/product-management.md` · `01-foundations/product-manager-role.md` · `01-foundations/product-manager-skills.md` · `04-strategy/product-value.md` · `04-strategy/product-vision.md` · `07-execution/working-with-engineering.md` · `12-design-and-ux/product-triad.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S141** | Why UX is Essential for Product Managers | ProductSchool? | January 24, 2024 | 13p / 1943w | C | 09-metrics | `09-metrics/product-metrics.md` · `12-design-and-ux/ux-for-product-managers.md` |
| **S142** | Writing an Effective Guide for a UX Interview - NN G | NNg | — | 7p / 1580w | A | 02-discovery | `02-discovery/user-interviews.md` · `08-ideation/mind-mapping.md` |
| **S143** | ¿Qué es una estrategia de comercialización    Guía completa de GTM | HubSpot?(ES) | — | 37p / 5472w | B | 11-lifecycle-and-launch | `11-lifecycle-and-launch/go-to-market.md` |
## Publisher concentration

The corpus is dominated by a small number of commercial publishers. This matters because it means
**the knowledge base inherits their perspective unless deliberately counterbalanced.**

| Publisher | Approx. sources | Nature |
|---|---|---|
| **Product School** | ~20 | Training provider; every article promotes certifications |
| **ProductPlan** | ~12 | Roadmapping software vendor |
| **Aha!** | ~8 | Product-management software vendor |
| **Nielsen Norman Group** | ~11 | **UX research organisation — the corpus's main source of empirical evidence** |
| **Atlassian** | ~6 | Software vendor (Jira, Confluence) |
| **Mind the Product** | ~7 | Practitioner community (Pendo) |
| **Mitti / SafetyCulture** | ~6 | Safety and GRC software vendor |
| **Productboard** | ~5 | Product-management software vendor |
| **Project Management Academy** | 4 | **PMI Authorized Training Partner — the corpus's main source of standards-aligned material** |
| **Reforge** | 4 | Practitioner education with named contributors |
| **Miro / Mural** | 5 | Collaboration software vendors |
| **Mountain Goat Software** | 2 | **Mike Cohn — primary authority on user stories** |
| Others (IxDF, Maze, Maven, Notion, Figma, LogRocket, HelloPM, CareerFoundry, ProdPad, Railsware, UXtweak, Koru UX, Hyperproof, Riskonnect, Asana, Pragmatic Institute, Productside, airfocus, Planview, Tempo, SVPG, Learning Loop, Smashing Magazine, Wikipedia, Step Change, Userpilot, LaunchNotes, Notejoy, Roman Pichler, Ravi Mehta, John Cutler) | 1–3 each | Mixed |

> **Roughly 85% of the corpus is commercially motivated content.** The knowledge base handles this by
> separating each source's substantive claims from its promotional framing, recording the commercial
> interest in each document's Limitations section, and preferring Tier-A sources where they conflict.

## Tier A sources and why

Where a Tier-A and a Tier-B source disagree, **prefer the Tier-A source** unless the knowledge-base
document states otherwise.

| ID | Why it is Tier A |
|---|---|
| **S010** | Wikipedia's *6-3-5 Brainwriting* — cites Rohrbach's original 1969 publication plus peer-reviewed journals (Shah, *J. Mechanical Design*, 2000; VanGundy, *J. Consumer Marketing*, 1984). **The best-referenced document in the corpus** |
| **S022** | Quotes the **Agile Manifesto verbatim** with its full signatory list — the only primary text reproduced anywhere in the corpus |
| **S064** | NN/g survey, **n=372**, significance-tested at p<0.05, sample and method stated |
| **S017, S028, S044, S099, S103, S105, S115, S142** | Nielsen Norman Group — research organisation; method-based, authored, dated |
| **S052, S127** | Mountain Goat Software (Mike Cohn) — a primary authority on user stories, writing **critically** about the technique and about its alternative |
| **S094** | Marty Cagan (SVPG) — originator of the product-vision position being explained |
| **S040** | Roman Pichler — author of the GO Product Roadmap being described |
| **S106** | Ravi Mehta (ex-CPO Tinder) — own framework, worked example, **and its real negative outcome disclosed** |
| **S108** | John Cutler — named practitioner, dated, original argument |
| **S043, S051, S065, S100** | Project Management Academy — **PMI Authorized Training Partner**, quoting PMI definitions directly |
| **S072** | Cites Theodore Levitt, *Exploit the Product Life Cycle*, Harvard Business Review, **1965** |

## External sources (Phase 2)

Retrieved deliberately to close gaps identified in [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md).
**Acquired September 2026**, except where the source itself carries a later retrieval note.

### How to read the provenance column

The user requirement that shaped this register: distinguish **what the original creator said** from
**a later interpretation**, from **what is considered current practice**, from **what empirical
evidence exists**. Every external source is typed accordingly.

| Code | Meaning |
|---|---|
| `PRIMARY` | The creator's or standard body's own text |
| `EMPIRICAL` | A study with a stated method and reported results |
| `PRACTICE` | Documented current practice; assertion-based, not measured |
| `SECONDARY` | A report *about* a source not read in the original |
| `VENDOR PROJECTION` | Modelled figures published by a party with a commercial interest |
| `BIBLIOGRAPHY ONLY` | Listed for completeness; **not consulted** — nothing is attributed to it |

### The register

| ID | Source | Date | Provenance | Tier | Used in |
|---|---|---|---|---|---|
| **E001** | **The Scrum Guide** — Ken Schwaber & Jeff Sutherland, `scrumguides.org` | **Nov 2020** (verified current, Sept 2026 — no later revision) | `PRIMARY` | **A** | [07-execution/scrum.md](07-execution/scrum.md) · [agile-manifesto](07-execution/agile-manifesto.md) · [acceptance-criteria](06-requirements/acceptance-criteria.md) · [pm-vs-po](01-foundations/product-manager-vs-product-owner.md) · [user-stories](06-requirements/user-stories.md) · [estimation](05-planning/estimation.md) |
| **E002** | **Principles behind the Agile Manifesto** — the 17 signatories, `agilemanifesto.org/principles.html` | **2001** | `PRIMARY` | **A** | [07-execution/agile-manifesto.md](07-execution/agile-manifesto.md) · [estimation](05-planning/estimation.md) · [spec-driven-development](13-ai-agent-collaboration/spec-driven-development.md) |
| **E003** | **Essential Kanban Condensed** — David J. Anderson & Andy Carmichael, Lean Kanban University Press | **2015–2016**; 1st digital ed. 17 Apr 2016 | `PRIMARY` · `PRACTICE` | **A** | [07-execution/kanban.md](07-execution/kanban.md) · [estimation](05-planning/estimation.md) · [acceptance-criteria](06-requirements/acceptance-criteria.md) · [pm-vs-po](01-foundations/product-manager-vs-product-owner.md) · [roadmap-formats](05-planning/roadmap-formats.md) · [project-monitoring](07-execution/project-monitoring-and-control.md) |
| **E004** | **The Kanban Guide** — Kanban University, `kanban.university/kanban-guide` | retrieved Sept 2026 | `PRIMARY` | **A** | [07-execution/kanban.md](07-execution/kanban.md) |
| **E005** | Anderson, D. J. — *Kanban: Successful Evolutionary Change for Your Technology Business* | 2010 | `BIBLIOGRAPHY ONLY` | — | Listed in [kanban.md](07-execution/kanban.md); **not consulted** |
| **E006** | **METR — *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*** — Becker, Rush, Barnes & Rein | **10 Jul 2025** (study period Feb–Jun 2025) | `EMPIRICAL` (RCT, n=16 devs / 246 tasks) | **A** | [evidence-on-ai-assisted-delivery](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) · [pm-with-ai-implementers](13-ai-agent-collaboration/pm-with-ai-implementers.md) · [evals-and-acceptance](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md) · [estimation](05-planning/estimation.md) |
| **E007** | **METR — *We are Changing our Developer Productivity Experiment Design*** | **24 Feb 2026** | `EMPIRICAL / CORRECTION` | **A** | [evidence-on-ai-assisted-delivery](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) · [pm-with-ai-implementers](13-ai-agent-collaboration/pm-with-ai-implementers.md) |
| **E008** | **DORA / Google Cloud — *State of AI-assisted Software Development*** (v.2025.2) | **2025**; survey 13 Jun – 21 Jul 2025, n≈5,000 | `EMPIRICAL` (self-report survey + 78 interviews) | **B** | [evidence-on-ai-assisted-delivery](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) · [pm-with-ai-implementers](13-ai-agent-collaboration/pm-with-ai-implementers.md) |
| **E009** | DORA — *ROI of AI-assisted Software Development* | **2026** | `VENDOR PROJECTION` | **C** | [evidence-on-ai-assisted-delivery](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) — **not read in original** |
| **E010** | InfoQ — *New DORA Report Claims Strong Engineering Foundations Drive AI Return on Investment* | **11 May 2026** | `SECONDARY` | **C** | Sole route to [E009] |
| **E011** | **Anthropic — *Demystifying evals for AI agents*** — Grace, Hadfield, Olivares & De Jonghe | **9 Jan 2026** | `PRACTICE` | **B** | [evals-and-acceptance](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md) · [pm-with-ai-implementers](13-ai-agent-collaboration/pm-with-ai-implementers.md) · [spec-driven-development](13-ai-agent-collaboration/spec-driven-development.md) · [acceptance-criteria](06-requirements/acceptance-criteria.md) |
| **E012** | **GitHub — `github/spec-kit`** (MIT licence) | retrieved Sept 2026 | `PRIMARY (tool)` · `PRACTICE` | **B** | [spec-driven-development](13-ai-agent-collaboration/spec-driven-development.md) · [pm-with-ai-implementers](13-ai-agent-collaboration/pm-with-ai-implementers.md) |
| **E013** | **Kiro (AWS) — official documentation**, `kiro.dev/docs/specs/` | product launched 14 Jul 2025; docs retrieved Sept 2026 | `PRIMARY (tool)` · `PRACTICE` | **B** | [spec-driven-development](13-ai-agent-collaboration/spec-driven-development.md) · [pm-with-ai-implementers](13-ai-agent-collaboration/pm-with-ai-implementers.md) |
| **E014** | **EARS — Easy Approach to Requirements Syntax** — Alistair Mavin et al., **Rolls-Royce plc**, `alistairmavin.com/ears` | first published **2009** | `PRIMARY` | **A** | [spec-driven-development](13-ai-agent-collaboration/spec-driven-development.md) · [pm-with-ai-implementers](13-ai-agent-collaboration/pm-with-ai-implementers.md) |

### What the external register does not contain

- **No Level-4 sources.** Blogs, forums, newsletters and vendor comparison articles were used for
  **discovery** — to find which primary sources and studies exist — and **none is cited as
  authority**. The one exception is [E010], a technology-news report, cited **only** as the
  acknowledged route to a report not read in the original, and flagged everywhere it appears.
- **No model-memory content.** Nothing in this knowledge base is asserted from the model's internal
  knowledge. Where a fact was needed and not retrievable, it is recorded as a gap.
- **Nine of fourteen external sources are vendor-published.** [E001], [E002], [E006], [E007] and
  [E014] are the independent or originator-authored exceptions. This concentration is a real
  limitation: the parties writing about AI-assisted development are largely the parties selling it.

### Verification performed

| Source | Check |
|---|---|
| [E001] | Confirmed the **November 2020** edition is the current one as of September 2026 — no 2025 or 2026 revision exists |
| [E002] | The four values, quoted in the corpus from [S022] (Atlassian), were checked against the canonical text and **match** |
| [E006] | Full paper retrieved and read, including the factor-analysis table and the authors' own list of misreadings |
| [E007] | Retrieved specifically to check whether [E006] still stands. **It does not stand as a description of current tooling**, per its own authors |
| [E009] | **Not obtained.** Recorded as read-through-[E010] and tiered accordingly |
| [E003] | Full text extracted and read, not summarised from a secondary source |

## Primary sources still referenced but NOT obtained

Named by corpus sources; obtaining them would materially raise confidence. Two entries were closed
in Phase 2 and are marked. See [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md).

| Referenced work | Referenced by | What it would settle |
|---|---|---|
| ~~**The Scrum Guide**~~ | S078, S118, S126 | ✅ **Obtained — [E001]** |
| ~~**The 12 Agile Principles**~~ | S022 | ✅ **Obtained — [E002]** |
| Cagan, *Inspired* / *Empowered* | S140, S094 | Valuable/usable/feasible; empowered vs feature teams |
| Ries, *The Lean Startup* | S110 | MVP; build–measure–learn |
| Torres, *Continuous Discovery Habits* | S110, S031 | Opportunity Solution Tree |
| Knapp, *Sprint* | S110 | Design Sprint |
| Christensen, *The Innovator's Dilemma* / *Solution* | S042, S053 | Disruption; JTBD origins |
| Klement, *When Coffee and Kale Compete* (2014) | S052, S053 | Job stories |
| Ulwick, *Jobs to Be Done* (2020) | S053, S031 | Opportunity-scoring formula (see disputed-information) |
| Moore, *Crossing the Chasm* | S005 | Value-proposition template |
| Osterwalder, *Value Proposition Design* | S005 | The canvas |
| Maurya, Lean Canvas | S005 | The canvas |
| Osborn, *Applied Imagination* (1953) | S101 | SCAMPER's origin prompts |
| Hall & Stark, *Just Enough Research* (2019) | S105 | Survey critique |
| Croll & Yoskovitz, *Lean Analytics* (2013) | S005 | The Sean Ellis 40% benchmark |
| Levitt, HBR (1965) | S072 | The product lifecycle |
| Doerr, *Measure What Matters*; Grove, *High Output Management* | S080 | OKR origins |
| **PMBOK Guide** | S043, S051, S065, S100 | All PMI process definitions |
| **DSDM documentation** | S031 | The MoSCoW 60% Must cap |
| NIST SP 800-30 | S050 | IT risk framework |
| McClure, *Startup Metrics for Pirates* (2007) | S021 | AARRR |
| Sy, dual-track paper (2007) | S110 | Dual-track agile |
| Design Council, Double Diamond | S110, S028 | The model |
| NN/g linked corpus (~40 articles, via S099) | S099 | Usability-testing execution |
| NN/g 20-method research map | S017 | Method selection (the chart did not extract) |
| Anderson, *Kanban* (2010) — [E005] | E003 | Kanban's original formulation; later developments (cadences, STATIK) postdate it |
| Little, *A Proof for the Queuing Formula* (1961) | E003 | The origin of Little's Law |

## Notes on extraction

All sources are **browser-printed PDFs of web pages**. Consequences for what this knowledge base can
contain:

1. **Images did not extract.** Diagrams, canvases, matrices, roadmap examples and framework figures
   are absent. Where a source's argument depended on a figure, the affected document says so.
2. **Multi-column and sidebar layouts interleaved.** Navigation, cookie banners and promotional
   panels appear mid-sentence in the raw text. A cleaning pass removed ~7% of extracted words as
   boilerplate; residual noise was filtered during reading. Eight over-trimmed files were detected
   and restored (S006, S011, S017, S023, S083, S086, S091, S104, S121).
3. **Several sources are substantially truncated.** Notably S017, S083, S091, S104, S123, S015,
   S134, S033, S037, S112, S102, S069. Each affected knowledge-base document records what was lost.
4. **Paywalled and gated content** (S067, S108) extracted only to the gate.
5. **URLs were largely not preserved** in the printed output, so canonical links cannot be given for
   most sources. Publisher and title are the available identifiers.

## Related

- [CORPUS_AUDIT.md](CORPUS_AUDIT.md) — the audit this register comes from
- [99-reference/excluded-content.md](99-reference/excluded-content.md) — what was removed and why
- [99-reference/disputed-information.md](99-reference/disputed-information.md) — source disagreements
- [99-reference/outdated-information.md](99-reference/outdated-information.md) — time-sensitive claims
- [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) — gaps and what to obtain
