"""The retrieval plan: the parser against the seven shapes the answer arrives in, and the
intent classifier against real requests in both languages.

None of the shapes is invented: models really send JSON cut by ``max_tokens``, JSON inside
prose or a fenced block, and the legacy ``BOXES:`` line. The seventh is sending nothing
useful at all, which also happens.
"""

from __future__ import annotations

import pytest

from mirag.retrieval.engine import RetrievalEngine, RetrievalEngineFactory
from mirag.retrieval.plan import EMPTY_PLAN, PLAN_TOOL, Depth, RetrievalPlan

REQUEST = {
    "en": "how do I stop two users from booking the same seat at the same time in postgres",
    "es": "como evito que dos usuarios reserven la misma plaza a la vez en postgres",
}


def parse(engine: RetrievalEngine, response: object, k: int = 4) -> RetrievalPlan:
    return engine.plan_parser.parse(response, REQUEST[engine.locale], k)


# ── the seven shapes ─────────────────────────────────────────────────────────

def test_shape_1_an_already_parsed_dict(engine: RetrievalEngine) -> None:
    plan = parse(engine, {"domains": ["04"], "needs_code": True})
    assert (plan.domains, plan.needs_code, plan.origin) == (("04",), True, "model_dict")


def test_shape_2_valid_json(engine: RetrievalEngine) -> None:
    plan = parse(engine, '{"goal":"avoid double booking","domains":["04","08"],'
                         '"technologies":["PostgreSQL"],"needs_code":true,"depth":"deep"}')
    assert plan.domains == ("04", "08")
    assert plan.technologies == ("PostgreSQL",)
    assert plan.needs_code is True and plan.depth == "deep"
    assert plan.origin == "json_text" and plan.goal == "avoid double booking"


def test_shape_3_json_wrapped_in_prose(engine: RetrievalEngine) -> None:
    plan = parse(engine, 'I thought about it. {"goal":"x","domains":["12"],"needs_graph":true} '
                         "As you see, observability matters.")
    assert (plan.domains, plan.needs_graph, plan.origin) == (("12",), True, "json_in_prose")


def test_nested_objects_do_not_confuse_the_extraction(engine: RetrievalEngine) -> None:
    """A greedy or a lazy brace regex gets objects inside objects wrong."""
    plan = parse(engine, 'look: {"goal":"x","domains":["04"],"extra":{"a":{"b":1}}} done')
    assert plan.domains == ("04",)


def test_shape_4_json_inside_a_fenced_block(engine: RetrievalEngine) -> None:
    plan = parse(engine, 'Sure, here it is:\n```json\n{"goal":"x","domains":["07"]}\n```\nHope it helps.')
    assert (plan.domains, plan.origin) == (("07",), "json_block")


def test_shape_5_json_cut_in_half_is_repaired(engine: RetrievalEngine) -> None:
    plan = parse(engine, '{"goal":"avoid double booking","domains":["04","08"],"technologies":["Postg')
    assert plan.domains == ("04", "08"), plan
    assert plan.origin == "json_repaired"


def test_shape_5_beyond_repair_falls_back_to_the_deduced_plan(engine: RetrievalEngine) -> None:
    plan = parse(engine, '{"goal":"avo')
    assert plan.domains == engine.deducer.deduce(REQUEST[engine.locale]).domains
    assert plan.origin == "not_understood"


@pytest.mark.parametrize("line", ["I reasoned a lot.\n\n**BOXES: 03, 07**", "He razonado.\n\n**CAJAS: 03, 07**"])
def test_shape_6_the_legacy_boxes_line_in_either_language(engine: RetrievalEngine, line: str) -> None:
    plan = parse(engine, line)
    assert (plan.domains, plan.origin) == (("03", "07"), "legacy_boxes")
    assert parse(engine, "BOXES: 01, 02, 03, 04, 05", k=2).domains == ("01", "02")


@pytest.mark.parametrize("response", ["", "   ", "sorry, I do not know", "{}", "[]", '{"other_thing": 1}', None])
def test_shape_7_nothing_useful_gives_the_deduced_plan(engine: RetrievalEngine, response: object) -> None:
    plan = parse(engine, response)
    assert isinstance(plan, RetrievalPlan)
    assert plan.domains == engine.deducer.deduce(REQUEST[engine.locale]).domains
    assert plan.origin in {"not_understood", "json_without_plan_fields", "no_model_answer"}


@pytest.mark.parametrize("garbage", [
    "{{{{", "}{", '{"domains": }', '{"domains": [[[}', "\x00\x01", '{"depth": "deepest"}',
    '{"needs_code": "maybe"}', '{"domains": {"a": "04"}}', "]" * 500, '{"domains":["99","abc"]}',
    42, 3.5, ["04"], b"bytes",
])
def test_the_parser_never_raises(engine: RetrievalEngine, garbage: object) -> None:
    """Whatever arrives, parse() returns a plan: a failure here would take the pipeline down."""
    plan = parse(engine, garbage)
    assert isinstance(plan, RetrievalPlan)
    assert plan.domains
    assert plan.origin and plan.origin != "unknown"


def test_deeply_nested_json_does_not_escape_as_recursion_error(engine: RetrievalEngine) -> None:
    """Thousands of nested brackets make the JSON decoder overflow instead of failing to
    parse: RecursionError is not a ValueError, and it used to escape from parse()."""
    deep = 100_000
    for garbage in ("[" * deep,
                    '{"a":' + "[" * deep + "]" * deep + "}",
                    'prose {"a":' + "[" * deep + "]" * deep + '} and {"domains":["04"]}',
                    '{"domains":["04"],"x":' + "[" * deep):
        plan = parse(engine, garbage)
        assert isinstance(plan, RetrievalPlan) and plan.domains, garbage[:30]


# ── normalisation ────────────────────────────────────────────────────────────

def test_boxes_by_name_are_normalised_to_numbers(engine: RetrievalEngine) -> None:
    assert parse(engine, '{"domains":["Databases","Distributed Systems"]}').domains == ("04", "08")
    assert parse(engine, '{"domains":["4","box 08","19 · System Design"]}').domains == ("04", "08", "19")


def test_invented_boxes_are_dropped_and_the_floor_is_used(engine: RetrievalEngine) -> None:
    plan = parse(engine, '{"domains":["99","a box that does not exist"]}')
    assert "99" not in plan.domains
    assert plan.domains == engine.deducer.deduce(REQUEST[engine.locale]).domains
    assert plan.origin_note == "no_boxes"


def test_a_plan_without_boxes_uses_the_deduced_ones_and_says_so(engine: RetrievalEngine) -> None:
    plan = parse(engine, '{"goal":"something"}')
    assert plan.domains, "should have fallen back to the boxes deduced from the request"
    assert plan.origin_note == "no_boxes"
    described = plan.describe_origin(engine.catalog)
    assert engine.catalog.t("plan.origin_note.no_boxes") in described


def test_normalise_boxes_caps_and_deduplicates(engine: RetrievalEngine) -> None:
    normalise = engine.deducer.normalise_boxes
    assert normalise(["04", "4", "Databases"]) == ("04",)
    assert len(normalise([str(n) for n in range(1, 20)])) == 6
    assert normalise(None) == () and normalise("") == ()
    assert normalise("04, 08") == ("04", "08")


def test_lists_as_strings_and_booleans_as_text(engine: RetrievalEngine) -> None:
    assert parse(engine, '{"domains":["04"],"technologies":"PostgreSQL, Redis"}').technologies == (
        "PostgreSQL", "Redis")
    plan = parse(engine, '{"domains":["04"],"needs_graph":"true","needs_symbols":"no"}')
    assert plan.needs_graph is True and plan.needs_symbols is False


def test_an_invalid_depth_falls_back_to_normal(engine: RetrievalEngine) -> None:
    assert parse(engine, '{"domains":["04"],"depth":"very deep"}').depth == Depth.NORMAL.value
    assert parse(engine, '{"domains":["09"]}').depth == Depth.NORMAL.value


def test_the_origin_is_always_known_and_translated(engine: RetrievalEngine) -> None:
    """The UI must be able to say where the plan came from."""
    t = engine.catalog
    for response in ('{"domains":["04"]}', "BOXES: 04", "garbage", None, {"domains": ["04"]}, "{}"):
        described = parse(engine, response).describe_origin(t)
        assert described and not described.startswith("plan.origin"), (response, described)
        assert described != t("plan.origin.unknown")


def test_the_summary_is_readable_in_the_language_of_the_catalog(engine: RetrievalEngine) -> None:
    plan = parse(engine, '{"domains":["04","08"],"technologies":["PostgreSQL"],"needs_graph":true}')
    summary = plan.summary(engine.catalog)
    assert "04" in summary and "PostgreSQL" in summary
    assert engine.catalog.t("plan.need.graph") in summary
    assert RetrievalPlan().summary(engine.catalog) == engine.catalog.t("plan.summary.unbounded")


def test_the_empty_plan_says_it_is_empty(engine: RetrievalEngine) -> None:
    assert EMPTY_PLAN.origin == "disabled" and not EMPTY_PLAN.domains
    assert "RETRIEVAL_PLAN=off" in EMPTY_PLAN.describe_origin(engine.catalog)


def test_without_a_request_the_floor_is_an_empty_plan(engine: RetrievalEngine) -> None:
    plan = engine.plan_parser.parse("garbage", "")
    assert plan.domains == () and plan.origin == "not_understood"


def test_the_plan_tool_asks_for_goal_and_domains() -> None:
    schema = PLAN_TOOL["function"]["parameters"]
    assert PLAN_TOOL["function"]["name"] == "search_plan"
    assert schema["required"] == ["goal", "domains"]
    assert schema["properties"]["depth"]["enum"] == [d.value for d in Depth]


# ── the deduced plan: the floor of everything ────────────────────────────────

def test_the_deduced_plan_needs_no_model(engine: RetrievalEngine) -> None:
    plan = engine.deducer.deduce(REQUEST[engine.locale])
    assert plan.origin == "deduced"
    assert "04" in plan.domains, f"postgres/seats should touch databases: {plan.domains}"
    assert plan.needs_symbols is False, "a conceptual question needs no symbols"
    assert plan.needs_code is False


@pytest.mark.parametrize(("locale", "question"), [
    ("en", "what is a postgresql index"), ("es", "que es un indice de postgresql"),
])
def test_a_conceptual_question_switches_on_nothing_expensive(
    engines: RetrievalEngineFactory, locale: str, question: str
) -> None:
    plan = engines.get(locale).deducer.deduce(question)
    assert not (plan.needs_symbols or plan.needs_graph or plan.needs_code or plan.needs_project)


@pytest.mark.parametrize(("locale", "code", "symbols", "graph", "deep"), [
    ("en", "Implement a calculate function with its tests", "where is the JWT validated in this project?",
     "what is the relationship between the outbox pattern and idempotency in payments",
     "design the architecture of a booking system"),
    ("es", "implementa una funcion calculate con sus tests", "¿donde se valida el JWT en este proyecto?",
     "que relacion hay entre el outbox pattern y la idempotencia en pagos",
     "diseñar la arquitectura de un sistema de reservas"),
])
def test_the_deduced_plan_inherits_the_classifier(
    engines: RetrievalEngineFactory, locale: str, code: str, symbols: str, graph: str, deep: str
) -> None:
    deducer = engines.get(locale).deducer
    assert deducer.deduce(code).needs_code
    assert deducer.deduce(symbols).needs_symbols
    assert deducer.deduce(graph).needs_graph
    assert deducer.deduce(deep).depth == Depth.DEEP.value
    assert not deducer.deduce(code).needs_symbols


# ══ does it ask for code? measured, not assumed ═════════════════════════════

ASKS_FOR_CODE = {
    "es": [
        "API de reservas para una clase con 1 sola plaza. Dos usuarios pueden reservar a la vez. Node.js.",
        "Reservar stock de un producto sin vender de mas cuando llegan pedidos simultaneos. Node.js.",
        "Rate limiter por usuario con token bucket, seguro ante peticiones concurrentes. Node.js.",
        "Consumidor de una cola que no aplique el mismo mensaje dos veces. Node.js.",
        "Crea calculator.py con calculate(a,b,operation) y sus tests",
        "Implementa reservar(conn, plaza_id, usuario) con sus tests",
        "Una funcion slugify(texto) que normalice acentos",
        "Cache LRU con expiracion por TTL, thread-safe. Python.",
        "Parser de CSV que tolere comillas escapadas. Python.",
    ],
    "en": [
        "Booking API for a class with a single seat. Two users can book at the same time. Node.js.",
        "Reserve stock of a product without overselling when simultaneous orders arrive. Node.js.",
        "Per-user rate limiter with a token bucket, safe under concurrent requests. Node.js.",
        "Queue consumer that never applies the same message twice. Node.js.",
        "Create calculator.py with calculate(a,b,operation) and its tests",
        "Implement book_seat(conn, seat_id, user) with its tests",
        "A slugify(text) function that strips accents",
        "LRU cache with TTL expiry, thread-safe. Python.",
        "CSV parser that tolerates escaped quotes. Python.",
    ],
}

# The rioplatense imperative ("Creá", "agregá", "separá") and its English counterpart.
IMPERATIVES = {
    "es": [
        "Creá una API REST de libros con CRUD completo", "Agregá tests al modulo de pagos",
        "Separá router, service y repository", "Implementá un microservicio de pagos",
        "Armá un bot de Telegram con comandos", "Hacé una CLI que lea un CSV",
        "Generá el scaffolding de una API de usuarios", "Añadí validacion de entrada",
        "Construí un rate limiter",
    ],
    "en": [
        "Create a books REST API with full CRUD", "Add tests to the payments module",
        "Split router, service and repository", "Implement a payments microservice",
        "Build a Telegram bot with commands", "Make me a CLI that reads a CSV",
        "Generate the scaffolding of a users API", "Add input validation", "Build a rate limiter",
    ],
}

PROJECTS = {
    "es": [
        "Creá una API REST de libros con CRUD completo usando FastAPI, SQLite y arquitectura por "
        "dominios. Separá router, service, repository, schemas y models. Agregá tests.",
        "Crea una API REST de libros con CRUD completo. Arquitectura por dominios, tests incluidos.",
        "Creá un microservicio de pagos con su estructura de carpetas, tests y README",
        "Quiero un proyecto Python con una CLI, sus tests y un requirements.txt",
        "Generá el scaffolding de una API de usuarios con capas separadas",
        "Hacé un backend de tareas con router, service y repository. Con tests.",
    ],
    "en": [
        "Create a books REST API with full CRUD using FastAPI, SQLite and a domain-based architecture. "
        "Split router, service, repository, schemas and models. Add tests.",
        "Create a books REST API with full CRUD. Domain-based architecture, tests included.",
        "Create a payments microservice with its folder structure, tests and README",
        "I want a Python project with a CLI, its tests and a requirements.txt",
        "Generate the scaffolding of a users API with separate layers",
        "Build a tasks backend with router, service and repository. With tests.",
    ],
}

# Single-file tasks of the agent benchmark: code, never a project tree.
SINGLE_FILE_TASKS = {
    "es": [
        "API de reservas para una clase con 1 sola plaza. Dos usuarios pueden reservar a la vez: nunca "
        "deben asignarse dos reservas a la misma plaza. Node.js.",
        "Endpoint POST /payments con orderId y amount, Idempotency-Key y sin doble cobro ante reintentos "
        "concurrentes. Node.js.",
        "Reservar stock de un producto sin vender de mas cuando llegan pedidos simultaneos. Node.js.",
        "Rate limiter por usuario con token bucket, seguro ante peticiones concurrentes. Node.js.",
        "Consumidor de una cola que no aplique el mismo mensaje dos veces aunque se reentregue. Node.js.",
        "Crea calculator.py con calculate(a,b,operation) y sus tests",
        "Una funcion slugify(texto) que normalice acentos",
        "Cache LRU con expiracion por TTL, thread-safe. Python.",
    ],
    "en": [
        "Booking API for a class with a single seat. Two users can book at the same time: two bookings "
        "must never be assigned to the same seat. Node.js.",
        "POST /payments endpoint with orderId and amount, Idempotency-Key and no double charge under "
        "concurrent retries. Node.js.",
        "Reserve stock of a product without overselling when simultaneous orders arrive. Node.js.",
        "Per-user rate limiter with a token bucket, safe under concurrent requests. Node.js.",
        "Queue consumer that never applies the same message twice even if it is redelivered. Node.js.",
        "Create calculator.py with calculate(a,b,operation) and its tests",
        "A slugify(text) function that strips accents",
        "LRU cache with TTL expiry, thread-safe. Python.",
    ],
}

# The easy and hard retrieval benchmark questions: every one is a query, not an order.
QUESTIONS = {
    "es": [
        "que es el outbox pattern", "como funciona el reranking en RAG",
        "diferencia entre liveness y readiness", "como se evita el thundering herd", "que es write skew",
        "SLO y error budget", "pagination con cursor", "como guardo una contraseña de usuario",
        "que es CORS y para que sirve", "prompt injection en agentes",
        "idempotency key para no cobrar dos veces", "que es un circuit breaker",
        "tipos de indices en postgres", "blue green o canary", "testcontainers para tests", "N+1 queries",
        "como funciona el GIL de python", "multi-tenancy y aislamiento", "fan out on write timeline",
        "dead letter queue", "que es SQL injection", "como uso JWT", "SSE o websocket",
        "diferencia entre inner join y left join", "que es coupling y cohesion",
        "que dimensiones tiene un embedding", "worker pool en python", "como se escribe un ADR",
        "checklist antes de desplegar", "volumenes persistentes en kubernetes", "CSV injection",
        "mi servicio se queda esperando para siempre a otro que no responde",
        "cuando un servicio va lento las peticiones se amontonan y tiran todo lo demas",
        "que el cliente no pague dos veces si le da dos veces al boton",
        "subir un archivo grande sin que pase por mi servidor",
        "enterarme de que algo va mal antes de que me lo cuente un cliente",
        "la consulta tarda muchisimo cuando filtro por fecha y hay millones de filas",
        "guardar quien hizo que y cuando para poder auditarlo despues",
        "repartir el trabajo pesado para no bloquear la respuesta al usuario",
        "como hago health check de un servicio", "cursor based pagination o offset para mi API",
        "necesito rate limiting en mi endpoint", "graceful shutdown de un pod sin cortar requests en vuelo",
        "idenpotencia en pagos", "indices en postgress", "transaciones y aislamento en base de datos",
        "como evito que dos usuarios reserven la misma plaza a la vez en postgres",
        "cobrar una sola vez aunque el cliente reintente y la red falle",
        "publicar un evento y guardar en base de datos sin que se descuadren",
    ],
    "en": [
        "what is the outbox pattern", "how does reranking work in RAG",
        "difference between liveness and readiness", "how do you avoid the thundering herd",
        "what is write skew", "SLO and error budget", "cursor pagination", "how do I store a user password",
        "what is CORS and what is it for", "prompt injection in agents",
        "idempotency key so we never charge twice", "what is a circuit breaker",
        "types of indexes in postgres", "blue green or canary", "testcontainers for tests", "N+1 queries",
        "how does the python GIL work", "multi-tenancy and isolation", "fan out on write timeline",
        "dead letter queue", "what is SQL injection", "how do I use JWT", "SSE or websocket",
        "difference between inner join and left join", "what are coupling and cohesion",
        "how many dimensions does an embedding have", "worker pool in python", "how do you write an ADR",
        "checklist before deploying", "persistent volumes in kubernetes", "CSV injection",
        "my service waits forever for another one that does not answer",
        "when a service is slow the requests pile up and take everything else down",
        "the customer must not pay twice if they press the button twice",
        "upload a big file without it going through my server",
        "find out something is wrong before a customer tells me",
        "the query takes forever when I filter by date and there are millions of rows",
        "keep who did what and when so it can be audited later",
        "spread the heavy work so the response to the user is not blocked",
        "how do I health check a service", "cursor based pagination or offset for my API",
        "I need rate limiting on my endpoint", "graceful shutdown of a pod without cutting in-flight requests",
        "idenpotency in payments", "indexes in postgress", "transations and isolaton in a database",
        "how do I stop two users from booking the same seat at the same time in postgres",
        "charge only once even if the client retries and the network fails",
        "publish an event and save to the database without them getting out of sync",
    ],
}

# Genuinely ambiguous: offering code for "worker pool in python" does no harm.
KNOWN_AMBIGUOUS = {"worker pool en python", "worker pool in python", "fan out on write timeline"}


def test_the_code_detector_catches_the_real_requests(engine: RetrievalEngine) -> None:
    """The first three used to FAIL: no imperative verb, and the user got prose back."""
    missed = [q for q in ASKS_FOR_CODE[engine.locale] if not engine.classifier.asks_for_code(q)]
    assert not missed


def test_the_imperative_asks_for_code_including_the_rioplatense_one(engine: RetrievalEngine) -> None:
    """Only the accent changed: "Creá" gave False and "Crea" True, so half of the user's code
    requests got prose."""
    missed = [q for q in IMPERATIVES[engine.locale] if not engine.classifier.asks_for_code(q)]
    assert not missed


@pytest.mark.parametrize(("with_accent", "without"), [
    ("Creá una API de libros", "Crea una API de libros"),
    ("Agregá tests", "Agrega tests"),
    ("Separá router y service", "Separa router y service"),
    ("Implementá un rate limiter", "Implementa un rate limiter"),
    ("¿Qué es una función pura?", "que es una funcion pura?"),
])
def test_the_accent_does_not_change_the_decision(engine_es: RetrievalEngine, with_accent: str, without: str) -> None:
    classifier = engine_es.classifier
    assert classifier.asks_for_code(with_accent) == classifier.asks_for_code(without)
    assert classifier.asks_for_project(with_accent) == classifier.asks_for_project(without)


def test_the_code_detector_does_not_fire_on_questions(engine: RetrievalEngine) -> None:
    """A false positive sends the model to generate code for a conceptual query."""
    false = [q for q in QUESTIONS[engine.locale] if engine.classifier.asks_for_code(q)]
    assert set(false) <= KNOWN_AMBIGUOUS, false
    assert len(false) <= 2, false
    if engine.locale == "es":
        assert len(false) <= 1, "the original measurement: 1 false positive out of 49"


@pytest.mark.xfail(strict=True, reason=(
    "lexicon bug (src/mirag/locales/en/lexicon.json intent.code_verbs): the bare verb 'write' "
    "also matches the noun phrase 'fan out on write'. Remove this xfail when the lexicon is fixed."))
def test_the_english_write_verb_does_not_fire_on_fan_out_on_write(engine_en: RetrievalEngine) -> None:
    assert not engine_en.classifier.asks_for_code("fan out on write timeline")


@pytest.mark.parametrize(("locale", "question"), [
    ("es", "como se escribe un ADR"), ("es", "necesito rate limiting en mi endpoint"),
    ("es", "¿que es una funcion pura?"), ("es", "¿qué es una función pura?"),
    ("en", "how do you write an ADR"), ("en", "I need rate limiting on my endpoint"),
    ("en", "what is a pure function?"),
])
def test_starting_with_a_question_beats_the_vocabulary(engines: RetrievalEngineFactory, locale: str, question: str) -> None:
    assert not engines.get(locale).classifier.asks_for_code(question)


@pytest.mark.parametrize(("locale", "request_"), [
    ("es", "¿Como implemento slugify(texto) que normalice acentos?"), ("es", "que hago con calculator.py"),
    ("en", "How do I implement slugify(text) that strips accents?"), ("en", "what do I do with calculator.py"),
])
def test_a_signature_or_a_file_name_beats_the_question_form(engines: RetrievalEngineFactory, locale: str, request_: str) -> None:
    assert engines.get(locale).classifier.asks_for_code(request_)


# ══ a project or a single file? ═════════════════════════════════════════════

def test_a_project_is_recognised_as_a_project(engine: RetrievalEngine) -> None:
    missed = [q for q in PROJECTS[engine.locale] if not engine.classifier.asks_for_project(q)]
    assert not missed


def test_a_single_file_is_not_a_project(engine: RetrievalEngine) -> None:
    """Asking for `calculator.py` with its tests must not trigger the generation of a tree."""
    false = [q for q in SINGLE_FILE_TASKS[engine.locale] if engine.classifier.asks_for_project(q)]
    assert not false


def test_a_question_is_never_a_project(engine: RetrievalEngine) -> None:
    false = [q for q in QUESTIONS[engine.locale] if engine.classifier.asks_for_project(q)]
    assert not false


@pytest.mark.parametrize(("locale", "question"), [
    ("es", "¿qué es un CRUD?"), ("es", "cómo se estructura un proyecto por dominios"),
    ("es", "cuál es la diferencia entre service y repository"),
    ("en", "what is a CRUD?"), ("en", "how do you structure a project by domains"),
    ("en", "what is the difference between service and repository"),
])
def test_asking_about_a_crud_is_not_asking_for_one(engines: RetrievalEngineFactory, locale: str, question: str) -> None:
    assert not engines.get(locale).classifier.asks_for_project(question)


def test_asking_for_a_project_implies_asking_for_code(engine: RetrievalEngine) -> None:
    """If they contradicted each other, the pipeline would take the project branch without
    asking for code. 'Split router, service and repository' used to break it in English."""
    loc = engine.locale
    everything = (PROJECTS[loc] + IMPERATIVES[loc] + SINGLE_FILE_TASKS[loc] + QUESTIONS[loc]
                  + ASKS_FOR_CODE[loc])
    classifier = engine.classifier
    broken = [q for q in everything if classifier.asks_for_project(q) and not classifier.asks_for_code(q)]
    assert not broken
    for request in everything:
        plan = engine.deducer.deduce(request)
        assert plan.needs_code or not plan.needs_project, request


@pytest.mark.parametrize(("locale", "request_"), [
    ("es", "Armá un bot de Telegram con comandos y persistencia en SQLite"),
    ("en", "Build a Telegram bot with commands and persistence in SQLite"),
])
def test_the_known_limit_of_the_detector_stays_where_it_is(engines: RetrievalEngineFactory, locale: str, request_: str) -> None:
    """Measured: this stays a single file. It is genuinely ambiguous and forcing it would open
    false positives. If it ever changes, let it be on purpose."""
    classifier = engines.get(locale).classifier
    assert classifier.asks_for_code(request_)
    assert not classifier.asks_for_project(request_)


def test_empty_requests_ask_for_nothing(engine: RetrievalEngine) -> None:
    classifier = engine.classifier
    for request in ("", None):
        assert not classifier.asks_for_code(request)  # type: ignore[arg-type]
        assert not classifier.asks_for_project(request)  # type: ignore[arg-type]
        assert not classifier.needs_symbols(request)  # type: ignore[arg-type]
        assert classifier.depth(request) == Depth.NORMAL.value  # type: ignore[arg-type]
