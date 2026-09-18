"""Retrieval eval: MRR and recall@k per query family, on the path production really runs.

WHAT IS MEASURED
    Every case goes through ``RetrievalService.retrieve`` - the SAME call the pipeline makes
    (``KnowledgeStage``), on an engine built by the same ``RetrievalEngineFactory``, with the
    plan the pipeline would use and the feature gate deciding the conditional stages exactly
    as it does in production (family ``general``: production never knows the family of a
    question). ``--vector`` / ``--rerank`` force a stage through the arguments of
    ``retrieve``, never through globals.

    Labels are chunks of the knowledge index, so recall and MRR are scored on THAT index,
    ranked down to ``--depth`` (10). The other two indices still run: they are part of the
    same call and feed the context, whose size is reported.

WHAT IS NOT MEASURED ANY MORE: QUERY REWRITING
    The legacy eval measured two columns: the literal question and the query the model
    rewrote before calling its search tool (cached in ``eval_cache.json``). Both are gone for
    good reasons: the cache was never committed, and the production pipeline now retrieves
    with the LITERAL question (only the experimental architect mode lets the model search
    with its own words). Measuring the literal question is measuring production.

COST
    0 model calls, 0 dollars: the container is built with the offline lock on, so even an
    embeddings backend configured by environment falls back to the local one.

    python -m benchmarks.retrieval_eval --locale en
    python -m benchmarks.retrieval_eval --locale es --save          # results/retrieval_eval_es.json
    python -m benchmarks.retrieval_eval --locale en --rerank on --vector off
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmarks.cases import EASY, RetrievalCase, RetrievalDataset, UncoveredCase
from benchmarks.harness import (
    RESULTS_DIR,
    RankMetrics,
    isolated_container,
    median,
    utf8_console,
    write_json,
)
from mirag.retrieval.engine import RetrievalEngine, RetrievalEngineFactory
from mirag.retrieval.plan import EMPTY_PLAN, RetrievalPlan
from mirag.retrieval.service import RetrievalResult

DEPTH = 10
"""How far down the ranking a hit still counts, for MRR and recall@k."""
PRODUCTION_FAMILY = "general"
"""What the pipeline passes to the gate: it never knows the family of a question."""
MODES = {"auto": None, "on": True, "off": False}


def production_plan(engines: RetrievalEngineFactory, engine: RetrievalEngine, query: str) -> RetrievalPlan:
    """The plan ``KnowledgeStage`` would use: deduced, unless the gate switched plans off."""
    return engine.deducer.deduce(query) if engines.gate.decide("retrieval_plan").enabled else EMPTY_PLAN


def describe_mode(value: bool | None) -> str:
    return "auto (gate)" if value is None else ("forced on" if value else "forced off")


# ── results ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CaseOutcome:
    case: RetrievalCase
    positions: tuple[int, ...]
    """Every rank (1 = first) of an acceptable chunk within the depth."""
    context_tokens: int
    """Approximate tokens of the context production would build for this question."""
    ms: float

    @property
    def first(self) -> int | None:
        return self.positions[0] if self.positions else None

    def as_dict(self) -> dict[str, Any]:
        return {**self.case.as_dict(), "positions": list(self.positions),
                "context_tokens": self.context_tokens, "ms": round(self.ms, 2)}


@dataclass(frozen=True, slots=True)
class UncoveredOutcome:
    case: UncoveredCase
    observed: str
    """The sufficiency grade the pipeline would give."""

    @property
    def agrees(self) -> bool:
        return self.observed == self.case.grade

    def as_dict(self) -> dict[str, Any]:
        return {**self.case.as_dict(), "observed": self.observed}


@dataclass(frozen=True, slots=True)
class EvalReport:
    locale: str
    depth: int
    vector: bool | None
    rerank: bool | None
    chunks: int
    outcomes: tuple[CaseOutcome, ...]
    uncovered: tuple[UncoveredOutcome, ...] = ()

    def metrics(self, outcomes: Sequence[CaseOutcome]) -> RankMetrics:
        return RankMetrics.of([o.first for o in outcomes], self.depth)

    @property
    def families(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(o.case.family for o in self.outcomes))

    def by_family(self) -> dict[str, RankMetrics]:
        return {f: self.metrics([o for o in self.outcomes if o.case.family == f]) for f in self.families}

    @property
    def easy(self) -> RankMetrics:
        return self.metrics([o for o in self.outcomes if o.case.family == EASY])

    @property
    def hard(self) -> RankMetrics:
        return self.metrics([o for o in self.outcomes if o.case.family != EASY])

    @property
    def total(self) -> RankMetrics:
        return self.metrics(self.outcomes)

    def misses(self) -> list[CaseOutcome]:
        """Hard cases with no acceptable chunk within the depth: where the work is."""
        return [o for o in self.outcomes if o.case.family != EASY and o.first is None]

    def context_stats(self) -> dict[str, float]:
        tokens = [o.context_tokens for o in self.outcomes]
        return {"median": median(tokens), "max": max(tokens, default=0), "min": min(tokens, default=0)}

    def as_dict(self) -> dict[str, Any]:
        return {
            "locale": self.locale,
            "measured_with": "literal question through RetrievalService.retrieve (production path)",
            "model_calls": 0,
            "depth": self.depth,
            "stages": {"vector": describe_mode(self.vector), "rerank": describe_mode(self.rerank)},
            "chunks": self.chunks,
            "families": {f: m.as_dict() for f, m in self.by_family().items()},
            "easy": self.easy.as_dict(),
            "hard": self.hard.as_dict(),
            "total": self.total.as_dict(),
            "context_tokens": self.context_stats(),
            "cases": [o.as_dict() for o in self.outcomes],
            "uncovered": [o.as_dict() for o in self.uncovered],
        }


# ── the evaluator ────────────────────────────────────────────────────────────


class RetrievalEvaluator:
    """Runs a labelled set through the production retrieval of one locale."""

    def __init__(self, engines: RetrievalEngineFactory, locale: str, depth: int = DEPTH,
                 vector: bool | None = None, rerank: bool | None = None) -> None:
        self._engines = engines
        self._engine = engines.get(locale)
        self.locale = locale
        self.depth = depth
        self.vector = vector
        self.rerank = rerank

    def _retrieve(self, query: str, plan: RetrievalPlan, depth: int | None = None) -> RetrievalResult:
        limits = {"knowledge": depth} if depth is not None else None
        return self._engine.service.retrieve(query, plan=plan, family=PRODUCTION_FAMILY,
                                             vector=self.vector, rerank=self.rerank, per_index_limit=limits)

    def evaluate_case(self, case: RetrievalCase) -> CaseOutcome:
        plan = production_plan(self._engines, self._engine, case.query)
        ranked = self._retrieve(case.query, plan, self.depth)
        positions = case.hit_positions(rc.chunk for rc in ranked.by_index["knowledge"])
        # The context is measured on the retrieval production really does (its own k per index),
        # not on the deeper ranking used for scoring.
        served = self._retrieve(case.query, plan)
        _, measures = self._engine.context.build(served, request=case.query)
        return CaseOutcome(case, positions, measures.approx_tokens, float(ranked.metrics["ms"]))

    def evaluate_uncovered(self, case: UncoveredCase) -> UncoveredOutcome:
        plan = production_plan(self._engines, self._engine, case.query)
        served = self._retrieve(case.query, plan)
        verdict = self._engine.sufficiency.evaluate(
            case.query, [(rc.chunk, rc.score) for rc in served.selected], plan)
        return UncoveredOutcome(case, verdict.grade.value)

    def run(self, dataset: RetrievalDataset) -> EvalReport:
        if dataset.locale != self.locale:
            raise ValueError(f"a {dataset.locale!r} dataset cannot be scored on the {self.locale!r} corpus")
        return EvalReport(
            locale=self.locale,
            depth=self.depth,
            vector=self.vector,
            rerank=self.rerank,
            chunks=len(self._engine.corpus.chunks),
            outcomes=tuple(self.evaluate_case(case) for case in dataset.cases),
            uncovered=tuple(self.evaluate_uncovered(case) for case in dataset.uncovered),
        )


# ── presentation ─────────────────────────────────────────────────────────────


def render(report: EvalReport) -> str:
    lines = [f"retrieval eval · locale {report.locale} · {report.chunks} chunks · "
             f"{report.easy.n} easy · {report.hard.n} hard · OFFLINE (0 model calls)",
             f"vector: {describe_mode(report.vector)} · reranker: {describe_mode(report.rerank)} · "
             f"depth {report.depth}"]
    families = report.by_family()
    if EASY in families:
        lines += ["", "EASY SET (labelled by box - saturated, kept to compare)",
                  RankMetrics.header(report.depth), families[EASY].row(EASY)]
    hard = [f for f in families if f != EASY]
    if hard:
        lines += ["", "HARD SET (labelled by chunk - this is where the headroom is)",
                  RankMetrics.header(report.depth)]
        lines += [families[f].row(f) for f in hard]
        if len(hard) > 1:
            lines.append(report.hard.row("TOTAL"))
    context = report.context_stats()
    lines += ["", f"retrieved context: median {context['median']:,.0f} tokens · "
                  f"max {context['max']:,} · min {context['min']:,}"]
    misses = report.misses()
    if misses:
        lines += ["", f"hard cases not retrieved within {report.depth} positions ({len(misses)}):"]
        for outcome in misses:
            lines.append(f"  x [{outcome.case.family}] {outcome.case.query}")
            lines.append(f"      expected: {', '.join(str(label) for label in outcome.case.expected)}")
    if report.uncovered:
        agreeing = sum(1 for o in report.uncovered if o.agrees)
        lines += ["", f"not covered by the corpus ({len(report.uncovered)} cases, outside recall; "
                      f"sufficiency agrees on {agreeing}):"]
        for outcome in report.uncovered:
            mark = "ok" if outcome.agrees else "!!"
            lines.append(f"  {mark} expected {outcome.case.grade:<9} observed {outcome.observed:<13} "
                         f"{outcome.case.query}")
    return "\n".join(lines)


def default_output(locale: str) -> Path:
    return RESULTS_DIR / f"retrieval_eval_{locale}.json"


def main(argv: Sequence[str] | None = None) -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--locale", choices=("en", "es"), default="en")
    parser.add_argument("--depth", type=int, default=DEPTH, help=f"ranking depth for MRR and recall@k (default {DEPTH})")
    parser.add_argument("--vector", choices=tuple(MODES), default="auto", help="vector signal: gate decides, or force")
    parser.add_argument("--rerank", choices=tuple(MODES), default="auto", help="reranker: gate decides, or force")
    parser.add_argument("--per-family", type=int, default=0, metavar="N", help="only the first N cases of each family")
    parser.add_argument("--save", nargs="?", const="", default=None, metavar="PATH",
                        help="freeze the measurement as JSON (default: results/retrieval_eval_<locale>.json)")
    args = parser.parse_args(argv)

    dataset = RetrievalDataset.load(args.locale)
    if args.per_family > 0:
        dataset = dataset.subset(args.per_family)
    started = time.perf_counter()
    with isolated_container(offline=True) as container:
        evaluator = RetrievalEvaluator(container.engines, args.locale, args.depth,
                                       vector=MODES[args.vector], rerank=MODES[args.rerank])
        report = evaluator.run(dataset)
    print(render(report))
    print(f"\n{time.perf_counter() - started:.1f}s")
    if args.save is not None:
        path = write_json(Path(args.save) if args.save else default_output(args.locale), report.as_dict())
        print(f"saved to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
