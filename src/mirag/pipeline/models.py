"""The records a pipeline run produces."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from mirag.evidence.obligations import CoverageRow
from mirag.evidence.properties import EvidenceRow
from mirag.execution.verdict import ExecutionResult

if TYPE_CHECKING:
    from mirag.projects.artifacts import Artifact
    from mirag.projects.certification import Certificate
    from mirag.projects.model import Project
    from mirag.retrieval.plan import RetrievalPlan
    from mirag.retrieval.sufficiency import SufficiencyVerdict


class StepStatus(StrEnum):
    EXECUTED = "executed"
    SKIPPED = "skipped"
    FALLBACK = "fallback"
    ERROR = "error"
    WARNING = "warning"


class Source(StrEnum):
    EXECUTION = "execution"
    MODEL = "model"
    CORPUS = "corpus"


_MARKS = {StepStatus.EXECUTED: "·", StepStatus.SKIPPED: "○", StepStatus.FALLBACK: "△",
          StepStatus.ERROR: "✗", StepStatus.WARNING: "!"}


@dataclass(frozen=True, slots=True)
class Step:
    name: str
    """A stable identifier (``retrieval_plan``, ``bm25:knowledge``...). The UI translates it."""
    status: StepStatus
    summary: str
    """Already localised for the reader."""
    ms: float = 0.0
    source: Source | None = None
    detail: Any = None

    def line(self) -> str:
        return f"  {_MARKS.get(self.status, '?')} {self.name:<24} {self.summary}"


StepListener = Callable[[Step], None]


@dataclass
class PipelineRun:
    """Everything that happened, not just the result."""

    question: str
    locale: str
    steps: list[Step] = field(default_factory=list)
    answer: str = ""
    plan: RetrievalPlan | None = None
    verdict: SufficiencyVerdict | None = None
    delivery: dict[str, Any] | None = None
    evidence: list[EvidenceRow] = field(default_factory=list)
    anti_pattern_coverage: list[CoverageRow] = field(default_factory=list)
    execution: ExecutionResult | None = None
    repaired: bool = False
    simulated: bool = True
    """Did the decision come from a double?"""
    project: Project | None = None
    certificate: Certificate | None = None
    artifact: Artifact | None = None
    trace: dict[str, Any] | None = None
    output_folder: str | None = None

    @property
    def ms(self) -> float:
        return round(sum(step.ms for step in self.steps), 1)

    def step(self, name: str) -> Step | None:
        return next((s for s in self.steps if s.name == name), None)

    def ran(self, name: str) -> bool:
        step = self.step(name)
        return step is not None and step.status is StepStatus.EXECUTED

    def render(self) -> str:
        lines = [f"\n{self.question}\n", *(s.line() for s in self.steps),
                 f"\n  {self.ms} ms · {'SIMULATED decision' if self.simulated else 'real model'}"]
        return "\n".join(lines)
