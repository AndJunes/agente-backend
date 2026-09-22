"""The chain that turns a generated project into a project with evidence.

THE ONLY PLACE THAT DECIDES THE STATUS
    :meth:`StatusDeriver.derive` is the only function that returns these statuses, and it
    receives nothing from the model: phases, markers and findings. It is deliberate.

THE DISTINCTION THAT HOLDS EVERYTHING UP
    A missing external dependency does NOT sink the status: it puts a CEILING on it. A
    well-written FastAPI project stays VALIDATED and says why, instead of being called FAILED.
    A broken internal import IS an error, and it is repaired.
"""

from __future__ import annotations

import re

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from mirag.core.timing import Stopwatch
from mirag.evidence.properties import EvidenceBuilder, EvidenceRow
from mirag.execution.runner import CodeRunner
from mirag.execution.syntax import SyntaxChecker
from mirag.execution.verdict import ExecutionResult, ExecutionStatus
from mirag.i18n.catalog import MessageCatalog
from mirag.projects import probes
from mirag.projects.dependencies import DependencyAnalyzer, Finding, Severity
from mirag.projects.model import Project

MAX_REPAIRS = 2
"""A single file allows 1; a project has more surface."""


class ProjectStatus(StrEnum):
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    EXECUTED = "EXECUTED"
    TESTED = "TESTED"
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class PhaseStatus(StrEnum):
    OK = "ok"
    FAILED = "failed"
    LIMITED = "limited"
    SKIPPED = "skipped"


_FROM_EXECUTION = {ExecutionStatus.PASSED: PhaseStatus.OK, ExecutionStatus.FAILED: PhaseStatus.FAILED}


@dataclass(frozen=True, slots=True)
class Phase:
    name: str
    status: PhaseStatus
    detail: str
    ms: float = 0.0
    output: str = ""
    """The RAW output when it executed something."""


@dataclass(frozen=True, slots=True)
class Certificate:
    status: ProjectStatus
    reason: str
    phases: tuple[Phase, ...]
    findings: tuple[Finding, ...]
    markers: dict[str, str]
    evidence: tuple[EvidenceRow, ...] = ()
    repairs: tuple[dict[str, Any], ...] = ()
    interpreter: str = ""
    project: Project | None = field(default=None, compare=False)
    """The (possibly repaired) project that was really verified."""

    @property
    def ok(self) -> bool:
        return self.status is ProjectStatus.VERIFIED

    @property
    def passed(self) -> int:
        return sum(1 for v in self.markers.values() if v == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for v in self.markers.values() if v == "FAIL")


Repairer = Callable[[Project, Sequence[Finding], str, int], tuple[Project, tuple[str, ...], str]]
"""``(project, errors, output, attempt) -> (new project, changed paths, cause)``. ONE type:
the generator builds it and the certifier calls it."""

PhaseListener = Callable[[Phase], None]


def validate_structure(project: Project, catalog: MessageCatalog) -> list[str]:
    """What must exist for the rest to mean anything."""
    problems = []
    files = project.files()
    if not files:
        problems.append(catalog.t("cert.problem.no_files"))
    if not any(f.path.startswith("tests/") or "test" in f.path.split("/")[-1] for f in files):
        problems.append(catalog.t("cert.problem.no_tests"))
    if not any(f.path.endswith((".py", ".js")) for f in files):
        problems.append(catalog.t("cert.problem.no_code"))
    # Python packages without __init__.py: it works from the root and fails elsewhere
    packages = {"/".join(f.path.split("/")[:-1]) for f in files if f.path.endswith(".py") and "/" in f.path}
    for package in sorted(packages):
        if package.startswith("tests"):
            continue
        if not project.get(f"{package}/__init__.py"):
            problems.append(catalog.t("cert.problem.missing_init", package=package))
    return problems


ENTRYPOINT_NAMES = ("create_server", "crear_servidor", "create_app", "crear_app", "make_server")
ENTRYPOINT = re.compile(r"^\s*(?:async\s+)?def\s+(" + "|".join(ENTRYPOINT_NAMES) + r")\s*\(", re.MULTILINE)
"""What the CRUD probe imports and calls.

The contract asks for `create_server` in English, and the language directive simultaneously
pushes the model towards the user's language — a real run produced `crear_servidor`. When the
substring search missed, `crud` was SKIPPED, no markers existed, and the project topped out at
GENERATED with nothing anywhere saying why. Accepting the handful of names a model actually
writes costs nothing; the probe calls whichever one it found."""


def find_entrypoint(project: Project) -> tuple[str, str]:
    """``(module, function)`` of the server factory, or ``("", "")``.

    Searched in the code, not assumed — and matched as a definition rather than as a
    substring, so a mention in a docstring or a README does not count as one. The file the
    blueprint declared as the entrypoint is asked first: a test module that happens to define
    a `create_app` helper would otherwise be imported and started as if it were the server."""
    entrypoints = project.files("entrypoint")
    rest = (f for f in project.files() if f not in entrypoints and not f.path.startswith("tests"))
    for file in (*entrypoints, *rest):
        if not file.path.endswith(".py"):
            continue
        if found := ENTRYPOINT.search(file.text):
            return file.module, found.group(1)
    return "", ""


class StatusDeriver:
    """Derives the STATUS only from what was observed. Read top to bottom: the first
    condition that holds wins."""

    SUPERSEDES = {"tests_after_repair": "tests"}
    """A phase that re-runs an earlier one under a different name.

    `tests_after_repair` is the whole list today. It exists because the trace should show that
    the tests failed AND that they were fixed, while the verdict must read only the second.
    Without this a repair could never lead anywhere but PARTIAL."""

    def __init__(self, catalog: MessageCatalog) -> None:
        self._t = catalog

    @classmethod
    def _concern(cls, phase: Phase) -> str:
        """What a phase is ABOUT, ignoring which attempt it was."""
        base = phase.name.split(":")[0]
        return cls.SUPERSEDES.get(base, base)

    def derive(
        self,
        phases: Sequence[Phase],
        markers: Mapping[str, str],
        findings: Sequence[Finding],
        crud: Sequence[str] = (),
    ) -> tuple[ProjectStatus, str]:
        t = self._t
        by_name = {self._concern(p): p for p in phases}
        # A dict keeps the LAST row per concern, which is what "effective" means here: a
        # phase that ran again after a repair replaces the one that failed before it.
        effective = tuple(by_name.values())
        errors = [f for f in findings if f.severity is Severity.ERROR]
        limits = [f for f in findings if f.severity is Severity.LIMIT]
        passing = [k for k, v in markers.items() if v == "PASS"]
        failing = [k for k, v in markers.items() if v == "FAIL"]

        if (p := by_name.get("structure")) and p.status is PhaseStatus.FAILED:
            return ProjectStatus.FAILED, t("derive.structure")
        if (p := by_name.get("syntax")) and p.status is PhaseStatus.FAILED:
            return ProjectStatus.FAILED, t("derive.syntax")
        if errors:
            return ProjectStatus.FAILED, t("derive.broken_imports", count=len(errors))
        if not markers:
            if limits:
                return ProjectStatus.VALIDATED, t("derive.validated_missing_dependency")
            if by_name.get("tests"):
                return ProjectStatus.EXECUTED, t("derive.executed_no_markers")
            return ProjectStatus.GENERATED, t("derive.nothing_ran")
        if failing:
            status = ProjectStatus.PARTIAL if passing else ProjectStatus.FAILED
            return status, t("derive.markers_failed", failed=len(failing), total=len(markers))
        if crud and not set(crud) <= set(markers):
            return ProjectStatus.PARTIAL, t("derive.crud_incomplete", missing=len(set(crud) - set(markers)))
        if limits:
            return ProjectStatus.PARTIAL, t("derive.partial_limits")
        if not passing:
            return ProjectStatus.EXECUTED, t("derive.no_pass")
        # A phase that RAN and produced no evidence cannot be hidden by another that did: the
        # project's 9 tests came out NO EVIDENCE and the 7 CRUD markers dragged the status
        # to VERIFIED. That is exactly what must not happen.
        silent = [p.name for p in effective
                  if p.status is PhaseStatus.LIMITED and self._concern(p) in ("tests", "crud")]
        if silent:
            return ProjectStatus.PARTIAL, t("derive.silent_phase", phase=silent[0])
        broken = [p.name for p in effective if p.status is PhaseStatus.FAILED]
        if broken:
            return ProjectStatus.PARTIAL, t("derive.phase_failed", phase=broken[0])
        reason = t("derive.verified", count=len(passing))
        if crud:
            reason += t("derive.verified_crud_suffix")
        return ProjectStatus.VERIFIED, reason


class ProjectCertifier:
    """Walks the whole chain and returns a :class:`Certificate`. It calls no model unless a
    repairer is given, and even then at most :data:`MAX_REPAIRS` times."""

    def __init__(self, runner: CodeRunner, syntax: SyntaxChecker, analyzer: DependencyAnalyzer,
                 evidence: EvidenceBuilder | None = None) -> None:
        self._runner = runner
        self._syntax = syntax
        self._analyzer = analyzer
        self._evidence = evidence or EvidenceBuilder()

    def _python(self) -> str:
        return "python3"

    def certify(
        self,
        project: Project,
        catalog: MessageCatalog,
        test_command: str | None = None,
        on_phase: PhaseListener | None = None,
        repairer: Repairer | None = None,
    ) -> Certificate:
        t = catalog
        phases: list[Phase] = []
        repairs: list[dict[str, Any]] = []
        interpreter = self._runner.interpreters.resolve(self._python()) or ""

        def note(phase: Phase) -> Phase:
            phases.append(phase)
            if on_phase:
                on_phase(phase)
            return phase

        # ── 1. structure ─────────────────────────────────────────────────────
        clock = Stopwatch()
        problems = validate_structure(project, catalog)
        totals = project.totals
        note(Phase("structure", PhaseStatus.FAILED if problems else PhaseStatus.OK,
                   "; ".join(problems) or t("cert.structure.ok", files=totals["files"],
                                            directories=totals["directories"]), clock.ms))
        if problems:
            return Certificate(ProjectStatus.FAILED, t("cert.reason.structure", problem=problems[0]),
                               tuple(phases), (), {}, project=project)

        # ── 2. syntax ────────────────────────────────────────────────────────
        clock.restart()
        syntax_error = self._syntax.check(project.as_text_mapping())
        note(Phase("syntax", PhaseStatus.FAILED if syntax_error else PhaseStatus.OK,
                   syntax_error.describe(t) if syntax_error else t("cert.syntax.ok"), clock.ms))
        if syntax_error:
            return Certificate(ProjectStatus.FAILED, t("cert.reason.syntax", detail=syntax_error.detail[:120]),
                               tuple(phases), (), {}, project=project)

        # ── 3. imports and dependencies ──────────────────────────────────────
        clock.restart()
        _imports, findings = self._analyzer.analyze(project)
        errors = DependencyAnalyzer.of_severity(findings, Severity.ERROR)
        limits = DependencyAnalyzer.of_severity(findings, Severity.LIMIT)
        note(Phase("imports",
                   PhaseStatus.FAILED if errors else (PhaseStatus.LIMITED if limits else PhaseStatus.OK),
                   (t("cert.imports.broken", count=len(errors)) if errors else
                    t("cert.imports.limited", count=len(limits)) if limits else t("cert.imports.ok")),
                   clock.ms))

        if errors and repairer:
            for attempt in range(1, MAX_REPAIRS + 1):
                clock.restart()
                repaired, changed, cause = repairer(project, errors, "", attempt)
                repairs.append({"attempt": attempt, "files": list(changed), "cause": cause, "motive": "imports"})
                note(Phase(f"repair:{attempt}", PhaseStatus.OK if changed else PhaseStatus.FAILED,
                           t("cert.repair.imports", count=len(changed)), clock.ms))
                if not changed:
                    break
                project = repaired
                _imports, findings = self._analyzer.analyze(project)
                errors = DependencyAnalyzer.of_severity(findings, Severity.ERROR)
                limits = DependencyAnalyzer.of_severity(findings, Severity.LIMIT)
                if not errors:
                    # Re-noted, not left as it was. The first `imports` row said FAILED and
                    # that row is what the verdict reads; without this a project whose imports
                    # were repaired, whose tests pass and whose CRUD is green comes out
                    # PARTIAL because of a phase that is no longer true. The failed row stays
                    # in the trace — the history is the point — and this one supersedes it.
                    note(Phase("imports", PhaseStatus.LIMITED if limits else PhaseStatus.OK,
                               t("cert.imports.limited", count=len(limits)) if limits
                               else t("cert.imports.repaired", attempt=attempt), clock.ms))
                    break

        if errors:
            return Certificate(ProjectStatus.FAILED,
                               t("cert.reason.broken_imports", count=len(errors), detail=errors[0].detail),
                               tuple(phases), tuple(findings), {}, repairs=tuple(repairs), project=project)

        # With a missing external dependency nothing can run, and that is NOT a project
        # failure. It is a ceiling: VALIDATED, saying exactly why.
        if limits:
            missing = ", ".join(sorted({f.subject for f in findings if f.kind == "missing_dependency"}))
            note(Phase("execution", PhaseStatus.LIMITED, t("cert.execution.limited", missing=missing)))
            return Certificate(ProjectStatus.VALIDATED, t("cert.reason.validated", missing=missing),
                               tuple(phases), tuple(findings), {}, repairs=tuple(repairs),
                               interpreter=interpreter, project=project)

        # Sections 4 and 5 are the ONLY ones that run the project. With execution off none of
        # their phases is noted, on purpose: a "tests" phase makes the status EXECUTED ("the
        # tests ran and printed no marker"), which would be false. Without them it is
        # GENERATED, "there are files and nothing ran" - exactly what happened. Structure,
        # syntax and imports above are static analysis and still catch the real failures.
        if not self._runner.enabled:
            note(Phase("execution", PhaseStatus.SKIPPED, t("cert.execution.disabled")))
            status, reason = StatusDeriver(t).derive(tuple(phases), {}, tuple(findings))
            return Certificate(status, reason, tuple(phases), tuple(findings), {}, repairs=tuple(repairs),
                               interpreter=interpreter, project=project)

        # ── 4. the project's tests, ALWAYS through the probe ─────────────────
        # With the bare project command, unittest prints no markers and the phase comes out
        # NO EVIDENCE - a silence the CRUD markers used to hide, giving a false VERIFIED.
        clock.restart()
        harness = probes.tests_probe("tests")
        tests = self._runner.run({**project.as_text_mapping(), **harness}, f"{self._python()} _probe_tests.py")
        note(Phase("tests", _FROM_EXECUTION.get(tests.status, PhaseStatus.LIMITED), tests.describe(t),
                   clock.ms, tests.text))
        markers = dict(tests.markers)

        # And apart, the command the README tells the user to run. If it fails, it does not
        # matter that the probe passes: what the user types will not work.
        if test_command:
            clock.restart()
            documented = self._runner.run(project.as_text_mapping(), test_command)
            broken = documented.status in (ExecutionStatus.FAILED, ExecutionStatus.NOT_EXECUTED)
            note(Phase("documented_command", PhaseStatus.FAILED if broken else PhaseStatus.OK,
                       (t("cert.documented.fails", command=test_command, header=documented.describe(t)) if broken
                        else t("cert.documented.ok", command=test_command)),
                       clock.ms, documented.text))

        if tests.status is ExecutionStatus.FAILED and repairer:
            for attempt in range(len(repairs) + 1, MAX_REPAIRS + 1):
                clock.restart()
                repaired, changed, cause = repairer(project, [], tests.text, attempt)
                repairs.append({"attempt": attempt, "files": list(changed), "cause": cause, "motive": "tests"})
                note(Phase(f"repair:{attempt}", PhaseStatus.OK if changed else PhaseStatus.FAILED,
                           t("cert.repair.tests", count=len(changed)), clock.ms))
                if not changed:
                    break
                project = repaired
                tests = self._runner.run({**project.as_text_mapping(), **harness},
                                         f"{self._python()} _probe_tests.py")
                note(Phase("tests_after_repair", _FROM_EXECUTION.get(tests.status, PhaseStatus.LIMITED),
                           tests.describe(t), 0.0, tests.text))
                markers = dict(tests.markers)
                if tests.status is ExecutionStatus.PASSED:
                    break

        # ── 5. real CRUD, if the project exposes the contract ────────────────
        entrypoint, factory = find_entrypoint(project)
        crud: tuple[str, ...] = ()
        if entrypoint:
            clock.restart()
            mark = probes.nonce()
            crud = probes.crud_ids(mark)
            resource = str(project.spec.get("resource") or "/books")
            sample, change = probes.sample_for(project.spec.get("entity"), project.spec.get("fields"))
            crud_run = self._runner.run({**project.as_text_mapping(),
                                         **probes.crud_probe(entrypoint, mark, resource, sample, change,
                                                             entrypoint_name=factory)},
                                        f"{self._python()} _probe_crud.py")
            note(Phase("crud", _FROM_EXECUTION.get(crud_run.status, PhaseStatus.LIMITED), crud_run.describe(t),
                       clock.ms, crud_run.text))
            markers.update(crud_run.markers)
        else:
            note(Phase("crud", PhaseStatus.SKIPPED, t("cert.crud.skipped")))

        evidence = self._evidence.build(
            [{"risk": t("cert.crud_risk", operation=i.split("_")[1]),
              "property": t("cert.crud_property", operation=i.split("_")[1]), "test_id": i} for i in crud],
            ExecutionResult(ExecutionStatus.PASSED if markers else ExecutionStatus.NO_EVIDENCE, "", "", markers),
            executed=bool(markers),
        )
        status, reason = StatusDeriver(t).derive(tuple(phases), markers, tuple(findings), crud)
        return Certificate(status, reason, tuple(phases), tuple(findings), markers, tuple(evidence),
                           tuple(repairs), interpreter, project)
