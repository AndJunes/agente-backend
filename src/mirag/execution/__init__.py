"""Executing code and deciding, from the execution alone, what it proved.

:mod:`mirag.execution.verdict` is the ONLY place where "green" is decided. It used to be
re-derived in eight places with expressions that disagreed: a TIMEOUT was an "error" on one
line and "green" fourteen lines below.
"""

from mirag.execution.calculator import SafeCalculator
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.runner import CodeRunner
from mirag.execution.syntax import SyntaxChecker
from mirag.execution.verdict import MARKER, ExecutionResult, ExecutionStatus

__all__ = [
    "MARKER",
    "CodeRunner",
    "ExecutionResult",
    "ExecutionStatus",
    "InterpreterRegistry",
    "SafeCalculator",
    "SyntaxChecker",
]
