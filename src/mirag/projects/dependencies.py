"""A broken import is not the same as a missing dependency. Here they are told apart.

WHY IT MATTERS SO MUCH
    If they are confused, both bad things happen at once: a perfectly written FastAPI project
    looks broken, and the repair loop starts "fixing" imports that were fine. And the other
    way round, ``from app.books.repo import BookRepo`` against a file that defines
    ``RepoBooks`` would slip through as "it will work once something is installed".

        internal import that does not resolve  -> project ERROR. It gets repaired.
        missing external dependency            -> LIMIT of this machine. NOT an error.
                                                  It caps the status, it does not sink it.

    Everything with ``ast`` and the standard library. Zero model calls, zero cost.

A DETAIL THAT TOOK TIME TO FIND
    The interpreter Mirag uses to RUN the code is not necessarily the one running Mirag. So
    the presence of a dependency is observed in the real interpreter, in a subprocess.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from mirag.execution.interpreters import InterpreterRegistry
from mirag.projects.model import Project, ProjectFile


class Severity(StrEnum):
    ERROR = "error"
    """The project is wrong."""
    LIMIT = "limit"
    """This machine cannot check it; the project may be fine."""
    NOTICE = "notice"
    """Worth knowing, does not block."""


@dataclass(frozen=True, slots=True)
class ImportRecord:
    file: str
    line: int
    module: str
    names: tuple[str, ...]
    level: int
    kind: str
    """``internal`` | ``stdlib`` | ``external``."""


@dataclass(frozen=True, slots=True)
class Finding:
    kind: str
    """``broken_internal_import`` | ``missing_symbol`` | ``missing_dependency`` | ``undeclared_dependency``."""
    severity: Severity
    file: str
    line: int
    detail: str
    subject: str = ""
    """The module or package the finding is about."""


def _target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Tuple | ast.List):
        return {name for element in target.elts for name in _target_names(element)}
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    return set()


def _bound_names(body: Sequence[ast.stmt]) -> set[str]:
    """The names a block binds at module level.

    Imports bind names too: ``from app.main import create_server`` in ``app/__init__.py`` is
    exactly the re-export a repair adds, and ignoring it reported the fix itself as a
    ``missing_symbol`` ERROR. Compound statements are entered (``try: from x import y`` /
    ``except ImportError: y = None`` defines ``y`` either way); functions and classes are not,
    their inner names are not module attributes.
    """
    names: set[str] = set()
    for node in body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                names |= _target_names(target)
        elif isinstance(node, ast.AnnAssign | ast.AugAssign):
            names |= _target_names(node.target)
        elif isinstance(node, ast.Import):
            names |= {alias.asname or alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            names |= {alias.asname or alias.name for alias in node.names if alias.name != "*"}
        elif isinstance(node, ast.For | ast.AsyncFor):
            names |= _target_names(node.target) | _bound_names(node.body) | _bound_names(node.orelse)
        elif isinstance(node, ast.While | ast.If):
            names |= _bound_names(node.body) | _bound_names(node.orelse)
        elif isinstance(node, ast.With | ast.AsyncWith):
            for item in node.items:
                if item.optional_vars is not None:
                    names |= _target_names(item.optional_vars)
            names |= _bound_names(node.body)
        elif isinstance(node, ast.Try | ast.TryStar):
            names |= _bound_names(node.body) | _bound_names(node.orelse) | _bound_names(node.finalbody)
            for handler in node.handlers:
                names |= _bound_names(handler.body)
    return names


def exported_names(source: str) -> frozenset[str]:
    """What a module REALLY defines, read from the AST. Not what the manifest promises."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return frozenset()
    return frozenset(_bound_names(tree.body))


def has_module_getattr(source: str) -> bool:
    """PEP 562: a module-level ``__getattr__`` can create symbols at runtime. With it,
    "the symbol is not in the AST" stops being proof that it does not exist."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    return any(isinstance(n, ast.FunctionDef) and n.name == "__getattr__" for n in tree.body)


def has_star_import(source: str) -> bool:
    """``from x import *`` binds names the source never spells: same consequence as above."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    return any(isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names) for n in ast.walk(tree))


def worst(findings: Iterable[Finding]) -> Severity | None:
    findings = list(findings)
    if any(f.severity is Severity.ERROR for f in findings):
        return Severity.ERROR
    if any(f.severity is Severity.LIMIT for f in findings):
        return Severity.LIMIT
    return Severity.NOTICE if findings else None


ProbeArgv = Callable[[str, str], list[str]]
"""``(script, dependencies) -> argv``. The second argument names the Docker volume of
installed packages the probe must be able to import, or ``""`` for "ask about the bare
interpreter"."""


class DependencyAnalyzer:
    def __init__(self, interpreters: InterpreterRegistry,
                 probe_argv: ProbeArgv | None = None) -> None:
        self._interpreters = interpreters
        # Not routed through a `CodeExecutionBackend`: this check runs UNCONDITIONALLY, even
        # with execution switched off, because "is this importable here" is a fact independent
        # of whether the agent is allowed to run the project's own tests. `runner.run()` would
        # short-circuit to `not_executed` the moment `enabled` is `False`, which would silently
        # turn every accurate answer here into "could not be observed". `probe_argv` still lets
        # the docker backend point this at the SAME interpreter its tests actually run against,
        # without adopting the runner's enabled-gating.
        self._probe_argv = probe_argv or self._host_probe_argv

    def _host_probe_argv(self, script: str, dependencies: str = "") -> list[str]:
        # Ignored: a volume name means nothing to a host interpreter, and the host backend is
        # never wired to an installer, so this is always "". See `projects/installation.py`.
        del dependencies
        return [self._interpreters.resolve("python3") or sys.executable, "-c", script]

    @staticmethod
    def module_map(project: Project) -> dict[str, str]:
        """``{"app.books.repo": "app/books/repo.py"}`` plus the intermediate packages."""
        mapping: dict[str, str] = {}
        packages: set[str] = set()
        for file in project.files():
            if not file.module:
                continue
            mapping[file.module] = file.path
            parts = file.module.split(".")
            if parts[-1] == "__init__":
                mapping[".".join(parts[:-1])] = file.path
                parts = parts[:-1]
            for i in range(1, len(parts)):
                packages.add(".".join(parts[:i]))
        for package in packages:
            mapping.setdefault(package, "")  # implicit package, without its own __init__.py
        return mapping

    def imports(self, project: Project) -> tuple[ImportRecord, ...]:
        """Every import of the project, classified. Also the ones inside functions."""
        mapping = self.module_map(project)
        out: list[ImportRecord] = []
        for file in project.files():
            if not file.path.endswith(".py"):
                continue
            try:
                tree = ast.parse(file.text)
            except SyntaxError:
                continue  # syntax is judged by another phase, not this one
            package = ".".join(file.module.split(".")[:-1])
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        out.append(self._classify(file, node.lineno, alias.name, (), 0, mapping))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if node.level:  # relative: resolved against its package
                        base = package.split(".")[: len(package.split(".")) - (node.level - 1)]
                        module = ".".join([p for p in base if p] + ([module] if module else []))
                    names = tuple(a.name for a in node.names)
                    out.append(self._classify(file, node.lineno, module, names, node.level, mapping))
        return tuple(out)

    @staticmethod
    def _classify(file: ProjectFile, line: int, module: str, names: tuple[str, ...],
                  level: int, mapping: dict[str, str]) -> ImportRecord:
        root = module.split(".")[0] if module else ""
        # A relative import is internal by definition: `from .helpers import x` in a top-level
        # file used to be taken for a missing PACKAGE called 'helpers' - a LIMIT - when it is
        # an import of this project that does not resolve.
        if level or module in mapping or (root and root in mapping):
            kind = "internal"
        elif root in sys.stdlib_module_names:
            kind = "stdlib"
        else:
            kind = "external"
        return ImportRecord(file.path, line, module, names, level, kind)

    def installed(self, roots: Iterable[str], dependencies: str = "") -> dict[str, bool | None]:
        """Are they installed IN THE INTERPRETER MIRAG RUNS CODE WITH? Observed, not assumed.
        ``None`` means it could not be observed.

        ``dependencies`` names the volume of packages just installed for this project. It is
        what turns "``fastapi`` is not installed on this machine" into an answer that can
        change within one run, which is the entire point of installing anything.
        """
        names = sorted({r for r in roots if r})
        if not names:
            return {}
        script = ("import importlib.util as u\n"
                  f"for m in {names!r}:\n"
                  "    print(m, u.find_spec(m) is not None, flush=True)\n")
        try:
            completed = subprocess.run(self._probe_argv(script, dependencies),
                                       capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=20, check=False)
        except (OSError, subprocess.SubprocessError):
            return {n: None for n in names}
        seen: dict[str, bool] = {}
        for line in completed.stdout.splitlines():
            parts = line.split()
            if len(parts) == 2:
                seen[parts[0]] = parts[1] == "True"
        return {n: seen.get(n) for n in names}

    @staticmethod
    def declared(project: Project) -> frozenset[str]:
        """The dependencies the project itself says it needs (``requirements.txt``)."""
        file = project.get("requirements.txt")
        if not file:
            return frozenset()
        names: set[str] = set()
        for line in file.text.splitlines():
            clean = line.split("#")[0].strip()
            if clean and not clean.startswith("-"):
                for sep in ("[", "=", ">", "<", "~"):
                    clean = clean.split(sep)[0]
                names.add(clean.strip().lower().replace("-", "_"))
        return frozenset(names)

    def analyze(self, project: Project,
                dependencies: str = "") -> tuple[tuple[ImportRecord, ...], tuple[Finding, ...]]:
        """``(imports, findings)``. The findings carry the severity that decides the status.

        Run a second time with ``dependencies`` after an install, and the
        ``missing_dependency`` LIMITs that capped the project simply are not produced: the
        analysis is the same, the interpreter's answer is what changed.
        """
        imports = self.imports(project)
        mapping = self.module_map(project)
        by_path = {f.path: f for f in project.files()}
        external_roots = {i.module.split(".")[0] for i in imports if i.kind == "external"}
        present = self.installed(external_roots, dependencies)
        declared = self.declared(project)
        findings: list[Finding] = []

        for record in imports:
            if record.kind == "internal":
                target = mapping.get(record.module)
                if target is None:
                    findings.append(Finding("broken_internal_import", Severity.ERROR, record.file, record.line,
                                            f"imports {record.module!r} and that module does not exist in the project",
                                            record.module))
                    continue
                if record.names and target:
                    source = by_path.get(target)
                    if source and not has_module_getattr(source.text) and not has_star_import(source.text):
                        defined = exported_names(source.text)
                        missing = [n for n in record.names
                                   if n != "*" and n not in defined and n not in mapping
                                   and f"{record.module}.{n}" not in mapping]
                        if missing:
                            findings.append(Finding("missing_symbol", Severity.ERROR, record.file, record.line,
                                                    f"{target} does not define {', '.join(missing)}", record.module))
            elif record.kind == "external":
                root = record.module.split(".")[0]
                if present.get(root) is False:
                    findings.append(Finding("missing_dependency", Severity.LIMIT, record.file, record.line,
                                            f"{root!r} is not installed on this machine. The code may be fine; "
                                            "here there is no way to check it.", root))
                if root.lower().replace("-", "_") not in declared:
                    findings.append(Finding("undeclared_dependency", Severity.NOTICE, record.file, record.line,
                                            f"uses {root!r} and it is not in requirements.txt", root))
        unique: list[Finding] = []
        seen: set[tuple[str, str, str]] = set()
        for finding in findings:
            key = (finding.kind, finding.file, finding.detail)
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        return imports, tuple(unique)

    def reached_from(self, project: Project, seeds: Iterable[str], depth: int = 3) -> list[str]:
        """The files ``seeds`` can reach through internal imports, seeds included.

        This is what the repairer needed and did not have. A failing test names the TEST file;
        the bug is almost always in the code that test exercises, and the import graph is the
        only thing that knows which code that is. Measured on a real failure: a test in
        `tests/test_plantas_crud.py` reaches `plantas/service.py` → `plantas/repository.py` →
        `shared/database.py`, and the last of those was the one file that had to change.

        Without it, file selection was a substring search over a truncated log and resolved to
        the test file alone — the model was handed the symptom and asked for the cause.

        ``depth`` is bounded because a project with a shared `errors` module reaches most of
        itself in a few hops, and a prompt holding every file is the same as a prompt holding
        none. Three is enough for entrypoint → service → repository → storage.
        """
        edges: dict[str, set[str]] = {}
        mapping = self.module_map(project)
        for record in self.imports(project):
            if record.kind != "internal":
                continue
            target = mapping.get(record.module)
            if target and target != record.file:
                edges.setdefault(record.file, set()).add(target)

        seen = {seed for seed in seeds if project.get(seed) is not None}
        frontier = set(seen)
        for _ in range(depth):
            nxt = {target for path in frontier for target in edges.get(path, ())} - seen
            if not nxt:
                break
            seen |= nxt
            frontier = nxt
        return sorted(seen)

    @staticmethod
    def of_severity(findings: Sequence[Finding], severity: Severity) -> list[Finding]:
        return [f for f in findings if f.severity is severity]
