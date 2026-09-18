# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

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
