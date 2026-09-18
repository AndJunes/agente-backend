# Development

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"            # add ",blockchain" for the optional Stellar layer
```

Python 3.11 or newer. The runtime has no third-party dependencies; `dev` brings pytest, ruff
and mypy.

## Everyday commands

| Command | What it does |
|---|---|
| `make run` / `mirag serve` | Start the server on http://127.0.0.1:8000 (offline, $0) |
| `make test` / `pytest` | The fast suite (offline, isolated temp folders). Tests marked `slow` are skipped by default |
| `make test-all` / `pytest -m "not network"` | Everything, including the `slow` tests (subprocesses, HTTP servers) |
| `make lint` / `ruff check src tests` | Lint |
| `make typecheck` / `mypy` | Type check |
| `make demo` / `mirag demo all` | Run the four canonical demos and check their contracts |
| `mirag ask "question" --locale es` | One question through the pipeline, printed |
| `mirag features` | The state of every feature flag and why |
| `mirag traces -n 20` | The last trace lines |

On Windows without `make`, run the commands on the right.

## Tests

```
tests/
├── conftest.py        shared fixtures (offline settings, isolated data dir, engines per locale)
├── unit/<area>/       one folder per package
├── integration/       real HTTP server, full project generation, optional network suites
├── architecture/      AST rules: layering, no third-party imports, encodings, English identifiers
└── fixtures/          sample repositories
```

Rules:

- Every test is offline. The gateway refuses to reach a model while `MIRAG_OFFLINE` is on, so a
  test cannot spend money by accident; model decisions come from `ScriptedChatModel` scripts.
- Tests write only under `tmp_path`: the `settings`/`container` fixtures point
  `MIRAG_DATA_DIR` there.
- Mark tests that spawn interpreters or servers with `@pytest.mark.slow`.
- Tests that need the real Stellar network are marked `network` and skipped unless enabled.

## Conventions

- English identifiers, comments and docstrings. User-facing text goes through the catalogs of
  **both** locales (the i18n tests fail if a key or a placeholder is missing in one of them).
- Comments explain *why* (a measurement, a past bug), not *what*.
- Value objects are frozen dataclasses; closed sets of values are `StrEnum`s.
- Dependencies are injected through constructors; `container.py` is the only composition root.
- Always pass `encoding="utf-8"` when reading or writing text.

## Configuration

See [configuration.md](configuration.md).

## Benchmarks

See `benchmarks/README.md`. The calibration benchmark is the only writer of
`src/mirag/resources/feature_gains.json`, the file the feature gate reads.
