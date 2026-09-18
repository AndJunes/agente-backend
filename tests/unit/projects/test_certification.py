"""The chain that turns a project into evidence, and the ONE place that decides its status."""

from __future__ import annotations

import itertools
import re
from collections.abc import Sequence

import pytest

from mirag.i18n.catalog import MessageCatalog
from mirag.offline import books_project
from mirag.projects import probes
from mirag.projects.certification import (
    MAX_REPAIRS,
    Certificate,
    Phase,
    PhaseStatus,
    ProjectCertifier,
    ProjectStatus,
    StatusDeriver,
    find_entrypoint,
    validate_structure,
)
from mirag.projects.dependencies import Finding, Severity
from mirag.projects.model import Project

from .conftest import BooksFactory

OK, FAILED, LIMITED, SKIPPED = PhaseStatus.OK, PhaseStatus.FAILED, PhaseStatus.LIMITED, PhaseStatus.SKIPPED
ABSENT = "surely_not_installed_mirag_probe_pkg"
MINIMAL_TESTS = {"tests/__init__.py": "", "tests/test_x.py": "# t\n"}


def phases(*pairs: tuple[str, PhaseStatus]) -> tuple[Phase, ...]:
    return tuple(Phase(name, status, "") for name, status in pairs)


def finding(severity: Severity) -> Finding:
    return Finding("x", severity, "app/main.py", 1, "detail", "subject")


BASE = (("structure", OK), ("syntax", OK), ("imports", OK))
GREEN = phases(*BASE, ("tests", OK), ("crud", OK))
ALL_PASS = {"test_a": "PASS", "crud_create_x": "PASS"}


# ── the status table ─────────────────────────────────────────────────────────

TABLE = [
    # (case, phases, markers, findings, crud ids, expected)
    ("structure failed", phases(("structure", FAILED)), {}, (), (), ProjectStatus.FAILED),
    ("structure failed beats passing markers", phases(("structure", FAILED), ("tests", OK)), ALL_PASS, (), (),
     ProjectStatus.FAILED),
    ("syntax failed", phases(("structure", OK), ("syntax", FAILED)), {}, (), (), ProjectStatus.FAILED),
    ("a broken import sinks it even with every marker green", GREEN, ALL_PASS, (finding(Severity.ERROR),), (),
     ProjectStatus.FAILED),
    ("missing dependency and nothing ran", phases(*BASE, ("execution", LIMITED)), {}, (finding(Severity.LIMIT),),
     (), ProjectStatus.VALIDATED),
    ("exit 0 without markers is not passing", phases(*BASE, ("tests", LIMITED)), {}, (), (),
     ProjectStatus.EXECUTED),
    ("nothing ran", phases(*BASE), {}, (), (), ProjectStatus.GENERATED),
    ("some FAIL, some PASS", GREEN, {"a": "PASS", "b": "FAIL"}, (), (), ProjectStatus.PARTIAL),
    ("every marker FAIL", GREEN, {"a": "FAIL", "b": "FAIL"}, (), (), ProjectStatus.FAILED),
    ("the CRUD was not exercised entirely", GREEN, ALL_PASS, (), ("crud_create_x", "crud_list_x"),
     ProjectStatus.PARTIAL),
    ("a limit caps a green run", GREEN, ALL_PASS, (finding(Severity.LIMIT),), (), ProjectStatus.PARTIAL),
    ("a silent test phase cannot be hidden by the CRUD markers", phases(*BASE, ("tests", LIMITED), ("crud", OK)),
     {"crud_create_x": "PASS"}, (), ("crud_create_x",), ProjectStatus.PARTIAL),
    ("the README command fails", phases(*BASE, ("tests", OK), ("documented_command", FAILED)), ALL_PASS, (), (),
     ProjectStatus.PARTIAL),
    ("green with the full CRUD", GREEN, ALL_PASS, (), ("crud_create_x",), ProjectStatus.VERIFIED),
    ("green without an API", phases(*BASE, ("tests", OK), ("crud", SKIPPED)), {"test_a": "PASS"}, (), (),
     ProjectStatus.VERIFIED),
    ("a notice does not block", GREEN, ALL_PASS, (finding(Severity.NOTICE),), (), ProjectStatus.VERIFIED),
]


@pytest.mark.parametrize(("case", "given", "markers", "findings", "crud", "expected"), TABLE,
                         ids=[row[0] for row in TABLE])
def test_the_status_table(catalog_en: MessageCatalog, case: str, given: tuple[Phase, ...], markers: dict[str, str],
                          findings: tuple[Finding, ...], crud: tuple[str, ...], expected: ProjectStatus) -> None:
    status, reason = StatusDeriver(catalog_en).derive(given, markers, findings, crud)
    assert status is expected, f"{case}: {status} ({reason})"
    assert reason and "{" not in reason, reason


def test_a_limit_caps_the_status_and_an_error_sinks_it(catalog_en: MessageCatalog) -> None:
    derive = StatusDeriver(catalog_en).derive
    assert derive(GREEN, ALL_PASS, ())[0] is ProjectStatus.VERIFIED
    assert derive(GREEN, ALL_PASS, (finding(Severity.LIMIT),))[0] is ProjectStatus.PARTIAL
    assert derive(GREEN, ALL_PASS, (finding(Severity.ERROR),))[0] is ProjectStatus.FAILED


def test_nothing_is_ever_verified_without_a_passing_marker(catalog_en: MessageCatalog) -> None:
    derive = StatusDeriver(catalog_en).derive
    statuses = list(PhaseStatus)
    severities = [(), (finding(Severity.NOTICE),), (finding(Severity.LIMIT),), (finding(Severity.ERROR),)]
    for tests, crud, found in itertools.product(statuses, statuses, severities):
        given = phases(*BASE, ("tests", tests), ("crud", crud))
        for markers in ({}, {"a": "FAIL"}):
            status, _ = derive(given, markers, found, ())
            assert status is not ProjectStatus.VERIFIED, (tests, crud, found, markers)


@pytest.mark.parametrize(("catalog_name", "words"), [("catalog_en", "not passing"), ("catalog_es", "no es aprobar")])
def test_exit_zero_without_markers_says_it_is_not_passing(request: pytest.FixtureRequest, catalog_name: str,
                                                         words: str) -> None:
    catalog: MessageCatalog = request.getfixturevalue(catalog_name)
    status, reason = StatusDeriver(catalog).derive(phases(*BASE, ("tests", LIMITED)), {}, (), ())
    assert status is ProjectStatus.EXECUTED and words in reason


@pytest.mark.parametrize(("catalog_name", "words"), [("catalog_en", "not one marker"),
                                                     ("catalog_es", "no produjo ni un marcador")])
def test_a_silent_phase_is_named(request: pytest.FixtureRequest, catalog_name: str, words: str) -> None:
    """The 9 tests came out NO EVIDENCE and the 7 CRUD markers dragged the status to
    VERIFIED. That happened for real and cannot happen again."""
    catalog: MessageCatalog = request.getfixturevalue(catalog_name)
    status, reason = StatusDeriver(catalog).derive(phases(*BASE, ("tests", LIMITED), ("crud", OK)),
                                                   {"crud_a": "PASS"}, (), ("crud_a",))
    assert status is ProjectStatus.PARTIAL
    assert words in reason and "'tests'" in reason


def test_the_verified_reason_mentions_the_crud_only_when_there_was_one(catalog_en: MessageCatalog) -> None:
    derive = StatusDeriver(catalog_en).derive
    with_crud = derive(GREEN, ALL_PASS, (), ("crud_create_x",))[1]
    without = derive(phases(*BASE, ("tests", OK)), {"a": "PASS"}, (), ())[1]
    assert "CRUD" in with_crud and "CRUD" not in without


def test_the_certificate_counts_its_markers() -> None:
    certificate = Certificate(ProjectStatus.PARTIAL, "", (), (), {"a": "PASS", "b": "FAIL", "c": "PASS"})
    assert (certificate.passed, certificate.failed, certificate.ok) == (2, 1, False)
    assert Certificate(ProjectStatus.VERIFIED, "", (), (), {"a": "PASS"}).ok


# ── structure ────────────────────────────────────────────────────────────────

def test_the_demo_structure_is_complete(books: BooksFactory, catalog_en: MessageCatalog) -> None:
    assert validate_structure(books(), catalog_en) == []


@pytest.mark.parametrize("catalog_name", ["catalog_en", "catalog_es"])
def test_structure_problems_are_named(request: pytest.FixtureRequest, catalog_name: str) -> None:
    catalog: MessageCatalog = request.getfixturevalue(catalog_name)
    assert validate_structure(Project("x"), catalog) == [catalog.t("cert.problem.no_files"),
                                                         catalog.t("cert.problem.no_tests"),
                                                         catalog.t("cert.problem.no_code")]
    problems = validate_structure(Project.from_mapping("x", {"app/core/db.py": "", **MINIMAL_TESTS}), catalog)
    assert problems == [catalog.t("cert.problem.missing_init", package="app/core")]
    assert "app/core" in problems[0]


def test_the_tests_package_does_not_need_an_init(catalog_en: MessageCatalog) -> None:
    project = Project.from_mapping("x", {"main.py": "", "tests/test_x.py": ""})
    assert validate_structure(project, catalog_en) == []


def test_the_entrypoint_is_searched_in_the_code(books: BooksFactory) -> None:
    assert find_entrypoint(books()) == "app.main"
    assert find_entrypoint(Project.from_mapping("x", {"main.py": "def serve():\n    pass\n"})) == ""


# ── the chain, without spawning anything ─────────────────────────────────────

def test_an_incomplete_structure_stops_the_chain(certifier: ProjectCertifier, catalog_en: MessageCatalog) -> None:
    seen: list[Phase] = []
    project = Project.from_mapping("x", {"app/main.py": "x = 1\n"})
    certificate = certifier.certify(project, catalog_en, on_phase=seen.append)
    assert certificate.status is ProjectStatus.FAILED
    assert [p.name for p in seen] == ["structure"] and seen[0].status is FAILED
    assert certificate.markers == {} and certificate.project is project


def test_a_syntax_error_fails_before_running_anything(certifier: ProjectCertifier, catalog_en: MessageCatalog) -> None:
    project = Project.from_mapping("x", {"app/__init__.py": "", "app/main.py": "def broken(:\n", **MINIMAL_TESTS})
    certificate = certifier.certify(project, catalog_en)
    assert certificate.status is ProjectStatus.FAILED
    assert [(p.name, p.status) for p in certificate.phases] == [("structure", OK), ("syntax", FAILED)]


def test_a_broken_import_leaves_the_project_failed(certifier: ProjectCertifier, catalog_en: MessageCatalog) -> None:
    project = Project.from_mapping("x", {"app/__init__.py": "", "app/main.py": "from app.missing import x\n",
                                         **MINIMAL_TESTS})
    certificate = certifier.certify(project, catalog_en)
    assert certificate.status is ProjectStatus.FAILED
    assert certificate.phases[-1].name == "imports" and certificate.phases[-1].status is FAILED
    assert [f.kind for f in certificate.findings] == ["broken_internal_import"]


@pytest.mark.parametrize(("catalog_name", "words"), [("catalog_en", "no evidence"), ("catalog_es", "no hay evidencia")])
def test_a_missing_dependency_stops_at_validated_and_says_why(request: pytest.FixtureRequest, certifier: ProjectCertifier,
                                                             catalog_name: str, words: str) -> None:
    """A well-written FastAPI project is VALIDATED, never FAILED and never VERIFIED."""
    catalog: MessageCatalog = request.getfixturevalue(catalog_name)
    project = Project.from_mapping("api", {
        "app/__init__.py": "", "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "requirements.txt": "fastapi\n",
        "tests/__init__.py": "",
        "tests/test_x.py": "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n"})
    certificate = certifier.certify(project, catalog)
    assert certificate.status is ProjectStatus.VALIDATED, certificate.reason
    assert "fastapi" in certificate.reason and words in certificate.reason
    assert certificate.phases[-1].name == "execution" and certificate.phases[-1].status is LIMITED
    assert certificate.markers == {}


def test_a_repairer_that_changes_nothing_is_asked_once(certifier: ProjectCertifier, catalog_en: MessageCatalog) -> None:
    calls: list[int] = []

    def repairer(project: Project, errors: Sequence[Finding], output: str, attempt: int):
        calls.append(attempt)
        return project, (), "no idea"

    project = Project.from_mapping("x", {"app/__init__.py": "", "app/main.py": "from app.missing import x\n",
                                         **MINIMAL_TESTS})
    certificate = certifier.certify(project, catalog_en, repairer=repairer)
    assert calls == [1]
    assert certificate.status is ProjectStatus.FAILED
    assert certificate.repairs == ({"attempt": 1, "files": [], "cause": "no idea", "motive": "imports"},)


def test_repairs_are_capped(certifier: ProjectCertifier, catalog_en: MessageCatalog) -> None:
    """At most MAX_REPAIRS model calls, even when every answer "changes" something."""
    calls: list[int] = []

    def repairer(project: Project, errors: Sequence[Finding], output: str, attempt: int):
        calls.append(attempt)
        copy = project.copy()
        copy.add("app/noise.py", f"N = {attempt}\n")
        return copy, ("app/noise.py",), "still broken"

    project = Project.from_mapping("x", {"app/__init__.py": "", "app/main.py": "from app.missing import x\n",
                                         **MINIMAL_TESTS})
    certificate = certifier.certify(project, catalog_en, repairer=repairer)
    assert calls == list(range(1, MAX_REPAIRS + 1))
    assert certificate.status is ProjectStatus.FAILED
    assert certificate.project is not project, "the certificate carries the LAST project it looked at"


# ── the chain, for real ──────────────────────────────────────────────────────

@pytest.mark.slow
def test_the_demo_project_comes_out_verified(certifier: ProjectCertifier, books: BooksFactory,
                                             catalog_en: MessageCatalog) -> None:
    project = books().seal()
    certificate = certifier.certify(project, catalog_en, test_command=books_project.SPEC["test_command"])
    assert certificate.status is ProjectStatus.VERIFIED, certificate.reason
    assert certificate.passed >= 16 and certificate.failed == 0
    assert certificate.project is project, "no repair: the verified project is the one given"
    assert [p.name for p in certificate.phases] == ["structure", "syntax", "imports", "tests",
                                                    "documented_command", "crud"]
    assert all(p.status is OK for p in certificate.phases)


@pytest.mark.slow
def test_the_crud_is_exercised_over_http_with_this_runs_nonce(certifier: ProjectCertifier, books: BooksFactory,
                                                              catalog_en: MessageCatalog) -> None:
    first = certifier.certify(books(), catalog_en)
    second = certifier.certify(books(), catalog_en)
    nonces = []
    for certificate in (first, second):
        crud = {k: v for k, v in certificate.markers.items() if k.startswith("crud_")}
        assert len(crud) == 7 and set(crud.values()) == {"PASS"}, crud
        (nonce,) = {k.rsplit("_", 1)[1] for k in crud}
        assert re.fullmatch(r"[0-9a-f]{8}", nonce)
        assert set(crud) == set(probes.crud_ids(nonce))
        nonces.append(nonce)
        verified = [row for row in certificate.evidence if row.status.value == "verified"]
        assert {row.test_id for row in verified} == set(crud)
    assert nonces[0] != nonces[1], "the nonce must change on every run"


@pytest.mark.slow
def test_a_server_that_lies_is_caught(certifier: ProjectCertifier, books: BooksFactory,
                                      catalog_en: MessageCatalog) -> None:
    """The PUT answers 200 and does not persist. A complacent test would not see it."""
    original = books_project.FILES["app/books/repository.py"]
    update = ('"UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?",\n'
              '                                    (data["title"], data.get("author", ""), data.get("year"), book_id))')
    assert update in original, "the fixture changed: this test would prove nothing"
    lying = original.replace(update, '"SELECT 1 FROM books WHERE id = ?", (book_id,))')
    certificate = certifier.certify(books(replace={"app/books/repository.py": lying}), catalog_en)
    assert certificate.status is not ProjectStatus.VERIFIED
    persists = [k for k in certificate.markers if k.startswith("crud_persists_")]
    assert persists and certificate.markers[persists[0]] == "FAIL", certificate.markers


@pytest.mark.slow
def test_if_the_readme_command_fails_it_is_not_verified(certifier: ProjectCertifier, books: BooksFactory,
                                                        catalog_en: MessageCatalog) -> None:
    """It is the command whoever unzips the ZIP is going to type."""
    certificate = certifier.certify(books(), catalog_en, test_command="python3 does_not_exist.py")
    assert certificate.status is ProjectStatus.PARTIAL
    documented = next(p for p in certificate.phases if p.name == "documented_command")
    assert documented.status is FAILED and "does_not_exist.py" in documented.detail


@pytest.mark.slow
def test_the_repair_loop_is_wired_and_the_repaired_project_is_the_one_certified(
        certifier: ProjectCertifier, catalog_en: MessageCatalog) -> None:
    """It sat written and unconnected until a real run showed it. Checked by BEHAVIOUR: a
    grep of the source cannot tell "declared" from "connected"."""
    calls: list[tuple[int, int]] = []

    def repairer(project: Project, errors: Sequence[Finding], output: str, attempt: int):
        calls.append((len(errors), attempt))
        if attempt > 1:
            return project, (), "nothing else to fix"
        fixed = project.copy()
        fixed.add("app/broken.py", "def exists():\n    return 1\n")
        return fixed, ("app/broken.py",), "the module was missing"

    original = Project.from_mapping("x", {"app/__init__.py": "", "app/main.py": "from app.broken import exists\n",
                                          **MINIMAL_TESTS}).seal()
    certificate = certifier.certify(original, catalog_en, repairer=repairer)
    assert calls and calls[0] == (1, 1), "the repairer was not called: the loop is not connected"
    assert certificate.project is not original and certificate.project.get("app/broken.py") is not None
    assert original.get("app/broken.py") is None and original.sealed, "the sealed original was touched"
    assert certificate.repairs[0]["motive"] == "imports" and certificate.repairs[0]["files"] == ["app/broken.py"]
    assert not [f for f in certificate.findings if f.severity is Severity.ERROR], "the repair was not re-analysed"
    assert [p.name for p in certificate.phases][:4] == ["structure", "syntax", "imports", "repair:1"]


@pytest.mark.slow
def test_a_really_absent_dependency_ends_validated(real_certifier: ProjectCertifier, catalog_en: MessageCatalog) -> None:
    project = Project.from_mapping("api", {"app/__init__.py": "", "app/main.py": f"import {ABSENT}\n",
                                           "requirements.txt": f"{ABSENT}\n", **MINIMAL_TESTS})
    certificate = real_certifier.certify(project, catalog_en)
    assert certificate.status is ProjectStatus.VALIDATED, certificate.reason
    assert ABSENT in certificate.reason
