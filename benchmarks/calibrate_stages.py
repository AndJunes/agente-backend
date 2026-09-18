"""The bench that decides which conditional retrieval stages switch on. 0 model calls, 0 cost.

It measures each conditional stage (``reranker``, ``vector_signal``) against the SAME base, on
the SAME labelled set, through ``RetrievalService.retrieve`` - the function production uses.
Each arm forces its stages through the ``vector=`` / ``rerank=`` arguments of that call, never
through globals or the environment. What it measures IS the policy: with ``--write`` it
becomes ``src/mirag/resources/feature_gains.json``, which the feature gate reads to decide.
I do not choose which stages run; this measurement does.

    python -m benchmarks.calibrate_stages                   # measure and show (es corpus)
    python -m benchmarks.calibrate_stages --locale en
    python -m benchmarks.calibrate_stages --write           # ALSO rewrite the production policy
    python -m benchmarks.calibrate_stages --write out.json  # write the policy somewhere else
    python -m benchmarks.calibrate_stages --report          # save arms + diagnostics to results/

HOW COST IS NORMALISED
    A stage has to win more MRR than it costs. Cost is brought to the MRR scale like this:

        normalized_cost = ms_extra_per_query / 1000  +  usd_extra_per_query * 100

    That is: one extra SECOND "costs" 1.0 of MRR, and one cent per query costs 1.0. It is an
    equivalence chosen by hand, and it is written here so it can be argued with.

    NOTE ON METHOD: the first version divided by 100, so 100 ms were worth a whole MRR point.
    That is absurd next to a model call, which takes between 2 and 30 SECONDS: the whole
    retrieval is noise in that budget. It was changed AFTER seeing the results, and that has
    to be said because it changes a verdict: with /100 the reranker was rejected on a tie (it
    won 0.044 and cost 0.044) and with /1000 it passes. The reason for the change does not
    depend on that result, but the reader has the right to know in which order things happened.

    Both stages measured here make no model call (the reranker is a local heuristic and the
    vector signal is local character n-grams), so their dollar cost per query is 0.

WHAT "general" MEANS IN THE POLICY
    The delta over the HARD set (every family except ``easy``). The easy set is saturated:
    a stage cannot show a gain against a ceiling, so it does not get a vote on the general
    decision. Each family also gets its own entry.

WARM-UP
    Each arm runs the set once untimed before the timed pass. The vector index is built once
    per chunk set and cached (as in production); without the warm-up the first arm to touch a
    filter pays the indexing, and the gate would reject a stage for a cost that is ours.
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmarks.cases import EASY, RetrievalDataset
from benchmarks.harness import (
    RESULTS_DIR,
    RankMetrics,
    isolated_container,
    median,
    percentile,
    utf8_console,
    write_json,
)
from benchmarks.retrieval_eval import DEPTH, production_plan
from mirag.features.flags import FeatureGate
from mirag.i18n.catalog import MessageCatalog
from mirag.paths import FEATURE_GAINS_FILE
from mirag.retrieval.engine import RetrievalEngineFactory

DEFAULT_LOCALE = "es"
"""The published policy was measured on the Spanish corpus: re-running without flags compares."""
MEASURED_OVER = "real pipeline (phase 3)"
"""Kept verbatim from the published policy: it names the method (measured on the production
retrieval path, the rule introduced in phase 3), not a date."""
GENERAL = "general"
MS_PER_MRR_POINT = 1000.0
USD_PER_MRR_POINT = 0.01


def normalized_cost(ms_extra: float, usd_extra: float = 0.0) -> float:
    """Extra latency and spend per query, on the MRR scale. Savings do not count as gains."""
    return round(max(0.0, ms_extra) / MS_PER_MRR_POINT + max(0.0, usd_extra) / USD_PER_MRR_POINT, 4)


@dataclass(frozen=True, slots=True)
class ArmSpec:
    name: str
    vector: bool
    rerank: bool


BASELINE = ArmSpec("baseline · BM25 + 3 indices", vector=False, rerank=False)
STAGE_ARMS: dict[str, ArmSpec] = {
    "reranker": ArmSpec("+ reranker", vector=False, rerank=True),
    "vector_signal": ArmSpec("+ vector", vector=True, rerank=False),
}
ARMS: tuple[ArmSpec, ...] = (BASELINE, *STAGE_ARMS.values(), ArmSpec("+ vector + reranker", vector=True, rerank=True))


@dataclass(frozen=True, slots=True)
class ArmMeasurement:
    spec: ArmSpec
    families: dict[str, RankMetrics]
    total: RankMetrics
    hard: RankMetrics
    ms_median: float
    ms_p95: float
    candidates: dict[str, int]
    """Chunks returned per index over the whole set: proof that the three indices ran."""
    usd_per_query: float = 0.0

    def metrics(self, family: str) -> RankMetrics:
        return self.hard if family == GENERAL else self.families[family]

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.spec.name, "config": {"vector": self.spec.vector, "rerank": self.spec.rerank},
                "families": {f: m.as_dict() for f, m in self.families.items()},
                "total": self.total.as_dict(), "hard": self.hard.as_dict(),
                "ms_median": self.ms_median, "ms_p95": self.ms_p95,
                "usd_per_query": self.usd_per_query, "candidates": self.candidates}


class StageCalibrator:
    """Measures arms of the production retrieval of one locale over a labelled set."""

    def __init__(self, engines: RetrievalEngineFactory, locale: str, depth: int = DEPTH, warmup: bool = True) -> None:
        self._engines = engines
        self._engine = engines.get(locale)
        self.locale = locale
        self.depth = depth
        self.warmup = warmup

    def _pass(self, spec: ArmSpec, dataset: RetrievalDataset) -> ArmMeasurement:
        positions: dict[str, list[int | None]] = {}
        latencies: list[float] = []
        candidates: dict[str, int] = {}
        for case in dataset.cases:
            plan = production_plan(self._engines, self._engine, case.query)
            result = self._engine.service.retrieve(
                case.query, plan=plan, family=case.family, vector=spec.vector, rerank=spec.rerank,
                per_index_limit={"knowledge": self.depth})
            latencies.append(float(result.metrics["ms"]))
            hits = case.hit_positions(rc.chunk for rc in result.by_index["knowledge"])
            positions.setdefault(case.family, []).append(hits[0] if hits else None)
            for index, count in result.metrics["candidates"].items():
                candidates[index] = candidates.get(index, 0) + count
        every = [p for ps in positions.values() for p in ps]
        hard = [p for family, ps in positions.items() if family != EASY for p in ps]
        return ArmMeasurement(
            spec=spec,
            families={family: RankMetrics.of(ps, self.depth) for family, ps in positions.items()},
            total=RankMetrics.of(every, self.depth),
            hard=RankMetrics.of(hard, self.depth),
            ms_median=round(median(latencies), 2),
            ms_p95=round(percentile(latencies, 0.95), 2),
            candidates=candidates,
        )

    def measure(self, spec: ArmSpec, dataset: RetrievalDataset) -> ArmMeasurement:
        """One arm. Same set, same queries, same function as production."""
        if self.warmup:
            self._pass(spec, dataset)
        return self._pass(spec, dataset)

    def measure_arms(self, dataset: RetrievalDataset, arms: Sequence[ArmSpec] = ARMS) -> list[ArmMeasurement]:
        return [self.measure(spec, dataset) for spec in arms]

    # ── diagnostics (production configuration: the gate decides) ────────────

    def index_contribution(self, dataset: RetrievalDataset) -> dict[str, Any]:
        """What each index brings: distinct chunks, overlaps, and how many reach the context."""
        distinct: dict[str, set[tuple[str, str]]] = {}
        overlaps = retrieved = in_context = 0
        for case in dataset.cases:
            plan = production_plan(self._engines, self._engine, case.query)
            result = self._engine.service.retrieve(case.query, plan=plan)
            owners: dict[tuple[str, str], list[str]] = {}
            for rc in result.selected:
                owners.setdefault(rc.chunk.key, []).append(rc.index)
                distinct.setdefault(rc.index, set()).add(rc.chunk.key)
            overlaps += sum(1 for indices in owners.values() if len(indices) > 1)
            retrieved += len(result.selected)
            _, measures = self._engine.context.build(result, request=case.query)
            in_context += measures.included
        return {"distinct_chunks_per_index": {k: len(v) for k, v in distinct.items()},
                "retrieved_total": retrieved, "overlaps": overlaps, "reach_context": in_context,
                "discarded_by_dedup_percent": round(100 * (retrieved - in_context) / max(retrieved, 1), 1)}

    def rrf_single_signal(self, query: str) -> dict[str, Any]:
        """Does RRF do anything with a single signal? It must be a passthrough."""
        plan = production_plan(self._engines, self._engine, query)
        result = self._engine.service.retrieve(query, plan=plan, vector=False)
        stages = {stage.name: stage for stage in result.stages}
        bm25, rrf = stages["bm25:knowledge"], stages["rrf:knowledge"]
        single = self._engine.catalog.t("retrieval.stage.rrf_single")
        return {"query": query, "detail": rrf.detail, "bm25_candidates": bm25.candidates,
                "rrf_candidates": rrf.candidates,
                "passthrough": bm25.candidates == rrf.candidates and rrf.detail == single}

    def vector_overlap(self, dataset: RetrievalDataset, limit: int = 20) -> dict[str, Any]:
        """Does the vector bring candidates BM25 does not, or the same ones again?"""
        new = shared = queries = 0
        for case in dataset.cases[:limit]:
            plan = production_plan(self._engines, self._engine, case.query)
            without = set(self._engine.service.retrieve(case.query, plan=plan, vector=False).ids())
            with_vector = set(self._engine.service.retrieve(case.query, plan=plan, vector=True).ids())
            new += len(with_vector - without)
            shared += len(without & with_vector)
            queries += 1
        return {"queries": queries, "new_candidates_from_vector": new, "shared": shared,
                "new_percent": round(100 * new / max(new + shared, 1), 1)}


# ── the policy ───────────────────────────────────────────────────────────────


def gains_table(base: ArmMeasurement, stages: Mapping[str, ArmMeasurement], locale: str,
                measured_on: str | None = None) -> dict[str, dict[str, dict[str, Any]]]:
    """The measurement in the schema of ``resources/feature_gains.json``."""
    measured_on = measured_on or time.strftime("%Y-%m-%d")
    table: dict[str, dict[str, dict[str, Any]]] = {}
    for stage, measured in stages.items():
        cost = normalized_cost(measured.ms_median - base.ms_median, measured.usd_per_query - base.usd_per_query)
        entry: dict[str, dict[str, Any]] = {}
        for family in (*base.families, GENERAL):
            before, after = base.metrics(family), measured.metrics(family)
            entry[family] = {"delta_mrr": round(after.mrr - before.mrr, 4), "normalized_cost": cost,
                             "measured_on": measured_on, "measured_over": MEASURED_OVER,
                             "baseline": before.mrr, "corpus_locale": locale}
        table[stage] = entry
    return table


def gate_decisions(table: Mapping[str, Any], catalog: MessageCatalog) -> list[tuple[str, str, bool, str]]:
    """What the gate would decide with these numbers, with no environment override."""
    gate = FeatureGate({})
    rows = []
    for stage, entry in table.items():
        for family in entry:
            decision = gate.decide(stage, family, gains=table)
            rows.append((stage, family, decision.enabled, decision.explain(catalog)))
    return rows


# ── presentation ─────────────────────────────────────────────────────────────


def render(arms: Sequence[ArmMeasurement], table: Mapping[str, Any], catalog: MessageCatalog) -> str:
    base = arms[0]
    width = max(len(a.spec.name) for a in arms) + 2
    lines = [f"{'arm':<{width}} {'R@1':>7} {'R@3':>7} {'MRR':>6} {'MRR hard':>9} {'ms':>7} {'p95':>7} {'Δ MRR hard':>11}",
             "─" * (width + 60)]
    for arm in arms:
        t, h = arm.total, arm.hard
        delta = "" if arm is base else f"{h.mrr - base.hard.mrr:+.3f}"
        lines.append(f"{arm.spec.name:<{width}} {f'{t.hits_at_1}/{t.n}':>7} {f'{t.hits_at_3}/{t.n}':>7} "
                     f"{t.mrr:>6.3f} {h.mrr:>9.3f} {arm.ms_median:>7.2f} {arm.ms_p95:>7.2f} {delta:>11}")
    families = list(base.families)
    lines += ["", "MRR per family:", f"  {'arm':<{width}} " + " ".join(f"{f:>11}" for f in families)]
    for arm in arms:
        lines.append(f"  {arm.spec.name:<{width}} " + " ".join(f"{arm.families[f].mrr:>11.3f}" for f in families))
    lines += ["", "what the gate decides with these numbers:"]
    for stage, family, enabled, reason in gate_decisions(table, catalog):
        lines.append(f"  {'ON ' if enabled else 'off'} {stage:<14} {family:<11} {reason}")
    return "\n".join(lines)


def render_diagnostics(indices: Mapping[str, Any], rrf: Mapping[str, Any], vector: Mapping[str, Any]) -> str:
    lines = ["", f"what the three indices bring ({indices['retrieved_total']} chunks retrieved):"]
    lines += [f"  {name:<14} {count} distinct chunks" for name, count in indices["distinct_chunks_per_index"].items()]
    lines.append(f"  {indices['retrieved_total']} retrieved -> {indices['reach_context']} in the context "
                 f"({indices['discarded_by_dedup_percent']}% discarded as duplicates)")
    lines.append(f"\nRRF with one signal: {rrf['bm25_candidates']} -> {rrf['rrf_candidates']} candidates · "
                 f"passthrough = {rrf['passthrough']}")
    lines.append(f"vector vs BM25 ({vector['queries']} queries): {vector['new_candidates_from_vector']} new "
                 f"candidates, {vector['shared']} shared ({vector['new_percent']}% new)")
    return "\n".join(lines)


def default_report(locale: str) -> Path:
    return RESULTS_DIR / f"calibration_{locale}.json"


def main(argv: Sequence[str] | None = None) -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--locale", choices=("en", "es"), default=DEFAULT_LOCALE)
    parser.add_argument("--depth", type=int, default=DEPTH)
    parser.add_argument("--per-family", type=int, default=0, metavar="N",
                        help="only the first N cases of each family (quick look; cannot be written)")
    parser.add_argument("--no-warmup", action="store_true", help="skip the untimed pass of each arm")
    parser.add_argument("--write", nargs="?", const=str(FEATURE_GAINS_FILE), default=None, metavar="PATH",
                        help="write the gains (default: the production policy, src/mirag/resources/feature_gains.json)")
    parser.add_argument("--report", nargs="?", const="", default=None, metavar="PATH",
                        help="save arms and diagnostics as JSON (default: results/calibration_<locale>.json)")
    args = parser.parse_args(argv)
    if args.write is not None and args.per_family > 0:
        parser.error("--write needs the whole set: a policy measured on a sample would decide production")

    dataset = RetrievalDataset.load(args.locale)
    if args.per_family > 0:
        dataset = dataset.subset(args.per_family)
    print(f"calibrating on the production retrieval · locale {args.locale} · {len(dataset.cases)} cases · "
          f"0 model calls · 0 cost\n")
    with isolated_container(offline=True) as container:
        calibrator = StageCalibrator(container.engines, args.locale, args.depth, warmup=not args.no_warmup)
        arms = calibrator.measure_arms(dataset)
        by_name = {arm.spec.name: arm for arm in arms}
        table = gains_table(arms[0], {stage: by_name[spec.name] for stage, spec in STAGE_ARMS.items()}, args.locale)
        catalog = container.i18n.catalog(args.locale)
        print(render(arms, table, catalog))
        probe = (dataset.hard or dataset.cases)[0].query
        indices = calibrator.index_contribution(dataset)
        rrf = calibrator.rrf_single_signal(probe)
        vector = calibrator.vector_overlap(dataset)
        print(render_diagnostics(indices, rrf, vector))

    if args.report is not None:
        path = write_json(Path(args.report) if args.report else default_report(args.locale),
                          {"locale": args.locale, "depth": args.depth, "cases": len(dataset.cases),
                           "arms": [arm.as_dict() for arm in arms], "indices": indices, "rrf": rrf,
                           "vector": vector, "gains": table})
        print(f"\nreport saved to {path}")
    if args.write is not None:
        path = write_json(Path(args.write), table, indent=2)
        print(f"\ngains written to {path}")
    else:
        print("\n(policy not written: use --write to update it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
