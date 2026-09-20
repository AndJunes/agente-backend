---
title: Product Manager vs Product Owner
domain: foundations
type: comparison
topics:
  - product owner
  - product manager vs product owner
  - scrum roles
  - backlog ownership
source_count: 6
sources: [S078, S118, S064, S006, E001, E003]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: true
verified: partial
phase: 2
provenance:
  primary: [E001, E003]
  interpretation: [S078, S118, S006]
  practice: []
  empirical: [S064]
last_reviewed: 2026-09-16
---

# Product Manager vs Product Owner

## Why this distinction exists at all

The product owner is a **Scrum role**. [S078] states the dependency directly: "if a team is
practicing scrum, then they also need to have a product owner." The product manager is an
organizational function that exists independently of any development methodology. The two
therefore sit on different axes, which is a large part of why they are confused.

## The distinction as commonly drawn

[S078]: "While a product manager defines the direction of the product through research,
vision-setting, alignment, and prioritization, the product owner should work more closely
with the development team to execute against the goals that the product manager helps to
define."

| Product Manager [S078] | Product Owner [S078] |
|---|---|
| Works with outside stakeholders | Works with internal stakeholders |
| Helps to define the product vision | Helps teams execute on a shared vision |
| Outlines what success looks like | Outlines the plan for achieving success |
| Owns vision, marketing, ROI | Owns team backlog and fulfillment work |
| Works at a conceptual level | Involved in day-to-day activities |

[S118] describes the product owner as "embedded in one or more scrum teams, but their focus
is mainly tactical, helping ensure the strategy laid out by product managers is
appropriately executed," and notes that "while there's some debate, product owners are often
considered part of product management."

## The boundary moves with team setup

This is the most decision-relevant point in the corpus, from [S078]:

- If the team **is not doing Scrum** (e.g. Kanban), "the product manager might end up doing
  the prioritization for the development team and play a larger role in making sure everyone
  is on the same page."
- If the team **is doing Scrum but has no product manager**, "the product owner often ends
  up taking on some of the product manager's responsibilities."

[S078] warns about the failure mode: "All of this can get really murky really quickly, which
is why teams have to be careful to clearly define responsibilities, or they can risk falling
into the old ways of building software, where one group writes the requirements and throws
it over the fence for another group to build. When this happens expectations get misaligned,
time gets wasted, and teams run the risk of creating products or features that don't satisfy
customer needs."

## Evidence that practitioners are genuinely confused

[S064] provides survey data (n=372 UX and PM professionals) showing this is not merely a
definitional quibble. When asked who should be responsible for vision and prioritization
tasks:

- Over **63%** of PM respondents assigned all vision- and prioritization-related tasks to
  **product management**.
- **UX respondents were split** between assigning these tasks to product owners and to
  product managers.
- For every such task, more PM respondents assigned it to PM than UX respondents did; more
  UX respondents assigned it to PO than PM respondents did.

[S064]'s reading: "it seems that UXers do not have a clear understanding of the different
responsibilities of product owners and product managers when it comes to product vision and
strategy."

Similar splits appeared for *ensuring the project meets business requirements* (PMs said PM;
UXers said PO) and for *championing the product* (most UX responses, 41%, said PO; most PM
responses said PM).

> This is documented disagreement between professional groups, not a resolvable definition.
> An agent should treat "who owns X" as an **organization-specific fact to be established**,
> not inferred.

## A contested claim

[S006] asserts that strategic thinking "is a skill that separates the role of a product
manager from the role of a product owner. As a product manager you are creating the vision
and driving product growth whereas with product ownership, your focus is more on... the
functional, operational, and executional based responsibilities within your team."

> **Classification: OPINION.** [S006] is a short blog post from a commercial training
> institute with no supporting evidence. It is consistent in direction with [S078] and
> [S118], but its framing — that product owners do not think strategically — is stronger
> than what the other sources claim and is contradicted by the ambiguity documented in
> [S064].

## Phase 2 — what the primary texts say, and why the question stays open

The corpus itself contained **no primary Scrum source**; every statement above is second-hand.
Phase-2 research retrieved two primary texts. **They did not resolve the question — they turned a
two-sided corpus disagreement into a documented three-way one.**

### What the Scrum Guide actually says
[E001], the 2020 Scrum Guide — see [../07-execution/scrum.md](../07-execution/scrum.md):

- The **Product Owner is accountable for maximizing the value of the product**, and for developing
  and communicating the **Product Goal**, creating and communicating **Product Backlog items**,
  **ordering** the Product Backlog, and ensuring it is transparent, visible and understood.
- > **"The Product Owner is one person, not a committee."** [E001]
- The Product Owner is **accountable** for the Product Backlog — [E001] does **not** require personal
  authorship, which matches [S127]'s distinction in
  [../06-requirements/user-stories.md](../06-requirements/user-stories.md).

> **This settles the backlog-ownership question that [S064] found practitioners disagreeing about —
> for teams running Scrum.** The Product Owner is accountable. Full stop.

> **⚠ What [E001] does NOT contain: the words "product manager."** The Scrum Guide never mentions the
> role and never describes how the two relate. **The relationship the corpus argues about is not
> addressed by the framework that created one of the two roles.** [S078]'s claim that a Scrum team
> "needs to have a product owner" is confirmed; every claim about how a PM sits above, beside or
> inside that role is **outside Scrum's scope entirely.**

### What Kanban says — and it directly contradicts the corpus
[E003], *Essential Kanban Condensed*, defines a **Service Request Manager**: responsible for
understanding customer needs and expectations and for facilitating selection and ordering of work at
the Replenishment Meeting. Its listed **alternative names for that role**:

> **"Product Manager, Product Owner, and Service Manager."** [E003]

> **[E003] treats Product Manager and Product Owner as interchangeable names for one function.** The
> corpus sources ([S078], [S118], [S006]) treat them as **strategic versus tactical**. [E001] defines
> one and ignores the other.

### The three-way disagreement, stated plainly

| Source | Position | Provenance |
|---|---|---|
| **[E001]** Scrum Guide 2020 | Product Owner is a defined accountability; **Product Manager is not a Scrum concept and is never mentioned** | Primary — framework originators |
| **[E003]** Kanban Method | **The same function, differently named** depending on the organisation. Roles are *"hats"*, not job titles; *"there are no required roles in Kanban"* | Primary — method originator |
| **[S078], [S118], [S006]** | **Different roles at different altitudes** — PM strategic, PO tactical and embedded | Vendor and training-provider guides |
| **[S064]** NN/g, n=372 | Practitioners **do not agree** on who owns what | Empirical survey |

> **Do not resolve this by preferring one.** [E001] and [E003] are not making competing claims about
> the same thing: Scrum defines a role inside its own framework and is silent beyond it; Kanban
> deliberately refuses to define roles at all and names what it observes. The **vendor sources are
> describing a job-market distinction**, which is a real phenomenon and a different question from
> what either framework prescribes. [S064] measures that none of this is settled in practice.
>
> **The useful answer to "what is the difference?" is therefore: it depends on who is asking and
> about what** — a framework accountability, a Kanban hat, or a job title. Recorded in
> [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

## Related concepts

- [product-manager-role.md](product-manager-role.md)
- [product-vs-project-management.md](product-vs-project-management.md)
- [pm-and-ux-collaboration.md](pm-and-ux-collaboration.md)
- [../07-execution/agile-manifesto.md](../07-execution/agile-manifesto.md)
- [../07-execution/scrum.md](../07-execution/scrum.md) — the Product Owner accountability, from the primary text
- [../07-execution/kanban.md](../07-execution/kanban.md) — the Service Request Manager
- [../05-planning/prioritization.md](../05-planning/prioritization.md)
- [../05-planning/backlog-management.md](../05-planning/backlog-management.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S078 | Atlassian (Sherif Mansour) — *Product Manager: Role & Best Practices* | Vendor guide | Comparison table, methodology dependency, failure mode |
| S118 | ProductPlan — *The Ultimate Guide to Product Management* | Vendor guide | PO as tactical, embedded in scrum teams |
| S064 | Nielsen Norman Group — *PM and UX Have Markedly Different Views* | Survey research (n=372) | Empirical evidence of role confusion |
| S006 | Institute of Product Leadership — *4 Ways to Develop Your Strategic Thinking Skills* | Training-provider blog | Contested strategic-thinking claim (flagged as opinion) |
| **E001** | **The Scrum Guide**, Schwaber & Sutherland, November 2020 | **Primary text** | **The Product Owner accountability verbatim; "one person, not a committee"; the absence of "product manager" from the Guide** |
| **E003** | **Anderson & Carmichael — *Essential Kanban Condensed*, 2016** | **Primary text** | **Service Request Manager, with Product Manager and Product Owner as alternative names for one function** |
