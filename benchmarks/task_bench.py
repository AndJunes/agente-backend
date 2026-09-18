"""Task bench: is the new version a better TOOL, not only a better metric?

It runs the same tasks with and without the retrieval plan and compares three dimensions:

    GOOD    properties verified by execution / declared, and green runs
    CHEAP   cost, tokens and context size
    FAST    model calls and latency (what you wait for while watching the screen)

Both arms go through ``QuestionPipeline.run``, the path the server runs:

    baseline   ``forced_plan`` = the EMPTY plan (narrows nothing: no boxes, no filters)
    default    no forced plan: the pipeline deduces its own, as in production

The baseline keeps ONE thing from the request: its intent (``needs_code`` / ``needs_project``).
``EMPTY_PLAN`` alone says "no code needed", the code stage then offers the model no delivery
tool, and the arm would measure "the model could not deliver" instead of "retrieval was not
narrowed". The legacy bench did the same (it only emptied the boxes of the deduced plan).

It costs real money: every task is a full run (~$0.10 each with the default model).

    MIRAG_OFFLINE=0 python -m benchmarks.task_bench                  # both arms, then compare
    MIRAG_OFFLINE=0 python -m benchmarks.task_bench --arm baseline   # one arm (merged into results)
    python -m benchmarks.task_bench --compare                        # compare what is saved
    python -m benchmarks.task_bench --dry                            # scripted calculator, free

``--dry`` (or the offline lock on) replaces the tasks with the canonical calculator request
answered by its script: it proves the harness works end to end, nothing about the model.
Results go to ``benchmarks/results/task_bench.json``.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

from benchmarks.cases import DATASETS_DIR
from benchmarks.harness import (
    RESULTS_DIR,
    isolated_container,
    read_json,
    utf8_console,
    warm_up,
    write_json,
)
from mirag.container import Container
from mirag.llm.gateway import LLMGateway
from mirag.observability.tracing import evidence_counts
from mirag.pipeline.models import PipelineRun
from mirag.retrieval.plan import EMPTY_PLAN, RetrievalPlan

DEFAULT_OUTPUT = RESULTS_DIR / "task_bench.json"
TASKS_FILE = "tasks.json"


class Arm(StrEnum):
    BASELINE = "baseline"
    DEFAULT = "default"


@dataclass(frozen=True, slots=True)
class Task:
    name: str
    request: str


def load_tasks(locale: str, directory: Path = DATASETS_DIR) -> tuple[Task, ...]:
    data = json.loads((directory / locale / TASKS_FILE).read_text(encoding="utf-8"))
    return tuple(Task(item["name"], item["request"]) for item in data["tasks"])


# ── running ──────────────────────────────────────────────────────────────────


class TaskBench:
    """Runs tasks through the production pipeline under one arm or the other."""

    def __init__(self, container: Container, locale: str = "en", dry: bool = True) -> None:
        self._container = container
        self.locale = locale
        self.dry = dry
        self._demos = container.demos(locale)
        warm_up(container, locale)

    def tasks(self, limit: int | None = None) -> tuple[Task, ...]:
        if self.dry:  # the script only knows how to answer the calculator
            return (Task("calculator", self._demos.canonical_question("construction")),)
        tasks = load_tasks(self.locale)
        return tasks[:limit] if limit else tasks

    def _gateway(self) -> LLMGateway:
        """A fresh one per task, with its own budget: nothing carries over between tasks."""
        gateways = self._container.gateways
        return gateways.create(script=self._demos.script("code")) if self.dry else gateways.create()

    def plan_for(self, arm: Arm, request: str) -> RetrievalPlan | None:
        """``None`` = let the pipeline deduce the plan (the default arm)."""
        if arm is Arm.DEFAULT:
            return None
        deduced = self._container.engines.get(self.locale).deducer.deduce(request)
        return replace(EMPTY_PLAN, needs_code=deduced.needs_code, needs_project=deduced.needs_project)

    def run_task(self, task: Task, arm: Arm) -> dict[str, Any]:
        gateway = self._gateway()
        started = time.time()
        row: dict[str, Any] = {"task": task.name, "arm": arm.value, "error": None}
        try:
            run = self._container.pipeline.run(task.request, gateway, self.locale, persist=False,
                                               forced_plan=self.plan_for(arm, task.request),
                                               version=f"bench:{arm.value}")
            row.update(self.describe(run))
        except Exception as exc:  # a task that blows up IS a result
            row.update({"status": "exception", "green": False, "error": f"{type(exc).__name__}: {exc}"[:200]})
        spent = gateway.budget.snapshot()
        row.update({"seconds": round(time.time() - started, 1), "cost_usd": round(spent.cost_usd, 5),
                    "calls": spent.calls, "tokens": spent.tokens})
        return row

    @staticmethod
    def describe(run: PipelineRun) -> dict[str, Any]:
        counts, verified, in_simulation = evidence_counts(run.evidence)
        context = run.step("context")
        if run.certificate is not None:
            status, green = run.certificate.status.value, run.certificate.ok
        elif run.execution is not None:
            status, green = run.execution.status.value, run.execution.is_green
        else:
            status, green = "no_code", False
        return {
            "mode": "project" if run.certificate is not None else "pipeline",
            "status": status,
            "green": green,
            "verified_success": round(verified, 3),
            # apart on purpose: proved against a simulation is NOT proved
            "success_in_simulation": round(in_simulation, 3),
            "properties": counts,
            "repaired": run.repaired,
            "context_tokens": (context.detail or {}).get("approx_tokens") if context else None,
            "plan_origin": run.plan.origin if run.plan else None,
            "boxes": list(run.plan.domains) if run.plan else [],
        }

    def run_arm(self, arm: Arm, tasks: Sequence[Task]) -> list[dict[str, Any]]:
        rows = []
        for task in tasks:
            print(f"\n{'─' * 70}\n{arm.value} · {task.name}\n{'─' * 70}", flush=True)
            row = self.run_task(task, arm)
            rows.append(row)
            print(f"  {str(row['status']).upper()} · {row.get('properties', {}).get('verified', 0)} verified · "
                  f"{row['calls']} calls · {row['tokens']:,} tokens · ${row['cost_usd']:.4f} · "
                  f"{row['seconds']:.0f}s" + (f" · {row['error']}" if row["error"] else ""), flush=True)
        return rows


# ── comparing ────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Dimension:
    field: str
    label: str
    higher_is_better: bool


DIMENSIONS: tuple[Dimension, ...] = (
    Dimension("verified_success", "verified success (GOOD)", True),
    Dimension("green", "green runs (GOOD)", True),
    Dimension("cost_usd", "cost per task (CHEAP)", False),
    Dimension("tokens", "tokens per task (CHEAP)", False),
    Dimension("context_tokens", "context (CHEAP)", False),
    Dimension("calls", "model calls (FAST)", False),
    Dimension("seconds", "latency (FAST)", False),
)
NOISE_PERCENT = 5.0


def arm_median(rows: Sequence[Mapping[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return float(statistics.median(values)) if values else None


def compare(arms: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Lines comparing the default arm against the baseline, dimension by dimension."""
    if not all(arm.value in arms for arm in Arm):
        return ["Both arms are needed. Run --arm baseline and --arm default first (or both at once)."]
    base, new = arms[Arm.BASELINE.value], arms[Arm.DEFAULT.value]
    lines = []
    if base.get("dry") != new.get("dry") or base.get("locale") != new.get("locale"):
        lines.append("!! the arms were run under different conditions (dry/locale): the comparison is not fair")
    lines.append(f"{'arm':10} {'n':>3} {'verified':>9} {'green':>7} {'$/task':>9} {'tokens':>9} "
                 f"{'ctx':>7} {'calls':>6} {'sec':>6}")
    for name in (Arm.BASELINE.value, Arm.DEFAULT.value):
        rows = arms[name]["rows"]
        greens = sum(1 for row in rows if row.get("green"))

        def cell(field: str, fmt: str, rows: Sequence[Mapping[str, Any]] = rows) -> str:
            value = arm_median(rows, field)
            return "-" if value is None else format(value, fmt)

        lines.append(f"{name:10} {len(rows):>3} {cell('verified_success', '.2f'):>9} {f'{greens}/{len(rows)}':>7} "
                     f"{cell('cost_usd', '.4f'):>9} {cell('tokens', ',.0f'):>9} {cell('context_tokens', ',.0f'):>7} "
                     f"{cell('calls', '.0f'):>6} {cell('seconds', '.0f'):>6}")
    lines.append(f"\n{Arm.DEFAULT.value} against {Arm.BASELINE.value} (medians):")
    for dimension in DIMENSIONS:
        before = arm_median(base["rows"], dimension.field)
        after = arm_median(new["rows"], dimension.field)
        if before is None or after is None:
            continue
        change = (after - before) / before * 100 if before else 0.0
        fine = abs(change) < NOISE_PERCENT or (change > 0) == dimension.higher_is_better
        lines.append(f"  {'ok' if fine else '!!'} {dimension.label:28} {before:>10.4f} -> {after:<10.4f} ({change:+.0f}%)")
    lines.append("\nThe rule: an improvement only counts if it does not seriously degrade the other\n"
                 "dimensions. If verified success drops, saving cost does not make up for it.")
    return lines


# ── entry point ──────────────────────────────────────────────────────────────


def load_results(path: Path) -> dict[str, Any]:
    try:
        data = read_json(path)
    except (OSError, ValueError):
        return {"arms": {}}
    return data if isinstance(data, dict) and isinstance(data.get("arms"), dict) else {"arms": {}}


def main(argv: Sequence[str] | None = None) -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--arm", choices=("both", *(arm.value for arm in Arm)), default="both")
    parser.add_argument("--compare", action="store_true", help="only compare the arms already saved")
    parser.add_argument("--dry", action="store_true", help="scripted calculator instead of the model (free)")
    parser.add_argument("--locale", choices=("en", "es"), default="en")
    parser.add_argument("-n", "--tasks", type=int, default=0, metavar="N", help="only the first N tasks")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="results file (read and merged)")
    args = parser.parse_args(argv)

    results = load_results(args.output)
    if args.compare:
        print("\n".join(compare(results["arms"])))
        return 0

    arms = list(Arm) if args.arm == "both" else [Arm(args.arm)]
    with isolated_container(offline=True if args.dry else None) as container:
        dry = args.dry or container.settings.offline
        if dry and not args.dry:
            print("the offline lock is on (MIRAG_OFFLINE=0 to use the model): running the script")
        bench = TaskBench(container, args.locale, dry=dry)
        tasks = bench.tasks(args.tasks or None)
        print(f"{len(tasks)} task(s) · arms {', '.join(arm.value for arm in arms)} · "
              f"{'SCRIPT (simulated decision)' if dry else 'REAL MODEL - this costs money (~$0.10 per task)'}")
        model = "deterministic double" if dry else container.settings.model
        for arm in arms:
            # only the latest run of each arm is kept: comparing against history mixes versions
            results["arms"][arm.value] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "dry": dry,
                                          "locale": args.locale, "model": model,
                                          "rows": bench.run_arm(arm, tasks)}
    path = write_json(args.output, results)
    print(f"\nwritten to {path}\n")
    print("\n".join(compare(results["arms"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
