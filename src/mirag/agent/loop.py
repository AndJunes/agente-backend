"""The agent: a model call and a loop. That is all.

``messages`` IS the agent's memory: everything that happens accumulates there. The model
may answer, or ask for tools; tool results go back into the conversation and the model is
called again, up to ``max_turns``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mirag.core.errors import BudgetExceededError
from mirag.evidence.claims import ClaimAuditor
from mirag.execution.verdict import ExecutionResult
from mirag.llm.gateway import LLMGateway
from mirag.pipeline.prompts import SYSTEM_PROMPT
from mirag.tools.builtin import RUN_CODE
from mirag.tools.registry import ToolRegistry

RECENT = 2
"""How many tool results are sent in full."""
TRIM_THRESHOLD = 40_000
"""From how many characters older tool results start being summarised."""

EventListener = Callable[[dict[str, Any]], None]


@dataclass
class AgentStep:
    kind: str
    """``thought`` | ``tool``."""
    text: str = ""
    name: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    execution: ExecutionResult | None = None

    def as_event(self) -> dict[str, Any]:
        if self.kind == "thought":
            return {"type": "thought", "text": self.text}
        return {"type": "tool", "name": self.name, "args": self.args, "result": self.result}


@dataclass
class AgentResult:
    steps: list[AgentStep]
    answer: str

    @property
    def executions(self) -> list[ExecutionResult]:
        return [s.execution for s in self.steps if s.execution is not None]


def trim_history(messages: list[dict[str, Any]], recent: int = RECENT, threshold: int = TRIM_THRESHOLD) -> list[dict[str, Any]]:
    """Corpus chunks are resent on EVERY turn and the cost grows quadratically.

    The last ``recent`` tool results travel in full; earlier ones are summarised: the model
    already reasoned over them and only needs to remember it consulted them.
    """
    if sum(len(m.get("content") or "") for m in messages) < threshold:
        return messages
    indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    to_trim = set(indices[:-recent] if len(indices) > recent else [])
    return [{**m, "content": f"[trimmed: {len(m['content'])} characters already consulted]"} if i in to_trim else m
            for i, m in enumerate(messages)]


class AgentLoop:
    def __init__(self, tools: ToolRegistry, auditor: ClaimAuditor) -> None:
        self._tools = tools
        self._auditor = auditor

    @property
    def tools(self) -> ToolRegistry:
        return self._tools

    def run(self, question: str, gateway: LLMGateway, system: str | None = None, max_turns: int = 5,
            on_event: EventListener | None = None) -> AgentResult:
        messages: list[dict[str, Any]] = [{"role": "system", "content": system or SYSTEM_PROMPT},
                                          {"role": "user", "content": question}]
        steps: list[AgentStep] = []

        def record(step: AgentStep) -> None:
            steps.append(step)
            if on_event:
                on_event(step.as_event())

        for _ in range(max_turns):
            try:
                message = gateway.chat(trim_history(messages), tools=self._tools.schemas())
            except BudgetExceededError:
                raise  # this one climbs: the caller handles it
            except Exception as exc:  # network, provider JSON, anything
                return AgentResult(steps, f"The run was cut: {type(exc).__name__}: {exc}")
            messages.append(message)

            if not message.get("tool_calls"):
                # The only point where the final prose and the execution record live together.
                # Without this, the model could read an output without markers and write "the 3
                # tests passed", and that sentence reached the user uncontradicted.
                return AgentResult(steps, self._audit(message.get("content"), steps))

            if message.get("content"):  # sometimes it "thinks aloud" before using a tool
                record(AgentStep("thought", text=message["content"]))

            for call in message["tool_calls"]:
                name = call["function"]["name"]
                args: dict[str, Any] = {}
                execution = None
                # the model may send wrong, incomplete or cut arguments: the error is RETURNED
                # to it as the result so it retries; it does not propagate
                try:
                    # strict=False: literal newlines inside strings are invalid strict JSON
                    # and models send them all the time
                    parsed = json.loads(call["function"]["arguments"] or "{}", strict=False)
                    args = parsed if isinstance(parsed, dict) else {}
                    output = self._tools.invoke(name, args)
                    result, execution = output.text, output.execution
                except json.JSONDecodeError as exc:
                    result = f"ERROR: the arguments are not valid JSON ({exc}). Retry."
                except LookupError as exc:
                    result = f"ERROR: {exc}"
                except TypeError as exc:
                    result = f"ERROR: wrong arguments for {name}: {exc}. Check the schema and retry."
                except Exception as exc:
                    result = f"ERROR running {name}: {type(exc).__name__}: {exc}"
                record(AgentStep("tool", name=name, args=args, result=result, execution=execution))
                messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": result})
            # ...and the model is called again, now with the results inside.

        return AgentResult(steps, self._audit("I ran out of turns.", steps))

    def _audit(self, answer: str | None, steps: list[AgentStep]) -> str:
        """The warning is prepended; the model's text is kept whole underneath."""
        executions = [s.execution for s in steps if s.execution is not None and s.name == RUN_CODE]
        text, _status = self._auditor.apply(answer or "", executions)
        return text
