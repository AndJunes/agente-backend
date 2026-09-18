"""How many times out of N does the model produce a project that passes its own tests?

    MIRAG_OFFLINE=0 python -m benchmarks.project_bench 10     # real model: COSTS MONEY
    python -m benchmarks.project_bench 3 --dry                 # scripted books project, free

Every run is independent and goes through ``QuestionPipeline.run`` - the path the server
takes - with its own gateway and budget. Each run is recorded whole: status, where it broke,
how many markers, how many repairs, cost and time. The count only says HOW MANY; what helps
fix something is WHY the others failed.

``--dry`` (or the offline lock on) answers with the scripted books project: it proves the
measuring machine works, not that the model can do it, and the report says so.

The report goes to ``benchmarks/results/project_bench.json``; every other file the runs
produce lives in a temporary data directory that is deleted at the end.
"""

from __future__ import annotations

import argparse
import statistics
import time
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from benchmarks.harness import RESULTS_DIR, isolated_container, utf8_console, warm_up, write_json
from mirag.container import Container
from mirag.llm.gateway import LLMGateway
from mirag.offline.demos import CANONICAL
from mirag.pipeline.models import PipelineRun, StepStatus
from mirag.projects.certification import PhaseStatus

DEFAULT_OUTPUT = RESULTS_DIR / "project_bench.json"
DEMO = "project"
VERIFIED = "VERIFIED"


def contract_problems(observed: dict[str, Any], requires: dict[str, Any]) -> list[str]:
    """The canonical project demo's contract, checked on what this run really produced."""
    problems = []
    for name, expected in requires.items():
        real = observed.get(name)
        if isinstance(expected, tuple):
            ok = real in expected
        elif isinstance(expected, bool):
            ok = bool(real) is expected
        else:
            ok = isinstance(real, int) and real >= expected
        if not ok:
            problems.append(f"{name}: required {expected!r}, observed {real!r}")
    return problems


class ProjectBench:
    """Runs the project request N times through the production pipeline and records each run."""

    def __init__(self, container: Container, locale: str = "en", dry: bool = True) -> None:
        self._container = container
        self.locale = locale
        self.dry = dry
        self._demos = container.demos(locale)
        warm_up(container, locale)
        self.question = self._demos.canonical_question(DEMO)

    def _gateway(self) -> LLMGateway:
        """A fresh one per run: the spending cap is PER RUN, as in the server."""
        gateways = self._container.gateways
        return gateways.create(script=self._demos.script(DEMO)) if self.dry else gateways.create()

    def run_once(self, index: int) -> dict[str, Any]:
        # The legacy bench shared one process-wide budget: a bench of ten ran out of money at
        # the seventh and the last three were recorded as EXCEPTION - four runs that never
        # happened contaminated the measurement. Here each run owns its gateway and budget.
        gateway = self._gateway()
        started = time.time()
        row: dict[str, Any] = {"n": index, "status": None, "error": None}
        try:
            run = self._container.pipeline.run(self.question, gateway, self.locale, persist=False,
                                               version="bench:project")
            row.update(self.describe(run))
        except Exception as exc:  # a run that blows up IS a result
            row["status"] = "EXCEPTION"
            row["error"] = f"{type(exc).__name__}: {exc}"[:200]
        spent = gateway.budget.snapshot()
        row.update({"seconds": round(time.time() - started, 1), "cost_usd": round(spent.cost_usd, 4),
                    "calls": spent.calls, "tokens": spent.tokens})
        return row

    @staticmethod
    def describe(run: PipelineRun) -> dict[str, Any]:
        certificate, project, artifact = run.certificate, run.project, run.artifact
        phases = certificate.phases if certificate else ()
        markers = dict(certificate.markers) if certificate else {}
        package = artifact.package if artifact else None
        observed = {
            "has_project": project is not None,
            "files": project.totals["files"] if project else 0,
            "project_status": certificate.status.value if certificate else None,
            "integrity_ok": bool(package and package.ok),
            "crud_verified": sum(1 for k, v in markers.items() if k.startswith("crud_") and v == "PASS"),
            "has_download": bool(artifact and artifact.download_url),
        }
        problems = contract_problems(observed, CANONICAL[DEMO].requires)
        return {
            "status": certificate.status.value if certificate else "NO_CERTIFICATE",
            "reason": (certificate.reason if certificate else run.answer)[:160],
            # the first phase that did not go well: that is what has to be fixed
            "first_failed_phase": next((p.name for p in phases if p.status is PhaseStatus.FAILED), None),
            "first_limited_phase": next((p.name for p in phases if p.status is PhaseStatus.LIMITED), None),
            "first_error_step": next((s.name for s in run.steps if s.status is StepStatus.ERROR), None),
            "files": observed["files"],
            "lines": project.totals["lines"] if project else 0,
            "markers_passed": sum(1 for v in markers.values() if v == "PASS"),
            "markers_total": len(markers),
            "crud_passed": observed["crud_verified"],
            "repairs": len(certificate.repairs) if certificate else 0,
            "integrity": observed["integrity_ok"],
            "zip_bytes": package.size if package else 0,
            "downloadable": bool(artifact and artifact.downloadable),
            "fulfils_contract": not problems,
            "contract_problems": problems,
            "phases": [[p.name, p.status.value] for p in phases],
        }

    def run(self, times: int, on_row: Callable[[dict[str, Any]], None] | None = None) -> list[dict[str, Any]]:
        rows = []
        for index in range(1, times + 1):
            row = self.run_once(index)
            rows.append(row)
            if on_row:
                on_row(row)
        return rows


def summarize(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    costs = [row["cost_usd"] for row in rows]
    seconds = [row["seconds"] for row in rows]
    return {
        "runs": len(rows),
        "verified": sum(1 for row in rows if row["status"] == VERIFIED),
        "statuses": dict(Counter(row["status"] for row in rows)),
        "first_failed_phase": dict(Counter(row["first_failed_phase"] for row in rows if row.get("first_failed_phase"))),
        "zip_integrity": sum(1 for row in rows if row.get("integrity")),
        "cost_usd_total": round(sum(costs), 4),
        "cost_usd_mean": round(statistics.mean(costs), 4) if costs else 0.0,
        "seconds_total": round(sum(seconds), 1),
        "seconds_median": round(statistics.median(seconds), 1) if seconds else 0.0,
    }


def line(row: dict[str, Any], times: int) -> str:
    text = (f"  {row['n']:>2}/{times}  {row['status']:<14} "
            f"{row.get('markers_passed', 0):>2}/{row.get('markers_total', 0):<2} markers · "
            f"{row.get('files', 0):>2} files · repairs={row.get('repairs', 0)} · "
            f"${row['cost_usd']:.4f} · {row['seconds']:>5.1f}s")
    if row["status"] != VERIFIED:
        text += f"  [{row.get('first_failed_phase') or row.get('first_error_step') or row.get('error') or ''}]"
    return text


def main(argv: Sequence[str] | None = None) -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="?", type=int, default=10, help="independent runs (default 10)")
    parser.add_argument("--dry", action="store_true", help="scripted books project instead of the model (free)")
    parser.add_argument("--locale", choices=("en", "es"), default="en")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="where the report goes")
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("at least one run")

    # --dry forces the lock on: a dry bench can never spend, whatever the environment says.
    with isolated_container(offline=True if args.dry else None) as container:
        dry = args.dry or container.settings.offline
        if dry and not args.dry:
            print("the offline lock is on (MIRAG_OFFLINE=0 to use the model): running the script")
        print(f"{args.runs} runs · {'SCRIPT (simulated decision)' if dry else 'REAL MODEL - this costs money'} · "
              f"locale {args.locale}\n")
        bench = ProjectBench(container, args.locale, dry=dry)
        rows = bench.run(args.runs, on_row=lambda row: print(line(row, args.runs), flush=True))
        model = container.settings.model

    summary = summarize(rows)
    print(f"\n{'─' * 70}")
    print(f"  VERIFIED: {summary['verified']}/{summary['runs']}")
    print(f"  statuses: {summary['statuses']}")
    if summary["first_failed_phase"]:
        print(f"  first phase that breaks: {summary['first_failed_phase']}")
    print(f"  cost: ${summary['cost_usd_total']:.4f} total · ${summary['cost_usd_mean']:.4f} mean")
    print(f"  time: {summary['seconds_total']:.0f}s total · {summary['seconds_median']:.0f}s median")
    print(f"  ZIP integrity: {summary['zip_integrity']}/{summary['runs']}")
    path = write_json(args.output, {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "locale": args.locale,
                                    "dry": dry, "model": "deterministic double" if dry else model,
                                    "question": bench.question, "summary": summary, "runs": rows})
    print(f"\n  written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
