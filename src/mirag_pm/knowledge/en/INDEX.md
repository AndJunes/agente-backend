# INDEX — Concept Retrieval Map

Maps concepts — and **the words people actually use for them** — to the documents that answer them.

**How to use it.** Two sections:

1. **[Quick answers](#quick-answers)** — the questions this knowledge base was built to answer.
2. **[Concept → document](#concept--document)**, per domain, giving each document's **Primary**
   location, **Related** documents (adjacent questions), and **Keywords** (alternative phrasings, so
   lexical and hybrid search can reach a document whose title does not match the query).
3. **[Alphabetical lookup](#alphabetical-lookup)** — 633 concept terms, flat, for direct resolution.

Entries marked **⚠ gap** mean the concept is *referenced* in this knowledge base but **not
adequately covered**. Those documents exist to record precisely what is missing and to stop an agent
answering from thin material. Entries marked **❌** have no answer here at all. See
[RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md).

Documents marked **[E]** are **Phase-2 external research**, not corpus-derived — see
[SOURCES.md](SOURCES.md) for the separate `[Ennn]` register.

---

## Quick answers

| If you are asked… | Start here |
|---|---|
| **How is an MVP defined?** | ⚠ **still a gap** — [02-discovery/discovery-frameworks.md](02-discovery/discovery-frameworks.md) — **gap**: the corpus has one sentence. [04-strategy/strategic-thinking.md](04-strategy/strategic-thinking.md) explains the *purpose* (minimise cost-to-learn) better than any definition in the corpus |
| **How do you build a roadmap?** | [05-planning/roadmaps.md](05-planning/roadmaps.md) → [05-planning/outcome-based-roadmaps.md](05-planning/outcome-based-roadmaps.md) → [05-planning/roadmap-formats.md](05-planning/roadmap-formats.md) |
| **How do you prioritize features?** | [05-planning/prioritization.md](05-planning/prioritization.md) (the practice and its failure modes) → [05-planning/prioritization-frameworks.md](05-planning/prioritization-frameworks.md) (RICE, Kano, MoSCoW, value/effort, opportunity scoring, cost of delay, weighted scoring) |
| **What's the difference between roadmap, backlog and release plan?** | [05-planning/roadmap-vs-backlog-vs-release-plan.md](05-planning/roadmap-vs-backlog-vs-release-plan.md) |
| **How do you define OKRs?** | [04-strategy/okrs.md](04-strategy/okrs.md) → [04-strategy/product-goals.md](04-strategy/product-goals.md) for alternatives (NCTs, Dream Maps) and when each fits |
| **How do you write a PRD?** | [06-requirements/prd.md](06-requirements/prd.md) — including the live argument about whether PRDs are obsolete |
| **How do you elicit requirements?** | [06-requirements/requirements.md](06-requirements/requirements.md) |
| **How do you manage risks?** | [10-risk/risk-management.md](10-risk/risk-management.md) → identification → assessment → response → monitoring |
| **How do you decompose an initiative into epics, stories and tasks?** | [06-requirements/epics-and-decomposition.md](06-requirements/epics-and-decomposition.md) |
| **How do you define scope?** | [06-requirements/scope-definition.md](06-requirements/scope-definition.md) |
| **How do you run discovery?** | [02-discovery/product-discovery.md](02-discovery/product-discovery.md) → [02-discovery/discovery-frameworks.md](02-discovery/discovery-frameworks.md) |
| **How do you validate a hypothesis?** | [02-discovery/hypotheses-and-assumptions.md](02-discovery/hypotheses-and-assumptions.md) → [02-discovery/user-research-methods.md](02-discovery/user-research-methods.md) for choosing the method |
| **How do you work with engineering?** | [07-execution/working-with-engineering.md](07-execution/working-with-engineering.md) |
| **How do you measure product success?** | ⚠ [09-metrics/product-metrics.md](09-metrics/product-metrics.md) — **thin**: definitions only, no measurement design |
| **How do you manage dependencies?** | ⚠ [05-planning/dependencies.md](05-planning/dependencies.md) — **thin**: no source in the corpus is about this |
| **How do you plan?** | [05-planning/roadmaps.md](05-planning/roadmaps.md) · [05-planning/continuous-roadmapping.md](05-planning/continuous-roadmapping.md) · ⚠ [05-planning/release-planning.md](05-planning/release-planning.md) |
| **How do you make a product decision?** | [04-strategy/strategic-thinking.md](04-strategy/strategic-thinking.md) — the strongest decision framework in the corpus |
| **Which frameworks exist, and when do you use each?** | [05-planning/prioritization-frameworks.md](05-planning/prioritization-frameworks.md) · [02-discovery/discovery-frameworks.md](02-discovery/discovery-frameworks.md) · [04-strategy/product-goals.md](04-strategy/product-goals.md) · [08-ideation/brainstorming.md](08-ideation/brainstorming.md) |
| **What must a PM know to work with software teams and AI agents?** | [01-foundations/product-manager-skills.md](01-foundations/product-manager-skills.md) · [07-execution/working-with-engineering.md](07-execution/working-with-engineering.md) · **[13-ai-agent-collaboration/](13-ai-agent-collaboration/)** |
| **How does PM work change when an AI agent writes the code?** | **[13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) first** (what is measured), then ⚠ [pm-with-ai-implementers.md](13-ai-agent-collaboration/pm-with-ai-implementers.md) — `confidence: low`, mostly labelled inference |
| **Does AI make developers faster?** | [13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) — **the honest answer is "unresolved"**; do not cite "19% slower" without its scope conditions |
| **How do you write a spec an AI agent can implement?** | ⚠ [13-ai-agent-collaboration/spec-driven-development.md](13-ai-agent-collaboration/spec-driven-development.md) — widely adopted practice, **no efficacy evidence** |
| **What do acceptance criteria mean when the implementer is non-deterministic?** | [13-ai-agent-collaboration/evals-and-acceptance-for-agents.md](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md) — pass@k vs pass^k |
| **How should a multi-agent software team be organised?** | ❌ **Not answerable.** See [13-ai-agent-collaboration/open-questions-ai-and-pm.md](13-ai-agent-collaboration/open-questions-ai-and-pm.md) §B1 |
| **How does Scrum work?** | [07-execution/scrum.md](07-execution/scrum.md) — from the 2020 Scrum Guide [E001], **including what Scrum deliberately does not define** |
| **What is Kanban?** | [07-execution/kanban.md](07-execution/kanban.md) — the **method**, not the board [E003]. WIP limits, pull, flow metrics, Little's Law, cadences |
| **What are the twelve Agile principles?** | [07-execution/agile-manifesto.md](07-execution/agile-manifesto.md) — verbatim from [E002] |
| **How do you forecast a delivery date?** | [07-execution/kanban.md](07-execution/kanban.md) + [05-planning/estimation.md](05-planning/estimation.md) — **probabilistic forecasting from flow data**. ⚠ Story points and velocity remain a gap |
| **Who owns discovery / research / the roadmap?** | [01-foundations/pm-and-ux-collaboration.md](01-foundations/pm-and-ux-collaboration.md) — **read this before asserting any ownership boundary**; the corpus has survey evidence that practitioners disagree |
| **Should we build this at all?** | [02-discovery/opportunity-assessment.md](02-discovery/opportunity-assessment.md) — including when *not* to run a full assessment |
| **How do you retire a product?** | [11-lifecycle-and-launch/decline-and-end-of-life.md](11-lifecycle-and-launch/decline-and-end-of-life.md) |
| **How do you get stakeholder buy-in?** | [05-planning/roadmap-communication.md](05-planning/roadmap-communication.md) |

### Composite retrieval — worked example

> *"I need to create a roadmap for a new feature whose problem is not yet validated, and there are
> technical constraints."*

This question should retrieve, in roughly this order:

1. [02-discovery/hypotheses-and-assumptions.md](02-discovery/hypotheses-and-assumptions.md) — the
   problem is not validated, so **that** is the first task
2. [02-discovery/product-discovery.md](02-discovery/product-discovery.md) — how to frame and research it
3. [02-discovery/opportunity-assessment.md](02-discovery/opportunity-assessment.md) — is it worth pursuing
4. [05-planning/prioritization.md](05-planning/prioritization.md) — where it sits against other work
5. [05-planning/outcome-based-roadmaps.md](05-planning/outcome-based-roadmaps.md) — expressing it as an outcome rather than a feature
6. [06-requirements/requirements.md](06-requirements/requirements.md) — constraints vs assumptions vs dependencies
7. [07-execution/working-with-engineering.md](07-execution/working-with-engineering.md) — surfacing feasibility early
8. [10-risk/product-risk.md](10-risk/product-risk.md) — unclear user needs as a named risk

> The reasoning this supports: **an unvalidated problem should not go onto a roadmap as a
> committed feature.** See [CONCEPT_GRAPH.md](CONCEPT_GRAPH.md).

---

## Concept → document

## 01 · Foundations

### PM and UX Role Boundaries (Survey Evidence)

**Primary:** [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)

**Related:**
- [Product Manager vs Product Owner](01-foundations/product-manager-vs-product-owner.md)
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [The Product Triad (Desirable, Viable, Feasible)](12-design-and-ux/product-triad.md)
- [UX for Product Managers](12-design-and-ux/ux-for-product-managers.md)

**Keywords:** cross-functional boundaries, pm and ux, raci, responsibility ambiguity, role overlap, who owns discovery

**Type:** `research-finding` · **Confidence:** `high`

### Product Management

**Primary:** [`01-foundations/product-management.md`](01-foundations/product-management.md)

**Related:**
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)
- [Product Manager Skills and Competencies](01-foundations/product-manager-skills.md)
- [Product Management vs Project Management](01-foundations/product-vs-project-management.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)
- [The Product Lifecycle](11-lifecycle-and-launch/product-lifecycle.md)
- [Product Strategy](04-strategy/product-strategy.md)

**Keywords:** pm discipline, product discipline, product function, product management, product management definition, product organization

**Type:** `concept` · **Confidence:** `high`

### Product Management Specializations and Types of Product Work

**Primary:** [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)

**Related:**
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)
- [Product Manager Skills and Competencies](01-foundations/product-manager-skills.md)
- [Product-Led Growth and Growth Models](04-strategy/product-led-growth.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Pirate Metrics — AARRR and RARRA](09-metrics/pirate-metrics.md)

**Keywords:** core pm, feature work, growth pm, innovation pm, platform pm, pm specialization, product-market fit expansion, scaling work, types of product work

**Type:** `framework` · **Confidence:** `medium`

### Product Management vs Project Management

**Primary:** [`01-foundations/product-vs-project-management.md`](01-foundations/product-vs-project-management.md)

**Related:**
- [Product Manager vs Product Owner](01-foundations/product-manager-vs-product-owner.md)
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)
- [Dependencies](05-planning/dependencies.md)
- [Project Monitoring and Control](07-execution/project-monitoring-and-control.md)
- [project risk management](10-risk/risk-management.md)

**Keywords:** delivery management, product manager vs project manager, project management, role boundaries, what vs how

**Type:** `comparison` · **Confidence:** `high`

### Product Manager Role and Responsibilities

**Primary:** [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)

**Related:**
- [Product Management](01-foundations/product-management.md)
- [Product Manager Skills and Competencies](01-foundations/product-manager-skills.md)
- [Product Manager vs Product Owner](01-foundations/product-manager-vs-product-owner.md)
- [PM and UX Role Boundaries (Survey Evidence)](01-foundations/pm-and-ux-collaboration.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)
- [Working with Engineering](07-execution/working-with-engineering.md)

**Keywords:** ceo of the product, influence without authority, pm responsibilities, pm role, product manager, product manager duties, product owner of the product vision, three pillars

**Type:** `concept` · **Confidence:** `high`

### Product Manager Skills and Competencies

**Primary:** [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)

**Related:**
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [User Interviews and Interview Guides](02-discovery/user-interviews.md)

**Keywords:** data literacy, hard skills, pm skills, prioritization skill, product management competencies, soft skills, storytelling

**Type:** `concept` · **Confidence:** `medium`

### Product Manager vs Product Owner

**Primary:** [`01-foundations/product-manager-vs-product-owner.md`](01-foundations/product-manager-vs-product-owner.md)

**Related:**
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)
- [Product Management vs Project Management](01-foundations/product-vs-project-management.md)
- [PM and UX Role Boundaries (Survey Evidence)](01-foundations/pm-and-ux-collaboration.md)
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [Prioritization — The Practice](05-planning/prioritization.md)

**Keywords:** backlog ownership, product manager vs product owner, product owner, scrum roles

**Type:** `comparison` · **Confidence:** `medium`


## 02 · Discovery

### Choosing a User Research Method

**Primary:** [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)

**Related:**
- [Product Discovery](02-discovery/product-discovery.md)
- [User Interviews and Interview Guides](02-discovery/user-interviews.md)
- [Surveys in Product Research](02-discovery/surveys.md)
- [Usability Testing](02-discovery/usability-testing.md)
- [Ethnographic Research and Contextual Observation](02-discovery/ethnographic-research.md)
- [Market Research](03-market-intelligence/market-research.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** attitudinal vs behavioral, method selection, qualitative vs quantitative, research methods, triangulation, user research

**Type:** `decision-framework` · **Confidence:** `high`

### Ethnographic Research and Contextual Observation

**Primary:** [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)

**Related:**
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [User Interviews and Interview Guides](02-discovery/user-interviews.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [Identifying Unmet Customer Needs](02-discovery/identifying-unmet-needs.md)
- [Service Design](12-design-and-ux/service-design.md)

**Keywords:** contextual inquiry, ethnographic research, ethnography, field research, observer bias, participant observation, say-do gap

**Type:** `technique` · **Confidence:** `medium`

### Hypotheses, Assumptions and Validation

**Primary:** [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)

**Related:**
- [Product Discovery](02-discovery/product-discovery.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [Product Discovery Frameworks](02-discovery/discovery-frameworks.md)
- [Product Risk](10-risk/product-risk.md)
- [Assumptions and Constraints as Risk Sources](10-risk/assumptions-and-constraints.md)
- [Prioritization — The Practice](05-planning/prioritization.md)

**Keywords:** assumption mapping, assumption testing, assumptions, evidence, experiments, hypothesis, hypothesis validation, idea validation, risk vs evidence grid, riskiest assumption, validation

**Type:** `process` · **Confidence:** `medium`

### Identifying Unmet Customer Needs

**Primary:** [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)

**Related:**
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Ethnographic Research and Contextual Observation](02-discovery/ethnographic-research.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Identifying Market Needs](03-market-intelligence/market-needs.md)
- [Value Proposition](04-strategy/value-proposition.md)

**Keywords:** customer journey mapping, latent needs, pain points, silent churn, triggers barriers drivers, unmet needs, voice of the customer

**Type:** `technique` · **Confidence:** `low`

### Jobs to be Done (JTBD)

**Primary:** [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md)

**Related:**
- [User Interviews and Interview Guides](02-discovery/user-interviews.md)
- [Product Discovery Frameworks](02-discovery/discovery-frameworks.md)
- [Identifying Unmet Customer Needs](02-discovery/identifying-unmet-needs.md)
- [Job Stories and When to Prefer Them Over User Stories](06-requirements/job-stories.md)
- [User Stories](06-requirements/user-stories.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)
- [Value Proposition](04-strategy/value-proposition.md)

**Keywords:** competing alternatives, job story, jobs to be done, jtbd, progress-making forces, push pull anxiety inertia, struggling moments

**Type:** `framework` · **Confidence:** `medium`

### Product Discovery

**Primary:** [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)

**Related:**
- [Product Discovery Frameworks](02-discovery/discovery-frameworks.md)
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [User Interviews and Interview Guides](02-discovery/user-interviews.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Product Risk](10-risk/product-risk.md)

**Keywords:** continuous discovery, customer discovery, desirable viable feasible, discovery, discovery phase, double diamond, problem framing, problem space, product discovery

**Type:** `concept` · **Confidence:** `high`

### Product Discovery Frameworks

**Primary:** [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)

**Related:**
- [Product Discovery](02-discovery/product-discovery.md)
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Brainstorming — Techniques and When to Use Them](08-ideation/brainstorming.md)
- [Product Risk](10-risk/product-risk.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)

**Keywords:** build measure learn, design sprint, double diamond, dual-track agile, jobs to be done, lean startup, mvp, opportunity solution tree

**Type:** `framework-catalogue` · **Confidence:** `medium`

### Product Opportunity Assessment

**Primary:** [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)

**Related:**
- [Product Discovery](02-discovery/product-discovery.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Identifying Unmet Customer Needs](02-discovery/identifying-unmet-needs.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Product Risk](10-risk/product-risk.md)
- [Product Strategy](04-strategy/product-strategy.md)

**Keywords:** feasibility, go / no-go, idea validation, opportunity assessment, opportunity evaluation, strategic fit, tam

**Type:** `process` · **Confidence:** `medium`

### Surveys in Product Research

**Primary:** [`02-discovery/surveys.md`](02-discovery/surveys.md)

**Related:**
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [User Interviews and Interview Guides](02-discovery/user-interviews.md)
- [Usability Testing](02-discovery/usability-testing.md)
- [Product Metrics](09-metrics/product-metrics.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)

**Keywords:** ces, csat, nps, questionnaire, seq, survey design, survey misuse, surveys, sus

**Type:** `technique` · **Confidence:** `high`

### Usability Testing

**Primary:** [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)

**Related:**
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [Surveys in Product Research](02-discovery/surveys.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [UX for Product Managers](12-design-and-ux/ux-for-product-managers.md)

**Keywords:** facilitation, five users, moderated testing, test tasks, think-aloud protocol, unmoderated testing, usability testing, user testing

**Type:** `technique` · **Confidence:** `medium`

### User Interviews and Interview Guides

**Primary:** [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)

**Related:**
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [Surveys in Product Research](02-discovery/surveys.md)
- [Identifying Unmet Customer Needs](02-discovery/identifying-unmet-needs.md)

**Keywords:** critical incident method, discussion guide, interview guide, open-ended questions, probing questions, semistructured interview, user interviews

**Type:** `technique` · **Confidence:** `high`


## 03 · Market Intelligence

### Competitive Analysis

**Primary:** [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md)

**Related:**
- [Market Research](03-market-intelligence/market-research.md)
- [Market Trend Analysis](03-market-intelligence/market-trends.md)
- [Identifying Market Needs](03-market-intelligence/market-needs.md)
- [Product Positioning](04-strategy/positioning.md)
- [Value Proposition](04-strategy/value-proposition.md)
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Risk Identification](10-risk/risk-identification.md)

**Keywords:** competitive analysis, competitor research, differentiation, direct and indirect competitors, do nothing competitor, positioning map, substitutes, swot

**Type:** `process` · **Confidence:** `medium`

### Identifying Market Needs

**Primary:** [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)

**Related:**
- [Market Research](03-market-intelligence/market-research.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)
- [Market Trend Analysis](03-market-intelligence/market-trends.md)
- [Identifying Unmet Customer Needs](02-discovery/identifying-unmet-needs.md)
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Product Value](04-strategy/product-value.md)

**Keywords:** cross-cultural research, functional emotional social needs, market needs, pain points, pestle, research bias

**Type:** `process` · **Confidence:** `medium`

### Market Research

**Primary:** [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)

**Related:**
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)
- [Market Trend Analysis](03-market-intelligence/market-trends.md)
- [Identifying Market Needs](03-market-intelligence/market-needs.md)
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [Surveys in Product Research](02-discovery/surveys.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Product Positioning](04-strategy/positioning.md)

**Keywords:** customer insights, exploratory research, focus groups, market research, market sizing, secondary research, segmentation

**Type:** `process` · **Confidence:** `medium`

### Market Trend Analysis

**Primary:** [`03-market-intelligence/market-trends.md`](03-market-intelligence/market-trends.md)

> ⚠ **Documented gap** — method named, not explained. This document records what is missing.

**Related:**
- [Market Research](03-market-intelligence/market-research.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)
- [Identifying Market Needs](03-market-intelligence/market-needs.md)
- [Product Strategy](04-strategy/product-strategy.md)
- [outdated information](99-reference/outdated-information.md)

**Keywords:** anticipating needs, emerging patterns, market trends, temporal information, trend analysis

**Type:** `technique` · **Confidence:** `low`


## 04 · Strategy

### OKRs (Objectives and Key Results)

**Primary:** [`04-strategy/okrs.md`](04-strategy/okrs.md)

**Related:**
- [Product Goals and Goal-Setting Frameworks](04-strategy/product-goals.md)
- [Product Strategy](04-strategy/product-strategy.md)
- [Product Vision (and how it differs from Mission)](04-strategy/product-vision.md)
- [Outcome-Based Roadmaps](05-planning/outcome-based-roadmaps.md)
- [North Star Metric](09-metrics/north-star-metric.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** goal setting, key results, kpi vs okr, objectives and key results, okr, outcomes over outputs

**Type:** `framework` · **Confidence:** `medium`

### Product Goals and Goal-Setting Frameworks

**Primary:** [`04-strategy/product-goals.md`](04-strategy/product-goals.md)

**Related:**
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)
- [Product Strategy](04-strategy/product-strategy.md)
- [Product Vision (and how it differs from Mission)](04-strategy/product-vision.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)
- [Outcome-Based Roadmaps](05-planning/outcome-based-roadmaps.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** dream map, framework selection, goal setting, mspot, nct, product goals, smart goals, v2mom

**Type:** `framework-catalogue` · **Confidence:** `medium`

### Product Positioning

**Primary:** [`04-strategy/positioning.md`](04-strategy/positioning.md)

> ⚠ **Documented gap** — both sources heavily truncated. This document records what is missing.

**Related:**
- [Value Proposition](04-strategy/value-proposition.md)
- [Product Strategy](04-strategy/product-strategy.md)
- [Product Vision (and how it differs from Mission)](04-strategy/product-vision.md)
- [Product Value](04-strategy/product-value.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)
- [Go-to-Market Strategy](11-lifecycle-and-launch/go-to-market.md)

**Keywords:** differentiation, messaging, perception, positioning, positioning statement, target market

**Type:** `concept` · **Confidence:** `medium`

### Product Strategy

**Primary:** [`04-strategy/product-strategy.md`](04-strategy/product-strategy.md)

**Related:**
- [Product Vision (and how it differs from Mission)](04-strategy/product-vision.md)
- [Product Goals and Goal-Setting Frameworks](04-strategy/product-goals.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)
- [Product Positioning](04-strategy/positioning.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)
- [Product Roadmap](05-planning/roadmaps.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)

**Keywords:** differentiation, product strategy, strategic imperatives, strategy components, strategy vs plan

**Type:** `concept` · **Confidence:** `medium`

### Product Value

**Primary:** [`04-strategy/product-value.md`](04-strategy/product-value.md)

**Related:**
- [Value Proposition](04-strategy/value-proposition.md)
- [Product Positioning](04-strategy/positioning.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** customer benefit, perceived value, product value, value vs price, value-price-cost

**Type:** `concept` · **Confidence:** `medium`

### Product Vision (and how it differs from Mission)

**Primary:** [`04-strategy/product-vision.md`](04-strategy/product-vision.md)

**Related:**
- [Product Strategy](04-strategy/product-strategy.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)
- [Product Goals and Goal-Setting Frameworks](04-strategy/product-goals.md)
- [Product Positioning](04-strategy/positioning.md)
- [Value Proposition](04-strategy/value-proposition.md)
- [Product Roadmap](05-planning/roadmaps.md)
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)

**Keywords:** mission statement, missionaries vs mercenaries, north star, product vision, vision vs mission, visiontype

**Type:** `concept` · **Confidence:** `high`

### Product-Led Growth and Growth Models

**Primary:** [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)

**Related:**
- [Pirate Metrics — AARRR and RARRA](09-metrics/pirate-metrics.md)
- [Product Metrics](09-metrics/product-metrics.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)
- [Go-to-Market Strategy](11-lifecycle-and-launch/go-to-market.md)
- [Product Value](04-strategy/product-value.md)

**Keywords:** free trial, freemium, growth loops, growth strategy, plg, product-led growth, sales-led growth, time to value

**Type:** `framework` · **Confidence:** `medium`

### Product-Market Fit

**Primary:** [`04-strategy/product-market-fit.md`](04-strategy/product-market-fit.md)

> ⚠ **Documented gap** — referenced constantly, defined inconsistently. This document records what is missing.

**Related:**
- [Value Proposition](04-strategy/value-proposition.md)
- [Product-Led Growth and Growth Models](04-strategy/product-led-growth.md)
- [Product Value](04-strategy/product-value.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Product Discovery](02-discovery/product-discovery.md)

**Keywords:** pmf, pmf expansion, product-market fit, sean ellis test, validation

**Type:** `concept` · **Confidence:** `low`

### Strategic Thinking and Product Decisions

**Primary:** [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)

**Related:**
- [Product Strategy](04-strategy/product-strategy.md)
- [Product Goals and Goal-Setting Frameworks](04-strategy/product-goals.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [risk analysis](10-risk/risk-assessment.md)
- [Product Risk](10-risk/product-risk.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Product Manager Skills and Competencies](01-foundations/product-manager-skills.md)

**Keywords:** decision making, one-way door, optionality, probability and consequence, reversibility, risk and reward, second-order effects, strategic thinking

**Type:** `decision-framework` · **Confidence:** `high`

### Value Proposition

**Primary:** [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)

**Related:**
- [Product Positioning](04-strategy/positioning.md)
- [Product Value](04-strategy/product-value.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Product Strategy](04-strategy/product-strategy.md)
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Competitive Analysis](03-market-intelligence/competitive-analysis.md)
- [Surveys in Product Research](02-discovery/surveys.md)

**Keywords:** 40% rule, crossing the chasm template, lean canvas, product vision board, sean ellis test, value proposition, value proposition canvas

**Type:** `framework-catalogue` · **Confidence:** `medium`


## 05 · Planning

### Backlog Management

**Primary:** [`05-planning/backlog-management.md`](05-planning/backlog-management.md)

> ⚠ **Documented gap** — refinement is covered; structure and hygiene are not. This document records what is missing.

**Related:**
- [Roadmap vs Backlog vs Release Plan](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [User Stories](06-requirements/user-stories.md)
- [Decomposition — Initiatives, Epics, Stories and Tasks](06-requirements/epics-and-decomposition.md)
- [Product Manager vs Product Owner](01-foundations/product-manager-vs-product-owner.md)

**Keywords:** backlog health, backlog ownership, backlog refinement, grooming, product backlog

**Type:** `process` · **Confidence:** `low`

### Communicating the Roadmap and Aligning Stakeholders

**Primary:** [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)

**Related:**
- [Product Roadmap](05-planning/roadmaps.md)
- [Roadmap Formats](05-planning/roadmap-formats.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Outcome-Based Roadmaps](05-planning/outcome-based-roadmaps.md)
- [Cross-Functional Product Collaboration](07-execution/product-collaboration.md)
- [North Star Metric](09-metrics/north-star-metric.md)

**Keywords:** buy-in, roadmap presentation, saying no, stakeholder alignment, stakeholder management, transparency, trust

**Type:** `technique` · **Confidence:** `medium`

### Continuous Roadmapping

**Primary:** [`05-planning/continuous-roadmapping.md`](05-planning/continuous-roadmapping.md)

**Related:**
- [Product Roadmap](05-planning/roadmaps.md)
- [Outcome-Based Roadmaps](05-planning/outcome-based-roadmaps.md)
- [Roadmap Formats](05-planning/roadmap-formats.md)
- [Roadmap vs Backlog vs Release Plan](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- [Estimation](05-planning/estimation.md)
- [North Star Metric](09-metrics/north-star-metric.md)

**Keywords:** bets, big-batch planning, continuous roadmapping, north star metric, premature convergence, rolling planning

**Type:** `technique` · **Confidence:** `medium`

### Dependencies

**Primary:** [`05-planning/dependencies.md`](05-planning/dependencies.md)

> ⚠ **Documented gap** — no source is about dependency management. This document records what is missing.

**Related:**
- [Requirements — Types and Elicitation](06-requirements/requirements.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Product Roadmap](05-planning/roadmaps.md)
- [Release Planning](05-planning/release-planning.md)
- [project risk management](10-risk/risk-management.md)
- [Working with Engineering](07-execution/working-with-engineering.md)
- [Project Monitoring and Control](07-execution/project-monitoring-and-control.md)

**Keywords:** blockers, critical path, cross-team dependencies, dependencies, dependency management, third-party dependencies

**Type:** `concept` · **Confidence:** `low`

### Estimation

**Primary:** [`05-planning/estimation.md`](05-planning/estimation.md)

> ⚠ **Documented gap** — estimation has no source in the corpus. This document records what is missing.

**Related:**
- [Prioritization Frameworks](05-planning/prioritization-frameworks.md)
- [Continuous Roadmapping](05-planning/continuous-roadmapping.md)
- [Communicating the Roadmap and Aligning Stakeholders](05-planning/roadmap-communication.md)
- [Decomposition — Initiatives, Epics, Stories and Tasks](06-requirements/epics-and-decomposition.md)
- [Working with Engineering](07-execution/working-with-engineering.md)

**Keywords:** effort, estimation, forecasting, planning poker, story points, t-shirt sizing, velocity

**Type:** `concept` · **Confidence:** `low`

### Outcome-Based Roadmaps

**Primary:** [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md)

**Related:**
- [Product Roadmap](05-planning/roadmaps.md)
- [Roadmap Formats](05-planning/roadmap-formats.md)
- [Continuous Roadmapping](05-planning/continuous-roadmapping.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)
- [Product Goals and Goal-Setting Frameworks](04-strategy/product-goals.md)
- [Product Strategy](04-strategy/product-strategy.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** feature factory, go product roadmap, goal-oriented roadmap, outcome-based roadmap, outcomes over outputs, roadmap transition

**Type:** `framework` · **Confidence:** `high`

### Prioritization Frameworks

**Primary:** [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)

**Related:**
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Product Roadmap](05-planning/roadmaps.md)
- [Backlog Management](05-planning/backlog-management.md)
- [Estimation](05-planning/estimation.md)
- [Product Discovery Frameworks](02-discovery/discovery-frameworks.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** cost of delay, kano model, moscow, opportunity scoring, prioritization matrix, rice, value vs effort, weighted scoring, wsjf

**Type:** `framework-catalogue` · **Confidence:** `medium`

### Prioritization — The Practice

**Primary:** [`05-planning/prioritization.md`](05-planning/prioritization.md)

**Related:**
- [Prioritization Frameworks](05-planning/prioritization-frameworks.md)
- [Product Roadmap](05-planning/roadmaps.md)
- [Backlog Management](05-planning/backlog-management.md)
- [Communicating the Roadmap and Aligning Stakeholders](05-planning/roadmap-communication.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Identifying Unmet Customer Needs](02-discovery/identifying-unmet-needs.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)

**Keywords:** bias, decision making, feature requests, kill condition, prioritization, saying no, trade-offs

**Type:** `process` · **Confidence:** `medium`

### Product Roadmap

**Primary:** [`05-planning/roadmaps.md`](05-planning/roadmaps.md)

**Related:**
- [Outcome-Based Roadmaps](05-planning/outcome-based-roadmaps.md)
- [Roadmap Formats](05-planning/roadmap-formats.md)
- [Continuous Roadmapping](05-planning/continuous-roadmapping.md)
- [Communicating the Roadmap and Aligning Stakeholders](05-planning/roadmap-communication.md)
- [Roadmap vs Backlog vs Release Plan](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Product Strategy](04-strategy/product-strategy.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)

**Keywords:** product plan, product roadmap, roadmap, roadmap audiences, roadmap ownership, strategic communication, strategic roadmap, themes

**Type:** `artifact` · **Confidence:** `high`

### Release Planning

**Primary:** [`05-planning/release-planning.md`](05-planning/release-planning.md)

> ⚠ **Documented gap** — two sentences across two sources, which contradict each other. This document records what is missing.

**Related:**
- [Roadmap vs Backlog vs Release Plan](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- [Roadmap Formats](05-planning/roadmap-formats.md)
- [Dependencies](05-planning/dependencies.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Scope Definition and Scope Creep](06-requirements/scope-definition.md)
- [Product Launch](11-lifecycle-and-launch/product-launch.md)

**Keywords:** launch readiness, milestones, release criteria, release notes, release plan

**Type:** `process` · **Confidence:** `low`

### Roadmap Formats

**Primary:** [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)

**Related:**
- [Product Roadmap](05-planning/roadmaps.md)
- [Outcome-Based Roadmaps](05-planning/outcome-based-roadmaps.md)
- [Continuous Roadmapping](05-planning/continuous-roadmapping.md)
- [Communicating the Roadmap and Aligning Stakeholders](05-planning/roadmap-communication.md)
- [Roadmap vs Backlog vs Release Plan](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- [The Agile Manifesto](07-execution/agile-manifesto.md)

**Keywords:** agile roadmap, kanban roadmap, now next later, roadmap format selection, sprint roadmap, theme-based roadmap, timeline roadmap

**Type:** `framework-catalogue` · **Confidence:** `medium`

### Roadmap vs Backlog vs Release Plan

**Primary:** [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)

**Related:**
- [Product Roadmap](05-planning/roadmaps.md)
- [Backlog Management](05-planning/backlog-management.md)
- [Release Planning](05-planning/release-planning.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Outcome-Based Roadmaps](05-planning/outcome-based-roadmaps.md)
- [Decomposition — Initiatives, Epics, Stories and Tasks](06-requirements/epics-and-decomposition.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)

**Keywords:** altitude, planning artifacts, product backlog, release plan, roadmap vs backlog, strategy vs execution

**Type:** `comparison` · **Confidence:** `medium`


## 06 · Requirements

### Acceptance Criteria and Definition of Done

**Primary:** [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md)

**Related:**
- [User Stories](06-requirements/user-stories.md)
- [Job Stories and When to Prefer Them Over User Stories](06-requirements/job-stories.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Requirements — Types and Elicitation](06-requirements/requirements.md)
- [Backlog Management](05-planning/backlog-management.md)
- [Release Planning](05-planning/release-planning.md)

**Keywords:** acceptance criteria, confirmation, definition of done, release criteria, testable requirements

**Type:** `artifact` · **Confidence:** `medium`

### Decomposition — Initiatives, Epics, Stories and Tasks

**Primary:** [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md)

**Related:**
- [User Stories](06-requirements/user-stories.md)
- [Job Stories and When to Prefer Them Over User Stories](06-requirements/job-stories.md)
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [Scope Definition and Scope Creep](06-requirements/scope-definition.md)
- [Backlog Management](05-planning/backlog-management.md)
- [Estimation](05-planning/estimation.md)
- [Product Roadmap](05-planning/roadmaps.md)

**Keywords:** decomposition, epic, hierarchy, initiative, story splitting, task, work breakdown

**Type:** `concept` · **Confidence:** `medium`

### Job Stories and When to Prefer Them Over User Stories

**Primary:** [`06-requirements/job-stories.md`](06-requirements/job-stories.md)

**Related:**
- [User Stories](06-requirements/user-stories.md)
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [Jobs to be Done (JTBD)](02-discovery/jobs-to-be-done.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)

**Keywords:** backlog item format, job story, jtbd, trigger motivation outcome, user story vs job story

**Type:** `artifact` · **Confidence:** `high`

### Product Requirements Document (PRD)

**Primary:** [`06-requirements/prd.md`](06-requirements/prd.md)

**Related:**
- [Requirements — Types and Elicitation](06-requirements/requirements.md)
- [User Stories](06-requirements/user-stories.md)
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [Scope Definition and Scope Creep](06-requirements/scope-definition.md)
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [Release Planning](05-planning/release-planning.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)

**Keywords:** agile documentation, brd, mrd, prd, product requirements document, product spec, requirements doc, requirements documentation, specification

**Type:** `artifact` · **Confidence:** `high`

### Requirements — Types and Elicitation

**Primary:** [`06-requirements/requirements.md`](06-requirements/requirements.md)

**Related:**
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [User Stories](06-requirements/user-stories.md)
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [Scope Definition and Scope Creep](06-requirements/scope-definition.md)
- [Decomposition — Initiatives, Epics, Stories and Tasks](06-requirements/epics-and-decomposition.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Working with Engineering](07-execution/working-with-engineering.md)

**Keywords:** constraints, dependencies, functional requirements, non-functional requirements, requirements, requirements elicitation, requirements gathering

**Type:** `concept` · **Confidence:** `medium`

### Scope Definition and Scope Creep

**Primary:** [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md)

**Related:**
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Requirements — Types and Elicitation](06-requirements/requirements.md)
- [Decomposition — Initiatives, Epics, Stories and Tasks](06-requirements/epics-and-decomposition.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Release Planning](05-planning/release-planning.md)
- [Project Monitoring and Control](07-execution/project-monitoring-and-control.md)
- [project risk management](10-risk/risk-management.md)

**Keywords:** boundaries, change requests, features out, out of scope, scope, scope creep

**Type:** `concept` · **Confidence:** `medium`

### User Stories

**Primary:** [`06-requirements/user-stories.md`](06-requirements/user-stories.md)

**Related:**
- [Job Stories and When to Prefer Them Over User Stories](06-requirements/job-stories.md)
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [Decomposition — Initiatives, Epics, Stories and Tasks](06-requirements/epics-and-decomposition.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Requirements — Types and Elicitation](06-requirements/requirements.md)
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [Backlog Management](05-planning/backlog-management.md)

**Keywords:** backlog refinement, card conversation confirmation, epic, story mapping, story splitting, story template, story vs task, user stories

**Type:** `artifact` · **Confidence:** `high`


## 07 · Execution

### Scrum  **[E]**

**Primary:** [`07-execution/scrum.md`](07-execution/scrum.md)

**Related:**
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [Kanban (the Kanban Method)](07-execution/kanban.md)
- [Product Manager vs Product Owner](01-foundations/product-manager-vs-product-owner.md)
- [User Stories](06-requirements/user-stories.md)
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [Backlog Management](05-planning/backlog-management.md)
- [Estimation](05-planning/estimation.md)

**Keywords:** scrum, sprint, sprint planning, sprint goal, sprint review, sprint retrospective, retrospective, daily scrum, stand-up, product owner, scrum master, developers, scrum team, product backlog, sprint backlog, increment, definition of done, product goal, scrum events, scrum ceremonies, scrum artifacts, scrum accountabilities, timebox, empiricism, transparency inspection adaptation, scrum values, scrum guide

**Type:** `framework` · **Confidence:** `high` · **Provenance:** `primary` [E001]

### Kanban (the Kanban Method)  **[E]**

**Primary:** [`07-execution/kanban.md`](07-execution/kanban.md)

**Related:**
- [Scrum](07-execution/scrum.md)
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [Project Monitoring and Control](07-execution/project-monitoring-and-control.md)
- [Estimation](05-planning/estimation.md)
- [Prioritization Frameworks](05-planning/prioritization-frameworks.md)
- [Roadmap Formats](05-planning/roadmap-formats.md)
- [Dependencies](05-planning/dependencies.md)

**Keywords:** kanban, kanban method, kanban system, kanban board, wip limits, work in progress, pull system, push system, flow, manage flow, lead time, cycle time, delivery rate, throughput, cumulative flow diagram, little's law, cost of delay, classes of service, expedite fixed date standard intangible, explicit policies, cadences, replenishment meeting, kanban meeting, service delivery review, statik, kanban litmus test, service request manager, service delivery manager, service level expectation, service level agreement, probabilistic forecasting, monte carlo, evolutionary change, start with what you do now, bottleneck, blocker

**Type:** `framework` · **Confidence:** `high` · **Provenance:** `primary` [E003], [E004]

### Cross-Functional Product Collaboration

**Primary:** [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)

**Related:**
- [Working with Engineering](07-execution/working-with-engineering.md)
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [The Product Development Process](07-execution/product-development-process.md)
- [PM and UX Role Boundaries (Survey Evidence)](01-foundations/pm-and-ux-collaboration.md)
- [Communicating the Roadmap and Aligning Stakeholders](05-planning/roadmap-communication.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)

**Keywords:** cross-functional teams, over-collaboration, product collaboration, shared vision, stopping work, team structure

**Type:** `practice` · **Confidence:** `medium`

### Project Monitoring and Control

**Primary:** [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)

**Related:**
- [The Product Development Process](07-execution/product-development-process.md)
- [Working with Engineering](07-execution/working-with-engineering.md)
- [Risk Monitoring and Control](10-risk/risk-monitoring.md)
- [Scope Definition and Scope Creep](06-requirements/scope-definition.md)
- [Dependencies](05-planning/dependencies.md)
- [Product Management vs Project Management](01-foundations/product-vs-project-management.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** change requests, corrective action, kpis, project control, project monitoring, scope monitoring

**Type:** `process` · **Confidence:** `medium`

### The Agile Manifesto

**Primary:** [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)

**Related:**
- [Working with Engineering](07-execution/working-with-engineering.md)
- [The Product Development Process](07-execution/product-development-process.md)
- [User Stories](06-requirements/user-stories.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Roadmap Formats](05-planning/roadmap-formats.md)
- [Product Manager vs Product Owner](01-foundations/product-manager-vs-product-owner.md)

**Keywords:** agile manifesto, agile values, cargo cult agile, faux agile, snowbird, twelve principles

**Type:** `primary-text` · **Confidence:** `high`

### The Product Development Process

**Primary:** [`07-execution/product-development-process.md`](07-execution/product-development-process.md)

**Related:**
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [Working with Engineering](07-execution/working-with-engineering.md)
- [Project Monitoring and Control](07-execution/project-monitoring-and-control.md)
- [Product Discovery Frameworks](02-discovery/discovery-frameworks.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [The Product Lifecycle](11-lifecycle-and-launch/product-lifecycle.md)

**Keywords:** design phase, development phase, launch and iteration, opportunity validation, product development process, strategic fit

**Type:** `process` · **Confidence:** `medium`

### Working with Engineering

**Primary:** [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)

**Related:**
- [The Agile Manifesto](07-execution/agile-manifesto.md)
- [Cross-Functional Product Collaboration](07-execution/product-collaboration.md)
- [The Product Development Process](07-execution/product-development-process.md)
- [Product Manager Skills and Competencies](01-foundations/product-manager-skills.md)
- [User Stories](06-requirements/user-stories.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Estimation](05-planning/estimation.md)
- [The Product Triad (Desirable, Viable, Feasible)](12-design-and-ux/product-triad.md)

**Keywords:** engineering collaboration, product manager vs engineering manager, requirements clarity, technical feasibility, technical fluency, working with engineers

**Type:** `practice` · **Confidence:** `medium`


## 08 · Ideation

### Brainstorming — Techniques and When to Use Them

**Primary:** [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)

**Related:**
- [Brainwriting and the 6-3-5 Method](08-ideation/brainwriting.md)
- [Mind Mapping](08-ideation/mind-mapping.md)
- [SCAMPER](08-ideation/scamper.md)
- [Evaluating and Converging on Ideas](08-ideation/idea-evaluation.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [Risk Identification](10-risk/risk-identification.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)

**Keywords:** 5 whys, affinity mapping, brainstorming, divergence and convergence, rapid ideation, reverse brainstorming, round robin, starbursting

**Type:** `technique-catalogue` · **Confidence:** `medium`

### Brainwriting and the 6-3-5 Method

**Primary:** [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)

**Related:**
- [Brainstorming — Techniques and When to Use Them](08-ideation/brainstorming.md)
- [Evaluating and Converging on Ideas](08-ideation/idea-evaluation.md)
- [Mind Mapping](08-ideation/mind-mapping.md)
- [SCAMPER](08-ideation/scamper.md)
- [Risk Identification](10-risk/risk-identification.md)
- [Product Discovery](02-discovery/product-discovery.md)

**Keywords:** 6-3-5 method, brainwriting, introvert participation, nominal group technique, production blocking, rohrbach, silent ideation

**Type:** `technique` · **Confidence:** `high`

### Evaluating and Converging on Ideas

**Primary:** [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)

**Related:**
- [Brainstorming — Techniques and When to Use Them](08-ideation/brainstorming.md)
- [Brainwriting and the 6-3-5 Method](08-ideation/brainwriting.md)
- [SCAMPER](08-ideation/scamper.md)
- [Mind Mapping](08-ideation/mind-mapping.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Prioritization Frameworks](05-planning/prioritization-frameworks.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)

**Keywords:** affinity mapping, convergence, dot voting, idea evaluation, idea to action, nominal group technique, screening

**Type:** `process` · **Confidence:** `medium`

### Mind Mapping

**Primary:** [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)

**Related:**
- [Brainstorming — Techniques and When to Use Them](08-ideation/brainstorming.md)
- [Brainwriting and the 6-3-5 Method](08-ideation/brainwriting.md)
- [Evaluating and Converging on Ideas](08-ideation/idea-evaluation.md)
- [User Interviews and Interview Guides](02-discovery/user-interviews.md)

**Keywords:** associative structure, bubble map, concept map, mind map, tree map, visual thinking

**Type:** `technique` · **Confidence:** `medium`

### SCAMPER

**Primary:** [`08-ideation/scamper.md`](08-ideation/scamper.md)

**Related:**
- [Brainstorming — Techniques and When to Use Them](08-ideation/brainstorming.md)
- [Brainwriting and the 6-3-5 Method](08-ideation/brainwriting.md)
- [Mind Mapping](08-ideation/mind-mapping.md)
- [Evaluating and Converging on Ideas](08-ideation/idea-evaluation.md)
- [Product Discovery Frameworks](02-discovery/discovery-frameworks.md)

**Keywords:** eberle, force-fitting, idea transformation, osborn, scamper, substitute combine adapt

**Type:** `technique` · **Confidence:** `medium`


## 09 · Metrics

### North Star Metric

**Primary:** [`09-metrics/north-star-metric.md`](09-metrics/north-star-metric.md)

> ⚠ **Documented gap** — referenced by four sources, defined by none. This document records what is missing.

**Related:**
- [Product Metrics](09-metrics/product-metrics.md)
- [Pirate Metrics — AARRR and RARRA](09-metrics/pirate-metrics.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)
- [Product Vision (and how it differs from Mission)](04-strategy/product-vision.md)
- [Communicating the Roadmap and Aligning Stakeholders](05-planning/roadmap-communication.md)
- [Continuous Roadmapping](05-planning/continuous-roadmapping.md)

**Keywords:** guiding metric, metric alignment, north star metric

**Type:** `concept` · **Confidence:** `low`

### Pirate Metrics — AARRR and RARRA

**Primary:** [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)

**Related:**
- [Product Metrics](09-metrics/product-metrics.md)
- [North Star Metric](09-metrics/north-star-metric.md)
- [Product-Led Growth and Growth Models](04-strategy/product-led-growth.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)

**Keywords:** aarrr, acquisition activation retention referral revenue, funnel, pirate metrics, rarra, retention-first

**Type:** `framework` · **Confidence:** `medium`

### Product Metrics

**Primary:** [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)

> ⚠ **Documented gap** — definitions only; no measurement design. This document records what is missing.

**Related:**
- [Pirate Metrics — AARRR and RARRA](09-metrics/pirate-metrics.md)
- [North Star Metric](09-metrics/north-star-metric.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)
- [Product Goals and Goal-Setting Frameworks](04-strategy/product-goals.md)
- [Surveys in Product Research](02-discovery/surveys.md)
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [Prioritization — The Practice](05-planning/prioritization.md)

**Keywords:** activation, ces, churn, conversion, csat, kpi, nps, outcomes over outputs, product metrics, retention, vanity metrics

**Type:** `concept` · **Confidence:** `low`


## 10 · Risk

### Assumptions and Constraints as Risk Sources

**Primary:** [`10-risk/assumptions-and-constraints.md`](10-risk/assumptions-and-constraints.md)

**Related:**
- [Risk Identification](10-risk/risk-identification.md)
- [Risk Management — Foundations](10-risk/risk-management.md)
- [Product Risk](10-risk/product-risk.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Requirements — Types and Elicitation](06-requirements/requirements.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [Dependencies](05-planning/dependencies.md)

**Keywords:** assumption analysis, assumption log, assumptions, constraints, unconscious assumptions

**Type:** `concept` · **Confidence:** `medium`

### IT and Security Risk Assessment

**Primary:** [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)

**Related:**
- [Risk Assessment and Analysis](10-risk/risk-assessment.md)
- [Risk Response Strategies](10-risk/risk-response.md)
- [Product Risk](10-risk/product-risk.md)
- [Product Opportunity Assessment](02-discovery/opportunity-assessment.md)
- [Prioritization Frameworks](05-planning/prioritization-frameworks.md)
- [Working with Engineering](07-execution/working-with-engineering.md)

**Keywords:** compliance, controls, impact analysis, it risk, nist, security risk, threats and vulnerabilities

**Type:** `process` · **Confidence:** `medium`

### Product Risk

**Primary:** [`10-risk/product-risk.md`](10-risk/product-risk.md)

**Related:**
- [Risk Management — Foundations](10-risk/risk-management.md)
- [Risk Assessment and Analysis](10-risk/risk-assessment.md)
- [Risk Response Strategies](10-risk/risk-response.md)
- [Assumptions and Constraints as Risk Sources](10-risk/assumptions-and-constraints.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)

**Keywords:** assumption mapping, product failure modes, product risk, product vs project vs business risk, risk vs evidence grid

**Type:** `concept` · **Confidence:** `medium`

### Risk Assessment and Analysis

**Primary:** [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)

**Related:**
- [Risk Management — Foundations](10-risk/risk-management.md)
- [Risk Identification](10-risk/risk-identification.md)
- [Risk Response Strategies](10-risk/risk-response.md)
- [Risk Monitoring and Control](10-risk/risk-monitoring.md)
- [IT and Security Risk Assessment](10-risk/it-and-security-risk.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)

**Keywords:** 5 whys, probability and impact matrix, qualitative risk analysis, quantitative risk analysis, risk assessment, risk data quality, risk score

**Type:** `process` · **Confidence:** `high`

### Risk Identification

**Primary:** [`10-risk/risk-identification.md`](10-risk/risk-identification.md)

**Related:**
- [Risk Management — Foundations](10-risk/risk-management.md)
- [Risk Assessment and Analysis](10-risk/risk-assessment.md)
- [Risk Response Strategies](10-risk/risk-response.md)
- [Product Risk](10-risk/product-risk.md)
- [Assumptions and Constraints as Risk Sources](10-risk/assumptions-and-constraints.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Brainstorming — Techniques and When to Use Them](08-ideation/brainstorming.md)

**Keywords:** assumptions analysis, barriers to identification, delphi technique, risk identification, risk register, root cause analysis, swot

**Type:** `process` · **Confidence:** `high`

### Risk Management — Foundations

**Primary:** [`10-risk/risk-management.md`](10-risk/risk-management.md)

**Related:**
- [Risk Identification](10-risk/risk-identification.md)
- [Risk Assessment and Analysis](10-risk/risk-assessment.md)
- [Risk Response Strategies](10-risk/risk-response.md)
- [Risk Monitoring and Control](10-risk/risk-monitoring.md)
- [Product Risk](10-risk/product-risk.md)
- [Assumptions and Constraints as Risk Sources](10-risk/assumptions-and-constraints.md)
- [Hypotheses, Assumptions and Validation](02-discovery/hypotheses-and-assumptions.md)
- [Project Monitoring and Control](07-execution/project-monitoring-and-control.md)

**Keywords:** positive risk, project risk, risk definition, risk management, risk management plan, risk register, risk tolerance

**Type:** `concept` · **Confidence:** `high`

### Risk Monitoring and Control

**Primary:** [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)

**Related:**
- [Risk Management — Foundations](10-risk/risk-management.md)
- [Risk Identification](10-risk/risk-identification.md)
- [Risk Assessment and Analysis](10-risk/risk-assessment.md)
- [Risk Response Strategies](10-risk/risk-response.md)
- [Product Risk](10-risk/product-risk.md)
- [Project Monitoring and Control](07-execution/project-monitoring-and-control.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)

**Keywords:** audits, earned value, proactive monitoring, reserve analysis, risk monitoring, risk register updates, risk triggers

**Type:** `process` · **Confidence:** `medium`

### Risk Response Strategies

**Primary:** [`10-risk/risk-response.md`](10-risk/risk-response.md)

**Related:**
- [Risk Management — Foundations](10-risk/risk-management.md)
- [Risk Assessment and Analysis](10-risk/risk-assessment.md)
- [Risk Monitoring and Control](10-risk/risk-monitoring.md)
- [Product Risk](10-risk/product-risk.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)

**Keywords:** accept, avoid, enhance, escalate, exploit, mitigate, residual risk, risk response, share, transfer

**Type:** `framework` · **Confidence:** `high`


## 11 · Lifecycle & Launch

### Decline and End-of-Life

**Primary:** [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)

**Related:**
- [The Product Lifecycle](11-lifecycle-and-launch/product-lifecycle.md)
- [Managing a Mature Product](11-lifecycle-and-launch/managing-maturity.md)
- [Product Launch](11-lifecycle-and-launch/product-launch.md)
- [Prioritization — The Practice](05-planning/prioritization.md)
- [Product Risk](10-risk/product-risk.md)
- [Product Strategy](04-strategy/product-strategy.md)

**Keywords:** decline stage, deprecation, end of life, eol, product retirement, reversibility, sunsetting

**Type:** `process` · **Confidence:** `medium`

### Go-to-Market Strategy

**Primary:** [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)

**Related:**
- [Product Launch](11-lifecycle-and-launch/product-launch.md)
- [The Product Lifecycle](11-lifecycle-and-launch/product-lifecycle.md)
- [Product Positioning](04-strategy/positioning.md)
- [Value Proposition](04-strategy/value-proposition.md)
- [Product-Led Growth and Growth Models](04-strategy/product-led-growth.md)
- [Market Research](03-market-intelligence/market-research.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** channels, enablement, go-to-market, gtm, gtm motion, icp, pricing and packaging

**Type:** `framework` · **Confidence:** `medium`

### Managing a Mature Product

**Primary:** [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)

**Related:**
- [The Product Lifecycle](11-lifecycle-and-launch/product-lifecycle.md)
- [Decline and End-of-Life](11-lifecycle-and-launch/decline-and-end-of-life.md)
- [Backlog Management](05-planning/backlog-management.md)
- [OKRs (Objectives and Key Results)](04-strategy/okrs.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)

**Keywords:** backlog beast, feature factory, hackathon, innovation lab, innovation time, maturity stage, self-disruption

**Type:** `practice` · **Confidence:** `medium`

### Product Launch

**Primary:** [`11-lifecycle-and-launch/product-launch.md`](11-lifecycle-and-launch/product-launch.md)

**Related:**
- [Go-to-Market Strategy](11-lifecycle-and-launch/go-to-market.md)
- [The Product Lifecycle](11-lifecycle-and-launch/product-lifecycle.md)
- [Release Planning](05-planning/release-planning.md)
- [Product Risk](10-risk/product-risk.md)
- [Strategic Thinking and Product Decisions](04-strategy/strategic-thinking.md)
- [Product Metrics](09-metrics/product-metrics.md)
- [Product Positioning](04-strategy/positioning.md)

**Keywords:** beta program, launch metrics, launch plan, launch types, post-launch retrospective, product launch

**Type:** `process` · **Confidence:** `medium`

### The Product Lifecycle

**Primary:** [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)

**Related:**
- [Managing a Mature Product](11-lifecycle-and-launch/managing-maturity.md)
- [Decline and End-of-Life](11-lifecycle-and-launch/decline-and-end-of-life.md)
- [Product Launch](11-lifecycle-and-launch/product-launch.md)
- [Go-to-Market Strategy](11-lifecycle-and-launch/go-to-market.md)
- [Product-Market Fit](04-strategy/product-market-fit.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)
- [The Product Development Process](07-execution/product-development-process.md)

**Keywords:** introduction growth maturity decline, mlp, plc, product lifecycle, saturation, theodore levitt

**Type:** `framework` · **Confidence:** `medium`


## 12 · Design & UX

### Product Design Fundamentals for Product Managers

**Primary:** [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)

**Related:**
- [UX for Product Managers](12-design-and-ux/ux-for-product-managers.md)
- [The Product Triad (Desirable, Viable, Feasible)](12-design-and-ux/product-triad.md)
- [Service Design](12-design-and-ux/service-design.md)
- [Usability Testing](02-discovery/usability-testing.md)
- [Product Requirements Document (PRD)](06-requirements/prd.md)
- [PM and UX Role Boundaries (Survey Evidence)](01-foundations/pm-and-ux-collaboration.md)

**Keywords:** design principles, design process, mockups, pm and designer collaboration, product design, prototypes, wireframes

**Type:** `concept` · **Confidence:** `medium`

### Service Design

**Primary:** [`12-design-and-ux/service-design.md`](12-design-and-ux/service-design.md)

**Related:**
- [The Product Triad (Desirable, Viable, Feasible)](12-design-and-ux/product-triad.md)
- [UX for Product Managers](12-design-and-ux/ux-for-product-managers.md)
- [Product Design Fundamentals for Product Managers](12-design-and-ux/product-design-fundamentals.md)
- [Product Discovery](02-discovery/product-discovery.md)
- [Product Management Specializations and Types of Product Work](01-foundations/pm-specializations.md)
- [Product Risk](10-risk/product-risk.md)

**Keywords:** frontstage backstage, goods-services continuum, internal processes, people props processes, service blueprint, service design

**Type:** `concept` · **Confidence:** `medium`

### The Product Triad (Desirable, Viable, Feasible)

**Primary:** [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)

**Related:**
- [UX for Product Managers](12-design-and-ux/ux-for-product-managers.md)
- [Product Design Fundamentals for Product Managers](12-design-and-ux/product-design-fundamentals.md)
- [PM and UX Role Boundaries (Survey Evidence)](01-foundations/pm-and-ux-collaboration.md)
- [Product Manager Role and Responsibilities](01-foundations/product-manager-role.md)
- [Product Management](01-foundations/product-management.md)
- [Working with Engineering](07-execution/working-with-engineering.md)
- [Product Discovery](02-discovery/product-discovery.md)

**Keywords:** cross-functional ownership, desirable viable feasible, dvf, ideo, product triad, product trio, three-legged stool

**Type:** `framework` · **Confidence:** `high`

### UX for Product Managers

**Primary:** [`12-design-and-ux/ux-for-product-managers.md`](12-design-and-ux/ux-for-product-managers.md)

**Related:**
- [PM and UX Role Boundaries (Survey Evidence)](01-foundations/pm-and-ux-collaboration.md)
- [Product Design Fundamentals for Product Managers](12-design-and-ux/product-design-fundamentals.md)
- [The Product Triad (Desirable, Viable, Feasible)](12-design-and-ux/product-triad.md)
- [Service Design](12-design-and-ux/service-design.md)
- [Choosing a User Research Method](02-discovery/user-research-methods.md)
- [Usability Testing](02-discovery/usability-testing.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** pm and ux boundary, usability, user experience, ux for pms, ux metrics

**Type:** `concept` · **Confidence:** `medium`

---

## 13 · AI Agent Collaboration  **[E — Phase 2 external research]**

> **Entry point: read [the evidence document](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) first.**
> The rest of this domain is downstream of what has actually been measured, which is very little.

### What the Evidence Says About AI-Assisted Software Delivery

**Primary:** [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)

**Related:**
- [PM When the Implementer Is an Agent](13-ai-agent-collaboration/pm-with-ai-implementers.md)
- [Open Questions](13-ai-agent-collaboration/open-questions-ai-and-pm.md)
- [Product Metrics](09-metrics/product-metrics.md)
- [Estimation](05-planning/estimation.md)
- [Kanban](07-execution/kanban.md)

**Keywords:** does ai make developers faster, ai productivity evidence, metr study, 19% slower, perception gap, developer productivity, dora report, ai amplifier, delivery instability, verification tax, j-curve, user-centric focus, small batches, ai capabilities model, ai adoption, trust in ai code, ai roi

**Type:** `evidence-review` · **Confidence:** `medium` · **Provenance:** `empirical` [E006], [E007], [E008]

### Product Management When the Implementer Is an Agent  ⚠

**Primary:** [`13-ai-agent-collaboration/pm-with-ai-implementers.md`](13-ai-agent-collaboration/pm-with-ai-implementers.md)

> ⚠ **`confidence: low`, `verified: partial`.** Five of its seven claims are labelled `[INFERENCE]`.
> **No source studies the PM role under agent implementation.**

**Related:**
- [What the Evidence Says](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- [Spec-Driven Development](13-ai-agent-collaboration/spec-driven-development.md)
- [Evals and Acceptance for Agents](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- [Open Questions](13-ai-agent-collaboration/open-questions-ai-and-pm.md)
- [Working with Engineering](07-execution/working-with-engineering.md)
- [Kanban](07-execution/kanban.md)

**Keywords:** ai agents as team members, working with ai agents, managing ai agents, pm and ai agents, agentic development, agent implementer, directing agents, tacit knowledge, standing context, project constitution, review bottleneck, batch size and ai, what changes for a pm with ai

**Type:** `analysis` · **Confidence:** `low` · **Provenance:** `empirical` [E008] · `practice` [E011]–[E013]

### Spec-Driven Development  ⚠

**Primary:** [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)

> ⚠ Widely adopted; **no efficacy evidence exists in this knowledge base.**

**Related:**
- [PRD](06-requirements/prd.md)
- [Requirements](06-requirements/requirements.md)
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [User Stories](06-requirements/user-stories.md)
- [Evals and Acceptance for Agents](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- [Epics and Decomposition](06-requirements/epics-and-decomposition.md)

**Keywords:** spec-driven development, sdd, spec first, specification as source of truth, spec kit, speckit, kiro, ears, easy approach to requirements syntax, the system shall, requirements.md design.md tasks.md, constitution, converge, vibe coding, writing specs for ai, agent instructions, unwanted behaviour requirement

**Type:** `practice` · **Confidence:** `medium` · **Provenance:** `primary` [E012]–[E014] · `practice`

### Evals and Acceptance When the Implementer Is an Agent

**Primary:** [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)

**Related:**
- [Acceptance Criteria and Definition of Done](06-requirements/acceptance-criteria.md)
- [Spec-Driven Development](13-ai-agent-collaboration/spec-driven-development.md)
- [Risk Response](10-risk/risk-response.md)
- [Risk Monitoring and Control](10-risk/risk-monitoring.md)
- [Product Metrics](09-metrics/product-metrics.md)

**Keywords:** evals, evaluations, evaluating ai agents, testing ai agents, capability evals, regression evals, llm as judge, model-based grader, code-based grader, human grader, pass@k, pass^k, eval saturation, swiss cheese model, transcript, partial credit, non-determinism, acceptance for agents, verification

**Type:** `practice` · **Confidence:** `medium` · **Provenance:** `practice` [E011]

### Open Questions — Product Management and AI Agents  ❌

**Primary:** [`13-ai-agent-collaboration/open-questions-ai-and-pm.md`](13-ai-agent-collaboration/open-questions-ai-and-pm.md)

> **24 questions with no answer in this knowledge base**, and what evidence would settle each.
> **Retrieve this when a question about PM and AI agents does not resolve elsewhere** — "I don't
> know, and here is what would have to be true to know" is the correct answer, not silence.

**Related:**
- [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md)
- [What the Evidence Says](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- [99-reference/disputed-information.md](99-reference/disputed-information.md)

**Keywords:** what we do not know, open questions ai pm, unanswered, multi-agent team organisation, junior roles ai, defect rate ai code, cost of agent implementation, accessibility gap, research needed

**Type:** `gap-register` · **Confidence:** `high` (that these are open)

---

## Alphabetical lookup

**633 concept terms** resolving directly to documents.

**#**
#- 40% rule → [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)
- 5 whys → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md) · [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- 6-3-5 method → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)


**A**
A- aarrr → [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)
- accept → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- acceptance criteria and definition of done → [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md)
- acceptance criteria → [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md)
- acceptance for ai agents → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- acquisition activation retention referral revenue → [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)
- activation → [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- affinity mapping → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md) · [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- agent evaluation → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- agents as team members → [`13-ai-agent-collaboration/pm-with-ai-implementers.md`](13-ai-agent-collaboration/pm-with-ai-implementers.md)
- agile documentation → [`06-requirements/prd.md`](06-requirements/prd.md)
- agile manifesto → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- agile roadmap → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- agile values → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- ai adoption evidence → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- ai agents → [`13-ai-agent-collaboration/pm-with-ai-implementers.md`](13-ai-agent-collaboration/pm-with-ai-implementers.md) · [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- ai amplifier → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- ai capabilities model (dora) → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- ai coding productivity → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- altitude → [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- anticipating needs → [`03-market-intelligence/market-trends.md`](03-market-intelligence/market-trends.md)
- associative structure → [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)
- assumption analysis → [`10-risk/assumptions-and-constraints.md`](10-risk/assumptions-and-constraints.md)
- assumption log → [`10-risk/assumptions-and-constraints.md`](10-risk/assumptions-and-constraints.md)
- assumption mapping → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md) · [`10-risk/product-risk.md`](10-risk/product-risk.md)
- assumption testing → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)
- assumptions analysis → [`10-risk/risk-identification.md`](10-risk/risk-identification.md)
- assumptions and constraints as risk sources → [`10-risk/assumptions-and-constraints.md`](10-risk/assumptions-and-constraints.md)
- assumptions → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md) · [`10-risk/assumptions-and-constraints.md`](10-risk/assumptions-and-constraints.md)
- attitudinal vs behavioral → [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)
- audits → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- avoid → [`10-risk/risk-response.md`](10-risk/risk-response.md)


**B**
B- backlog beast → [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- backlog health → [`05-planning/backlog-management.md`](05-planning/backlog-management.md)
- backlog item format → [`06-requirements/job-stories.md`](06-requirements/job-stories.md)
- backlog management → [`05-planning/backlog-management.md`](05-planning/backlog-management.md)
- backlog ownership → [`01-foundations/product-manager-vs-product-owner.md`](01-foundations/product-manager-vs-product-owner.md) · [`05-planning/backlog-management.md`](05-planning/backlog-management.md)
- backlog refinement → [`05-planning/backlog-management.md`](05-planning/backlog-management.md) · [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- barriers to identification → [`10-risk/risk-identification.md`](10-risk/risk-identification.md)
- beta program → [`11-lifecycle-and-launch/product-launch.md`](11-lifecycle-and-launch/product-launch.md)
- bets → [`05-planning/continuous-roadmapping.md`](05-planning/continuous-roadmapping.md)
- bias → [`05-planning/prioritization.md`](05-planning/prioritization.md)
- big-batch planning → [`05-planning/continuous-roadmapping.md`](05-planning/continuous-roadmapping.md)
- blocker (vs bottleneck) → [`07-execution/kanban.md`](07-execution/kanban.md)
- blockers → [`05-planning/dependencies.md`](05-planning/dependencies.md)
- bottleneck → [`07-execution/kanban.md`](07-execution/kanban.md)
- boundaries → [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md)
- brainstorming — techniques and when to use them → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)
- brainstorming → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)
- brainwriting and the 6-3-5 method → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)
- brainwriting → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)
- brd → [`06-requirements/prd.md`](06-requirements/prd.md)
- bubble map → [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)
- build measure learn → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)
- buy-in → [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)


**C**
C- cadences (kanban) → [`07-execution/kanban.md`](07-execution/kanban.md)
- capability evals → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- card conversation confirmation → [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- cargo cult agile → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- ceo of the product → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- ces → [`02-discovery/surveys.md`](02-discovery/surveys.md) · [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- change requests → [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md) · [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)
- channels → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- choosing a user research method → [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)
- churn → [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- classes of service → [`07-execution/kanban.md`](07-execution/kanban.md)
- commitment point → [`07-execution/kanban.md`](07-execution/kanban.md)
- communicating the roadmap and aligning stakeholders → [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)
- competing alternatives → [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md)
- competitive analysis → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md)
- competitor research → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md)
- compliance → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)
- concept map → [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)
- confirmation → [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md)
- constitution (spec-kit) → [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)
- constraints → [`06-requirements/requirements.md`](06-requirements/requirements.md) · [`10-risk/assumptions-and-constraints.md`](10-risk/assumptions-and-constraints.md)
- contextual inquiry → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- continuous discovery → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- continuous roadmapping → [`05-planning/continuous-roadmapping.md`](05-planning/continuous-roadmapping.md)
- controls → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)
- convergence → [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- conversion → [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- core pm → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- corrective action → [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)
- cost of delay → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- cost of delay → [`07-execution/kanban.md`](07-execution/kanban.md)
- critical incident method → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- critical path → [`05-planning/dependencies.md`](05-planning/dependencies.md)
- cross-cultural research → [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)
- cross-functional boundaries → [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)
- cross-functional ownership → [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)
- cross-functional product collaboration → [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)
- cross-functional teams → [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)
- cross-team dependencies → [`05-planning/dependencies.md`](05-planning/dependencies.md)
- crossing the chasm template → [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)
- csat → [`02-discovery/surveys.md`](02-discovery/surveys.md) · [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- cumulative flow diagram → [`07-execution/kanban.md`](07-execution/kanban.md)
- customer benefit → [`04-strategy/product-value.md`](04-strategy/product-value.md)
- customer discovery → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- customer insights → [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)
- customer journey mapping → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)


**D**
D- daily scrum → [`07-execution/scrum.md`](07-execution/scrum.md)
- data literacy → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- decision making → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md) · [`05-planning/prioritization.md`](05-planning/prioritization.md)
- decline and end-of-life → [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- decline stage → [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- decomposition — initiatives, epics, stories and tasks → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md)
- decomposition → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md)
- definition of done → [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md)
- definition of done → [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md) · [`07-execution/scrum.md`](07-execution/scrum.md)
- delivery instability → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- delivery management → [`01-foundations/product-vs-project-management.md`](01-foundations/product-vs-project-management.md)
- delivery point → [`07-execution/kanban.md`](07-execution/kanban.md)
- delivery rate → [`07-execution/kanban.md`](07-execution/kanban.md)
- delphi technique → [`10-risk/risk-identification.md`](10-risk/risk-identification.md)
- dependencies → [`05-planning/dependencies.md`](05-planning/dependencies.md) · [`06-requirements/requirements.md`](06-requirements/requirements.md)
- dependency management → [`05-planning/dependencies.md`](05-planning/dependencies.md)
- deprecation → [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- design phase → [`07-execution/product-development-process.md`](07-execution/product-development-process.md)
- design principles → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- design process → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- design sprint → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)
- desirable viable feasible → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md) · [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)
- developers (scrum) → [`07-execution/scrum.md`](07-execution/scrum.md)
- development phase → [`07-execution/product-development-process.md`](07-execution/product-development-process.md)
- differentiation → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md) · [`04-strategy/positioning.md`](04-strategy/positioning.md) · [`04-strategy/product-strategy.md`](04-strategy/product-strategy.md)
- direct and indirect competitors → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md)
- discovery phase → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- discovery → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- discussion guide → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- divergence and convergence → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)
- do nothing competitor → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md)
- dora report → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- dot voting → [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- double diamond → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md) · [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- dream map → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- dual-track agile → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)
- dvf → [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)


**E**
E- earned value → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- ears → [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)
- easy approach to requirements syntax → [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)
- eberle → [`08-ideation/scamper.md`](08-ideation/scamper.md)
- effort → [`05-planning/estimation.md`](05-planning/estimation.md)
- emerging patterns → [`03-market-intelligence/market-trends.md`](03-market-intelligence/market-trends.md)
- empiricism → [`07-execution/scrum.md`](07-execution/scrum.md)
- enablement → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- end of life → [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- engineering collaboration → [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)
- enhance → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- eol → [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- epic → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md) · [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- escalate → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- estimation → [`05-planning/estimation.md`](05-planning/estimation.md)
- ethnographic research and contextual observation → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- ethnographic research → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- ethnography → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- eval saturation → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- evals → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- evaluating and converging on ideas → [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- evaluations → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- evidence → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)
- experiments → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)
- explicit policies → [`07-execution/kanban.md`](07-execution/kanban.md)
- exploit → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- exploratory research → [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)


**F**
F- facilitation → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- faux agile → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- feasibility → [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)
- feature factory → [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md) · [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- feature requests → [`05-planning/prioritization.md`](05-planning/prioritization.md)
- feature work → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- features out → [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md)
- field research → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- five users → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- flow metrics → [`07-execution/kanban.md`](07-execution/kanban.md)
- focus groups → [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)
- force-fitting → [`08-ideation/scamper.md`](08-ideation/scamper.md)
- forecasting → [`05-planning/estimation.md`](05-planning/estimation.md)
- framework selection → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- free trial → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- freemium → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- frontstage backstage → [`12-design-and-ux/service-design.md`](12-design-and-ux/service-design.md)
- functional emotional social needs → [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)
- functional requirements → [`06-requirements/requirements.md`](06-requirements/requirements.md)
- funnel → [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)


**G**
G- go / no-go → [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)
- go product roadmap → [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md)
- go-to-market strategy → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- go-to-market → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- goal setting → [`04-strategy/okrs.md`](04-strategy/okrs.md) · [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- goal-oriented roadmap → [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md)
- goods-services continuum → [`12-design-and-ux/service-design.md`](12-design-and-ux/service-design.md)
- grader types → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- grooming → [`05-planning/backlog-management.md`](05-planning/backlog-management.md)
- growth loops → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- growth pm → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- growth strategy → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- gtm motion → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- gtm → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- guiding metric → [`09-metrics/north-star-metric.md`](09-metrics/north-star-metric.md)


**H**
H- hackathon → [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- hard skills → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- hierarchy → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md)
- hypotheses, assumptions and validation → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)
- hypothesis validation → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)
- hypothesis → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)


**I**
I- icp → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- idea evaluation → [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- idea to action → [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- idea transformation → [`08-ideation/scamper.md`](08-ideation/scamper.md)
- idea validation → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md) · [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)
- identifying market needs → [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)
- identifying unmet customer needs → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)
- ideo → [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)
- impact analysis → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)
- increment → [`07-execution/scrum.md`](07-execution/scrum.md)
- influence without authority → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- initiative → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md)
- innovation lab → [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- innovation pm → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- innovation time → [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- internal processes → [`12-design-and-ux/service-design.md`](12-design-and-ux/service-design.md)
- interview guide → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- introduction growth maturity decline → [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)
- introvert participation → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)
- it and security risk assessment → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)
- it risk → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)


**J**
J- j-curve (ai adoption) → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- job stories and when to prefer them over user stories → [`06-requirements/job-stories.md`](06-requirements/job-stories.md)
- job story → [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md) · [`06-requirements/job-stories.md`](06-requirements/job-stories.md)
- jobs to be done (jtbd) → [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md)
- jobs to be done → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md) · [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md)
- jtbd → [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md) · [`06-requirements/job-stories.md`](06-requirements/job-stories.md)


**K**
K- kanban board → [`07-execution/kanban.md`](07-execution/kanban.md)
- kanban litmus test → [`07-execution/kanban.md`](07-execution/kanban.md)
- kanban meeting → [`07-execution/kanban.md`](07-execution/kanban.md)
- kanban method → [`07-execution/kanban.md`](07-execution/kanban.md)
- kanban roadmap → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- kanban system → [`07-execution/kanban.md`](07-execution/kanban.md)
- kanban → [`07-execution/kanban.md`](07-execution/kanban.md)
- kano model → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- key results → [`04-strategy/okrs.md`](04-strategy/okrs.md)
- kill condition → [`05-planning/prioritization.md`](05-planning/prioritization.md)
- kiro → [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)
- kpi vs okr → [`04-strategy/okrs.md`](04-strategy/okrs.md)
- kpi → [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- kpis → [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)


**L**
L- latent needs → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)
- launch and iteration → [`07-execution/product-development-process.md`](07-execution/product-development-process.md)
- launch metrics → [`11-lifecycle-and-launch/product-launch.md`](11-lifecycle-and-launch/product-launch.md)
- launch plan → [`11-lifecycle-and-launch/product-launch.md`](11-lifecycle-and-launch/product-launch.md)
- launch readiness → [`05-planning/release-planning.md`](05-planning/release-planning.md)
- launch types → [`11-lifecycle-and-launch/product-launch.md`](11-lifecycle-and-launch/product-launch.md)
- lead time → [`07-execution/kanban.md`](07-execution/kanban.md)
- lean canvas → [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)
- lean startup → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)
- little's law → [`07-execution/kanban.md`](07-execution/kanban.md)
- llm as judge → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)


**M**
M- managing a mature product → [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- market needs → [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)
- market research → [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)
- market sizing → [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)
- market trend analysis → [`03-market-intelligence/market-trends.md`](03-market-intelligence/market-trends.md)
- market trends → [`03-market-intelligence/market-trends.md`](03-market-intelligence/market-trends.md)
- maturity stage → [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- messaging → [`04-strategy/positioning.md`](04-strategy/positioning.md)
- method selection → [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)
- metr study → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- metric alignment → [`09-metrics/north-star-metric.md`](09-metrics/north-star-metric.md)
- milestones → [`05-planning/release-planning.md`](05-planning/release-planning.md)
- mind map → [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)
- mind mapping → [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)
- mission statement → [`04-strategy/product-vision.md`](04-strategy/product-vision.md)
- missionaries vs mercenaries → [`04-strategy/product-vision.md`](04-strategy/product-vision.md)
- mitigate → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- mlp → [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)
- mockups → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- moderated testing → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- monte carlo forecasting → [`07-execution/kanban.md`](07-execution/kanban.md) · [`05-planning/estimation.md`](05-planning/estimation.md)
- moscow → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- mrd → [`06-requirements/prd.md`](06-requirements/prd.md)
- mspot → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- multi-agent team organisation → [`13-ai-agent-collaboration/open-questions-ai-and-pm.md`](13-ai-agent-collaboration/open-questions-ai-and-pm.md)
- mvp → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)


**N**
N- nct → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- nist → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)
- nominal group technique → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md) · [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- non-functional requirements → [`06-requirements/requirements.md`](06-requirements/requirements.md)
- north star metric → [`05-planning/continuous-roadmapping.md`](05-planning/continuous-roadmapping.md) · [`09-metrics/north-star-metric.md`](09-metrics/north-star-metric.md)
- north star → [`04-strategy/product-vision.md`](04-strategy/product-vision.md)
- now next later → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- nps → [`02-discovery/surveys.md`](02-discovery/surveys.md) · [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)


**O**
O- objectives and key results → [`04-strategy/okrs.md`](04-strategy/okrs.md)
- observer bias → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- okr → [`04-strategy/okrs.md`](04-strategy/okrs.md)
- okrs (objectives and key results) → [`04-strategy/okrs.md`](04-strategy/okrs.md)
- one-way door → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)
- open questions (ai and pm) → [`13-ai-agent-collaboration/open-questions-ai-and-pm.md`](13-ai-agent-collaboration/open-questions-ai-and-pm.md)
- open-ended questions → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- operations review → [`07-execution/kanban.md`](07-execution/kanban.md)
- opportunity assessment → [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)
- opportunity evaluation → [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)
- opportunity scoring → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- opportunity solution tree → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)
- opportunity validation → [`07-execution/product-development-process.md`](07-execution/product-development-process.md)
- optionality → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)
- osborn → [`08-ideation/scamper.md`](08-ideation/scamper.md)
- out of scope → [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md)
- outcome-based roadmap → [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md)
- outcome-based roadmaps → [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md)
- outcomes over outputs → [`04-strategy/okrs.md`](04-strategy/okrs.md) · [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md) · [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- over-collaboration → [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)


**P**
P- pain points → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md) · [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)
- participant observation → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- pass@k → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- pass^k → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- people props processes → [`12-design-and-ux/service-design.md`](12-design-and-ux/service-design.md)
- perceived value → [`04-strategy/product-value.md`](04-strategy/product-value.md)
- perception gap (productivity) → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- perception → [`04-strategy/positioning.md`](04-strategy/positioning.md)
- pestle → [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)
- pirate metrics — aarrr and rarra → [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)
- pirate metrics → [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)
- planning artifacts → [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- planning poker → [`05-planning/estimation.md`](05-planning/estimation.md)
- platform pm → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- plc → [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)
- plg → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- pm and designer collaboration → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- pm and ux boundary → [`12-design-and-ux/ux-for-product-managers.md`](12-design-and-ux/ux-for-product-managers.md)
- pm and ux role boundaries (survey evidence) → [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)
- pm and ux → [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)
- pm discipline → [`01-foundations/product-management.md`](01-foundations/product-management.md)
- pm responsibilities → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- pm role → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- pm skills → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- pm specialization → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- pmf expansion → [`04-strategy/product-market-fit.md`](04-strategy/product-market-fit.md)
- pmf → [`04-strategy/product-market-fit.md`](04-strategy/product-market-fit.md)
- positioning map → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md)
- positioning statement → [`04-strategy/positioning.md`](04-strategy/positioning.md)
- positioning → [`04-strategy/positioning.md`](04-strategy/positioning.md)
- positive risk → [`10-risk/risk-management.md`](10-risk/risk-management.md)
- post-launch retrospective → [`11-lifecycle-and-launch/product-launch.md`](11-lifecycle-and-launch/product-launch.md)
- prd → [`06-requirements/prd.md`](06-requirements/prd.md)
- premature convergence → [`05-planning/continuous-roadmapping.md`](05-planning/continuous-roadmapping.md)
- pricing and packaging → [`11-lifecycle-and-launch/go-to-market.md`](11-lifecycle-and-launch/go-to-market.md)
- prioritization frameworks → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- prioritization matrix → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- prioritization skill → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- prioritization — the practice → [`05-planning/prioritization.md`](05-planning/prioritization.md)
- prioritization → [`05-planning/prioritization.md`](05-planning/prioritization.md)
- proactive monitoring → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- probabilistic forecasting → [`07-execution/kanban.md`](07-execution/kanban.md) · [`05-planning/estimation.md`](05-planning/estimation.md)
- probability and consequence → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)
- probability and impact matrix → [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- probing questions → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- problem framing → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- problem space → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- product backlog (scrum) → [`07-execution/scrum.md`](07-execution/scrum.md)
- product backlog → [`05-planning/backlog-management.md`](05-planning/backlog-management.md) · [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- product collaboration → [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)
- product design fundamentals for product managers → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- product design → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- product development process → [`07-execution/product-development-process.md`](07-execution/product-development-process.md)
- product discipline → [`01-foundations/product-management.md`](01-foundations/product-management.md)
- product discovery frameworks → [`02-discovery/discovery-frameworks.md`](02-discovery/discovery-frameworks.md)
- product discovery → [`02-discovery/product-discovery.md`](02-discovery/product-discovery.md)
- product failure modes → [`10-risk/product-risk.md`](10-risk/product-risk.md)
- product function → [`01-foundations/product-management.md`](01-foundations/product-management.md)
- product goal → [`07-execution/scrum.md`](07-execution/scrum.md)
- product goals and goal-setting frameworks → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- product goals → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- product launch → [`11-lifecycle-and-launch/product-launch.md`](11-lifecycle-and-launch/product-launch.md)
- product lifecycle → [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)
- product management competencies → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- product management definition → [`01-foundations/product-management.md`](01-foundations/product-management.md)
- product management specializations and types of product work → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- product management vs project management → [`01-foundations/product-vs-project-management.md`](01-foundations/product-vs-project-management.md)
- product management → [`01-foundations/product-management.md`](01-foundations/product-management.md)
- product manager duties → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- product manager role and responsibilities → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- product manager skills and competencies → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- product manager vs engineering manager → [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)
- product manager vs product owner → [`01-foundations/product-manager-vs-product-owner.md`](01-foundations/product-manager-vs-product-owner.md)
- product manager vs project manager → [`01-foundations/product-vs-project-management.md`](01-foundations/product-vs-project-management.md)
- product manager → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- product metrics → [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- product opportunity assessment → [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)
- product organization → [`01-foundations/product-management.md`](01-foundations/product-management.md)
- product owner accountability → [`07-execution/scrum.md`](07-execution/scrum.md) · [`01-foundations/product-manager-vs-product-owner.md`](01-foundations/product-manager-vs-product-owner.md)
- product owner of the product vision → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- product owner → [`01-foundations/product-manager-vs-product-owner.md`](01-foundations/product-manager-vs-product-owner.md)
- product plan → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- product positioning → [`04-strategy/positioning.md`](04-strategy/positioning.md)
- product requirements document (prd) → [`06-requirements/prd.md`](06-requirements/prd.md)
- product requirements document → [`06-requirements/prd.md`](06-requirements/prd.md)
- product retirement → [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- product risk → [`10-risk/product-risk.md`](10-risk/product-risk.md)
- product roadmap → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- product spec → [`06-requirements/prd.md`](06-requirements/prd.md)
- product strategy → [`04-strategy/product-strategy.md`](04-strategy/product-strategy.md)
- product triad → [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)
- product trio → [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)
- product value → [`04-strategy/product-value.md`](04-strategy/product-value.md)
- product vision (and how it differs from mission) → [`04-strategy/product-vision.md`](04-strategy/product-vision.md)
- product vision board → [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)
- product vision → [`04-strategy/product-vision.md`](04-strategy/product-vision.md)
- product vs project vs business risk → [`10-risk/product-risk.md`](10-risk/product-risk.md)
- product-led growth and growth models → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- product-led growth → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- product-market fit expansion → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- product-market fit → [`04-strategy/product-market-fit.md`](04-strategy/product-market-fit.md)
- production blocking → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)
- progress-making forces → [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md)
- project control → [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)
- project management → [`01-foundations/product-vs-project-management.md`](01-foundations/product-vs-project-management.md)
- project monitoring and control → [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)
- project monitoring → [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)
- project risk → [`10-risk/risk-management.md`](10-risk/risk-management.md)
- prototypes → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- pull system → [`07-execution/kanban.md`](07-execution/kanban.md)
- push pull anxiety inertia → [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md)
- push system → [`07-execution/kanban.md`](07-execution/kanban.md)


**Q**
Q- qualitative risk analysis → [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- qualitative vs quantitative → [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)
- quantitative risk analysis → [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- questionnaire → [`02-discovery/surveys.md`](02-discovery/surveys.md)


**R**
R- raci → [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)
- rapid ideation → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)
- rarra → [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)
- regression evals → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- release criteria → [`05-planning/release-planning.md`](05-planning/release-planning.md) · [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md)
- release notes → [`05-planning/release-planning.md`](05-planning/release-planning.md)
- release plan → [`05-planning/release-planning.md`](05-planning/release-planning.md) · [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- release planning → [`05-planning/release-planning.md`](05-planning/release-planning.md)
- replenishment meeting → [`07-execution/kanban.md`](07-execution/kanban.md)
- requirements clarity → [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)
- requirements doc → [`06-requirements/prd.md`](06-requirements/prd.md)
- requirements documentation → [`06-requirements/prd.md`](06-requirements/prd.md)
- requirements elicitation → [`06-requirements/requirements.md`](06-requirements/requirements.md)
- requirements gathering → [`06-requirements/requirements.md`](06-requirements/requirements.md)
- requirements — types and elicitation → [`06-requirements/requirements.md`](06-requirements/requirements.md)
- requirements → [`06-requirements/requirements.md`](06-requirements/requirements.md)
- research bias → [`03-market-intelligence/market-needs.md`](03-market-intelligence/market-needs.md)
- research methods → [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)
- reserve analysis → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- residual risk → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- responsibility ambiguity → [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)
- retention → [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- retention-first → [`09-metrics/pirate-metrics.md`](09-metrics/pirate-metrics.md)
- retrospective → [`07-execution/scrum.md`](07-execution/scrum.md)
- reverse brainstorming → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)
- reversibility → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md) · [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- review bottleneck → [`13-ai-agent-collaboration/pm-with-ai-implementers.md`](13-ai-agent-collaboration/pm-with-ai-implementers.md)
- rice → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- risk and reward → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)
- risk assessment and analysis → [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- risk assessment → [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- risk data quality → [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- risk definition → [`10-risk/risk-management.md`](10-risk/risk-management.md)
- risk identification → [`10-risk/risk-identification.md`](10-risk/risk-identification.md)
- risk management plan → [`10-risk/risk-management.md`](10-risk/risk-management.md)
- risk management — foundations → [`10-risk/risk-management.md`](10-risk/risk-management.md)
- risk management → [`10-risk/risk-management.md`](10-risk/risk-management.md)
- risk monitoring and control → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- risk monitoring → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- risk register updates → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- risk register → [`10-risk/risk-identification.md`](10-risk/risk-identification.md) · [`10-risk/risk-management.md`](10-risk/risk-management.md)
- risk response strategies → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- risk response → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- risk review (kanban) → [`07-execution/kanban.md`](07-execution/kanban.md)
- risk score → [`10-risk/risk-assessment.md`](10-risk/risk-assessment.md)
- risk tolerance → [`10-risk/risk-management.md`](10-risk/risk-management.md)
- risk triggers → [`10-risk/risk-monitoring.md`](10-risk/risk-monitoring.md)
- risk vs evidence grid → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md) · [`10-risk/product-risk.md`](10-risk/product-risk.md)
- riskiest assumption → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md)
- roadmap audiences → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- roadmap format selection → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- roadmap formats → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- roadmap ownership → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- roadmap presentation → [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)
- roadmap transition → [`05-planning/outcome-based-roadmaps.md`](05-planning/outcome-based-roadmaps.md)
- roadmap vs backlog vs release plan → [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- roadmap vs backlog → [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- roadmap → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- rohrbach → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)
- role boundaries → [`01-foundations/product-vs-project-management.md`](01-foundations/product-vs-project-management.md)
- role overlap → [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)
- rolling planning → [`05-planning/continuous-roadmapping.md`](05-planning/continuous-roadmapping.md)
- root cause analysis → [`10-risk/risk-identification.md`](10-risk/risk-identification.md)
- round robin → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)


**S**
S- sales-led growth → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- saturation → [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)
- say-do gap → [`02-discovery/ethnographic-research.md`](02-discovery/ethnographic-research.md)
- saying no → [`05-planning/prioritization.md`](05-planning/prioritization.md) · [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)
- scaling work → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)
- scamper → [`08-ideation/scamper.md`](08-ideation/scamper.md)
- scope creep → [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md)
- scope definition and scope creep → [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md)
- scope monitoring → [`07-execution/project-monitoring-and-control.md`](07-execution/project-monitoring-and-control.md)
- scope → [`06-requirements/scope-definition.md`](06-requirements/scope-definition.md)
- screening → [`08-ideation/idea-evaluation.md`](08-ideation/idea-evaluation.md)
- scrum guide → [`07-execution/scrum.md`](07-execution/scrum.md)
- scrum master → [`07-execution/scrum.md`](07-execution/scrum.md)
- scrum roles → [`01-foundations/product-manager-vs-product-owner.md`](01-foundations/product-manager-vs-product-owner.md)
- scrum team → [`07-execution/scrum.md`](07-execution/scrum.md)
- scrum values → [`07-execution/scrum.md`](07-execution/scrum.md)
- scrum → [`07-execution/scrum.md`](07-execution/scrum.md)
- sean ellis test → [`04-strategy/product-market-fit.md`](04-strategy/product-market-fit.md) · [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)
- second-order effects → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)
- secondary research → [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)
- security risk → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)
- segmentation → [`03-market-intelligence/market-research.md`](03-market-intelligence/market-research.md)
- self-disruption → [`11-lifecycle-and-launch/managing-maturity.md`](11-lifecycle-and-launch/managing-maturity.md)
- semistructured interview → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- seq → [`02-discovery/surveys.md`](02-discovery/surveys.md)
- service blueprint → [`12-design-and-ux/service-design.md`](12-design-and-ux/service-design.md)
- service delivery manager → [`07-execution/kanban.md`](07-execution/kanban.md)
- service delivery principles → [`07-execution/kanban.md`](07-execution/kanban.md)
- service design → [`12-design-and-ux/service-design.md`](12-design-and-ux/service-design.md)
- service level agreement → [`07-execution/kanban.md`](07-execution/kanban.md)
- service level expectation → [`07-execution/kanban.md`](07-execution/kanban.md)
- service request manager → [`07-execution/kanban.md`](07-execution/kanban.md) · [`01-foundations/product-manager-vs-product-owner.md`](01-foundations/product-manager-vs-product-owner.md)
- share → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- shared vision → [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)
- silent churn → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)
- silent ideation → [`08-ideation/brainwriting.md`](08-ideation/brainwriting.md)
- smart goals → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- snowbird → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- soft skills → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- spec kit → [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)
- spec-driven development → [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)
- specification → [`06-requirements/prd.md`](06-requirements/prd.md)
- sprint backlog → [`07-execution/scrum.md`](07-execution/scrum.md)
- sprint goal → [`07-execution/scrum.md`](07-execution/scrum.md)
- sprint planning → [`07-execution/scrum.md`](07-execution/scrum.md)
- sprint retrospective → [`07-execution/scrum.md`](07-execution/scrum.md)
- sprint review → [`07-execution/scrum.md`](07-execution/scrum.md)
- sprint roadmap → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- sprint → [`07-execution/scrum.md`](07-execution/scrum.md)
- stakeholder alignment → [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)
- stakeholder management → [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)
- starbursting → [`08-ideation/brainstorming.md`](08-ideation/brainstorming.md)
- statik → [`07-execution/kanban.md`](07-execution/kanban.md)
- stopping work → [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)
- story mapping → [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- story points → [`05-planning/estimation.md`](05-planning/estimation.md)
- story splitting → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md) · [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- story template → [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- story vs task → [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- storytelling → [`01-foundations/product-manager-skills.md`](01-foundations/product-manager-skills.md)
- strategic communication → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- strategic fit → [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md) · [`07-execution/product-development-process.md`](07-execution/product-development-process.md)
- strategic imperatives → [`04-strategy/product-strategy.md`](04-strategy/product-strategy.md)
- strategic roadmap → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- strategic thinking and product decisions → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)
- strategic thinking → [`04-strategy/strategic-thinking.md`](04-strategy/strategic-thinking.md)
- strategy components → [`04-strategy/product-strategy.md`](04-strategy/product-strategy.md)
- strategy review (kanban) → [`07-execution/kanban.md`](07-execution/kanban.md)
- strategy vs execution → [`05-planning/roadmap-vs-backlog-vs-release-plan.md`](05-planning/roadmap-vs-backlog-vs-release-plan.md)
- strategy vs plan → [`04-strategy/product-strategy.md`](04-strategy/product-strategy.md)
- struggling moments → [`02-discovery/jobs-to-be-done.md`](02-discovery/jobs-to-be-done.md)
- substitute combine adapt → [`08-ideation/scamper.md`](08-ideation/scamper.md)
- substitutes → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md)
- sunsetting → [`11-lifecycle-and-launch/decline-and-end-of-life.md`](11-lifecycle-and-launch/decline-and-end-of-life.md)
- survey design → [`02-discovery/surveys.md`](02-discovery/surveys.md)
- survey misuse → [`02-discovery/surveys.md`](02-discovery/surveys.md)
- surveys in product research → [`02-discovery/surveys.md`](02-discovery/surveys.md)
- surveys → [`02-discovery/surveys.md`](02-discovery/surveys.md)
- sus → [`02-discovery/surveys.md`](02-discovery/surveys.md)
- swiss cheese model → [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- swot → [`03-market-intelligence/competitive-analysis.md`](03-market-intelligence/competitive-analysis.md) · [`10-risk/risk-identification.md`](10-risk/risk-identification.md)


**T**
T- t-shirt sizing → [`05-planning/estimation.md`](05-planning/estimation.md)
- tacit knowledge (and agents) → [`13-ai-agent-collaboration/pm-with-ai-implementers.md`](13-ai-agent-collaboration/pm-with-ai-implementers.md)
- tam → [`02-discovery/opportunity-assessment.md`](02-discovery/opportunity-assessment.md)
- target market → [`04-strategy/positioning.md`](04-strategy/positioning.md)
- task → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md)
- team structure → [`07-execution/product-collaboration.md`](07-execution/product-collaboration.md)
- technical feasibility → [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)
- technical fluency → [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)
- temporal information → [`03-market-intelligence/market-trends.md`](03-market-intelligence/market-trends.md)
- test tasks → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- testable requirements → [`06-requirements/acceptance-criteria.md`](06-requirements/acceptance-criteria.md)
- the agile manifesto → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- the product development process → [`07-execution/product-development-process.md`](07-execution/product-development-process.md)
- the product lifecycle → [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)
- the product triad (desirable, viable, feasible) → [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)
- theme-based roadmap → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- themes → [`05-planning/roadmaps.md`](05-planning/roadmaps.md)
- theodore levitt → [`11-lifecycle-and-launch/product-lifecycle.md`](11-lifecycle-and-launch/product-lifecycle.md)
- think-aloud protocol → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- third-party dependencies → [`05-planning/dependencies.md`](05-planning/dependencies.md)
- threats and vulnerabilities → [`10-risk/it-and-security-risk.md`](10-risk/it-and-security-risk.md)
- three pillars → [`01-foundations/product-manager-role.md`](01-foundations/product-manager-role.md)
- three-legged stool → [`12-design-and-ux/product-triad.md`](12-design-and-ux/product-triad.md)
- throughput → [`07-execution/kanban.md`](07-execution/kanban.md)
- time to value → [`04-strategy/product-led-growth.md`](04-strategy/product-led-growth.md)
- timeline roadmap → [`05-planning/roadmap-formats.md`](05-planning/roadmap-formats.md)
- trade-offs → [`05-planning/prioritization.md`](05-planning/prioritization.md)
- transfer → [`10-risk/risk-response.md`](10-risk/risk-response.md)
- transparency → [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)
- tree map → [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)
- trend analysis → [`03-market-intelligence/market-trends.md`](03-market-intelligence/market-trends.md)
- triangulation → [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)
- trigger motivation outcome → [`06-requirements/job-stories.md`](06-requirements/job-stories.md)
- triggers barriers drivers → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)
- trust → [`05-planning/roadmap-communication.md`](05-planning/roadmap-communication.md)
- twelve agile principles → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- twelve principles → [`07-execution/agile-manifesto.md`](07-execution/agile-manifesto.md)
- types of product work → [`01-foundations/pm-specializations.md`](01-foundations/pm-specializations.md)


**U**
U- unconscious assumptions → [`10-risk/assumptions-and-constraints.md`](10-risk/assumptions-and-constraints.md)
- unmet needs → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)
- unmoderated testing → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- usability testing → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- usability → [`12-design-and-ux/ux-for-product-managers.md`](12-design-and-ux/ux-for-product-managers.md)
- user experience → [`12-design-and-ux/ux-for-product-managers.md`](12-design-and-ux/ux-for-product-managers.md)
- user interviews and interview guides → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- user interviews → [`02-discovery/user-interviews.md`](02-discovery/user-interviews.md)
- user research → [`02-discovery/user-research-methods.md`](02-discovery/user-research-methods.md)
- user stories → [`06-requirements/user-stories.md`](06-requirements/user-stories.md)
- user story vs job story → [`06-requirements/job-stories.md`](06-requirements/job-stories.md)
- user testing → [`02-discovery/usability-testing.md`](02-discovery/usability-testing.md)
- user-centric focus (dora) → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- ux for pms → [`12-design-and-ux/ux-for-product-managers.md`](12-design-and-ux/ux-for-product-managers.md)
- ux for product managers → [`12-design-and-ux/ux-for-product-managers.md`](12-design-and-ux/ux-for-product-managers.md)
- ux metrics → [`12-design-and-ux/ux-for-product-managers.md`](12-design-and-ux/ux-for-product-managers.md)


**V**
V- v2mom → [`04-strategy/product-goals.md`](04-strategy/product-goals.md)
- validation → [`02-discovery/hypotheses-and-assumptions.md`](02-discovery/hypotheses-and-assumptions.md) · [`04-strategy/product-market-fit.md`](04-strategy/product-market-fit.md)
- value proposition canvas → [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)
- value proposition → [`04-strategy/value-proposition.md`](04-strategy/value-proposition.md)
- value vs effort → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- value vs price → [`04-strategy/product-value.md`](04-strategy/product-value.md)
- value-price-cost → [`04-strategy/product-value.md`](04-strategy/product-value.md)
- vanity metrics → [`09-metrics/product-metrics.md`](09-metrics/product-metrics.md)
- velocity → [`05-planning/estimation.md`](05-planning/estimation.md)
- verification tax → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md) · [`13-ai-agent-collaboration/evals-and-acceptance-for-agents.md`](13-ai-agent-collaboration/evals-and-acceptance-for-agents.md)
- vibe coding → [`13-ai-agent-collaboration/spec-driven-development.md`](13-ai-agent-collaboration/spec-driven-development.md)
- vision vs mission → [`04-strategy/product-vision.md`](04-strategy/product-vision.md)
- visiontype → [`04-strategy/product-vision.md`](04-strategy/product-vision.md)
- visual thinking → [`08-ideation/mind-mapping.md`](08-ideation/mind-mapping.md)
- voice of the customer → [`02-discovery/identifying-unmet-needs.md`](02-discovery/identifying-unmet-needs.md)


**W**
W- [CONCEPT_GRAPH.md](CONCEPT_GRAPH.md) — relationships between concepts
- [GLOSSARY.md](GLOSSARY.md) — term definitions
- [RESEARCH_BACKLOG.md](RESEARCH_BACKLOG.md) — what is missing
- [TAXONOMY.md](TAXONOMY.md) — how the knowledge is organised and why
- weighted scoring → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)
- what vs how → [`01-foundations/product-vs-project-management.md`](01-foundations/product-vs-project-management.md)
- who owns discovery → [`01-foundations/pm-and-ux-collaboration.md`](01-foundations/pm-and-ux-collaboration.md)
- wip limits → [`07-execution/kanban.md`](07-execution/kanban.md)
- wireframes → [`12-design-and-ux/product-design-fundamentals.md`](12-design-and-ux/product-design-fundamentals.md)
- work breakdown → [`06-requirements/epics-and-decomposition.md`](06-requirements/epics-and-decomposition.md)
- work in progress limits → [`07-execution/kanban.md`](07-execution/kanban.md)
- working in small batches → [`13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md`](13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md)
- working with engineering → [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)
- working with engineers → [`07-execution/working-with-engineering.md`](07-execution/working-with-engineering.md)
- wsjf → [`05-planning/prioritization-frameworks.md`](05-planning/prioritization-frameworks.md)

