"""Which free models can actually do this agent's job?

    python scripts/probe_models.py                 # every free model that advertises tools
    python scripts/probe_models.py --quick         # a toy file: fast, and it lies (see below)
    python scripts/probe_models.py MODEL [MODEL…]  # only these

Free models rotate: one disappears, another appears, and `MIRAG_MODEL` has to change. This
script answers which one to change it to, and it exists because the obvious way of deciding
gave the wrong answer twice.

THE TWO THINGS A MODEL CARD DOES NOT TELL YOU

1. **Whether it can write a newline inside a tool call.** The project branch delivers files
   through ``deliver_group``, so every line of every file travels as a JSON string.
   `nvidia/nemotron-3-ultra-550b-a55b:free` cannot: it drops the line breaks entirely and
   emits stray ones outside the string. It produced a fifteen-file project that was fifteen
   lines long — ``import jsonimport urllib.parse`` — which passed packaging and offered a
   download button. "Supports tools" was true and useless.

2. **Whether it can do it on a REAL request.** This is why ``--quick`` is not the default.
   Asked for one small file, four models wrote clean multi-line Python. Asked for what this
   agent actually sends — the full contract, the interface list, five files at once — three
   of those four returned an empty message with ``finish_reason: length``: the entire output
   budget spent on reasoning, nothing emitted. A toy probe would have chosen any of them.

So the default probe is the real one. It costs nothing (these are free models) and a minute
per model, and it is the only version whose answer has ever been right.

A model is USABLE when it returns a tool call whose files parse, are text, and carry real
line breaks. Anything else is reported with the reason, because the reasons differ and so do
the fixes: `length` wants a bigger budget or a model that thinks less, `error` is the
provider, prose is the model ignoring `tool_choice`.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from mirag.execution.interpreters import InterpreterRegistry
from mirag.projects.generator import DELIVER_GROUP_TOOL, ProjectGenerator

MODELS_URL = "https://openrouter.ai/api/v1/models"
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TOKENS = 16_000
FLAT_AFTER = 200
"""Characters past which a file with no line break is not a file. Matches the generator."""

QUICK = """\
  app/greet.py — a module docstring, a function greet(name), and an `if __name__` block"""

REAL = """\
  bike_workshop/__init__.py — the package
  bike_workshop/db.py — sqlite connection, schema and a write lock
  bike_workshop/models.py — Bike, Part, Volunteer, WorkSession as dataclasses
  bike_workshop/api.py — the request handler with the CRUD routes
  bike_workshop/server.py — create_server(port=0, db=":memory:")"""

INTERFACES = (
    "PROJECT INTERFACES. You may only import what appears here or the standard\n"
    "library. An import that is not here is detected with AST and the delivery is\n"
    "rejected.\n\n"
    + "\n".join(
        f"  {path:<34} exports: {exports}   [PENDING - do not import it yet]"
        for path, exports in (
            ("bike_workshop/__init__.py", "(nothing to import)"),
            ("bike_workshop/db.py", "get_connection, write_lock, init_schema"),
            ("bike_workshop/models.py", "Bike, Part, Volunteer, WorkSession"),
            ("bike_workshop/api.py", "APIHandler"),
            ("bike_workshop/server.py", "create_server"),
            ("tests/test_bike.py", "(nothing to import)"),
            ("README.md", "(nothing to import)"),
        )
    )
)


def free_models_with_tools() -> list[str]:
    with urllib.request.urlopen(MODELS_URL, timeout=60) as response:
        models = json.load(response)["data"]
    return sorted(
        model["id"]
        for model in models
        if model["id"].endswith(":free") and "tools" in (model.get("supported_parameters") or [])
    )


def files_of(arguments: object) -> dict[str, object]:
    """The same two shapes the generator accepts: an object, or a list of objects."""
    if isinstance(arguments, dict):
        return dict(arguments)
    if not isinstance(arguments, list):
        return {}
    return {
        entry["path"]: entry.get("content")
        for entry in arguments
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }


def probe(model: str, quick: bool) -> str:
    """One line saying whether this model can be `MIRAG_MODEL`, and if not, why not."""
    contract = ProjectGenerator(InterpreterRegistry()).contract()
    body = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "tools": [DELIVER_GROUP_TOOL],
        # Forced, exactly as the generator forces it for a delivery.
        "tool_choice": {"type": "function", "function": {"name": "deliver_group"}},
        "messages": [
            {"role": "system", "content": contract if quick else f"{contract}\n\n{INTERFACES}"},
            {
                "role": "user",
                "content": "Write the COMPLETE content of these files of the group 'core':\n"
                + (QUICK if quick else REAL),
            },
        ],
    }
    request = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + os.environ.get("OPENROUTER_API_KEY", ""),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        return f"unreachable      HTTP {error.code}"
    except Exception as error:  # noqa: BLE001 — every failure is a result here, not a crash
        return f"unreachable      {type(error).__name__}: {str(error)[:60]}"

    if "choices" not in payload:
        return f"no completion    {str((payload.get('error') or {}).get('message'))[:70]}"
    choice = payload["choices"][0]
    message = choice.get("message") or {}
    finish = choice.get("finish_reason")
    calls = message.get("tool_calls") or []
    if not calls:
        prose = len(message.get("content") or "")
        # `length` with nothing written is the interesting one: the model reasoned until the
        # budget ran out. It is not a rate limit and not a bad prompt.
        return f"no tool call     finish={finish}, {prose} chars of prose"
    raw = calls[0].get("function", {}).get("arguments") or ""
    try:
        files = files_of(json.loads(raw, strict=False).get("files"))
    except (ValueError, AttributeError) as error:
        return f"unparseable      {type(error).__name__}, {len(raw)} chars, ends {raw[-40:]!r}"
    if not files:
        return f"no files         finish={finish}, keys were empty"
    flat = [
        path
        for path, content in files.items()
        if isinstance(content, str) and len(content) > FLAT_AFTER and "\n" not in content
    ]
    if flat:
        return f"NO NEWLINES      {len(flat)}/{len(files)} files on one line: {flat[0]}"
    lines = sum(c.count("\n") for c in files.values() if isinstance(c, str))
    chars = sum(len(c) for c in files.values() if isinstance(c, str))
    return f"USABLE           {len(files)} files, {lines} lines, {chars} chars"


def main(argv: list[str]) -> int:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set: there is nothing to probe.", file=sys.stderr)
        return 2
    quick = "--quick" in argv
    named = [arg for arg in argv if not arg.startswith("-")]
    models = named or free_models_with_tools()
    print(f"{len(models)} models, {'toy' if quick else 'real'} request\n")
    usable = []
    for model in models:
        verdict = probe(model, quick)
        print(f"  {model:<50} {verdict}", flush=True)
        if verdict.startswith("USABLE"):
            usable.append(model)
    print("\nUsable:", ", ".join(usable) or "none — try again, free providers rate-limit hard")
    return 0 if usable else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
