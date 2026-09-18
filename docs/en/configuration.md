# Configuration

Mirag reads its configuration once, from the environment and an optional `.env` file at the
repository root (copy `.env.example`). Existing environment variables always win over `.env`.

## Runtime

| Variable | Default | Meaning |
|---|---|---|
| `MIRAG_OFFLINE` | `1` | The lock. While on, no real model is ever called (demos are scripted and labelled SIMULATED). Set `0` to spend for real. |
| `OPENROUTER_API_KEY` | - | Needed only with `MIRAG_OFFLINE=0` (or the remote vector backend). |
| `MIRAG_MODEL` | `anthropic/claude-haiku-4.5` | OpenRouter model id. `openrouter/free` routes to the free models (20 requests/minute, 50/day); the cost panel then says `FREE`. |
| `MIRAG_LLM_URL` | OpenRouter's chat/completions | Any provider speaking the same dialect (NVIDIA, Groq, Gemini): the URL and the model are all that changes. |
| `MIRAG_BUDGET_USD` | `0.50` | Spending cap per request; the call that would exceed it is never made. `0` = no cap. |
| `MIRAG_MAX_OUTPUT_TOKENS` | `12000` | `max_tokens` per model call. |
| `MIRAG_LOCALE` | `en` | Default locale when the request and `Accept-Language` say nothing (`en`, `es`). |
| `MIRAG_HOST` / `MIRAG_PORT` | `127.0.0.1` / `8000` | Where the server listens. Anything but loopback is announced at startup; in a container publish it against `127.0.0.1` ([deployment.md](deployment.md)). |
| `MIRAG_TOKEN` | - | Shared secret required in the `X-Mirag-Token` header by `POST /api/v1/chat` and the download. Empty = open to whoever reaches the port, and the startup says so. |
| `MIRAG_EXECUTION` | `off` | Run the generated code and its tests? Off, they are delivered without running them (that is the QA agent's job) and the verdict is `not_executed`; structure, syntax and imports are still checked. `mirag demo` and the benchmarks switch it on unless it is set. |
| `MIRAG_DATA_DIR` | `<repo>/var` or `~/.mirag` | Where outputs, artifacts, traces and caches are written. |
| `MIRAG_SYMBOLS_ROOT` | the `src` folder | The code base the symbol index reads. |
| `MIRAG_VECTOR_BACKEND` | `local` | `local` (character n-grams, free) or `openrouter` (real embeddings, falls back to local). |
| `MIRAG_CODE_TIMEOUT_S` | `30` | Timeout of each code execution. The executed code receives no credential: only `PATH`, `HOME`, locale and temp variables. |
| `MIRAG_HTTP_LOG` | - | `1` to print the HTTP access log. |

## Feature flags

Every flag accepts `on`, `off` or `auto` through `MIRAG_<NAME>`. `mirag features` prints the
state of each one and **why**.

| Flag | Kind | In `auto` |
|---|---|---|
| `RETRIEVAL_PLAN`, `METADATA_ROUTING`, `HYBRID_RETRIEVAL`, `SYMBOL_RETRIEVAL`, `SUFFICIENCY` | core | always on (unless switched off by hand) |
| `VECTOR_SIGNAL`, `RERANKER`, `GRAPH_RETRIEVAL` | conditional | on only if `feature_gains.json` measured a gain above 0.02 MRR that beats its cost |
| `MODEL_ROUTING`, `SEMANTIC_CACHE`, `KNOWLEDGE_TREE` | experimental | never on by themselves; `on` by hand is labelled EXPERIMENTAL |
| `CONTEXTUAL_CHUNKS`, `COLBERT` | not implemented | never on, not even by hand |

Setting a flag that does nothing is reported instead of silently ignored.

## Optional Stellar layer

`MIRAG_BLOCKCHAIN` (`off` by default, `testnet` to enable) and the `STELLAR_*` variables are
described in [blockchain.md](blockchain.md).
