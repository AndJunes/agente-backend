"""One line per execution in a JSONL file, to be able to compare versions.

It measures nothing new: it gathers what is already counted separately - the real cost of
the per-request budget and the evidence rows - and stores it on disk with the version, to
answer "did yesterday's change improve anything?".

What is not persisted did not happen: an old trace must be able to answer "why did Mirag
retrieve this?" and "what was delivered to the user?".
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mirag.evidence.properties import EvidenceRow, PropertyStatus
from mirag.llm.budget import BudgetSnapshot

TRACE_VERSION = "v2.0"


def evidence_counts(rows: Iterable[EvidenceRow]) -> tuple[dict[str, int], float, float]:
    """Counts per status, plus TWO fractions that must not be confused.

    'verified in simulation' used to be a surprise key that fell out of the numerator: a task
    with 10 properties proved against a simulation scored 0.0, exactly like a task where
    nothing was proved. So they are kept apart: ``verified_success`` counts ONLY what was
    really proved, and simulation is reported separately instead of vanishing.
    """
    counts = {status.value: 0 for status in PropertyStatus}
    for row in rows:
        counts[row.status.value] = counts.get(row.status.value, 0) + 1
    total = sum(counts.values())
    if not total:
        return counts, 0.0, 0.0
    return (counts, counts[PropertyStatus.VERIFIED.value] / total,
            counts[PropertyStatus.VERIFIED_IN_SIMULATION.value] / total)


@dataclass
class TraceRecord:
    """Everything a run wants persisted. Fields that do not apply stay ``None``, never invented."""

    task: str
    mode: str
    status: str
    simulated: bool
    evidence: list[EvidenceRow] = field(default_factory=list)
    boxes: list[str] = field(default_factory=list)
    context_tokens: int | None = None
    repaired: bool = False
    spent: BudgetSnapshot = field(default_factory=BudgetSnapshot)
    locale: str = "en"
    extra: dict[str, Any] = field(default_factory=dict)
    """plan, filters, retrieval, context, verification, anti_patterns, fallbacks, errors, model..."""


class TraceWriter:
    def __init__(self, path: Path, version: str = TRACE_VERSION) -> None:
        self.path = Path(path)
        self.version = version
        self._lock = threading.Lock()

    def write(self, record: TraceRecord, seconds: float, version: str | None = None) -> dict[str, Any]:
        counts, verified, in_simulation = evidence_counts(record.evidence)
        # What THIS run cost, not what the process has spent so far: summing a column of
        # running totals counts the first run six times.
        cost = record.spent.cost_usd
        row: dict[str, Any] = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "version": version or self.version,
            "locale": record.locale,
            "task": record.task[:120],
            "mode": record.mode,
            "status": record.status,
            "calls": record.spent.calls,
            # Without this, a night of doubles reads as 65 model calls for $0.00, which looks
            # like an accounting bug instead of what it is: simulation.
            "simulated_decision": record.simulated,
            "tokens": record.spent.tokens,
            "cost_usd": round(cost, 5),
            "seconds": round(seconds, 1),
            "context_tokens": record.context_tokens,
            "boxes": list(record.boxes),
            "repaired": record.repaired,
            "properties": counts,
            "properties_detail": [
                {"risk": row_.risk[:200], "property": row_.property[:200],
                 "test_id": row_.test_id, "status": row_.status.value}
                for row_ in record.evidence[:20]
            ],
            **{key: value for key, value in record.extra.items()},
            "verified_success": round(verified, 3),
            # apart on purpose: proved against a simulation is NOT proved
            "success_in_simulation": round(in_simulation, 3),
            # the plan metric: what was proved per dollar-second
            "value": round(verified / max(cost * seconds, 1e-9), 4),
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        return row

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @staticmethod
    def one_line(row: Mapping[str, Any]) -> str:
        """The readable closing line shown at the end of each task."""
        props = row["properties"]
        minutes, seconds = divmod(int(row["seconds"]), 60)
        parts = [f"{props.get('verified', 0)} verified"]
        if props.get("verified_in_simulation"):
            parts.append(f"{props['verified_in_simulation']} only in simulation")
        if props.get("refuted"):
            parts.append(f"{props['refuted']} refuted")
        if props.get("unverified"):
            parts.append(f"{props['unverified']} unverified")
        return (f"{' · '.join(parts)} · {row['calls']} calls · ${row['cost_usd']:.4f} · "
                f"{minutes}m {seconds:02d}s")
