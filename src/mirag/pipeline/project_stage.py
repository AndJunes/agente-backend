"""The project branch: plan -> groups -> verification -> ZIP -> registry.

A BRANCH, not a parallel pipeline: plan, retrieval, context and sufficiency are exactly the
same. It reuses everything above and below; what is new is what happens in the middle. It
does NOT use the single-file output folder, which flattens paths and is emptied on every
request: a project goes to its own artifact, with its own id.
"""

from __future__ import annotations

from mirag.core.errors import OfflineModeError
from mirag.core.timing import Stopwatch
from mirag.llm.gateway import LLMGateway
from mirag.pipeline.knowledge_stage import PreparedRequest
from mirag.pipeline.models import PipelineRun, Source, Step, StepListener, StepStatus
from mirag.presentation.answers import AnswerFormatter
from mirag.projects.artifacts import ArtifactRegistry
from mirag.projects.certification import PhaseStatus, ProjectCertifier
from mirag.projects.generator import GenerationStep, ProjectGenerator
from mirag.projects.packaging import Packager
from mirag.retrieval.engine import RetrievalEngine

_PHASE_TO_STEP = {PhaseStatus.OK: StepStatus.EXECUTED, PhaseStatus.FAILED: StepStatus.ERROR,
                  PhaseStatus.LIMITED: StepStatus.FALLBACK, PhaseStatus.SKIPPED: StepStatus.SKIPPED}


class ProjectDeliveryStage:
    def __init__(self, generator: ProjectGenerator, certifier: ProjectCertifier, packager: Packager,
                 artifacts: ArtifactRegistry) -> None:
        self._generator = generator
        self._certifier = certifier
        self._packager = packager
        self._artifacts = artifacts

    def run(self, run: PipelineRun, prepared: PreparedRequest, engine: RetrievalEngine, gateway: LLMGateway,
            note: StepListener, persist: bool = True, version: str = "mirag") -> None:
        t = engine.catalog
        directive = t("llm.language_directive")

        def generation_step(step: GenerationStep) -> None:
            note(Step(step.name, StepStatus(step.status), step.summary, 0.0, Source.MODEL, step.detail))

        clock = Stopwatch()
        try:
            generated = self._generator.generate(run.question, prepared.context, gateway, t, directive,
                                                 on_step=generation_step)
        except OfflineModeError as exc:
            note(Step("generation", StepStatus.ERROR, t("pipeline.model.offline"), clock.ms, Source.EXECUTION))
            run.answer = t("pipeline.model.no_model_answer", error=str(exc))
            return
        project = generated.project
        if project is None:
            note(Step("project", StepStatus.ERROR, t("pipeline.project.failed"), clock.ms, Source.EXECUTION))
            run.answer = t("pipeline.project.failed_answer")
            return
        totals = project.totals
        note(Step("project", StepStatus.EXECUTED,
                  t("pipeline.project.summary", files=totals["files"], directories=totals["directories"],
                    lines=totals["lines"]),
                  clock.ms, Source.MODEL, {"tree": list(project.paths()), "totals": totals}))

        project.seal()  # from here on it does not change: what is verified is what is packaged
        # The repairer IS wired. It sat written and unconnected until a real run showed a
        # `from books_api import create_server` against an __init__.py that did not re-export
        # it, leaving the project FAILED without even trying to fix it.
        certificate = self._certifier.certify(
            project, t, test_command=(generated.spec or {}).get("test_command"),
            on_phase=lambda phase: note(Step(phase.name, _PHASE_TO_STEP.get(phase.status, StepStatus.SKIPPED),
                                             phase.detail, phase.ms, Source.EXECUTION)),
            repairer=self._generator.repairer(prepared.context, gateway, directive),
        )
        # Package the project that was REALLY verified (a repair replaces the sealed one).
        verified = (certificate.project or project).seal()

        clock.restart()
        package = self._packager.seal(verified, certificate, version=version)
        note(Step("packaging", StepStatus.EXECUTED if package.ok else StepStatus.ERROR,
                  (t("pipeline.packaging.ok", name=package.name, bytes=f"{package.size:,}",
                     checks=len(package.inspection.checks)) if package.ok
                   else t("pipeline.packaging.integrity_error", reason=package.inspection.reason[:90])),
                  clock.ms, Source.EXECUTION, {"checks": [list(c) for c in package.inspection.checks]}))

        # The artifact is ALWAYS registered: without it there is nothing to download, and the
        # ZIP bytes already exist in memory. `persist` only decides whether it is also on disk.
        clock.restart()
        try:
            artifact = self._artifacts.save(verified, certificate, package, on_disk=persist,
                                            simulated=gateway.simulated)
            run.artifact = artifact
            note(Step("artifact", StepStatus.EXECUTED,
                      t("pipeline.artifact.ready", id=artifact.id)
                      + " · " + (t("pipeline.artifact.on_disk") if persist else t("pipeline.artifact.memory_only")),
                      clock.ms, Source.EXECUTION))
        except Exception as exc:
            note(Step("artifact", StepStatus.ERROR, t("pipeline.artifact.failed", error=f"{type(exc).__name__}: {exc}"),
                      clock.ms, Source.EXECUTION))

        run.project = verified
        run.certificate = certificate
        run.evidence = list(certificate.evidence)
        run.repaired = bool(certificate.repairs)
        run.answer = AnswerFormatter(t).project_answer(verified, certificate, package, generated.spec)
        run.delivery = None
