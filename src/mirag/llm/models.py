"""The chat-model port and its real adapter."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


@dataclass(frozen=True, slots=True)
class LLMResponse:
    message: dict[str, Any]
    usage: Usage


@runtime_checkable
class ChatModel(Protocol):
    """Anything that answers a conversation. One method, nothing else to depend on."""

    name: str
    simulated: bool
    """``True`` when the decision does not come from a real model (a script)."""

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> LLMResponse: ...


Opener = Callable[..., Any]


class OpenRouterChatModel:
    """A single HTTP call to OpenRouter's chat completions endpoint.

    It knows nothing about budgets or the offline lock: the :class:`LLMGateway` applies
    both before this object is reached, the same way for every model.
    """

    simulated = False

    def __init__(
        self,
        model: str,
        api_key: str,
        url: str = "https://openrouter.ai/api/v1/chat/completions",
        max_tokens: int = 12_000,
        timeout_s: float = 60.0,
        opener: Opener | None = None,
    ) -> None:
        self.name = model
        self._api_key = api_key
        self._url = url
        self._max_tokens = max_tokens
        self._timeout_s = timeout_s
        # Indirection on purpose: tests replace THIS callable to simulate network failures
        # without opening a socket and without patching the global urllib.
        self._open = opener or urllib.request.urlopen

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set: cannot call the model")
        body: dict[str, Any] = {
            "model": self.name,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "usage": {"include": True},  # ask for the real cost
        }
        # None or [] = NO tools, and then the key is not sent at all. Without this, a
        # conceptual question received every tool and the model started calling them in a
        # pipeline that was never going to run them.
        if tools:
            body["tools"] = tools
        request = urllib.request.Request(
            self._url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Content-Type": "application/json",
            },
        )
        with self._open(request, timeout=self._timeout_s) as response:
            payload = json.loads(response.read())
        usage = payload.get("usage") or {}
        return LLMResponse(
            message=payload["choices"][0]["message"],
            usage=Usage(
                prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                completion_tokens=int(usage.get("completion_tokens", 0) or 0),
                cost_usd=float(usage.get("cost", 0.0) or 0.0),
            ),
        )
