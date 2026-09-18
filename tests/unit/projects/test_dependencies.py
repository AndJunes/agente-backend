"""A broken import is not a missing dependency: ERROR sinks the project, LIMIT caps it."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from mirag.projects.dependencies import (
    DependencyAnalyzer,
    Finding,
    Severity,
    exported_names,
    has_module_getattr,
    has_star_import,
    worst,
)
from mirag.projects.model import Project

from .conftest import BooksFactory, KnownInstalls

Analyzer = Callable[..., KnownInstalls]
ABSENT = "surely_not_installed_mirag_probe_pkg"


def findings_of(analyzer: DependencyAnalyzer, files: dict[str, str]) -> tuple[Finding, ...]:
    return analyzer.analyze(Project.from_mapping("x", files))[1]


def kinds(findings: tuple[Finding, ...]) -> set[str]:
    return {f.kind for f in findings}


# ── internal: an ERROR of the project ────────────────────────────────────────

def test_a_broken_internal_import_is_an_error(analyzer: Analyzer) -> None:
    found = findings_of(analyzer(), {"app/__init__.py": "", "app/main.py": "from app.missing import x\n"})
    broken = [f for f in found if f.kind == "broken_internal_import"]
    assert broken and broken[0].severity is Severity.ERROR
    assert broken[0].file == "app/main.py" and broken[0].line == 1 and broken[0].subject == "app.missing"


def test_a_symbol_that_does_not_exist_is_an_error(analyzer: Analyzer) -> None:
    """The manifest can promise ``BookRepo`` while the file defines ``RepoBooks``."""
    found = findings_of(analyzer(), {"app/__init__.py": "", "app/repo.py": "class RepoBooks:\n    pass\n",
                                     "app/main.py": "from app.repo import BookRepo\n"})
    missing = [f for f in found if f.kind == "missing_symbol"]
    assert missing and missing[0].severity is Severity.ERROR
    assert "BookRepo" in missing[0].detail


def test_imports_inside_functions_are_seen_too(analyzer: Analyzer) -> None:
    found = findings_of(analyzer(), {"app/__init__.py": "",
                                     "app/main.py": "def lazy():\n    from app.nowhere import x\n    return x\n"})
    assert "broken_internal_import" in kinds(found)


def test_relative_imports_resolve_against_their_package(analyzer: Analyzer) -> None:
    files = {"app/__init__.py": "", "app/books/__init__.py": "",
             "app/books/models.py": "def validate():\n    return []\n",
             "app/books/service.py": "from . import models\nfrom .models import validate\nfrom ..books import models as m\n"}
    assert findings_of(analyzer(), files) == ()
    files["app/books/service.py"] = "from .nothing import validate\n"
    assert "broken_internal_import" in kinds(findings_of(analyzer(), files))


def test_a_relative_import_is_never_taken_for_a_missing_package(analyzer: Analyzer) -> None:
    """``from .helpers import x`` in a top-level file used to become "'helpers' is not
    installed" (a LIMIT that caps) instead of a broken import of the project (an ERROR)."""
    found = findings_of(analyzer(), {"main.py": "from .helpers import x\n", "tests/test_x.py": ""})
    assert "missing_dependency" not in kinds(found)
    assert "broken_internal_import" in kinds(found)


def test_a_re_exported_name_is_defined(analyzer: Analyzer) -> None:
    """The fix a repair adds - ``app/__init__.py`` re-exporting ``create_server`` - used to be
    reported as a missing symbol itself, so the repair could never converge."""
    files = {"app/__init__.py": "from app.main import create_server\nfrom .main import Handler as H\n",
             "app/main.py": "class Handler:\n    pass\n\n\ndef create_server():\n    return None\n",
             "run.py": "from app import create_server, H\n"}
    assert not [f for f in findings_of(analyzer(), files) if f.severity is Severity.ERROR]


def test_names_bound_in_compound_statements_count(analyzer: Analyzer) -> None:
    source = ("try:\n    from json import loads as parse\nexcept ImportError:\n    parse = None\n"
              "if True:\n    FLAG = 1\nelse:\n    OTHER = 2\n"
              "A, (B, *C) = 1, (2, 3)\n"
              "with open(__file__) as HANDLE:\n    pass\n"
              "for INDEX in range(1):\n    pass\n"
              "def outer():\n    INNER = 1\n")
    assert {"parse", "FLAG", "OTHER", "A", "B", "C", "HANDLE", "INDEX", "outer"} <= exported_names(source)
    assert "INNER" not in exported_names(source), "a function's locals are not module attributes"


def test_a_module_getattr_lowers_the_severity(analyzer: Analyzer) -> None:
    """PEP 562: the symbol can exist at runtime without being in the AST."""
    files = {"app/__init__.py": "", "app/dyn.py": "def __getattr__(name):\n    return 1\n",
             "app/main.py": "from app.dyn import whatever\n"}
    assert "missing_symbol" not in kinds(findings_of(analyzer(), files))
    assert has_module_getattr(files["app/dyn.py"])


def test_a_star_import_makes_the_absence_unprovable(analyzer: Analyzer) -> None:
    files = {"app/__init__.py": "", "app/base.py": "X = 1\n", "app/api.py": "from app.base import *\n",
             "app/main.py": "from app.api import X\n"}
    assert has_star_import(files["app/api.py"])
    assert "missing_symbol" not in kinds(findings_of(analyzer(), files))


def test_importing_a_submodule_by_name_is_not_a_missing_symbol(analyzer: Analyzer) -> None:
    files = {"app/__init__.py": "", "app/books/__init__.py": "", "app/books/repository.py": "",
             "app/main.py": "from app.books import repository\nfrom app import books\n"}
    assert findings_of(analyzer(), files) == ()


def test_a_syntax_error_is_not_judged_here(analyzer: Analyzer) -> None:
    """Syntax belongs to another phase: here it must neither crash nor invent findings."""
    assert findings_of(analyzer(), {"app/__init__.py": "", "app/main.py": "def broken(:\n"}) == ()
    assert exported_names("def broken(:\n") == frozenset()


# ── external: a LIMIT of this machine ────────────────────────────────────────

def test_a_missing_dependency_is_a_limit_not_an_error(analyzer: Analyzer) -> None:
    """The distinction that makes the FastAPI case honest."""
    found = findings_of(analyzer(), {"app/__init__.py": "", "app/main.py": "from fastapi import FastAPI\n",
                                     "requirements.txt": "fastapi\n"})
    absent = [f for f in found if f.kind == "missing_dependency"]
    assert absent and all(f.severity is Severity.LIMIT for f in absent)
    assert absent[0].subject == "fastapi"
    assert not [f for f in found if f.severity is Severity.ERROR]
    assert "undeclared_dependency" not in kinds(found), "it IS declared in requirements.txt"


def test_an_installed_dependency_raises_no_limit(analyzer: Analyzer) -> None:
    found = findings_of(analyzer(fastapi=True), {"app/__init__.py": "", "app/main.py": "import fastapi\n",
                                                 "requirements.txt": "fastapi\n"})
    assert found == ()


def test_a_dependency_that_could_not_be_observed_is_not_called_missing(analyzer: Analyzer) -> None:
    """``None`` means "could not look": that is not proof of absence."""
    found = findings_of(analyzer(fastapi=None), {"app/__init__.py": "", "app/main.py": "import fastapi\n",
                                                 "requirements.txt": "fastapi\n"})
    assert "missing_dependency" not in kinds(found)


def test_an_undeclared_dependency_is_only_a_notice(analyzer: Analyzer) -> None:
    found = findings_of(analyzer(requests=True), {"app/__init__.py": "", "app/main.py": "import requests\n"})
    assert kinds(found) == {"undeclared_dependency"}
    assert worst(found) is Severity.NOTICE


def test_the_standard_library_produces_no_findings(analyzer: Analyzer) -> None:
    found = findings_of(analyzer(), {"app/__init__.py": "",
                                     "app/main.py": "import json, sqlite3, threading\n"
                                                    "from http.server import ThreadingHTTPServer\n"})
    assert found == ()


def test_the_demo_project_has_no_finding_at_all(analyzer: Analyzer, books: BooksFactory) -> None:
    imports, found = analyzer().analyze(books())
    assert found == ()
    assert {i.kind for i in imports} == {"internal", "stdlib"}


def test_every_import_is_classified(analyzer: Analyzer) -> None:
    imports = analyzer().imports(Project.from_mapping("x", {
        "app/__init__.py": "", "app/core.py": "",
        "app/main.py": "import os\nimport fastapi.routing\nfrom app.core import x\nfrom . import core\n"}))
    by_module = {(i.module, i.level): i.kind for i in imports}
    assert by_module == {("os", 0): "stdlib", ("fastapi.routing", 0): "external",
                         ("app.core", 0): "internal", ("app", 1): "internal"}


def test_the_declared_dependencies_are_read_from_requirements(books: BooksFactory) -> None:
    project = Project.from_mapping("x", {"requirements.txt": "FastAPI[all]>=0.1  # web\n-r other.txt\n"
                                                             "uvicorn==1\npython-dateutil~=2\n\n# comment\n"})
    assert DependencyAnalyzer.declared(project) == {"fastapi", "uvicorn", "python_dateutil"}
    assert DependencyAnalyzer.declared(books()) == frozenset(), "comments are not dependencies"
    assert DependencyAnalyzer.declared(Project("empty")) == frozenset()


def test_the_module_map_includes_implicit_packages() -> None:
    mapping = DependencyAnalyzer.module_map(Project.from_mapping("x", {
        "app/__init__.py": "", "app/books/repo.py": "", "README.md": ""}))
    assert mapping["app"] == "app/__init__.py"
    assert mapping["app.books.repo"] == "app/books/repo.py"
    assert mapping["app.books"] == "", "a package without __init__.py still resolves"
    assert "README" not in mapping


def test_findings_are_deduplicated(analyzer: Analyzer) -> None:
    found = findings_of(analyzer(), {"app/__init__.py": "",
                                     "app/main.py": "from app.missing import a\nfrom app.missing import a\n"})
    assert len([f for f in found if f.kind == "broken_internal_import"]) == 1


# ── severity ─────────────────────────────────────────────────────────────────

def _finding(severity: Severity) -> Finding:
    return Finding("x", severity, "a.py", 1, "")


@pytest.mark.parametrize(("severities", "expected"), [
    ((), None),
    ((Severity.NOTICE,), Severity.NOTICE),
    ((Severity.NOTICE, Severity.LIMIT), Severity.LIMIT),
    ((Severity.LIMIT, Severity.ERROR, Severity.NOTICE), Severity.ERROR),
])
def test_worst_orders_error_over_limit_over_notice(severities: tuple[Severity, ...], expected: Severity | None) -> None:
    assert worst(_finding(s) for s in severities) is expected


def test_of_severity_filters(analyzer: Analyzer) -> None:
    found = [_finding(Severity.ERROR), _finding(Severity.LIMIT), _finding(Severity.ERROR)]
    assert len(DependencyAnalyzer.of_severity(found, Severity.ERROR)) == 2


# ── observed, not assumed: the real interpreter ──────────────────────────────

@pytest.mark.slow
def test_presence_is_observed_in_the_interpreter_that_runs_the_code(real_analyzer: DependencyAnalyzer) -> None:
    observed = real_analyzer.installed({ABSENT, "json", ""})
    assert observed == {ABSENT: False, "json": True}
    assert real_analyzer.installed(set()) == {}


@pytest.mark.slow
def test_a_really_absent_package_ends_as_a_limit(real_analyzer: DependencyAnalyzer) -> None:
    found = findings_of(real_analyzer, {"app/__init__.py": "", "app/main.py": f"import {ABSENT}\n"})
    assert {(f.kind, f.severity) for f in found} == {("missing_dependency", Severity.LIMIT),
                                                     ("undeclared_dependency", Severity.NOTICE)}
