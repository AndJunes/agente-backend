"""From execution to evidence: claims, properties and obligations."""

from __future__ import annotations

import pytest

from mirag.evidence.claims import ClaimAuditor, ClaimStatus
from mirag.evidence.obligations import ObligationChecker, ObligationStatus
from mirag.evidence.properties import (
    EvidenceBuilder,
    EvidenceRow,
    PropertyStatus,
    SimulationDetector,
)
from mirag.execution.verdict import ExecutionResult
from mirag.i18n.registry import I18n

GREEN = ExecutionResult.from_run("TEST:a:PASS\nTEST:b:PASS", 0)
EMPTY = ExecutionResult.from_run("", 0)
RED = ExecutionResult.from_run("TEST:a:PASS\nTEST:b:FAIL", 0)


# ── properties ───────────────────────────────────────────────────────────────

def test_status_comes_from_the_markers_not_from_the_model() -> None:
    rows = EvidenceBuilder().build(
        [{"risk": "r1", "property": "p1", "test_id": "a"},
         {"risk": "r2", "property": "p2", "test_id": "b"},
         {"risk": "r3", "property": "p3", "test_id": "never_printed"}], RED, executed=True)
    assert [r.status for r in rows] == [PropertyStatus.VERIFIED, PropertyStatus.REFUTED, PropertyStatus.UNVERIFIED]


def test_declaring_nothing_leaves_a_trace_instead_of_silence() -> None:
    rows = EvidenceBuilder().build([], GREEN, executed=True)
    assert len(rows) == 1
    assert rows[0].status is PropertyStatus.UNVERIFIED


def test_green_against_a_simulation_is_not_verified() -> None:
    rows = EvidenceBuilder().build([{"test_id": "a"}], GREEN, executed=True, substituted=["PostgreSQL"])
    assert rows[0].status is PropertyStatus.VERIFIED_IN_SIMULATION


def test_properties_can_arrive_as_a_json_string_or_plain_text() -> None:
    rows = EvidenceBuilder().build('[{"risk": "r", "test_id": "a"}]', GREEN, executed=True)
    assert rows[0].status is PropertyStatus.VERIFIED
    assert EvidenceBuilder().build("just a risk", GREEN, executed=True)[0].risk == "just a risk"


def test_simulation_detector_reads_the_executed_code() -> None:
    detector = SimulationDetector()
    assert detector.detect("store it in postgres", {"a.py": "store = {}"}) == ["PostgreSQL"]
    assert detector.detect("store it in postgres", {"a.py": "import psycopg"}) == []
    assert detector.detect("an in-memory cache", {"a.py": "store = {}"}) == []


# ── claims ───────────────────────────────────────────────────────────────────

@pytest.fixture(params=["en", "es"])
def auditor(request: pytest.FixtureRequest, i18n: I18n) -> ClaimAuditor:
    return ClaimAuditor(i18n.lexicon(request.param), i18n.catalog(request.param))


CLAIMS = {
    "en": {"passed": "Perfect. All the tests passed.", "neutral": "Here is the code.",
           "warns": "INSUFFICIENT EVIDENCE: no evidence the tests passed."},
    "es": {"passed": "Perfecto. Los 3 test cases pasaron realmente.", "neutral": "Aquí tenés el código.",
           "warns": "EVIDENCIA INSUFICIENTE: sin evidencia de que pasaran."},
}


def _claims(auditor: ClaimAuditor) -> dict[str, str]:
    return CLAIMS[auditor._t.locale]


def test_a_claim_without_markers_is_unsupported(auditor: ClaimAuditor) -> None:
    warning, status = auditor.audit(_claims(auditor)["passed"], [EMPTY])
    assert status is ClaimStatus.UNSUPPORTED
    assert warning and warning.startswith("> ⚠️")


def test_a_claim_backed_by_markers_has_no_warning(auditor: ClaimAuditor) -> None:
    assert auditor.audit(_claims(auditor)["passed"], [GREEN]) == (None, ClaimStatus.SUPPORTED)


def test_claiming_over_a_fail_is_refuted(auditor: ClaimAuditor) -> None:
    warning, status = auditor.audit(_claims(auditor)["passed"], [RED])
    assert status is ClaimStatus.REFUTED
    assert "`b`" in (warning or "")


def test_claiming_when_nothing_ran(auditor: ClaimAuditor) -> None:
    _, status = auditor.audit(_claims(auditor)["passed"], [ExecutionResult.not_executed("bash")])
    assert status is ClaimStatus.NOT_EXECUTED
    _, status = auditor.audit(_claims(auditor)["passed"], [])
    assert status is ClaimStatus.UNSUPPORTED


def test_no_claim_no_warning(auditor: ClaimAuditor) -> None:
    assert auditor.audit(_claims(auditor)["neutral"], [EMPTY]) == (None, ClaimStatus.NO_CLAIM)


def test_a_model_that_already_warns_is_not_warned_again(auditor: ClaimAuditor) -> None:
    assert auditor.audit(_claims(auditor)["warns"], [EMPTY])[1] is ClaimStatus.NO_CLAIM


def test_declared_properties_that_never_appeared(auditor: ClaimAuditor) -> None:
    _, status = auditor.audit(_claims(auditor)["neutral"], [GREEN], [{"test_id": "zzz"}])
    assert status is ClaimStatus.UNSUPPORTED


def test_apply_keeps_the_original_text_whole(auditor: ClaimAuditor) -> None:
    text = _claims(auditor)["passed"]
    audited, _ = auditor.apply(text, [EMPTY])
    assert audited.endswith(text)
    assert auditor.apply(None, [])[0] == ""


def test_the_auditor_does_not_blow_up_on_garbage(auditor: ClaimAuditor) -> None:
    assert auditor.audit("", [ExecutionResult.parse("\x00garbage")], ["not a dict", 3])[1] is ClaimStatus.NO_CLAIM


# ── obligations ──────────────────────────────────────────────────────────────

def _row(risk: str, prop: str, status: PropertyStatus, test_id: str = "t") -> EvidenceRow:
    return EvidenceRow(risk, prop, test_id, status)


def test_obligations_come_from_the_retrieved_anti_patterns(engine) -> None:
    question = {"en": "Bookings API: two users must not keep the same seat",
                "es": "API de reservas: dos usuarios no pueden quedarse con la misma plaza"}[engine.locale]
    result = engine.service.retrieve(question, plan=engine.deducer.deduce(question))
    obligations = ObligationChecker(engine.lexicon).from_retrieval(result)
    assert obligations
    assert all(o.avoid for o in obligations)
    assert all(o.id.split(" · ")[0].isdigit() for o in obligations)


def test_a_declared_property_is_not_enough_it_must_be_proved(engine) -> None:
    checker = ObligationChecker(engine.lexicon)
    result = engine.service.retrieve("idempotency key double charge retries payments")
    obligations = checker.from_retrieval(result)[:1]
    assert obligations
    words = " ".join(obligations[0].terms)
    proved = checker.coverage(obligations, [_row(words, words, PropertyStatus.VERIFIED)])
    declared = checker.coverage(obligations, [_row(words, words, PropertyStatus.UNVERIFIED)])
    unrelated = checker.coverage(obligations, [_row("colour", "blue", PropertyStatus.VERIFIED)])
    assert proved[0].status is ObligationStatus.COVERED
    assert declared[0].status is ObligationStatus.DECLARED
    assert unrelated[0].status is ObligationStatus.NOT_COVERED
    assert ObligationChecker.count(proved) == {"covered": 1}
