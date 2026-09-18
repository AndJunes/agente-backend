"""The deterministic double of the model: the orchestrator cannot tell the difference.

WHAT IT IS AND WHAT IT IS NOT
    From the outside it behaves like a model: it receives messages and returns a message
    with content or with tool calls. Everything AROUND the model runs for real - retrieval,
    tools, test execution, verification, tracing.

    The only simulated thing is the model's DECISION. That is why whatever it proves is
    labelled SIMULATED and never VERIFIED: it shows the machine works when the model answers
    as expected, not that the model will answer that.

COST
    A double spends nothing and says so. It does not invent an "equivalent" cost: zero calls
    are zero dollars.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from mirag.llm.messages import assistant_text
from mirag.llm.models import LLMResponse, Usage

EXHAUSTED = "(the script ran out of answers)"


class ScriptedChatModel:
    """Returns the scripted messages in order."""

    name = "deterministic double"
    simulated = True

    def __init__(
        self,
        script: Iterable[dict[str, Any]],
        cost_usd: float = 0.0,
        fail_on_call: int | None = None,
        error: Exception | None = None,
    ) -> None:
        self._script = list(script)
        self._cost_usd = cost_usd
        self._fail_on_call = fail_on_call
        self._error = error or RuntimeError("the model failed")
        self.calls = 0
        self.received: list[dict[str, Any]] = []
        """What was sent, so tests can assert on it."""

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> LLMResponse:
        self.calls += 1
        # a copy: the caller keeps appending to the same list after the call
        self.received.append({"messages": list(messages), "tools": tools})
        if self._fail_on_call == self.calls:
            raise self._error
        message = self._script.pop(0) if self._script else assistant_text(EXHAUSTED)
        return LLMResponse(message=message, usage=Usage(cost_usd=self._cost_usd))
