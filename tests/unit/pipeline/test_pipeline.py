"""The production pipeline, end to end, with scripted model decisions (zero cost)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mirag.container import Container, build_container
from mirag.execution.verdict import ExecutionStatus
from mirag.llm.messages import assistant_text
from mirag.offline.scripts import ScriptLibrary
from mirag.pipeline.models import PipelineRun, Source, StepStatus
from mirag.retrieval.plan import EMPTY_PLAN
from tests.conftest import offline_settings

QUESTIONS = {
    "concept": {"en": "What is a PostgreSQL index and when does it stop helping?",
                "es": "¿Qué es un índice de PostgreSQL y cuándo deja de servir?"},
    "code": {"en": "Create calculator.py with a function calculate(a, b, operation) and its tests",
             "es": "Crea calculator.py con una función calculate(a, b, operation) y sus tests"},
    "raft": {"en": "How do I implement Raft consensus with linearizability guarantees?",
             "es": "¿Cómo implemento consenso Raft con garantías de linealizabilidad?"},
}


def run(container: Container, kind: str, locale: str, script: list | None = None, **kwargs) -> PipelineRun:
    gateway = container.gateways.create(script=script if script is not None else [])
    return container.pipeline.run(QUESTIONS[kind][locale], gateway, locale, **kwargs)


def scripts(container: Container, locale: str) -> ScriptLibrary:
    return ScriptLibrary(container.i18n.catalog(locale))


@pytest.mark.parametrize("locale", ["en", "es"])
def test_a_conceptual_question_retrieves_and_answers_in_its_language(container: Container, locale: str) -> None:
    result = run(container, "concept", locale, scripts(container, locale).conceptual(), persist=False)
    assert result.ran("retrieval")
    assert result.delivery is None
    assert "PostgreSQL" in result.answer
    assert result.step("retrieval").detail["ids"]  # provenance travels with the step
    assert result.simulated is True


@pytest.mark.slow
@pytest.mark.parametrize("locale", ["en", "es"])
def test_code_is_generated_executed_and_verified(container: Container, locale: str) -> None:
    result = run(container, "code", locale, scripts(container, locale).calculator())
    assert result.execution is not None and result.execution.status is ExecutionStatus.PASSED
    assert {row.status.value for row in result.evidence} == {"verified"}
    assert result.ran("verification") and result.ran("evidence") and result.ran("persistence")
    assert Path(result.output_folder or "").is_dir()
    assert result.repaired is False


@pytest.mark.slow
def test_the_repair_loop_fixes_once_and_says_so(container: Container) -> None:
    result = run(container, "code", "en", scripts(container, "en").broken_then_fixed(), persist=False)
    assert result.step("verification").status is StepStatus.ERROR
    assert result.step("verification_after_repair").status is StepStatus.EXECUTED
    assert result.repaired is True
    assert result.execution is not None and result.execution.is_green


@pytest.mark.slow
def test_a_broken_delivery_is_an_error_step_not_a_crash(container: Container) -> None:
    result = run(container, "code", "en", scripts(container, "en").broken_json()[:1], persist=False)
    assert result.step("delivery").status is StepStatus.ERROR
    assert result.execution is None


def test_without_a_script_the_lock_says_there_is_no_model(tmp_path: Path) -> None:
    container = build_container(offline_settings(tmp_path))
    gateway = container.gateways.create()  # the real model, behind the lock
    result = container.pipeline.run(QUESTIONS["concept"]["en"], gateway, "en", persist=False)
    assert result.step("model").status is StepStatus.ERROR
    assert result.answer.startswith("[no model]")


@pytest.mark.parametrize("locale", ["en", "es"])
def test_an_uncovered_topic_is_said_before_answering(container: Container, locale: str) -> None:
    result = run(container, "raft", locale, [assistant_text("Raft is...")], persist=False)
    assert result.verdict is not None and not result.verdict.sufficient
    assert result.verdict.grade.value in ("mentioned", "absent")
    assert result.answer.startswith(result.verdict.warning)
    assert result.answer.endswith("Raft is...")


def test_every_step_declares_where_its_claim_comes_from(container: Container) -> None:
    result = run(container, "concept", "en", scripts(container, "en").conceptual(), persist=False)
    assert result.steps
    assert all(step.source in set(Source) for step in result.steps)


def test_internal_retrieval_stages_are_named_per_index(container: Container) -> None:
    names = [s.name for s in run(container, "concept", "en", [assistant_text("x")], persist=False).steps]
    for index in ("knowledge", "anti_patterns", "failures"):
        assert f"bm25:{index}" in names and f"reranker:{index}" in names


def test_a_forced_empty_plan_is_labelled_as_such(container: Container) -> None:
    result = run(container, "concept", "en", [assistant_text("x")], persist=False, forced_plan=EMPTY_PLAN)
    assert result.plan is EMPTY_PLAN
    assert result.step("retrieval_plan").detail["origin"].startswith("no plan")


def test_questions_about_mirag_are_answered_without_searching(container: Container) -> None:
    gateway = container.gateways.create(script=[])
    result = container.pipeline.run("which model do you use?", gateway, "en", persist=False)
    assert result.steps[0].name == "project_state"
    assert result.steps[0].status is StepStatus.EXECUTED
    assert len(result.steps) == 1
    assert gateway.budget.calls == 0


@pytest.mark.slow
def test_a_paid_call_is_always_traced_and_a_free_one_only_when_persisting(container: Container) -> None:
    trace_file = container.traces.path
    run(container, "concept", "en", [assistant_text("x")], persist=False)
    assert not trace_file.exists()  # a double that persists nothing leaves no trace
    result = run(container, "code", "en", scripts(container, "en").calculator(), persist=True)
    rows = [json.loads(line) for line in trace_file.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row == result.trace
    assert row["simulated_decision"] is True
    assert row["locale"] == "en"
    assert row["final_status"] == "passed"
    assert row["properties"]["verified"] == 3
    assert row["retrieval"]["ids"] and row["context"]["sha"]
    assert row["model_route"] is None  # there is no router: null, not invented
    assert row["tools"] == [{"tool": "run_code", "status": "passed"}]


@pytest.mark.slow
def test_a_persistence_failure_never_erases_the_answer(container: Container, tmp_path: Path) -> None:
    blocker = tmp_path / "not_a_folder"
    blocker.write_text("x", encoding="utf-8")
    gateway = container.gateways.create(script=scripts(container, "en").calculator())
    result = container.pipeline.run(QUESTIONS["code"]["en"], gateway, "en", output_folder=blocker / "sub")
    assert result.step("persistence").status is StepStatus.ERROR
    assert result.execution is not None and result.execution.is_green
    assert result.evidence
