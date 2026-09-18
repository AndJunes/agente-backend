"""The harness Mirag writes: nonce ids, markers per test, never a silence, never injectable."""

from __future__ import annotations

import ast
import re

import pytest

from mirag.execution.runner import CodeRunner
from mirag.execution.verdict import ExecutionStatus
from mirag.offline import books_project
from mirag.projects import probes
from mirag.projects.packaging import FORBIDDEN

NONCE = re.compile(r"\A[0-9a-f]{8}\Z")


def probe_source(files: dict[str, str]) -> str:
    (source,) = files.values()
    return source


def test_every_nonce_is_fresh_hex() -> None:
    """The model cannot guess ``TEST:crud_create_<nonce>:PASS``, so it cannot fabricate it."""
    nonces = [probes.nonce() for _ in range(50)]
    assert all(NONCE.match(n) for n in nonces)
    assert len(set(nonces)) == 50


def test_the_crud_ids_carry_the_nonce_one_per_operation() -> None:
    ids = probes.crud_ids("a3f19c2b")
    assert ids == tuple(f"crud_{op}_a3f19c2b" for op in probes.OPERATIONS)
    assert len(ids) == 7 and "crud_persists_a3f19c2b" in ids


def test_the_crud_probe_embeds_exactly_this_runs_ids() -> None:
    first = probe_source(probes.crud_probe("app.main", "11111111"))
    second = probe_source(probes.crud_probe("app.main", "22222222"))
    assert all(i in first for i in probes.crud_ids("11111111"))
    assert "22222222" not in first and "11111111" not in second


@pytest.mark.parametrize("files", [
    probes.crud_probe("app.main", "abcd1234"),
    probes.crud_probe("my-api.main", "abcd1234", "/api/v1/books"),
    probes.tests_probe("tests", 3),
    probes.deps_probe(["fastapi", "uvicorn"]),
])
def test_every_probe_is_valid_python_and_named_as_a_probe(files: dict[str, str]) -> None:
    for name, source in files.items():
        assert name.startswith(probes.PROBE_PREFIX)
        compile(source, name, "exec")


def test_probe_files_can_never_enter_the_zip() -> None:
    """They are written only into the temporary execution folder."""
    for name in (*probes.crud_probe("app.main", "x"), *probes.tests_probe(), *probes.deps_probe([])):
        assert any(pattern.search(name) for pattern in FORBIDDEN), name


def test_the_crud_probe_uses_a_watchdog_not_sigalrm() -> None:
    """``signal.SIGALRM`` does not exist on Windows."""
    source = probe_source(probes.crud_probe("app.main", "abcd1234"))
    assert "SIGALRM" not in source and "threading.Timer" in source
    assert probes.PROBE_TIMEOUT_S < 30, "the probe must die before the runner and keep its output"


def test_the_crud_probe_checks_that_the_put_persists() -> None:
    """Not that a PUT handler exists: a GET after it must see the change."""
    source = probe_source(probes.crud_probe("app.main", "abcd1234", change={"title": "Changed"}))
    assert "after.get('title') == 'Changed'" in source


@pytest.mark.parametrize(("resource", "expected"), [
    ("/books", "/books"),
    ("books", "/books"),
    ("/books/", "/books"),
    ("/api/v1/authors", "/api/v1/authors"),
    ("", probes.DEFAULT_RESOURCE),
    (None, probes.DEFAULT_RESOURCE),
    ("/books/{id}", probes.DEFAULT_RESOURCE),
    ('/books", None); mark(0, True); x = ("', probes.DEFAULT_RESOURCE),
    ("/books\nimport os", probes.DEFAULT_RESOURCE),
])
def test_the_resource_is_validated(resource: object, expected: str) -> None:
    assert probes.safe_resource(resource) == expected


def test_a_hostile_resource_cannot_write_markers_into_the_probe() -> None:
    """The resource comes from the MODEL's spec. Pasted raw, this one was valid Python that
    printed PASS for every nonce id from inside Mirag's own probe."""
    hostile = '/books", None); [mark(i, True) for i in range(len(IDS))]; x = ("'
    source = probe_source(probes.crud_probe("app.main", "abcd1234", hostile))
    tree = ast.parse(source)
    constants = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert hostile not in source
    comprehensions = [n for n in ast.walk(tree) if isinstance(n, ast.ListComp)]
    assert not comprehensions, "code from the spec ended up in the probe"
    assert probes.DEFAULT_RESOURCE in constants


def test_the_entrypoint_is_embedded_as_a_literal() -> None:
    source = probe_source(probes.crud_probe("app.main", "abcd1234"))
    assert "ENTRYPOINT = 'app.main'" in source and "importlib.import_module(ENTRYPOINT)" in source


# ── executed for real ────────────────────────────────────────────────────────

@pytest.mark.slow
def test_zero_tests_is_not_passing(runner: CodeRunner) -> None:
    """An import that fails inside a silent try leaves 0 tests and exit 0. That is NOT passing."""
    files = {"tests/__init__.py": "",
             "tests/test_x.py": "try:\n    from app.nowhere import x\nexcept ImportError:\n    pass\n",
             **probes.tests_probe("tests")}
    result = runner.run(files, "python3 _probe_tests.py")
    assert result.status is ExecutionStatus.FAILED
    assert result.markers == {"test_coverage": "FAIL"}


@pytest.mark.slow
def test_the_tests_probe_emits_one_marker_per_test(runner: CodeRunner) -> None:
    files = {"tests/__init__.py": "",
             "tests/test_x.py": "import unittest\n\n\nclass T(unittest.TestCase):\n"
                                "    def test_ok(self):\n        pass\n\n"
                                "    def test_bad(self):\n        self.fail('no')\n",
             **probes.tests_probe("tests")}
    result = runner.run(files, "python3 _probe_tests.py")
    assert result.status is ExecutionStatus.FAILED
    assert sorted(result.markers.values()) == ["FAIL", "PASS"]
    assert any(k.endswith("test_ok") for k, v in result.markers.items() if v == "PASS")


@pytest.mark.slow
def test_a_project_without_create_server_fails_every_crud_marker(runner: CodeRunner) -> None:
    """If the contract is not met the probe says so with FAIL markers - never with a silence."""
    files = {"app/__init__.py": "", "app/main.py": "X = 1\n", **probes.crud_probe("app.main", "deadbeef")}
    result = runner.run(files, "python3 _probe_crud.py")
    assert result.status is ExecutionStatus.FAILED
    assert result.markers == {i: "FAIL" for i in probes.crud_ids("deadbeef")}


@pytest.mark.slow
def test_an_entrypoint_that_is_not_an_identifier_fails_with_markers(runner: CodeRunner) -> None:
    files = {"my-api/main.py": "X = 1\n", **probes.crud_probe("my-api.main", "deadbeef")}
    result = runner.run(files, "python3 _probe_crud.py")
    assert result.markers == {i: "FAIL" for i in probes.crud_ids("deadbeef")}


@pytest.mark.slow
def test_the_crud_probe_passes_against_the_demo_server(runner: CodeRunner) -> None:
    files = {**books_project.FILES, **probes.crud_probe("app.main", "c0ffee00")}
    result = runner.run(files, "python3 _probe_crud.py")
    assert result.status is ExecutionStatus.PASSED, result.text
    assert result.markers == {i: "PASS" for i in probes.crud_ids("c0ffee00")}


@pytest.mark.slow
def test_the_deps_probe_observes_instead_of_assuming(runner: CodeRunner) -> None:
    files = {**probes.deps_probe(["json", "surely_not_installed_mirag_probe_pkg"])}
    result = runner.run(files, "python3 _probe_deps.py")
    assert "DEP:json:INSTALLED" in result.text
    assert "DEP:surely_not_installed_mirag_probe_pkg:MISSING" in result.text
