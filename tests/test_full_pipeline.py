"""El test que importa: una tarea real recorre el pipeline entero.

Sin red, sin claves, sin dinero. La decision del modelo la pone un doble
determinista; TODO lo demas ocurre de verdad — el retrieval, el filtrado, la
suficiencia, la ejecucion de los tests y la evidencia.

    python3 test_full_pipeline.py

QUE DEMUESTRA Y QUE NO
    Demuestra que la maquina alrededor del modelo esta bien construida.
    NO demuestra que un modelo real vaya a decidir lo que decide el doble.
    Por eso estos casos son SIMULATED en el informe, no VERIFIED LOCALLY.
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
import os
import sys

import agent
import config
import dobles
import pipeline

# La ejecucion real esta APAGADA por defecto (skills.impedimento_de_ejecucion): en
# produccion este agente entrega el codigo y sus casos de test sin correrlos, y de eso se
# encarga el agente de QA. Estos casos existen para demostrar que cuando SI se ejecuta, la
# maquina no miente sobre lo que vio — asi que la encienden a proposito.
# La bandera se lee en cada llamada, no al importar, justo para permitir esto.
os.environ.setdefault("MIRAG_EJECUCION", "on")

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def etapa(ejecucion, nombre):
    for p in ejecucion.pasos:
        if p.nombre == nombre:
            return p
    raise AssertionError(f"el pipeline no registro la etapa {nombre!r}; "
                         f"registro: {[p.nombre for p in ejecucion.pasos]}")


def corrio(ejecucion, nombre):
    return etapa(ejecucion, nombre).estado == "ejecutado"


# ══ los seis recorridos ══════════════════════════════════════════════════════

def r1_pregunta_simple_ruta_minima():
    """Una pregunta trivial no puede encender la maquinaria cara."""
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar("¿Que es un indice de PostgreSQL?", guardar=False)
    assert not corrio(e, "simbolos"), "una pregunta conceptual no necesita el codigo"
    assert not corrio(e, "grafo"), "ni el grafo"
    # los nombres llevan el indice: tres llamadas producian tres pasos 'bm25' iguales
    # y etapa() devolvia el primero, asi que el test medía uno y creía medir tres
    for indice in ("conocimiento", "antipatrones", "fallos"):
        assert corrio(e, f"bm25:{indice}"), f"falta el retrieval de {indice}"
    assert e.veredicto.grado == "cubierto", e.veredicto.motivo
    assert e.ms < 2000, f"demasiado lento para una pregunta trivial: {e.ms} ms"


def r1_las_etapas_omitidas_dicen_por_que():
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar("¿Que es un indice de PostgreSQL?", guardar=False)
    for p in e.pasos:
        if p.estado == "omitido":
            assert p.resumen and len(p.resumen) > 8, f"{p.nombre} omitida sin explicar"


def r2_pregunta_conceptual():
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar("diferencia entre readiness y liveness probes", guardar=False)
    for indice in ("conocimiento", "antipatrones", "fallos"):
        assert corrio(e, f"filtro:{indice}") and corrio(e, f"bm25:{indice}") \
            and corrio(e, f"rrf:{indice}"), f"el pipeline de {indice} no corrio entero"
    assert etapa(e, "contexto").estado == "ejecutado"
    assert corrio(e, "recuperacion"), "no se registro la recuperacion unificada"
    assert e.veredicto.grado == "cubierto", e.veredicto.motivo


def r3_multisalto_recupera_lo_que_toca():
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar(
            "como evito un race condition al reservar un slot en postgres", guardar=False)
    # antes esto calculaba `cajas` a partir de un detalle que era un string, salia
    # vacio, y no se afirmaba nada sobre el. Ahora la recuperacion expone ids reales.
    ids = etapa(e, "recuperacion").detalle["ids"]
    cajas = {i.split(":")[1] for i in ids}
    assert len(cajas) >= 2, f"una pregunta multi-salto deberia tocar varias cajas: {cajas}"
    assert any(i.startswith("antipatrones:") for i in ids), \
        "una pregunta de concurrencia tiene que traer anti-patrones"
    assert e.veredicto.grado == "cubierto", e.veredicto.motivo
    # el grafo es condicional: lo que se exige es que la decision este EXPLICADA
    g = etapa(e, "grafo")
    assert g.resumen, "el grafo tiene que decir por que corrio o por que no"


def r4_tarea_de_codigo_se_ejecuta_de_verdad():
    """El codigo del fixture corre en un subproceso real y produce evidencia real."""
    with dobles.usar(dobles.CODIGO_CALCULADORA):
        e = pipeline.ejecutar(
            "Crea calculator.py con calculate(a, b, operation) que soporte add, subtract, "
            "multiply y divide, con manejo de division por cero y tests", guardar=False)
    assert e.entrega, "no hubo entrega"
    assert corrio(e, "verificacion"), etapa(e, "verificacion").resumen
    import skills
    assert skills.veredicto(e.salida)[0] == "verde", e.salida[:120]
    verificadas = [x for x in e.evidencia if x["estado"] == "verificado"]
    assert len(verificadas) == 3, f"esperaba 3 propiedades demostradas, hay {len(verificadas)}"
    assert all(x["ejecutado"] for x in verificadas), "una propiedad 'verificada' sin ejecucion"


def r4_el_arreglo_corrige_codigo_roto():
    with dobles.usar(dobles.CODIGO_ROTO_LUEGO_ARREGLADO):
        e = pipeline.ejecutar("Crea calculator.py con manejo de division por cero y tests",
                              guardar=False)
    assert any("arreglo" in p.nombre for p in e.pasos), \
        "no intento arreglar un codigo que fallaba"
    import skills
    assert skills.veredicto(e.salida)[0] == "verde", f"el arreglo no funciono: {e.salida[:100]}"


def r4_codigo_roto_sin_arreglo_no_miente():
    guion = [dobles.tool("entregar_implementacion",
                         {"archivos": {"calculator.py": dobles.CALCULADORA_ROTA,
                                       "test_calculator.py": dobles.TEST_CALCULADORA},
                          "comando_test": "python3 test_calculator.py",
                          "decisiones": "x", "propiedades": [
                              {"riesgo": "division por cero", "propiedad": "lanza",
                               "test_id": "division_por_cero"}], "sin_cubrir": []})] * 3
    with dobles.usar(guion):
        e = pipeline.ejecutar("Crea calculator.py con division por cero", guardar=False)
    refutadas = [x for x in e.evidencia if x["estado"] == "refutado"]
    assert refutadas, f"un test que imprime FAIL tiene que refutar la propiedad: {e.evidencia}"
    assert etapa(e, "verificacion").estado == "error"


def r5_simbolos_solo_cuando_toca():
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar("¿donde se valida el JWT en este proyecto?", guardar=False)
    assert corrio(e, "simbolos"), \
        f"una pregunta sobre codigo existente deberia usarlos: {etapa(e, 'simbolos').resumen}"
    nombres = [n for n, _, _ in (etapa(e, "simbolos").detalle or [])]
    assert nombres, "no encontro ningun simbolo"


def r6_lo_que_no_sabe_lo_dice():
    """El caso dificil: el retrieval SI devuelve algo, y aun asi hay que avisar."""
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar("implementar consenso Raft con garantias de linealizabilidad",
                              guardar=False)
    assert e.veredicto.grado == "mencionado", \
        f"Raft se menciona pero no se cubre: {e.veredicto.grado} · {e.veredicto.motivo}"
    assert not e.veredicto.suficiente
    assert "raft" in e.respuesta.lower(), "la respuesta tiene que avisar, no disimular"
    assert etapa(e, "suficiencia").estado == "fallback"


def r6_lo_ausente_tambien():
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar("streaming de video en tiempo real con WebRTC", guardar=False)
    assert e.veredicto.grado == "ausente", e.veredicto.motivo
    assert "no cubre" in e.respuesta.lower()


def r0_lo_que_ya_sabemos_no_se_busca():
    """ProjectState: 0 llamadas, 0 retrieval, respuesta instantanea."""
    with dobles.usar(dobles.DECISION_SIMPLE) as doble:
        e = pipeline.ejecutar("¿que skills tiene el agente?", guardar=False)
    assert doble.llamadas == 0, "respondio el estado del proyecto: no debia llamar a nadie"
    assert corrio(e, "estado del proyecto")
    assert len(e.pasos) == 1, f"no deberia haber recuperado nada: {[p.nombre for p in e.pasos]}"
    assert not e.simulado_llm, "esto no lo decidio ningun modelo"


# ══ invariantes de todo el pipeline ══════════════════════════════════════════

def nunca_se_llama_a_la_red():
    """El candado sigue puesto durante todo el recorrido."""
    assert agent.OFFLINE, "este test tiene que correr con el candado puesto"
    try:
        agent.llm([{"role": "user", "content": "x"}])
        raise AssertionError("agent.llm real no fallo con el candado puesto")
    except agent.ModoOffline:
        pass


def el_doble_no_gasta():
    antes = agent.PRESUPUESTO.coste
    with dobles.usar(dobles.DECISION_SIMPLE):
        pipeline.ejecutar("¿que es un indice?", guardar=False)
    assert agent.PRESUPUESTO.coste == antes, "un doble no puede sumar coste"


def toda_etapa_declara_su_fuente():
    with dobles.usar(dobles.CODIGO_CALCULADORA):
        e = pipeline.ejecutar("Crea calculator.py con tests", guardar=False)
    for p in e.pasos:
        assert p.fuente in ("ejecucion", "modelo", "corpus", ""), (p.nombre, p.fuente)
    ejecucion = [p for p in e.pasos if p.fuente == "ejecucion" and p.estado == "ejecutado"]
    assert ejecucion, "ninguna etapa produjo evidencia de ejecucion"


def la_traza_se_escribe_aparte():
    import traza
    destino = traza.ARCHIVO.parent / "trazas_noche.jsonl"
    antes = len(traza.leer(destino))
    with dobles.usar(dobles.CODIGO_CALCULADORA):
        # con carpeta propia: escribir en salida/ pisaba la ultima entrega del usuario
        import tempfile
        e = pipeline.ejecutar("Crea calculator.py con tests", guardar=True,
                              carpeta=tempfile.mkdtemp())
    filas = traza.leer(destino)
    assert len(filas) == antes + 1, "no se escribio la traza"
    assert filas[-1]["version"] == "v2-offline", filas[-1]["version"]
    assert filas[-1]["coste_usd"] == 0, "una ejecucion sin modelo no puede costar dinero"


def el_pipeline_no_revienta_con_basura():
    for entrada in ("", "   ", "?", "a", "\x00", "x" * 3000, "😀😀😀"):
        with dobles.usar(dobles.DECISION_SIMPLE):
            e = pipeline.ejecutar(entrada, guardar=False)
        assert isinstance(e.respuesta, str), entrada[:20]


if __name__ == "__main__":
    print("pipeline completo · sin red · sin claves · sin coste\n")
    for nombre, fn in list(globals().items()):
        if callable(fn) and getattr(fn, "__module__", "") == "__main__" \
                and not nombre.startswith(("probar", "etapa", "corrio", "_")):
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    print(f"llamadas reales al modelo: 0 · coste: $0.00 · dobles usados: "
          f"{dobles.CONTADOR['llamadas']}")
    sys.exit(1 if fallos else 0)
