"""The chat-model port and its real adapter."""

from __future__ import annotations

import http.client
import json
import socket
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from mirag.core.errors import (
    ClientGoneError,
    DeadlineExceededError,
    ModelUnreachableError,
    RateLimitedError,
)
from mirag.core.timing import Deadline

RETRYABLE = frozenset({429, 500, 502, 503, 504})
"""Statuses worth asking again about: the provider's problem, not the request's."""

ANY_TOOL = "*"
"""``require="*"`` means one of the offered tools, no matter which — `tool_choice: required`.

Distinct from naming one, and from naming none. A turn where two answers are both correct
cannot name one, and naming none is not the same as leaving it open: with no `tool_choice`
at all a model was observed calling `find_skill`, which was not among the tools it was given
that turn — it had read the name in the retrieved context and invented the call."""

ATTEMPTS = 3
BACKOFF_S = (2.0, 6.0)
"""Waits between attempts. Short, because a person is watching a progress list, and free
providers usually clear a burst limit in seconds rather than minutes."""

CALL_TIMEOUT_S = 600.0
"""Total wall clock for one :meth:`complete`, retries and backoff included.

Measured: one call on the free model averages 234 seconds. This is about 2.5x that. A call
still going at ten minutes is not a slow answer, it is a stuck socket — and from in here the
two look identical, which is exactly why this has to be a clock and not a judgement."""

ATTEMPT_SHARE = 0.5
"""How much of the call's budget one exchange may take.

Half, so a first attempt that hangs cannot eat the retry that would have worked. The retry is
not decoration here: this module is built around free providers dropping calls."""

WATCH_POLL_S = 0.5
"""How often the watchdog looks up. It also waits on the call finishing, so this is the worst
case for a watchdog outliving its call, not the common one."""


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

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None,
                 require: str | None = None) -> LLMResponse: ...


Opener = Callable[..., Any]


@runtime_checkable
class Bounded(Protocol):
    """A model that can be told when the whole run has to be over.

    Apart from :class:`ChatModel` on purpose: a scripted double never reaches a socket and has
    nothing to bound, so making every model implement this would be asking most of them to
    carry a method they cannot use.
    """

    def accept_deadline(self, deadline: Deadline) -> None: ...


class _Interrupt:
    """Ends one HTTP exchange from outside when its time is up, or when nobody is waiting.

    `urlopen(timeout=T)` is `socket.settimeout(T)`: it bounds one `recv`, and EVERY BYTE THAT
    ARRIVES REARMS IT. Measured against a local server sending one byte every 0.4s with
    T=1.0, the read was still blocked after five seconds and was never going to return.

    What ends that from another thread is `shutdown()` on the socket underneath, which makes
    the blocked `recv` return EOF. Measured: it breaks a dripped body with `IncompleteRead`
    and dripped headers with `BadStatusLine`, both at the deadline.

    NOT `close()`. Closing a descriptor while another thread is blocked on it is how a
    descriptor gets reused by somebody else's connection. Holding the socket OBJECT is what
    makes this safe: once urllib has closed it, its `fileno()` is -1 and `shutdown()` raises
    EBADF in THIS thread rather than reaching into a stranger's file.
    """

    __slots__ = ("_deadline", "_seconds", "_lock", "_socket", "_response", "_done", "_thread",
                 "fired")

    def __init__(self, deadline: Deadline, seconds: float) -> None:
        self._deadline = deadline
        self._seconds = seconds
        self._lock = threading.Lock()
        self._socket: socket.socket | None = None
        self._response: Any = None
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._watch, name="llm-watchdog", daemon=True)
        self.fired = ""
        """``""`` | ``"deadline"`` | ``"cancelled"`` — who broke the socket. `_send` reads it
        to tell a deadline apart from a network that failed on its own, which matters: saying
        "the provider could not be reached" about a connection WE cut names the wrong
        machine."""

    def adopt(self, sock: socket.socket | None) -> None:
        """The socket, the moment it is connected and BEFORE the request is written.

        A watchdog armed on the response object instead does not exist yet while the provider
        drips the response HEADERS — and that hangs inside `urlopen` itself, before there is
        any response to arm it on.
        """
        with self._lock:
            self._socket = sock

    def watching(self, response: Any) -> None:
        """The fallback for an injected opener (the test seam): there is no socket to reach,
        so the best available is `close()` on whatever it returned."""
        with self._lock:
            self._response = response

    def __enter__(self) -> _Interrupt:
        self._thread.start()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self._done.set()
        self._thread.join(timeout=1.0)

    def _watch(self) -> None:
        end = time.monotonic() + self._seconds
        while True:
            if self._deadline.cancelled.is_set():
                self._break("cancelled")
                return
            left = end - time.monotonic()
            if left <= 0:
                self._break("deadline")
                return
            if self._done.wait(min(left, WATCH_POLL_S)):
                return  # the exchange finished on its own: there is nothing to break

    def _break(self, reason: str) -> None:
        with self._lock:
            self.fired, sock, response = reason, self._socket, self._response
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # already closed, or never connected: nothing left to end
        elif response is not None:
            try:
                response.close()
            except Exception:  # noqa: BLE001 — a double may close in any way it likes
                pass


def _watched_opener(interrupt: _Interrupt, opener: Opener) -> Opener:
    """`urlopen` with a hand on the socket, and nothing else about urllib changed.

    The connection is substituted through `do_open` rather than by reimplementing
    `https_open`, because 3.11 passes `check_hostname` to it and 3.12 does not — this
    override never names those arguments and forwards whatever its Python sent. `HTTPError`
    still arrives with its body, which the retry below reads for `Retry-After`.
    """
    if opener is not urllib.request.urlopen:
        return opener  # a double was injected: leave it exactly as it is

    class _Watch:
        def do_open(self, http_class: Any, req: Any, **kwargs: Any) -> Any:
            def build(*args: Any, **kw: Any) -> Any:
                connection = http_class(*args, **kw)
                connect = connection.connect

                def watched_connect() -> None:
                    connect()
                    interrupt.adopt(connection.sock)

                connection.connect = watched_connect
                return connection

            return super().do_open(build, req, **kwargs)  # type: ignore[misc]

    class _HTTPS(_Watch, urllib.request.HTTPSHandler):
        pass

    class _HTTP(_Watch, urllib.request.HTTPHandler):
        pass

    return urllib.request.build_opener(_HTTP(), _HTTPS()).open


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
        call_timeout_s: float = CALL_TIMEOUT_S,
    ) -> None:
        self.name = model
        self._api_key = api_key
        self._url = url
        self._max_tokens = max_tokens
        self._timeout_s = timeout_s
        self._call_timeout_s = call_timeout_s
        # Unlimited until a gateway hands one over. A model built directly — a benchmark, a
        # script — is not inside a request and has no run to be bounded by.
        self._deadline = Deadline()
        # Indirection on purpose: tests replace THIS callable to simulate network failures
        # without opening a socket and without patching the global urllib.
        self._open = opener or urllib.request.urlopen

    def accept_deadline(self, deadline: Deadline) -> None:
        """The run's clock. The gateway can only check BETWEEN calls, and the call is the part
        that hangs — so the model gets the same clock and the watchdog reads it."""
        self._deadline = deadline

    def _send(self, request: urllib.request.Request) -> dict[str, Any]:
        """The call, retried while the provider is the one saying no — and bounded in total.

        ONE deadline for the whole method, retries and backoff included. Per-attempt was the
        other candidate and it is a lie to the caller: with three attempts and this backoff,
        a "600 second" call is a 1,808-second call, and nothing upstream can promise a number
        that is not enforced. Inside it no single exchange gets more than
        :data:`ATTEMPT_SHARE`, so a first attempt that hangs cannot eat the retry that would
        have worked.

        An attempt the deadline cut does NOT sleep the backoff before retrying. It has
        already waited.
        """
        guard = self._deadline
        end = time.monotonic() + self._call_timeout_s
        last = ""
        unreachable = ""
        cut = ""
        for attempt in range(ATTEMPTS):
            left = min(end - time.monotonic(), guard.remaining())
            if guard.cancelled.is_set() or left <= 0:
                break
            budget = min(left, self._call_timeout_s * ATTEMPT_SHARE)
            with _Interrupt(guard, budget) as interrupt:
                opener = _watched_opener(interrupt, self._open)
                try:
                    # The socket timeout STAYS. It is the cheap first line against a peer that
                    # says nothing at all, and it costs nothing. It is simply not the bound.
                    with opener(request, timeout=min(self._timeout_s, budget)) as response:
                        interrupt.watching(response)
                        payload = json.loads(response.read())
                    # A 200 carrying an error body. OpenRouter does this for some upstream
                    # failures — "Service temporarily overloaded" arrived this way while
                    # testing — and it was judged AFTER `_send` returned, outside the retry,
                    # so the most transient failure of the three was the only one asked about
                    # once. It is the same event as a 503 with a different status line.
                    if not (detail := _unusable(payload)):
                        return payload
                    last = detail
                    if attempt + 1 == ATTEMPTS:
                        break
                    guard.sleep(BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)])
                    continue
                except urllib.error.HTTPError as error:
                    if error.code not in RETRYABLE:
                        raise
                    last = _detail(error)
                    if attempt + 1 == ATTEMPTS:
                        break
                    guard.sleep(_wait_for(error, attempt))
                except (urllib.error.URLError, TimeoutError, OSError) as error:
                    # Never caught before, so a DNS failure, a refused connection or —
                    # measured on this machine — a certificate that could not be verified
                    # escaped every frame up to `socketserver`, which answers by closing the
                    # socket with no body.
                    if interrupt.fired:
                        # WE broke this socket. Calling that "the provider could not be
                        # reached" names the wrong machine, which is the whole mistake
                        # `ModelUnreachableError` exists to stop making.
                        cut = interrupt.fired
                        if cut == "cancelled":
                            break
                        continue  # the top of the loop decides whether there is time for more
                    # A TLS failure will not fix itself on the second attempt, so it is not
                    # retried: only the ones that plausibly pass next time are.
                    reason = getattr(error, "reason", error)
                    unreachable = f"{type(error).__name__}: {reason}"
                    if isinstance(reason, ssl.SSLError) or attempt + 1 == ATTEMPTS:
                        break
                    guard.sleep(BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)])
                except (http.client.HTTPException, ValueError) as error:
                    # A body that stops half way. `IncompleteRead` and `BadStatusLine` are
                    # HTTPExceptions and `json.JSONDecodeError` is a ValueError: NOT ONE of
                    # the three is an OSError, so until now all three escaped `_send`
                    # entirely — no retry, no named error — and arrived at the API boundary
                    # as a 502 with a sentence about the wrong thing.
                    #
                    # They are also exactly what breaking a socket produces, so this branch is
                    # what makes the deadline above reportable at all.
                    if interrupt.fired:
                        cut = interrupt.fired
                        if cut == "cancelled":
                            break
                        continue
                    last = f"{type(error).__name__}: {error}"
                    if attempt + 1 == ATTEMPTS:
                        break
                    guard.sleep(BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)])
        if guard.cancelled.is_set() or cut == "cancelled":
            raise ClientGoneError(
                f"{self.name}: the call was abandoned — nobody is waiting for this answer.")
        if cut or guard.expired() or time.monotonic() >= end:
            raise DeadlineExceededError(
                f"{self.name}: no answer within {self._call_timeout_s:.0f}s. The provider was "
                f"still sending when the time ran out — a socket timeout does not catch that, "
                f"it bounds one read and every byte rearms it. Raise MIRAG_LLM_CALL_TIMEOUT_S "
                f"if this model is genuinely this slow.")
        if unreachable:
            raise ModelUnreachableError(
                f"{self.name}: the provider could not be reached at {self._url} — {unreachable}. "
                f"This is the network between here and OpenRouter, not the request. If it is a "
                f"certificate, this Python has no CA bundle: run Install Certificates.command, "
                f"or set SSL_CERT_FILE."
            )
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
            if require == ANY_TOOL:
                # "call one of the tools I gave you, I do not mind which". The case for it is
                # a turn with two valid answers — the PM's `plan` may legitimately deliver a
                # plan OR ask another round — where naming one is wrong and naming none let
                # the model call `find_skill`, a tool it had merely READ ABOUT in its own
                # context and which was not offered in that turn at all.
                body["tool_choice"] = "required"
            elif require:
                body["tool_choice"] = {"type": "function", "function": {"name": require}}
        request = urllib.request.Request(
            self._url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Content-Type": "application/json",
            },
        )
        payload = self._send(request)  # `_send` has already established it is usable
        usage = payload.get("usage") or {}
        return LLMResponse(
            message=payload["choices"][0]["message"],
            usage=Usage(
                prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                completion_tokens=int(usage.get("completion_tokens", 0) or 0),
                cost_usd=float(usage.get("cost", 0.0) or 0.0),
            ),
        )


def _unusable(payload: Any) -> str:
    """Why this 200 cannot be read as a completion, or ``""`` when it can.

    `choices` present but EMPTY is its own case and was an IndexError three frames from the
    cause: `poolside/laguna-s-2.1:free` returns it under load.
    """
    if not isinstance(payload, dict):
        return f"the body is a {type(payload).__name__}, not an object"
    choices = payload.get("choices")
    if choices is None:
        inner = payload.get("error") or {}
        message = inner.get("message") if isinstance(inner, dict) else None
        return str(message or str(payload)[:200]) or "no choices and no error either"
    if not isinstance(choices, list) or not choices:
        return "the provider answered with an empty list of choices"
    if not isinstance(choices[0], dict) or not isinstance(message := choices[0].get("message"), dict):
        return "the first choice carries no message"
    # A 200, a choice, a message — and nothing in it. Free providers return this under load,
    # and it passed every check here because the SHAPE was right. Downstream it read as "the
    # model did not call the tool; it answered 0 characters of text", which blames the model
    # for a turn it never took. It is as transient as a 429 and now retried like one.
    if not (message.get("content") or "").strip() and not message.get("tool_calls"):
        reason = choices[0].get("native_finish_reason") or choices[0].get("finish_reason") or "?"
        return f"the provider returned an empty message with no tool call (finish_reason: {reason})"
    return ""


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
