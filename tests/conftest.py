"""Shared fixtures. Fakes here are as dumb as they can be: a test that needs a clever fake is
usually testing the fake."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest

from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.verdict import ExecutionResult
from mirag.i18n.catalog import MessageCatalog
from mirag.paths import LOCALES_DIR
from mirag.projects.dependencies import DependencyAnalyzer, Finding
from mirag.projects.installation import InstallReport
from mirag.projects.model import Project

INSTALLED_AT = "mirag-deps-abc123def4567890"
"""The Docker volume a successful install reports.

A NAME, not a path: that is the property the rework was about, and a test that used a path
here would keep passing over a regression back to one."""


@pytest.fixture
def catalog() -> MessageCatalog:
    """The REAL English catalog, not a stub.

    `MessageCatalog.template` returns the key itself when it is missing, so a stub catalog
    would make every message key look fine and a missing one would only surface in front of a
    user. With the bundled file, a key that was never added shows up as the literal
    `cert.dependencies.installed` in an assertion.
    """
    return MessageCatalog.from_file("en", LOCALES_DIR / "en" / "messages.json")


@pytest.fixture
def interpreters() -> InterpreterRegistry:
    return InterpreterRegistry()


def make_project(**files: str) -> Project:
    """A project with the four things `validate_structure` insists on, plus what is asked for."""
    base = {
        "app/__init__.py": "from app.main import create_thing\n",
        "app/main.py": "import fastapi\n\n\ndef create_thing():\n    return fastapi\n",
        "tests/test_main.py": "def test_it():\n    assert True\n",
        "requirements.txt": "fastapi==0.115.0\n",
    }
    return Project.from_mapping("demo", {**base, **files})


class FakeRunner:
    """A `CodeExecutionBackend` that answers from a script and remembers what it was asked."""

    def __init__(self, interpreters: InterpreterRegistry, *results: ExecutionResult,
                 enabled: bool = True) -> None:
        self.interpreters = interpreters
        self.enabled = enabled
        self._results = list(results)
        self.calls: list[tuple[str, str]] = []
        """``(command, dependency_path)`` per call, in order."""

    @property
    def default(self) -> ExecutionResult:
        return ExecutionResult.from_run("TEST:ok:PASS", 0)

    def run(self, files: Mapping[str, str], command: str, *,
            dependencies: str = "") -> ExecutionResult:
        del files
        self.calls.append((command, dependencies))
        return self._results.pop(0) if self._results else self.default

    @property
    def volumes(self) -> list[str]:
        """The dependency volume each call was given, in order."""
        return [volume for _command, volume in self.calls]


class FakeAnalyzer(DependencyAnalyzer):
    """The real analysis, with only the one subprocess replaced.

    `installed` is the single place the analyzer leaves the process, and it is also the only
    thing an install changes. Overriding it keeps the import classification, the symbol check
    and the severity rules under test instead of stubbing them out.
    """

    def __init__(self, interpreters: InterpreterRegistry, present_at: str = "") -> None:
        super().__init__(interpreters)
        self.present_at = present_at
        """The volume in which the external packages become importable. ``""`` means they
        never are."""
        self.asked: list[str] = []

    def installed(self, roots, dependencies: str = "") -> dict[str, bool | None]:
        self.asked.append(dependencies)
        found = bool(self.present_at) and dependencies == self.present_at
        return {root: found for root in sorted({r for r in roots if r})}


class FakeInstaller:
    """Installs nothing and reports whatever the test wants it to have reported."""

    def __init__(self, report: InstallReport, enabled: bool = True) -> None:
        self.report = report
        self.enabled = enabled
        self.projects: list[Project] = []

    def install(self, project: Project) -> InstallReport:
        self.projects.append(project)
        return self.report


def succeeded(volume: str = INSTALLED_AT, *packages: str) -> InstallReport:
    installed = packages or ("fastapi==0.115.0",)
    return InstallReport(True, f"installed {len(installed)}", volume, installed)


def failed(detail: str = "no network") -> InstallReport:
    return InstallReport(False, detail, log="could not resolve pypi.org")


class ScriptedRepairer:
    """A repairer that applies canned edits, and counts how many times it was asked.

    Each entry is what to write into the project on that attempt; ``None`` means "decline",
    which is the case that used to be indistinguishable from a failure.
    """

    def __init__(self, *edits: Mapping[str, str] | None) -> None:
        self._edits = list(edits)
        self.calls: list[tuple[int, tuple[str, ...]]] = []
        """``(attempt, subjects of the findings it was given)``."""

    def __call__(self, project: Project, findings: Sequence[Finding], output: str,
                 attempt: int) -> tuple[Project, tuple[str, ...], str]:
        del output
        self.calls.append((attempt, tuple(f.file for f in findings)))
        edit = self._edits.pop(0) if self._edits else None
        if edit is None:
            return project, (), "nothing left to change"
        copy = project.copy()
        for path, content in edit.items():
            copy.add(path, content)
        return copy, tuple(edit), f"repair {attempt}"
