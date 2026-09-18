"""Ready-made model scripts. Real, runnable code: what matters is that VERIFICATION runs for real.

The code inside the scripts is English for every locale; the human-readable strings the
model would write (answers, risks, decisions) come from the locale's messages.
"""

from __future__ import annotations

from typing import Any

from mirag.i18n.catalog import MessageCatalog
from mirag.llm.messages import assistant_text, raw_tool_call, tool_call
from mirag.offline import books_project

CALCULATOR = '''\
"""Minimal calculator."""


class CalculationError(ValueError):
    pass


def calculate(a, b, operation):
    if operation not in ("add", "subtract", "multiply", "divide"):
        raise CalculationError(f"unsupported operation: {operation}")
    if operation == "divide" and b == 0:
        raise CalculationError("division by zero")
    return {"add": a + b, "subtract": a - b,
            "multiply": a * b, "divide": a / b if b else None}[operation]
'''

CALCULATOR_TEST = '''\
from calculator import calculate, CalculationError

failures = 0


def check(test_id, condition):
    global failures
    print(f"TEST:{test_id}:{'PASS' if condition else 'FAIL'}")
    if not condition:
        failures += 1


check("add", calculate(2, 3, "add") == 5)
check("subtract", calculate(5, 3, "subtract") == 2)
check("multiply", calculate(4, 3, "multiply") == 12)
check("divide", calculate(6, 3, "divide") == 2)

try:
    calculate(1, 0, "divide")
    check("division_by_zero", False)
except CalculationError:
    check("division_by_zero", True)

try:
    calculate(1, 2, "power")
    check("invalid_operation", False)
except CalculationError:
    check("invalid_operation", True)

print(f"=== SUMMARY === {6 - failures} PASSED, {failures} FAILED")
raise SystemExit(1 if failures else 0)
'''

# the same code, broken: to exercise the repair path
BROKEN_CALCULATOR = CALCULATOR.replace(
    'if operation == "divide" and b == 0:\n        raise CalculationError("division by zero")', "pass")


class ScriptLibrary:
    """The canned answers of the model, in the reader's language."""

    def __init__(self, catalog: MessageCatalog) -> None:
        self._t = catalog

    # ── plans (for the plan parser tests) ────────────────────────────────────

    @staticmethod
    def valid_plan() -> list[dict[str, Any]]:
        return [assistant_text('I will look at databases and distributed systems.\n'
                               '{"goal":"avoid a double booking","domains":["04","08"],'
                               '"technologies":["PostgreSQL"],"needs_code":true,"depth":"deep"}')]

    @staticmethod
    def truncated_plan() -> list[dict[str, Any]]:
        return [assistant_text('{"goal":"something","domains":["04","08"],"technologies":["Postg')]

    # ── answers ──────────────────────────────────────────────────────────────

    def conceptual(self) -> list[dict[str, Any]]:
        return [assistant_text(self._t("demo.script.conceptual_answer"))]

    def no_model(self) -> list[dict[str, Any]]:
        return [assistant_text(self._t("demo.no_model"))]

    def delivery(self, broken: bool = False) -> dict[str, Any]:
        t = self._t
        return {
            "files": {"calculator.py": BROKEN_CALCULATOR if broken else CALCULATOR,
                      "test_calculator.py": CALCULATOR_TEST},
            "test_command": "python3 test_calculator.py",
            "decisions": t("demo.script.decisions"),
            "properties": [
                {"risk": t("demo.script.risk_division"), "property": "calculate(1,0,'divide') raises CalculationError",
                 "test_id": "division_by_zero"},
                {"risk": t("demo.script.risk_operation"), "property": "calculate(1,2,'power') raises CalculationError",
                 "test_id": "invalid_operation"},
                {"risk": t("demo.script.risk_arithmetic"),
                 "property": "add/subtract/multiply/divide return the right result", "test_id": "add"},
            ],
            "uncovered": [t("demo.script.uncovered_precision"), t("demo.script.uncovered_types")],
        }

    def calculator(self) -> list[dict[str, Any]]:
        return [tool_call("deliver_implementation", self.delivery())]

    def broken_then_fixed(self) -> list[dict[str, Any]]:
        return [tool_call("deliver_implementation", self.delivery(broken=True)),
                tool_call("deliver_implementation", self.delivery())]  # the fix

    def broken_json(self) -> list[dict[str, Any]]:
        return [raw_tool_call("deliver_implementation", '{"files": {"a.py": "print(1)"'),
                tool_call("deliver_implementation", self.delivery())]

    @staticmethod
    def unknown_tool() -> list[dict[str, Any]]:
        return [tool_call("invented_tool", {"x": 1}), assistant_text("Fine, it does not exist. Answering without tools.")]

    @staticmethod
    def search_and_answer() -> list[dict[str, Any]]:
        return [tool_call("search_docs", {"query": "outbox pattern"}),
                assistant_text("The outbox pattern solves the dual write.")]

    @staticmethod
    def books_project() -> list[dict[str, Any]]:
        """A whole PROJECT, group by group, as the model would deliver it. It really runs."""
        groups = [tool_call("deliver_group", {"files": {p: books_project.FILES[p] for p in books_project.GROUPS[g]},
                                              "notes": ""})
                  for g in ("core", "domain", "tests", "docs")]
        return [tool_call("specify_project", books_project.SPEC), *groups]
