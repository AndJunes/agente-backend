from __future__ import annotations

from datetime import datetime

import pytest

from mirag.execution.runner import CodeRunner
from mirag.execution.verdict import ExecutionStatus
from mirag.retrieval.engine import RetrievalEngine
from mirag.tools.builtin import build_default_tools
from mirag.tools.registry import FunctionTool, ToolOutput, ToolRegistry

EXPECTED = {"search_docs", "search_tradeoffs", "search_failures", "search_anti_patterns", "related_boxes",
            "run_code", "calculate", "current_time"}


def test_the_default_tools_and_their_schemas(engine: RetrievalEngine, runner: CodeRunner) -> None:
    registry = build_default_tools(engine.search, runner)
    assert set(registry.names) == EXPECTED
    names = {schema["function"]["name"] for schema in registry.schemas()}
    assert names == EXPECTED
    assert {s["function"]["name"] for s in registry.schemas(only=["calculate"])} == {"calculate"}


def test_the_run_code_description_only_lists_interpreters_that_exist(engine: RetrievalEngine,
                                                                    runner: CodeRunner) -> None:
    description = build_default_tools(engine.search, runner).get("run_code").description
    for name in runner.interpreters.available:
        assert name in description
    assert "bash" not in description


def test_an_unknown_tool_lists_the_real_ones() -> None:
    registry = ToolRegistry([FunctionTool("a", "d", {"type": "object", "properties": {}}, lambda: "x")])
    with pytest.raises(LookupError, match="available ones are: a\\."):
        registry.invoke("invented", {})


def test_tools_return_text_and_optionally_the_execution(engine: RetrievalEngine, runner: CodeRunner) -> None:
    registry = build_default_tools(engine.search, runner, now=lambda: datetime(2026, 9, 18, 12, 30))
    assert registry.invoke("calculate", {"expression": "2 + 2"}) == ToolOutput("4")
    assert registry.invoke("current_time", {}).text == "2026-09-18 12:30"
    assert registry.invoke("search_docs", {"query": "idempotency"}).text
    related = registry.invoke("related_boxes", {"box": "07"}).text
    assert related.startswith("[07")


@pytest.mark.slow
def test_run_code_carries_the_structured_result(engine: RetrievalEngine, runner: CodeRunner) -> None:
    output = build_default_tools(engine.search, runner).invoke(
        "run_code", {"files": {"t.py": "print('TEST:x:PASS')"}, "command": "python3 t.py"})
    assert output.execution is not None
    assert output.execution.status is ExecutionStatus.PASSED
    assert output.text.startswith("TESTS PASSED")


def test_run_code_with_files_that_are_not_a_mapping(engine: RetrievalEngine, runner: CodeRunner) -> None:
    output = build_default_tools(engine.search, runner).invoke("run_code", {"files": "oops", "command": "python3 t"})
    assert output.execution is not None
    assert output.execution.status is ExecutionStatus.NOT_EXECUTED
