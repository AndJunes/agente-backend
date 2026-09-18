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
from dataclasses import dataclass, field
from typing import Any

from mirag.core.errors import ForbiddenPathError
from mirag.execution.interpreters import InterpreterRegistry
from mirag.i18n.catalog import MessageCatalog
from mirag.llm.gateway import LLMGateway
from mirag.llm.messages import first_tool_arguments, function_tool
from mirag.projects.certification import Repairer
from mirag.projects.dependencies import Finding
from mirag.projects.model import FILE_KINDS, Project

MAX_CALLS = 7
GROUPS = ("core", "domain", "tests", "docs")

HTTP_CONTRACT = """\
MANDATORY PROJECT RULES (set by Mirag, not negotiable):
- The entrypoint exposes `create_server(port=0, db=":memory:")` which RETURNS an already built
  ThreadingHTTPServer WITHOUT starting it. Whoever calls it starts it.
- NOTHING runs when a module is imported. Start-up goes under `if __name__ == "__main__":`.
- `sqlite3.connect(..., check_same_thread=False)` and a `threading.Lock` around writes.
- Every package has its `__init__.py`.
- Tests live in `tests/` and use `unittest`. MANDATORY: the plan must include at least one
  file in `tests/`. Without tests there is nothing to verify and the project is delivered FAILED.
- `test_command` must start with one of the interpreters that EXIST on this machine:
  {interpreters}.
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
            "language": {"type": "string"},
            "framework": {"type": "string", "description": "'stdlib' if none is needed"},
            "database": {"type": "string"},
            "architecture": {"type": "string"},
            "entity": {"type": "string", "description": "the main entity, e.g. book"},
            "resource": {"type": "string", "description": "the REST path, e.g. /books"},
            "fields": {"type": "array", "items": {"type": "string"}, "description": "the entity fields"},
            "dependencies": {"type": "array", "items": {"type": "string"},
                             "description": "only the ones really needed. Empty for stdlib."},
            "test_command": {"type": "string", "description": "starts with python3 or node"},
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


StepListener = Callable[[GenerationStep], None]


def _files_of(data: Mapping[str, Any]) -> dict[str, Any]:
    raw = data.get("files")
    return raw if isinstance(raw, dict) else {}


class ProjectGenerator:
    def __init__(self, interpreters: InterpreterRegistry) -> None:
        self._interpreters = interpreters

    def contract(self, language_directive: str = "") -> str:
        return HTTP_CONTRACT.format(interpreters=self._interpreters.describe() or "python3",
                                    language=language_directive)

    # ── the plan ─────────────────────────────────────────────────────────────

    @staticmethod
    def complete_plan(plan: list[dict[str, Any]], spec: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        """Add what the structure requires and the model forgot.

        Measured over 6 real runs: in 5 the plan came without a single file in tests/, even
        though the request asked for them and the contract marks them mandatory. Generating
        thirteen files and failing them later for "no tests" is expensive and our fault: if we
        know they are missing, they are added. The content is still written by the model.
        """
        paths = {f.get("path", "") for f in plan}
        if any(p.startswith("tests/") and p.endswith(".py") for p in paths):
            return plan, []
        entity = (spec or {}).get("entity") or "api"
        entrypoint = next((f["path"] for f in plan if f.get("kind") == "entrypoint"), "")
        if not entrypoint:
            entrypoint = next((f["path"] for f in plan if f.get("path", "").endswith("main.py")), "")
        added = []
        for path, purpose in (("tests/__init__.py", "tests package"),
                              (f"tests/test_{entity}.py", f"full CRUD of {entity} over real HTTP, with unittest")):
            if path in paths:
                continue
            plan = [*plan, {"path": path, "kind": "test", "purpose": purpose, "exports": [], "group": "tests",
                            "depends_on": [entrypoint] if entrypoint and path.endswith(f"test_{entity}.py") else []}]
            added.append(path)
        return plan, added

    def validate_plan(self, plan: Sequence[Mapping[str, Any]], spec: Mapping[str, Any] | None,
                      catalog: MessageCatalog) -> list[str]:
        """What a plan must bring for the rest to mean anything."""
        problems = []
        paths = [f.get("path", "") for f in plan]
        if not any(p.startswith("tests/") for p in paths):
            problems.append(catalog.t("generation.problem.no_tests"))
        if not any(f.get("kind") == "entrypoint" for f in plan):
            problems.append(catalog.t("generation.problem.no_entrypoint"))
        command = (spec or {}).get("test_command") or ""
        first = command.split()[0] if command.split() else ""
        if first and self._interpreters.resolve(first) is None:
            problems.append(catalog.t("generation.problem.bad_interpreter", first=first,
                                      available=self._interpreters.describe()))
        return problems

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
        """Uses at most :data:`MAX_CALLS` model calls."""
        result = GenerationResult(None, None)
        t = catalog

        def note(step: GenerationStep) -> None:
            result.steps.append(step)
            if on_step:
                on_step(step)

        contract = self.contract(language_directive)
        system = f"{context}\n\n{contract}\n\nFirst define the project and its file plan. Without writing code."
        message = gateway.chat([{"role": "system", "content": system}, {"role": "user", "content": request}],
                               tools=[SPECIFY_TOOL])
        spec = first_tool_arguments(message)
        result.spec = spec
        if not spec or not isinstance(spec.get("files"), list) or not spec["files"]:
            note(GenerationStep("specification", "error", t("generation.no_plan")))
            return result

        plan = [f for f in spec["files"] if isinstance(f, dict) and f.get("path")]
        # tolerate the legacy field names some models still send
        for entry in plan:
            entry.setdefault("kind", entry.pop("type", "code"))
        plan, added = self.complete_plan(plan, spec)
        if added:
            note(GenerationStep("plan", "fallback", t("generation.tests_added", count=len(added)), {"added": added}))
        if problems := self.validate_plan(plan, spec, catalog):
            # Said HERE, not after generating eleven files and failing on structure.
            note(GenerationStep("plan", "error", "; ".join(problems), {"problems": problems}))
        note(GenerationStep("specification", "executed",
                            t("generation.specified", name=spec.get("name", "project"),
                              framework=spec.get("framework", "?"), count=len(plan)),
                            {"spec": {k: v for k, v in spec.items() if k != "files"},
                             "plan": [f.get("path") for f in plan]}))

        project = Project(spec.get("name") or "project", spec)
        used = 1
        for group in GROUPS:
            own = [f for f in plan if f.get("group") == group]
            if not own:
                continue
            if used >= MAX_CALLS:
                note(GenerationStep(f"generation:{group}", "skipped", t("generation.call_cap", cap=MAX_CALLS)))
                continue
            wanted = "\n".join(f"  {f['path']} — {f.get('purpose', '')}" for f in own)
            message = gateway.chat([
                {"role": "system", "content": f"{contract}\n\n{self.interface_contract(plan, project, group)}"},
                {"role": "user", "content": f"Write the COMPLETE content of these files of the group '{group}':\n{wanted}"},
            ], tools=[DELIVER_GROUP_TOOL])
            used += 1
            reasons: list[str] = []
            data = first_tool_arguments(message, reasons) or {}
            files = _files_of(data)
            if not files and not reasons:
                reasons.append(f"the tool call brought no files: keys {sorted(data)}")
            placed, rejected = [], []
            for path, content in files.items():
                # The schema says string; a model can still send null for an empty file. A
                # None used to raise TypeError out of the whole generation, and an int became
                # that many NUL bytes (bytes(5)). Strict when writing: it is rejected, visibly.
                if not isinstance(content, str):
                    rejected.append(f"{path}: the content is {type(content).__name__}, not text")
                    continue
                try:
                    project.add(path, content, kind=self._kind_of(path, plan), group=group)
                    placed.append(path)
                except ForbiddenPathError as exc:
                    rejected.append(f"{path}: {exc}")
            summary = t("generation.group_files", count=len(placed))
            if rejected:
                summary += " · " + t("generation.group_rejected", count=len(rejected))
            if not placed and reasons:
                summary += f" · {reasons[0][:90]}"
            note(GenerationStep(f"generation:{group}", "executed" if placed else "error", summary,
                                {"files": placed, "rejected": rejected, "reasons": reasons,
                                 "requested": [f["path"] for f in own]}))

        result.project = project if project.files() else None
        return result

    # ── repair ───────────────────────────────────────────────────────────────

    def repairer(self, context: str, gateway: LLMGateway, language_directive: str = "") -> Repairer:
        """A function ``(project, errors, output, attempt) -> (new, changed, cause)``.

        Only the files involved are sent: the whole project is not regenerated because
        ``books/repository.py`` fails.
        """
        contract = self.contract(language_directive)

        def repair(project: Project, errors: Sequence[Finding], output: str, attempt: int) -> tuple[Project, tuple[str, ...], str]:
            involved = sorted({f.file for f in errors} | {f.path for f in project.files() if output and f.path in output})
            if not involved:
                involved = [f.path for f in project.files() if f.path.endswith(".py")][:4]
            found = [(p, file) for p in involved if (file := project.get(p)) is not None]
            bodies = "\n\n".join(f"--- {p}\n{file.text}" for p, file in found)
            diagnosis = "\n".join(f"  {f.file}:{f.line} {f.detail}" for f in errors)
            message = gateway.chat([
                {"role": "system", "content": f"{contract}\n\nFix the CAUSE, not the symptom. "
                                              "Return ONLY the files you change."},
                {"role": "user", "content": f"Attempt {attempt}. This is wrong:\n{diagnosis or '(see the output)'}\n\n"
                                            f"Execution output:\n{(output or '')[:3000]}\n\nFiles involved:\n{bodies}"},
            ], tools=[REPAIR_TOOL])
            data = first_tool_arguments(message) or {}
            new_files = _files_of(data)
            if not new_files:
                return project, (), str(data.get("cause", "the model returned no file"))
            copy = project.copy()
            changed = []
            for path, content in new_files.items():
                if not isinstance(content, str):
                    continue
                try:
                    copy.add(path, content)
                    changed.append(path)
                except ForbiddenPathError:
                    continue
            return copy, tuple(changed), str(data.get("cause", ""))

        return repair
