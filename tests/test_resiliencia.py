"""Romper Mirag a proposito y comprobar que no se cae en silencio.

Regla para cada caso: o hay un fallback, o hay un fallo controlado. Nunca un crash
sin explicar, y nunca un exito fingido sobre algo que no ocurrio.

    python3 test_resiliencia.py
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
import json
import os
import sys

import agent
import config
import dobles
import hibrido
import metadatos as M
import pipeline
import plan as P
import rag
import rapido
import skills
import suficiencia

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


def etapa(e, nombre):
    return next((p for p in e.pasos if p.nombre == nombre), None)


# ── el modelo devuelve cosas rotas ───────────────────────────────────────────

def json_invalido_del_modelo():
    with dobles.usar(dobles.JSON_ROTO):
        e = pipeline.ejecutar("Crea calculator.py con tests", guardar=False)
    paso = etapa(e, "entrega")
    assert paso and paso.estado == "error", "un JSON cortado tiene que quedar como error"
    assert "JSON" in paso.resumen or "json" in paso.resumen, paso.resumen


def el_modelo_no_devuelve_nada():
    with dobles.usar([{"role": "assistant", "content": None}]):
        e = pipeline.ejecutar("que es un indice", guardar=False)
    assert isinstance(e.respuesta, str)


def el_modelo_revienta():
    with dobles.usar(dobles.DECISION_SIMPLE, fallar_en=1):
        try:
            e = pipeline.ejecutar("que es un indice", guardar=False)
            assert isinstance(e.respuesta, str)
        except RuntimeError:
            pass          # propagar tambien vale: lo que no vale es un crash mudo


def el_guion_se_queda_corto():
    with dobles.usar([]):
        e = pipeline.ejecutar("que es un indice", guardar=False)
    assert isinstance(e.respuesta, str)


# ── skills y ejecucion ───────────────────────────────────────────────────────

def skill_que_no_existe():
    r = agent.SKILLS.get("skill_inventada") if hasattr(agent, "SKILLS") else None
    assert r is None
    salida = skills.verificar_codigo({"a.py": "print(1)"}, "cobol a.py")
    assert skills.veredicto(salida)[0] == "no_ejecutado", salida[:80]


def comando_que_no_existe():
    salida = skills.verificar_codigo({"a.py": "print(1)"}, "python3 no_existe.py")
    assert salida.startswith("FALLO"), salida[:80]


def codigo_generado_invalido():
    salida = rapido._comprobar_sintaxis({"roto.py": "def (:\n  pass"})
    assert salida and "sintaxis" in salida, salida


def dependencia_que_no_esta():
    salida = skills.verificar_codigo({"a.py": "import una_libreria_que_no_existe"},
                                     "python3 a.py")
    assert salida.startswith("FALLO"), salida[:80]
    assert "ModuleNotFound" in salida or "No module" in salida, salida[:160]


def sin_archivos():
    salida = skills.verificar_codigo({}, "python3 a.py")
    assert skills.veredicto(salida)[0] == "no_ejecutado", salida[:80]


def ruta_fuera_del_directorio():
    salida = skills.verificar_codigo({"../../fuera.py": "print(1)"}, "python3 fuera.py")
    assert skills.veredicto(salida)[0] == "no_ejecutado", salida[:80]


def el_timeout_corta():
    salida = skills.verificar_codigo({"a.py": "while True: pass"}, "python3 a.py")
    assert skills.veredicto(salida)[0] == "no_ejecutado", salida[:80]
    assert "TIMEOUT" in salida, salida[:80]


# ── retrieval ────────────────────────────────────────────────────────────────

def el_vector_falla_y_sigue_bm25():
    import hibrido as H
    original = H._tienda_para
    H._tienda_para = lambda trozos: (_ for _ in ()).throw(RuntimeError("backend caido"))
    try:
        r = H.recuperar("que es un indice de postgresql", vector=True)
        assert r.trozos, "sin vector hay que seguir devolviendo resultados"
        assert any(et == "vector" for et, _ in r.fallbacks), r.fallbacks
        assert any(p.nombre == "vector" and "fallo" in p.detalle for p in r.etapas)
    finally:
        H._tienda_para = original


def el_reranker_falla_y_queda_el_orden_de_rrf():
    original = hibrido._rerank_local
    hibrido._rerank_local = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("roto"))
    try:
        r = hibrido.recuperar("que es un indice", reranker=True)
        assert r.trozos, "tiene que quedar el orden previo"
        assert any(et == "reranker" for et, _ in r.fallbacks), r.fallbacks
    finally:
        hibrido._rerank_local = original


def el_filtro_deja_cero_y_se_avisa():
    p = P.deducir("que es un indice")._replace(technologies=["TecnologiaInventada"])
    r = hibrido.recuperar("que es un indice", plan=p)
    assert r.trozos, "un filtro vacio no puede dejarnos sin nada"
    assert any(et == "metadata_routing" for et, _ in r.fallbacks), \
        f"el fallback del filtro tiene que registrarse: {r.fallbacks}"


def retrieval_sin_resultados():
    r = hibrido.recuperar("zzzz qqqq xxxx")
    assert isinstance(r.trozos, list)
    v = suficiencia.evaluar("zzzz qqqq xxxx", r.trozos)
    assert not v.suficiente or v.grado == "cubierto"


def el_grafo_no_disponible():
    import builtins
    original = builtins.__import__

    def sin_grafo(nombre, *a, **k):
        if nombre == "grafo":
            raise ImportError("no hay grafo")
        return original(nombre, *a, **k)
    builtins.__import__ = sin_grafo
    try:
        import os, importlib
        os.environ["MIRAG_GRAPH_RETRIEVAL"] = "on"
        importlib.reload(config)
        with dobles.usar(dobles.DECISION_SIMPLE):
            e = pipeline.ejecutar("como se relaciona el outbox con las colas y ademas los "
                                  "reintentos", guardar=False)
        paso = etapa(e, "grafo")
        assert paso and paso.estado in ("error", "omitido"), paso
        assert isinstance(e.respuesta, str), "el pipeline tiene que terminar igual"
    finally:
        builtins.__import__ = original
        os.environ.pop("MIRAG_GRAPH_RETRIEVAL", None)
        importlib.reload(config)


def trozo_corrupto_no_tumba_los_metadatos():
    malo = rag.Trozo("", "", "sin separador", "")
    m = M.de(malo)
    assert isinstance(m.domain, str)


def corpus_vacio():
    r = hibrido.recuperar("lo que sea", indice=[])
    assert r.trozos == []


# ── presupuesto ──────────────────────────────────────────────────────────────

def presupuesto_agotado_para_seguro():
    original = agent.PRESUPUESTO.limite
    try:
        agent.PRESUPUESTO.reiniciar()
        agent.PRESUPUESTO.limite = 0.01
        agent.PRESUPUESTO.coste = 0.02
        with dobles.usar(dobles.DECISION_SIMPLE, coste=0.05):
            try:
                pipeline.ejecutar("que es un indice", guardar=False)
            except agent.PresupuestoAgotado:
                return
        raise AssertionError("con el tope pasado hay que parar, no seguir gastando")
    finally:
        agent.PRESUPUESTO.limite = original
        agent.PRESUPUESTO.reiniciar()


def el_candado_no_se_puede_saltar():
    assert agent.OFFLINE
    try:
        agent.llm([{"role": "user", "content": "x"}])
        raise AssertionError("el candado no mordio")
    except agent.ModoOffline:
        pass


# ── entradas absurdas ────────────────────────────────────────────────────────

def contexto_demasiado_grande():
    enorme = "reserva concurrente postgres " * 3000
    with dobles.usar(dobles.DECISION_SIMPLE):
        e = pipeline.ejecutar(enorme, guardar=False)
    assert isinstance(e.respuesta, str)


def entradas_raras():
    for entrada in ("", " ", "\n\n", "\x00\x01", "😀" * 50, "'; DROP TABLE --",
                    "../../etc/passwd", "a" * 5000):
        with dobles.usar(dobles.DECISION_SIMPLE):
            e = pipeline.ejecutar(entrada, guardar=False)
        assert isinstance(e.respuesta, str), repr(entrada[:20])


def plan_completamente_roto():
    for basura in ("{{{{", None, "]" * 100, '{"domains": [[[}', b"bytes"):
        p = P.leer(basura, "que es un indice")
        assert isinstance(p, P.PlanRecuperacion)


def ganancias_corruptas_no_encienden_nada():
    """Un archivo de politica ilegible no puede encender etapas por accidente."""
    si, motivo = config.activar("reranker", "general", ganancias={"reranker": "no soy un dict"})
    assert not si, motivo


if __name__ == "__main__":
    print("rompiendo a proposito · sin red · sin coste\n")
    for nombre, fn in list(globals().items()):
        if callable(fn) and getattr(fn, "__module__", "") == "__main__" \
                and not nombre.startswith(("probar", "etapa", "_")):
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
