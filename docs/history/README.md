# Project history / Historia del proyecto

**EN** — This folder is an archive. It holds the documents and phase reports written while
Mirag was a flat collection of Spanish modules (before version 2.0.0). They are kept because
they are the evidence behind many decisions still visible in the code (why the reranker is on,
why the vector signal is off, why a project can be `VALIDATED` instead of `FAILED`, why the
server serves an allow-list of routes...). They refer to the **old** module names (`rag.py`,
`pipeline.py`, `skills.py`, `/descarga`, ...); the current architecture is described in
[`docs/en`](../en/architecture.md) and [`docs/es`](../es/architecture.md).

**ES** — Esta carpeta es un archivo. Contiene los documentos y los informes de fase escritos
cuando Mirag era una colección plana de módulos en español (antes de la versión 2.0.0). Se
conservan porque son la evidencia detrás de muchas decisiones que siguen visibles en el código.
Se refieren a los nombres **viejos** de los módulos; la arquitectura actual está en
[`docs/es`](../es/architecture.md) y [`docs/en`](../en/architecture.md).

| Old document | What it covers |
|---|---|
| `PRODUCT_OVERVIEW.md` | What the product is and its measured limits |
| `CURRENT_ARCHITECTURE.md`, `CURRENT_STATUS.md` | The pre-2.0 architecture and status |
| `DEMO.md`, `DEMO_CONTRACTS.md` | The canonical demos and their contracts |
| `EXPERIMENTAL_CAPABILITIES.md` | What existed but was not wired |
| `blockchain.md` | The first version of the Stellar identity layer |
| `reports/` | Phase reports, audits and benchmark reports |

## Name mapping (old → new)

| Old | New |
|---|---|
| `server.py` | `mirag/api/server.py`, `mirag/api/chat_service.py` |
| `pipeline.py` | `mirag/pipeline/` (`orchestrator.py`, `knowledge_stage.py`, `code_stage.py`, `project_stage.py`) |
| `rag.py` | `mirag/retrieval/corpus.py`, `ranking.py`, `search.py` |
| `recuperacion.py`, `hibrido.py` | `mirag/retrieval/service.py`, `hybrid.py`, `context.py` |
| `plan.py`, `metadatos.py`, `suficiencia.py`, `grafo.py`, `vectores.py`, `simbolos.py` | `mirag/retrieval/plan.py`, `metadata.py`, `sufficiency.py`, `graph.py`, `vectors.py`, `symbols.py` |
| `config.py` | `mirag/features/flags.py`, `mirag/core/settings.py` |
| `agent.py` | `mirag/llm/` (gateway, budget, models) and `mirag/agent/loop.py` |
| `skills.py` | `mirag/tools/`, `mirag/execution/` (`verdict.py`, `runner.py`, `calculator.py`) |
| `rapido.py` | `mirag/evidence/properties.py`, `mirag/pipeline/delivery.py`, `prompts.py` |
| `auditoria.py`, `obligaciones.py` | `mirag/evidence/claims.py`, `obligations.py` |
| `proyecto.py`, `generador.py`, `dependencias.py`, `sondas.py`, `verificacion_proyecto.py`, `empaquetado.py`, `artefactos.py` | `mirag/projects/` (`model.py`, `generator.py`, `dependencies.py`, `probes.py`, `certification.py`, `packaging.py`, `artifacts.py`) |
| `estado.py` | `mirag/self_knowledge/project_state.py` |
| `traza.py` | `mirag/observability/tracing.py` |
| `demos.py`, `dobles.py`, `fixture_proyecto.py` | `mirag/offline/` (`demos.py`, `scripts.py`, `books_project.py`, `contracts.py`) and `mirag/llm/scripted.py` |
| `arquitecto.py` | `mirag/agent/architect.py` |
| `conocimientos/` | `mirag/knowledge/es/` (and the English edition `mirag/knowledge/en/`) |
| `benchmarks/ganancias.json` | `mirag/resources/feature_gains.json` (old measurements in `benchmarks/results/`) |
| `experimental/` | `mirag/experimental/` |
| `blockchain/` | `mirag/integrations/blockchain/` |
| `tests/test_*.py` (self-running scripts) | `tests/` (pytest: `unit/`, `integration/`, `architecture/`) |
