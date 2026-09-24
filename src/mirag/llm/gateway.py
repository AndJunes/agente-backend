"""The single entry point to the model: offline lock first, budget second, then the call."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterable
from typing import Any

from mirag.core.errors import OfflineModeError
from mirag.core.settings import Settings
from mirag.core.timing import Deadline
from mirag.llm.budget import Budget
from mirag.llm.models import Bounded, ChatModel, OpenRouterChatModel
from mirag.llm.scripted import ScriptedChatModel


class LLMGateway:
    """What the application calls. It owns the per-request budget.

    The lock lives here, in the only object that can reach a socket through the model: we
    do not trust ourselves to remember not to spend, we make it impossible. A scripted
    model is allowed through because it never leaves the process.
    """

    def __init__(self, model: ChatModel, budget: Budget | None = None, offline: bool = True,
                 deadline: Deadline | None = None) -> None:
        self.model = model
        self.budget = budget or Budget()
        self.offline = offline
        self.deadline = deadline or Deadline()
        # The gateway can only check BETWEEN calls, and the call is the part that hangs — so
        # the model is handed the same clock and its watchdog reads it. A model that cannot
        # take one never needed one: a scripted double never reaches a socket.
        if isinstance(model, Bounded):
            model.accept_deadline(self.deadline)

    @property
    def simulated(self) -> bool:
        return bool(getattr(self.model, "simulated", False))

    @property
    def model_name(self) -> str:
        return self.model.name

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None,
             require: str | None = None) -> dict[str, Any]:
        """One model turn. ``tools=None`` or ``[]`` sends no tools at all.

        ``require`` names a tool the answer MUST be a call to. Use it where the pipeline has
        no path forward without that call — the blueprint, the delivery — and not as a default:
        a model forced to call a tool it has nothing to say through will call it with rubbish.
        """
        if self.offline and not self.simulated:
            raise OfflineModeError(
                "MIRAG_OFFLINE is on: OpenRouter is not called. To try without spending use a "
                "scripted model; to spend for real, set MIRAG_OFFLINE=0."
            )
        self.deadline.check()  # do not START a call this run has no time left for
        self.budget.check()    # cut BEFORE spending, not after
        response = self._complete(messages, list(tools) if tools else None, require)
        self.budget.record(
            response.usage.prompt_tokens, response.usage.completion_tokens, response.usage.cost_usd
        )
        return response.message

    def _complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None,
                  require: str | None):
        """Calls the model, tolerating one that does not know about ``tool_choice``.

        Older clients and third-party doubles take two arguments. Rather than make every one of
        them grow a parameter they ignore, the requirement is dropped when it cannot be
        passed — the caller then gets the same answer it got before this existed."""
        if require is None:
            return self.model.complete(messages, tools)
        try:
            return self.model.complete(messages, tools, require)
        except TypeError:
            return self.model.complete(messages, tools)


ModelBuilder = Callable[[Settings], ChatModel]


def _openrouter(settings: Settings) -> ChatModel:
    return OpenRouterChatModel(
        model=settings.model,
        api_key=settings.openrouter_api_key,
        url=settings.openrouter_url,
        max_tokens=settings.max_output_tokens,
        timeout_s=settings.llm_timeout_s,
        call_timeout_s=settings.llm_call_timeout_s,
    )


class LLMGatewayFactory:
    """Creates one gateway per request, with its own budget."""

    def __init__(self, settings: Settings, model_builder: ModelBuilder = _openrouter) -> None:
        self._settings = settings
        self._build_model = model_builder

    @property
    def offline(self) -> bool:
        return self._settings.offline

    def create(self, script: Iterable[dict[str, Any]] | None = None, budget_usd: float | None = None,
               cancelled: threading.Event | None = None) -> LLMGateway:
        """A gateway backed by the real model, or by ``script`` when one is given.

        ``cancelled`` is the request's own Event: set it and every call after it refuses,
        and the one in flight is cut. It arrives here rather than being threaded through the
        pipeline because this is the single object every model call already passes through.
        """
        model: ChatModel = (
            ScriptedChatModel(script) if script is not None else self._build_model(self._settings)
        )
        limit = self._settings.budget_usd if budget_usd is None else budget_usd
        return LLMGateway(model, Budget(limit), offline=self._settings.offline,
                          deadline=Deadline(self._settings.run_timeout_s, cancelled))

    def with_model(self, model: ChatModel, budget_usd: float | None = None) -> LLMGateway:
        limit = self._settings.budget_usd if budget_usd is None else budget_usd
        return LLMGateway(model, Budget(limit), offline=self._settings.offline)
