"""What every code-execution backend is: `run(files, command) -> ExecutionResult`, plus the
two attributes anything downstream reads off one (`.enabled`, `.interpreters`).

`CodeRunner` (a host subprocess) and `DockerCodeRunner` (a disposable container) both satisfy
this shape without either naming the other — a `Protocol`, not a base class, because
`CodeRunner` predates this file and should not have to inherit from something to keep working.

The two guards here are the security-relevant half of `CodeRunner.run()`, pulled out so a
second backend reuses the exact same validation instead of a hand-copied second version that
could quietly drift from it: which interpreter a command may name, and where a file may be
written.
"""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, runtime_checkable

from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.verdict import ExecutionResult


@runtime_checkable
class CodeExecutionBackend(Protocol):
    interpreters: InterpreterRegistry
    enabled: bool

    def run(self, files: Mapping[str, str], command: str, *,
            dependencies: str = "") -> ExecutionResult: ...
    """``dependencies`` names a Docker volume of packages the code may import for THIS call.

    A volume name and not a path, deliberately: a generated project's dependencies are
    third-party code chosen by a model, they are installed inside the sandbox, and there is
    no host directory for anybody to be handed. A backend that has no sandbox (the host one)
    can do nothing with the name and ignores it.

    Per call and not per backend: one process certifies several projects at once, each with
    its own dependencies, and a backend carrying the name as state would hand one project's
    packages to another's tests. It is read-only input, exactly like the files are — a
    container that gets one still has no network."""


def resolve_command(
    command: str, interpreters: InterpreterRegistry
) -> tuple[str, list[str]] | ExecutionResult:
    """The resolved executable and full argv for ``command``, or a ready ``not_executed()``
    result when it is malformed or names something outside ``interpreters``'s allow-list."""
    try:
        parts = shlex.split(command or "")
    except ValueError as exc:
        return ExecutionResult.not_executed(f"malformed command ({exc})")
    executable = interpreters.resolve(parts[0]) if parts else None
    if not parts or executable is None:
        return ExecutionResult.not_executed(
            f"only {interpreters.describe()} may run here. You asked: {command!r}"
        )
    return executable, parts


def write_workspace(files: Mapping[str, str], root: Path) -> ExecutionResult | None:
    """Writes ``files`` under ``root``. ``None`` on success, else a ready ``not_executed()``
    result — a path escaping ``root`` (``../../etc/passwd``), nothing like it is allowed."""
    for relative, content in files.items():
        target = (root / relative).resolve()
        if not target.is_relative_to(root):
            return ExecutionResult.not_executed(f"path not allowed ({relative!r})")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(str(content).encode("utf-8"))
    return None
