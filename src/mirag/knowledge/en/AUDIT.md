# Audit against the syllabus — status after the conversion

Comparison of the documents against the 19-box syllabus (**157 subcategories**) and against the 15-field
`knowledge_item` format.

## Before and after

| | Before | Now |
|---|---|---|
| Boxes | 20 (one outside the syllabus) | **19, in the syllabus order and with the syllabus names** |
| Subcategories covered | 120 / 157 (76%) | **157 / 157** |
| Partial | 35 | 0 |
| Missing | 2 | 0 |
| Explicit schema fields | 4 / 15 | **15 / 15** |
| Documents with sources | 1 / 20 | **19 / 19** |
| Lines | 5,123 | **8,735** |
| Cards (knowledge_items with the 15 fields) | 0 | **228** |
| Code blocks | 59 | **105** |

## What was added, per box

| Box | New sections |
|---|---|
| 01 Fundamentals | `tests` (property-based and how to test concurrency) · concurrency patterns (worker pool, fan-out/in, pipeline) · latency table as its own item · consistent hashing implemented |
| 02 Web & Protocols | `implementations` (nginx, middleware and its order) · `constraints` (table of limits and timeouts) · `failure_modes` (502/504/reset/TLS) |
| 03 APIs | a complete endpoint from start to finish · how an API fails in production |
| 04 Databases | **joins, aggregations, window functions and recursive CTEs** · what changes between Postgres/MySQL/Mongo/Redis · failures, including silent corruption |
| 05 Architecture | **coupling and cohesion** (never defined before) · real folder structures with an architecture test · `constraints` (team, budget, legacy, strangler fig) · how an architecture fails |
| 06 Security | the security stack in code (authn/authz/RLS) · `constraints` (compliance and threat modeling with STRIDE) · how it fails in practice · security incident response |
| 07 Payments | the complete flow of a charge in code, with reconciliation · how a payments system fails |
| 08 Distributed Systems | **event schema and versioning** · producer with outbox and idempotent consumer in code · how a distributed system fails |
| 09 Performance | the techniques in code (single-flight, batching, bulkhead, streaming) · diagnosing an incident · order of intervention when scaling |
| 10 Reliability | health checks and graceful shutdown in code · circuit breaker implemented · incident debugging · data recovery |
| 11 Testing | `failure_scenarios` (adversarial cases, IDOR and idempotency tests, fuzzing) |
| 12 Observability | instrumentation with OpenTelemetry in code · what to monitor and which signal gives each failure away |
| 13 Cloud & Infrastructure | volumes and state in containers · cost (where the money goes) |
| 14 DevOps | deployment checklist · production checklist for a new service |
| 15 Files & Data | how file handling fails · consistency between the file and its record |
| 16 Integrations | how an integration fails · reliability inherited from dependencies |
| 17 Business Logic | **entities and aggregates** · business inconsistencies and invariant verification |
| 18 AI Backend | **embeddings** as their own item · how an AI system fails |
| 19 System Design | **ADRs** with a template · **diagrams** (C4 and sequence) |

## The two structural mismatches, resolved

1. **Box 20 (Production) was dissolved** into devops (checklists), reliability (debugging, recovery),
   observability (monitoring), performance (incidents and scaling), cloud (cost) and security
   (security incidents). There is no longer any overlap with reliability.
2. **Self-contained boxes vs cross-references:** we went with **references**. Each concept is
   developed in a single box and the others link to it with `[NN]`. The subcategories the syllabus asks for per
   box (`constraints`, `failure_modes`, `implementations`) now **do exist in every box**, but they
   cover what is specific to that box instead of repeating another box's content.

## Effect on the RAG

| | Before | Now |
|---|---|---|
| Chunks | 212 | 271 |
| Median size | 1,196 chars | 1,853 chars |
| top-1 | 21/23 | **28/31** |
| recall@3 | 22/23 | **30/31** |

The only miss in the test set: *"how do you write an ADR"* returns box 05 (which mentions them) instead
of box 19 (which develops them). The result is still relevant, but it's a case where two boxes
compete for the same term.
