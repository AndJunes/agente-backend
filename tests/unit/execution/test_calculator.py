"""The calculator evaluates what the MODEL writes, inside the server process: allow-list only."""

from __future__ import annotations

import pytest

from mirag.execution.calculator import SafeCalculator


@pytest.mark.parametrize(("expression", "expected"), [
    ("20 - 8", "12"), ("1847 * 293", "541171"), ("7 / 2", "3.5"), ("-(3 ** 2)", "-9"), ("10 % 4", "2"),
])
def test_arithmetic(expression: str, expected: str) -> None:
    assert SafeCalculator().evaluate(expression) == expected


@pytest.mark.parametrize("expression", [
    "__import__('os').environ['OPENROUTER_API_KEY']",
    "open('/etc/passwd').read()",
    "(1).__class__",
    "[1, 2][0]",
    "x + 1",
    "True + 1",
    "'a' * 3",
])
def test_anything_but_numbers_is_rejected(expression: str) -> None:
    assert SafeCalculator().evaluate(expression).startswith(("Rejected", "Not a valid"))


def test_huge_exponents_are_refused_before_hanging_the_process() -> None:
    assert "exponent too large" in SafeCalculator().evaluate("2 ** 10 ** 9")


def test_division_by_zero_and_syntax_errors_are_answers_not_exceptions() -> None:
    calculator = SafeCalculator()
    assert calculator.evaluate("1 / 0") == "Division by zero."
    assert calculator.evaluate("2 +").startswith("Not a valid expression")
