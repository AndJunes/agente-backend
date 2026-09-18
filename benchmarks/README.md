# Benchmarks

Measurement benches for Mirag. Each one measures the **same code production runs**:
`RetrievalService.retrieve` for retrieval, `QuestionPipeline.run` for whole requests. They
are built by the production composition root (`mirag.container.build_container`). A bench that
measures a parallel implementation is how the original audit started: the numbers were right,
but about a pipeline nobody ran.

Run them as modules from the repository root:

```bash
python -m benchmarks.retrieval_eval --locale en      # retrieval quality, free
python -m benchmarks.calibrate_stages --locale es    # which retrieval stages pay off, free
python -m benchmarks.project_bench 3 --dry           # project generation harness, free
python -m benchmarks.task_bench --dry                # task bench harness, free
```

If the package is not installed (`pip install -e .`), `benchmarks/__init__.py` adds `src/` to
`sys.path`, so `python -m benchmarks.<name>` still works. Running a file directly
(`python benchmarks/retrieval_eval.py`) does not work because the benches import each other
as a package.

## What each bench costs

| bench | measures | model calls | cost | writes |
|---|---|---|---|---|
| `retrieval_eval` | MRR and recall@1/3/k per query family, context size, abstention | 0 | $0 | only with `--save` |
| `calibrate_stages` | MRR gain and cost of each conditional stage (`reranker`, `vector_signal`) | 0 | $0 | only with `--write` / `--report` |
| `project_bench` | how many of N project generations reach VERIFIED, and why the others do not | 0 with `--dry`, ~7 per run with the model | $0 dry; real spend with the model | `results/project_bench.json` |
| `task_bench` | GOOD / CHEAP / FAST for five tasks, baseline plan vs default plan | 0 with `--dry`, 1-2 per task and arm | $0 dry; ~$0.10 per task and arm | `results/task_bench.json` |

Spending is opt-in. The offline lock is on unless `MIRAG_OFFLINE=0`, and the two retrieval
benches always force it on. `--dry` also forces it on, whatever the environment says. When
the lock is on and `--dry` was not passed, the pipeline benches fall back to the script and
print that they did.

Every bench uses a container whose `MIRAG_DATA_DIR` is a temporary folder that is deleted at
the end. Traces, artifacts, embeddings caches and deliveries never land in the repository.
The legacy task bench once wrote into the production output folder and wiped the user's last
delivery. The only repository paths a bench writes are its report in `benchmarks/results/` and,
with `calibrate_stages --write`, the gains policy.

## Datasets

`datasets/<locale>/retrieval.json` holds the labelled retrieval set. The same questions exist
in both languages.

```json
{
  "locale": "es",
  "description": "free text",
  "cases": [
    {"family": "easy", "query": "que es el outbox pattern", "expected": ["08"]},
    {"family": "typos", "query": "indices en postgress", "expected": ["04 · Índices"]}
  ],
  "uncovered": [
    {"grade": "mentioned", "query": "implementar consenso Raft con garantias de linealizabilidad"}
  ]
}
```

- `family`: one of `easy`, `paraphrase`, `mixed`, `typos`, `multi_hop`.
  - `easy` is the original set. It is labelled by box and saturated (31/31 at recall@3 in
    the legacy measurements), so it is kept only for comparison.
  - The other four families form the **hard set**. They cover the cases where lexical
    retrieval really struggles: paraphrases that share no vocabulary with the answer,
    mixed English and Spanish, typos, and questions whose answer is spread across several
    sections.
- `query`: the literal user question.
- `expected`: acceptable answers, as labels. `"NN"` accepts any chunk of box NN.
  `"NN · Title"` accepts only that section (a `##` title of the corpus of that locale). The
  hard set is labelled by chunk because that is what reaches the model. A box label would
  count "right box, wrong section" as a hit.
- `uncovered`: questions the corpus does not answer. They are outside recall because no chunk
  is correct. Each one carries the sufficiency grade it should get: `mentioned` (the term
  appears only in prose, which is the hard case) or `absent`.

The keys are validated strictly (`benchmarks/cases.py`). A dataset with an unknown family, an
empty query or a label that does not exist in its corpus fails the tests.

**The English chunk labels are computed, not typed.** The English corpus has exactly the same
`##` sections, in the same order, as the Spanish one in every box. So the i-th section of
box NN in Spanish is the i-th section in English. The Spanish set is the hand-labelled one;
the English file holds the translated queries, and its labels are derived from the Spanish ones:

```bash
python -m benchmarks.sync_labels            # rewrite en labels from es (queries untouched)
python -m benchmarks.sync_labels --check    # exit 1 if they drifted
```

If the two corpora ever stop having the same number of sections in a box, the alignment
raises an error instead of guessing. In English, the `typos` family keeps realistic English
typos (`postgress`, `paymnets`) and `mixed` mixes English and Spanish the way bilingual teams
really write (`necesito rate limiting on my endpoint`).

`datasets/<locale>/tasks.json` holds the task bench requests:
`{"locale", "description", "tasks": [{"name", "request"}]}`.

## `retrieval_eval`: retrieval quality

```bash
python -m benchmarks.retrieval_eval --locale en [--depth 10] [--vector auto|on|off]
                                    [--rerank auto|on|off] [--per-family N] [--save [PATH]]
```

Each case goes through `RetrievalService.retrieve` with the plan the pipeline would use and
family `general`. Production never knows the family of a question, so the feature gate decides
the conditional stages exactly as it does for a real request. `--vector` and `--rerank` force
a stage through the arguments of `retrieve`.

- Scoring uses the knowledge index, ranked to `--depth` (default 10). Each case contributes the
  rank of its first acceptable chunk.
- `R@1`, `R@3`, `R@k` are hit counts. `MRR` is the mean reciprocal rank at depth k.
- The context size is measured on the retrieval production really serves (its own k per index)
  through `ContextBuilder`.
- For `uncovered` cases the report prints the sufficiency grade the pipeline would give,
  compared with the expected one.
- `--save` freezes the report as JSON (default `results/retrieval_eval_<locale>.json`).

**Query rewriting was dropped.** The legacy eval also measured the query the model rewrote
before calling its search tool, using a cache (`eval_cache.json`) that was never committed.
The production pipeline now retrieves with the **literal** question. Only the experimental
architect mode lets the model search with its own words. So measuring the literal question is
measuring production, and the eval makes zero model calls.

Measured on 2026-09-18, production configuration (gate: reranker on, vector off), depth 10:

| family | es MRR | en MRR |
|---|---|---|
| easy (31) | 0.942 | 0.974 |
| paraphrase (8) | 0.427 | 0.451 |
| mixed (4) | 1.000 | 0.833 |
| typos (3) | 0.500 | 0.833 |
| multi_hop (3) | 0.833 | 0.511 |
| **hard total (18)** | **0.634** | **0.610** |

## `calibrate_stages`: which stages switch on

```bash
python -m benchmarks.calibrate_stages [--locale es] [--per-family N] [--no-warmup]
                                      [--report [PATH]] [--write [PATH]]
```

This bench measures four arms on the same set and base, each through `RetrievalService.retrieve`
with `vector=` / `rerank=` forced:

- baseline (BM25 over the three indices)
- `+ reranker`
- `+ vector`
- `+ vector + reranker`

Each arm runs once untimed first. The vector index is built once per chunk set and cached, as
in production. Without the warm-up the first arm would pay the indexing, and the gate would
reject a stage for a cost that belongs to the bench.

The result is the policy the feature gate reads, in the schema of
`src/mirag/resources/feature_gains.json`:

```json
{"reranker": {"typos": {"delta_mrr": 0.3333, "normalized_cost": 0.0012, "measured_on": "2026-09-18",
                        "measured_over": "real pipeline (phase 3)", "baseline": 0.1667,
                        "corpus_locale": "es"}, "...": {}},
 "vector_signal": {"...": {}}}
```

- There is one entry per family (`easy`, `paraphrase`, `mixed`, `typos`, `multi_hop`) plus
  `general`. `general` is the delta over the **hard** set: the easy set is saturated, and a
  stage cannot show a gain against a ceiling.
- The cost normalisation is written down so it can be argued with:

  `normalized_cost = ms_extra_per_query / 1000 + usd_extra_per_query * 100`

  One extra second per query costs 1.0 of MRR, and so does one extra cent per query. The first
  version divided by 100, which made 100 ms worth a whole MRR point. That is absurd next to a
  model call of 2-30 seconds. The divisor was changed after seeing the results, and that
  changed a verdict: with /100 the reranker was rejected on a tie. The docstring of the bench
  records the order of events. Both stages are local (the heuristic reranker and the
  character n-gram vector signal), so their dollar cost is 0.
- The gate switches a stage on for a family when `delta_mrr >= 0.02` and `delta_mrr > normalized_cost`.
- The bench prints what the gate would decide with the new numbers, plus three diagnostics:
  - how many distinct chunks each index brings, and how many are discarded as duplicates;
  - that RRF with a single signal is a passthrough;
  - how many candidates the vector signal adds that BM25 does not.
- Nothing is written by default.
  - `--write` rewrites the production policy (`src/mirag/resources/feature_gains.json`), and
    `--write PATH` writes it somewhere else.
  - `--write` refuses to run with `--per-family`: a policy measured on a sample would decide
    production.
  - `--report` saves the arms and diagnostics (default `results/calibration_<locale>.json`).
- The default locale is `es` because the published policy was measured on the Spanish corpus.
  Re-running without flags therefore compares like with like. Run it with `--locale en` to see
  the English numbers.

## `project_bench`: how many projects out of N are verified

```bash
MIRAG_OFFLINE=0 python -m benchmarks.project_bench 10     # real model, costs money
python -m benchmarks.project_bench 3 --dry [--locale es] [--output PATH]
```

Each run sends the canonical project request ("REST API of books with full CRUD...") through
`QuestionPipeline.run` with its own gateway and budget. In the legacy bench the budget was
shared across the process: a bench of ten ran out at the seventh run and recorded three runs
that never happened. Each run records:

- the certificate status;
- the first failed phase, the first limited phase and the first error step (that is, where it
  broke);
- markers passed out of total, CRUD markers and repairs;
- file and line counts;
- ZIP integrity and size, and whether it is downloadable;
- whether it fulfils the canonical demo contract;
- seconds, cost, calls and tokens.

`--dry` answers with the scripted books project. That proves the measuring machine works, not
that the model can do it, and the report records `"dry": true`.

## `task_bench`: GOOD / CHEAP / FAST

```bash
MIRAG_OFFLINE=0 python -m benchmarks.task_bench [--arm both|baseline|default] [-n N] [--locale en]
python -m benchmarks.task_bench --compare
python -m benchmarks.task_bench --dry
```

Five concurrency-sensitive tasks (booking, payment, stock, rate limiting, queue consumer) run
through `QuestionPipeline.run` under two arms:

- **baseline**: `forced_plan` is `EMPTY_PLAN`. It narrows nothing: no boxes, no filters. It
  keeps one thing from the request: its intent (`needs_code` / `needs_project`). `EMPTY_PLAN`
  alone says "no code needed", so the code stage would offer the model no delivery tool. The
  arm would then measure "the model could not deliver" instead of "retrieval was not
  narrowed". The legacy baseline likewise only emptied the boxes of the deduced plan.
- **default**: no forced plan. The pipeline deduces its own, as in production.

The bench compares three dimensions:

- GOOD: verified success (properties verified by execution / declared) and green runs.
- CHEAP: cost, tokens and context tokens.
- FAST: model calls and seconds.

It reports the median per arm and flags any change beyond ±5% in the wrong direction. The rule
from the legacy bench still holds: an improvement only counts if it does not seriously degrade
the other dimensions. Saving cost does not make up for a drop in verified success.

Running a single arm merges it into `results/task_bench.json`, keeping the latest run of each
arm, so the two paid arms can be run separately and compared with `--compare`. `--dry`
replaces the tasks with the canonical calculator request answered by its script. It tests the
harness, not the model.

## `results/`

`results/*.json` from before this port (`baseline.json`, `calibracion_fase3.json`,
`ganancias.json`, `proyectos.json`...) were produced by the legacy Spanish benches. They are
kept unchanged as the historical record: their keys are Spanish and their shapes are the old
ones. The new benches write English files next to them: `retrieval_eval_<locale>.json`,
`calibration_<locale>.json`, `project_bench.json` and `task_bench.json`.
