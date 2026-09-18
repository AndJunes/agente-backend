"""The verdict of an execution, decided only by what was observed.

Exit 0 proves that the command did not crash. It does not prove that it tested anything.
Evidence is the markers each test prints: ``TEST:<id>:PASS`` or ``TEST:<id>:FAIL``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

from mirag.i18n.catalog import MessageCatalog

MARKER = re.compile(r"TEST:([^:\s]+):(PASS|FAIL)")
MAX_OUTPUT = 4000
TRUNCATION_NOTE = "characters truncated"


class ExecutionStatus(StrEnum):
    PASSED = "passed"
    """There were markers and every one passed."""
    FAILED = "failed"
    """It ran and failed (non-zero exit, a FAIL marker, or broken syntax)."""
    NO_EVIDENCE = "no_evidence"
    """It finished without error and printed NOT ONE marker. That is not passing."""
    NOT_EXECUTED = "not_executed"
    """It never ran."""


class Failure(StrEnum):
    EXIT = "exit"
    MARKERS = "markers"
    SYNTAX = "syntax"


HEADER_PREFIX = {
    ExecutionStatus.PASSED: "TESTS PASSED",
    ExecutionStatus.FAILED: "FAILED",
    ExecutionStatus.NO_EVIDENCE: "NO EVIDENCE",
    ExecutionStatus.NOT_EXECUTED: "NOT EXECUTED",
}
NO_EVIDENCE_HEADER = (
    "NO EVIDENCE: the command finished without errors but printed no TEST:<id>:PASS marker, "
    "so nobody knows what was tested. Do NOT claim the tests passed: print one marker per "
    "case and run again."
)


def body_markers(body: str) -> dict[str, str]:
    return dict(MARKER.findall(body or ""))


def truncate_keeping_markers(output: str, limit: int = MAX_OUTPUT) -> str:
    """Shorten the output without throwing the evidence away.

    Keeping only the tail lost the markers of a test that printed 9,600 characters of noise
    AFTER them: the run had passed and was reported as NO EVIDENCE. Now head and tail are
    kept, and any marker the cut would have removed is re-attached.
    """
    if len(output) <= limit:
        return output
    half = limit // 2
    cut = (output[:half] + f"\n\n[... {len(output) - limit:,} {TRUNCATION_NOTE} ...]\n\n" + output[-half:])
    lost = [f"TEST:{i}:{v}" for i, v in MARKER.findall(output) if f"TEST:{i}:{v}" not in cut]
    if lost:
        cut += "\n\n[markers recovered from the truncated span]\n" + "\n".join(dict.fromkeys(lost))
    return cut


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """What was OBSERVED when running. Not a label: the record."""

    status: ExecutionStatus
    header: str
    """Canonical first line (English, stable prefixes). The model reads it."""
    body: str = ""
    markers: dict[str, str] = field(default_factory=dict)
    exit_code: int | None = None
    failure: Failure | None = None
    detail: str = ""
    """The reason when it did not run, or the failure detail."""

    # ── construction ─────────────────────────────────────────────────────────

    @classmethod
    def not_executed(cls, reason: str) -> ExecutionResult:
        return cls(ExecutionStatus.NOT_EXECUTED, f"NOT EXECUTED: {reason}", detail=reason)

    @classmethod
    def syntax_error(cls, detail: str) -> ExecutionResult:
        return cls(ExecutionStatus.FAILED, f"FAILED syntax of {detail}", failure=Failure.SYNTAX, detail=detail)

    @classmethod
    def from_run(cls, full_output: str, exit_code: int, limit: int = MAX_OUTPUT) -> ExecutionResult:
        """The header is computed on the FULL output: on the truncated one, a test that
        prints a lot before its markers would be reported as NO EVIDENCE having passed."""
        found = MARKER.findall(full_output or "")
        passed = sum(1 for _, r in found if r == "PASS")
        body = truncate_keeping_markers(full_output, limit)
        markers = body_markers(body)
        if exit_code != 0:
            return cls(ExecutionStatus.FAILED, f"FAILED (exit {exit_code})", body, markers,
                       exit_code, Failure.EXIT)
        if found and passed < len(found):
            # a test can print FAIL and exit 0. That test is broken, and so is the run
            return cls(ExecutionStatus.FAILED, f"FAILED: {len(found) - passed} of {len(found)} markers failed",
                       body, markers, exit_code, Failure.MARKERS)
        if found:
            return cls(ExecutionStatus.PASSED, f"TESTS PASSED · {passed} of {len(found)} markers",
                       body, markers, exit_code)
        return cls(ExecutionStatus.NO_EVIDENCE, NO_EVIDENCE_HEADER, body, markers, exit_code)

    @classmethod
    def parse(cls, text: str | None) -> ExecutionResult:
        """Rebuild a result from its rendered :attr:`text` (tool results travel as text).

        Markers are read from the BODY, never from the header: the NO EVIDENCE header
        mentions the literal ``TEST:<id>:PASS`` to explain what is missing, and it used to be
        counted as evidence of itself.
        """
        text = text or ""
        header, _, body = text.partition("\n")
        body = body.lstrip("\n")
        markers = body_markers(body)
        if header.startswith("NOT EXECUTED"):
            return cls(ExecutionStatus.NOT_EXECUTED, header, body, markers,
                       detail=header.removeprefix("NOT EXECUTED:").strip())
        if header.startswith("FAILED syntax of"):
            return cls(ExecutionStatus.FAILED, header, body, markers, failure=Failure.SYNTAX,
                       detail=header.removeprefix("FAILED syntax of").strip())
        if header.startswith("FAILED"):
            exit_match = re.match(r"FAILED \(exit (-?\d+)\)", header)
            if exit_match:
                return cls(ExecutionStatus.FAILED, header, body, markers, int(exit_match.group(1)), Failure.EXIT)
            return cls(ExecutionStatus.FAILED, header, body, markers, 0, Failure.MARKERS)
        if header.startswith("NO EVIDENCE"):
            return cls(ExecutionStatus.NO_EVIDENCE, header, body, markers, 0)
        if header.startswith("TESTS PASSED"):
            return cls(ExecutionStatus.PASSED, header, body, markers, 0)
        return cls(ExecutionStatus.NO_EVIDENCE, header or "(no output)", body, markers)

    # ── reading ──────────────────────────────────────────────────────────────

    @property
    def passed(self) -> int:
        return sum(1 for v in self.markers.values() if v == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for v in self.markers.values() if v == "FAIL")

    @property
    def is_green(self) -> bool:
        return self.status is ExecutionStatus.PASSED

    @property
    def truncated(self) -> bool:
        return TRUNCATION_NOTE in self.body

    @property
    def text(self) -> str:
        """What the model reads: the header, a blank line, and the (truncated) output."""
        if self.status is ExecutionStatus.NOT_EXECUTED or self.failure is Failure.SYNTAX:
            return self.header + (f"\n\n{self.body}" if self.body else "")
        return f"{self.header}\n\n{self.body or '(no output)'}"

    @property
    def output_chars(self) -> int:
        return len(self.text)

    def describe(self, catalog: MessageCatalog) -> str:
        """The header in the reader's language."""
        total = len(self.markers)
        if self.status is ExecutionStatus.PASSED:
            return catalog.t("execution.header.passed", passed=self.passed, total=total)
        if self.status is ExecutionStatus.NOT_EXECUTED:
            return catalog.t("execution.header.not_executed", reason=self.detail)
        if self.status is ExecutionStatus.NO_EVIDENCE:
            return catalog.t("execution.header.no_evidence")
        if self.failure is Failure.SYNTAX:
            return catalog.t("execution.header.failed_syntax", detail=self.detail[:300])
        if self.failure is Failure.MARKERS:
            return catalog.t("execution.header.failed_markers", failed=self.failed, total=total)
        return catalog.t("execution.header.failed_exit", code=self.exit_code)

    def as_record(self) -> dict[str, object]:
        """The explicit executor object, persisted as is in traces."""
        return {
            "status": self.status.value, "header": self.header, "markers": dict(self.markers),
            "passed": self.passed, "failed": self.failed, "exit_code": self.exit_code,
            "output_chars": self.output_chars, "truncated": self.truncated,
        }
