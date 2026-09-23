"""From a request to a whole project, in few calls and without giant JSON.

THE STRATEGY

    1 call      specify + plan       what is built and which file does what
    2-4         by groups            core · domain · tests · docs
    0-2         selective repair     only the files involved

Neither one giant JSON with the whole project (it gets cut by max_tokens and there is no way
to know what is missing), nor one call per file (14 calls per project).

HOW CONSISTENCY ACROSS CALLS HOLDS
    Each group receives the CONTRACT: what every generated file exports and what is still
    pending. For the group's direct dependencies it also gets their real code. The prompt
    does not grow with the project because not everything travels, only what is needed.

    And afterwards it is checked with AST: declaring is not complying. The dependency
    analyzer reads the real imports and crosses them with the symbols the files really define.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from mirag.core.errors import (
    BudgetExceededError,
    ClientGoneError,
    DeadlineExceededError,
    ForbiddenPathError,
    ModelUnreachableError,
    RateLimitedError,
    RunStoppedError,
)
from mirag.execution.interpreters import InterpreterRegistry
from mirag.i18n.catalog import MessageCatalog
from mirag.llm.gateway import LLMGateway
from mirag.llm.messages import first_tool_arguments, function_tool
from mirag.projects import languages
from mirag.projects.certification import Repairer
from mirag.projects.dependencies import DependencyAnalyzer, Finding
from mirag.projects.model import FILE_KINDS, Project

SUGGESTED_FILES = 16
"""What the contract ASKS FOR, and nothing more than that.

This was a hard cap, and a plan over it was trimmed — which silently dropped files the plan
had asked for and could perfectly well break the code that imported them. Rejecting a
blueprint for being one file too long, or quietly cutting it, solves the wrong problem: the
real one was that a big plan did not fit in the call budget, and the answer to that is
generating the batches in parallel, not throwing files away.

The number stays as guidance because it is still true that fewer, larger modules deliver more
reliably than thirty-six stubs — every file is another chance for one not to arrive."""

MAX_CALLS = 16
"""The real ceiling on model calls inside :meth:`ProjectGenerator.generate`.

It was 7 and was never enforced: the blueprint's retry was not counted (`used = 1` whatever
had happened) so the true ceiling was 8, and with four groups `used >= MAX_CALLS` could not
fire at all. Now every call is counted, and the number is the worst case it has to allow:
two blueprint attempts plus, for each of four groups, enough passes to deliver it in batches
of `GROUP_BATCH`. Repairs are NOT in here — they belong to certification, which has its own
attempt cap."""

SPECIFY_ATTEMPTS = 2
"""How many times the blueprint is asked for before giving up.

Two, not one, and not more: a model that answers in prose twice is not going to answer in a
tool call on the third try, and each attempt costs a call out of MAX_CALLS."""

GROUP_ATTEMPTS = 4
"""Passes a group gets. Each one asks only for what is still missing.

Two was enough when the only failure being handled was a dropped call. It is not enough for
a group of twenty files delivered in batches: four passes of six covers twenty-four, which
is more than any group a blueprint has produced. `MAX_CALLS` is the real ceiling."""

_STOP_REASON: dict[type[Exception], str] = {
    BudgetExceededError: "generation.budget_stopped",
    RateLimitedError: "generation.provider_stopped",
    ModelUnreachableError: "generation.unreachable_stopped",
    DeadlineExceededError: "generation.deadline_stopped",
    ClientGoneError: "generation.abandoned_stopped",
}
"""Which sentence each stop deserves. They are handled the same and they are not the same."""

PREVIEW_BYTES = 400_000
"""How much generated source travels with the steps, before the paths go without their text.

Matches the artifact's own ceiling. A project is capped at 400 kB in total, so in practice
every file's text fits and the cap only bites on something pathological."""

CONCURRENT_BATCHES = 4
"""Batches of one group asked for at the same time.

Four, and the number comes from the provider's own documented limits rather than a guess:
OpenRouter allows 20 requests a minute on free models and documents no concurrency limit. A
call measured at 234 seconds is 0.25 requests a minute — four at once is still a twentieth of
what is allowed, with room for the retries and the repairs that come later.

It is not higher because the gain flattens: a plan is rarely more than four batches deep in
one group, and each concurrent call is another output budget being spent at once."""

GROUP_BATCH = 6
"""Files asked for in one call.

Not a guess: asked for twenty at once the model wrote three and stopped, which is the correct
behaviour for something with a finite output budget. Six times ~1,500 characters sits well
inside 16,000 output tokens with the contract and the interface list in front of it."""
GROUPS = ("core", "domain", "tests", "docs")
"""The order the four known groups are generated in — not the list of what exists.

`GROUPS` used to BE the loop, so a plan entry with `group: "config"`, `group: "api"` or no
group at all was never asked for, never generated and never reported: the files simply
vanished between the blueprint and the project. The enum in the schema is a suggestion the
model is free to ignore, and offline this never showed because the demo labels its fourteen
files with these four exact names."""


def groups_of(plan: Sequence[Mapping[str, Any]]) -> list[str]:
    """Every group the plan actually mentions, the four known ones first."""
    present = {str(f.get("group") or "") for f in plan}
    extra = sorted(g for g in present if g and g not in GROUPS)
    return [g for g in GROUPS if g in present] + extra


LINE_BASED = (*sorted(languages.SOURCE_EXTENSIONS), ".sql", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".md", ".sh")
FLAT_AFTER = 200
"""Characters past which a line-based file with no line break is not a file anyone can use."""


def _flattened(path: str, content: str) -> str:
    """Why this content cannot be a source file, or ``""``.

    Only for formats where a line break carries meaning. JSON, HTML and CSS are legitimately
    written on one line, and a short module genuinely can be.
    """
    if not path.endswith(LINE_BASED) or len(content) <= FLAT_AFTER or "\n" in content:
        return ""
    return (f"{path}: {len(content)} characters and not one line break — the model cannot write "
            f"newlines inside a tool call, so this is not usable source")


REPAIR_OUTPUT = 12_000
"""Characters of execution output the repairer is shown.

It was 3,000, on top of the runner's own 4,000-character cap — and the two interacted badly.
The markers go to stdout and the tracebacks to stderr, the runner concatenates them in that
order, so 2,283 characters of `TEST:x:FAIL` lines filled the ENTIRE 2,000-character head of
the truncation window. Of thirty-five failures the model saw roughly two explained. It knew
which tests failed and, for almost all of them, not why."""

MAX_INVOLVED = 8
"""Files sent in one repair prompt. Enough for a test, the chain it exercises, and the
storage underneath; small enough that the bodies still leave room for an answer."""

_REPAIR_ADVICE = {
    "failing_test": (
        "The project's own tests are FAILING. Fix the CODE UNDER TEST, not the tests.\n"
        "Weakening an assertion, deleting a case or wrapping it in try/except is not a repair "
        "and will be rejected: the tests are the only evidence this project works.\n"
        "The bug is usually NOT in the test file. Read the traceback and follow it into the "
        "module that raised.\n"
        "Return ONLY the files you change."
    ),
    "syntax_error": (
        "A file does not compile. Fix the syntax where the error points, change nothing else, "
        "and return ONLY the files you change."
    ),
    "broken_internal_import": (
        "An import does not resolve. Either the module is missing what it is asked for, or the "
        "import names the wrong thing. Fix whichever is actually wrong — do not delete the "
        "import to silence it. Return ONLY the files you change."
    ),
    "failure": "Fix the CAUSE, not the symptom. Return ONLY the files you change.",
}
"""One instruction per motive.

All three repair loops shared a single prompt that only talked about generating a project. A
model handed test files and told "fix the cause" has one cheap move available — soften the
assertion — and nothing was telling it not to."""


def _involved(project: Project, errors: Sequence[Finding], output: str,
              analyzer: DependencyAnalyzer | None) -> list[str]:
    """Which files the repairer is shown.

    Three sources, in order of how much they know:

    1. The files the findings NAME. For a failing test that is now the deepest project frame
       in the traceback — where it actually broke — not the test that noticed.
    2. What those files REACH through the import graph. This is the part that was missing: a
       failing test names a test file, and the bug lives in the code that test exercises. The
       graph is the only thing that knows which code that is.
    3. Paths that appear in the output, as a last resort.

    The old fallback — the first four `.py` files in alphabetical order — is gone. For a
    project with `tests/` and `vivero/`, "alphabetical" meant the four test files and not one
    line of implementation: the model was asked for the cause while holding only the symptom.
    """
    named = [f.file for f in errors if f.file and project.get(f.file) is not None]
    if named and analyzer is not None:
        reached = analyzer.reached_from(project, named)
        # Named first: they are where the traceback pointed, and the prompt is capped.
        ordered = named + [path for path in reached if path not in named]
        return ordered[:MAX_INVOLVED]
    if named:
        return sorted(set(named))[:MAX_INVOLVED]
    mentioned = sorted(f.path for f in project.files() if output and f.path in output)
    if mentioned:
        return mentioned[:MAX_INVOLVED]
    # Nothing to go on — which happens when the probe died before running anything. The
    # entrypoint is the one file always worth looking at.
    entry = [f.path for f in project.files("entrypoint")]
    return (entry or [f.path for f in project.files() if languages.is_source(f.path)])[:MAX_INVOLVED]


def _group_for(entry: Mapping[str, Any]) -> str:
    """The group of a plan entry that came without one, inferred from what it is."""
    path, kind = str(entry.get("path") or ""), str(entry.get("kind") or "")
    if kind == "test" or path.startswith("tests/") or languages.looks_like_test(path):
        return "tests"
    if kind == "doc" or path.endswith((".md", ".txt")) or path in ("Dockerfile", "LICENSE", "Makefile"):
        return "docs"
    if kind == "config" or path.endswith((".json", ".toml", ".ini", ".cfg", ".yml", ".yaml", ".example")):
        return "core"
    return "core"

HTTP_CONTRACT = """\
MANDATORY PROJECT RULES (set by Mirag, not negotiable):
- Some rules below name Python constructs (`create_server`, `ThreadingHTTPServer`, `sqlite3`,
  `__init__.py`). In a Python project apply them as written. In any other language apply their
  equivalent: a factory that RETURNS an unstarted server, one shared database connection, and
  nothing running at import time.
- The entrypoint exposes `create_server(port=0, db=":memory:")` which RETURNS an already built
  ThreadingHTTPServer WITHOUT starting it. Whoever calls it starts it.
- NOTHING runs when a module is imported. Start-up goes under `if __name__ == "__main__":`.
- THE DATABASE IS **ONE CONNECTION**, opened once inside `create_server` and shared by every
  request. Pass it down; do not open one per request and do not close it between requests.
  This is not a style preference, it is how `:memory:` works: every `sqlite3.connect(":memory:")`
  opens a SEPARATE, EMPTY database, so a per-request connection sees none of the writes, and
  the database is destroyed when its last connection closes. Open it with
  `sqlite3.connect(db, check_same_thread=False)` and serialise the WRITES with a
  `threading.Lock` — that is what `check_same_thread=False` requires of you, and it is the
  companion of the shared connection, not a substitute for it.
- Every Python package has its `__init__.py`.
- TESTS ARE WRITTEN IN THE SAME LANGUAGE AS THE PROJECT, with that language's own standard test
  framework, and never in another one unless the request explicitly asks for it. A Python
  project is tested with `unittest`, a Node.js one in JavaScript with the built-in `node:test`
  and `node:assert/strict` (no dependencies), a Go one with `testing`, and so on for any other
  language. A test file in a different language than the code it tests can never pass.
  MANDATORY: the plan must include at least one test file, in `tests/` or wherever that
  language's convention puts it. Without tests there is nothing to verify and the project is
  delivered FAILED.
- EVERY TEST STARTS FROM A CLEAN DATABASE, built in the per-test setup (`setUp`, `beforeEach`)
  and not in a class-wide or file-wide one. Tests must pass in any order and on their own: one
  that only passes after another has inserted a row is a test that will fail here.
- `test_command` runs the tests with the language's own runner. When the language has an
  interpreter on this machine it must start with one of them: {interpreters} — for example
  `python3 -m unittest discover -s tests -t .` or `node --test tests/`. Never `npm`, `npx` or
  `yarn`: they are not here. A language none of those covers still gets its tests and its usual
  command (`go test ./...`, `cargo test`): it is written down for whoever runs it, not run here.
- PREFER FEWER, LARGER MODULES — around {max_files} files, never one file per class. Every
  file is a separate thing that can arrive wrong or not arrive at all, and a project is
  delivered only when ALL of its planned files exist.
- Standard library only, unless the request explicitly asks for something else.
- File paths are relative, without `..`, with a known extension.
- Code, identifiers and comments are in English.
{language}"""

SPECIFY_TOOL = function_tool(
    "specify_project",
    "Define WHAT is going to be built and with which files, without writing code.",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "lower case and hyphens, e.g. books-api"},
            "language": {"type": "string",
                         "description": "the programming language, e.g. python, javascript, go, java"},
            "framework": {"type": "string", "description": "'stdlib' if none is needed"},
            "database": {"type": "string"},
            "architecture": {"type": "string"},
            "entity": {"type": "string", "description": "the main entity, e.g. book"},
            "resource": {"type": "string", "description": "the REST path, e.g. /books"},
            "fields": {"type": "array", "items": {"type": "string"}, "description": "the entity fields"},
            "dependencies": {"type": "array", "items": {"type": "string"},
                             "description": "only the ones really needed. Empty for stdlib."},
            "test_command": {"type": "string",
                             "description": "the language's own test runner: python3 -m unittest ... "
                                            "or node --test tests/; never npm, npx or yarn"},
            "assumptions": {"type": "array", "items": {"type": "string"},
                            "description": "what you decided without being told, and why"},
            "files": {
                "type": "array",
                "description": "the plan: one file per entry, WITHOUT content",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "kind": {"type": "string", "enum": list(FILE_KINDS)},
                        "purpose": {"type": "string"},
                        "exports": {"type": "array", "items": {"type": "string"},
                                    "description": "functions and classes others will import"},
                        "depends_on": {"type": "array", "items": {"type": "string"},
                                       "description": "paths of this same project"},
                        "group": {"type": "string", "enum": list(GROUPS)},
                    },
                    "required": ["path", "kind", "purpose", "exports", "depends_on", "group"],
                },
            },
        },
        "required": ["name", "language", "framework", "database", "architecture", "entity", "resource",
                     "fields", "dependencies", "test_command", "assumptions", "files"],
    },
)

DELIVER_GROUP_TOOL = function_tool(
    "deliver_group",
    "The complete content of the files of ONE group of the plan.",
    {
        "type": "object",
        "properties": {
            "files": {"type": "object", "additionalProperties": {"type": "string"},
                      "description": "path -> complete file content"},
            "notes": {"type": "string", "description": "decisions of this group"},
        },
        "required": ["files"],
    },
)

REPAIR_TOOL = function_tool(
    "repair_files",
    "Return ONLY the files you change. Do not rewrite the whole project.",
    {
        "type": "object",
        "properties": {
            "files": {"type": "object", "additionalProperties": {"type": "string"}},
            "cause": {"type": "string", "description": "what was wrong, in one sentence"},
        },
        "required": ["files", "cause"],
    },
)


@dataclass(frozen=True, slots=True)
class GenerationStep:
    name: str
    status: str
    """``executed`` | ``error`` | ``fallback`` | ``skipped``."""
    summary: str
    detail: Any = None


@dataclass
class GenerationResult:
    project: Project | None
    spec: dict[str, Any] | None
    steps: list[GenerationStep] = field(default_factory=list)
    calls: int = 0
    """Model calls actually spent. Reported rather than assumed, because the number the
    docstring promised and the number the loop spent were never the same."""
    expected: tuple[str, ...] = ()
    """Every path the COMPLETED plan asked for.

    It travels to certification because nothing else could: `validate_structure` never reads
    the plan, so a project missing a third of its files passed structure, passed imports (the
    delivered files happened to compile), and came out VERIFIED."""


StepListener = Callable[[GenerationStep], None]


def _files_of(data: Mapping[str, Any]) -> dict[str, Any]:
    """``{path: content}`` out of whatever shape the model used for ``files``.

    The schema asks for an object. Models routinely send a LIST of objects instead —
    ``[{"path": ..., "content": ...}]`` is the commonest way to write a path→content map, and
    the docs group was seen doing exactly that. This used to return ``{}`` for anything that
    was not a dict, so every file was lost with no diagnostic and the step read "the tool call
    brought no files" for a call that brought all of them.
    """
    raw = data.get("files")
    if isinstance(raw, dict):
        return dict(raw)
    if not isinstance(raw, list):
        return {}
    files: dict[str, Any] = {}
    for entry in raw:
        if not isinstance(entry, Mapping):
            continue
        path = entry.get("path") or entry.get("name") or entry.get("filename")
        if not isinstance(path, str) or not path.strip():
            continue
        for key in ("content", "text", "body", "source", "code"):
            if key in entry:
                files[path] = entry[key]
                break
    return files


class ProjectGenerator:
    def __init__(self, interpreters: InterpreterRegistry) -> None:
        self._interpreters = interpreters

    def contract(self, language_directive: str = "") -> str:
        return HTTP_CONTRACT.format(interpreters=self._interpreters.describe() or "python3",
                                    max_files=SUGGESTED_FILES, language=language_directive)

    # ── the plan ─────────────────────────────────────────────────────────────

    @staticmethod
    def complete_plan(plan: list[dict[str, Any]], spec: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        """Add what the structure requires and the model forgot.

        Measured over 6 real runs: in 5 the plan came without a single file in tests/, even
        though the request asked for them and the contract marks them mandatory. Generating
        thirteen files and failing them later for "no tests" is expensive and our fault: if we
        know they are missing, they are added. The content is still written by the model.

        The README is here for the same reason and was found the same way. Every prompt this
        agent is sent through CodeZard asks in its first line for "a README", nothing
        downstream requires one, and a real 15-file project arrived without it: the `docs`
        group had nothing planned in it, so it was never even asked for. A project nobody can
        run is not a delivery, and the run that dropped it reported no problem at all.
        """
        paths = {f.get("path", "") for f in plan}
        entity = (spec or {}).get("entity") or "api"
        entrypoint = next((f["path"] for f in plan if f.get("kind") == "entrypoint"), "")
        if not entrypoint:
            entrypoint = next((f["path"] for f in plan if f.get("path", "").endswith("main.py")), "")
        added = []

        # The tests that are added are the PROJECT'S language's, and only where the layout is
        # known. This used to add `unittest` files whenever no `tests/*.py` existed — including
        # to a Node.js plan whose JavaScript tests were sitting right there — and a Python test
        # for a server it cannot import is a failing test nobody wrote on purpose. For a
        # language with no known layout nothing is added: `validate_plan` says so instead.
        language = languages.detect(spec, paths)
        if language and not languages.has_tests(paths, language):
            for template in language.test_files:
                path = template.format(entity=languages.slug(entity))
                if path in paths:
                    continue
                is_package_marker = path.endswith("__init__.py")
                plan = [*plan, {"path": path, "kind": "test",
                                "purpose": "tests package" if is_package_marker
                                else f"full CRUD of {entity} over real HTTP, with {language.framework}",
                                "exports": [], "group": "tests",
                                "depends_on": [entrypoint] if entrypoint and not is_package_marker else []}]
                added.append(path)

        if not any(p.upper().startswith("README") for p in paths):
            plan = [*plan, {"path": "README.md", "kind": "doc", "group": "docs", "exports": [],
                            "depends_on": [entrypoint] if entrypoint else [],
                            "purpose": "what this is, how to install and RUN it (the exact command), "
                                       "the endpoints, how to run the tests, and any environment "
                                       "variable it reads"}]
            added.append("README.md")
        return plan, added

    def validate_plan(self, plan: Sequence[Mapping[str, Any]], spec: Mapping[str, Any] | None,
                      catalog: MessageCatalog) -> list[str]:
        """What a plan must bring for the rest to mean anything."""
        problems = []
        paths = [f.get("path", "") for f in plan]
        language = languages.detect(spec, paths)
        if not languages.has_tests(paths, language):
            problems.append(catalog.t("generation.problem.no_tests"))
        if not any(p.upper().startswith("README") for p in paths):
            problems.append(catalog.t("generation.problem.no_readme"))
        if not any(f.get("kind") == "entrypoint" for f in plan):
            problems.append(catalog.t("generation.problem.no_entrypoint"))

        # Only for a language Mirag runs. For the others the command is documentation — `go
        # test ./...` is right and simply cannot execute here — and flagging it would put a
        # "problem" on every plan that did exactly what the contract asked.
        command = (spec or {}).get("test_command") or ""
        first = command.split()[0] if command.split() else ""
        if language and language.harness and first and self._interpreters.resolve(first) is None:
            problems.append(catalog.t("generation.problem.bad_interpreter", first=first,
                                      available=self._interpreters.describe()))
        return problems

    def normalize_test_command(self, spec: dict[str, Any], plan: Sequence[Mapping[str, Any]]) -> tuple[str, str] | None:
        """``(old, new)`` when the model's test command could not run here and the language's
        own could; ``None`` when nothing was changed.

        The commonest miss is `npm test` for a Node.js project: `npm` is not an interpreter
        here, so the command failed as "not executed" while `node --test tests/` — what it
        stands for — runs. Replacing it is a repair of the model's guess, not a decision about
        the project, and it is reported as a step so nobody wonders where the command came from.
        """
        language = languages.detect(spec, [str(f.get("path", "")) for f in plan])
        command = str(spec.get("test_command") or "")
        first = command.split()[0] if command.split() else ""
        if not (language and language.harness and language.test_command and first):
            return None
        if self._interpreters.resolve(first) is not None:
            return None
        if self._interpreters.resolve(language.test_command.split()[0]) is None:
            return None
        spec["test_command"] = language.test_command
        return command, language.test_command

    @staticmethod
    def interface_contract(plan: Sequence[Mapping[str, Any]], project: Project, group: str) -> str:
        """What each file exports: the ones already generated and the ones still pending.

        Only the CODE of the group's direct dependencies travels. The prompt does not grow
        with the project.
        """
        lines = ["PROJECT INTERFACES. You may only import what appears here or the standard",
                 "library. An import that is not here is detected with AST and the delivery is",
                 "rejected.", ""]
        own = [f for f in plan if f.get("group") == group]
        needed = {r for f in own for r in (f.get("depends_on") or [])}
        for entry in plan:
            path = entry.get("path", "")
            done = project.get(path) is not None
            exports = ", ".join(entry.get("exports") or []) or "(nothing to import)"
            state = "ALREADY GENERATED" if done else "PENDING - do not import it yet"
            lines.append(f"  {path:<34} exports: {exports}   [{state}]")
        bodies = []
        for path in sorted(needed):
            file = project.get(path) if path else None
            if file:
                bodies.append(f"\n--- {path} (your group imports it; here is its real code)\n{file.text}")
        return "\n".join(lines) + ("\n" + "\n".join(bodies) if bodies else "")

    @staticmethod
    def _kind_of(path: str, plan: Sequence[Mapping[str, Any]]) -> str:
        for entry in plan:
            if entry.get("path") == path:
                return str(entry.get("kind") or "code")
        return "test" if path.startswith("tests/") else "code"

    # ── generation ───────────────────────────────────────────────────────────

    def generate(self, request: str, context: str, gateway: LLMGateway, catalog: MessageCatalog,
                 language_directive: str = "", on_step: StepListener | None = None) -> GenerationResult:
        """Uses at most :data:`MAX_CALLS` model calls, and now actually counts them.

        Repairs are not included: they are certification's, with their own cap."""
        result = GenerationResult(None, None)
        t = catalog

        def note(step: GenerationStep) -> None:
            result.steps.append(step)
            if on_step:
                on_step(step)

        contract = self.contract(language_directive)
        system = f"{context}\n\n{contract}\n\nFirst define the project and its file plan. Without writing code."
        messages = [{"role": "system", "content": system}, {"role": "user", "content": request}]

        # Asked twice before giving up, because one empty answer is not evidence that the model
        # cannot do this. The same request was observed failing and then succeeding minutes
        # later with a 23-file blueprint: free providers drop calls. Without the retry a
        # transient hiccup ends the whole generation, and the user sees an agent that cannot
        # build their project rather than a provider that blinked.
        spec = None
        used = 0
        why: list[str] = []
        for attempt in range(SPECIFY_ATTEMPTS):
            why = []
            message = gateway.chat(messages, tools=[SPECIFY_TOOL], require="specify_project")
            used += 1
            spec = first_tool_arguments(message, why, name="specify_project")
            files = spec.get("files") if isinstance(spec, dict) else None
            if spec and isinstance(files, list) and files:
                break
            if spec is not None and not (files or []):
                why.append("the blueprint arrived with no files in it")
            if attempt + 1 < SPECIFY_ATTEMPTS:
                note(GenerationStep("specification", "fallback", t("generation.no_plan_retry")))
        result.spec = spec
        if not spec or not isinstance(spec.get("files"), list) or not spec["files"]:
            # `first_tool_arguments` has always collected WHY — prose, truncated JSON, wrong
            # shape — and this step has always thrown it away, reporting the same sentence for
            # three different problems with three different fixes. It cost an afternoon.
            note(GenerationStep("specification", "error", t("generation.no_plan"),
                                detail={"diagnostics": why} if why else None))
            result.calls = used
            return result

        plan = [f for f in spec["files"] if isinstance(f, dict) and f.get("path")]
        # tolerate the legacy field names some models still send
        for entry in plan:
            entry.setdefault("kind", entry.pop("type", "code"))
            # An entry with no group is an entry no loop would ever ask for. Inferring one is
            # not a guess about intent — it is the difference between the file being written
            # and the file disappearing between the blueprint and the project.
            if not str(entry.get("group") or "").strip():
                entry["group"] = _group_for(entry)
        plan, added = self.complete_plan(plan, spec)
        if added:
            note(GenerationStep("plan", "fallback", t("generation.tests_added", count=len(added)), {"added": added}))
        if replaced := self.normalize_test_command(spec, plan):
            note(GenerationStep("plan", "fallback",
                                t("generation.test_command_replaced", old=replaced[0], new=replaced[1]),
                                {"old": replaced[0], "new": replaced[1]}))
        if problems := self.validate_plan(plan, spec, catalog):
            # Said HERE, not after generating eleven files and failing on structure.
            note(GenerationStep("plan", "error", "; ".join(problems), {"problems": problems}))
            # And it used to be said and then ignored: four more calls went into a blueprint
            # already known to be unverifiable. The plan is repaired once — `complete_plan`
            # already adds missing tests — and only a plan with NO entrypoint is fatal, because
            # without one nothing downstream can be run at all.
            if not any(f.get("kind") == "entrypoint" for f in plan):
                for entry in plan:
                    if entry.get("path", "").endswith("main.py") or entry.get("group") == "core":
                        entry["kind"] = "entrypoint"
                        note(GenerationStep("plan", "fallback", t("generation.entrypoint_assumed",
                                                                  path=entry["path"]), {"path": entry["path"]}))
                        break
                else:
                    note(GenerationStep("plan", "error", t("generation.plan_unusable"), {"problems": problems}))
                    result.calls = used
                    return result
        note(GenerationStep("specification", "executed",
                            t("generation.specified", name=spec.get("name", "project"),
                              framework=spec.get("framework", "?"), count=len(plan)),
                            {"spec": {k: v for k, v in spec.items() if k != "files"},
                             "plan": [f.get("path") for f in plan]}))

        # The plan that travels is the COMPLETED one. `complete_plan` returns a new list, so
        # until now `spec["files"]` was the model's original — without the README and the
        # tests Mirag adds. Everything downstream that reads the spec (the manifest, the
        # answer) was reading a plan that had not been true since three lines above.
        spec["files"] = plan
        result.expected = tuple(str(f["path"]) for f in plan)
        project = Project(spec.get("name") or "project", spec)
        shown = 0
        """Bytes of preview sent so far. Past the cap the paths still travel and the text does
        not — the same trade the artifact makes, and for the same reason: a response of tens of
        megabytes is not a delivery."""
        stopped = ""
        pending = groups_of(plan)
        for index, group in enumerate(pending):
            if stopped:
                note(GenerationStep(f"generation:{group}", "skipped",
                                    t("generation.stopped_earlier", reason=stopped[:90]),
                                    {"cause": stopped}))
                continue
            own = [f for f in plan if f.get("group") == group]
            if not own:
                continue
            if used >= MAX_CALLS:
                note(GenerationStep(f"generation:{group}", "skipped", t("generation.call_cap", cap=MAX_CALLS)))
                continue
            # One call is held back for each group still to come.
            #
            # Measured: `core` had 31 files, took four passes, and by then the cap was gone.
            # `docs` — a single file, the README — was never asked for at all. A group of
            # thirty-one starving a group of one is not a budget, it is a race, and the
            # cheapest and most necessary file in the project lost it.
            reserved = len(pending) - index - 1
            ceiling = MAX_CALLS - reserved
            # Asked more than once, for the same reason the blueprint is: the group that
            # failed in the real run was `docs`, on a free provider that drops calls, and one
            # empty answer ended the only chance the project had of getting a README.
            #
            # And asked again while files are STILL MISSING, which is the other half and the
            # one that was wrong. The loop used to stop the moment anything at all arrived:
            # measured, a `core` group of twenty files delivered THREE, reported "executed",
            # and the project went on to fail with fifteen broken imports pointing at the
            # seventeen that were never written. A partial delivery is not a delivery.
            placed: list[str] = []
            rejected: list[str] = []
            reasons: list[str] = []
            for _attempt in range(GROUP_ATTEMPTS):
                # The group's own ceiling, not the run's: what is left after the reservation.
                # A group is still allowed its FIRST call even when the reservation is spent,
                # because a group that never gets asked cannot deliver anything at all.
                if used >= (ceiling if placed or _attempt else MAX_CALLS):
                    break
                missing = [f for f in own if project.get(f["path"]) is None]
                if not missing:
                    break
                # In batches, because a model has an output budget and twenty files do not fit
                # in it. Asked for all twenty it wrote three good ones rather than twenty bad
                # ones, which is the right call — so it is asked for a number that fits.
                #
                # And SEVERAL AT ONCE. Sequentially, a 36-file plan is six batches at the
                # measured 234 seconds each — nearly half an hour, which is why a file cap
                # looked like the answer and was not. OpenRouter documents 20 requests a
                # minute for free models and no concurrency limit at all; at one call every
                # 234 seconds we were using 0.25 of that 20. The waiting was never the
                # provider's rule, it was ours.
                #
                # The batches are independent by construction: `interface_contract` is built
                # from the PLAN, and files inside one batch cannot see each other's bodies in
                # the sequential version either. Groups stay in order, because `domain`
                # imports `core`.
                room = max(1, (ceiling if placed or _attempt else MAX_CALLS) - used)
                batches = [missing[i:i + GROUP_BATCH] for i in range(0, len(missing), GROUP_BATCH)]
                batches = batches[:min(CONCURRENT_BATCHES, room)]
                system = f"{contract}\n\n{self.interface_contract(plan, project, group)}"

                def ask(batch: list[dict[str, Any]], system: str = system,
                        group: str = group) -> tuple[dict[str, Any], list[str]]:
                    """One batch. Returns what came back; writes nothing shared.

                    `system` and `group` are bound as defaults rather than captured: the
                    workers run inside this iteration so a late-bound closure would happen to
                    be correct, and "happens to be correct" is how the next person moving this
                    line introduces a bug that only shows up under concurrency.
                    """
                    wanted = "\n".join(f"  {f['path']} — {f.get('purpose', '')}" for f in batch)
                    mine: list[str] = []
                    message = gateway.chat([
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"Write the COMPLETE content of these files "
                                                    f"of the group '{group}':\n{wanted}"},
                    ], tools=[DELIVER_GROUP_TOOL], require="deliver_group")
                    return first_tool_arguments(message, mine, name="deliver_group") or {}, mine

                delivered: list[dict[str, Any]] = []
                try:
                    if len(batches) == 1:
                        data, mine = ask(batches[0])
                        used += 1
                        delivered.append(data)
                        reasons.extend(mine)
                    else:
                        with ThreadPoolExecutor(max_workers=len(batches)) as pool:
                            # Results are collected IN ORDER and applied afterwards, from this
                            # thread. `project.add` was written for a single writer, and two
                            # batches landing at once is not a race worth having for the sake
                            # of a few milliseconds.
                            for data, mine in pool.map(ask, batches):
                                used += 1
                                delivered.append(data)
                                reasons.extend(mine)
                except (BudgetExceededError, RateLimitedError, ModelUnreachableError,
                        RunStoppedError) as exc:
                    # Eleven files already exist. Letting this out of `generate` threw them
                    # away and answered with a stack trace; what the user gets instead is the
                    # project that WAS built, with a step saying which group never arrived.
                    #
                    # And saying WHY. These three are caught together because the handling is
                    # the same — keep what exists, stop asking — but they are three different
                    # events with three different fixes, and one message for all of them
                    # reported "the spending cap was reached" for a run that never spent a
                    # cent: the model had burned its output budget reasoning. That is the same
                    # kind of misleading sentence this whole pass exists to remove.
                    stopped = str(exc)
                    note(GenerationStep(f"generation:{group}", "error",
                                        t(_STOP_REASON.get(type(exc), "generation.model_stopped"),
                                          reason=stopped[:120]),
                                        {"cause": stopped, "kind": type(exc).__name__}))
                    break

                files = {}
                for data in delivered:
                    batch_files = _files_of(data)
                    if not batch_files:
                        reasons.append(f"a batch brought no files: keys {sorted(data)}")
                    files.update(batch_files)
                for path, content in files.items():
                    # The schema says string; a model can still send null for an empty file. A
                    # None used to raise TypeError out of the whole generation, and an int became
                    # that many NUL bytes (bytes(5)). Strict when writing: it is rejected, visibly.
                    if not isinstance(content, str):
                        rejected.append(f"{path}: the content is {type(content).__name__}, not text")
                        continue
                    if flat := _flattened(path, content):
                        # Measured: a free model wrote every file of a 15-file project with no
                        # line breaks at all — `import jsonimport urllib.parse` — because it
                        # cannot emit `\n` inside a tool-call string. Fifteen files, twelve
                        # kilobytes, fifteen lines. It packaged, it offered a download, and the
                        # only sign was one red `syntax` row. Rejecting it here says which file
                        # and why, and leaves the retry a reason to send with the second ask.
                        rejected.append(flat)
                        reasons.append(flat)
                        continue
                    try:
                        project.add(path, content, kind=self._kind_of(path, plan), group=group)
                        placed.append(path)
                    except ForbiddenPathError as exc:
                        rejected.append(f"{path}: {exc}")
            # A model asked for one group hands back a neighbouring file it needed to write
            # anyway — `core` delivered `models.py`, which the plan had put in `domain`. That
            # is a good answer, not a mistake, and it left this group with nothing to ask for.
            # Reporting "0 files · error" for files that EXIST was worse than the old bug it
            # replaced: it says the generation failed when the project is complete.
            early = sorted({f["path"] for f in own if project.get(f["path"]) is not None}
                           - set(placed))
            never = sorted(f["path"] for f in own if project.get(f["path"]) is None)
            if placed:
                summary = t("generation.group_files", count=len(placed))
            elif early:
                summary = t("generation.group_early", count=len(early))
            else:
                summary = t("generation.group_files", count=0)
            if rejected:
                summary += " · " + t("generation.group_rejected", count=len(rejected))
            # Said out loud. A group that delivered three of twenty used to read exactly like
            # one that delivered twenty of twenty, and the first sign of the difference was a
            # wall of broken imports several phases later.
            if never:
                summary += " · " + t("generation.group_missing", count=len(never))
            if not placed and not early and reasons:
                summary += f" · {reasons[0][:90]}"
            status = "error" if not (placed or early) else ("fallback" if never else "executed")
            # The CONTENT travels with the step, not only the paths.
            #
            # The file tree used to appear all at once in the closing `done` event, so a
            # person watching a generation saw a spinner for ten or twenty minutes and then
            # everything. Sending what each group wrote as it is written lets the panel fill
            # up while the agent works.
            #
            # It is a preview and `done` remains authoritative: a repair can replace any of
            # these before the project is certified, and the two are allowed to differ.
            # Nothing here reaches the persisted trace, which records errors and totals, not
            # step details.
            wrote = {}
            for path in placed:
                file = project.get(path)
                if file is None:
                    continue
                shown += file.size
                wrote[path] = file.text if shown <= PREVIEW_BYTES else None
            note(GenerationStep(f"generation:{group}", status, summary,
                                {"files": placed, "delivered_earlier": early, "rejected": rejected,
                                 "missing": never, "reasons": reasons, "wrote": wrote,
                                 "requested": [f["path"] for f in own], "calls": used}))

        result.project = project if project.files() else None
        result.calls = used
        return result

    # ── repair ───────────────────────────────────────────────────────────────

    def repairer(self, context: str, gateway: LLMGateway, language_directive: str = "",
                 analyzer: DependencyAnalyzer | None = None) -> Repairer:
        """A function ``(project, errors, output, attempt) -> (new, changed, cause)``.

        Only the files involved are sent: the whole project is not regenerated because
        ``books/repository.py`` fails. Which files those ARE is the hard part — see
        :func:`_involved`.
        """
        contract = self.contract(language_directive)

        def repair(project: Project, errors: Sequence[Finding], output: str,
                   attempt: int) -> tuple[Project, tuple[str, ...], str]:
            involved = _involved(project, errors, output, analyzer)
            found = [(path, file) for path in involved if (file := project.get(path)) is not None]
            if not found:
                # A call that CANNOT land, so it is not made. With nothing resolved there are no
                # bodies to show and `allowed` below is empty, which means every path the model
                # returns is refused and the whole answer is discarded — measured once at 61
                # seconds, 13% of that run, for a guaranteed-empty result.
                return project, (), "no file of the project could be tied to the failure"
            bodies = "\n\n".join(f"--- {path}\n{file.text}" for path, file in found)
            diagnosis = "\n".join(f"  {f.file}:{f.line} {f.detail}" for f in errors)
            motive = errors[0].kind if errors else "failure"
            why: list[str] = []
            try:
                message = gateway.chat([
                    {"role": "system", "content": f"{contract}\n\n{_REPAIR_ADVICE.get(motive, _REPAIR_ADVICE['failure'])}"},
                    {"role": "user",
                     "content": f"Attempt {attempt}. This is wrong:\n{diagnosis or '(see the output)'}\n\n"
                                f"Execution output:\n{(output or '')[:REPAIR_OUTPUT]}\n\n"
                                f"Files involved:\n{bodies}"},
                ], tools=[REPAIR_TOOL], require="repair_files")
            except RunStoppedError as exc:
                # A repair is the one model call the project can do without. Letting the
                # clock out of here would throw away a project that is already built and
                # already worth packaging; the certifier's own `if not changed: break` ends
                # the repair loop, and the reason travels in the cause.
                return project, (), str(exc)
            data = first_tool_arguments(message, why, name="repair_files") or {}
            new_files = _files_of(data)
            if not new_files:
                # `why` was collected and thrown away, so prose, truncated JSON and a wrong
                # tool all reported the same sentence.
                return project, (), str(data.get("cause") or (why[0] if why else "the model returned no file"))
            copy = project.copy()
            changed, refused = [], []
            allowed = set(involved)
            for path, content in new_files.items():
                if not isinstance(content, str):
                    continue
                # Only what it was SHOWN. `project.add` replaces, so a model returning a path
                # it never read overwrites a file it wrote from imagination — and the counts
                # in the trace said "8 files touched" for a model that had been handed one.
                if path not in allowed:
                    refused.append(path)
                    continue
                try:
                    copy.add(path, content)
                    changed.append(path)
                except ForbiddenPathError:
                    continue
            cause = str(data.get("cause", ""))
            if refused:
                cause += f" (refused {len(refused)} paths it was not shown: {', '.join(refused[:3])})"
            return copy, tuple(changed), cause

        return repair
