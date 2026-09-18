"""The tool loop and the experimental architect workflow, driven by scripted models."""

from __future__ import annotations

from typing import Any

import pytest

from mirag.agent.architect import PHASES, ArchitectWorkflow
from mirag.agent.loop import AgentLoop, trim_history
from mirag.core.errors import BudgetExceededError
from mirag.evidence.claims import ClaimAuditor
from mirag.execution.runner import CodeRunner
from mirag.i18n.registry import I18n
from mirag.llm.budget import Budget
from mirag.llm.gateway import LLMGateway
from mirag.llm.messages import assistant_text, raw_tool_call, tool_call
from mirag.llm.scripted import ScriptedChatModel
from mirag.retrieval.engine import RetrievalEngine
from mirag.tools.builtin import build_default_tools


def gateway_for(script: list[dict[str, Any]], budget: Budget | None = None) -> LLMGateway:
    return LLMGateway(ScriptedChatModel(script), budget or Budget(), offline=True)


@pytest.fixture
def loop(engine_en: RetrievalEngine, runner: CodeRunner, i18n: I18n) -> AgentLoop:
    return AgentLoop(build_default_tools(engine_en.search, runner),
                     ClaimAuditor(i18n.lexicon("en"), i18n.catalog("en")))


def test_it_searches_and_answers(loop: AgentLoop) -> None:
    events: list[dict[str, Any]] = []
    result = loop.run("what is the outbox?", gateway_for([
        tool_call("search_docs", {"query": "outbox pattern"}),
        assistant_text("The outbox pattern solves the dual write."),
    ]), on_event=events.append)
    assert result.answer == "The outbox pattern solves the dual write."
    assert [e["type"] for e in events] == ["tool"]
    assert events[0]["name"] == "search_docs"


def test_an_unknown_tool_is_reported_back_to_the_model(loop: AgentLoop) -> None:
    gateway = gateway_for([tool_call("invented_tool", {"x": 1}), assistant_text("Fine.")])
    result = loop.run("x", gateway)
    assert result.steps[0].result.startswith("ERROR")
    assert "search_docs" in result.steps[0].result
    tool_message = gateway.model.received[1]["messages"][-1]  # type: ignore[attr-defined]
    assert tool_message["role"] == "tool"


def test_broken_json_arguments_become_a_retryable_error(loop: AgentLoop) -> None:
    result = loop.run("x", gateway_for([raw_tool_call("calculate", '{"expression": '), assistant_text("ok")]))
    assert "not valid JSON" in result.steps[0].result


def test_wrong_arguments_become_a_retryable_error(loop: AgentLoop) -> None:
    result = loop.run("x", gateway_for([tool_call("calculate", {"nope": 1}), assistant_text("ok")]))
    assert "wrong arguments" in result.steps[0].result


def test_thoughts_are_recorded(loop: AgentLoop) -> None:
    result = loop.run("x", gateway_for([tool_call("calculate", {"expression": "1+1"}, content="let me add"),
                                        assistant_text("2")]))
    assert result.steps[0].kind == "thought"
    assert result.steps[1].result == "2"


def test_it_stops_after_max_turns(loop: AgentLoop) -> None:
    script = [tool_call("calculate", {"expression": "1+1"})] * 3
    result = loop.run("x", gateway_for(script), max_turns=2)
    assert result.answer.endswith("I ran out of turns.")


def test_budget_exhaustion_climbs_to_the_caller(loop: AgentLoop) -> None:
    budget = Budget(0.01)
    budget.record(cost_usd=1.0)
    with pytest.raises(BudgetExceededError):
        loop.run("x", gateway_for([assistant_text("never")], budget))


def test_other_failures_cut_the_run_with_a_reason(loop: AgentLoop) -> None:
    gateway = LLMGateway(ScriptedChatModel([], fail_on_call=1, error=ConnectionError("down")), Budget(), True)
    assert loop.run("x", gateway).answer.startswith("The run was cut: ConnectionError")


@pytest.mark.slow
def test_a_final_claim_is_audited_against_what_really_ran(loop: AgentLoop) -> None:
    script = [tool_call("run_code", {"files": {"t.py": "print('hello')"}, "command": "python3 t.py"}),
              assistant_text("All the tests passed.")]
    result = loop.run("x", gateway_for(script))
    assert result.answer.startswith("> ⚠️")
    assert result.answer.endswith("All the tests passed.")


def test_old_tool_results_are_trimmed_but_the_recent_ones_travel_whole() -> None:
    messages = [{"role": "system", "content": "s"}] + [
        {"role": "tool", "content": "x" * 20_000} for _ in range(4)]
    trimmed = trim_history(messages)
    assert trimmed[1]["content"].startswith("[trimmed")
    assert trimmed[2]["content"].startswith("[trimmed")
    assert trimmed[3]["content"] == "x" * 20_000
    assert trim_history(messages[:2]) == messages[:2]


# ── architect ────────────────────────────────────────────────────────────────

def test_the_architect_runs_every_phase_in_order(loop: AgentLoop, i18n: I18n) -> None:
    workflow = ArchitectWorkflow(loop, i18n.catalog("es"))
    events: list[dict[str, Any]] = []
    script = [assistant_text(f"phase {i}") for i in range(len(PHASES))]
    result = workflow.design("a payments system", gateway_for(script), on_event=events.append)
    assert len(result.phases) == len(PHASES)
    assert result.final_answer == f"phase {len(PHASES) - 1}"
    phases = [e["text"] for e in events if e["type"] == "phase"]
    assert phases[0].startswith("1 · Entender")
    assert result.exhausted is None


def test_the_architect_stops_with_what_it_has_when_the_budget_runs_out(loop: AgentLoop, i18n: I18n) -> None:
    budget = Budget(0.01)
    budget.record(cost_usd=1.0)
    result = ArchitectWorkflow(loop, i18n.catalog("en")).design("x", gateway_for([], budget))
    assert result.exhausted and "Spending cap" in result.exhausted
    assert result.phases == []
