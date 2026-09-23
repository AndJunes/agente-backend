"""The canonical demos, run end to end and checked against their contract.

The report says what was required, what was observed and whether they match - without
interpreting anything: the data comes from the real run. It measures what the USER SEES
(the rendered markdown), not an internal field: a contract that looked at the internal
answer would pass a product that shows nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mirag.offline.demos import CANONICAL
from mirag.pipeline.models import PipelineRun
from mirag.presentation.answers import AnswerFormatter

if TYPE_CHECKING:
    from mirag.container import Container


@dataclass
class DemoReport:
    key: str
    question: str
    simulated: bool
    markdown: str
    observed: dict[str, Any]
    problems: list[str] = field(default_factory=list)
    run: PipelineRun | None = None

    @property
    def fulfils(self) -> bool:
        return not self.problems


class DemoContractRunner:
    def __init__(self, container: Container) -> None:
        self._container = container

    @staticmethod
    def keys() -> list[str]:
        return list(CANONICAL)

    def run(self, key: str, locale: str, offline: bool | None = None, persist: bool = False) -> DemoReport:
        if key not in CANONICAL:
            raise KeyError(f"unknown demo: {key!r}. Available: {', '.join(CANONICAL)}")
        demo = CANONICAL[key]
        container = self._container
        catalog = container.i18n.catalog(locale)
        demos = container.demos(locale)
        question = demos.canonical_question(key)
        simulate = container.settings.offline if offline is None else offline

        gateway = (container.gateways.create(script=demos.script(demo.script)) if simulate
                   else container.gateways.create())
        run = container.pipeline.run(question, gateway, locale, persist=persist)
        markdown = AnswerFormatter(catalog).pipeline_answer(run, demo.script if simulate else None)
        certificate = run.certificate
        artifact = run.artifact
        execution = run.execution
        observed = {
            # Not the same question as `has_project`, and that is the point: this one says
            # the pipeline took the project branch at all. A demo that loads the multi-file
            # script while the branch is single-file fails HERE, naming the contradiction,
            # instead of surfacing three stages later as an empty delivery.
            "took_project_branch": bool(run.plan and run.plan.needs_project),
            "has_project": run.project is not None,
            "files": run.project.totals["files"] if run.project else 0,
            "project_status": certificate.status.value if certificate else None,
            "integrity_ok": bool(artifact and artifact.package and artifact.package.ok),
            "crud_verified": sum(1 for k, v in (certificate.markers if certificate else {}).items()
                                 if k.startswith("crud_") and v == "PASS"),
            "has_download": bool(artifact and artifact.download_url),
            "has_answer": len(markdown.strip()) > 40,
            "has_retrieval": run.ran("retrieval"),
            "has_code": bool(run.delivery),
            "executed": execution is not None,
            "execution_status": execution.status.value if execution else None,
            "sufficiency": run.verdict.grade.value if run.verdict else None,
            "verified_properties": sum(1 for row in run.evidence if row.status.value == "verified"),
            "warns_coverage": bool(run.verdict and not run.verdict.sufficient and run.verdict.warning
                                   and run.answer.startswith(run.verdict.warning[:24])),
        }
        problems = []
        for field_name, expected in demo.requires.items():
            real = observed.get(field_name)
            if isinstance(expected, tuple):
                ok = real in expected
            elif isinstance(expected, bool):
                ok = bool(real) is expected
            else:
                ok = isinstance(real, int) and real >= expected
            if not ok:
                problems.append(f"{field_name}: required {expected!r}, observed {real!r}")
        return DemoReport(key, question, simulate, markdown, observed, problems, run)
