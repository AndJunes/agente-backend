"""The batches of a group are asked for at the same time, and nothing is lost doing it.

    python scripts/check_parallel.py

Sequentially, a plan of twenty files is four batches at the measured 234 seconds each — over
fifteen minutes, which is why a hard cap on the number of planned files looked like the answer
and was not. OpenRouter documents 20 requests a minute for free models and no concurrency
limit at all; at one call every 234 seconds the generator was using 0.25 of that 20.

Concurrency is cheap here and correctness is not, so this checks the three things that break
when work moves off one thread:

  the calls really overlap        — otherwise the change bought nothing
  every file still arrives        — `project.add` has one writer, and results are applied in
                                    order from the calling thread rather than by the workers
  the call count stays exact      — it is what `MAX_CALLS` and the spending cap are read from

No model and no network: the double answers instantly and records when it was called.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from mirag.execution.interpreters import InterpreterRegistry
from mirag.i18n.catalog import MessageCatalog
from mirag.llm.budget import Budget
from mirag.llm.gateway import LLMGateway
from mirag.projects.generator import CONCURRENT_BATCHES, GROUP_BATCH, ProjectGenerator

WIDE = [f"app/module_{i:02d}.py" for i in range(20)]
PLAN = {
    "name": "wide-api", "language": "python", "framework": "stdlib", "database": "sqlite",
    "architecture": "layered", "entity": "thing", "resource": "/things", "fields": ["id"],
    "dependencies": [], "test_command": "python3 -m unittest", "assumptions": [],
    "files": [
        {"path": "app/__init__.py", "kind": "code", "purpose": "pkg", "exports": [],
         "depends_on": [], "group": "core"},
        {"path": "app/main.py", "kind": "entrypoint", "purpose": "server",
         "exports": ["create_server"], "depends_on": [], "group": "core"},
        *[{"path": path, "kind": "code", "purpose": f"part {i}", "exports": [],
           "depends_on": [], "group": "core"} for i, path in enumerate(WIDE)],
        {"path": "tests/__init__.py", "kind": "test", "purpose": "pkg", "exports": [],
         "depends_on": [], "group": "tests"},
        {"path": "tests/test_api.py", "kind": "test", "purpose": "crud", "exports": [],
         "depends_on": [], "group": "tests"},
        {"path": "README.md", "kind": "doc", "purpose": "readme", "exports": [],
         "depends_on": [], "group": "docs"},
    ],
}


@dataclass
class Usage:
    prompt_tokens: int = 10
    completion_tokens: int = 10
    cost_usd: float = 0.0


@dataclass
class Response:
    message: dict
    usage: Usage


class Slow:
    """Answers every file it is asked for, after a pause, and records the overlap."""

    name = "slow-double"
    simulated = True
    PAUSE = 0.35

    def __init__(self) -> None:
        self.spans: list[tuple[float, float]] = []
        self.batch_sizes: list[int] = []
        self.in_flight = 0
        self.peak = 0
        self._lock = threading.Lock()

    def complete(self, messages, tools=None, require=None):
        started = time.monotonic()
        with self._lock:
            self.in_flight += 1
            self.peak = max(self.peak, self.in_flight)
        try:
            user = messages[-1]["content"]
            wanted = [line.strip().split(" — ")[0] for line in user.splitlines()
                      if line.startswith("  ")]
            if "Without writing code" in messages[0]["content"]:
                arguments = PLAN
                name = "specify_project"
            else:
                with self._lock:
                    self.batch_sizes.append(len(wanted))
                arguments = {"files": {path: f"# {path}\n" + (
                    "def create_server(port=0, db=':memory:'):\n    return None\n"
                    if path.endswith("main.py") else "x = 1\n") for path in wanted}}
                name = "deliver_group"
            time.sleep(self.PAUSE)
            return Response({"role": "assistant", "content": None, "tool_calls": [{
                "id": "c", "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)}}]}, Usage())
        finally:
            with self._lock:
                self.in_flight -= 1
                self.spans.append((started, time.monotonic()))


def overlapping(spans: list[tuple[float, float]]) -> int:
    """The most calls that were in flight at the same moment."""
    events = sorted([(s, 1) for s, _ in spans] + [(e, -1) for _, e in spans])
    peak = live = 0
    for _, delta in events:
        live += delta
        peak = max(peak, live)
    return peak


def main() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    model = Slow()
    catalog = MessageCatalog.from_file("en", Path("src/mirag/locales/en/messages.json"))
    generator = ProjectGenerator(InterpreterRegistry())
    started = time.monotonic()
    result = generator.generate("a wide api", "", LLMGateway(model, Budget(), offline=False),
                                catalog)
    elapsed = time.monotonic() - started

    planned = {f["path"] for f in PLAN["files"]}
    built = {f.path for f in result.project.files()} if result.project else set()
    delivery_calls = len(model.batch_sizes)

    print(f"\n=== {len(planned)} planned files, {delivery_calls} delivery calls "
          f"in {elapsed:.1f}s ===")
    for step in result.steps:
        if step.name.startswith("generation:"):
            print(f"  [{step.status:<9}] {step.name:<20} {step.summary}")

    print("\n=== the calls actually overlapped ===")
    peak = overlapping(model.spans)
    check("more than one at a time", peak > 1, f"peak {peak} concurrent")
    check("never past the cap", peak <= CONCURRENT_BATCHES, f"peak {peak} of {CONCURRENT_BATCHES}")
    # Sequentially this many calls would take at least calls * PAUSE.
    floor = delivery_calls * model.PAUSE
    check("faster than doing them one by one", elapsed < floor,
          f"{elapsed:.1f}s against {floor:.1f}s sequential")

    print("\n=== nothing was lost writing them ===")
    missing = sorted(planned - built)
    check("every planned file exists", not missing, str(missing[:4]))
    check("no batch went over the size", all(n <= GROUP_BATCH for n in model.batch_sizes),
          str(sorted(set(model.batch_sizes))))

    print("\n=== the counting stayed exact ===")
    # One specify call plus the deliveries. `result.calls` is what MAX_CALLS and the budget
    # are read from, so an undercount here spends more than it says.
    check("calls reported match calls made", result.calls == delivery_calls + 1,
          f"reported {result.calls}, made {delivery_calls + 1}")

    print("\n=== no worker thread outlived the run ===")
    alive = [t.name for t in threading.enumerate() if "ThreadPoolExecutor" in t.name]
    check("the pool was closed", not alive, str(alive))

    print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILED: {failures}"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
