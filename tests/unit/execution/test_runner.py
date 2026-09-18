"""The runner executes for real: these tests spawn interpreters."""

from __future__ import annotations

import sys

import pytest

from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.runner import CodeRunner
from mirag.execution.syntax import SyntaxChecker
from mirag.execution.verdict import ExecutionStatus, Failure

pytestmark = pytest.mark.slow

PASSING = "print('TEST:one:PASS')\nprint('TEST:two:PASS')\n"


def test_running_for_real_gives_evidence(runner: CodeRunner) -> None:
    result = runner.run({"t.py": PASSING}, "python3 t.py")
    assert result.status is ExecutionStatus.PASSED
    assert result.markers == {"one": "PASS", "two": "PASS"}


def test_an_exit_code_fails(runner: CodeRunner) -> None:
    result = runner.run({"t.py": "import sys\nprint('TEST:x:PASS')\nsys.exit(4)\n"}, "python t.py")
    assert result.status is ExecutionStatus.FAILED
    assert result.exit_code == 4


def test_a_command_outside_the_allow_list_never_runs(runner: CodeRunner) -> None:
    result = runner.run({"t.py": PASSING}, "bash -c 'echo TEST:x:PASS'")
    assert result.status is ExecutionStatus.NOT_EXECUTED
    assert "only" in result.detail


def test_a_path_escaping_the_sandbox_is_rejected(runner: CodeRunner) -> None:
    result = runner.run({"../escape.py": PASSING}, "python3 escape.py")
    assert result.status is ExecutionStatus.NOT_EXECUTED
    assert "path not allowed" in result.detail


def test_no_files_and_malformed_commands(runner: CodeRunner) -> None:
    assert runner.run({}, "python3 t.py").status is ExecutionStatus.NOT_EXECUTED
    assert runner.run({"t.py": PASSING}, "python3 'unclosed").status is ExecutionStatus.NOT_EXECUTED


def test_a_timeout_is_not_executed_not_green(interpreters: InterpreterRegistry) -> None:
    slow = CodeRunner(interpreters, timeout_s=1)
    result = slow.run({"t.py": "import time\ntime.sleep(10)\nprint('TEST:x:PASS')\n"}, "python3 t.py")
    assert result.status is ExecutionStatus.NOT_EXECUTED
    assert "TIMEOUT" in result.detail


def test_subfolders_are_created_and_utf8_survives(runner: CodeRunner) -> None:
    files = {"pkg/__init__.py": "", "pkg/mod.py": "TEXT = 'acción ñ'\n",
             "t.py": "from pkg.mod import TEXT\nprint('TEST:utf8:' + ('PASS' if TEXT == 'acción ñ' else 'FAIL'))\n"}
    assert runner.run(files, "python3 t.py").markers == {"utf8": "PASS"}


def test_syntax_is_checked_before_running(syntax: SyntaxChecker) -> None:
    result = syntax.check_then_run({"t.py": "def broken(:\n"}, "python3 t.py")
    assert result.status is ExecutionStatus.FAILED
    assert result.failure is Failure.SYNTAX
    assert syntax.check({"ok.py": "x = 1\n"}) is None


def test_python_always_resolves_even_without_a_usable_alias() -> None:
    registry = InterpreterRegistry(which=lambda name: None, probe=lambda path, args: False)
    assert registry.resolve("python3") == sys.executable
    assert registry.resolve("node") is None
    assert registry.resolve("bash") is None
    assert "node" not in registry.available


def test_a_stub_that_does_not_run_is_not_trusted() -> None:
    """The Windows Store alias exists on PATH and does not run Python: it must be probed."""
    registry = InterpreterRegistry(which=lambda name: f"C:/stub/{name}.exe", probe=lambda path, args: False)
    assert registry.resolve("python3") == sys.executable
