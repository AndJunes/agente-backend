---
title: Service Design
domain: design-and-ux
type: concept
topics:
  - service design
  - service blueprint
  - people props processes
  - frontstage backstage
  - goods-services continuum
  - internal processes
source_count: 3
sources: [S103, S102, S112]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# Service Design

## Definition

[S103] (Nielsen Norman Group, Sarah Gibbons, 9 July 2017):

> "**Service design: The activity of planning and organizing a business's resources (people, props,
> and processes) in order to (1) directly improve the *employee's* experience, and (2) indirectly,
> the *customer's* experience.**"

[S102] (IxDF): "Service design is concerned with **the design of services and making them better
suit the needs of the service's users and customers. It examines all activities, infrastructure,
communication, people, and material components involved in the service to improve both quality of
service and interactions between the provider of the service and its customers.**"

> **Note the causal direction in [S103]'s definition.** Service design improves the customer
> experience **indirectly, by improving the employee's.** That is the distinctive claim, and it is
> what separates service design from UX design.

## Why a product manager should care

[S103] makes the argument concretely:

> "**Most organizations are centered around products and delivery channels. Many of the
> organizations' resources (time, budget, logistics) are spent on customer-facing outputs, and the
> internal processes (including the experience of the organization's employees) are overlooked;
> service design focuses on these internal processes.**"

And the failure mode it explains:

> "**Complex user experiences often break due to an internal organizational shortcoming — a weak
> link in the ecosystem.** For example, **when was the last time you called a support hotline, gave
> your personal information, only to be transferred to another agent asking you to repeat the exact
> information you had already provided? This pain point stems from an internal process flaw that
> was produced by a lack of service design.**" [S103]

> **This is the key insight for a product manager:** some user-facing problems cannot be fixed in
> the product, because their cause is an internal process or handoff. Diagnosing a problem as a UX
> problem when it is a service problem produces interface changes that do not work.

## The goods–services continuum

[S103] explains why the distinction has eroded:

> "Traditional economics draws a clear distinction between goods and services. **Goods are tangible
> and consumable** — pens, sunglasses, shoes. **Services are instantaneous exchanges that are
> intangible and do not result in ownership** — medical treatment, the postal service, public
> transportation.
>
> **Today, there is no longer a clear distinction.** A continuum of goods–services exists with a
> plethora of combined products and services in the middle. For example, **a song (an mp3 file) is
> a product that can be accessed via a service like Spotify or Apple Music. To the user, the
> difference between a product and service — owning the sound file versus streaming the song — can
> be close to identical while behind the scenes they are quite different.**"

[S112] (Andy Budd, Mind the Product) addresses the same shift under the title *The Move From Product
to a Service Mindset*, with sections on "Selling a Service," "Service Design," and "The Experience
Economy."

> Most software products sold by subscription are **services in this sense**: the customer's
> experience includes onboarding, support, billing, incident response and offboarding — none of
> which is the interface. A product manager who treats only the interface as "the product" is
> managing a fraction of the experience.

## The three components

[S103]: "The three main components of service design are **people, props, and processes.**"

| Component | Definition [S103] | Examples given |
|---|---|---|
| **People** | "Anyone who **creates or uses** the service, as well as **individuals who may be indirectly affected** by the service" | Employees; "fellow customers encountered throughout the service" |
| **Props** | "The **physical or digital artifacts (including products)** that are needed to perform the service successfully" | Physical space (storefront, teller window, conference room); digital environment (webpages, blogs, social media); objects and collateral (digital files, physical products) |
| **Processes** | *(The section did not extract; the term is defined by context as the workflows and procedures that deliver the service)* | — |

[S103] frames the integration requirement by analogy with UX: "In user experience design multiple
components must be designed: visuals, features and commands, copywriting, information architecture,
and more. **Not only must each component be designed correctly, but they also must be integrated to
create a total user experience. Service design follows the same basic idea.**"

> The inclusion of **"fellow customers encountered throughout the service"** under People is worth
> noticing — other users are part of the designed experience, which is obvious in a restaurant and
> easy to forget in a marketplace or community product.

## A worked illustration

[S103]'s restaurant example makes the scope concrete:

> "Imagine a restaurant where there are a range of employees: hosts, servers, busboys, and chefs.
> **Service design focuses on how the restaurant operates and delivers the food it promises — from
> sourcing and receiving ingredients, to on-boarding new chefs, to server-chef communication
> regarding a diner's allergies. Each moving part plays a role in the food that arrives on the
> diner's plate, even though it is not directly part of their experience.**"

## Tools and related concepts named

[S103] names several without developing them in the extracted text:

| Concept | What [S103] says |
|---|---|
| **Service blueprint** | "Service design can be **mapped using a service blueprint**" |
| **Frontstage vs backstage** | Named as a section; the distinction between customer-visible and internal activity |
| **Service design vs designing a service** | Named as a section — a distinction the corpus does not deliver |
| **Journey mapping** | "Journey Mapping to Understand Customer Needs" |
| **Lean UX and Agile** | Named as a related section |
| **History of service design** | Named; [S102] refers to "A Brief History of Service Design" |

> ⚠ **The service blueprint — the discipline's primary artefact — is named but never explained
> anywhere in the corpus.** Neither is the frontstage/backstage distinction, despite both being
> core. Recorded in [RESEARCH_BACKLOG.md](../RESEARCH_BACKLOG.md).

[S028] independently names the **service blueprint** as a possible discovery output, alongside
user-journey maps. See
[../02-discovery/product-discovery.md](../02-discovery/product-discovery.md).

## Where this connects

| Connection | Why |
|---|---|
| **Platform PM specialization** | [S111] lists **service design** among the key skills of a platform PM, whose "customers are internal stakeholders and other product teams." See [../01-foundations/pm-specializations.md](../01-foundations/pm-specializations.md) |
| **Product risk** | [S087] names "**inadequate onboarding or user education**" and "**missing key integrations**" as product risks — both are service-level failures, not interface failures. See [../10-risk/product-risk.md](../10-risk/product-risk.md) |
| **End-of-life** | [S118]'s shutdown obligations — data portability, migration assistance, support and partner communication — are service-design concerns. See [../11-lifecycle-and-launch/decline-and-end-of-life.md](../11-lifecycle-and-launch/decline-and-end-of-life.md) |
| **Customer journey mapping** | [S009] and [S110] both treat journey mapping; service design extends it behind the scenes |

## Limitations

- **[S103] is substantially truncated** — the Processes component, frontstage/backstage, service
  blueprinting, the history, and the Lean UX/Agile connection are all headings without content.
- **[S102] is a one-page IxDF stub** (~270 words) contributing only a definition.
- **[S112] did not extract substantively** beyond its section structure.
- **No method.** The corpus explains what service design *is* and why it matters, but contains no
  process, no blueprint template, and no guidance on running a service-design engagement.
- **No evidence** of impact.
- **[S103] is dated July 2017** — the concepts are durable, but the examples predate current
  service models.

## Related concepts

- [product-triad.md](product-triad.md)
- [ux-for-product-managers.md](ux-for-product-managers.md)
- [product-design-fundamentals.md](product-design-fundamentals.md)
- [../02-discovery/product-discovery.md](../02-discovery/product-discovery.md) — service blueprints as a discovery output
- [../01-foundations/pm-specializations.md](../01-foundations/pm-specializations.md)
- [../10-risk/product-risk.md](../10-risk/product-risk.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S103 | Nielsen Norman Group (Sarah Gibbons) — *Service Design 101*, 9 Jul 2017 | UX research organization | Definition, goods–services continuum, internal-process argument, three components, restaurant example |
| S102 | Interaction Design Foundation — *Service Design – Design is Not Just for Products* | Glossary stub | Definition |
| S112 | Mind the Product (Andy Budd) — *The Move From Product to a Service Mindset* | Practitioner essay (largely unextracted) | Product-to-service shift framing |
