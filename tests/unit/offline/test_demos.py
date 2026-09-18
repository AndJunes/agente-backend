"""Prepared demos: recognised, scripted, never served for the wrong question."""

from __future__ import annotations

import pytest

from mirag.container import Container
from mirag.offline.contracts import DemoContractRunner
from mirag.offline.demos import CANONICAL, DEMO_ORDER

RECOGNISED = {
    "en": [("Create a REST API of books with full CRUD", "project"),
           ("Create a function divide(a, b) that handles division by zero", "repair"),
           ("Create calculator.py with calculate(a, b, operation)", "code"),
           ("What is a PostgreSQL index?", "conceptual"),
           ("create a complete project with a calculator", "project")],
    "es": [("Creá una API REST de libros con CRUD completo", "project"),
           ("Crea una función divide(a, b) que maneje la división por cero", "repair"),
           ("Crea calculator.py con calculate(a, b, operation)", "code"),
           ("¿Qué es un índice de PostgreSQL?", "conceptual"),
           ("crea un proyecto completo con una calculadora", "project")],
}


@pytest.mark.parametrize("locale", ["en", "es"])
def test_each_demo_is_recognised_from_the_most_specific_to_the_most_general(
        shared_container: Container, locale: str) -> None:
    demos = shared_container.demos(locale)
    for question, expected in RECOGNISED[locale]:
        assert demos.recognize(question)[0] == expected, question


@pytest.mark.parametrize("locale", ["en", "es"])
def test_a_question_outside_the_demos_gets_no_model_instead_of_another_topic(
        shared_container: Container, locale: str) -> None:
    demos = shared_container.demos(locale)
    for question in ("what is Raft?", "¿qué es Raft?", "how does distributed consensus work"):
        key, script = demos.script_for(question)
        assert key is None
        assert "MIRAG_OFFLINE=1" in script[0]["content"]


def test_scripts_by_key_and_unknown_keys(shared_container: Container) -> None:
    demos = shared_container.demos("en")
    assert set(demos.available_scripts()) == set(DEMO_ORDER)
    assert demos.script(None)[0]["role"] == "assistant"
    with pytest.raises(KeyError):
        demos.script("invented")


@pytest.mark.parametrize("locale", ["en", "es"])
def test_the_listing_offers_the_four_canonical_demos_localised(shared_container: Container, locale: str) -> None:
    listing = shared_container.demos(locale).listing()
    assert [d["key"] for d in listing] == ["knowledge", "construction", "abstention", "project"]
    assert all(d["title"] and d["question"] and d["demonstrates"] for d in listing)
    assert next(d for d in listing if d["key"] == "abstention")["script"] is None


@pytest.mark.parametrize("locale", ["en", "es"])
def test_each_canonical_question_runs_the_script_it_announces(shared_container: Container, locale: str) -> None:
    """A demo button must never run another demo (a question mentioning division by zero used to
    be taken by the repair script while the page announced the construction one)."""
    demos = shared_container.demos(locale)
    for key, demo in CANONICAL.items():
        recognised, _ = demos.recognize(demos.canonical_question(key))
        assert recognised == demo.script, key


@pytest.mark.slow
@pytest.mark.parametrize("locale", ["en", "es"])
@pytest.mark.parametrize("key", list(CANONICAL))
def test_every_canonical_demo_fulfils_its_contract(container: Container, locale: str, key: str) -> None:
    report = DemoContractRunner(container).run(key, locale)
    assert report.fulfils, report.problems
    assert report.simulated is True


@pytest.mark.slow
def test_two_runs_give_the_same_observation(container: Container) -> None:
    runner = DemoContractRunner(container)
    first, second = runner.run("construction", "en"), runner.run("construction", "en")
    assert first.observed == second.observed


def test_unknown_demo(container: Container) -> None:
    with pytest.raises(KeyError):
        DemoContractRunner(container).run("invented", "en")
