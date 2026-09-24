# Contributing

Thanks for helping. The short version: keep the evidence discipline, keep both languages in
sync, and keep the CI checks green.

## Workflow

1. Create a branch from `main` (`feature/...`, `fix/...`, `docs/...`).
2. `pip install -e ".[dev]"`
3. Make the change.
4. `make lint typecheck demo` (or `python -m ruff check src benchmarks scripts`,
   `python -m mypy`, `python -m mirag demo all`), plus the `scripts/check_*.py` that touch what
   you changed. There is no test suite; the full list of checks is in
   [docs/en/development.md](docs/en/development.md#checks).
5. Open a pull request describing **what was measured or observed**, not only what changed.

## Rules the reviewers will check

- **Execution decides.** Never let a model claim become a status. New statuses are derived in
  `mirag/execution/verdict.py` or `mirag/projects/certification.py`, nowhere else.
- **Measure before switching on.** A new retrieval stage is declared in `features/flags.py`, is
  born off, and is enabled by a measurement written by `benchmarks/calibrate_stages.py`.
- **Both locales, always.** Every user-facing string goes through `messages.json` / `ui.json`
  in `en` **and** `es`, with the same keys and placeholders. Corpus changes go to both
  `knowledge/en` and `knowledge/es` keeping the section structure identical. No test checks
  the parity any more, so compare the key sets by hand.
- **Standard library core.** No third-party runtime dependency outside
  `integrations/` (declared as an extra).
- **Dependencies point inwards.** Domain packages never import the API, the container, the
  pipeline or the presentation. Nothing enforces it automatically since `tests/architecture`
  was removed, so reviewers look for it.
- **Offline checks.** No check may reach a real model or an outside network: run them with
  `MIRAG_OFFLINE=1`, as CI does.
- **English code, comments that explain why.**

## Commit messages

Imperative mood, short subject (`Add English lexicon for claims`), a body explaining the why
when it is not obvious.
