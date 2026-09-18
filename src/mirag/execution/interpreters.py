"""Which interpreters exist ON THIS MACHINE. Observed, not assumed.

Having ``pytest`` in the allow-list while it was not installed made the model propose
``pytest -q``: nothing ran and the task was still considered done. So each name is
resolved AND probed. On Windows ``shutil.which("python3")`` can return the Microsoft Store
alias stub, which exists but does not run Python: probing catches it.

Mirag itself runs on Python, so ``python`` and ``python3`` always resolve: when the name
is not usable, they map to the interpreter running Mirag.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading
from collections.abc import Callable

ALLOWED: tuple[str, ...] = ("node", "python3", "python", "pytest")
PYTHON_NAMES = frozenset({"python", "python3"})
_PROBE_ARGS = {"node": ["--version"], "pytest": ["--version"]}


def _probe(path: str, args: list[str]) -> bool:
    try:
        completed = subprocess.run([path, *args], capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


class InterpreterRegistry:
    """Resolves allowed interpreter names to executables that really work."""

    def __init__(
        self,
        allowed: tuple[str, ...] = ALLOWED,
        which: Callable[[str], str | None] = shutil.which,
        probe: Callable[[str, list[str]], bool] = _probe,
    ) -> None:
        self.allowed = allowed
        self._which = which
        self._probe = probe
        self._resolved: dict[str, str | None] = {}
        self._lock = threading.Lock()

    def resolve(self, name: str) -> str | None:
        """The executable to run for ``name``, or ``None`` when it is not allowed or absent."""
        if name not in self.allowed:
            return None
        with self._lock:
            if name not in self._resolved:
                self._resolved[name] = self._find(name)
            return self._resolved[name]

    def _find(self, name: str) -> str | None:
        path = self._which(name)
        args = ["-c", "print(1)"] if name in PYTHON_NAMES else _PROBE_ARGS.get(name, ["--version"])
        if path and self._probe(path, args):
            return path
        if name in PYTHON_NAMES:
            return sys.executable
        return None

    @property
    def available(self) -> tuple[str, ...]:
        """Allowed names that resolve here, sorted."""
        return tuple(sorted(n for n in self.allowed if self.resolve(n)))

    def describe(self) -> str:
        return ", ".join(self.available) or "(none)"
