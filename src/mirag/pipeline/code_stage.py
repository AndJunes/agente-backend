"""Stages 10-11 for a single deliverable: the model, then verification by EXECUTION."""

from __future__ import annotations

from pathlib import Path

from mirag.core.errors import OfflineModeError
from mirag.core.timing import Stopwatch
from mirag.evidence.obligations import ObligationChecker, ObligationStatus
from mirag.evidence.properties import EvidenceBuilder, SimulationDetector
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.syntax import SyntaxChecker
from mirag.execution.verdict import ExecutionStatus
from mirag.llm.gateway import LLMGateway
from mirag.pipeline.delivery import DeliveryReader, OutputWriter
from mirag.pipeline.knowledge_stage import PreparedRequest
from mirag.pipeline.models import PipelineRun, Source, Step, StepListener, StepStatus
from mirag.pipeline.prompts import REPAIR_SYSTEM_PROMPT, SYSTEM_PROMPT, deliver_tool
from mirag.retrieval.engine import RetrievalEngine

MAX_REPAIRS = 1


class CodeDeliveryStage:
    def __init__(self, syntax: SyntaxChecker, interpreters: InterpreterRegistry, writer: OutputWriter,
                 evidence: EvidenceBuilder | None = None, simulation: SimulationDetector | None = None) -> None:
        self._syntax = syntax
        self._interpreters = interpreters
        self._writer = writer
        self._evidence = evidence or EvidenceBuilder()
        self._simulation = simulation or SimulationDetector()
        self._reader = DeliveryReader()

    def run(self, run: PipelineRun, prepared: PreparedRequest, engine: RetrievalEngine, gateway: LLMGateway,
            note: StepListener, persist: bool = True, output_folder: Path | None = None) -> None:
        t = engine.catalog
        plan = prepared.plan
        tool = deliver_tool(self._interpreters.describe())
        system = f"{SYSTEM_PROMPT}\n\n{t('llm.language_directive')}"

        # ── 10. the model ────────────────────────────────────────────────────
        clock = Stopwatch()
        try:
            message = gateway.chat([{"role": "system", "content": system},
                                    {"role": "user", "content": prepared.context}],
                                   tools=[tool] if plan.needs_code else [])
        except OfflineModeError as exc:
            note(Step("model", StepStatus.ERROR, t("pipeline.model.offline"), clock.ms, Source.EXECUTION))
            run.answer = t("pipeline.model.no_model_answer", error=str(exc))
            return
        note(Step("model", StepStatus.EXECUTED,
                  t("pipeline.model.asked_code") if message.get("tool_calls") else t("pipeline.model.answered_text"),
                  clock.ms, Source.MODEL))

        # ── 11. if there is code: run it and verify ─────────────────────────
        if message.get("tool_calls"):
            self._verify(run, prepared, engine, gateway, message, tool, note, persist, output_folder)

        # The warning is silenced ONLY if the execution proved something: then correctness
        # does not depend on the corpus. Looking like a code task is not enough.
        proved = run.execution is not None and run.execution.is_green
        answer = message.get("content") or ""
        if not prepared.verdict.sufficient and not proved:
            answer = f"{prepared.verdict.warning}\n\n{answer}"
        run.answer = answer

    def _verify(self, run: PipelineRun, prepared: PreparedRequest, engine: RetrievalEngine, gateway: LLMGateway,
                message: dict, tool: dict, note: StepListener, persist: bool, output_folder: Path | None) -> None:
        t = engine.catalog
        clock = Stopwatch()
        delivery, error = self._reader.read(message)
        if error or delivery is None:
            note(Step("delivery", StepStatus.ERROR, t(f"pipeline.delivery.{error}"), clock.ms, Source.MODEL))
            return
        note(Step("delivery", StepStatus.EXECUTED,
                  t("pipeline.delivery.summary", count=len(delivery["files"]),
                    command=delivery.get("test_command", "?")),
                  clock.ms, Source.MODEL, list(delivery["files"])))

        clock.restart()
        result = self._syntax.check_then_run(delivery["files"], delivery.get("test_command", ""))
        # Execution switched off: the step did not fail, it did not run. Calling that an error
        # is the same lie as calling red what nobody looked at.
        skipped = result.status is ExecutionStatus.NOT_EXECUTED and not self._syntax.executes
        note(Step("verification",
                  StepStatus.EXECUTED if result.is_green else StepStatus.SKIPPED if skipped else StepStatus.ERROR,
                  result.describe(t), clock.ms, Source.EXECUTION, result.text[:2000]))

        # Nothing ran, so there is nothing to repair. Without this guard every run with
        # execution off paid for a blind repair of a failure nobody had seen.
        if not result.is_green and not skipped and MAX_REPAIRS:
            clock.restart()
            try:
                fix = gateway.chat(
                    [{"role": "system", "content": REPAIR_SYSTEM_PROMPT},
                     {"role": "user", "content": f"{prepared.context}\n\nREAL OUTPUT:\n{result.text[:2000]}"}],
                    tools=[tool])
                new_delivery, fix_error = self._reader.read(fix)
                if not fix_error and new_delivery is not None:
                    delivery = {**delivery, **new_delivery}  # a fix may omit fields: merge
                    run.repaired = True
                    result = self._syntax.check_then_run(delivery["files"], delivery.get("test_command", ""))
                    note(Step("verification_after_repair",
                              StepStatus.EXECUTED if result.is_green else StepStatus.ERROR,
                              result.describe(t), clock.ms, Source.EXECUTION, result.text[:2000]))
            except Exception as exc:  # the repair never kills the run (offline, budget, network...)
                note(Step("repair", StepStatus.ERROR, f"{type(exc).__name__}: {exc}", clock.ms, Source.MODEL))

        run.delivery = delivery
        run.execution = result

        clock.restart()
        substituted = self._simulation.detect(run.question, delivery.get("files"))
        run.evidence = self._evidence.build(delivery.get("properties"), result, executed=not skipped,
                                            substituted=substituted)
        counts = EvidenceBuilder.count(run.evidence)
        note(Step("evidence", StepStatus.EXECUTED,
                  " · ".join(f"{n} {t(f'evidence.status.{k}')}" for k, n in counts.items()) or t("pipeline.evidence.none"),
                  clock.ms, Source.EXECUTION, [row.as_dict() for row in run.evidence]))

        # The corpus brought anti-patterns "that MUST be covered" and nobody checked whether
        # the delivery covered them. They are crossed with the REAL evidence.
        clock.restart()
        checker = ObligationChecker(engine.lexicon)
        run.anti_pattern_coverage = checker.coverage(checker.from_retrieval(prepared.retrieval), run.evidence)
        counts = ObligationChecker.count(run.anti_pattern_coverage)
        note(Step("anti_patterns",
                  StepStatus.WARNING if counts.get(ObligationStatus.NOT_COVERED.value) else StepStatus.EXECUTED,
                  " · ".join(f"{n} {t(f'obligation.status.{k}')}" for k, n in counts.items())
                  or t("pipeline.anti_patterns.none"),
                  clock.ms, Source.EXECUTION, [row.as_dict() for row in run.anti_pattern_coverage]))

        if persist:
            # Persisting can NOT kill the run. When it raised, the exception climbed up to the
            # server and the whole answer was discarded - after paying and verifying.
            clock.restart()
            try:
                folder = self._writer.save(delivery, output_folder)
                run.output_folder = str(folder.resolve())
                note(Step("persistence", StepStatus.EXECUTED, t("pipeline.persistence.saved", folder=folder),
                          clock.ms, Source.EXECUTION))
            except Exception as exc:
                note(Step("persistence", StepStatus.ERROR,
                          t("pipeline.persistence.failed", error=f"{type(exc).__name__}: {exc}"),
                          clock.ms, Source.EXECUTION))
