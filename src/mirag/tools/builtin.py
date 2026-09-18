"""The built-in tools. The description IS the routing signal: each says what it is for AND
what it is not for, because the model chooses by reading it."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from mirag.execution.calculator import SafeCalculator
from mirag.execution.runner import CodeRunner
from mirag.retrieval.search import KnowledgeSearch
from mirag.tools.registry import FunctionTool, ToolOutput, ToolRegistry

SEARCH_TOOLS = ("search_docs", "search_tradeoffs", "search_failures", "search_anti_patterns", "related_boxes")
RUN_CODE = "run_code"

BOX_NAMES = ("Fundamentals, Web & Protocols, APIs, Databases, Architecture, Security, Payments, "
             "Distributed Systems, Performance, Reliability, Testing, Observability, "
             "Cloud & Infrastructure, DevOps, Files & Data, Integrations, Business Logic, "
             "AI Backend, System Design")


def _string_parameter(name: str, description: str) -> dict[str, Any]:
    return {"type": "object", "properties": {name: {"type": "string", "description": description}},
            "required": [name]}


def build_default_tools(
    search: KnowledgeSearch,
    runner: CodeRunner,
    calculator: SafeCalculator | None = None,
    now: Callable[[], datetime] = datetime.now,
) -> ToolRegistry:
    calculator = calculator or SafeCalculator()
    interpreters = runner.interpreters.describe()

    def run_code(files: object, command: str) -> ToolOutput:
        result = runner.run(files if isinstance(files, dict) else {}, command)
        return ToolOutput(result.text, result)

    return ToolRegistry([
        FunctionTool(
            "search_docs",
            "Explains a technical concept: what it is, how it works, how it is implemented. It is "
            "the general search over 19 senior backend boxes (fundamentals, HTTP, APIs, databases, "
            "architecture, security, payments, distributed systems, performance, reliability, "
            "testing, observability, cloud, devops, files, integrations, business logic, AI and "
            "system design). USE THIS by default. Do not use it to compare options or anticipate "
            "failures: search_tradeoffs and search_failures exist for that.",
            _string_parameter("query", "Technical terms to search for"),
            lambda query: search.docs(query),
        ),
        FunctionTool(
            "search_tradeoffs",
            "Returns the decision CARDS of the concepts related to a topic: when to use each thing, "
            "its limits, the anti-pattern and the trade-off you accept. Use it when you must CHOOSE "
            "between alternatives or justify a decision. It returns condensed decision criteria, not "
            "explanations: to understand a concept, use search_docs.",
            _string_parameter("topic", "The topic or decision to evaluate"),
            lambda topic: search.tradeoffs(topic),
        ),
        FunctionTool(
            "search_failures",
            "Returns only what can GO WRONG on a topic: known failure modes, symptoms and "
            "mitigations. Use it to anticipate risks, review a design or debug an incident. It does "
            "not explain what something is nor help choose between options.",
            _string_parameter("topic", "The component or area whose failures matter"),
            lambda topic: search.failures(topic),
        ),
        FunctionTool(
            "related_boxes",
            "Returns the dependency map between knowledge areas: which boxes one box references and "
            "which reference it, with the weight of each link. Use it to discover which areas a "
            "cross-cutting problem touches. It returns area names and numbers, NOT technical content.",
            _string_parameter("box", f"Number (01-19) or English name of the box: {BOX_NAMES}"),
            lambda box: search.related_boxes(box),
        ),
        FunctionTool(
            "search_anti_patterns",
            "Returns the KNOWN mistakes on a topic: what NOT to do and what to do instead. Use it "
            "when reviewing code or a design, to contrast it with documented failures. It does not "
            "explain concepts nor compare options.",
            _string_parameter("topic", "The component or pattern to contrast"),
            lambda topic: search.anti_patterns(topic),
        ),
        FunctionTool(
            RUN_CODE,
            "RUNS code for real and returns its real output and exit code. It is the only way to "
            "PROVE that something works instead of giving an opinion. Use it to run the tests of "
            "code you just wrote, above all concurrency, idempotency and edge cases. Interpreters "
            f"allowed ON THIS MACHINE: {interpreters}. Do not use any other one: the command is "
            "rejected without running and you prove nothing. ESSENTIAL: each test must print an "
            "exact line TEST:<id>:PASS or TEST:<id>:FAIL. Without those markers the run is reported "
            "as NO EVIDENCE however well the code works, because there is no way to know what was "
            "tested.",
            {
                "type": "object",
                "properties": {
                    "files": {"type": "object", "additionalProperties": {"type": "string"},
                              "description": "Map path -> content. Include the code AND the tests."},
                    "command": {"type": "string",
                                "description": f"How to run it. It starts with one of: {interpreters}"},
                },
                "required": ["files", "command"],
            },
            run_code,
        ),
        FunctionTool(
            "calculate",
            "Evaluates an arithmetic expression, for example '20 - 8' or '1847 * 293'.",
            _string_parameter("expression", "Arithmetic expression"),
            lambda expression: calculator.evaluate(expression),
        ),
        FunctionTool(
            "current_time",
            "Returns the current date and time.",
            {"type": "object", "properties": {}},
            lambda: now().strftime("%Y-%m-%d %H:%M"),
        ),
    ])
