"""Presenters only read what the pipeline recorded; they decide nothing."""

from __future__ import annotations

import pytest

from mirag.container import Container
from mirag.evidence.properties import EvidenceRow, PropertyStatus
from mirag.execution.verdict import ExecutionResult
from mirag.i18n.registry import I18n
from mirag.llm.budget import BudgetSnapshot
from mirag.offline.scripts import ScriptLibrary
from mirag.pipeline.models import PipelineRun, Source, Step, StepStatus
from mirag.presentation.answers import AnswerFormatter
from mirag.presentation.panels import (
    CostPresenter,
    EvidencePanelPresenter,
    StepSerializer,
    TimelinePresenter,
)


def _run(**kwargs) -> PipelineRun:
    return PipelineRun(question="q", locale="en", **kwargs)


ROWS = [EvidenceRow("r1", "p1", "a", PropertyStatus.VERIFIED),
        EvidenceRow("r2", "p2", "b", PropertyStatus.VERIFIED_IN_SIMULATION),
        EvidenceRow("r3", "p3", "c", PropertyStatus.UNVERIFIED),
        EvidenceRow("r4", "p4", "d", PropertyStatus.REFUTED)]


def test_the_evidence_panel_separates_claim_from_verified(i18n: I18n) -> None:
    run = _run(evidence=ROWS, execution=ExecutionResult.from_run("TEST:a:PASS\nTEST:d:FAIL", 0),
               delivery={"uncovered": ["precision"]})
    panel = EvidencePanelPresenter().present(run, i18n.catalog("en"))
    assert len(panel["claim"]) == 4
    assert [r["test_id"] for r in panel["verified"]] == ["a"]
    assert [r["test_id"] for r in panel["simulated"]] == ["b"]
    assert [r["test_id"] for r in panel["not_verified"]] == ["c", "d"]
    assert panel["observed"]["status"] == "failed"
    assert panel["uncovered"] == ["precision"]
    verified_ids = {r["test_id"] for r in panel["verified"]}
    assert verified_ids <= {r["test_id"] for r in panel["claim"]}


def test_without_execution_nothing_is_observed(i18n: I18n) -> None:
    assert EvidencePanelPresenter().present(_run(), i18n.catalog("en"))["observed"] is None
    delivered = EvidencePanelPresenter().present(_run(delivery={"files": {"a": "b"}}), i18n.catalog("es"))
    assert delivered["observed"]["status"] == "not_executed"


def test_the_timeline_folds_retrieval_without_losing_time() -> None:
    steps = [Step("retrieval_plan", StepStatus.EXECUTED, "", 1.0, Source.EXECUTION),
             Step("bm25:knowledge", StepStatus.EXECUTED, "", 10.0, Source.CORPUS),
             Step("rrf:failures", StepStatus.EXECUTED, "", 5.0, Source.CORPUS),
             Step("retrieval", StepStatus.EXECUTED, "", 2.0, Source.CORPUS)]
    rows = TimelinePresenter().present(_run(steps=steps))
    assert [r["stage"] for r in rows] == ["retrieval_plan", "retrieval"]
    assert rows[-1]["ms"] == 17.0
    assert sum(r["ms"] for r in rows) == sum(s.ms for s in steps)


def test_a_double_does_not_cost_zero_point_zero_zero_zero_zero(i18n: I18n) -> None:
    catalog = i18n.catalog("en")
    assert CostPresenter().present(_run(simulated=True), BudgetSnapshot(), catalog, "code")["text"] == "SIMULATED · $0"
    assert CostPresenter().present(_run(simulated=True), BudgetSnapshot(), catalog)["text"] == "NO MODEL · $0"
    real = CostPresenter().present(_run(simulated=False), BudgetSnapshot(0.0123, 2, 99), catalog)
    assert real == {"simulated": False, "text": "$0.0123", "calls": 2, "tokens": 99}


def test_step_events_are_json_safe() -> None:
    event = StepSerializer.to_event(Step("x", StepStatus.FALLBACK, "s", 1.234, None, {"a": object()}))
    assert event["type"] == "step" and event["status"] == "fallback" and event["source"] == ""
    assert isinstance(event["detail"], str)
    assert StepSerializer.to_event(Step("y", StepStatus.EXECUTED, "s", 0, Source.MODEL, [("a", 1)]))["detail"] == [["a", 1]]


@pytest.mark.slow
@pytest.mark.parametrize("locale", ["en", "es"])
def test_a_code_answer_explains_what_was_done_and_never_says_correct(container: Container, locale: str) -> None:
    catalog = container.i18n.catalog(locale)
    gateway = container.gateways.create(script=ScriptLibrary(catalog).calculator())
    run = container.pipeline.run("Create calculator.py with calculate(a, b, operation)", gateway, locale,
                                 persist=False)
    markdown = AnswerFormatter(catalog).pipeline_answer(run, "code")
    assert markdown.startswith(f"## {catalog.t('answer.what_was_done')}")
    assert catalog.t("answer.evidence.title") in markdown
    assert "SIMUL" in markdown  # the simulated demo is labelled as such
    assert ("not *it is correct*" in markdown) if locale == "en" else ("no *es correcto*" in markdown)


def test_no_model_is_not_presented_as_a_demo(i18n: I18n) -> None:
    catalog = i18n.catalog("en")
    assert "NO MODEL" in AnswerFormatter(catalog).pipeline_answer(_run(simulated=True, answer="x"))
    assert "SIMULATED" in AnswerFormatter(catalog).pipeline_answer(_run(simulated=True, answer="x"), "code")
