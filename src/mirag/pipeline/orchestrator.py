"""The question pipeline: composes the stages and records the trace."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mirag.core.timing import Stopwatch
from mirag.llm.gateway import LLMGateway
from mirag.observability.tracing import TRACE_VERSION, TraceRecord, TraceWriter
from mirag.pipeline.code_stage import CodeDeliveryStage
from mirag.pipeline.knowledge_stage import KnowledgeStage, PreparedRequest
from mirag.pipeline.models import PipelineRun, Source, Step, StepListener, StepStatus
from mirag.pipeline.project_stage import ProjectDeliveryStage
from mirag.retrieval.engine import RetrievalEngine, RetrievalEngineFactory
from mirag.retrieval.plan import RetrievalPlan
from mirag.self_knowledge.project_state import ProjectStateResponder

StateResponderProvider = Callable[[str], ProjectStateResponder]


class QuestionPipeline:
    """Walks the whole diagram. Returns everything that happened, not only the result."""

    def __init__(
        self,
        engines: RetrievalEngineFactory,
        state: StateResponderProvider,
        knowledge: KnowledgeStage,
        code: CodeDeliveryStage,
        project: ProjectDeliveryStage,
        traces: TraceWriter,
    ) -> None:
        self._engines = engines
        self._state = state
        self._knowledge = knowledge
        self._code = code
        self._project = project
        self._traces = traces

    def run(
        self,
        question: str,
        gateway: LLMGateway,
        locale: str = "en",
        family: str = "general",
        on_step: StepListener | None = None,
        persist: bool = True,
        forced_plan: RetrievalPlan | None = None,
        version: str | None = None,
        output_folder: Path | None = None,
    ) -> PipelineRun:
        started = time.time()
        # So the trace records what THIS run cost and not the running total of the process.
        spent_before = gateway.budget.snapshot()
        engine = self._engines.get(locale)
        run = PipelineRun(question=question, locale=locale, simulated=gateway.simulated)

        def note(step: Step) -> None:
            run.steps.append(step)
            if on_step:
                on_step(step)

        # ── 1. project state: what we already know is not searched ─────────
        clock = Stopwatch()
        direct = self._state(locale).answer(question)
        if direct:
            note(Step("project_state", StepStatus.EXECUTED, engine.catalog.t("pipeline.state.answered"),
                      clock.ms, Source.EXECUTION))
            run.answer = direct
            run.simulated = False
            return run
        note(Step("project_state", StepStatus.SKIPPED, engine.catalog.t("pipeline.state.not_about_mirag"),
                  clock.ms, Source.EXECUTION))

        prepared = self._knowledge.prepare(question, engine, note, family, forced_plan)
        run.plan = prepared.plan
        run.verdict = prepared.verdict

        # ── 10-bis. is a whole PROJECT requested? ───────────────────────────
        if prepared.plan.needs_project:
            self._project.run(run, prepared, engine, gateway, note, persist, version or TRACE_VERSION)
            mode = "project"
        else:
            self._code.run(run, prepared, engine, gateway, note, persist, output_folder)
            mode = "pipeline"

        # ── 12. trace ────────────────────────────────────────────────────────
        # `persist` decides whether FILES are written. The record is another matter: a call
        # that cost money must be written down even when nothing was wanted on disk. Doubles do
        # not dirty the file when nothing is persisted: they cost nothing.
        if persist or not gateway.simulated:
            record = self._record(run, prepared, engine, gateway, mode, spent_before)
            run.trace = self._traces.write(
                record, time.time() - started,
                version=version or (f"{TRACE_VERSION}-offline" if gateway.simulated else TRACE_VERSION))
        return run

    @staticmethod
    def _record(run: PipelineRun, prepared: PreparedRequest, engine: RetrievalEngine, gateway: LLMGateway,
                mode: str, spent_before: Any) -> TraceRecord:
        plan = prepared.plan
        retrieval = prepared.retrieval
        certificate = run.certificate
        if certificate is not None:
            status = certificate.status.value
            verification: dict[str, Any] | None = {"status": certificate.status.value,
                                                   "header": certificate.reason,
                                                   "markers": dict(certificate.markers)}
        else:
            status = run.execution.status.value if run.execution is not None else "no_code"
            verification = run.execution.as_record() if run.execution is not None else None
        package = run.artifact.package if run.artifact is not None else None
        extra: dict[str, Any] = {
            "plan": {"origin": plan.origin, "domains": list(plan.domains), "needs_code": plan.needs_code,
                     "needs_project": plan.needs_project, "needs_symbols": plan.needs_symbols,
                     "needs_graph": plan.needs_graph, "depth": plan.depth},
            "filters": retrieval.filters,
            "retrieval": {"ids": retrieval.ids(), "candidates": retrieval.metrics["candidates"],
                          "methods": retrieval.metrics["methods"], "ms": retrieval.metrics["ms"],
                          "per_index": {k: len(v) for k, v in retrieval.by_index.items()},
                          "symbols": len(prepared.symbols) or None},
            "context": prepared.measures.as_dict(with_discarded=False),
            "verification": verification,
            "anti_patterns": _count(run.anti_pattern_coverage) or None,
            "anti_patterns_detail": [{"obligation": r.obligation, "status": r.status.value, "reason": r.reason_code}
                                     for r in run.anti_pattern_coverage[:20]],
            "repair_attempts": len(certificate.repairs) if certificate is not None else int(run.repaired),
            "final_status": status,
            "fallbacks": [{"stage": a, "reason": b} for a, b in retrieval.fallbacks],
            "errors": [{"stage": s.name, "detail": s.summary} for s in run.steps if s.status is StepStatus.ERROR],
            "model": gateway.model_name,
            "model_route": None,  # there is no active router: null, not invented
            "tools": ([{"tool": "generate_project", "status": status}] if certificate is not None else
                      [{"tool": "run_code", "status": status}] if run.execution is not None else []),
            "project": ({"files": run.project.totals["files"], "bytes": run.project.totals["bytes"],
                         "status": status, "zip_bytes": package.size if package else None,
                         "integrity": package.ok if package else None,
                         "artifact": run.artifact.id if run.artifact else None}
                        if run.project is not None else None),
        }
        return TraceRecord(
            task=run.question, mode=mode, status=status, simulated=gateway.simulated,
            evidence=list(run.evidence), boxes=list(plan.domains),
            context_tokens=prepared.measures.approx_tokens, repaired=run.repaired,
            spent=gateway.budget.snapshot().minus(spent_before), locale=engine.locale, extra=extra,
        )


def _count(rows: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status.value] = counts.get(row.status.value, 0) + 1
    return counts
