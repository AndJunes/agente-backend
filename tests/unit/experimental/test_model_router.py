"""The model router: classification, fallback, the feature gate and honesty about cost."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mirag.core.errors import BudgetExceededError, OfflineModeError
from mirag.experimental.model_router import (
    DEFAULT_TABLE,
    AllModelsFailedError,
    AttemptOutcome,
    CostEstimate,
    ModelRoute,
    ModelRouter,
    TaskClass,
    TaskClassifier,
    TokenRate,
    call_with_fallback,
)
from mirag.features.flags import FeatureGate, GainsRepository
from mirag.llm.budget import Budget
from mirag.llm.gateway import LLMGateway
from mirag.llm.messages import assistant_text
from mirag.llm.models import OpenRouterChatModel
from mirag.llm.scripted import ScriptedChatModel
from mirag.retrieval.engine import RetrievalEngine
from mirag.retrieval.plan import Depth, RetrievalPlan

DEFAULT_MODEL = "anthropic/claude-haiku-4.5"
EXAMPLES = {
    "en": {
        TaskClass.SIMPLE: "What is a PostgreSQL index?",
        TaskClass.NORMAL: "Create a calculator.py file with its tests",
        TaskClass.COMPLEX: "how do I avoid a race condition when booking a seat",
        TaskClass.ARCHITECTURAL: "design the architecture of a payment system that scales",
    },
    "es": {
        TaskClass.SIMPLE: "¿Que es un indice de PostgreSQL?",
        TaskClass.NORMAL: "Crea un archivo calculator.py con sus tests",
        TaskClass.COMPLEX: "como evito un race condition al reservar una plaza",
        TaskClass.ARCHITECTURAL: "diseña la arquitectura de un sistema de pagos que escale",
    },
}
SHORT_DEFINITION = {"en": "What is an index?", "es": "¿Que es un indice?"}
MESSAGES = [{"role": "user", "content": "x"}]


@pytest.fixture
def classifier(engine: RetrievalEngine) -> TaskClassifier:
    return TaskClassifier(engine.lexicon)


def gate(tmp_path: Path, env: dict[str, str] | None = None, gains: dict[str, Any] | None = None) -> FeatureGate:
    """A gate isolated from the real gains file of the package."""
    path = tmp_path / "feature_gains.json"
    if gains is not None:
        path.write_text(json.dumps(gains), encoding="utf-8")
    return FeatureGate(env or {}, GainsRepository(path))


def scripted_gateway(*answers: dict[str, Any], error: Exception | None = None) -> LLMGateway:
    model = ScriptedChatModel(list(answers), fail_on_call=1 if error else None, error=error)
    return LLMGateway(model, offline=True)  # a script never leaves the process: the lock lets it through


# ── classification ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("expected", list(TaskClass))
def test_classifies_each_task_class(engine: RetrievalEngine, classifier: TaskClassifier, expected: TaskClass) -> None:
    result = classifier.classify(EXAMPLES[engine.locale][expected])
    assert result.task_class is expected, result


def test_the_plan_raises_the_class(engine: RetrievalEngine, classifier: TaskClassifier) -> None:
    """A short question that crosses four areas is not simple any more."""
    question = SHORT_DEFINITION[engine.locale]
    narrow = classifier.classify(question, RetrievalPlan(domains=("04",)))
    wide = classifier.classify(question, RetrievalPlan(domains=("04", "08", "09", "10")))
    assert narrow.task_class is TaskClass.SIMPLE
    assert wide.task_class is TaskClass.COMPLEX, wide.reason
    assert "4" in wide.reason


def test_code_or_depth_in_the_plan_lift_a_simple_question(engine: RetrievalEngine, classifier: TaskClassifier) -> None:
    question = SHORT_DEFINITION[engine.locale]
    assert classifier.classify(question, RetrievalPlan(needs_code=True)).task_class is TaskClass.NORMAL
    assert classifier.classify(question, RetrievalPlan(depth=Depth.DEEP.value)).task_class is TaskClass.NORMAL


def test_a_long_definition_is_not_simple(engine: RetrievalEngine, classifier: TaskClassifier) -> None:
    question = SHORT_DEFINITION[engine.locale] + " " + "x " * 60
    assert classifier.classify(question).task_class is TaskClass.NORMAL


@pytest.mark.parametrize("text", ["", "x", "what is this", "qué es esto", "design something", "race condition", None])
def test_there_is_always_a_reason(classifier: TaskClassifier, text: str | None) -> None:
    result = classifier.classify(text)
    assert result.task_class in TaskClass
    assert result.reason, f"{text!r} without a reason"


# ── the router and the feature gate ──────────────────────────────────────────


def test_off_by_default_returns_the_usual_model(tmp_path: Path, classifier: TaskClassifier) -> None:
    route = ModelRouter(classifier, gate(tmp_path), "some/default-model").choose("anything")
    assert route.model == "some/default-model"
    assert not route.routed and route.task_class is None
    assert "router off" in route.reason
    assert route.gate is not None and route.gate.code == "experimental"


def test_a_good_measurement_does_not_switch_it_on(tmp_path: Path, classifier: TaskClassifier) -> None:
    """Experimental: it never switches itself on, not even with a measured gain."""
    measured = {"model_routing": {"general": {"delta_mrr": 0.5, "normalized_cost": 0.0}}}
    route = ModelRouter(classifier, gate(tmp_path, gains=measured), DEFAULT_MODEL).choose("design it")
    assert not route.routed


def test_forced_on_by_hand_it_routes(engine: RetrievalEngine, tmp_path: Path, classifier: TaskClassifier) -> None:
    router = ModelRouter(classifier, gate(tmp_path, {"MIRAG_MODEL_ROUTING": "on"}), DEFAULT_MODEL)
    route = router.choose(EXAMPLES[engine.locale][TaskClass.ARCHITECTURAL])
    assert route.routed and route.task_class is TaskClass.ARCHITECTURAL
    assert route.max_tokens == 16_000
    assert route.gate is not None and route.gate.code == "experimental_forced_on"
    simple = router.choose(EXAMPLES[engine.locale][TaskClass.SIMPLE])
    assert simple.task_class is TaskClass.SIMPLE and simple.max_tokens == 4_000


def test_forced_off_stays_off(tmp_path: Path, classifier: TaskClassifier) -> None:
    route = ModelRouter(classifier, gate(tmp_path, {"MIRAG_MODEL_ROUTING": "off"}), DEFAULT_MODEL).choose("x")
    assert not route.routed and route.gate is not None and route.gate.code == "forced_off"


def test_the_fallback_is_unreachable_with_the_default_table(tmp_path: Path, classifier: TaskClassifier) -> None:
    """Every class maps to the same model, so the fallbacks come out empty. Written down on purpose:
    if this fails, somebody added a second model - update the NOTE in the module."""
    router = ModelRouter(classifier, gate(tmp_path, {"MIRAG_MODEL_ROUTING": "on"}), DEFAULT_MODEL)
    assert router.choose("design the architecture").fallbacks == ()
    assert set(DEFAULT_TABLE.models.values()) == set(DEFAULT_TABLE.fallbacks)


# ── calling with fallback ────────────────────────────────────────────────────


def test_the_fallback_steps_in_when_the_primary_fails() -> None:
    gateways = {
        "model/primary": scripted_gateway(error=RuntimeError("503 from the provider")),
        "model/backup": scripted_gateway(assistant_text("ok")),
    }
    requested: list[str] = []

    def gateway_for(model: str) -> LLMGateway:
        requested.append(model)
        return gateways[model]

    route = ModelRoute("model/primary", TaskClass.NORMAL, "test", ("model/backup",))
    result = call_with_fallback(MESSAGES, route, None, gateway_for)
    assert result.message["content"] == "ok"
    assert result.model == "model/backup"
    assert [a.outcome for a in result.attempts] == [AttemptOutcome.FAILED, AttemptOutcome.OK]
    assert "503" in result.attempts[0].error
    assert requested == ["model/primary", "model/backup"], "each attempt gets its own gateway"


def test_when_every_model_fails_it_says_so() -> None:
    route = ModelRoute("a", TaskClass.NORMAL, "x", ("b",))
    with pytest.raises(AllModelsFailedError) as caught:
        call_with_fallback([], route, None, lambda _model: scripted_gateway(error=RuntimeError("down")))
    assert "every model failed" in str(caught.value)
    assert [a.model for a in caught.value.attempts] == ["a", "b"]
    assert all(a.outcome is AttemptOutcome.FAILED for a in caught.value.attempts)


def test_the_route_repeats_no_candidate() -> None:
    route = ModelRoute("a", TaskClass.NORMAL, "x", ("a", "b", "b"))
    assert route.candidates == ("a", "b")


def test_the_offline_lock_is_not_retried() -> None:
    """If the offline lock fires, the next model must not be tried: it is not a failure."""
    requested: list[str] = []

    def real_but_locked(model: str) -> LLMGateway:
        requested.append(model)
        return LLMGateway(OpenRouterChatModel(model, api_key=""), offline=True)

    with pytest.raises(OfflineModeError):
        call_with_fallback(MESSAGES, ModelRoute("a", TaskClass.NORMAL, "x", ("b",)), None, real_but_locked)
    assert requested == ["a"]


def test_the_budget_cap_is_not_dodged_by_the_next_model() -> None:
    spent = Budget(0.01)
    spent.record(cost_usd=0.02)
    requested: list[str] = []

    def capped(model: str) -> LLMGateway:
        requested.append(model)
        return LLMGateway(ScriptedChatModel([assistant_text("ok")]), spent, offline=True)

    with pytest.raises(BudgetExceededError):
        call_with_fallback(MESSAGES, ModelRoute("a", TaskClass.NORMAL, "x", ("b",)), None, capped)
    assert requested == ["a"]


def test_tools_reach_the_model() -> None:
    model = ScriptedChatModel([assistant_text("ok")])
    tools = [{"type": "function", "function": {"name": "t", "description": "d", "parameters": {}}}]
    call_with_fallback(MESSAGES, ModelRoute("a", None, "x"), tools, lambda _m: LLMGateway(model, offline=True))
    assert model.received[0]["tools"] == tools


# ── cost ─────────────────────────────────────────────────────────────────────


def test_the_cost_is_labelled_as_an_estimate(tmp_path: Path, classifier: TaskClassifier) -> None:
    route = ModelRouter(classifier, gate(tmp_path), DEFAULT_MODEL).choose("anything")
    estimate = route.estimated_cost()
    assert isinstance(estimate, CostEstimate) and estimate.kind == "estimate"
    assert estimate.usd == pytest.approx(8_000 / 1e6 * 1.0 + 2_000 / 1e6 * 5.0)
    assert "ESTIMATE" in (ModelRoute.estimated_cost.__doc__ or "")
    assert "ESTIMATE" in (TokenRate.__doc__ or "")


def test_without_a_known_rate_no_number_is_invented() -> None:
    assert ModelRoute("model/without/rate", TaskClass.NORMAL, "x").estimated_cost() is None
