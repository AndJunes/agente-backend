"""The chat-model port and its real adapter."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from mirag.core.errors import RateLimitedError

RETRYABLE = frozenset({429, 500, 502, 503, 504})
"""Statuses worth asking again about: the provider's problem, not the request's."""

ATTEMPTS = 3
BACKOFF_S = (2.0, 6.0)
"""Waits between attempts. Short, because a person is watching a progress list, and free
providers usually clear a burst limit in seconds rather than minutes."""


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

    def _send(self, request: urllib.request.Request) -> dict[str, Any]:
        """The call, retried while the provider is the one saying no."""
        last = ""
        for attempt in range(ATTEMPTS):
            try:
                with self._open(request, timeout=self._timeout_s) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as error:
                if error.code not in RETRYABLE:
                    raise
                last = _detail(error)
                if attempt + 1 == ATTEMPTS:
                    break
                time.sleep(_wait_for(error, attempt))
        raise RateLimitedError(
            f"{self.name}: the provider refused {ATTEMPTS} times — {last}. This is a limit on "
            f"the provider's side, not a problem with the request. Free models are rate-limited "
            f"per minute; wait, or set MIRAG_MODEL to another one."
        )

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None,
                 require: str | None = None) -> LLMResponse: ...


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

    def _send(self, request: urllib.request.Request) -> dict[str, Any]:
        """The call, retried while the provider is the one saying no."""
        last = ""
        for attempt in range(ATTEMPTS):
            try:
                with self._open(request, timeout=self._timeout_s) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as error:
                if error.code not in RETRYABLE:
                    raise
                last = _detail(error)
                if attempt + 1 == ATTEMPTS:
                    break
                time.sleep(_wait_for(error, attempt))
        raise RateLimitedError(
            f"{self.name}: the provider refused {ATTEMPTS} times — {last}. This is a limit on "
            f"the provider's side, not a problem with the request. Free models are rate-limited "
            f"per minute; wait, or set MIRAG_MODEL to another one."
        )

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None,
                 require: str | None = None) -> LLMResponse:
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
            # When the pipeline cannot continue without a specific call, ASK for it as
            # required instead of hoping. A model that answers a "deliver the blueprint"
            # request in prose has not failed at reasoning — it has answered a different
            # question — and on a free provider that happens often enough to look like the
            # agent is broken. `tool_choice` is what the field is for.
            if require:
                body["tool_choice"] = {"type": "function", "function": {"name": require}}
        request = urllib.request.Request(
            self._url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Content-Type": "application/json",
            },
        )
        payload = self._send(request)
        if "choices" not in payload:
            # A 200 carrying an error body. OpenRouter does this for some upstream failures,
            # and reading `choices` straight would raise a KeyError three frames away from
            # the cause.
            detail = (payload.get("error") or {}).get("message") or str(payload)[:200]
            raise RateLimitedError(f"{self.name}: the provider answered without a completion — {detail}")
        usage = payload.get("usage") or {}
        return LLMResponse(
            message=payload["choices"][0]["message"],
            usage=Usage(
                prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                completion_tokens=int(usage.get("completion_tokens", 0) or 0),
                cost_usd=float(usage.get("cost", 0.0) or 0.0),
            ),
        )


def _detail(error: urllib.error.HTTPError) -> str:
    """The provider's own words, which are usually the useful part."""
    try:
        body = json.loads(error.read())
        inner = body.get("error") or {}
        raw = (inner.get("metadata") or {}).get("raw")
        return str(raw or inner.get("message") or body)[:220]
    except Exception:
        return f"HTTP {error.code}"


def _wait_for(error: urllib.error.HTTPError, attempt: int) -> float:
    """``Retry-After`` when the provider sends one, otherwise the backoff."""
    header = error.headers.get("Retry-After") if error.headers else None
    if header:
        try:
            return min(float(header), 30.0)
        except ValueError:
            pass
    return BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)]
