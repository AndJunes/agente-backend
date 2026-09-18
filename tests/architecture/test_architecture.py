"""Architecture rules, checked on the real source with ``ast`` on every run.

A rule that lives only in a document stops being true the day nobody reads the document.
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from mirag.paths import PACKAGE_ROOT

REPO_ROOT = PACKAGE_ROOT.parent.parent
CORE_EXCLUDED = ("integrations", "experimental")
LAYERS_BELOW_APPLICATION = ("core", "i18n", "llm", "features", "retrieval", "execution", "evidence", "tools",
                            "projects")


def modules(root: Path = PACKAGE_ROOT) -> Iterator[Path]:
    yield from (p for p in sorted(root.rglob("*.py")) if "__pycache__" not in p.parts)


def package_of(path: Path) -> str:
    return path.relative_to(PACKAGE_ROOT).parts[0]


def imported_modules(path: Path, top_level_only: bool = False) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = tree.body if top_level_only else list(ast.walk(tree))
    found: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module)
    return found


def test_the_core_has_no_third_party_dependency() -> None:
    offenders = {}
    for path in modules():
        if package_of(path) in CORE_EXCLUDED:
            continue
        third_party = {m for m in imported_modules(path)
                       if m.split(".")[0] not in sys.stdlib_module_names and m.split(".")[0] != "mirag"}
        if third_party:
            offenders[str(path.relative_to(PACKAGE_ROOT))] = sorted(third_party)
    assert not offenders


def test_production_never_imports_the_experimental_package() -> None:
    offenders = [str(p.relative_to(PACKAGE_ROOT)) for p in modules()
                 if package_of(p) != "experimental"
                 and any(m.startswith("mirag.experimental") for m in imported_modules(p))]
    assert not offenders


def test_the_blockchain_layer_is_only_imported_lazily_by_the_container() -> None:
    """A top-level import would tie the start-up of Mirag to an optional package."""
    importers = {str(p.relative_to(PACKAGE_ROOT)) for p in modules()
                 if package_of(p) != "integrations"
                 and any(m.startswith("mirag.integrations") for m in imported_modules(p))}
    assert importers <= {"container.py"}
    top_level = imported_modules(PACKAGE_ROOT / "container.py", top_level_only=True)
    assert not any(m.startswith("mirag.integrations") for m in top_level)


@pytest.mark.parametrize("layer", LAYERS_BELOW_APPLICATION)
def test_lower_layers_never_import_the_application_layers(layer: str) -> None:
    """Dependencies point inwards: the domain does not know the HTTP server, the container,
    the CLI, the pipeline orchestration or the presentation."""
    forbidden = ("mirag.api", "mirag.container", "mirag.cli", "mirag.pipeline", "mirag.presentation",
                 "mirag.offline", "mirag.agent", "mirag.self_knowledge")
    offenders = {}
    for path in modules(PACKAGE_ROOT / layer):
        bad = {m for m in imported_modules(path) if m.startswith(forbidden)}
        if bad:
            offenders[str(path.relative_to(PACKAGE_ROOT))] = sorted(bad)
    assert not offenders


def test_the_core_package_depends_on_nothing_else_in_mirag() -> None:
    for path in modules(PACKAGE_ROOT / "core"):
        internal = {m for m in imported_modules(path) if m.startswith("mirag.")}
        assert internal <= {"mirag.paths", "mirag.core.errors", "mirag.core.text", "mirag.core.timing"}, path


def test_only_settings_reads_the_process_environment() -> None:
    """Services receive Settings; nobody else reads os.environ (the blockchain lock is the
    documented exception: it is re-read on every call)."""
    allowed = {"core/settings.py", "execution/runner.py"}
    offenders = []
    for path in modules():
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        if relative in allowed or package_of(path) in CORE_EXCLUDED:
            continue
        if "os.environ" in path.read_text(encoding="utf-8"):
            offenders.append(relative)
    assert not offenders


def test_text_files_are_always_opened_with_an_explicit_encoding() -> None:
    """On Windows the default codec is not UTF-8: the legacy suites died with
    UnicodeDecodeError before running a single case."""
    offenders = []
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("read_text", "write_text")
                    and not any(k.arg == "encoding" for k in node.keywords)):
                offenders.append(f"{path.relative_to(PACKAGE_ROOT)}:{node.lineno}")
    assert not offenders


def test_library_code_does_not_print() -> None:
    allowed = {"cli.py", "api/server.py"}
    offenders = []
    for path in modules():
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        if relative in allowed or package_of(path) in CORE_EXCLUDED:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print"
               for n in ast.walk(tree)):
            offenders.append(relative)
    assert not offenders


def test_there_is_no_eval_or_exec_in_the_package() -> None:
    offenders = []
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders += [f"{path.relative_to(PACKAGE_ROOT)}:{n.lineno}" for n in ast.walk(tree)
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("eval", "exec")]
    assert not offenders


def test_the_identifiers_of_the_package_are_in_english() -> None:
    """The restructure translated the code base: no Spanish identifier may come back."""
    spanish = {"pregunta", "respuesta", "trozo", "caja", "ejecutar", "recuperar", "evidencia", "proyecto",
               "archivos", "salida", "entrega", "presupuesto", "guion", "doble", "verificar", "estado"}
    offenders = []
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            name = getattr(node, "name", None) or (node.id if isinstance(node, ast.Name) else None)
            if isinstance(name, str) and any(part in spanish for part in name.lower().split("_")):
                offenders.append(f"{path.relative_to(PACKAGE_ROOT)}:{getattr(node, 'lineno', '?')} {name}")
    assert not offenders


def test_the_repository_follows_the_standard_layout() -> None:
    for required in ("pyproject.toml", "README.md", "src/mirag/__init__.py", "tests/conftest.py",
                     "docs/en", "docs/es", "src/mirag/locales/en", "src/mirag/locales/es",
                     "src/mirag/knowledge/en", "src/mirag/knowledge/es"):
        assert (REPO_ROOT / required).exists(), required
    legacy = [p.name for p in REPO_ROOT.glob("*.py")]
    assert not legacy, f"loose modules at the repository root: {legacy}"


def test_benchmarks_write_where_production_reads() -> None:
    """The gate reads the measured gains from the package resources; that file must exist."""
    from mirag.paths import FEATURE_GAINS_FILE

    assert FEATURE_GAINS_FILE.is_file()
    assert FEATURE_GAINS_FILE.is_relative_to(PACKAGE_ROOT)
