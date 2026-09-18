"""Fixtures of the project area.

The demo project (``mirag.offline.books_project``) is the reference: pure stdlib, it really
runs, and every invariant is checked against it before being checked against a broken copy.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

import pytest

from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.runner import CodeRunner
from mirag.execution.syntax import SyntaxChecker
from mirag.offline import books_project
from mirag.projects.certification import ProjectCertifier
from mirag.projects.dependencies import DependencyAnalyzer
from mirag.projects.model import Project
from mirag.projects.packaging import Package, Packager

BooksFactory = Callable[..., Project]


class KnownInstalls(DependencyAnalyzer):
    """The analyzer with the installed packages DECLARED instead of observed.

    Observing spawns an interpreter; unit tests only need the classification to be right.
    Unknown external packages count as missing, which is exactly the case that matters.
    """

    def __init__(self, interpreters: InterpreterRegistry, installed: Mapping[str, bool | None] | None = None) -> None:
        super().__init__(interpreters)
        self._known = dict(installed or {})

    def installed(self, roots: Iterable[str]) -> dict[str, bool | None]:
        return {root: self._known.get(root, False) for root in sorted({r for r in roots if r})}


@pytest.fixture
def books() -> BooksFactory:
    """A fresh (unsealed) copy of the demo project, optionally renamed or with files replaced."""

    def make(name: str = "books-api", replace: Mapping[str, str] | None = None) -> Project:
        return Project.from_mapping(name, {**books_project.FILES, **(replace or {})}, books_project.SPEC)

    return make


@pytest.fixture
def analyzer(interpreters: InterpreterRegistry) -> Callable[..., KnownInstalls]:
    def make(**installed: bool | None) -> KnownInstalls:
        return KnownInstalls(interpreters, installed)

    return make


@pytest.fixture(scope="session")
def real_analyzer(interpreters: InterpreterRegistry) -> DependencyAnalyzer:
    return DependencyAnalyzer(interpreters)


@pytest.fixture
def certifier(runner: CodeRunner, syntax: SyntaxChecker, interpreters: InterpreterRegistry) -> ProjectCertifier:
    """Real runner and syntax checker; installed packages declared (no external one is)."""
    return ProjectCertifier(runner, syntax, KnownInstalls(interpreters))


@pytest.fixture(scope="session")
def real_certifier(runner: CodeRunner, syntax: SyntaxChecker, real_analyzer: DependencyAnalyzer) -> ProjectCertifier:
    return ProjectCertifier(runner, syntax, real_analyzer)


@pytest.fixture
def package(books: BooksFactory) -> Package:
    return Packager().seal(books())
