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
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from mirag.core.timing import Deadline, Stopwatch
from mirag.evidence.properties import EvidenceBuilder, EvidenceRow
from mirag.execution.backend import CodeExecutionBackend
from mirag.execution.syntax import SyntaxChecker
from mirag.execution.verdict import ExecutionResult, ExecutionStatus
from mirag.i18n.catalog import MessageCatalog
from mirag.projects import languages, probes
from mirag.projects.convergence import (
    MAX_ATTEMPTS,
    Convergence,
    ConvergenceLoop,
    Repairer,
    Round,
    Verdict,
)
from mirag.projects.dependencies import DependencyAnalyzer, Finding, Severity
from mirag.projects.installation import DependencyInstaller, InstallReport, NullInstaller
from mirag.projects.model import Project

__all__ = [
    "MAX_REPAIRS",
    "Certificate",
    "Phase",
    "PhaseStatus",
    "ProjectCertifier",
    "ProjectStatus",
    "Repairer",
    "StatusDeriver",
    "failures_as_findings",
    "find_entrypoint",
    "validate_structure",
]

MAX_REPAIRS = MAX_ATTEMPTS
"""Repair attempts PER MOTIVE: syntax, imports, failing tests.

Per motive, and that is the fix. The three loops used to draw from one shared pool, and the
last of them started at `range(len(repairs) + 1, ...)` — so a project that needed two syntax
repairs arrived at its failing tests with zero attempts left, and the tests were never even
asked about. The motive that got there first spent everything.

The loop itself now lives in `convergence.py` and this is an alias of its ceiling: the three
hand-written copies of it here had already drifted apart once, which is what that module
exists to stop happening twice."""


class ProjectStatus(StrEnum):
    INCOMPLETE = "INCOMPLETE"
    """The plan asked for files that were never written.

    Not a rung of the ladder below — it is off to the side, like FAILED. A project missing a
    third of its modules is not a lesser VERIFIED, it is a project that was not delivered.
    It used to be indistinguishable from a complete one: `validate_structure` never read the
    plan, so if the delivered subset happened to compile and its tests passed, the verdict
    was VERIFIED and the download button appeared."""

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


_REPAIR_STATUS = {True: PhaseStatus.OK, False: PhaseStatus.SKIPPED}
"""A repair that changed nothing is the repairer DECLINING, not the project failing.

It used to be noted FAILED, and `derive` turns any failed phase into PARTIAL — so a project
whose tests went green after the first repair still came out PARTIAL because a second attempt
found nothing left to change. The verdict of the thing being repaired is what says whether it
worked; this row only says whether a call was spent."""


_FROM_EXECUTION = {ExecutionStatus.PASSED: PhaseStatus.OK, ExecutionStatus.FAILED: PhaseStatus.FAILED}


@dataclass(frozen=True, slots=True)
class Phase:
    name: str
    status: PhaseStatus
    detail: str
    ms: float = 0.0
    output: str = ""
    """The RAW output when it executed something."""


def _repair_phase(t: MessageCatalog, motive: str, attempt: int, changed: Sequence[str],
                  cause: str, ms: float) -> Phase:
    """The row for one repair attempt — and WHY, when it changed nothing.

    `repair()` has always computed the cause and handed it back; only the structured
    `repairs` record kept it, so the row a person actually reads said "0 files touched" and
    stopped there. A measured run spent 61 seconds on such a row and there was no way, after
    the fact, to tell "the model returned nothing" from "it returned paths it was never
    shown" — two failures with different fixes. The count is the summary, the cause is the
    detail, and the detail is the part worth keeping.
    """
    detail = t("cert.repair." + motive, count=len(changed))
    return Phase(f"repair:{motive}:{attempt}", _REPAIR_STATUS[bool(changed)],
                 detail if changed else f"{detail} — {cause or 'sin causa declarada'}", ms, cause)


def _round_phase(t: MessageCatalog, round: Round) -> Phase:
    """One round of :class:`~mirag.projects.convergence.ConvergenceLoop` as a phase row.

    The loop knows nothing about phases, catalogs or statuses, and this is the whole of the
    translation between the two. `_repair_phase` keeps its own signature because a script
    checks it directly.
    """
    return _repair_phase(t, round.motive, round.attempt, round.changed, round.cause, round.ms)


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
    installation: InstallReport | None = field(default=None, compare=False)
    """What the dependency gate did, or ``None`` when it never ran.

    Kept on the certificate because "the tests passed" means something different when the
    packages under them were installed for this run than when they were already there, and a
    reader should not have to infer which from the phase rows. It also names the volume they
    went into, which is the only handle anybody has on them."""

    @property
    def ok(self) -> bool:
        return self.status is ProjectStatus.VERIFIED

    @property
    def passed(self) -> int:
        return sum(1 for v in self.markers.values() if v == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for v in self.markers.values() if v == "FAIL")


PhaseListener = Callable[[Phase], None]


def validate_structure(project: Project, catalog: MessageCatalog) -> list[str]:
    """What must exist for the rest to mean anything."""
    problems = []
    files = project.files()
    if not files:
        problems.append(catalog.t("cert.problem.no_files"))
    # `tests/` and nothing else, because that is where the harness looks.
    #
    # This used to accept a root-level `test_api.py` as well, while the tests probe runs
    # `unittest.defaultTestLoader.discover("tests", ...)` flat. When a project took the branch
    # this allowed, the probe raised `ImportError: Start directory is not importable`, exited
    # non-zero with NO markers — and `derive` reads `if not markers` BEFORE it looks for
    # broken phases, so the verdict came out EXECUTED ("it ran and printed nothing") instead
    # of PARTIAL. A project whose tests never ran was reported as one whose tests were silent.
    #
    # Two places disagreeing about where tests live is the bug. One place wins.
    #
    # That holds for the languages Mirag runs — Python and Node.js, where the harness looks in
    # `tests/` and only there. For every other language the test is recognised by its own
    # convention (`foo_test.go`, `src/test/`, `foo_spec.rb`): nothing here executes it, so
    # there is no harness whose search directory has to agree. Which language it is comes from
    # the blueprint, then from the files (see `languages.detect`).
    paths = [f.path for f in files]
    if not languages.has_tests(paths, languages.detect(project.spec, paths)):
        problems.append(catalog.t("cert.problem.no_tests"))
    if not any(languages.is_source(path) for path in paths):
        problems.append(catalog.t("cert.problem.no_code"))
    # Python packages without __init__.py: it works from the root and fails elsewhere
    packages = {"/".join(f.path.split("/")[:-1]) for f in files if f.path.endswith(".py") and "/" in f.path}
    for package in sorted(packages):
        if package.startswith("tests"):
            continue
        if not project.get(f"{package}/__init__.py"):
            problems.append(catalog.t("cert.problem.missing_init", package=package))
    return problems


SYNTAX_WHERE = re.compile(r"^([^\s:]+\.\w+):(\d+):")
"""`app/api.py:43: SyntaxError: ...` — the file and line the checker put at the front."""


def _as_findings(error: ExecutionResult) -> tuple[Finding, ...]:
    """The syntax failure as the one thing the repairer takes.

    The repairer asks for `Finding`s because that is what the dependency analyzer produces,
    and it uses exactly three fields of them: which file, which line, and what is wrong. A
    syntax error has all three — it just had no way to say so, which is the only reason it
    was never repaired.
    """
    found = SYNTAX_WHERE.match(error.detail or "")
    return (Finding(kind="syntax_error", severity=Severity.ERROR,
                    file=found.group(1) if found else "", line=int(found.group(2)) if found else 0,
                    detail=error.detail or "the file does not compile"),)


FAILING_TEST = re.compile(r"^(?:FAIL|ERROR):\s+(\S+)\s+\(([^)]+)\)", re.MULTILINE)
"""`FAIL: test_crear (tests.test_plantas.TestRepo.test_crear)` — unittest's own heading."""

TRACEBACK_FRAME = re.compile(r'^\s+File "([^"]+)", line (\d+)', re.MULTILINE)
"""A frame. The LAST one inside a block is where the assertion actually blew up."""

def _why(block: str) -> str:
    """The exception line that ends a traceback.

    Not a regex on the exception's NAME: real ones are dotted —
    `vivero.shared.errors.ConflictError`, `sqlite3.OperationalError` — and a pattern anchored
    on a bare word plus "Error" matches neither, which silently fell through to quoting the
    block's heading back at the model instead of the reason.

    unittest's own shape is what identifies it: the frames are indented, the exception is the
    last line that is not.
    """
    lines = [line for line in block.splitlines()
             if line.strip() and not line.startswith((" ", "\t"))
             and not line.startswith(("FAIL:", "ERROR:", "---", "Traceback"))]
    return lines[-1].strip() if lines else ""


def failures_as_findings(output: str, known: Collection[str]) -> tuple[Finding, ...]:
    """Every failing test as a `Finding` the repairer can act on.

    The tests loop was the one that passed `errors=[]`, and that single decision disabled
    everything downstream: with no findings the diagnosis became the literal string
    "(see the output)", and the choice of which files to send the model degenerated into
    asking whether a path happened to appear as a SUBSTRING of a truncated log.

    Measured on a real failure, that resolved to one file — a test file — for a project whose
    bug was in `shared/database.py`. The model was asked to fix a cause while holding only the
    symptom.

    `known` is the project's own paths, used to keep only frames that belong to it: a
    traceback is mostly `unittest/case.py` and other stdlib, which is never what to repair.
    """
    findings: list[Finding] = []
    for block in _blocks(output):
        head = FAILING_TEST.search(block)
        if head is None:
            continue
        frames = [(path, int(line)) for path, line in TRACEBACK_FRAME.findall(block)]
        mine = [(path, line) for path, line in frames
                if any(path.endswith(candidate) for candidate in known)]
        # The deepest frame in the project is where it broke; the shallowest is the test that
        # noticed. Prefer the former, fall back to the latter.
        where = mine[-1] if mine else (frames[-1] if frames else ("", 0))
        findings.append(Finding(
            kind="failing_test", severity=Severity.ERROR,
            file=_relative(where[0], known), line=where[1],
            detail=f"{head.group(1)} failed: {_why(block) or block.strip()[:160]}",
            subject=head.group(1)))
    return tuple(findings)


def _blocks(output: str) -> list[str]:
    """unittest separates each failure with a line of `=`."""
    return [block for block in re.split(r"^=+$", output, flags=re.MULTILINE) if "File \"" in block]


def _relative(path: str, known: Collection[str]) -> str:
    """A traceback carries the absolute path inside the sandbox; the project knows relatives."""
    return next((candidate for candidate in known if path.endswith(candidate)), path)


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

    SUPERSEDES: ClassVar[dict[str, str]] = {"tests_after_repair": "tests"}
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

    def __init__(self, runner: CodeExecutionBackend, syntax: SyntaxChecker, analyzer: DependencyAnalyzer,
                 evidence: EvidenceBuilder | None = None,
                 installer: DependencyInstaller | None = None,
                 max_repairs: int = MAX_REPAIRS) -> None:
        self._runner = runner
        self._syntax = syntax
        self._analyzer = analyzer
        self._evidence = evidence or EvidenceBuilder()
        self._installer: DependencyInstaller = installer or NullInstaller()
        self._max_repairs = max_repairs

    @property
    def analyzer(self) -> DependencyAnalyzer:
        """The import graph, for whoever needs to follow it — the repairer does."""
        return self._analyzer

    @property
    def installer(self) -> DependencyInstaller:
        return self._installer

    def _python(self) -> str:
        return "python3"

    def _tests_probe(self, language: languages.Language | None) -> tuple[dict[str, str], str] | None:
        """``(probe files, command)`` for a language Mirag can run here, else ``None``.

        `None` is an answer, not an error: for Go, Rust or Java the tests exist and are
        delivered, and nothing here can execute them. It is also what a Node.js project gets on a
        machine with no `node` — asking the runner anyway would come back "not executed" and be
        reported as tests that ran and printed nothing, which is a different sentence.
        """
        if language is None:
            return None
        if language.harness == "python":
            return probes.tests_probe("tests"), f"{self._python()} _probe_tests.py"
        if language.harness == "node" and self._runner.interpreters.resolve("node"):
            return probes.node_tests_probe("tests"), "node _probe_tests.mjs"
        return None

    def certify(
        self,
        project: Project,
        catalog: MessageCatalog,
        test_command: str | None = None,
        on_phase: PhaseListener | None = None,
        repairer: Repairer | None = None,
        expected: Sequence[str] = (),
        deadline: Deadline | None = None,
    ) -> Certificate:
        t = catalog
        phases: list[Phase] = []
        repairs: list[dict[str, Any]] = []
        interpreter = self._runner.interpreters.resolve(self._python()) or ""
        # The Docker volume the packages this project declared ended up in, once they have.
        # Empty until the dependency gate below runs, and every probe from there on is given
        # it — per call, never as state on the runner: one process certifies several projects
        # at a time and a runner remembering a volume would lend one project's packages to
        # another's tests.
        dependencies = ""
        loop = ConvergenceLoop(self._max_repairs, deadline)

        def note(phase: Phase) -> Phase:
            phases.append(phase)
            if on_phase:
                on_phase(phase)
            return phase

        def converge(motive: str, project: Project, verdict: Verdict,
                     probe: Callable[[Project], Verdict]) -> Convergence:
            """One motive, repaired until it is green or until there is a reason it is not.

            Every round is noted as it happens and recorded in `repairs`, so the trace shows
            the same history it always did — what changed is that the three motives no longer
            keep three separate, drifting copies of this.
            """
            def on_repair(round: Round) -> None:
                # Before the re-check, so the trace reads in the order things happened: what
                # the repair touched, and only then what happened when it was run again.
                note(_round_phase(t, round))
                repairs.append(round.as_record())

            return loop.converge(motive, project, verdict, probe, repairer, on_repair)

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

        # ── 1b. the plan is the contract, and nothing used to check it ───────
        #
        # `validate_structure` above checks four things and none of them is "the files that
        # were planned exist". The generator knows — it puts the list in its own step detail —
        # but that died in the trace. Measured: a plan of 36 files delivered 12, and because
        # those 12 happened to compile and import each other cleanly, the project went on to
        # be packaged with a download button.
        #
        # A file that arrived WITHOUT being planned is not a problem: models consolidate two
        # planned modules into one that carries both, which is usually the better call. It is
        # noted and allowed.
        if expected:
            missing = [path for path in expected if project.get(path) is None]
            extra = sorted({f.path for f in project.files()} - set(expected))
            note(Phase("plan", PhaseStatus.FAILED if missing else PhaseStatus.OK,
                       t("cert.plan.missing", count=len(missing), detail=", ".join(missing[:4]))
                       if missing else
                       t("cert.plan.extra", count=len(extra)) if extra else
                       t("cert.plan.ok", count=len(expected)),
                       clock.ms))
            if missing:
                return Certificate(
                    ProjectStatus.INCOMPLETE,
                    t("derive.incomplete", count=len(missing), detail=", ".join(missing[:6])),
                    tuple(phases), (), {}, project=project)

        # ── 2. syntax ────────────────────────────────────────────────────────
        clock.restart()
        syntax_error = self._syntax.check(project.as_text_mapping())
        note(Phase("syntax", PhaseStatus.FAILED if syntax_error else PhaseStatus.OK,
                   syntax_error.describe(t) if syntax_error else t("cert.syntax.ok"), clock.ms))

        # Repaired, like imports and tests below. This used to return on the spot, and a
        # syntax error is the ONE failure most worth repairing: measured, a real ten-file
        # project was lost to a single unclosed parenthesis in one test file, cut off because
        # the model hit its output budget. Nine good files were thrown away, certification
        # stopped before imports, and a download button appeared over a project that cannot
        # be imported. The repairer was sitting right there, already written.
        if syntax_error:
            def compiles(candidate: Project) -> Verdict:
                # The probe owns `syntax_error` from here on: what the loop returns is a
                # verdict, and what the code below needs is the failing result itself.
                nonlocal syntax_error
                syntax_error = self._syntax.check(candidate.as_text_mapping())
                return Verdict(green=syntax_error is None,
                               findings=() if syntax_error is None else _as_findings(syntax_error),
                               detail="" if syntax_error is None else syntax_error.detail)

            converged = converge("syntax", project, Verdict(False, _as_findings(syntax_error)),
                                 compiles)
            project = converged.project
            if converged.green:
                note(Phase("syntax", PhaseStatus.OK,
                           t("cert.syntax.repaired", attempt=converged.attempts), clock.ms))

        if syntax_error:
            return Certificate(ProjectStatus.FAILED, t("cert.reason.syntax", detail=syntax_error.detail[:120]),
                               tuple(phases), (), {}, repairs=tuple(repairs), project=project)

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

        if errors:
            def resolves(candidate: Project) -> Verdict:
                nonlocal findings, errors, limits
                _records, findings = self._analyzer.analyze(candidate, dependencies)
                errors = DependencyAnalyzer.of_severity(findings, Severity.ERROR)
                limits = DependencyAnalyzer.of_severity(findings, Severity.LIMIT)
                return Verdict(green=not errors, findings=tuple(errors),
                               detail=errors[0].detail if errors else "")

            converged = converge("imports", project, Verdict(False, tuple(errors)), resolves)
            project = converged.project
            if converged.green:
                # Re-noted, not left as it was. The first `imports` row said FAILED and that
                # row is what the verdict reads; without this a project whose imports were
                # repaired, whose tests pass and whose CRUD is green comes out PARTIAL because
                # of a phase that is no longer true. The failed row stays in the trace — the
                # history is the point — and this one supersedes it.
                note(Phase("imports", PhaseStatus.LIMITED if limits else PhaseStatus.OK,
                           t("cert.imports.limited", count=len(limits)) if limits
                           else t("cert.imports.repaired", attempt=converged.attempts), clock.ms))

        if errors:
            return Certificate(ProjectStatus.FAILED,
                               t("cert.reason.broken_imports", count=len(errors), detail=errors[0].detail),
                               tuple(phases), tuple(findings), {}, repairs=tuple(repairs), project=project)

        # ── 3b. the ceiling, and the one thing that lifts it ─────────────────
        #
        # A missing external dependency caps the status at VALIDATED and the tests are never
        # run. That is the honest verdict for a machine that cannot install anything, and it
        # was the FIRST answer on every machine — including the ones that can. A FastAPI
        # project was being delivered unexecuted because `fastapi` was not importable, when
        # installing it is one bounded command.
        #
        # So: install what the project declared, ask the analyzer again, and only then decide.
        # If the install fails nothing is lost — the ceiling below is exactly where the run
        # lands, now with the log saying why it could not be lifted.
        #
        # WHERE the packages go is the installer's business and it has exactly one answer: a
        # Docker volume, mounted read-only into the same sandbox the tests run in. On a
        # deployment with no sandbox there is no install, and `NullInstaller` says so — which
        # is why this branch checks `enabled` and never the backend.
        install: InstallReport | None = None
        if limits and self._installer.enabled and self._runner.enabled and not loop.out_of_time():
            clock.restart()
            install = self._installer.install(project)
            note(Phase("dependencies", PhaseStatus.OK if install.ok else PhaseStatus.LIMITED,
                       (t("cert.dependencies.installed", count=len(install.installed),
                          detail=", ".join(install.installed[:6]))
                        if install.ok
                        else t("cert.dependencies.failed", reason=install.detail)),
                       clock.ms, install.log))
            if install.refused:
                # Named rather than silently dropped: `-r other.txt`, `--index-url …` and
                # `git+ssh://…` are all ordinary lines of a requirements file, none of them
                # may reach pip from here, and a person reading the trace should see which.
                note(Phase("dependencies:refused", PhaseStatus.LIMITED,
                           t("cert.dependencies.refused", count=len(install.refused),
                             detail="; ".join(install.refused[:3]))))
            if install.ok:
                dependencies = install.volume
                clock.restart()
                _imports, findings = self._analyzer.analyze(project, dependencies)
                errors = DependencyAnalyzer.of_severity(findings, Severity.ERROR)
                limits = DependencyAnalyzer.of_severity(findings, Severity.LIMIT)
                note(Phase("imports",
                           PhaseStatus.FAILED if errors else
                           PhaseStatus.LIMITED if limits else PhaseStatus.OK,
                           (t("cert.imports.broken", count=len(errors)) if errors else
                            t("cert.imports.limited", count=len(limits)) if limits
                            else t("cert.imports.resolved_after_install")), clock.ms))

        # The ceiling, for whatever the install did not reach. Unchanged: VALIDATED, saying
        # exactly which package is missing.
        if limits:
            missing_deps = ", ".join(sorted({f.subject for f in findings if f.kind == "missing_dependency"}))
            note(Phase("execution", PhaseStatus.LIMITED, t("cert.execution.limited", missing=missing_deps)))
            return Certificate(ProjectStatus.VALIDATED, t("cert.reason.validated", missing=missing_deps),
                               tuple(phases), tuple(findings), {}, repairs=tuple(repairs),
                               interpreter=interpreter, project=project,
                               installation=install)

        # Sections 4 and 5 are the ONLY ones that run the project. With execution off none of
        # their phases is noted, on purpose: a "tests" phase makes the status EXECUTED ("the
        # tests ran and printed no marker"), which would be false. Without them it is
        # GENERATED, "there are files and nothing ran" - exactly what happened. Structure,
        # syntax and imports above are static analysis and still catch the real failures.
        # Out of time, and a project already exists. The sections below are the only ones that
        # RUN anything, and they are each bounded by the runner's own subprocess timeout — so
        # this is not about a hang, it is about not spending three more minutes on a run whose
        # answer nobody is waiting for. Degrading is the whole point: the project is kept,
        # packaged and reported as what it is, which `derive` already words correctly —
        # "there are files and nothing was ever executed".
        if loop.out_of_time():
            note(Phase("execution", PhaseStatus.SKIPPED, t("cert.execution.deadline")))
            status, reason = StatusDeriver(t).derive(tuple(phases), {}, tuple(findings))
            return Certificate(status, reason, tuple(phases), tuple(findings), {},
                               repairs=tuple(repairs), interpreter=interpreter, project=project,
                               installation=install)

        if not self._runner.enabled:
            note(Phase("execution", PhaseStatus.SKIPPED, t("cert.execution.disabled")))
            status, reason = StatusDeriver(t).derive(tuple(phases), {}, tuple(findings))
            return Certificate(status, reason, tuple(phases), tuple(findings), {}, repairs=tuple(repairs),
                               interpreter=interpreter, project=project, installation=install)

        # ── 4. the project's tests, ALWAYS through the probe ─────────────────
        # With the bare project command, unittest prints no markers and the phase comes out
        # NO EVIDENCE - a silence the CRUD markers used to hide, giving a false VERIFIED.
        language = languages.detect(project.spec, project.paths())
        probe = self._tests_probe(language)
        if probe is None:
            # Named "execution", not "tests": a phase called "tests" is what makes the status
            # EXECUTED — "the tests ran and printed no marker" — and nothing ran. Without it
            # the verdict is GENERATED, which is exactly the truth: there are files, and their
            # tests were written in the right language and are waiting for someone who can run
            # them.
            note(Phase("execution", PhaseStatus.SKIPPED,
                       t("cert.tests.no_harness", language=language.name if language else "?")))
            status, reason = StatusDeriver(t).derive(tuple(phases), {}, tuple(findings))
            return Certificate(status, reason, tuple(phases), tuple(findings), {}, repairs=tuple(repairs),
                               interpreter=interpreter, project=project, installation=install)
        harness, tests_command = probe

        def run_tests(candidate: Project) -> ExecutionResult:
            return self._runner.run({**candidate.as_text_mapping(), **harness}, tests_command,
                                    dependencies=dependencies)

        clock.restart()
        tests = run_tests(project)
        note(Phase("tests", _FROM_EXECUTION.get(tests.status, PhaseStatus.LIMITED), tests.describe(t),
                   clock.ms, tests.text))
        markers = dict(tests.markers)

        # And apart, the command the README tells the user to run. If it fails, it does not
        # matter that the probe passes: what the user types will not work.
        if test_command:
            clock.restart()
            documented = self._runner.run(project.as_text_mapping(), test_command,
                                          dependencies=dependencies)
            broken = documented.status in (ExecutionStatus.FAILED, ExecutionStatus.NOT_EXECUTED)
            note(Phase("documented_command", PhaseStatus.FAILED if broken else PhaseStatus.OK,
                       (t("cert.documented.fails", command=test_command, header=documented.describe(t)) if broken
                        else t("cert.documented.ok", command=test_command)),
                       clock.ms, documented.text))

        if tests.status is ExecutionStatus.FAILED:
            def green_tests(candidate: Project) -> Verdict:
                nonlocal tests, markers
                tests = run_tests(candidate)
                markers = dict(tests.markers)
                note(Phase("tests_after_repair", _FROM_EXECUTION.get(tests.status, PhaseStatus.LIMITED),
                           tests.describe(t), 0.0, tests.text))
                return Verdict(green=tests.status is ExecutionStatus.PASSED,
                               findings=failures_as_findings(tests.text, candidate.paths()),
                               output=tests.text, detail=tests.header)

            project = converge(
                "tests", project,
                Verdict(False, failures_as_findings(tests.text, project.paths()), tests.text),
                green_tests).project

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
                                        f"{self._python()} _probe_crud.py",
                                        dependencies=dependencies)
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
                           tuple(repairs), interpreter, project, install)
