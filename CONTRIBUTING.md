# Contributing

Thanks for helping. The short version: keep the evidence discipline, keep both languages in
sync, and keep the suite green.

## Workflow

1. Create a branch from `main` (`feature/...`, `fix/...`, `docs/...`).
2. `pip install -e ".[dev]"`
3. Make the change with its tests.
4. `make lint test typecheck` (or `ruff check src tests benchmarks scripts`, `pytest`, `mypy`).
5. Open a pull request describing **what was measured or observed**, not only what changed.

## Rules the reviewers will check

- **Execution decides.** Never let a model claim become a status. New statuses are derived in
  `mirag/execution/verdict.py` or `mirag/projects/certification.py`, nowhere else.
- **Measure before switching on.** A new retrieval stage is declared in `features/flags.py`, is
  born off, and is enabled by a measurement written by `benchmarks/calibrate_stages.py`.
- **Both locales, always.** Every user-facing string goes through `messages.json` / `ui.json`
  in `en` **and** `es`, with the same keys and placeholders. Corpus changes go to both
  `knowledge/en` and `knowledge/es` keeping the section structure identical. The i18n and
  retrieval tests fail otherwise.
- **Standard library core.** No third-party runtime dependency outside
  `integrations/` (declared as an extra).
- **Dependencies point inwards.** Domain packages never import the API, the container, the
  pipeline or the presentation (see `tests/architecture`).
- **Offline tests.** No test may reach the network or write outside `tmp_path`.
- **English code, comments that explain why.**

## Commit messages

Imperative mood, short subject (`Add English lexicon for claims`), a body explaining the why
when it is not obvious.
