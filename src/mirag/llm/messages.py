"""Builders for chat messages with the exact shape OpenRouter returns."""

from __future__ import annotations

import json
from typing import Any


def assistant_text(content: str) -> dict[str, Any]:
    """A plain answer, without tool calls."""
    return {"role": "assistant", "content": content}


def tool_call(
    name: str,
    arguments: dict[str, Any],
    content: str | None = None,
    call_id: str = "call_1",
) -> dict[str, Any]:
    """An answer that asks to run a tool."""
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)},
            }
        ],
    }


def raw_tool_call(name: str, raw_arguments: str, call_id: str = "call_1") -> dict[str, Any]:
    """A tool call with the arguments AS IS - to simulate broken JSON."""
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": call_id, "type": "function", "function": {"name": name, "arguments": raw_arguments}}
        ],
    }


def function_tool(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """A tool schema in the OpenAI / OpenRouter function-calling format."""
    return {
        "type": "function",
        "function": {"name": name, "description": description, "parameters": parameters},
    }


def first_tool_arguments(message: dict[str, Any], diagnostics: list[str] | None = None) -> dict[str, Any] | None:
    """The parsed arguments of the first tool call, or ``None``.

    ``diagnostics`` collects WHY they could not be read: "0 files" is a silence that does not
    distinguish "the model answered in prose" from "the JSON was cut in half by max_tokens",
    and those are two different problems with two different fixes.
    """
    note = diagnostics.append if diagnostics is not None else (lambda _msg: None)
    calls = message.get("tool_calls") or []
    if not calls:
        text = (message.get("content") or "").strip()
        note(f"the model did not call the tool; it answered {len(text)} characters of text: {text[:120]!r}")
        return None
    raw = (calls[0].get("function") or {}).get("arguments") or "{}"
    try:
        value = json.loads(raw, strict=False)
    except (ValueError, TypeError) as exc:
        note(f"the tool-call JSON could not be read ({type(exc).__name__}: {exc}); "
             f"{len(raw)} characters, ending in {raw[-60:]!r}")
        return None
    if not isinstance(value, dict):
        note(f"the tool-call arguments are a {type(value).__name__}, not an object")
        return None
    return value
