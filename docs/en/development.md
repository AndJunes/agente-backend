# Development

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"            # add ",blockchain" for the optional Stellar layer
```

Python 3.11 or newer. The runtime has no third-party dependencies; `dev` brings ruff and mypy.

## Everyday commands

| Command | What it does |
|---|---|
| `make run` / `mirag serve` | Start the single agent on http://127.0.0.1:8000 (offline, $0) |
| `make run-manager` / `python -m mirag_manager serve` | Start the backend agent and the PM behind one port, which is what the CodeZard screen uses (see the README) |
| `make lint` / `python -m ruff check src benchmarks scripts` | Lint |
| `make typecheck` / `python -m mypy` | Type check |
| `make demo` / `mirag demo all` | Run the four canonical demos and check their contracts |
| `mirag ask "question" --locale es` | One question through the pipeline, printed |
| `mirag features` | The state of every feature flag and why |
| `mirag traces -n 20` | The last trace lines |

On Windows without `make`, run the commands on the right.

## Checks

There is no test suite in this checkout: `tests/` was removed. What stands in for it is what CI
runs (`.github/workflows/ci.yml`):

| Command | What it guards |
|---|---|
| `python -m ruff check src benchmarks scripts` | Lint |
| `python -m mypy` | Types |
| `python -m mirag demo all`, and again with `--locale es` | The four demos' contracts, in both languages |
| `python -m mirag_pm.cli doctor` | Every PM locale loads, and none of its four indices is empty |
| `python -m mirag_pm.cli coverage --by-domain` | Every PM document is reachable by a skill |
| `python scripts/check_delivery.py` | A project that does not match its plan is not deliverable |
| `python scripts/check_deadlines.py` | A hanging call ends, and a closed tab stops the work |
| `python scripts/check_repair.py` | A failing test reaches the repairer as a file, a line and a reason |
| `python scripts/check_parallel.py` | Batches run at once without losing files or miscounting calls |

Rules:

- Every check is offline. The gateway refuses to reach a model while `MIRAG_OFFLINE` is on, so a
  check cannot spend money by accident; model decisions come from `ScriptedChatModel` scripts.
  CI sets `MIRAG_OFFLINE=1`. Do the same locally if your `.env` has a real key: `.env` only fills
  in what the environment has not already set.

## Conventions

- English identifiers, comments and docstrings. User-facing text goes through the catalogs of
  **both** locales. Keep the keys and placeholders identical by hand: the i18n parity tests went
  with `tests/`.
- Comments explain *why* (a measurement, a past bug), not *what*.
- Value objects are frozen dataclasses; closed sets of values are `StrEnum`s.
- Dependencies are injected through constructors; `container.py` is the only composition root.
- Always pass `encoding="utf-8"` when reading or writing text.

## Configuration

See [configuration.md](configuration.md).

## Benchmarks

See `benchmarks/README.md`. The calibration benchmark is the only writer of
`src/mirag/resources/feature_gains.json`, the file the feature gate reads.
