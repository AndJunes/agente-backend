---
title: IT and Security Risk Assessment
domain: risk
type: process
topics:
  - IT risk
  - security risk
  - threats and vulnerabilities
  - NIST
  - controls
  - impact analysis
  - compliance
source_count: 1
sources: [S050]
evidence_type: professional-practice
confidence: medium
corpus_origin: true
external_research: false
last_reviewed: 2026-09-16
---

# IT and Security Risk Assessment

## Why this is a separate document

Security risk uses a **different vocabulary** from project risk management — *assets, threats,
vulnerabilities, controls* rather than *risks, probability, impact, responses*. The two map onto
each other but are not interchangeable, and a product manager working on anything handling personal
or regulated data will encounter the security framing.

[S087] lists "**regulatory or compliance surprises**" among product risks, and [S081] requires
assessing "regulatory compliance, legal implications, and potential security or privacy concerns
(**especially important if your product involves sensitive user data, AI data analytics, or
regulated industries**)." This document supports that assessment.

## The core distinction: threat versus vulnerability

[S050]: "**A vulnerability is a weakness in your system or processes that might lead to a breach of
information security.**"

A **threat** is what might exploit it. [S050]: "**Hackers are usually top of mind, but threats to
your business's information security come in many different forms. A cyber security threat
assessment should cover external attackers, insider risks, third parties, misconfiguration, and
operational failure** — not just [hackers]."

> **Risk = a threat exploiting a vulnerability against an asset.** All three components are needed;
> a vulnerability with no plausible threat, or a threat with no vulnerability, is not a risk.

## The eight-step process

[S050]'s sequence:

### 1. Identify and catalog your information assets
> "Make sure that you have a **comprehensive list** of your informational assets. It's important to
> remember that **different roles and different departments will have different perspectives on
> what the most important assets are**, so you should get input from more than one source."

### 2. Identify threats
Coverage required: "**external attackers, insider risks, third parties, misconfiguration, and
operational failure.**"

> Note that three of those five are not adversarial. Misconfiguration and operational failure are
> the most common causes of incidents and the easiest to omit from a threat list.

### 3. Identify vulnerabilities
Examples given [S050]: "if your company **stores customers' credit card data but isn't encrypting
it** or testing that encryption process to ensure it's working properly, that's a significant
vulnerability. **Allowing weak passwords, failing to install the most recent security** [patches]"
are others.

Sources of vulnerability information: "**automated vulnerability scanning tools, or the NIST
vulnerability database.**"

**Physical vulnerabilities count too** [S050]: "suppose your employees work with hard copies of
sensitive information or use company electronics outside of the office. In that case, **this can
lead to the misuse of information**, just like [a digital breach]."

### 4. Analyze internal controls
> "Implement controls to minimize or eliminate the vulnerabilities and threats. This could be
> either **control to eliminate the vulnerability itself** or **control to address threats that
> can't be totally eliminated.**"

> This maps directly onto PMI's *avoid* versus *mitigate* distinction — see
> [risk-response.md](risk-response.md).

### 5. Determine likelihood
> "Using all the information you have gathered — **your assets, the threats those assets face, and
> the controls you have in place** — you can now categorize **how likely each of the
> vulnerabilities you found might actually be exploited.** Many organizations use the categories of
> **high, medium, and low.**"

> Likelihood is assessed **after** controls are accounted for. This is *residual* likelihood, not
> inherent likelihood.

### 6. Assess impact
> "This step is known as **impact analysis**, and it should be completed **for each vulnerability
> and threat you have identified, no matter the likelihood of one happening.**"

> The "regardless of likelihood" instruction matters. It prevents the common error of dismissing
> catastrophic-but-unlikely scenarios before their consequence is understood — the same error
> [S106] describes with shark attacks versus car crashes in
> [../04-strategy/strategic-thinking.md](../04-strategy/strategic-thinking.md).
>
> *([S050] states impact analysis "should include three things" but the list did not extract.)*

### 7. Prioritize the risks
> "Prioritizing your security risks will help you determine **which ones warrant immediate action,
> where you should invest your time and resources, and which risks you can address at a later
> time.**"

### 8. Design controls
"Once you've established priorities for all risks you've found and detailed, then you can begin
[designing controls]."

## Named frameworks

[S050] references two, with dates:

| Framework | [S050] |
|---|---|
| **NIST SP 800-30 / NIST Risk Management Framework** | "Originally published in **2002 and updated in 2012**, NIST Special Publication 800-30... is built alongside the gold-standard **NIST CSF** as a means to view an organization's security threats **through a risk-based lens**" |
| **World Economic Forum Cyber Risk Framework and Maturity Model** | "Published in **2015 in collaboration with Deloitte**... **relies on subjective judgments.** The model looks at risk through a lens known as '**value-at-risk**' and asks stakeholders to evaluate three components: **1) existing vulnerabilities and defense maturity of an organization, 2) value of the assets, and 3) profile of an attacker**" |

> **These are the only references to formal standards bodies anywhere in the corpus** besides PMI.
> Neither document is in the corpus; both are named and dated second-hand. **The dates given are
> from a 2026 vendor article and the standards may have been revised since.** Verify before
> relying on version specifics.

## What a product manager takes from this

The corpus does not state this synthesis, but it follows from [S050] combined with [S081] and
[S087]:

1. **Security and privacy are gating constraints, not tradeable features.** [S031] makes the same
   point in prioritization terms: safety, privacy and compliance are "a **hard gate** — treat it as
   a precondition, not a tradeable attribute. **If the gate fails, no score gets you out of it.**"
   See [../05-planning/prioritization-frameworks.md](../05-planning/prioritization-frameworks.md).
2. **Asset identification requires multiple perspectives** — the PM's view of what matters will
   differ from engineering's and legal's.
3. **Non-adversarial threats dominate** — misconfiguration and operational failure belong in any
   honest threat list.
4. **Impact must be assessed regardless of likelihood.**

## Limitations

- **Single source**, and it is a compliance-software vendor (Hyperproof). The article is oriented
  to enterprise IT and GRC, not to product management.
- **Step 6's three components of impact analysis did not extract.**
- **No treatment of privacy-by-design, data minimisation, threat modelling (STRIDE etc.), or secure
  development practices** — all of which a product manager working on data-handling features would
  need.
- **No treatment of regulatory regimes** (GDPR, HIPAA, SOC 2, etc.) beyond passing mentions,
  despite [S086] identifying regulated industries as a primary PRD use case.
- **The framework dates are second-hand and may be stale.** See
  [../99-reference/outdated-information.md](../99-reference/outdated-information.md).
- [S074] separately notes data-protection compliance as a research obligation: "Data protection
  compliance isn't the most exciting aspect of building a product, but you're going to need it if
  you want to be successful. **It's all about building trust.**" That is the corpus's only other
  compliance guidance.

## Related concepts

- [risk-assessment.md](risk-assessment.md)
- [risk-response.md](risk-response.md)
- [product-risk.md](product-risk.md) — regulatory and compliance surprises as a product risk
- [../02-discovery/opportunity-assessment.md](../02-discovery/opportunity-assessment.md) — operational constraint assessment
- [../05-planning/prioritization-frameworks.md](../05-planning/prioritization-frameworks.md) — the safety/privacy/compliance hard gate
- [../07-execution/working-with-engineering.md](../07-execution/working-with-engineering.md)

## Sources

| ID | Source | Type | Used for |
|---|---|---|---|
| S050 | Hyperproof (Maggie Paulk Welch) — *How to Perform an Effective IT Risk Assessment*, 10 Aug 2026 | Compliance-software vendor guide | Threat/vulnerability distinction, eight-step process, NIST and WEF framework references |
