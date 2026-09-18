# Conocimientos — Backend Senior

19 cajas alineadas con el temario. Cada documento es una caja; cada `##` dentro es un **knowledge_item**
con los 15 campos del esquema (ver [FORMAT.md](FORMAT.md)).

Español con los términos técnicos en inglés, que es como se habla y como te van a preguntar.

| # | Caja | Subcategorías que cubre |
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

## Cómo usarlos

- **Para estudiar:** en orden. Las cajas se referencian con `[NN]` y los conceptos se construyen unos
  sobre otros. Un concepto se desarrolla **en una sola caja**; las demás enlazan.
- **Para repasar antes de una entrevista:** la sección *Preguntas de entrevista y trade-offs* del final de
  cada documento, más las **fichas** de cada concepto.
- **Como RAG:** los `##` son las fronteras de chunk de [`../../retrieval/corpus.py`](../../retrieval/corpus.py). Cada uno se sostiene solo.

## Sobre la vigencia

Los datos sensibles al tiempo (OpenTelemetry, MCP, prácticas de RAG, versiones y recomendaciones de 2026)
se verificaron con búsqueda web en **septiembre de 2026**. Cada documento lista sus fuentes al final.
