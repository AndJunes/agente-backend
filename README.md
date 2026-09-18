# Mirag

**Give it a problem. Mirag searches what it knows, proposes a solution, runs it, and shows you
exactly what that solution rests on - and what it does not.**

*[Leer en español](README.es.md)*

Python standard library only: **the core has zero third-party dependencies** (checked by an
architecture test). The optional Stellar identity layer declares `stellar-sdk` as an extra.
English and Spanish are fully supported: knowledge corpus, UI, answers and language heuristics.

```bash
pip install -e ".[dev]"
mirag serve                 # http://127.0.0.1:8000
```

With `MIRAG_OFFLINE=1` (the default) four prepared demos run end to end and nothing costs
money. For real answers put your key in `.env` (copy `.env.example`) and start with
`MIRAG_OFFLINE=0`.

## What it does

```
Question → Plan → Retrieval (3 indices) → Context → Model
         → Tool → Verification → Evidence → Answer
```

And if you ask for a whole project instead of a single file:

```
Create a REST API of books with full CRUD. Architecture by domain.
        ↓
books-api · 14 files · its tests executed · [ Download ZIP ]
```

## What makes it different

**Status is decided by execution, never by the model.** Four possible verdicts:

| | |
|---|---|
| `passed` | there were test markers and all of them passed |
| `failed` | it ran and failed |
| `no_evidence` | it finished without error and **printed not a single marker** - that is not passing |
| `not_executed` | it never ran |

**Every answer separates three things** most tools mix up: what the model *says*
(`MODEL CLAIM`), what the machine *saw* (`OBSERVED`), and what is *proved* (`VERIFIED`). If the
model claims the tests pass and there are no markers, a warning goes on top and its text is kept
whole for you to judge.

**If the corpus does not cover what you ask, it says so before answering.**

## Repository layout

```
.
├── src/mirag/               the package (see docs/en/architecture.md)
│   ├── locales/{en,es}/     messages, UI strings, language heuristics, corpus markers
│   ├── knowledge/{en,es}/   the knowledge corpus: 19 senior-backend boxes per language
│   └── web/index.html       the page
├── tests/                   unit, integration and architecture suites (pytest)
├── benchmarks/              retrieval and project benchmarks, datasets and results
├── scripts/                 manual demos (Stellar identity)
├── docs/{en,es}/            documentation in both languages
└── docs/history/            the reports that explain how the project got here (Spanish)
```

## Running it

```bash
mirag serve                          # the page (offline, $0)
mirag demo all --locale es           # the 4 canonical demos, with their contracts checked
mirag ask "What is an idempotency key?" --locale en
mirag features                       # which pipeline stages are on, and why
pytest                               # the fast suite, offline
pytest -m "not network"              # everything, including the slow tests
```

`make run`, `make test`, `make lint`, `make demo` do the same on systems with `make`.

## The spending cap

Every call returns the real OpenRouter cost, so the agent **stops before going over**, not
after the invoice:

```bash
MIRAG_BUDGET_USD=0.20 MIRAG_OFFLINE=0 mirag serve
```

The default is $0.50 per request.

## The API

`POST /api/v1/chat` streams Server-Sent Events; generated projects download from
`GET /api/v1/artifacts/{id}/download`. The full contract is in [docs/en/api.md](docs/en/api.md).

## What is not proven

Project generation works end to end - it generates, runs, repairs, packages, checks the
integrity of the ZIP and serves it - but, **measured over 10 runs with a real model, none
reached `VERIFIED`**: they fail on syntax, imports or their own tests. What is proven is that
the machine does not lie when that happens. See
[docs/history/reports/PROJECT_BENCHMARK_REPORT.md](docs/history/reports/PROJECT_BENCHMARK_REPORT.md).

## Documentation

| | English | Español |
|---|---|---|
| Architecture | [docs/en/architecture.md](docs/en/architecture.md) | [docs/es/architecture.md](docs/es/architecture.md) |
| HTTP API | [docs/en/api.md](docs/en/api.md) | [docs/es/api.md](docs/es/api.md) |
| i18n | [docs/en/i18n.md](docs/en/i18n.md) | [docs/es/i18n.md](docs/es/i18n.md) |
| Configuration | [docs/en/configuration.md](docs/en/configuration.md) | [docs/es/configuration.md](docs/es/configuration.md) |
| Development | [docs/en/development.md](docs/en/development.md) | [docs/es/development.md](docs/es/development.md) |
| Stellar identity | [docs/en/blockchain.md](docs/en/blockchain.md) | [docs/es/blockchain.md](docs/es/blockchain.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) | |
