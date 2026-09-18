"""Tool abstraction and registry. New tools are added, never patched in (open/closed)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from mirag.execution.verdict import ExecutionResult
from mirag.llm.messages import function_tool


@dataclass(frozen=True, slots=True)
class ToolOutput:
    text: str
    """What the model reads."""
    execution: ExecutionResult | None = None
    """Set by tools that execute code: the structured record, not just its text."""


class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    @property
    def schema(self) -> dict[str, Any]:
        return function_tool(self.name, self.description, self.parameters)

    @abstractmethod
    def invoke(self, **arguments: Any) -> ToolOutput: ...


class FunctionTool(Tool):
    """A tool backed by a callable returning ``str`` or :class:`ToolOutput`."""

    def __init__(self, name: str, description: str, parameters: dict[str, Any],
                 handler: Callable[..., str | ToolOutput]) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self._handler = handler

    def invoke(self, **arguments: Any) -> ToolOutput:
        value = self._handler(**arguments)
        return value if isinstance(value, ToolOutput) else ToolOutput(str(value))


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    @property
    def names(self) -> list[str]:
        return sorted(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def schemas(self, only: Iterable[str] | None = None) -> list[dict[str, Any]]:
        wanted = set(only) if only is not None else None
        return [t.schema for t in self._tools.values() if wanted is None or t.name in wanted]

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def invoke(self, name: str, arguments: dict[str, Any]) -> ToolOutput:
        if name not in self._tools:
            # without the list the model repeats the same impossible call and burns a turn
            raise LookupError(
                f"the tool {name!r} does NOT exist. The only available ones are: "
                f"{', '.join(self.names)}. Use one of those or answer without tools."
            )
        return self._tools[name].invoke(**arguments)
