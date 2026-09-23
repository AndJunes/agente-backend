---
title: Kanban (the Kanban Method)
domain: execution
type: framework
topics:
  - kanban
  - kanban method
  - kanban system
  - wip limits
  - work in progress
  - pull system
  - flow
  - lead time
  - delivery rate
  - throughput
  - cumulative flow diagram
  - Little's Law
  - cost of delay
  - classes of service
  - cadences
  - STATIK
  - probabilistic forecasting
  - service level expectation
synonyms:
  - kanban board
  - flow-based method
  - pull system
  - evolutionary change method
source_count: 3
sources: [E003, E004, E005]
evidence_type: primary-text-quoted
confidence: high
corpus_origin: false
external_research: true
verified: true
phase: 2
provenance:
  primary: [E003, E004]
  interpretation: [S078, S126, S130, S048]
  practice: [E003]
  empirical: [E006]
last_reviewed: 2026-09-16
---

# Kanban (the Kanban Method)

> **Phase-2 document.** The original corpus named Kanban at least four times and **defined it
> never** — and in every case used it to mean *a board layout*. That is a category error this
> document corrects from the primary texts.
>
> **Primary sources:** [E003] Anderson & Carmichael, *Essential Kanban Condensed*, Lean Kanban
> University Press, 2016 · [E004] Kanban University, *The Kanban Guide* (official web guide,
> retrieved September 2026).

## Two different things share the name

| Term | What it means | Capitalisation |
|---|---|---|
| **kanban** | Japanese for *sign / signal card / visual board*. A **signalling token**. Used in process definition since the 1960s, when Toyota named its WIP-limiting factory systems "kanban systems" | lowercase |
| **a kanban system** | A delivery flow system that **limits work in progress using visual signals**, with a defined commitment point and delivery point | lowercase |
| **The Kanban Method** | A **management method** for defining, managing and improving knowledge-work services — values, principles, practices, cadences, roles, metrics | Capitalised |

> **⚠ CORRECTION to the original corpus.** [S130] listed a "Kanban roadmap" as a *roadmap format*
> "similar to a Kanban board"; [S048] listed "Kanban boards" alongside Gantt and burndown charts as
> tracking tools; [S126] described stories flowing through a Kanban board. **All four corpus
> references treat Kanban as a board.** A board is one visualisation used by the method; a board
> without WIP limits, a commitment point and a delivery point is **not a kanban system at all** —
> it is a flow system. [E003] states the condition explicitly: "*For it to be a kanban system
> rather than simply a flow system, the commitment and delivery points must be defined, and WiP
> Limits must be displayed.*" This correction is applied in
> [../05-planning/roadmap-formats.md](../05-planning/roadmap-formats.md) and recorded in
> [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

## Definition

[E003]: Kanban is **"a method for defining, managing, and improving services that deliver knowledge
work"** — professional services, creative work, and the design of physical and software products.

Two characterisations from the primary texts:

- **"Start from what you do now."** [E003] describes it as a catalyst for change that *"reduces
  resistance to beneficial change in line with the organization's goals."*
- **Applied to an existing process, not replacing one.** [E004]: *"Kanban is a management method or
  approach that should be applied to an existing process or way of working."*

### How the mechanism works

The method makes otherwise-intangible knowledge work visible so a service works on **the right
amount of work** — work the customer needs and the service has the capability to deliver. Signals
displayed on a board represent **WIP Limits**, and those limit policies create a **pull system**:
[E003] — work is *"'pulled' into the system when other work is completed and capacity becomes
available, rather than 'pushed' into it when new work is demanded."*

> **This is the single most important idea in the method**, and the one entirely absent from the
> corpus. Most product organisations operate push systems: work is assigned because it has been
> prioritised, regardless of whether capacity exists. Kanban inverts the trigger.

## Origin and provenance

| Claim | Status |
|---|---|
| **The Kanban Method was developed by David J. Anderson**, from work at Microsoft and then a project at **Corbis, 2006–2007**; the method with its six practices was named in 2007 | Well attested, including by Anderson's own published account. **[PROVENANCE: originator.]** |
| **First book-length description:** Anderson, *Kanban: Successful Evolutionary Change for Your Technology Business*, 2010 [E005] | **NOT CONSULTED for this document.** Cited as bibliography only — do not attribute quotations to it |
| **The concept of kanban signalling** originates with Toyota's manufacturing systems, 1960s | Attested, but predates and is distinct from the Kanban Method |

> **Provenance distinction the reader must keep.** Everything below comes from [E003] and [E004] —
> the **official, current articulation of the method** by its originator and Lean Kanban University.
> It is *not* the 2010 book (later developments such as the seven cadences, STATIK and the nine
> values are not all in it), *not* Toyota, and *not* the popular usage of "kanban" to mean a board.

## The three agendas

[E003] identifies three reasons an organisation adopts the method:

| Agenda | Direction | Concern |
|---|---|---|
| **Sustainability** | Looks **inward** | Finding a sustainable pace, improving focus, balancing demand with capability, reducing overburdening |
| **Service Orientation** | Looks **outward** to customers | Performance and customer satisfaction — services that are *fit for purpose* |
| **Survivability** | Looks **forward** | Staying competitive and adaptive as markets and technology change |

> The Sustainability Agenda is the same concern as Agile principle 8 (constant pace indefinitely) —
> see [agile-manifesto.md](agile-manifesto.md) — but Kanban gives it a mechanism (WIP limits)
> rather than only a commitment.

## The nine values

[E003]: the method *"is values led"* and its values *"may be summed up in that single word,
'respect'"*, expanded into nine:

**Transparency · Balance · Collaboration · Customer Focus · Flow · Leadership · Understanding ·
Agreement · Respect**

Two worth noting for product work:

- **Balance** — [E003] warns that some aspects, *"such as demand and capability, will cause
  breakdown if they are out of balance for an extended period."*
- **Agreement** — explicitly *"not management by consensus, but a dynamic co-commitment to
  improvement."*

[E003] states the method *"cannot be applied faithfully without embracing them."*

## The six foundational principles

Split into two groups — and the split matters, because the first group is about **how to change an
organisation** and the second about **how to run a service**.

### Change management principles
Premised on the observation that an organisation is *"a network of individuals, psychologically and
sociologically wired to resist change"* [E003]:

1. **Start with what you do now** — understanding current processes *as they are actually
   practised*, and **respecting existing roles, responsibilities and job titles**
2. **Agree to pursue improvement through evolutionary change**
3. **Encourage acts of leadership at every level** — from individual contributor to senior
   management

[E003] gives two reasons for "starting from here": minimising resistance by respecting current
practice and practitioners; and that current processes *"contain wisdom and resilience that even
those working with them may not fully appreciate."* Starting from current practice also
**establishes the performance baseline** against which future change is assessed.

> **This is the sharpest contrast with Scrum in either primary text.** [E001] defines a target state
> and says implementing only parts of it is not Scrum. [E003] defines *no* target state and requires
> you to begin from whatever you already do. A team choosing between them is choosing between
> **revolutionary adoption** and **evolutionary improvement** — not between two board layouts. See
> [scrum.md](scrum.md).

### Service delivery principles
Premised on an organisation being *"an ecosystem of interdependent services"*:

1. **Understand and focus on your customers' needs and expectations**
2. **Manage the work; let people self-organize around it**
3. **Evolve policies to improve customer and business outcomes**

[E003] names the failure these correct: when work and flow are invisible, *"organizations often
focus instead on what is visible, the people working on the service. Are they always busy? Are they
skilled enough? Could they work harder?"* — while the customer and the work items get less
attention.

## The six general practices

| Practice | What it requires [E003] |
|---|---|
| **1. Visualize** | Make work **and the policies governing it** visible. The method does not constrain board design |
| **2. Limit Work in Progress** | WIP limits turn a push system into a pull system. Excess partially-complete work *"is wasteful and expensive and, crucially, it lengthens lead times"* |
| **3. Manage Flow** | Maximise value delivery, minimise lead time, make flow **smooth and predictable**. Manage **bottlenecks** (internal constraints) and **blockers** (external dependencies) |
| **4. Make Policies Explicit** | Policies must be *"sparse, simple, well-defined, visible, always applied, and readily changeable by those providing the service"* |
| **5. Implement Feedback Loops** | Seven named cadences (below) |
| **6. Improve Collaboratively, Evolve Experimentally** | Change through designed experiments — keep and amplify useful change, reverse or dampen ineffective change |

### On practice 4 — a warning the corpus has no equivalent for
[E003]: *"always applied" and "readily changeable" go together.* Setting WIP limits and then never
challenging or changing them *"would be a poor application of this principle."* And: complex system
behaviour cannot be predicted from simple policies — intuitive policies *"(for example, 'the sooner
you start, the sooner you'll finish') often produce counterintuitive results."*

> [E003] names the **Definition of Done** as one kind of explicit policy, alongside WIP limits,
> capacity allocation and replenishment policies. That usage is consistent with [E001]'s — a
> team-level quality standard, not item-level acceptance criteria. See
> [../06-requirements/acceptance-criteria.md](../06-requirements/acceptance-criteria.md).

## Flow metrics and Little's Law

The method's measurement layer, entirely absent from the corpus.

**Minimum data to collect** [E003]: **Lead Time, Delivery Rate, WIP, and cost** (usually
person-days).

### Little's Law
In a **non-trending** flow system where all selected items are delivered, there is a fixed
relationship between the averages of these metrics:

> **average Lead Time = average WIP ÷ average Delivery Rate**

- Use **Time in Process (TiP)** instead of Lead Time when measuring a segment rather than
  commitment-to-delivery; more specific variants include Time in Development, Time in Test, Time in
  Queue, Time in System.
- Use **Throughput** instead of Delivery Rate when the segment does not end at the delivery point.
- It can be read off a **Cumulative Flow Diagram**, where the slope of the hypotenuse is the average
  delivery rate.

> **The consequence [E003] draws:** *"In order to optimize the Lead Time for work items, we must
> limit the Work in Progress."* This is why practice 2 exists. **WIP limits are not a discipline
> device — they are the only lever on lead time that does not require adding capacity.**
>
> ⚠ **Conditions matter.** The law holds *on averages*, in a *non-trending* system, where selected
> items are actually delivered. A team whose backlog is growing, or that abandons work in progress,
> is outside its assumptions. [E003] is explicit about this; most secondary presentations of
> Little's Law are not. Little's original proof is Little (1961), *Operations Research*.

### Cost of delay and classes of service
[E003] defines **cost of delay** as *"the amount of an item's value that is lost by delaying its
implementation by a specified period of time."* It is a function of time, and the rate of value
change (urgency) need not be constant.

Four **archetypes** characterise how value decays: **expedite · fixed date · standard ·
intangible.** These can order work items, or define **classes of service** with different policies.

> This is a **prioritisation model the corpus does not contain** — orthogonal to RICE, MoSCoW and
> value-vs-effort in [../05-planning/prioritization-frameworks.md](../05-planning/prioritization-frameworks.md),
> because it prices *waiting* rather than ranking *items*. It is also the conceptual parent of WSJF,
> listed as a Priority-2 gap in [../RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

### Four service levels
[E003] distinguishes terms that are commonly conflated:

| Term | Meaning |
|---|---|
| **Service Level Expectation** | What the customer expects |
| **Service Level Capability** | What the system can actually deliver |
| **Service Level Agreement** | What is agreed with the customer |
| **Service Fitness Threshold** | The level below which delivery is unacceptable to the customer |

## Probabilistic forecasting — the Kanban answer to estimation

This section closes part of Priority-1 gap 1.4; see [../05-planning/estimation.md](../05-planning/estimation.md).

[E003] describes traditional **"effort-plus-risk estimating"** — decompose, sum effort estimates,
fix either a date or a team size, and inflate by a risk factor *"of between 2 and 10."* Its verdict:

> *"This method has often proven spectacularly unsuccessful on all sizes of projects, but
> particularly on large and critical ones. Surprisingly, it still is the dominant method of
> forecasting."* [E003]

**The alternative:** once a kanban system is running, forecast from **observed flow** rather than
from estimates. A **Monte Carlo** model, fed with historical item-size variability, lead times and
delivery rates, runs many randomised scenarios and produces a **probability distribution over
completion dates** — quoted at, for example, 50%, 85% and 95% confidence.

Where no historical data exists, [E003] permits **range estimates** until real data accumulates.

> **Provenance caution.** [E003] asserts that effort-plus-risk estimating fails and that
> probabilistic forecasting is better; it hedges its own claim with *"some would say more
> reliable."* **No controlled study is cited in the text for that comparison.**
> **[EMPIRICAL: asserted by the method's authors, not independently verified in this knowledge
> base.]** What *is* independently supported is the underlying mathematics — Little's Law and Monte
> Carlo simulation are standard operations research, not Kanban inventions.

## Cadences — the seven feedback loops

[E003]: *"Cadences are the cyclical meetings and reviews that drive evolutionary change and
effective service delivery."* "Cadence" also names the interval between reviews.

| # | Cadence | Purpose | Scope |
|---|---|---|---|
| 1 | **Strategy Review** | Select which services to provide; define *fit for purpose*; sense the external environment | Multi-service |
| 2 | **Operations Review** | Balance across services; deploy resources to maximise value delivery | Multi-service |
| 3 | **Risk Review** | Understand risks to delivery — e.g. blocker clustering | Multi-service |
| 4 | **Service Delivery Review** | Examine and improve the effectiveness of one service | Single service |
| 5 | **Replenishment Meeting** | Move items over the **commitment point** into the system; prepare future options | Single service |
| 6 | **The Kanban Meeting** | Usually daily coordination, self-organisation and planning. Often a stand-up, focused on **completing items and unblocking issues** | Single service |
| 7 | **Delivery Planning Meeting** | Monitor and plan deliveries to customers | Single service |

**Two qualifications [E003] states explicitly:**
- This is **not seven new meetings.** Initially each cadence's *agenda* should be folded into
  existing meetings; one meeting may cover several cadences.
- Only the **Replenishment and Kanban Meetings** are *"considered a baseline in nearly all Kanban
  implementations."*
- Cadence frequency is context-dependent: too frequent and you change things before seeing the last
  change's effect; too infrequent and poor performance persists longer than necessary.

> **Compare with Scrum's Daily Scrum.** [E001] fixes the Daily Scrum at 15 minutes for the
> Developers, inspecting progress toward the Sprint Goal. The Kanban Meeting has no fixed timebox
> and is oriented to **flow** — what is blocked, what can be finished — not to a goal. **Boards can
> look identical while these two meetings do different work.**

## Roles

[E003] is emphatic: *"there are no required roles in Kanban and the method does not create new
positions in the organization."* Two roles nonetheless **emerged from practice** and are now defined
— described as *"hats" people wear*, not job titles:

| Role | Responsible for | Alternative names given in [E003] |
|---|---|---|
| **Service Request Manager** | Understanding customer needs and expectations; facilitating selection and ordering of work items at the Replenishment Meeting | **Product Manager, Product Owner,** Service Manager |
| **Service Delivery Manager** | Flow of work delivering selected items; facilitating the Kanban Meeting and Delivery Planning | Flow Manager, Delivery Manager, Flow Master |

> **Direct evidence for a corpus dispute.** [E003] treats **Product Manager and Product Owner as
> interchangeable alternative names for the same function** — understanding customer needs and
> ordering the input queue. [E001] defines Product Owner as a distinct accountability and never
> mentions Product Manager. The corpus sources disagree with each other and with both.
> **This is a genuine three-way disagreement between primary sources, not an error to be resolved.**
> Recorded in
> [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)
> and [../99-reference/disputed-information.md](../99-reference/disputed-information.md).

## STATIK — how to introduce Kanban

**Systems Thinking Approach to Introducing Kanban.** The steps are **iterative, not sequential**;
[E003] says the order may vary and revisiting steps is normal.

> **Step 0** Identify services.
> *Then, for each service:*
> **1** Understand what makes the service **fit for purpose** for the customer ·
> **2** Understand **sources of dissatisfaction** with the current system ·
> **3** Analyze **demand** ·
> **4** Analyze **capability** ·
> **5** Model **workflow** ·
> **6** Discover **classes of service** ·
> **7** Design the kanban system ·
> **8** Socialize the system and board design, and negotiate implementation.

[E003] warns that improving services in isolation produces **sub-optimisation**, and suggests
starting with higher-level services that deliver directly to customers rather than internal ones.

## The Kanban Litmus Test

Four questions, each a prerequisite for the next, for assessing how far an adoption has actually
gone [E003]:

1. **Has management behavior changed** to enable Kanban?
2. **Has the customer interface changed** in line with Kanban?
3. **Has the customer contract changed**, informed by Kanban?
4. **Has your service delivery business model changed** to exploit Kanban?

> **This is Kanban's equivalent of the cargo-cult-agile diagnostic in
> [agile-manifesto.md](agile-manifesto.md)** — and it is more demanding. Question 1 alone disqualifies
> most adoptions: a team can run a board with WIP limits for years while management behaviour is
> unchanged. Note that **not one of the four questions asks about the board.**

## Limitations

- **Sourced from the method's own official literature.** [E003] and [E004] are published by Lean
  Kanban University, which sells Kanban training and accreditation. The texts are technically
  substantive and unusually precise, but they are **not disinterested**, and no critical or
  independent treatment of the method was consulted.
- **No empirical evidence of effectiveness** is presented here. [E003] claims WIP limits produce
  *"improved lead time for services, improved quality, and a higher rate of deliveries"* and
  footnotes a supporting reference; **that reference was not retrieved or checked.**
  **[EMPIRICAL: not established in this knowledge base.]**
- **Little's Law is mathematics; the rest is method.** Do not let the rigour of the former transfer
  credibility to the latter.
- **Anderson's 2010 book was not consulted.** Historical claims about the method's development come
  from secondary accounts and are marked as such above.
- **Diagrams are not reproduced.** [E003] carries figures (cumulative flow diagram, cost-of-delay
  graphs, cadence network, board examples) that this text describes but cannot show. The source is
  freely downloadable from Kanban University.
- **The method says nothing about product discovery, strategy or what to build.** It is a delivery
  and improvement method. Pairing it with the discovery material in
  [../02-discovery/](../02-discovery/) is a choice this knowledge base makes, not one [E003] argues
  for.
- **Scaling, portfolio Kanban and Kanban Maturity Model** are outside this document.

## Related concepts

- [scrum.md](scrum.md) — the alternative, with an opposite theory of change
- [agile-manifesto.md](agile-manifesto.md)
- [working-with-engineering.md](working-with-engineering.md)
- [project-monitoring-and-control.md](project-monitoring-and-control.md) — corrected by this document's metrics section
- [../05-planning/estimation.md](../05-planning/estimation.md) — probabilistic forecasting as an alternative
- [../05-planning/prioritization-frameworks.md](../05-planning/prioritization-frameworks.md) — cost of delay as an orthogonal model
- [../05-planning/roadmap-formats.md](../05-planning/roadmap-formats.md) — corrected: "Kanban roadmap" is a board, not a kanban system
- [../05-planning/dependencies.md](../05-planning/dependencies.md) — blockers vs bottlenecks
- [../01-foundations/product-manager-vs-product-owner.md](../01-foundations/product-manager-vs-product-owner.md)

## Sources

| ID | Source | Type | Provenance | Used for |
|---|---|---|---|---|
| E003 | **Anderson, David J. & Carmichael, Andy — *Essential Kanban Condensed*, Lean Kanban University Press, 2016** (1st digital ed., 17 April 2016) | **Official condensed guide, co-authored by the method's originator** | `PRIMARY` | Definition, values, agendas, six principles, six practices, Little's Law, flow metrics, cost of delay, service levels, probabilistic forecasting, seven cadences, roles, STATIK, litmus test |
| E004 | Kanban University — *The Kanban Guide* (kanban.university/kanban-guide), retrieved September 2026 | Official web guide | `PRIMARY` | Cross-check of principles and practices; the "applied to an existing process" statement |
| E005 | Anderson, David J. — *Kanban: Successful Evolutionary Change for Your Technology Business*, 2010 | Originating book | `BIBLIOGRAPHY ONLY` | **Not consulted.** Listed because it is the method's first full description; nothing in this document is attributed to it |
| — | Little, J. D. C., *A Proof for the Queuing Formula: L = λW*, Operations Research, 1961 | Academic primary | `BIBLIOGRAPHY ONLY` | Cited by [E003] as the origin of Little's Law; not retrieved |
