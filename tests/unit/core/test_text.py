from __future__ import annotations

import pytest

from mirag.core.text import (
    as_bool,
    as_list,
    distinctive_terms,
    first_json_object,
    lenient_json_list,
    normalize,
    repair_truncated_json,
    sha256_hex,
    short_hash,
)


def test_normalize_removes_accents_and_case() -> None:
    assert normalize("¿Cuántos Índices?") == "¿cuantos indices?"


def test_distinctive_terms_skip_short_words_stopwords_and_repeats() -> None:
    assert distinctive_terms("Índice índice de postgres", 4, {"postgres"}) == ["indice"]


def test_first_json_object_ignores_prose_and_nested_braces() -> None:
    text = 'I think {"goal": "x", "nested": {"a": {"b": 1}}} and then {"other": 2}'
    assert first_json_object(text) == {"goal": "x", "nested": {"a": {"b": 1}}}


def test_first_json_object_handles_braces_inside_strings() -> None:
    assert first_json_object('prefix {"text": "a } b {"} suffix') == {"text": "a } b {"}


def test_repair_truncated_json_recovers_a_cut_object() -> None:
    repaired = repair_truncated_json('{"goal":"something","domains":["04","08"],"technologies":["Postg')
    assert repaired is not None
    assert repaired["goal"] == "something"
    assert repaired["domains"] == ["04", "08"]


def test_repair_truncated_json_gives_up_without_braces() -> None:
    assert repair_truncated_json("no json here") is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, []),
        ("a, b; c\nd", ["a", "b", "c", "d"]),
        (["x", {"k": 1}, "none", "-"], ["x", '{"k": 1}']),
        ({"a": "1", "b": "2"}, ["1", "2"]),
        (7, ["7"]),
    ],
)
def test_as_list_accepts_whatever_the_model_sends(value: object, expected: list[str]) -> None:
    assert as_list(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(True, True), ("sí", True), ("yes", True), ("no", False), (0, False)])
def test_as_bool(value: object, expected: bool) -> None:
    assert as_bool(value) is expected


def test_lenient_json_list_parses_double_escaped_json_without_breaking_utf8() -> None:
    double_escaped = '[{\\"risk\\": \\"acción\\"}]'
    assert lenient_json_list(double_escaped) == [{"risk": "acción"}]


def test_lenient_json_list_keeps_a_bare_string() -> None:
    assert lenient_json_list("just text") == ["just text"]


def test_hashes() -> None:
    assert len(sha256_hex(b"x")) == 64  # never truncated: it is a proof of identity
    assert len(short_hash("x")) == 16
