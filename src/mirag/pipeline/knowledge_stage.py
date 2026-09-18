"""Stages 2-9: plan, retrieval over three indices, symbols, graph, sufficiency and context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mirag.core.timing import Stopwatch
from mirag.features.flags import FeatureGate
from mirag.pipeline.models import Source, Step, StepListener, StepStatus
from mirag.pipeline.prompts import MEASUREMENT_INSTRUCTIONS
from mirag.retrieval.context import ContextMeasures
from mirag.retrieval.corpus import Chunk
from mirag.retrieval.engine import RetrievalEngine
from mirag.retrieval.plan import EMPTY_PLAN, RetrievalPlan
from mirag.retrieval.service import RetrievalResult
from mirag.retrieval.sufficiency import SufficiencyVerdict
from mirag.retrieval.symbols import Symbol, SymbolIndexCache


@dataclass
class PreparedRequest:
    plan: RetrievalPlan
    retrieval: RetrievalResult
    retrieved: list[tuple[Chunk, float]]
    symbols: list[tuple[Symbol, float]]
    verdict: SufficiencyVerdict
    context: str
    measures: ContextMeasures


class KnowledgeStage:
    def __init__(self, gate: FeatureGate, symbol_cache: SymbolIndexCache, symbols_root: Path) -> None:
        self._gate = gate
        self._symbol_cache = symbol_cache
        self._symbols_root = symbols_root

    def prepare(self, question: str, engine: RetrievalEngine, note: StepListener,
                family: str = "general", forced_plan: RetrievalPlan | None = None) -> PreparedRequest:
        t = engine.catalog

        # ── 2. the plan ──────────────────────────────────────────────────────
        # forced_plan: the benchmarks use it to force an arm without touching globals.
        # RETRIEVAL_PLAN off = no deduced plan: the baseline arm, and the way to check the
        # plan is useful instead of assuming it.
        clock = Stopwatch()
        if forced_plan is not None:
            plan = forced_plan
        elif self._gate.decide("retrieval_plan").enabled:
            plan = engine.deducer.deduce(question)
        else:
            plan = EMPTY_PLAN
        note(Step("retrieval_plan", StepStatus.EXECUTED, plan.summary(t), clock.ms, Source.EXECUTION,
                  {"origin": plan.describe_origin(t), "plan": plan.as_dict()}))

        # ── 3-5. THE retrieval: only one, over the three indices ────────────
        clock.restart()
        retrieval = engine.service.retrieve(question, plan=plan, family=family)
        for stage in retrieval.stages:
            summary = (t("pipeline.retrieval.stage", candidates=stage.candidates, detail=stage.detail)
                       if stage.used else stage.detail)
            note(Step(stage.name, StepStatus.EXECUTED if stage.used else StepStatus.SKIPPED, summary,
                      stage.ms, Source.CORPUS))
        for stage_name, reason in retrieval.fallbacks:
            note(Step(f"fallback:{stage_name}", StepStatus.FALLBACK, reason, 0.0, Source.EXECUTION))
        note(Step("retrieval", StepStatus.EXECUTED, f"{retrieval.summary()} · {retrieval.metrics['ms']} ms",
                  clock.ms, Source.CORPUS, {"ids": retrieval.ids(), "methods": retrieval.metrics["methods"]}))
        retrieved = [(rc.chunk, rc.score) for rc in retrieval.selected]

        # ── 6. symbols, only if the plan asks for them ──────────────────────
        clock.restart()
        symbols: list[tuple[Symbol, float]] = []
        symbol_gate = self._gate.decide("symbol_retrieval")
        if plan.needs_symbols and symbol_gate.enabled:
            try:
                index = self._symbol_cache.get(self._symbols_root)
                symbols = engine.symbols.search(index, question, k=5)
                note(Step("symbols", StepStatus.EXECUTED,
                          t("pipeline.symbols.found", found=len(symbols), total=len(index)), clock.ms,
                          Source.EXECUTION, [(s.name, s.file, s.line) for s, _ in symbols]))
            except Exception as exc:
                note(Step("symbols", StepStatus.ERROR, f"{type(exc).__name__}: {exc}", clock.ms, Source.EXECUTION))
        else:
            reason = t("pipeline.symbols.not_needed") if not plan.needs_symbols else symbol_gate.explain(t)
            note(Step("symbols", StepStatus.SKIPPED, reason, clock.ms, Source.EXECUTION))

        # ── 7. graph, only if measured AND the plan asks for it ─────────────
        clock.restart()
        graph_gate = self._gate.decide("graph_retrieval", family)
        if graph_gate.enabled and plan.needs_graph:
            try:
                extra, steps = engine.graph.expand([c for c, _ in retrieved], hops=1)
                retrieved += [(c, 0.0) for c in extra]
                note(Step("graph", StepStatus.EXECUTED, t("pipeline.graph.found", count=len(extra)), clock.ms,
                          Source.CORPUS, [s.explanation for s in steps]))
            except Exception as exc:
                note(Step("graph", StepStatus.ERROR, f"{type(exc).__name__}: {exc}", clock.ms, Source.CORPUS))
        else:
            reason = graph_gate.explain(t) if not graph_gate.enabled else t("pipeline.graph.not_needed")
            note(Step("graph", StepStatus.SKIPPED, reason, clock.ms, Source.EXECUTION))

        # ── 8. is this enough to answer? ────────────────────────────────────
        clock.restart()
        sufficiency_gate = self._gate.decide("sufficiency")
        verdict = (engine.sufficiency.evaluate(question, retrieved, plan) if sufficiency_gate.enabled
                   else engine.sufficiency.not_evaluated(sufficiency_gate.explain(t)))
        note(Step("sufficiency", StepStatus.EXECUTED if verdict.sufficient else StepStatus.FALLBACK,
                  f"{t(f'sufficiency.grade.{verdict.grade.value}')}: {verdict.reason}", clock.ms, Source.CORPUS,
                  verdict.signals))

        # ── 9. context: BUILT FROM THE RetrievalResult ──────────────────────
        clock.restart()
        # The coverage warning only applies to questions answered WITH the corpus: in a code
        # task correctness is decided by execution, not by the documents.
        context, measures = engine.context.build(
            retrieval, request=question,
            symbols=[s.describe() for s, _ in symbols],
            coverage_warning=None if verdict.sufficient else verdict.warning,
            extra_instructions=MEASUREMENT_INSTRUCTIONS if plan.needs_code else None,
        )
        summary = t("pipeline.context.summary", tokens=f"{measures.approx_tokens:,}", included=measures.included)
        if measures.discarded:
            summary += " · " + t("pipeline.context.discarded", count=len(measures.discarded))
        note(Step("context", StepStatus.EXECUTED, summary, clock.ms, Source.CORPUS, measures.as_dict()))
        return PreparedRequest(plan, retrieval, retrieved, symbols, verdict, context, measures)
