"""When the tests fail, does the repairer get told what broke and where?

    python scripts/check_repair.py

This is the vivero-api failure, kept as a fixture because it cost a real run. Sixteen files,
2,682 lines, compiled cleanly, imports resolved — and 41 of its tests were red because
`shared/database.py` handed every caller a NEW `sqlite3.connect(":memory:")`, which SQLite
documents as "a separate in-memory database". Two repair attempts touching twelve files fixed
nothing.

They could not have. The tests loop passed `errors=[]`, so:

  - the diagnosis the model received was the literal string "(see the output)";
  - the files it received were chosen by asking whether a path appeared as a SUBSTRING of a
    log that had already lost 84% of itself to truncation;
  - and when that found nothing, the fallback was the first four `.py` paths ALPHABETICALLY —
    which for a project with `tests/` and `vivero/` is four test files and no implementation.

So the model was handed the symptom and asked for the cause.

What this checks, with no model and no network:

  1. unittest's output becomes findings that name the real file, line and reason.
  2. From a failing test, the import graph reaches the module that actually broke.
  3. The repairer is shown that module, not only the test.
  4. A model that returns a path it was never shown has it refused.
"""

from __future__ import annotations

import sys

from mirag.execution.interpreters import InterpreterRegistry
from mirag.projects.certification import failures_as_findings
from mirag.projects.dependencies import DependencyAnalyzer
from mirag.projects.generator import ProjectGenerator
from mirag.projects.model import Project

# The shape of the real project, reduced to the chain that matters.
DATABASE = '''\
"""The bug, exactly as it was generated."""
import sqlite3

_db_path = None
_db_connection = None


def init_db(db_path):
    global _db_connection, _db_path
    _db_path = db_path
    _db_connection = sqlite3.connect(db_path, check_same_thread=False)
    _create_tables()


def get_connection():
    # Every call is a SEPARATE, EMPTY database when db_path is ":memory:".
    return sqlite3.connect(_db_path, check_same_thread=False)
'''

# unittest's own output for that failure, with the traceback it really produced.
OUTPUT = '''\
FAILED (exit 1)

TEST:test_crear_planta:FAIL
TEST:test_listar_plantas:FAIL

======================================================================
ERROR: test_crear_planta (tests.test_plantas_crud.TestPlantasRepository.test_crear_planta)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/run/vivero/plantas/repository.py", line 41, in crear
    cursor.execute("INSERT INTO plantas (nombre) VALUES (?)", (planta.nombre,))
sqlite3.OperationalError: no such table: plantas

During handling of the above exception, another exception occurred:

  File "/tmp/run/tests/test_plantas_crud.py", line 88, in test_crear_planta
    self.service.crear_planta(planta)
  File "/tmp/run/vivero/plantas/service.py", line 50, in crear_planta
    return self.repository.crear(planta)
  File "/tmp/run/vivero/plantas/repository.py", line 62, in crear
    raise ConflictError(f"Error al crear planta: {e}")
vivero.shared.errors.ConflictError: Error al crear planta: no such table: plantas
'''


def vivero() -> Project:
    project = Project("vivero-api", {"entity": "planta"})
    project.add("vivero/__init__.py", "")
    project.add("vivero/shared/__init__.py", "")
    project.add("vivero/shared/database.py", DATABASE)
    project.add("vivero/shared/errors.py", "class ConflictError(Exception): ...\n")
    project.add("vivero/plantas/__init__.py", "")
    project.add("vivero/plantas/repository.py",
                "from vivero.shared.database import get_connection\n"
                "from vivero.shared.errors import ConflictError\n\n\nclass Repo:\n    pass\n")
    project.add("vivero/plantas/service.py",
                "from vivero.plantas.repository import Repo\n\n\nclass Service:\n    pass\n")
    project.add("vivero/main.py",
                "from vivero.plantas.service import Service\n\n\n"
                "def create_server(port=0, db=':memory:'):\n    return None\n",
                kind="entrypoint")
    project.add("tests/__init__.py", "", kind="test")
    project.add("tests/test_plantas_crud.py",
                "from vivero.plantas.service import Service\nimport unittest\n", kind="test")
    return project


class Recorder:
    """A model that records what it was asked, and answers with a path it was never shown."""

    name = "recorder"
    simulated = True

    def __init__(self) -> None:
        self.system = ""
        self.user = ""

    def complete(self, messages, tools=None, require=None):
        import json
        from dataclasses import dataclass

        self.system = messages[0]["content"]
        self.user = messages[-1]["content"]

        @dataclass
        class Usage:
            prompt_tokens: int = 1
            completion_tokens: int = 1
            cost_usd: float = 0.0

        @dataclass
        class Response:
            message: dict
            usage: Usage

        return Response({"role": "assistant", "content": None, "tool_calls": [{
            "id": "c", "type": "function", "function": {"name": "repair_files", "arguments": json.dumps({
                "files": {"vivero/shared/database.py": DATABASE.replace("return sqlite3.connect", "return _db_connection  #"),
                          "vivero/never_shown.py": "# a file the model invented\n"},
                "cause": "one connection, shared"})}}]}, Usage())


def main() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    project = vivero()
    analyzer = DependencyAnalyzer(InterpreterRegistry())

    print("\n=== 1. the output becomes a finding that names the real file ===")
    findings = failures_as_findings(OUTPUT, project.paths())
    check("a finding came out", bool(findings), f"{len(findings)} found")
    if not findings:
        print("\n1 FAILED"), sys.exit(1)
    first = findings[0]
    print(f"    {first.file}:{first.line} — {first.detail[:88]}")
    check("it points at the implementation, not the test",
          first.file == "vivero/plantas/repository.py", first.file)
    check("it carries the real reason", "no such table" in first.detail, first.detail[:60])

    print("\n=== 2. the graph reaches the module that actually broke ===")
    reached = analyzer.reached_from(project, [f.file for f in findings])
    print("    " + ", ".join(reached))
    check("it reaches shared/database.py", "vivero/shared/database.py" in reached)

    print("\n=== 3. the repairer is shown the implementation ===")
    from mirag.llm.budget import Budget
    from mirag.llm.gateway import LLMGateway

    recorder = Recorder()
    repair = ProjectGenerator(InterpreterRegistry()).repairer(
        "", LLMGateway(recorder, Budget(), offline=False), analyzer=analyzer)
    repaired, changed, cause = repair(project, findings, OUTPUT, 1)

    shown = [line[4:] for line in recorder.user.splitlines() if line.startswith("--- ")]
    print("    files sent: " + ", ".join(shown))
    check("database.py was sent", "vivero/shared/database.py" in shown)
    check("the diagnosis is not '(see the output)'", "(see the output)" not in recorder.user)
    check("the traceback survived", "no such table: plantas" in recorder.user)

    print("\n=== 4. the prompt is about repairing TESTS ===")
    check("it forbids weakening the assertion",
          "Weakening an assertion" in recorder.system)
    check("it says the bug is probably not in the test file",
          "NOT in the test file" in recorder.system)

    print("\n=== 5. a path it was never shown is refused ===")
    check("the invented file was not written", repaired.get("vivero/never_shown.py") is None)
    check("the real fix was applied", "vivero/shared/database.py" in changed, str(changed))
    check("the refusal is reported", "refused" in cause, cause[:80])

    print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILED: {failures}"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
