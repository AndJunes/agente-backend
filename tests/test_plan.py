"""El parser del RetrievalPlan contra las siete formas en que llega la respuesta.

Ninguna de estas formas es inventada: las seis primeras son cosas que los modelos
mandan de verdad (el proyecto ya se comio JSON cortado por max_tokens, saltos de
linea literales dentro de cadenas y JSON doblemente escapado). La septima es que no
mande nada util, que tambien pasa.

    python3 test_plan.py
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
# La raiz (produccion) y las dos carpetas cuyos modulos se importan por nombre desnudo:
# `test_cache` importa `cache` (experimental/) y `test_plan` importa `eval` (benchmarks/).
for _d in (_RAIZ_REPO, _RAIZ_REPO / "experimental", _RAIZ_REPO / "benchmarks"):
    _sys.path.insert(0, str(_d))
import sys

import plan

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


PETICION = "como evito que dos usuarios reserven la misma plaza a la vez en postgres"


# ── 1. JSON valido ───────────────────────────────────────────────────────────

def json_valido():
    p = plan.leer('{"goal":"evitar doble reserva","domains":["04","08"],'
                  '"technologies":["PostgreSQL"],"needs_code":true,"depth":"deep"}', PETICION)
    assert p.domains == ["04", "08"], p.domains
    assert p.technologies == ["PostgreSQL"], p.technologies
    assert p.needs_code is True
    assert p.depth == "deep", p.depth


# ── 2. JSON dentro de un bloque de codigo ────────────────────────────────────

def json_en_bloque():
    p = plan.leer('Claro, aqui tienes:\n```json\n{"goal":"x","domains":["07"]}\n```\nEspero que sirva.',
                  PETICION)
    assert p.domains == ["07"], p.domains


# ── 3. JSON rodeado de prosa, sin bloque ─────────────────────────────────────

def json_con_prosa():
    p = plan.leer('He pensado esto. {"goal":"x","domains":["12"],"needs_graph":true} '
                  'Como ves, hace falta mirar observabilidad.', PETICION)
    assert p.domains == ["12"], p.domains
    assert p.needs_graph is True


def json_anidado_no_confunde():
    """Un regex de llaves codicioso o perezoso se equivoca con objetos dentro."""
    p = plan.leer('mira: {"goal":"x","domains":["04"],"extra":{"a":{"b":1}}} y ya', PETICION)
    assert p.domains == ["04"], p.domains


# ── 4. campos que faltan ─────────────────────────────────────────────────────

def campos_faltantes():
    p = plan.leer('{"domains":["09"]}', PETICION)
    assert p.domains == ["09"]
    assert p.depth == "normal", "tiene que haber un valor por defecto sensato"
    assert p.needs_symbols in (True, False)


def sin_cajas_usa_las_deducidas():
    """Un plan sin cajas no acota nada: mejor las deducidas que ninguna."""
    p = plan.leer('{"goal":"algo"}', PETICION)
    assert p.domains, "deberia haber caido a las cajas deducidas de la peticion"
    assert "deducidas" in p.origen, p.origen


# ── 5. JSON cortado a medias (max_tokens) ────────────────────────────────────

def json_cortado():
    p = plan.leer('{"goal":"evitar doble reserva","domains":["04","08"],"technologies":["Postg',
                  PETICION)
    assert p.domains == ["04", "08"], f"no rescato las cajas del JSON cortado: {p}"


def json_cortado_sin_remedio():
    p = plan.leer('{"goal":"evi', PETICION)
    assert p.domains, "si no se puede reparar, hay que caer al plan deducido"


# ── 6. el formato viejo ──────────────────────────────────────────────────────

def formato_viejo_cajas():
    p = plan.leer("He razonado bastante sobre el problema.\n\n**CAJAS: 03, 07**", PETICION)
    assert p.domains == ["03", "07"], p.domains
    assert "viejo" in p.origen, p.origen


# ── 7. nada aprovechable ─────────────────────────────────────────────────────

def respuesta_vacia():
    for entrada in ("", "   ", None, "no se, lo siento", "{}", "[]", '{"otra_cosa": 1}'):
        p = plan.leer(entrada, PETICION)
        assert isinstance(p, plan.PlanRecuperacion), entrada
        assert p.domains, f"con {entrada!r} deberia quedar el plan deducido"


def nunca_lanza():
    """Pase lo que pase, leer() devuelve un plan. Un fallo aqui tumbaria el pipeline."""
    for basura in ("{{{{", "}{", '{"domains": }', '{"domains": [[[}', "\x00\x01",
                   '{"depth": "profundisimo"}', '{"needs_code": "quiza"}',
                   '{"domains": {"a": "04"}}', "]" * 500, '{"domains":["99","abc"]}'):
        p = plan.leer(basura, PETICION)
        assert isinstance(p, plan.PlanRecuperacion), basura


# ── normalizacion ────────────────────────────────────────────────────────────

def cajas_por_nombre():
    p = plan.leer('{"domains":["Databases","Distributed Systems"]}', PETICION)
    assert p.domains == ["04", "08"], p.domains


def cajas_inventadas_se_tiran():
    p = plan.leer('{"domains":["99","caja que no existe"]}', PETICION)
    assert all(d != "99" for d in p.domains), p.domains


def listas_como_string():
    p = plan.leer('{"domains":["04"],"technologies":"PostgreSQL, Redis"}', PETICION)
    assert p.technologies == ["PostgreSQL", "Redis"], p.technologies


def booleanos_en_texto():
    p = plan.leer('{"domains":["04"],"needs_graph":"true","needs_symbols":"no"}', PETICION)
    assert p.needs_graph is True
    assert p.needs_symbols is False


def depth_invalido_cae_a_normal():
    p = plan.leer('{"domains":["04"],"depth":"muy profundo"}', PETICION)
    assert p.depth == "normal", p.depth


# ── el plan deducido, que es el suelo de todo ────────────────────────────────

def deducido_sin_modelo():
    p = plan.deducir(PETICION)
    assert p.domains, "sin modelo tambien hay que saber donde buscar"
    assert "04" in p.domains, f"postgres/plazas deberia tocar bases de datos: {p.domains}"
    assert p.needs_symbols is False, "una pregunta conceptual no necesita simbolos"


def deducido_detecta_codigo():
    p = plan.deducir("implementa una funcion calculate con sus tests")
    assert p.needs_code is True


def deducido_detecta_simbolos():
    p = plan.deducir("¿donde se valida el JWT en este proyecto?")
    assert p.needs_symbols is True, "una pregunta sobre codigo existente si los necesita"


def conceptual_no_pide_nada_caro():
    p = plan.deducir("que es un indice de postgresql")
    assert p.needs_symbols is False and p.needs_graph is False, \
        "una pregunta trivial no deberia encender etapas caras"


def el_resumen_es_legible():
    p = plan.leer('{"domains":["04","08"],"technologies":["PostgreSQL"],"needs_graph":true}',
                  PETICION)
    r = p.resumen()
    assert "04" in r and "PostgreSQL" in r and "grafo" in r, r


def el_origen_siempre_se_sabe():
    """La UI tiene que poder decir de donde salio el plan."""
    for entrada in ('{"domains":["04"]}', "CAJAS: 04", "basura", None):
        p = plan.leer(entrada, PETICION)
        assert p.origen and p.origen != "?", f"{entrada!r} -> sin origen"


# ══ ¿me piden codigo? medido, no supuesto ══════════════════════════════════

PIDEN_CODIGO = [
    "API de reservas para una clase con 1 sola plaza. Dos usuarios pueden reservar a la vez. Node.js.",
    "Reservar stock de un producto sin vender de mas cuando llegan pedidos simultaneos. Node.js.",
    "Rate limiter por usuario con token bucket, seguro ante peticiones concurrentes. Node.js.",
    "Consumidor de una cola que no aplique el mismo mensaje dos veces. Node.js.",
    "Crea calculator.py con calculate(a,b,operation) y sus tests",
    "Implementa reservar(conn, plaza_id, usuario) con sus tests",
    "Una funcion slugify(texto) que normalice acentos",
    "Cache LRU con expiracion por TTL, thread-safe. Python.",
    "Parser de CSV que tolere comillas escapadas. Python.",
]


def el_detector_de_codigo_caza_las_peticiones_reales():
    """Las tres primeras las FALLABA: sin verbo imperativo, el usuario recibia prosa.
    Lo descubrio el banco a nivel agente, con dinero real. Aqui se paga una vez."""
    fallan = [q for q in PIDEN_CODIGO if not plan.pide_codigo(q)]
    assert not fallan, f"pide codigo y no se detecta: {fallan}"


def el_detector_de_codigo_no_se_dispara_con_preguntas():
    """Un falso positivo manda al modelo a generar codigo para una consulta conceptual."""
    import eval as E
    consultas = [p for _f, p, _a in E.DUROS] + [p for p, _a in E.FACILES]
    falsos = [q for q in consultas if plan.pide_codigo(q)]
    # "worker pool en python" es genuinamente ambiguo: ofrecer codigo ahi no hace daño.
    assert len(falsos) <= 1, f"{len(falsos)} falsos positivos sobre {len(consultas)}: {falsos}"


def empezar_preguntando_manda_sobre_el_vocabulario():
    assert not plan.pide_codigo("como se escribe un ADR")
    assert not plan.pide_codigo("necesito rate limiting en mi endpoint")
    assert not plan.pide_codigo("¿que es una funcion pura?")


def una_firma_o_un_archivo_gana_a_la_forma_de_pregunta():
    """'¿Como implemento slugify(texto)?' pide codigo aunque empiece preguntando."""
    assert plan.pide_codigo("¿Como implemento slugify(texto) que normalice acentos?")
    assert plan.pide_codigo("que hago con calculator.py")


def el_plan_completo_hereda_la_deteccion():
    assert plan.deducir("Rate limiter por usuario con token bucket. Node.js.").needs_code
    assert not plan.deducir("que es un indice de postgres").needs_code


# ══ El imperativo rioplatense ══════════════════════════════════════════════

RIOPLATENSE = [
    "Creá una API REST de libros con CRUD completo",
    "Agregá tests al modulo de pagos",
    "Separá router, service y repository",
    "Implementá un microservicio de pagos",
    "Armá un bot de Telegram con comandos",
    "Hacé una CLI que lea un CSV",
    "Generá el scaffolding de una API de usuarios",
    "Añadí validacion de entrada",
    "Construí un rate limiter",
]


def el_imperativo_rioplatense_pide_codigo_igual():
    """Solo cambiaba la tilde: "Creá" daba False y "Crea" True. El usuario escribe asi,
    asi que la mitad de sus peticiones de codigo recibian prosa."""
    fallan = [q for q in RIOPLATENSE if not plan.pide_codigo(q)]
    assert not fallan, f"no se detectan como codigo: {fallan}"


def la_tilde_no_cambia_la_decision():
    for con, sin in (("Creá una API de libros", "Crea una API de libros"),
                     ("Agregá tests", "Agrega tests"),
                     ("Implementá un rate limiter", "Implementa un rate limiter")):
        assert plan.pide_codigo(con) == plan.pide_codigo(sin), (con, sin)


# ══ ¿proyecto o archivo suelto? ════════════════════════════════════════════

PROYECTOS = [
    "Creá una API REST de libros con CRUD completo usando FastAPI, SQLite y arquitectura "
    "por dominios. Separá router, service, repository, schemas y models. Agregá tests.",
    "Crea una API REST de libros con CRUD completo. Arquitectura por dominios, tests incluidos.",
    "Creá un microservicio de pagos con su estructura de carpetas, tests y README",
    "Quiero un proyecto Python con una CLI, sus tests y un requirements.txt",
    "Generá el scaffolding de una API de usuarios con capas separadas",
    "Hacé un backend de tareas con router, service y repository. Con tests.",
]


def un_proyecto_se_reconoce_como_proyecto():
    fallan = [q for q in PROYECTOS if not plan.pide_proyecto(q)]
    assert not fallan, f"piden un proyecto y no se detecta: {fallan}"


def un_archivo_suelto_no_es_un_proyecto():
    """Pedir `calculator.py` con sus tests no puede disparar la generacion de un arbol."""
    import banco
    sueltas = [t[1] for t in banco.TAREAS] + [
        "Crea calculator.py con calculate(a,b,operation) y sus tests",
        "Una funcion slugify(texto) que normalice acentos",
        "Cache LRU con expiracion por TTL, thread-safe. Python.",
    ]
    falsos = [q for q in sueltas if plan.pide_proyecto(q)]
    assert not falsos, f"un archivo suelto tomaria la rama de proyecto: {falsos}"


def una_consulta_nunca_es_un_proyecto():
    import eval as E
    consultas = [p for _f, p, _a in E.DUROS] + [p for p, _a in E.FACILES]
    falsos = [q for q in consultas if plan.pide_proyecto(q)]
    assert not falsos, f"{len(falsos)} consultas tomarian la rama de proyecto: {falsos[:3]}"


def preguntar_por_un_crud_no_es_pedirlo():
    for q in ("¿qué es un CRUD?", "cómo se estructura un proyecto por dominios",
              "cuál es la diferencia entre service y repository"):
        assert not plan.pide_proyecto(q), q


def pedir_un_proyecto_implica_pedir_codigo():
    """Si se contradijeran, el pipeline tomaria la rama de proyecto sin pedir codigo."""
    import banco
    import eval as E
    todas = (PROYECTOS + RIOPLATENSE + [t[1] for t in banco.TAREAS]
             + [p for _f, p, _a in E.DUROS] + [p for p, _a in E.FACILES])
    malas = [q for q in todas if plan.pide_proyecto(q) and not plan.pide_codigo(q)]
    assert not malas, f"proyecto sin codigo: {malas}"


def el_limite_conocido_del_detector_sigue_siendo_ese():
    """Medido: "Armá un bot de Telegram con comandos y persistencia" se queda en archivo
    suelto. Es genuinamente ambiguo y forzarlo abriria falsos positivos. Si algun dia
    cambia, que sea a proposito y no por un ajuste al azar."""
    assert not plan.pide_proyecto("Armá un bot de Telegram con comandos y persistencia en SQLite")


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "_")) and fn.__module__ == "__main__":
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
