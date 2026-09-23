# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

Brings in the deployment work done on `main` (PR #1) on the old flat layout, ported to
`src/mirag`.

### Security

- The generated code no longer inherits the environment: the child process gets only `PATH`,
  `HOME`, the locale and the temp variables. Before, a `print(os.environ)` in a generated test
  read the OpenRouter key and the Stellar seed.
- `MIRAG_TOKEN`: with it set, `POST /api/v1/chat` and the download require the
  `X-Mirag-Token` header (compared with `hmac.compare_digest`); anything else is `401`.
- An empty `MIRAG_HOST` no longer binds every interface; any non-loopback bind, a missing
  token and execution being off are announced at startup.

### Added

- `MIRAG_EXECUTION` (default `off`): the agent delivers code and tests without running them
  and the verdict is `not_executed`. The verification step is `skipped` (not `error`), no
  repair is paid for, JavaScript syntax is not faked, and a project is `GENERATED` after its
  static checks. `mirag demo` and the benchmarks switch it on unless it is set.
- `MIRAG_LLM_URL` for any chat/completions provider; `openrouter/free` shows `FREE` in the
  cost panel instead of `$0.0000`.
- The project panel carries each file's `text` (2 MB cap; files shaped like a credential are
  omitted and say why), so a client can show the code without unpacking the ZIP.
- `health` reports `execution` and `token_required`.
- `Dockerfile` (targets `base` and `identidad`), `docker-compose.yml`,
  `docker-compose.prod.yml`, `.env.server.example`, `scripts/publish.sh`, a CI job for the
  demo contracts and credentials, image publishing to GHCR on `main`, and
  `docs/{en,es}/deployment.md`.
- The earlier variable names `MIRAG_MODELO`, `LIMITE_USD` and `MIRAG_EJECUCION` are read when
  the new name is absent.
- `mirag/projects/languages.py`: one table of languages (Python, JavaScript, TypeScript, Go,
  Java, Kotlin, Rust, Ruby, PHP, C#, C, C++, Swift, Dart, Elixir, Scala, Haskell, Clojure, Lua,
  Perl, R, Julia) instead of Python assumed in four places. It drives language detection, which
  file counts as a test, the default test command and the extensions a project may contain.
  Adding a language is one row.
- A `node:test` harness (`probes.node_tests_probe`): a Node.js project's tests are executed and
  each one becomes a `TEST:<id>:PASS|FAIL` marker, like the `unittest` probe does for Python.

### Fixed

- Tests follow the project's language. `complete_plan` added `unittest` files whenever no
  `tests/*.py` existed — to a Node.js plan whose JavaScript tests were already there — and the
  structure check only accepted a `.py` under `tests/`, so an Express project came out `FAILED`
  on `unittest_loader__FailedTest_tests_test_HTTPServer`. Only a language with a known layout
  gets tests added, in that language; the rest is left to `validate_plan` to report.
- A language Mirag cannot run here (Go, Rust, Java…) is delivered with its tests in its own
  language and reported `GENERATED` with an `execution` phase `skipped`, never `EXECUTED`.
- `test_command` for a Node.js project is normalised from `npm test` (no `npm` here) to
  `node --test tests/`, and reported as a plan step.
- The project file allow-list no longer rejects the first `.go`, `.rs`, `.java`… file.

## [2.0.0] - 2026-09-18

### Changed

- The code base was restructured into an installable package (`src/mirag`) with one
  subpackage per responsibility and a single composition root (`mirag/container.py`). Services
  receive their collaborators through their constructors; there are no mutable module-level
  singletons (the old global `agent.llm` monkeypatching and the thread-local budget proxy are
  gone: each request gets its own `LLMGateway` and `Budget`).
- Every identifier, comment and docstring is in English.
- The HTTP API is versioned and in English: `POST /api/v1/chat` (was `POST /chat` with
  `pregunta`/`modo`), `GET /api/v1/artifacts/{id}/download` (was `/descarga?id=`),
  `GET /api/v1/blockchain/agent` (was `/api/blockchain/agent`). SSE events and JSON panels use
  English field names (`type: step|phase|thought|tool|cost|done`, `answer`, `evidence`, ...).
  See `docs/en/api.md`.
- Execution statuses are `passed | failed | no_evidence | not_executed` (were `verde | rojo |
  sin_evidencia | no_ejecutado`); project statuses are `GENERATED | VALIDATED | EXECUTED |
  TESTED | VERIFIED | PARTIAL | FAILED`.
- The generated-project contract is `create_server(port=0, db=":memory:")` (was
  `crear_servidor(puerto, bd)`), probes are `_probe_*.py` and the demo fixture is `books-api`.
- Configuration: `MIRAG_BUDGET_USD` replaces `LIMITE_USD`, `MIRAG_SUFFICIENCY` replaces
  `MIRAG_SUFICIENCIA`; new `MIRAG_MODEL`, `MIRAG_LOCALE`, `MIRAG_HOST`, `MIRAG_PORT`,
  `MIRAG_DATA_DIR`. Runtime data moved from folders next to the code to `MIRAG_DATA_DIR`.
- The stage gains policy moved to `src/mirag/resources/feature_gains.json` with English keys.
- Tests moved from 21 self-running scripts to a pytest suite (`tests/unit`, `tests/integration`,
  `tests/architecture`), offline and isolated in temporary folders.

### Added

- Internationalisation: English and Spanish, one folder each (`locales/en`, `locales/es`,
  `knowledge/en`, `knowledge/es`). The knowledge corpus was translated to English with the same
  structure; language heuristics (intent, stop words, claims, demos) are per-locale data.
- Locale resolution by request field, `Accept-Language` and `MIRAG_LOCALE`; a language switcher
  in the page; `GET /api/v1/i18n/{locale}`, `GET /api/v1/locales`, `GET /api/v1/demos`,
  `GET /api/v1/health`.
- Request validation with JSON errors before streaming; `405` for known paths with the wrong
  method; defensive headers on every response.
- The `mirag` command line (`serve`, `ask`, `demo`, `features`, `traces`), `pyproject.toml`,
  Makefile, CI workflow, ruff and mypy configuration.

### Fixed

- The whole legacy suite failed on Windows (`UnicodeDecodeError`): every text file is now read
  and written with an explicit UTF-8 encoding, and child processes run with UTF-8 I/O.
- The CRUD probe used `signal.SIGALRM`, which does not exist on Windows; it now uses a watchdog
  thread.
- `python3` on Windows can resolve to the Microsoft Store stub: interpreters are now probed, and
  Python names fall back to the interpreter running Mirag.
- A repaired project was certified but the unrepaired one was packaged; the ZIP now contains
  exactly the project that was verified.
- The syllabus line of a box was read only up to its first line break, missing subcategories.
