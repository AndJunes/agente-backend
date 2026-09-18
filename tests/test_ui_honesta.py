"""La pagina no puede afirmar nada que el backend no haya hecho.

El bug que cierra esta suite: con el candado offline, cualquier pregunta que no dijera
"calculator" recibia un parrafo fijo y seguro sobre indices de PostgreSQL. Preguntar
"¿que es Raft?" devolvia esa explicacion. El aviso de "decision simulada" era cierto y
el conjunto mentia igual: un fixture que responde con seguridad a la pregunta equivocada
es exactamente lo que este proyecto existe para no hacer.

    python3 test_ui_honesta.py
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
import re
import sys
from pathlib import Path

import demos
import dobles
import pipeline
import server

AQUI = Path(__file__).parent
import server as _srv
# `index.html` es de PRODUCCION: se ancla al modulo que lo sirve, no a esta carpeta.
# Colgado de `AQUI` dejaba de encontrarse en cuanto el test cambiaba de sitio.
_PAGINA = Path(_srv.__file__).resolve().parent / "index.html"
HTML = _PAGINA.read_text()
casos = []


def probar(nombre, fn):
    try:
        fn(); casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _por_http(pregunta, modo="pipeline"):
    """Arranca el servidor real en un puerto libre y lee los eventos SSE que emite."""
    import http.client
    import json
    import threading
    from http.server import ThreadingHTTPServer

    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    try:
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=120)
        c.request("POST", "/", json.dumps({"pregunta": pregunta, "modo": modo}),
                  {"Content-Type": "application/json"})
        cuerpo = c.getresponse().read().decode()
    finally:
        srv.shutdown()
    return [json.loads(l[6:]) for l in cuerpo.splitlines() if l.startswith("data: ")]


def _offline(pregunta):
    demo, guion = demos.guion_para(pregunta)
    with dobles.usar(guion):
        e = pipeline.ejecutar(pregunta, guardar=False)
    return demo, e, server._respuesta_pipeline(e, demo)


# ══ El fixture ya no contesta a lo que no le preguntaron ════════════════════

def una_pregunta_fuera_de_las_demos_no_recibe_respuesta_inventada():
    demo, e, md = _offline("¿Qué es Raft y cómo garantiza linealizabilidad?")
    assert demo is None, f"se le asigno la demo {demo!r}"
    assert "indice de PostgreSQL" not in e.respuesta, \
        "sigue contestando sobre indices a una pregunta sobre Raft"
    assert "SIN MODELO" in md
    assert "no se inventa" in md


def las_tres_demos_se_reconocen():
    esperado = {"reparacion", "codigo", "conceptual"}
    vistos = {demos.reconocer(d["ejemplo"])[0] for d in demos.catalogo()}
    assert vistos == esperado, f"alguna demo no se reconoce con su propio ejemplo: {vistos}"


def cada_demo_se_lleva_su_guion_y_no_el_de_otra():
    """'crea calculator.py que use un indice' es codigo, no una pregunta conceptual."""
    assert demos.reconocer("crea calculator.py que use un indice")[0] == "codigo"
    assert demos.reconocer("que es un indice de postgres")[0] == "conceptual"
    assert demos.reconocer("divide(a,b) con division por cero")[0] == "reparacion"


def sin_demo_el_pipeline_corre_igual():
    """Lo unico que falta es la decision del modelo: el resto es real y hay que verlo."""
    _, e, _ = _offline("¿Qué es Raft?")
    nombres = {p.nombre for p in e.pasos}
    assert {"plan de busqueda", "recuperacion", "suficiencia", "contexto"} <= nombres, nombres
    assert e.veredicto is not None, "sin veredicto de suficiencia no se ve nada real"


def sin_demo_se_dice_lo_que_el_corpus_si_sabe():
    _, e, _ = _offline("¿Qué es Raft?")
    assert "raft" in e.respuesta.lower(), "ni siquiera nombra lo que se pregunto"


# ══ Simulado y sin-modelo son cosas distintas ══════════════════════════════

def el_markdown_distingue_demo_de_sin_modelo():
    _, _, con = _offline("que es un indice de postgres")
    _, _, sin = _offline("¿Qué es Raft?")
    assert "SIMULADA · demo" in con and "SIN MODELO" not in con
    assert "SIN MODELO" in sin and "SIMULADA · demo" not in sin


def la_demo_dice_que_lo_ejecutado_si_es_real():
    _, _, md = _offline("Crea calculator.py con calculate y sus tests")
    assert "se verificó es real" in md, "no separa la decision simulada de la ejecucion real"


# ══ La pagina ══════════════════════════════════════════════════════════════

def los_chips_nuevos_existen_con_su_estilo():
    for chip in ("simulado", "sinmodelo", "experimental", "desactivado"):
        assert f"  {chip}:" in HTML or f"{chip}:" in HTML, f"falta el chip {chip}"
        assert f".chip-{chip}" in HTML, f"el chip {chip} no tiene estilo"


def la_pagina_no_habla_de_modos_retirados():
    """Un aviso que menciona un modo inexistente es ruido, no honestidad."""
    for muerto in ("modo === 'rapido'", "modo === 'simple'", "El modo rápido lo ejecuta"):
        assert muerto not in HTML, f"la pagina sigue hablando de un modo retirado: {muerto!r}"


def la_pagina_solo_ofrece_los_modos_que_existen():
    ofrecidos = set(re.findall(r'name="modo" value="(\w+)"', HTML))
    assert ofrecidos == {"pipeline", "arquitecto"}, ofrecidos


def arquitecto_va_etiquetado_como_experimental():
    i = HTML.index('value="arquitecto"')
    assert "experimental" in HTML[i:i + 400].lower()


def el_aviso_de_verde_no_dice_correcto():
    i = HTML.index("Verde aquí significa")
    assert "no <b>es correcto</b>" in HTML[i:i + 300]


# ══ El chip sale de un evento, no de una suposicion ════════════════════════

def el_backend_emite_el_estado_del_candado():
    """Contra el servidor de verdad, no grepeando el fuente: eso no prueba que se emita."""
    eventos = _por_http("¿Qué es Raft?")
    candado = next((e for e in eventos if e.get("nombre") == "candado offline"), None)
    assert candado, f"no se emitio el paso del candado: {[e.get('nombre') for e in eventos]}"
    assert candado["estado"] == "sinmodelo", candado
    assert candado["detalle"]["demo"] is None

    candado2 = next(e for e in _por_http("que es un indice de postgres")
                    if e.get("nombre") == "candado offline")
    assert candado2["estado"] == "simulado"
    assert candado2["detalle"]["demo"] == "conceptual"


def el_estado_emitido_coincide_con_el_markdown():
    """Lo que pinta el chip y lo que dice el texto tienen que ser el mismo hecho."""
    for pregunta, estado, marca in (("que es un indice de postgres", "simulado", "SIMULADA"),
                                    ("¿Qué es Raft?", "sinmodelo", "SIN MODELO")):
        demo, _, md = _offline(pregunta)
        assert ("simulado" if demo else "sinmodelo") == estado
        assert marca in md


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and getattr(fn, "__module__", "") == "__main__" \
                and not nombre.startswith(("probar", "_")):
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
