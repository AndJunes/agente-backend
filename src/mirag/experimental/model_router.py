"""Choosing a model by what the task asks for. EXPERIMENTAL: today, only the hook.

WHY THIS IS A SKELETON AND NOT A POLICY
    A model router cannot know which model is better until there is real data on cost,
    latency and verified success per model. There is none yet: everything runs with doubles.
    So the piece is built - deterministic classifier, fallback chain, a record of why each
    model was chosen - and left OFF: ``model_routing`` is an EXPERIMENTAL switch of the
    :class:`~mirag.features.flags.FeatureGate`, so it only runs when forced by hand
    (``MIRAG_MODEL_ROUTING=on``) and never switches itself on from a measurement.

    When there are real traces (several tasks, several models), :data:`DEFAULT_TABLE` is
    replaced by what was measured. Until then it is a declared preference, not a conclusion.

THE COST IS NOT INVENTED
    The project has no price table and the real cost is only known AFTER the answer
    (OpenRouter returns it in ``usage.cost``). An ESTIMATED rate per model can be declared to
    compare before calling, and it is labelled as an estimate everywhere it appears. It is
    never written down as a billed cost.

NO GLOBAL STATE
    The original swapped a module-level ``MODEL`` around each attempt and restored it
    afterwards. Here every attempt gets its own gateway from an injected
    ``gateway_for_model`` callable: nothing global is mutated, so nothing can be left behind.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Protocol

from mirag.core.errors import BudgetExceededError, MiragError, OfflineModeError
from mirag.features.flags import FeatureGate, GateDecision
from mirag.i18n.lexicon import Lexicon
from mirag.retrieval.plan import Depth, RetrievalPlan

FEATURE = "model_routing"
SIMPLE_MAX_LENGTH = 90
"""A definition request longer than this is not a quick definition any more."""
WIDE_PLAN_DOMAINS = 4
"""A plan that crosses this many boxes is not a simple question, however short it reads."""
LEADING_NOISE = " ¿¡\t\n"


class TaskClass(StrEnum):
    SIMPLE = "simple"
    NORMAL = "normal"
    COMPLEX = "complex"
    ARCHITECTURAL = "architectural"


@dataclass(frozen=True, slots=True)
class TokenRate:
    """USD per million tokens. An ESTIMATE from public list prices, never a billed cost."""

    input_per_million: float
    output_per_million: float


@dataclass(frozen=True, slots=True)
class CostEstimate:
    """An ESTIMATED cost, labelled as such so it cannot be mistaken for an invoice."""

    usd: float
    input_tokens: int
    output_tokens: int
    kind: str = "estimate"
    """Always ``"estimate"``: the real cost only exists after the call (``usage.cost``)."""


@dataclass(frozen=True, slots=True)
class RoutingTable:
    """Which model each task class prefers. A DECLARED preference, not a measured one."""

    models: Mapping[TaskClass, str]
    fallbacks: tuple[str, ...]
    max_tokens: Mapping[TaskClass, int]
    estimated_rates: Mapping[str, TokenRate] = field(default_factory=dict)
    default_max_tokens: int = 12_000


HAIKU = "anthropic/claude-haiku-4.5"

# Every class maps to the same model ON PURPOSE: changing them without data would be choosing
# blind. The hook is ready; the decision belongs to the day there are measurements.
#
# NOTE - the fallback of this module is UNREACHABLE today, and that is worth knowing before
# trusting it: the fallbacks of a route are this list minus the chosen model, and since every
# class maps to this same model, the list always comes out EMPTY. It is not a bug to fix
# blindly: adding a second model without having measured anything would be choosing at random.
# It is written down so nobody reads "there are fallbacks" where it says "there is a list".
DEFAULT_TABLE = RoutingTable(
    models=MappingProxyType({
        TaskClass.SIMPLE: HAIKU,
        TaskClass.NORMAL: HAIKU,
        TaskClass.COMPLEX: HAIKU,
        TaskClass.ARCHITECTURAL: HAIKU,
    }),
    fallbacks=(HAIKU,),
    max_tokens=MappingProxyType({
        TaskClass.SIMPLE: 4_000,
        TaskClass.NORMAL: 12_000,
        TaskClass.COMPLEX: 12_000,
        TaskClass.ARCHITECTURAL: 16_000,
    }),
    # $/1M tokens, ESTIMATED from the public web page. Only to compare before calling.
    estimated_rates=MappingProxyType({HAIKU: TokenRate(1.0, 5.0)}),
)


@dataclass(frozen=True, slots=True)
class ModelRoute:
    model: str
    task_class: TaskClass | None
    """``None`` when the router is off and nothing was classified."""
    reason: str
    fallbacks: tuple[str, ...] = ()
    max_tokens: int = 12_000
    estimated_rate: TokenRate | None = None
    gate: GateDecision | None = None
    """The feature-gate decision behind this route, so a caller can explain it in its locale."""

    @property
    def routed(self) -> bool:
        return self.task_class is not None

    @property
    def candidates(self) -> tuple[str, ...]:
        """The chosen model first, then the fallbacks, without repeats."""
        return tuple(dict.fromkeys((self.model, *self.fallbacks)))

    def estimated_cost(self, input_tokens: int = 8_000, output_tokens: int = 2_000) -> CostEstimate | None:
        """ESTIMATE, not a billed cost. ``None`` when there is no known rate: no invented numbers."""
        rate = self.estimated_rate
        if rate is None:
            return None
        usd = input_tokens / 1e6 * rate.input_per_million + output_tokens / 1e6 * rate.output_per_million
        return CostEstimate(round(usd, 5), input_tokens, output_tokens)


@dataclass(frozen=True, slots=True)
class Classification:
    task_class: TaskClass
    reasons: tuple[str, ...]

    @property
    def reason(self) -> str:
        return " · ".join(self.reasons)


class TaskClassifier:
    """simple | normal | complex | architectural. Deterministic and explainable.

    The patterns are per locale (``model_routing.*`` in ``lexicon.json``); the plan-based
    upgrades are language neutral.
    """

    def __init__(self, lexicon: Lexicon) -> None:
        self._architectural = lexicon.pattern("model_routing.architectural")
        self._complex = lexicon.pattern("model_routing.complex")
        self._simple = lexicon.pattern("model_routing.simple")

    def classify(self, request: str | None, plan: RetrievalPlan | None = None) -> Classification:
        text = request or ""
        reasons: list[str] = []
        if self._architectural.search(text):
            task, reasons = TaskClass.ARCHITECTURAL, ["asks to design or compare"]
        elif self._complex.search(text):
            task, reasons = TaskClass.COMPLEX, ["touches concurrency, consistency or security"]
        elif self._simple.match(text.strip(LEADING_NOISE)) and len(text) < SIMPLE_MAX_LENGTH:
            task, reasons = TaskClass.SIMPLE, ["short definition"]
        else:
            task, reasons = TaskClass.NORMAL, ["neither trivial nor design"]

        if plan is not None:
            if plan.needs_code and task is TaskClass.SIMPLE:
                task = TaskClass.NORMAL
                reasons.append("but code has to be generated")
            if len(plan.domains or ()) >= WIDE_PLAN_DOMAINS and task in (TaskClass.SIMPLE, TaskClass.NORMAL):
                task = TaskClass.COMPLEX
                reasons.append(f"crosses {len(plan.domains)} areas")
            if plan.depth == Depth.DEEP.value and task is TaskClass.SIMPLE:
                task = TaskClass.NORMAL
                reasons.append("the plan asks for depth")
        return Classification(task, tuple(reasons))


class ModelRouter:
    """Chooses the route of a request. Off by default: then it returns the usual model."""

    def __init__(
        self,
        classifier: TaskClassifier,
        gate: FeatureGate,
        default_model: str,
        table: RoutingTable = DEFAULT_TABLE,
    ) -> None:
        self._classifier = classifier
        self._gate = gate
        self._default_model = default_model
        self._table = table

    def _fallbacks_for(self, model: str) -> tuple[str, ...]:
        return tuple(m for m in dict.fromkeys(self._table.fallbacks) if m != model)

    def choose(self, request: str | None, plan: RetrievalPlan | None = None) -> ModelRoute:
        decision = self._gate.decide(FEATURE)
        if not decision.enabled:
            return ModelRoute(
                model=self._default_model,
                task_class=None,
                reason=f"router off ({decision.code})",
                fallbacks=self._fallbacks_for(self._default_model),
                max_tokens=self._table.default_max_tokens,
                estimated_rate=self._table.estimated_rates.get(self._default_model),
                gate=decision,
            )
        classification = self._classifier.classify(request, plan)
        model = self._table.models.get(classification.task_class, self._default_model)
        return ModelRoute(
            model=model,
            task_class=classification.task_class,
            reason=classification.reason,
            fallbacks=self._fallbacks_for(model),
            max_tokens=self._table.max_tokens.get(classification.task_class, self._table.default_max_tokens),
            estimated_rate=self._table.estimated_rates.get(model),
            gate=decision,
        )


# ── calling with fallback ────────────────────────────────────────────────────


class ChatGateway(Protocol):
    """What :func:`call_with_fallback` needs from a gateway (``LLMGateway`` satisfies it)."""

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]: ...


GatewayForModel = Callable[[str], ChatGateway]


class AttemptOutcome(StrEnum):
    OK = "ok"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Attempt:
    model: str
    outcome: AttemptOutcome
    error: str = ""


@dataclass(frozen=True, slots=True)
class FallbackResult:
    message: dict[str, Any]
    attempts: tuple[Attempt, ...]

    @property
    def model(self) -> str:
        """The model that finally answered."""
        return self.attempts[-1].model


class AllModelsFailedError(RuntimeError, MiragError):
    """Every candidate of a route failed. Carries each attempt so the trace can say why."""

    def __init__(self, attempts: Sequence[Attempt]) -> None:
        self.attempts = tuple(attempts)
        detail = "; ".join(f"{a.model}: {a.error}" for a in self.attempts)
        super().__init__(f"every model failed ({len(self.attempts)} attempts): {detail}")


NOT_RETRIED: tuple[type[BaseException], ...] = (OfflineModeError, BudgetExceededError)
"""Deliberate stops, not failures. The offline lock is not a flaky provider, and the spending
cap must not be dodged by asking the next model (each one may come with a fresh budget)."""


def call_with_fallback(
    messages: list[dict[str, Any]],
    route: ModelRoute,
    tools: list[dict[str, Any]] | None,
    gateway_for_model: GatewayForModel,
) -> FallbackResult:
    """Call the route's model; if it fails, try the next candidate. Report every attempt.

    ``gateway_for_model`` builds (or returns) the gateway of ONE model - for example
    ``lambda name: factory.with_model(OpenRouterChatModel(name, key))``. Nothing global is
    touched. The offline lock and the budget cap propagate at once: they are not retried.
    """
    attempts: list[Attempt] = []
    for model in route.candidates:
        try:
            message = gateway_for_model(model).chat(messages, tools)
        except NOT_RETRIED:
            raise
        except Exception as exc:  # deliberately broad: any provider failure moves to the next model
            attempts.append(Attempt(model, AttemptOutcome.FAILED, f"{type(exc).__name__}: {exc}"))
            continue
        attempts.append(Attempt(model, AttemptOutcome.OK))
        return FallbackResult(message, tuple(attempts))
    raise AllModelsFailedError(attempts)
