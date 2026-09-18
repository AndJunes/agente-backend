"""Arithmetic on an expression written by the MODEL.

This used to be ``eval(expression)`` with a comment saying "never use eval in production".
It runs inside the server process, with no subprocess, no timeout and no isolation, so
``__import__('os').environ['OPENROUTER_API_KEY']`` was a perfectly valid "expression".

Only these nodes and operators are allowed; everything else is rejected by default. An
allow-list cannot "forget" to forbid something new; a deny-list can.
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable
from typing import Any

_OPERATORS: dict[type, Callable[..., Any]] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
MAX_EXPONENT = 1000
"""``2**10**9`` is not a code attack, but it hangs the process all the same."""


class SafeCalculator:
    def _evaluate(self, node: ast.AST) -> int | float:
        """Arithmetic and nothing else: no names, attributes, calls or subscripts."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, int | float):
                raise ValueError(f"numbers only: {node.value!r}")
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            left, right = self._evaluate(node.left), self._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and (abs(right) > MAX_EXPONENT or abs(left) > MAX_EXPONENT):
                raise ValueError(f"exponent too large (maximum {MAX_EXPONENT})")
            return _OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](self._evaluate(node.operand))
        raise ValueError(f"not allowed: {type(node).__name__}")

    def evaluate(self, expression: str) -> str:
        try:
            tree = ast.parse(str(expression).strip(), mode="eval")
        except SyntaxError as exc:
            return f"Not a valid expression: {exc.msg}"
        try:
            return str(self._evaluate(tree.body))
        except ValueError as exc:
            return f"Rejected: {exc}. Only arithmetic with numbers is allowed."
        except ZeroDivisionError:
            return "Division by zero."
        except (OverflowError, MemoryError) as exc:
            return f"Number out of range: {type(exc).__name__}"
