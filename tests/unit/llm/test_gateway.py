"""The gateway: the offline lock first, the budget second, then the call."""

from __future__ import annotations

import io
import json
from typing import Any

import pytest

from mirag.core.errors import BudgetExceededError, OfflineModeError
from mirag.core.settings import Settings
from mirag.llm.budget import Budget, BudgetSnapshot
from mirag.llm.gateway import LLMGateway, LLMGatewayFactory
from mirag.llm.messages import assistant_text, first_tool_arguments, raw_tool_call, tool_call
from mirag.llm.models import LLMResponse, OpenRouterChatModel, Usage
from mirag.llm.scripted import EXHAUSTED, ScriptedChatModel


class CountingModel:
    """A 'real' model that must never be reached while the lock is on."""

    name = "real"
    simulated = False

    def __init__(self, cost: float = 0.0) -> None:
        self.calls = 0
        self.cost = cost

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> LLMResponse:
        self.calls += 1
        return LLMResponse(assistant_text("ok"), Usage(10, 5, self.cost))


def test_the_lock_bites_before_anything_else() -> None:
    model = CountingModel()
    gateway = LLMGateway(model, Budget(0.0), offline=True)
    with pytest.raises(OfflineModeError):
        gateway.chat([{"role": "user", "content": "hi"}])
    assert model.calls == 0


def test_the_lock_comes_before_the_budget() -> None:
    budget = Budget(0.01)
    budget.record(cost_usd=1.0)  # already over the cap
    with pytest.raises(OfflineModeError):
        LLMGateway(CountingModel(), budget, offline=True).chat([])


def test_it_can_be_opened_on_purpose() -> None:
    model = CountingModel()
    assert LLMGateway(model, Budget(), offline=False).chat([])["content"] == "ok"
    assert model.calls == 1


def test_a_script_passes_the_lock_because_it_never_leaves_the_process() -> None:
    gateway = LLMGateway(ScriptedChatModel([assistant_text("scripted")]), Budget(), offline=True)
    assert gateway.simulated is True
    assert gateway.chat([])["content"] == "scripted"


def test_the_budget_cuts_before_spending_more() -> None:
    model = CountingModel(cost=0.30)
    gateway = LLMGateway(model, Budget(0.50), offline=False)
    gateway.chat([])
    gateway.chat([])  # 0.60 spent: over the cap only after this call
    with pytest.raises(BudgetExceededError):
        gateway.chat([])
    assert model.calls == 2


def test_zero_budget_means_accounting_only() -> None:
    gateway = LLMGateway(CountingModel(cost=100.0), Budget(0.0), offline=False)
    for _ in range(3):
        gateway.chat([])
    assert gateway.budget.calls == 3
    assert gateway.budget.cost_usd == 300.0


def test_the_budget_counts_tokens_and_snapshots_subtract() -> None:
    budget = Budget()
    before = budget.snapshot()
    budget.record(10, 5, 0.25)
    assert budget.snapshot().minus(before) == BudgetSnapshot(0.25, 1, 15)
    assert "no cap" in str(budget)


def test_the_script_answers_in_order_then_says_it_ran_out() -> None:
    model = ScriptedChatModel([assistant_text("one")])
    assert model.complete([], None).message["content"] == "one"
    assert model.complete([], None).message["content"] == EXHAUSTED
    assert model.calls == 2


def test_the_script_can_fail_on_a_given_call() -> None:
    model = ScriptedChatModel([assistant_text("a"), assistant_text("b")], fail_on_call=2, error=ValueError("x"))
    model.complete([], None)
    with pytest.raises(ValueError):
        model.complete([], None)


def test_the_factory_gives_each_request_its_own_budget() -> None:
    factory = LLMGatewayFactory(Settings.from_env({"MIRAG_BUDGET_USD": "0.2"}))
    first, second = factory.create(script=[]), factory.create(script=[])
    assert first.budget is not second.budget
    assert first.budget.limit_usd == 0.2
    assert factory.offline is True


class FakeResponse(io.BytesIO):
    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def test_openrouter_sends_tools_only_when_there_are_some_and_reads_the_cost() -> None:
    sent: list[dict[str, Any]] = []

    def opener(request: Any, timeout: float) -> FakeResponse:
        sent.append(json.loads(request.data))
        payload = {"choices": [{"message": {"role": "assistant", "content": "hi"}}],
                   "usage": {"prompt_tokens": 3, "completion_tokens": 2, "cost": 0.001}}
        return FakeResponse(json.dumps(payload).encode())

    model = OpenRouterChatModel("m", "key", opener=opener)
    response = model.complete([{"role": "user", "content": "x"}], [])
    model.complete([], [{"type": "function", "function": {"name": "t"}}])
    assert "tools" not in sent[0]
    assert "tools" in sent[1]
    assert sent[0]["usage"] == {"include": True}
    assert response.usage == Usage(3, 2, 0.001)


def test_openrouter_without_a_key_fails_loudly() -> None:
    with pytest.raises(RuntimeError):
        OpenRouterChatModel("m", "").complete([], None)


def test_first_tool_arguments_explains_why_it_found_nothing() -> None:
    reasons: list[str] = []
    assert first_tool_arguments(assistant_text("prose"), reasons) is None
    assert "did not call the tool" in reasons[0]
    reasons.clear()
    assert first_tool_arguments(raw_tool_call("t", '{"cut": '), reasons) is None
    assert "could not be read" in reasons[0]
    assert first_tool_arguments(tool_call("t", {"a": 1})) == {"a": 1}
