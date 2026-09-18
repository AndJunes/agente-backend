"""Writes files into a temporary directory and runs a command there.

It is the only tool that produces EVIDENCE instead of opinion: the tests pass or they do
not. Minimal isolation (allow-listed binaries, timeout, temporary directory): enough for a
local demo, it is NOT a real sandbox.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path

from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.verdict import MAX_OUTPUT, ExecutionResult


def child_environment() -> dict[str, str]:
    """UTF-8 everywhere: on Windows a child Python otherwise prints in the ANSI code page."""
    env = dict(os.environ)
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    return env


class CodeRunner:
    def __init__(self, interpreters: InterpreterRegistry, timeout_s: int = 30, max_output: int = MAX_OUTPUT) -> None:
        self.interpreters = interpreters
        self.timeout_s = timeout_s
        self.max_output = max_output

    def run(self, files: Mapping[str, str], command: str) -> ExecutionResult:
        if not files:
            return ExecutionResult.not_executed("no file was given")
        try:
            parts = shlex.split(command or "")
        except ValueError as exc:
            return ExecutionResult.not_executed(f"malformed command ({exc})")
        executable = self.interpreters.resolve(parts[0]) if parts else None
        if not parts or executable is None:
            return ExecutionResult.not_executed(
                f"only {self.interpreters.describe()} may run here. You asked: {command!r}"
            )

        with tempfile.TemporaryDirectory(prefix="mirag-run-") as folder:
            root = Path(folder).resolve()
            for relative, content in files.items():
                target = (root / relative).resolve()
                if not target.is_relative_to(root):  # nothing like ../../etc/passwd
                    return ExecutionResult.not_executed(f"path not allowed ({relative!r})")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(str(content).encode("utf-8"))
            try:
                completed = subprocess.run(
                    [executable, *parts[1:]],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self.timeout_s,
                    env=child_environment(),
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return ExecutionResult.not_executed(
                    f"TIMEOUT, it did not finish in {self.timeout_s}s (an infinite loop, or waiting on the network?)"
                )
            except FileNotFoundError:
                return ExecutionResult.not_executed(f"{parts[0]} is not installed on this machine")

        output = ((completed.stdout or "") + (completed.stderr or "")).strip()
        return ExecutionResult.from_run(output, completed.returncode, self.max_output)
