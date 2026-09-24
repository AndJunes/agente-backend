# Architecture

Mirag answers backend-engineering questions and builds code, and it always separates three
things: what the model **claims**, what the machine **observed**, and what is **proved**.
This document explains how the code base is organised to keep that promise.

## Principles

1. **Execution decides, never the model.** The status of a piece of code is derived from an
   execution (exit code + `TEST:<id>:PASS|FAIL` markers) in exactly one place:
   `mirag/execution/verdict.py`. Project statuses are derived in exactly one place too:
   `StatusDeriver` in `mirag/projects/certification.py`.
2. **No stage runs out of habit.** Optional retrieval stages are switched on by the
   `FeatureGate` only when a benchmark measured that they help (`resources/feature_gains.json`).
   A stage that does not run is still reported, with its reason.
3. **One retrieval, one context.** `RetrievalService` is the only retrieval used by production
   and by the benchmarks; `ContextBuilder` is the only place that decides what enters a prompt.
4. **Offline by default.** The `LLMGateway` refuses to reach a real model unless
   `MIRAG_OFFLINE=0`. Demos use a deterministic scripted model and are labelled SIMULATED.
5. **Standard library runtime.** The core has zero third-party dependencies
   (`dependencies = []` in `pyproject.toml`). The optional Stellar layer declares `stellar-sdk`
   as an extra.
6. **Every user-facing string is localised.** Two locales today (`en`, `es`), one folder each.

## Layers

```
            ┌──────────────────────────────────────────────────────────┐
 boundary   │ api/ (HTTP router, SSE, validation)      cli.py          │
            ├──────────────────────────────────────────────────────────┤
 application│ container.py (composition root)                          │
            │ pipeline/ (QuestionPipeline + stages)   agent/ (loop,    │
            │ presentation/ (markdown, panels)          architect)     │
            │ offline/ (demo catalog, scripts, contracts)              │
            │ self_knowledge/ (project-state shortcut)                 │
            ├──────────────────────────────────────────────────────────┤
 domain     │ retrieval/  execution/  evidence/  projects/  tools/     │
            │ features/   llm/                                         │
            ├──────────────────────────────────────────────────────────┤
 foundation │ core/ (settings, errors, text)   i18n/   paths.py        │
            └──────────────────────────────────────────────────────────┘
   optional: integrations/blockchain/ (lazy)   not in production: experimental/
```

Dependencies only point downwards: the domain never imports the pipeline, the API, the
container or the presentation; `core` imports nothing else from Mirag; nothing imports
`experimental`; the blockchain layer is only imported lazily by the container. An AST test used
to enforce this; it went with `tests/`, so today the rule holds by review.

## The request path

```
POST /api/v1/chat ─▶ ChatService
   ├─ ProjectStateResponder  "which model do you use?" → answered from facts, 0 calls
   ├─ offline? → DemoCatalog picks a script (or "no model")  → LLMGateway(ScriptedChatModel)
   └─ QuestionPipeline.run
        1  project_state
        2  retrieval_plan         PlanDeducer (deterministic) — or EMPTY_PLAN when disabled
        3-5 retrieval             RetrievalService: 3 indices × (filter → BM25 → vector? → RRF → reranker?)
        6  symbols                only if the plan asks for code search
        7  graph                  only if measured AND the plan asks for relationships
        8  sufficiency            covered / mentioned / absent — warns before answering
        9  context                ContextBuilder
        10 model                  LLMGateway.chat
        11 code branch            deliver → syntax → run → repair once → evidence → anti-patterns
           or project branch      specify → generate by groups → certify (probes) → package → artifact
        12 trace                  TraceWriter (JSONL)
   └─ ClaimAuditor               the final prose is contrasted with the markers that really ran
   └─ done event                 answer + evidence panel + timeline + cost + project/deliverable
```

## SOLID, concretely

| Principle | Where it shows |
|---|---|
| Single responsibility | `CorpusParser` parses, `Bm25Ranker` ranks, `MetadataFilter` filters, `HybridRetriever` orchestrates one index, `RetrievalService` the three indices, `ContextBuilder` builds the prompt. `CodeRunner` runs, `SyntaxChecker` checks, `ExecutionResult` decides. `ZipBuilder` builds and `ZipInspector` inspects - on purpose with independent criteria. |
| Open/closed | New tools are new `Tool` objects in a `ToolRegistry`; new rankers subclass `Ranker`; new vector backends subclass `VectorStore`; new languages are new locale folders - none of them edits existing code. |
| Liskov | `LocalHashVectorStore` and `OpenRouterVectorStore` are interchangeable behind `VectorStore`; `ScriptedChatModel` and `OpenRouterChatModel` behind `ChatModel`. The pipeline cannot tell a script from a model (only the `simulated` flag, which it reports). |
| Interface segregation | `ChatModel` has one method (`complete`). `Repairer` is a single callable. Presenters receive only what they read. |
| Dependency inversion | Services receive collaborators through their constructors; `container.py` is the only place that picks concrete classes. Tests build the same graph with their own settings. |

## Packages

| Package | Responsibility |
|---|---|
| `core` | `Settings` (read once from the environment), domain errors, text helpers, timing |
| `i18n` | Locale registry, message catalogs, per-locale lexicon and corpus format |
| `features` | Feature flags and the measurement gate |
| `llm` | Chat-model port, OpenRouter adapter, scripted double, gateway (lock + budget) |
| `retrieval` | Corpus parsing, ranking, metadata, vectors, reranker, hybrid retrieval, service, context, plan, sufficiency, graph, symbols, typed searches, per-locale engine |
| `execution` | Interpreter discovery, sandboxed runner, syntax check, calculator, the verdict |
| `evidence` | Evidence rows, simulation detection, anti-pattern obligations, claim auditing |
| `tools` | Tool abstraction, registry and built-in tools |
| `projects` | Project model and path policy, dependency analysis, probes, certification, packaging, artifacts, generation |
| `pipeline` | The production orchestrator and its stages |
| `agent` | Tool-calling loop and the experimental architect workflow |
| `presentation` | Markdown answers and JSON panels, localised |
| `offline` | Demo catalog, canned scripts, the books-api fixture, demo contracts |
| `self_knowledge` | Answers about Mirag itself from real facts |
| `api` | HTTP server, router, request validation, chat use case |
| `integrations/blockchain` | Optional Stellar identity (lazy, never takes the server down) |
| `experimental` | Semantic cache, knowledge tree, model router - tested, not wired |

## Runtime data

Everything Mirag writes goes under `MIRAG_DATA_DIR` (default `<repo>/var` in a checkout,
`~/.mirag` when installed): `output/` (the last single-file deliverable), `artifacts/<id>/`
(generated projects), `traces/pipeline.jsonl`, `embeddings/` (remote vector cache). The package
folder is never written at runtime.

## Extension points

- **A new locale**: add `locales/<xx>/{messages,ui,lexicon,corpus}.json` and
  `knowledge/<xx>/`, then add the code to `SUPPORTED_LOCALES`. The i18n tests check key parity.
- **A new tool**: build a `FunctionTool` and add it in `tools/builtin.py`.
- **A new retrieval stage**: declare it in `features/flags.py`, wire it in `HybridRetriever`,
  measure it with `benchmarks/calibrate_stages.py`, and let the gate decide.
- **A new model provider**: implement `ChatModel` and pass a `model_builder` to
  `build_container`.
