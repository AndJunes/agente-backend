"""Writes files into a temporary directory and runs a command there.

It is the only tool that produces EVIDENCE instead of opinion: the tests pass or they do
not. Minimal isolation (allow-listed binaries, timeout, temporary directory): enough for a
local demo, it is NOT a real sandbox.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path

from mirag.execution.backend import resolve_command, write_workspace
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.verdict import MAX_OUTPUT, ExecutionResult

KEPT_FROM_ENVIRONMENT = (
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
    # Windows: without SYSTEMROOT a child Python cannot even seed its random generator
    "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "PATHEXT", "COMSPEC",
    # Windows: `pip install --user` (the default without admin rights) puts packages under
    # `%APPDATA%\Python\PythonXY\site-packages`, and the interpreter's own `site` module reads
    # this variable to find that directory. Without it a --user-installed package is invisible
    # to the child even though `sys.path` finds it fine when the parent runs the same import:
    # every console-script launcher (`pytest.exe` included) failed with "No module named
    # '_pytest'" here, on the one machine that ever runs this without a virtualenv.
    "APPDATA",
)

DISABLED_REASON = (
    "execution is switched off (MIRAG_EXECUTION=off). The code and its tests are delivered "
    "without running them; running them is the QA agent's job. This is neither a pass nor a "
    "fail: nothing was observed."
)


def child_environment() -> dict[str, str]:
    """The environment the generated code sees. Without a single credential.

    Without ``env=``, ``subprocess.run`` hands the child the WHOLE ``os.environ``: a
    ``print(os.environ)`` in a file called ``test_something.py`` read the OpenRouter key and
    the Stellar seed, and the child has network access. Reproduced before fixing it. A
    container does not protect from this, because you give it the key through the
    environment. Only what an interpreter needs to start and find its modules is kept.

    UTF-8 everywhere: on Windows a child Python otherwise prints in the ANSI code page.
    """
    env = {name: os.environ[name] for name in KEPT_FROM_ENVIRONMENT if name in os.environ}
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    return env


class CodeRunner:
    def __init__(self, interpreters: InterpreterRegistry, timeout_s: int = 30, max_output: int = MAX_OUTPUT,
                 enabled: bool = True) -> None:
        self.interpreters = interpreters
        self.timeout_s = timeout_s
        self.max_output = max_output
        self.enabled = enabled
        """``False``: nothing runs and every result is NOT EXECUTED (see ``Settings.execution``)."""

    def run(self, files: Mapping[str, str], command: str) -> ExecutionResult:
        if not self.enabled:  # before touching the disk at all
            return ExecutionResult.not_executed(DISABLED_REASON)
        if not files:
            return ExecutionResult.not_executed("no file was given")
        resolved = resolve_command(command, self.interpreters)
        if isinstance(resolved, ExecutionResult):
            return resolved
        executable, parts = resolved

        with tempfile.TemporaryDirectory(prefix="mirag-run-") as folder:
            root = Path(folder).resolve()
            error = write_workspace(files, root)
            if error is not None:
                return error
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
