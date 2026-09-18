"""A free syntax check that catches half of the failures before running anything."""

from __future__ import annotations

from collections.abc import Mapping

from mirag.execution.runner import CodeRunner
from mirag.execution.verdict import ExecutionResult, ExecutionStatus


class SyntaxChecker:
    """Python is compiled in process (no subprocess needed); JavaScript goes through
    ``node --check``. A file that cannot be checked here counts as not passing: nothing is
    assumed to compile."""

    def __init__(self, runner: CodeRunner) -> None:
        self._runner = runner

    def check(self, files: Mapping[str, str]) -> ExecutionResult | None:
        """``None`` when everything compiles; otherwise the failing result."""
        for path, content in files.items():
            if path.endswith(".py"):
                try:
                    compile(str(content), path, "exec", dont_inherit=True)
                except (SyntaxError, ValueError) as exc:
                    line = getattr(exc, "lineno", None)
                    where = f"{path}:{line}" if line else path
                    return ExecutionResult.syntax_error(f"{where}: {type(exc).__name__}: {exc}")
            elif path.endswith(".js"):
                result = self._runner.run(files, f"node --check {path}")
                if result.status in (ExecutionStatus.FAILED, ExecutionStatus.NOT_EXECUTED):
                    return ExecutionResult.syntax_error(f"{path}: {result.header}")
        return None

    def check_then_run(self, files: Mapping[str, str], command: str) -> ExecutionResult:
        return self.check(files) or self._runner.run(files, command)
