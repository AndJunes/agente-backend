# Knowledge — Senior Backend

19 boxes aligned with the syllabus. Each document is a box; each `##` inside it is a **knowledge_item**
with the 15 fields of the schema (see [FORMAT.md](FORMAT.md)).

This English edition mirrors the Spanish one ([`../es/`](../es/)) section by section: same boxes, same
`##` sections in the same order, same cards and the same `[NN]` references between boxes.

| # | Box | Subcategories covered |
|---|---|---|
| [01](01-fundamentals.md) | 🧱 Fundamentals | concepts · patterns · implementations · constraints · failure_modes · tradeoffs · tests |
| [02](02-web-protocols.md) | 🌐 Web & Protocols | concepts · protocols · headers · implementations · constraints · failure_modes · tradeoffs |
| [03](03-apis.md) | 🔌 APIs | concepts · patterns · protocols · implementations · security · failure_modes · tradeoffs |
| [04](04-databases.md) | 🗄️ Databases | concepts · modeling · queries · indexing · transactions · scaling · caching · implementations · failure_modes · tradeoffs |
| [05](05-architecture.md) | 🏗️ Architecture | concepts · patterns · implementations · boundaries · dependencies · constraints · failure_modes · tradeoffs |
| [06](06-security.md) | 🔐 Security | concepts · authentication · authorization · attacks · cryptography · implementations · constraints · failure_modes · tradeoffs |
| [07](07-payments.md) | 💳 Payments | concepts · providers · checkout · subscriptions · webhooks · refunds · implementations · state_machines · failure_modes · constraints · tradeoffs |
| [08](08-distributed-systems.md) | 📡 Distributed Systems | concepts · messaging · events · patterns · reliability · idempotency · implementations · failure_modes · tradeoffs |
| [09](09-performance.md) | ⚡ Performance | concepts · caching · optimization · scaling · profiling · implementations · bottlenecks · tradeoffs |
| [10](10-reliability.md) | 🛡️ Reliability | concepts · patterns · failure_modes · recovery · implementations · tradeoffs |
| [11](11-testing.md) | 🧪 Testing | concepts · unit · integration · e2e · contract · load · implementations · failure_scenarios |
| [12](12-observability.md) | 👁️ Observability | logging · metrics · tracing · alerting · dashboards · implementations · failure_modes |
| [13](13-cloud-infrastructure.md) | ☁️ Cloud & Infrastructure | linux · containers · orchestration · cloud · networking · storage · iam · tradeoffs |
| [14](14-devops.md) | 🚀 DevOps | git · cicd · deployment · infrastructure · secrets · rollback · failure_modes |
| [15](15-files-data.md) | 📁 Files & Data | uploads · storage · processing · streaming · security · failure_modes |
| [16](16-integrations.md) | 🔗 Integrations | external_apis · webhooks · oauth · email · notifications · storage · implementations · failure_modes · tradeoffs |
| [17](17-business-logic.md) | 💼 Business Logic | concepts · entities · workflows · state_machines · permissions · multi_tenancy · audit · failure_modes |
| [18](18-ai-backend.md) | 🤖 AI Backend | llms · prompting · embeddings · vector_databases · rag · search · reranking · tool_calling · agents · mcp · evals · guardrails · observability · failure_modes |
| [19](19-system-design.md) | 🧠 System Design | requirements · capacity · architecture · bottlenecks · failure_scenarios · tradeoffs · decisions · diagrams |

## How to use them

- **To study:** in order. Boxes reference each other with `[NN]` and the concepts build on one
  another. A concept is developed **in a single box**; the others link to it.
- **To review before an interview:** the *Interview questions and trade-offs* section at the end of
  each document, plus the **cards** for each concept.
- **As RAG:** the `##` headings are the chunk boundaries of [`../../retrieval/corpus.py`](../../retrieval/corpus.py). Each one stands on its own.

## On how current this is

Time-sensitive data (OpenTelemetry, MCP, RAG practices, 2026 versions and recommendations) was
verified with web search in **September 2026**. Each document lists its sources at the end.
