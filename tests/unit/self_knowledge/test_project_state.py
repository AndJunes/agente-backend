"""Questions about Mirag itself are answered from facts; work orders are never swallowed."""

from __future__ import annotations

import pytest

from mirag.container import Container

SHORTCUTS = {
    "es": ["¿qué modelo usas?", "¿cuáles son los modos?", "¿qué skills tienes?", "¿cuántas cajas hay?",
           "¿qué áreas cubre el corpus?", "¿dónde guarda el código?", "¿de qué archivos se compone el proyecto?"],
    "en": ["which model do you use?", "what modes are there?", "what tools do you have?",
           "how many boxes are there?", "which areas does the corpus cover?", "where do you save the code?",
           "what files is the project made of?"],
}

NOT_SHORTCUTS = {
    "es": [
        # technical questions go to retrieval
        "¿qué es el outbox pattern?", "¿cómo evito el doble cobro?", "diferencia entre inner join y left join",
        "¿qué es un circuit breaker?",
        # WORK ORDERS that contain the tempting words: they all used to hijack the shortcut
        "Crea una función divide(a,b) y si no obtenés los marcadores desde la salida real respondé EVIDENCIA INSUFICIENTE",
        "escribe tests para mi API usando las herramientas que necesites",
        "ejecuta el código en modo debug y enseñame la salida",
        "genera los archivos del proyecto base",
        "implementa un rate limiter y prueba la concurrencia",
    ],
    "en": [
        "what is the outbox pattern?", "how do I avoid charging twice?", "difference between inner and left join",
        "Create a function divide(a, b) and if you cannot read the markers from the real output answer INSUFFICIENT",
        "write tests for my API using the tools you need",
        "run the code in debug mode and show me the output",
        "generate the files of the base project",
        "implement a rate limiter and test the concurrency",
    ],
}


@pytest.mark.parametrize("locale", ["en", "es"])
def test_questions_about_mirag_are_answered(shared_container: Container, locale: str) -> None:
    responder = shared_container.state(locale)
    for question in SHORTCUTS[locale]:
        answer = responder.answer(question)
        assert answer is not None, question
        assert answer.startswith("## ")


@pytest.mark.parametrize("locale", ["en", "es"])
def test_technical_questions_and_work_orders_are_left_alone(shared_container: Container, locale: str) -> None:
    responder = shared_container.state(locale)
    for question in NOT_SHORTCUTS[locale]:
        assert responder.answer(question) is None, question


def test_the_facts_come_from_the_real_objects(shared_container: Container) -> None:
    responder = shared_container.state("en")
    assert shared_container.settings.model in (responder.answer("which model do you use?") or "")
    modes = responder.answer("what modes are there?") or ""
    assert "pipeline" in modes and "architect" in modes
    tools = responder.answer("what tools do you have?") or ""
    for name in shared_container.tools("en").names:
        assert f"`{name}`" in tools
    boxes = responder.answer("which areas does the corpus cover?") or ""
    assert boxes.count("\n- ") == 19  # the 19 boxes, one bullet each


def test_the_structure_answer_points_to_entry_modules_that_exist(shared_container: Container) -> None:
    from mirag.paths import PACKAGE_ROOT
    from mirag.self_knowledge.project_state import ENTRY_POINTS

    for path, _ in ENTRY_POINTS:
        assert (PACKAGE_ROOT / path).is_file(), path
