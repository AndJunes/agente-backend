"""The artifact: where a path is born, the caps, sealing, and where it may be written."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from mirag.core.errors import ForbiddenDestinationError, ForbiddenPathError, SealedProjectError
from mirag.execution.runner import CodeRunner
from mirag.execution.verdict import ExecutionStatus
from mirag.offline import books_project
from mirag.paths import PACKAGE_ROOT
from mirag.projects import model
from mirag.projects.model import (
    MAX_DEPTH,
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_PATH,
    MAX_TOTAL_BYTES,
    Project,
    mirag_root,
    safe_name,
    safe_path,
)

from .conftest import BooksFactory

# ── paths: the only place a path is born ─────────────────────────────────────

ATTACKS = [
    "../../etc/passwd",
    "/etc/passwd",
    "app/../../outside.py",
    "~/x.py",
    "C:\\Windows\\x.py",
    "c:/x.py",
    "\\\\server\\share\\x.py",
    "app/../../../root/.ssh/id_rsa",
    "__pycache__/x.pyc",
    "app/__pycache__/main.py",
    ".env",
    "app/.env",
    ".git/config",
    "node_modules/bad.js",
    "venv/x.py",
    ".venv/x.py",
    ".DS_Store",
    "app/.hidden.py",
    "app/x.exe",
    "app/my file.py",
    "app/-dash.py",
    "a/b/c/d/e/f/g/h.py",
    "app/" + "x" * MAX_PATH + ".py",
    "",
    "   ",
    "app/x\x00.py",
    "app//..//y.py",
    "app/",
]


@pytest.mark.parametrize("path", ATTACKS)
def test_no_hostile_path_is_ever_accepted(path: str) -> None:
    """If a single one passes, the model can write wherever it wants."""
    with pytest.raises(ForbiddenPathError):
        safe_path(path)


@pytest.mark.parametrize("value", [None, 42, b"app/main.py", ["app/main.py"]])
def test_a_path_that_is_not_text_is_rejected(value: object) -> None:
    with pytest.raises(ForbiddenPathError):
        safe_path(value)


@pytest.mark.parametrize("path", ["app/main.py", "app/books/router.py", "tests/test_x.py", "README.md",
                                  "requirements.txt", ".env.example", ".gitignore", "app/__init__.py"])
def test_ordinary_paths_pass_unchanged(path: str) -> None:
    assert safe_path(path) == path


def test_backslashes_are_normalised_to_forward_slashes() -> None:
    assert safe_path("app\\books\\router.py") == "app/books/router.py"


def test_the_depth_cap_is_exactly_the_cap() -> None:
    deepest = "/".join(["d"] * (MAX_DEPTH - 1)) + "/x.py"
    assert safe_path(deepest) == deepest
    with pytest.raises(ForbiddenPathError):
        safe_path("d/" + deepest)


def test_the_error_is_also_a_value_error() -> None:
    """Callers that guard with ``except ValueError`` must not let a hostile path through."""
    assert issubclass(ForbiddenPathError, ValueError)


def test_adding_a_bad_path_raises_and_leaves_nothing_inside() -> None:
    project = Project("x")
    for path in ("../outside.py", "/etc/passwd", ".env"):
        with pytest.raises(ForbiddenPathError):
            project.add(path, "x = 1")
    assert project.files() == ()


def test_adding_stays_strict_even_though_reading_is_tolerant() -> None:
    with pytest.raises(ForbiddenPathError):
        Project("x").add("app/books/api", "x = 1")


@pytest.mark.parametrize("path", ["app/books/api", "../outside", ".env", "", "x" * 300, "app/../../x.py"])
def test_reading_an_impossible_path_never_raises(books: BooksFactory, path: str) -> None:
    """When ``get`` raised, a dependency declared without extension by the model
    (``depends_on: ["app/books/api"]``) blew the whole generation up."""
    assert books().get(path) is None


# ── caps ─────────────────────────────────────────────────────────────────────

def test_a_file_over_the_size_cap_is_rejected() -> None:
    project = Project("x")
    with pytest.raises(ForbiddenPathError):
        project.add("big.py", "x" * (MAX_FILE_BYTES + 1))
    assert project.files() == ()


def test_the_file_count_cap_bites() -> None:
    project = Project("x")
    for i in range(MAX_FILES):
        project.add(f"m{i}.py", "")
    with pytest.raises(ForbiddenPathError):
        project.add("one_too_many.py", "")
    assert len(project.files()) == MAX_FILES


def test_the_total_size_cap_bites_and_the_rejected_add_changes_nothing() -> None:
    project = Project("x")
    chunk = MAX_FILE_BYTES - 1
    added = 0
    while (added + 1) * chunk <= MAX_TOTAL_BYTES:
        project.add(f"m{added}.py", "x" * chunk)
        added += 1
    before = project.paths()
    with pytest.raises(ForbiddenPathError):
        project.add("overflow.py", "x" * chunk)
    assert project.paths() == before


# ── names ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("raw", "clean"), [
    ("Books API!!", "books-api"),
    ("../../etc", "etc"),
    ('a"b\r\nc', "a-b-c"),
    ("", "project"),
    (None, "project"),
    ("...", "project"),
    ("Ñandú App", "nandu-app"),
])
def test_the_project_name_is_sanitised(raw: object, clean: str) -> None:
    assert safe_name(raw) == clean


@pytest.mark.parametrize("raw", ['x"\r\nSet-Cookie: a=b', "x\nY", 'a"b', "a/b\\c", "a" * 47 + ".b", "a" * 47 + "-b"])
def test_a_hostile_name_cannot_split_a_header_nor_make_a_bad_folder(raw: str) -> None:
    """A ``\\r\\n`` in Content-Disposition injects headers; a trailing '.' is dropped by
    Windows, so the folder on disk would not be the folder in the ZIP."""
    clean = safe_name(raw)
    assert not set(clean) & set('\r\n"/\\')
    assert len(clean) <= 48
    assert not clean.startswith(("-", ".", "_")) and not clean.endswith(("-", ".", "_"))


# ── the artifact ─────────────────────────────────────────────────────────────

def test_implicit_directories_appear_in_the_tree(books: BooksFactory) -> None:
    project = books()
    tree = project.tree()
    assert "app/" in tree and "tests/" in tree
    assert "core/" in tree["app/"] and "books/" in tree["app/"]
    assert project.totals["directories"] == 4
    assert project.totals["files"] == len(books_project.FILES)


def test_file_kinds_filter() -> None:
    project = Project("x")
    project.add("app/main.py", "", kind="entrypoint")
    project.add("tests/test_x.py", "", kind="test")
    assert [f.path for f in project.files("test")] == ["tests/test_x.py"]
    assert [f.path for f in project.files("entrypoint")] == ["app/main.py"]


def test_the_module_name_follows_the_path() -> None:
    project = Project.from_mapping("x", {"app/books/repository.py": "", "README.md": ""})
    assert project.get("app/books/repository.py").module == "app.books.repository"
    assert project.get("README.md").module == ""


def test_the_hash_is_complete_and_over_the_exact_bytes(books: BooksFactory) -> None:
    """Here the hash is the PROOF of identity, not a change detector: never truncated."""
    for file in books().files():
        assert len(file.sha256) == 64
        assert file.sha256 == hashlib.sha256(file.data).hexdigest()
        assert file.data == books_project.FILES[file.path].encode("utf-8")


def test_sealing_freezes_the_tree(books: BooksFactory) -> None:
    """What is verified has to be what is packaged."""
    project = books().seal()
    assert project.sealed
    with pytest.raises(SealedProjectError):
        project.add("new.py", "x = 1")
    with pytest.raises(RuntimeError):  # the historical contract: it is a RuntimeError too
        project.add("app/main.py", "x = 1")
    assert project.get("new.py") is None


def test_a_copy_of_a_sealed_project_is_unsealed_and_independent(books: BooksFactory) -> None:
    original = books().seal()
    clone = original.copy()
    clone.add("app/extra.py", "x = 1")
    assert not clone.sealed and original.sealed
    assert original.get("app/extra.py") is None
    assert clone.name == original.name and clone.spec == original.spec


def test_as_text_mapping_is_exactly_what_the_runner_consumes(books: BooksFactory) -> None:
    assert books().as_text_mapping() == books_project.FILES


@pytest.mark.slow
def test_the_text_mapping_really_runs(books: BooksFactory, runner: CodeRunner) -> None:
    result = runner.run(books().as_text_mapping(), "python3 -c \"import app.main; print('TEST:imports:PASS')\"")
    assert result.status is ExecutionStatus.PASSED, result.text


# ── to disk ──────────────────────────────────────────────────────────────────

def test_materialize_keeps_the_subdirectories_and_the_exact_bytes(books: BooksFactory, tmp_path: Path) -> None:
    """The single-file writer flattens with ``Path(path).name``: a project never goes there.
    And bytes, never write_text: on Windows it would turn every ``\\n`` into ``\\r\\n``."""
    destination = books().materialize(tmp_path / "out")
    assert (destination / "app" / "books" / "router.py").is_file()
    assert (destination / "tests" / "test_books.py").is_file()
    assert len(list(destination.rglob("*.py"))) == 11
    for path, text in books_project.FILES.items():
        assert (destination / path).read_bytes() == text.encode("utf-8"), path


def test_a_project_is_never_written_inside_a_protected_root(books: BooksFactory, tmp_path: Path) -> None:
    protected = tmp_path / "mirag"
    protected.mkdir()
    project = books()
    for destination in (protected, protected / "output", protected / "benchmarks",
                        tmp_path / "elsewhere" / ".." / "mirag" / "sneaky"):
        with pytest.raises(ForbiddenDestinationError):
            project.materialize(destination, protected_root=protected)
    assert sorted(p.name for p in protected.iterdir()) == [], "something was written before refusing"


def test_the_artifacts_area_and_the_outside_are_allowed(books: BooksFactory, tmp_path: Path) -> None:
    protected = tmp_path / "mirag"
    area = protected / "var" / "artifacts"
    inside_area = books().materialize(area / ("a" * 24) / "project", protected_root=protected, allowed_area=area)
    outside = books().materialize(tmp_path / "elsewhere", protected_root=protected)
    assert (inside_area / "app" / "main.py").is_file()
    assert (outside / "app" / "main.py").is_file()


def test_mirag_itself_is_protected_without_being_asked(books: BooksFactory) -> None:
    """The guard used to depend on the caller passing ``protected_root``, and the only caller
    did not: "never on top of Mirag" was opt-in. Now Mirag's own tree is always protected."""
    assert PACKAGE_ROOT.resolve().is_relative_to(mirag_root().resolve())
    project = books()
    targets = [PACKAGE_ROOT, PACKAGE_ROOT / "projects", mirag_root(), mirag_root() / "var" / "output",
               PACKAGE_ROOT / "_never_created_by_tests_"]
    try:
        for destination in targets:
            with pytest.raises(ForbiddenDestinationError):
                project.materialize(destination)
    finally:  # if the guard ever breaks, do not leave a project inside the package
        shutil.rmtree(PACKAGE_ROOT / "_never_created_by_tests_", ignore_errors=True)
    assert not (PACKAGE_ROOT / "projects" / "app").exists()


def test_the_default_root_is_the_checkout_or_the_package() -> None:
    assert model.mirag_root() in (model.source_checkout_root(), PACKAGE_ROOT)
