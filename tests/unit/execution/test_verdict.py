"""The verdict is decided only by what was observed: exit code and markers."""

from __future__ import annotations

import pytest

from mirag.execution.verdict import MAX_OUTPUT, ExecutionResult, ExecutionStatus, Failure


def test_an_empty_script_is_never_green() -> None:
    result = ExecutionResult.from_run("", 0)
    assert result.status is ExecutionStatus.NO_EVIDENCE
    assert result.markers == {}


def test_markers_all_passing_are_evidence() -> None:
    result = ExecutionResult.from_run("TEST:a:PASS\nTEST:b:PASS", 0)
    assert result.status is ExecutionStatus.PASSED
    assert result.is_green
    assert result.passed == 2


def test_a_fail_marker_with_exit_zero_is_red() -> None:
    result = ExecutionResult.from_run("TEST:a:PASS\nTEST:b:FAIL", 0)
    assert result.status is ExecutionStatus.FAILED
    assert result.failure is Failure.MARKERS


def test_a_non_zero_exit_is_red_whatever_the_markers_say() -> None:
    result = ExecutionResult.from_run("TEST:a:PASS", 3)
    assert result.status is ExecutionStatus.FAILED
    assert result.exit_code == 3


def test_what_never_ran_is_not_green() -> None:
    result = ExecutionResult.not_executed("bash is not allowed")
    assert result.status is ExecutionStatus.NOT_EXECUTED
    assert not result.is_green


def test_the_header_is_never_counted_as_evidence() -> None:
    """The NO EVIDENCE header quotes the literal TEST:<id>:PASS to explain what is missing."""
    text = ExecutionResult.from_run("", 0).text
    assert "TEST:<id>:PASS" in text
    assert ExecutionResult.parse(text).markers == {}


def test_parse_round_trips_every_status() -> None:
    cases = [
        ExecutionResult.from_run("TEST:a:PASS", 0),
        ExecutionResult.from_run("TEST:a:FAIL", 0),
        ExecutionResult.from_run("boom", 2),
        ExecutionResult.from_run("nothing", 0),
        ExecutionResult.not_executed("TIMEOUT"),
        ExecutionResult.syntax_error("a.py:1: SyntaxError"),
    ]
    for original in cases:
        parsed = ExecutionResult.parse(original.text)
        assert parsed.status is original.status
        assert parsed.markers == original.markers
        assert parsed.failure == original.failure


def test_garbage_text_is_no_evidence() -> None:
    assert ExecutionResult.parse("hello").status is ExecutionStatus.NO_EVIDENCE
    assert ExecutionResult.parse(None).status is ExecutionStatus.NO_EVIDENCE


@pytest.mark.parametrize("noise_first", [True, False])
def test_markers_survive_truncation_on_either_side(noise_first: bool) -> None:
    noise = "x" * (MAX_OUTPUT * 3)
    output = (noise + "\nTEST:deep:PASS") if not noise_first else ("TEST:deep:PASS\n" + noise + "\nTEST:tail:PASS")
    output = output if noise_first else ("TEST:head:PASS\n" + noise + "\nTEST:mid:PASS\n" + noise)
    result = ExecutionResult.from_run(output, 0)
    assert result.truncated
    assert len(result.body) < len(output)
    assert set(result.markers) == {m.split(":")[1] for m in output.split() if m.startswith("TEST:")}


def test_a_buried_fail_is_not_lost() -> None:
    output = "TEST:a:PASS\n" + "y" * (MAX_OUTPUT * 2) + "\nTEST:b:FAIL\n" + "z" * (MAX_OUTPUT * 2)
    result = ExecutionResult.from_run(output, 0)
    assert result.status is ExecutionStatus.FAILED
    assert result.markers["b"] == "FAIL"


def test_describe_is_localised(catalog_en, catalog_es) -> None:
    passed = ExecutionResult.from_run("TEST:a:PASS", 0)
    assert passed.describe(catalog_en).startswith("TESTS PASSED")
    assert passed.describe(catalog_es).startswith("TESTS EN VERDE")
    assert ExecutionResult.from_run("", 0).describe(catalog_es).startswith("SIN EVIDENCIA")


def test_the_record_is_persistable() -> None:
    record = ExecutionResult.from_run("TEST:a:PASS", 0).as_record()
    assert record["status"] == "passed"
    assert record["passed"] == 1
