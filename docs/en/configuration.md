# Configuration

Mirag reads its configuration once, from the environment and an optional `.env` file at the
repository root (copy `.env.example`). Existing environment variables always win over `.env`.

## Runtime

| Variable | Default | Meaning |
|---|---|---|
| `MIRAG_OFFLINE` | `1` | The lock. While on, no real model is ever called (demos are scripted and labelled SIMULATED). Set `0` to spend for real. |
| `OPENROUTER_API_KEY` | - | Needed only with `MIRAG_OFFLINE=0` (or the remote vector backend). |
| `MIRAG_MODEL` | `anthropic/claude-haiku-4.5` | OpenRouter model id. |
| `MIRAG_BUDGET_USD` | `0.50` | Spending cap per request; the call that would exceed it is never made. `0` = no cap. |
| `MIRAG_MAX_OUTPUT_TOKENS` | `12000` | `max_tokens` per model call. |
| `MIRAG_LOCALE` | `en` | Default locale when the request and `Accept-Language` say nothing (`en`, `es`). |
| `MIRAG_HOST` / `MIRAG_PORT` | `127.0.0.1` / `8000` | Where the server listens. Keep loopback: there is no authentication. |
| `MIRAG_DATA_DIR` | `<repo>/var` or `~/.mirag` | Where outputs, artifacts, traces and caches are written. |
| `MIRAG_SYMBOLS_ROOT` | the `src` folder | The code base the symbol index reads. |
| `MIRAG_VECTOR_BACKEND` | `local` | `local` (character n-grams, free) or `openrouter` (real embeddings, falls back to local). |
| `MIRAG_CODE_TIMEOUT_S` | `30` | Timeout of each code execution. |
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
