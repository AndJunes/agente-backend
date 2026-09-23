# Mirag

**Give it a problem. Mirag searches what it knows, proposes a solution, and shows you exactly
what that solution rests on - and what it does not.**

It generates the code and its test cases and, by default, **does not run them**: that will be
the QA agent's job (`MIRAG_EXECUTION=off`). What does not change is that nothing is claimed
that was not observed, and today that means saying `not_executed` instead of faking a pass.

*[Leer en español](README.es.md)*

Python standard library only: **the core has zero third-party dependencies**
(`dependencies = []` in `pyproject.toml`). The optional Stellar identity layer declares
`stellar-sdk` as an extra.
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

**Status is decided by execution, never by the model.** Four possible verdicts. With
execution off, production always gives the fourth; the machinery stays whole and the demos
switch it on to show it. Structure, syntax and imports are checked without running anything:

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
├── src/mirag_pm/            the PM agent: the same code, told it is a different agent
├── src/mirag_manager/       both agents behind one port (`python -m mirag_manager serve`)
├── benchmarks/              retrieval and project benchmarks, datasets and results
├── scripts/                 the checks CI runs, the model probe, and the Stellar demo
├── docs/{en,es}/            documentation in both languages
└── docs/history/            the reports that explain how the project got here (Spanish)
```

## Running it

```bash
mirag serve                          # the page (offline, $0)
mirag demo all --locale es           # the 4 canonical demos, with their contracts checked
mirag ask "What is an idempotency key?" --locale en
mirag features                       # which pipeline stages are on, and why
docker compose up -d                 # the same, in an unprivileged container
```

`make run`, `make run-manager`, `make lint`, `make typecheck` and `make demo` do the same on
systems with `make`. It is optional: each target is one `python -m ...` line in the `Makefile`,
which is what to run on Windows without it.

## Running it with CodeZard

The CodeZard screen does not talk to `mirag serve`. It needs **two** agents, this one (the
backend agent) and the PM (`mirag_pm`), and it reaches both through the gateway.
`mirag_manager` runs them in one process, on one port, told apart by the first segment of the
path:

| Path | Agent | Operations |
|---|---|---|
| `/backend/...` | `mirag` | `chat` |
| `/pm/...` | `mirag_pm` | `analyze`, `plan`, `revise` |

```bash
python -m venv .venv                       # once
# PowerShell: .venv\Scripts\Activate.ps1        bash/zsh: source .venv/bin/activate
pip install -e ".[dev]"                    # once
cp .env.example .env                       # once (PowerShell: Copy-Item .env.example .env)

python -m mirag_manager serve              # or: make run-manager
#   backend: chat
#   pm: analyze, plan, revise
```

Edit `.env` first. These are the values that matter for CodeZard:

| Variable | Set it to | Why |
|---|---|---|
| `MIRAG_PORT` | `8100` | The example says `8000`, which is the gateway's port. The gateway's `.env` points at `8100` |
| `MIRAG_TOKEN` | a secret | The gateway sends it as `X-Mirag-Token`, so it must equal `MIRAG_TOKEN` in `CodeZard/.env`. One token covers both agents |
| `MIRAG_OFFLINE` | `0` | `1` (the default) is the rehearsal lock: the PM replays one fixed plan, labelled simulated, and this agent only answers its prepared demos. `0` calls the model for real |
| `OPENROUTER_API_KEY` | your key | Needed with `MIRAG_OFFLINE=0` |
| `MIRAG_BACKEND_MODEL`, `MIRAG_PM_MODEL` | optional | One model per agent. Unset, both use `MIRAG_MODEL` |
| `MIRAG_EXECUTION` | `off` or `true` | Whether the generated code and its tests are run. `off`: they are delivered unrun and the verdict is `not_executed` |
| `MIRAG_CONSOLE` | `1`, optional | Lets the screen run commands in a delivered project. The gateway also needs `GATEWAY_ORCHESTRATION__CONSOLE=true` |

Check that it answers:

```bash
curl http://127.0.0.1:8100/backend/api/v1/health
curl http://127.0.0.1:8100/pm/api/v1/health
```

Then start the gateway (`CodeZard`, command `gateway`) and the screen (`codezard-front`, command
`npm run dev`); the `codezard-front` README has the whole walkthrough and a table of what to
check when something fails. A few things that go wrong here:

- **`mirag serve` is the wrong process for the screen.** It only serves `/api/v1/...`, so every
  `/pm/...` call is a `404`. Use `python -m mirag_manager serve`.
- **The `mirag-manager` command** is declared in `pyproject.toml`, but an environment installed
  before it was added does not have it. `python -m mirag_manager serve` always works.
- **On Windows, a restart can leave two managers on the same port.** `netstat -ano | findstr :8100`
  should list one listener.
- **In Docker**, `CodeZard/docker-compose.local.yml` builds this folder's `Dockerfile`
  (`--target base`) and runs the manager in a container.

## Checks

There is no test suite in this checkout (`tests/` was removed). What CI runs is:

```bash
python -m ruff check src benchmarks scripts     # make lint
python -m mypy                                  # make typecheck
python -m mirag demo all                        # make demo; add --locale es for the Spanish run
python -m mirag_pm.cli doctor                   # every PM locale loads, and its four indices
python -m mirag_pm.cli coverage --by-domain     # every PM document is reachable by a skill
python scripts/check_delivery.py                # a project that does not match its plan is not deliverable
python scripts/check_deadlines.py               # a hanging call ends, and a closed tab stops the work
python scripts/check_repair.py                  # a failing test tells the repairer where to look
python scripts/check_parallel.py                # batches run at once without losing files or miscounting calls
```

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

## On a server

```bash
docker compose up -d --build       # http://127.0.0.1:8000, and only there
```

Unprivileged user, its own code read-only, `/tmp` in RAM, no capabilities and CPU, memory and
process ceilings. The port is published against `127.0.0.1` on purpose, and `MIRAG_TOKEN`
shuts the door on whoever does not bring the secret. Two images from the same `Dockerfile`:
`--target base` without a single dependency, and `--target identidad` with `stellar-sdk`.
How, what each piece protects and **what is still not solved**:
[docs/en/deployment.md](docs/en/deployment.md).

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
| Deployment | [docs/en/deployment.md](docs/en/deployment.md) | [docs/es/deployment.md](docs/es/deployment.md) |
| i18n | [docs/en/i18n.md](docs/en/i18n.md) | [docs/es/i18n.md](docs/es/i18n.md) |
| Configuration | [docs/en/configuration.md](docs/en/configuration.md) | [docs/es/configuration.md](docs/es/configuration.md) |
| Development | [docs/en/development.md](docs/en/development.md) | [docs/es/development.md](docs/es/development.md) |
| Stellar identity | [docs/en/blockchain.md](docs/en/blockchain.md) | [docs/es/blockchain.md](docs/es/blockchain.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) | |
