"""The final markdown: the answer, the evidence, and what was NOT proved."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mirag.evidence.obligations import CoverageRow, ObligationStatus
from mirag.evidence.properties import EvidenceRow, PropertyStatus
from mirag.execution.verdict import ExecutionStatus
from mirag.i18n.catalog import MessageCatalog
from mirag.pipeline.models import PipelineRun
from mirag.projects.certification import Certificate, PhaseStatus, ProjectStatus
from mirag.projects.model import Project
from mirag.projects.packaging import Package

_PROPERTY_ICONS = {
    PropertyStatus.VERIFIED: "✅", PropertyStatus.REFUTED: "❌",
    PropertyStatus.VERIFIED_IN_SIMULATION: "🟡", PropertyStatus.UNVERIFIED: "❔",
}
_STATUS_ICONS = {ProjectStatus.VERIFIED: "✅", ProjectStatus.PARTIAL: "❔", ProjectStatus.VALIDATED: "○",
                 ProjectStatus.INCOMPLETE: "⚠️",
                 ProjectStatus.FAILED: "❌"}
_PHASE_ICONS = {PhaseStatus.OK: "✅", PhaseStatus.FAILED: "❌", PhaseStatus.LIMITED: "❔", PhaseStatus.SKIPPED: "—"}
_OBLIGATION_ICONS = {ObligationStatus.COVERED: "✅", ObligationStatus.DECLARED: "❔",
                     ObligationStatus.NOT_COVERED: "○", ObligationStatus.NOT_VERIFIABLE: "—"}


class AnswerFormatter:
    def __init__(self, catalog: MessageCatalog) -> None:
        self._t = catalog

    # ── pieces ───────────────────────────────────────────────────────────────

    def evidence_table(self, rows: Sequence[EvidenceRow]) -> list[str]:
        t = self._t
        lines = ["", f"## {t('answer.evidence.title')}", t("answer.evidence.intro"), "",
                 f"| {t('answer.evidence.col_status')} | {t('answer.evidence.col_risk')} | "
                 f"{t('answer.evidence.col_property')} | {t('answer.evidence.col_test')} |",
                 "|---|---|---|---|"]
        lines += [f"| {_PROPERTY_ICONS[r.status]} {t(f'evidence.status.{r.status.value}')} | {r.risk} | "
                  f"`{r.property}` | `{r.test_id}` |" for r in rows]
        return lines

    def obligations_table(self, rows: Sequence[CoverageRow]) -> str:
        if not rows:
            return ""
        t = self._t
        lines = [f"## {t('answer.obligations.title')}", "", t("answer.obligations.intro"), "",
                 f"| {t('answer.obligations.col_status')} | {t('answer.obligations.col_anti_pattern')} | "
                 f"{t('answer.obligations.col_avoid')} |", "|---|---|---|"]
        lines += [f"| {_OBLIGATION_ICONS[r.status]} {t(f'obligation.label.{r.status.value}')} | "
                  f"`{r.obligation}` | {r.avoid} |" for r in rows]
        unproved = [r for r in rows if r.status in (ObligationStatus.NOT_COVERED, ObligationStatus.DECLARED)]
        if unproved:
            lines += ["", t("answer.obligations.unproved", count=len(unproved), total=len(rows))]
        return "\n".join(lines)

    def execution_summary(self, run: PipelineRun) -> str:
        """One line with what really happened when running. Without repeating the code."""
        t = self._t
        result = run.execution
        if result is None:
            return t("answer.execution.not_run")
        attempts = t("answer.execution.repaired") if run.repaired else ""
        header = result.describe(t)
        if result.status is ExecutionStatus.PASSED:
            return t("answer.execution.passed", attempts=attempts, header=header, count=len(result.markers))
        if result.status is ExecutionStatus.FAILED:
            return t("answer.execution.failed", attempts=attempts, header=header)
        if result.status is ExecutionStatus.NO_EVIDENCE:
            return t("answer.execution.no_evidence", attempts=attempts)
        return f"> {attempts}**{header}**"

    def phase_label(self, name: str) -> str:
        """``repair:2`` -> ``Repair 2``, in the reader's language."""
        base, _, suffix = name.partition(":")
        label = self._t(f"phase.{base}")
        return f"{label} {suffix}" if suffix else label

    # ── whole answers ────────────────────────────────────────────────────────

    def pipeline_answer(self, run: PipelineRun, demo: str | None = None) -> str:
        """The coverage warning is already prepended by the pipeline: not repeated here."""
        t = self._t
        parts = [run.answer or ""]
        # In a code task the answer comes empty and the page used to jump straight to the
        # evidence table: the user saw WHAT was verified and never WHY it was built that way.
        # The decisions are what the model reasoned, so they are labelled as its own.
        decisions = (run.delivery or {}).get("decisions")
        if not (run.answer or "").strip() and decisions:
            parts = [f"## {t('answer.what_was_done')}\n\n{str(decisions).strip()}", "", self.execution_summary(run)]
        if run.evidence:
            parts += self.evidence_table(run.evidence)
        if run.anti_pattern_coverage:
            parts += ["", self.obligations_table(run.anti_pattern_coverage)]
        if run.simulated:
            # Two very different situations, and confusing them is the lie that closed a whole
            # phase: a prepared demo DOES answer what was asked; "no model" answers nothing.
            parts += ["", t("answer.simulated_demo", demo=demo) if demo else t("answer.no_model")]
        return "\n".join(parts)

    def project_answer(self, project: Project, certificate: Certificate, package: Package,
                       spec: Mapping[str, Any] | None) -> str:
        """The status comes from the certificate, never from the model's text."""
        t = self._t
        spec = spec or {}
        totals = project.totals
        parts = [f"## {project.name}", ""]
        if spec.get("architecture"):
            stack = " · ".join(str(spec.get(k, "")) for k in ("language", "framework", "database", "architecture"))
            parts += [stack.strip(" ·"), ""]
        parts += [t("answer.project.totals", files=totals["files"], directories=totals["directories"],
                    lines=totals["lines"]), ""]
        if spec.get("assumptions"):
            parts += [t("answer.project.assumptions"), ""]
            parts += [f"- {a}" for a in spec["assumptions"]] + [""]
        icon = _STATUS_ICONS.get(certificate.status, "○")
        parts += [f"### {icon} {t(f'project.status.{certificate.status.value}')}", "", certificate.reason, ""]
        if certificate.markers:
            parts += [t("answer.project.markers", passed=certificate.passed, total=len(certificate.markers)), ""]
        parts += [f"| {t('answer.project.col_phase')} | {t('answer.project.col_status')} | "
                  f"{t('answer.project.col_detail')} |", "|---|---|---|"]
        parts += [f"| {self.phase_label(p.name)} | {_PHASE_ICONS.get(p.status, p.status.value)} | {p.detail} |"
                  for p in certificate.phases]
        if not package.ok:
            parts += ["", t("answer.project.integrity_error", reason=package.inspection.reason)]
        return "\n".join(parts)
