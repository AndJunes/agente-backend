"""Tiny timing helpers. Every pipeline step reports how long it took — and one of them says
when the whole thing has to be over."""

from __future__ import annotations

import math
import threading
import time

from mirag.core.errors import ClientGoneError, DeadlineExceededError


class Stopwatch:
    """Milliseconds since construction (or since the last :meth:`restart`)."""

    __slots__ = ("_start",)

    def __init__(self) -> None:
        self._start = time.perf_counter()

    def restart(self) -> None:
        self._start = time.perf_counter()

    @property
    def ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000


class Deadline:
    """One wall clock for everything a request does: the calls, the retries, the backoff
    sleeps and the phases in between.

    `MAX_CALLS` counts calls and `Budget` counts money. Neither of them counts SECONDS, and a
    run that hangs spends neither: a provider trickling one byte a minute makes no further
    calls and costs nothing, so nothing stopped it. Measured against a local server sending
    one byte every 0.4s with a 1-second socket timeout, the read was still blocked after five
    seconds and was never going to return.

    It carries the cancellation Event rather than keeping it apart, because the two questions
    — "is there time left" and "is anybody still waiting" — are asked at exactly the same
    moments and answered by doing the same thing.
    """

    __slots__ = ("_limit", "_end", "cancelled")

    def __init__(self, limit_s: float = 0.0, cancelled: threading.Event | None = None) -> None:
        self._limit = limit_s if limit_s > 0 else 0.0
        self._end = time.monotonic() + self._limit if self._limit else math.inf
        self.cancelled = cancelled if cancelled is not None else threading.Event()

    @property
    def limited(self) -> bool:
        return self._limit > 0

    def remaining(self) -> float:
        """Seconds left, ``inf`` when unlimited.

        Monotonic on purpose: an operator changing the system clock, or a DST jump, neither
        ends a run early nor extends one.
        """
        return self._end - time.monotonic() if self._limit else math.inf

    def expired(self) -> bool:
        return self.remaining() <= 0

    def check(self) -> None:
        """Raise if this run must not START one more piece of work.

        The mirror of :meth:`Budget.check`: cut BEFORE spending, not after.
        """
        if self.cancelled.is_set():
            raise ClientGoneError("nobody is waiting for this answer any more")
        if self.expired():
            raise DeadlineExceededError(
                f"the {self._limit:.0f}s this request was given are spent. What was built is "
                f"kept; raise MIRAG_RUN_TIMEOUT_S to allow longer runs.")

    def sleep(self, seconds: float) -> None:
        """A wait that ends when the run does.

        The backoff used to be `time.sleep`, which sat six seconds waiting to retry a call
        that was never going to be made.
        """
        self.cancelled.wait(max(0.0, min(seconds, self.remaining())))
