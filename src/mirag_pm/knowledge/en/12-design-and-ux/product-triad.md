---
title: The Product Triad (Desirable, Viable, Feasible)
domain: design-and-ux
type: framework
topics:
  - product triad
  - product trio
  - DVF
  - desirable viable feasible
  - IDEO
  - cross-functional ownership
  - three-legged stool
source_count: 2
sources: [S115, S122]
evidence_type: professional-practice
confidence: high
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# The Product Triad (Desirable, Viable, Feasible)

## What it is

[S115] (Nielsen Norman Group, Pavel Samsonov, 18 July 2025): "The product triad (also called the
**product trio** or **three-legged-stool model**) is likely **the most common pattern for organizing
product teams in Agile organizations.** Its fundamental goal is to **structure collaboration between
design, product, and engineering.** The triad is composed of **one representative from each
function, working together on one product as equal partners.**"

The "three-legged stool" name is deliberate: it contrasts with "**a wobbly 'two-legged stool'
supported only by engineering and business**" — i.e. a team with no design representation.

## Origins

[S115]: "The product triad takes its roots from **the early 2000s**, when a set of principles for
innovation began to emerge. These principles established that, to be successful, business ventures
had to address three critical aspects: **People** who would buy the product · **Process** that would
provide the product · **Technology** that would make the product work."

> "**IDEO popularized these principles in its DVF (Desirable, Viable, Feasible) framework.**" [S115]

| Aspect | Definition [S115] |
|---|---|
| **Desirable** | "Any successful new product needs **a market of people willing to use it**" |
| **Viable** | "The **business model needs to be sound over a long enough term to be profitable**" |
| **Feasible** | "The company should be **able to execute the idea** behind the product" |

[S115] notes the common visual: "IDEO's DVF framework is sometimes represented as a Venn diagram,
with **valuable at the intersection of the three circles.**"

### Relationship to other triads in this knowledge base

The corpus contains three closely related but **not identical** formulations. They should not be
collapsed:

| Formulation | Terms | Source | What it describes |
|---|---|---|---|
| **DVF** | Desirable · Viable · Feasible | [S115] | Conditions a **venture** must satisfy |
| **Cagan's** | Valuable · Usable · Feasible | [S140], [S122] | Properties a **product/feature** must have |
| **Eriksson's** | Business · Technology · User experience | [S140] | Competences a **product manager** must span |
| **Discovery's** | Desirable · Feasible · Viable | [S028] | What a discovery must establish |

> [S115]'s version puts **valuable** at the *intersection*; Cagan's puts **valuable** as one of the
> three legs and adds **usable**. The difference is not trivial: Cagan's version treats usability as
> a first-class risk, which DVF folds into desirability.

## The misconception that matters most

This is the document's central correction, and it is the reason to read it:

> "There is a **common misconception** that the members of the triad each own one of the three
> aspects of the DVF framework: **designers own the desirable component, developers own the feasible
> one, and the product team owns the viable component.**
>
> **In reality, the purpose of the product triad is to *dissolve* siloed ownership. Effective triads
> collaborate on achieving all three aspects; while one individual may lead on ensuring that the
> necessary decisions get made, the team owns the decisions jointly.**" [S115]

> **Read carefully: the triad is not a division of labour, it is a structure for joint
> decision-making.** A team where the designer speaks only to desirability and the engineer only to
> feasibility has reproduced the silos the triad exists to remove. The distinction [S115] draws —
> *one person may lead on a decision; the team owns it* — is the operative one.
>
> This bears directly on the measured role confusion in
> [../01-foundations/pm-and-ux-collaboration.md](../01-foundations/pm-and-ux-collaboration.md),
> where PMs and UXers each claimed ownership of overlapping activities. The triad model suggests
> the framing of that question — *who owns X?* — may itself be the problem, though [S064]'s
> evidence also shows that leaving it unresolved has real costs.

## The roles, as described from the outside

[S115] is written for designers, and its descriptions of the other two roles are therefore
unusually candid — an outside view of what each actually contributes.

### The software engineering lead
> "The most senior engineer on the development team assigned to the product. In addition to writing
> code, the engineering lead will also **represent the product team when coordinating with other
> software engineering teams across the company.**" [S115]

**Their influence is larger than "feasibility":**

> "The engineering lead will be the main voice when **estimating the complexity** of any development
> work. **This is not solely an issue of feasibility — a lot of engineering work is feasible with
> unlimited time and budget, but it's also about understanding *viability* — whether the necessary
> amount of work would be justified by the business value produced in the long run.**
>
> As a result, **the engineering lead has a lot of influence when it comes to determining the final
> state of the user experience, through establishing the possible scope of what can be
> achieved.**" [S115]

> **This is the sharpest observation in the document.** Estimation is not a neutral input — it sets
> the boundary of what the experience can be. An engineering lead who estimates conservatively
> shapes the product as surely as a designer who sketches it. See
> [../05-planning/estimation.md](../05-planning/estimation.md), where the corpus's estimation
> coverage is otherwise almost nil.

### The product manager
> "The **main interface between the product team and the rest of the business.** As such, they are
> **responsible for keeping the product viable from a business perspective.**" [S115]

**For non-revenue products** [S115]: "On other products, **such as internal tools, this means
justifying the investment in the product through visible productivity increases or the support
provided to profit centers** within the business."

> This is the corpus's only treatment of **internal-product viability**, and it is a useful one: the
> viability argument does not disappear when there is no revenue, it changes denomination.

**Success criteria** [S115] separates two kinds:

| | Definition [S115] |
|---|---|
| **Requirements** | "**Specific outputs** that stakeholders expect from the product team" |
| **Metrics** | "**Measurable outcomes** of the team's work" |

"**Most metrics track user behavior, so a product manager needs to have a good understanding of how
users interact with the product and how changes to the product will impact that interaction.**"

**When there is no researcher** [S115]: "On product teams with **no dedicated user researcher, some
product managers take on this role** to ensure that the product is desirable to customers."

**The PM's core activities** [S115]: "determining **what the team should work on** to achieve the
established success criteria. Their work involves **scoping** (deciding how much work needs to be
done on a feature) and **prioritization** (deciding when that work should get done). Typically, the
priority and scope of work will be recorded on **a product roadmap, which the product manager
negotiates with business stakeholders.**"

> Note the word **negotiates**. The roadmap is characterised here as the outcome of a negotiation
> with the business, not as a plan the PM authors. That is consistent with
> [../05-planning/roadmap-communication.md](../05-planning/roadmap-communication.md).

### Design's role
[S115]'s remaining sections — "The Role of Design in Desirability / Viability / Feasibility" — did
not extract. Its summary states the thesis: "**Designers are expected to make products not only
desirable, but also viable and feasible.**"

> Even without the detail, the claim is clear and is the mirror of the misconception above:
> **design's contribution is not confined to desirability**, just as engineering's is not confined
> to feasibility.

## Limitations

- **Three of [S115]'s sections did not extract** — design's role across the three DVF dimensions,
  which is the article's actual subject.
- **[S115] is written from a design perspective** by a UX research organization. Its account of the
  PM and engineering roles is an informed outside view, not those roles' self-description.
- **IDEO's own DVF material is not in the corpus**; the attribution is second-hand.
- **The claim that the triad is "the most common pattern"** is asserted without data.
- **No treatment of how the triad scales**, what happens with multiple squads, or how triads relate
  to a product owner in Scrum.
- **No treatment of what to do when the triad disagrees** — the decision procedure when joint
  ownership produces deadlock is not addressed.

## Related concepts

- [ux-for-product-managers.md](ux-for-product-managers.md)
- [product-design-fundamentals.md](product-design-fundamentals.md)
- [../01-foundations/pm-and-ux-collaboration.md](../01-foundations/pm-and-ux-collaboration.md)
- [../01-foundations/product-manager-role.md](../01-foundations/product-manager-role.md) — Eriksson's three pillars
- [../01-foundations/product-management.md](../01-foundations/product-management.md) — valuable/usable/feasible
- [../07-execution/working-with-engineering.md](../07-execution/working-with-engineering.md)
- [../02-discovery/product-discovery.md](../02-discovery/product-discovery.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S115 | Nielsen Norman Group (Pavel Samsonov) — *The Product Triad: Design's Role*, 18 Jul 2025 | UX research organization | Entire document: definition, DVF origins, the ownership misconception, role descriptions |
| S122 | Productboard — *10 Essential Product Management Skills* | Vendor blog | Valuable/usable/feasible formulation |
