"""Crosses what the model SAID it would prove with what the execution demonstrates.

The status is never decided by the model: it is read from the real output. If the test id
does not appear, the property stays UNVERIFIED however much the model swears it covered it.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from mirag.core.text import lenient_json_list
from mirag.execution.verdict import ExecutionResult


class PropertyStatus(StrEnum):
    VERIFIED = "verified"
    VERIFIED_IN_SIMULATION = "verified_in_simulation"
    """Proved against a simulation (a Map instead of PostgreSQL). Not the same thing."""
    REFUTED = "refuted"
    UNVERIFIED = "unverified"


@dataclass(frozen=True, slots=True)
class EvidenceRow:
    risk: str
    property: str
    test_id: str
    status: PropertyStatus
    executed: bool = False
    substituted: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["substituted"] = list(self.substituted)
        return data

    def public(self) -> dict[str, Any]:
        """The four fields the page shows."""
        return {"risk": self.risk, "property": self.property, "test_id": self.test_id,
                "status": self.status.value}


class EvidenceBuilder:
    def build(
        self,
        properties: object,
        result: ExecutionResult | None,
        executed: bool,
        substituted: Sequence[str] = (),
    ) -> list[EvidenceRow]:
        markers = result.markers if result is not None else {}
        declared = lenient_json_list(properties)
        if not declared and executed:
            # Declaring ZERO properties was the quietest path: the evidence table vanished and
            # a "tests passed" stood without a single warning. Declaring five and proving
            # none shouted; declaring none did not. Now it leaves a trace.
            return [EvidenceRow("the model declared no property to prove", "(declared none)",
                                "(none)", PropertyStatus.UNVERIFIED, False, tuple(substituted))]
        rows = []
        for item in declared:
            if not isinstance(item, Mapping):
                item = {"risk": str(item)}
            test_id = str(item.get("test_id", "")).strip()
            marker = markers.get(test_id)
            status = {"PASS": PropertyStatus.VERIFIED, "FAIL": PropertyStatus.REFUTED}.get(
                marker or "", PropertyStatus.UNVERIFIED)
            # a green test against a Map proves NOTHING about PostgreSQL
            if status is PropertyStatus.VERIFIED and substituted:
                status = PropertyStatus.VERIFIED_IN_SIMULATION
            rows.append(EvidenceRow(
                risk=str(item.get("risk", "?")),
                property=str(item.get("property", "(not declared)")),
                test_id=test_id or "(no id)",
                status=status,
                executed=bool(executed and marker),
                substituted=tuple(substituted),
            ))
        return rows

    @staticmethod
    def count(rows: Iterable[EvidenceRow]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.status.value] = counts.get(row.status.value, 0) + 1
        return counts


# technology -> (how the request names it, how code that really uses it looks)
SUBSTITUTABLE: dict[str, tuple[str, str]] = {
    "PostgreSQL": (r"postgres|postgresql", r"require\(['\"]pg|from ['\"]pg|import pg\b|psycopg"),
    "MySQL": (r"\bmysql\b", r"mysql2?|require\(['\"]mysql"),
    "Redis": (r"\bredis\b", r"require\(['\"]redis|from redis|ioredis"),
    "MongoDB": (r"\bmongo", r"mongodb|mongoose"),
    "Kafka": (r"\bkafka\b", r"kafkajs|from kafka"),
    "S3": (r"\bs3\b", r"aws-sdk|boto3|@aws-sdk"),
}
# Express or FastAPI do not decide whether the code is correct: the invariant lives in the
# database or the queue. Replacing the HTTP framework does not degrade the evidence.


class SimulationDetector:
    """Technologies the request asks for and the EXECUTED code does not really use.

    Models tend to replace Postgres with a Map when they cannot run it, and then present
    the green tests as if they proved Postgres. The executor detects it by reading the code,
    not by asking the model.
    """

    def detect(self, request: str, files: Mapping[str, str] | None) -> list[str]:
        code = "\n".join((files or {}).values())
        return [
            name for name, (in_request, in_code) in SUBSTITUTABLE.items()
            if re.search(in_request, request or "", re.I) and not re.search(in_code, code, re.I)
        ]
