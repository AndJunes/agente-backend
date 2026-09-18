"""Tiny timing helpers. Every pipeline step reports how long it took."""

from __future__ import annotations

import time


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
