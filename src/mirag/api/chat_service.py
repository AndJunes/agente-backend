"""The chat use case: one question in, a stream of events out.

It picks the mode, applies the offline lock (scripted demos or "no model"), runs the
pipeline or the architect workflow, audits the final claim against what really ran, and
emits a closing ``done`` event with the panels the page draws.
"""

from __future__ import annotations

import threading

from collections.abc import Callable
from typing import Any

from mirag.agent.architect import ArchitectWorkflow
from mirag.api.schemas import ChatMode, ChatRequest
from mirag.core.errors import BudgetExceededError, RunStoppedError
from mirag.evidence.claims import ClaimAuditor
from mirag.execution.verdict import ExecutionResult
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.registry import I18n
from mirag.llm.gateway import LLMGateway, LLMGatewayFactory
from mirag.offline.demos import DemoCatalog
from mirag.pipeline.models import Step
from mirag.pipeline.orchestrator import QuestionPipeline
from mirag.presentation.answers import AnswerFormatter
from mirag.presentation.panels import (
    CostPresenter,
    EvidencePanelPresenter,
    StepSerializer,
    TimelinePresenter,
)
from mirag.self_knowledge.project_state import ProjectStateResponder

Emit = Callable[[dict[str, Any]], None]


class ChatService:
    MODES = (ChatMode.PIPELINE, ChatMode.ARCHITECT)

    def __init__(
        self,
        i18n: I18n,
        gateways: LLMGatewayFactory,
        pipeline: QuestionPipeline,
        state: Callable[[str], ProjectStateResponder],
        demos: Callable[[str], DemoCatalog],
        architect: Callable[[str], ArchitectWorkflow],
    ) -> None:
        self._i18n = i18n
        self._gateways = gateways
        self._pipeline = pipeline
        self._state = state
        self._demos = demos
        self._architect = architect

    def handle(self, request: ChatRequest, emit: Emit, accept_language: str | None = None,
               cancelled: threading.Event | None = None) -> None:
        """One request, start to finish.

        ``cancelled`` rides inside the gateway's `Deadline` rather than being threaded through
        the pipeline: the gateway is the single object every model call already passes
        through, so one parameter here reaches all of them and no stage has to learn a new
        word."""
        locale = self._i18n.resolve(request.locale, accept_language)
        t = self._i18n.catalog(locale)
        executions: list[ExecutionResult] = []

        def forward(event: dict[str, Any]) -> None:
            # the real executions are kept to audit the final claim
            if event.get("type") == "tool" and str(event.get("name", "")).startswith("run_code"):
                executions.append(ExecutionResult.parse(str(event.get("result", ""))))
            if event.get("type") == "step" and str(event.get("name", "")).startswith("verification"):
                executions.append(ExecutionResult.parse(str(event.get("detail") or "")))
            emit(event)

        # shortcut: if it asks about Mirag itself, the answer is a fact, not a search
        if direct := self._state(locale).answer(request.question):
            forward({"type": "phase", "text": t("chat.shortcut")})
            forward({"type": "done", "answer": direct, "mode": "state", "locale": locale,
                     "cost_summary": t("chat.shortcut_cost")})
            return

        panels: dict[str, Any] = {"evidence": None, "timeline": None, "cost": None, "project": None,
                                  "deliverable": None}
        gateway: LLMGateway | None = None
        try:
            if request.mode == ChatMode.PIPELINE:
                gateway, answer = self._pipeline_mode(request.question, locale, t, forward,
                                                      panels, cancelled)
            elif request.mode == ChatMode.ARCHITECT:
                gateway = self._gateways.create(cancelled=cancelled)
                result = self._architect(locale).design(request.question, gateway, on_event=forward)
                answer = result.final_answer or t("chat.no_phases")
                if result.exhausted:
                    answer = f"⛔ {result.exhausted}\n\n{answer}"
            else:
                # 'simple' and 'fast' were retired: two more production paths, each with its own
                # context and evidence. The loop lives on as the engine of the architect mode.
                answer = t("chat.unknown_mode", mode=request.mode, modes=", ".join(m.value for m in self.MODES))
        except BudgetExceededError as exc:
            answer = f"⛔ {exc}"
        except RunStoppedError as exc:
            # The clock running out and the person leaving are the same SHAPE of event as a
            # spent budget — stop, keep what exists, say so — and not the same sentence.
            answer = f"⏱ {exc}"
        except Exception as exc:  # what was emitted so far is already in the browser
            answer = f"Error: {type(exc).__name__}: {exc}"

        # neither the pipeline nor the architect prose passes through the loop's audit here
        answer, claim_status = ClaimAuditor(self._i18n.lexicon(locale), t).apply(answer, executions)
        forward({"type": "done", "answer": answer, "mode": request.mode, "locale": locale,
                 "cost_summary": str(gateway.budget) if gateway else "",
                 "claim_status": claim_status.value, **panels})

    def _pipeline_mode(self, question: str, locale: str, t: MessageCatalog, emit: Emit,
                       panels: dict[str, Any],
                       cancelled: threading.Event | None = None) -> tuple[LLMGateway, str]:
        demo: str | None = None
        if self._gateways.offline:
            # With the lock on the machine can still be seen working: the only thing replaced
            # is the model's DECISION, and the answer says so.
            demos = self._demos(locale)
            demo, script = demos.script_for(question)
            emit({"type": "step", "name": "offline_lock", "status": "simulated" if demo else "no_model",
                  "ms": 0.0, "source": "execution",
                  "summary": t("chat.offline.demo", demo=demo) if demo else t("chat.offline.no_demo"),
                  "detail": {"demo": demo, "offline": True, "available_demos": demos.available_scripts()}})
            gateway = self._gateways.create(script=script, cancelled=cancelled)
        else:
            gateway = self._gateways.create(cancelled=cancelled)

        run = self._pipeline.run(question, gateway, locale, on_step=lambda step: emit(StepSerializer.to_event(step)))
        answer = AnswerFormatter(t).pipeline_answer(run, demo)
        if run.artifact is not None:
            # The project wins over the deliverable: two different things, the page draws one.
            panels["project"] = run.artifact.for_page()
        panels["evidence"] = EvidencePanelPresenter().present(run, t)
        panels["timeline"] = TimelinePresenter().present(run)
        panels["cost"] = CostPresenter().present(run, gateway.budget.snapshot(), t, demo, gateway.model_name)
        if run.delivery:
            panels["deliverable"] = {
                "files": run.delivery.get("files", {}),
                "command": run.delivery.get("test_command"),
                "folder": run.output_folder,
                "status": run.execution.status.value if run.execution else "not_executed",
                "simulated": sorted({s for row in run.evidence for s in row.substituted}),
            }
        return gateway, answer

    @staticmethod
    def step_event(step: Step) -> dict[str, Any]:
        return StepSerializer.to_event(step)
