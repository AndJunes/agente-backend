---
title: Cross-Functional Product Collaboration
domain: execution
type: practice
topics:
  - product collaboration
  - cross-functional teams
  - shared vision
  - team structure
  - over-collaboration
  - stopping work
source_count: 3
sources: [S008, S019, S049]
evidence_type: practitioner-opinion
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Cross-Functional Product Collaboration

## The premise

[S008]: "Bringing a product to life is **a complex process that involves many teams, and if you
aren't working together effectively, everything can quickly fall apart.**"

Its contributors are named practitioners: **Adrienne Tan** (CEO, Brainmates), **Kathryn
Shepherd-King** (General Manager, Brainmates), **Valentina Dunoski** (former Head of Product at CBA,
UBank), **Sandeep Gondekar** (Director of Client Services, Brainmates).

## Ingredient 1 — Shared vision and strategy

**Collaboration must extend beyond product people** — Kathryn Shepherd-King, quoted in [S008]:
"**The most important thing is that we're collaborating with more than product people.**"

"**The entire business needs to know where they're going, what the guardrails are, how to get
there, and what you're focused on.**"

### The counterintuitive point: a shared vision limits collaboration, productively

Valentina Dunoski, quoted in [S008]:

> "**There's this tendency in tech companies for over-collaboration.** Having a clear North Star
> helps us know where we're going and the things we need to solve for our end customers."

> **Collaboration is not free.** More people in more conversations costs attention and slows
> decisions. A shared vision reduces the *need* to collaborate on every question, because people
> can decide alone within known guardrails. This is the same mechanism [S078] calls building "a
> shared brain" — see
> [../01-foundations/product-manager-role.md](../01-foundations/product-manager-role.md) — and what
> [S116] calls the trust–communication curve: more trust, less required communication. See
> [../05-planning/roadmap-communication.md](../05-planning/roadmap-communication.md).

### Alignment is what makes stopping possible

Kathryn Shepherd-King, quoted in [S008]:

> "While having a shared vision and strategy helps get people on board for **what you should be
> doing**, it also crucially helps everyone better understand **what they should stop doing.**
> **Being aligned as a team lets you surface the rationale of why something should be stopped**
> (e.g., revenue objectives, customer feedback, etc.)."

And: "**Whether you're killing something or launching something new, celebrate all your
milestones** and make sure everything's taking you down the path to achieving your outcome."

> This is a rare and valuable observation. Most alignment guidance is about **starting** things
> together. Stopping is harder and more politically costly, and it requires a shared standard to
> appeal to. Compare [S040] on declining feature requests using the outcome as the decision tool
> ([../05-planning/outcome-based-roadmaps.md](../05-planning/outcome-based-roadmaps.md)), and
> [S031] on writing the kill condition before launch
> ([../05-planning/prioritization.md](../05-planning/prioritization.md)).

## Ingredient 2 — The right capabilities and structure

Kathryn Shepherd-King, quoted in [S008]: "**You need to ensure that the right people are grouped
together to get the highest-performing team. Different people bring different things to the table —
it's not as simple as a role.**"

> "Not as simple as a role" is the same finding [S064] reports from survey data — that some teams
> now hire for **skills rather than roles**, with specific benefits and costs. See
> [../01-foundations/pm-and-ux-collaboration.md](../01-foundations/pm-and-ux-collaboration.md).

**On skill gaps** [S008]: "By looking at your team's **holistic performance**, you can remove skill
gaps to more effectively drive your strategy forward."

**On direction versus orders** — Sandeep Gondekar, quoted in [S008]:

> "**You don't often hear Product Managers talk about outcomes and customer value, but rather
> features and functionality.** But before you can tackle features, **you first need to empower
> your team to bring their expertise to drive value. In the right structure, it's not about giving
> orders, but about giving direction.**"

**On discovery as a capability** [S008]: Shepherd-King "emphasizes that **discovery is a vital, but
often underrated, capability in product**" *(the supporting passage did not extract)*. This
corroborates [S110]'s account of why discovery gets skipped — see
[../02-discovery/product-discovery.md](../02-discovery/product-discovery.md).

> [S008]'s remaining four "ingredients" did not extract from the source.

## Collaboration at scale

[S019] (a practitioner guest post) addresses what changes as an organization grows. Its substantive
points:

### A consistent prioritization framework across teams
> "Try to work with the other PMs to **build a common prioritization framework for validating
> feature demand. Get this framework accepted in the organisation through consensus** and then move
> quickly in communicating that. **You will see the benefits of aligning all teams to a common set
> of rules, a form of checks and balances before they seek the most precious thing of them all:
> engineering bandwidth.**" [S019]

Its cautions:
- **Do** "re-visit your framework when it shows signs of incompatibility with the org needs"
- **Don't** "**constantly change your framework to satisfy stakeholders. It will be far more
  counter-productive for your company and customer goals.**"

> "**Engineering bandwidth** as the scarcest resource" is a useful framing: a shared prioritization
> framework functions as an allocation mechanism for it, and its legitimacy depends on being stable.

### Feedback at scale
> "There are **no perfect tools** for Product Management... But that does not stop us from setting
> and reinforcing feedback loops that feed the backlog with **customer demands, stakeholder needs,
> platform and market trends.** You may have social media, community support, customer support,
> direct calls, emails, analytics, meeting notes, leadership steers, tech ticketing tools...
> **Find a way to create a system of record that serves as the single source of truth for all
> needs.**" [S019]

See [../05-planning/backlog-management.md](../05-planning/backlog-management.md).

### Transparent KPIs
[S019]: "**Setting clear OKRs will not only inform the KPIs that measure performance but will also
ensure the organization is aligned**... If you don't have OKRs in your org, it isn't the end of the
world. **If there is a clear goal that you can align your prioritization framework with, the metrics
become relatively clear.**"

Its caution: "**Don't come up with a sea of KPIs. You will hypnotize yourself and your stakeholders.
Try splitting the primary and secondary KPIs.**"

And a data-quality point: "**Do check for data sanity and accuracy. There is no point of surfacing
data that has errors baked in.**"

### Automation-first design
[S019] argues for a specific design stance at scale:

> "**A good Product Manager will build features that delight customers. A great Product Manager with
> scale in mind will build capabilities that delight the customers and satisfy internal
> stakeholders.** Talk to your Operations, Engineering and DevOps and ask **where the underlying
> design would have manual components and what would it take to automate them.**"
>
> "Traditional approaches include **starting with a human-run operation, automating as much activity
> as possible**... Using the automation-first approach means you **begin with automating as much as
> possible, then bring in people to do the tasks that digital labour cannot handle.**"

**Its own counterweight** [S019]: "**Don't obsess over automation.** It sounds counter-intuitive,
yes; but **unless you have unlimited engineering bandwidth, trade-offs will be made for
time-to-market.** Just remember to pick up the smaller manual bits when the dust settles."

> The automation-first framing is directly relevant to products that incorporate AI agents, where
> the question of *what the system does versus what a human does* is a primary design decision
> rather than an efficiency optimisation. The corpus contains almost nothing else on this. See
> [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

## Engineering collaboration specifically

Treated in [working-with-engineering.md](working-with-engineering.md), including the
mutual-expectations model from [S049].

## Limitations

- **[S008] is a vendor blog** (Productboard) summarising a video interview; **four of its six
  "ingredients" did not extract**, so this document covers only the first two.
- **[S019] is a guest post by a PM early in their career**, who says so explicitly: "**I am still
  new to product management and learning the ropes.**" Its advice is experiential and should be
  weighted accordingly — though several points (shared prioritization framework, system of record,
  primary/secondary KPI split) are corroborated elsewhere in this knowledge base.
- **No evidence** for any claim in this document.
- **No treatment of conflict resolution** between functions, remote or distributed collaboration,
  meeting design, or decision rights (RACI or equivalents) — though [S064] establishes that
  **unclear decision rights are a measured problem**.
- **No treatment of collaboration with sales, support, legal, or finance**, beyond their appearance
  in stakeholder lists.

## Related concepts

- [working-with-engineering.md](working-with-engineering.md)
- [agile-manifesto.md](agile-manifesto.md)
- [product-development-process.md](product-development-process.md)
- [../01-foundations/pm-and-ux-collaboration.md](../01-foundations/pm-and-ux-collaboration.md)
- [../05-planning/roadmap-communication.md](../05-planning/roadmap-communication.md)
- [../05-planning/prioritization.md](../05-planning/prioritization.md)
- [../04-strategy/okrs.md](../04-strategy/okrs.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S008 | Productboard — *6 Keys to Effective Product Collaboration*, 27 Aug 2023 | Vendor blog summarising named practitioners (Brainmates) | Shared vision, over-collaboration, stopping work, capabilities and structure |
| S019 | Product School (guest, Schandre Terblanche) — *The Do's and Don'ts of Scaling Product Management*, updated 25 Apr 2024 | Practitioner guest post; author self-describes as early-career | Shared prioritization framework, feedback at scale, transparent KPIs, automation-first |
| S049 | LogRocket — *How top product managers work with engineers* | Vendor blog | Cross-functional positioning of the PM role |
