"""La configuracion de retrieval, y que las decisiones tengan evidencia detras.

Ninguna etapa puede quedar encendida "porque ya existe". Estos tests comprueban que
lo que esta ON lo esta por una medicion, y que encenderlo no degrada nada que importe.

    python3 test_calibracion.py
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
import importlib
import json
import os
import sys
from pathlib import Path

import config
import plan as P
import recuperacion
import suficiencia

AQUI = Path(__file__).parent
# La raiz de PRODUCCION, derivada de un modulo suyo: inmune a donde viva el test.
_RAIZ_PROD = Path(config.__file__).resolve().parent
casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _ganancias():
    return json.loads(config.GANANCIAS.read_text())


# ══ 1 · baseline reproducible ════════════════════════════════════════════════

def el_baseline_es_reproducible():
    """Dos medidas del mismo brazo tienen que dar lo mismo. Si no, no se puede comparar."""
    import calibracion
    a = calibracion.medir("a")
    b = calibracion.medir("b")
    assert a["total"] == b["total"], f"{a['total']} vs {b['total']}"
    assert a["duro"] == b["duro"]


def la_calibracion_esta_guardada():
    d = json.loads((config.GANANCIAS.parent / "calibracion_fase3.json").read_text())
    assert {a["nombre"] for a in d["brazos"]}, "no hay brazos medidos"
    assert d["indices"]["recuperados_totales"] > 0


# ══ 2-3 · el reranker cambia ranking Y contexto ═════════════════════════════

def el_reranker_cambia_el_ranking():
    q = "como evito un race condition al reservar una plaza"
    plan_ = P.deducir(q)
    sin = recuperacion.recuperar(q, plan=plan_, reranker=False).ids()
    con = recuperacion.recuperar(q, plan=plan_, reranker=True).ids()
    assert sin != con, "el reranker no altera el orden de nada"


def el_reranker_cambia_el_contexto():
    q = "como evito un race condition al reservar una plaza"
    plan_ = P.deducir(q)
    a, _ = recuperacion.construir_contexto(
        recuperacion.recuperar(q, plan=plan_, reranker=True), peticion=q)
    b, _ = recuperacion.construir_contexto(
        recuperacion.recuperar(q, plan=plan_, reranker=False), peticion=q)
    assert a != b, "el reranker no llega al contexto"


def el_reranker_esta_on_por_una_medicion():
    si, motivo = config.activar("reranker", "general")
    assert si, f"el reranker deberia estar ON: {motivo}"
    assert "medida" in motivo, f"esta ON sin medicion detras: {motivo}"
    g = _ganancias()["reranker"]["general"]
    assert g["sobre"] == "pipeline real (fase 3)", g
    assert g["delta_mrr"] >= config.UMBRAL_MRR, g


# ══ 4 · el vector se puede encender y apagar sin romper ═════════════════════

def el_vector_se_puede_conmutar():
    q = "indices en postgress"
    plan_ = P.deducir(q)
    for v in (True, False):
        r = recuperacion.recuperar(q, plan=plan_, vector=v)
        assert r.seleccionados, f"vector={v} dejo el retrieval vacio"
        ctx, m = recuperacion.construir_contexto(r, peticion=q)
        assert m["incluidos"] > 0


def el_vector_esta_off_por_una_medicion():
    si, motivo = config.activar("vector_signal", "general")
    assert not si, f"el vector no deberia estar ON: {motivo}"
    assert "medida" in motivo, f"esta off sin medicion: {motivo}"
    assert _ganancias()["vector_signal"]["general"]["delta_mrr"] < config.UMBRAL_MRR


# ══ 5 · benchmark y produccion, mismos indices ══════════════════════════════

def benchmark_y_produccion_usan_los_mismos_indices():
    import banco_recuperacion
    m = banco_recuperacion.medir("x", vector=False, reranker=False)
    assert set(m["trozos_por_indice"]) == {n for n, _, _, _ in recuperacion.INDICES}


# ══ 6-7 · symbols y graph solo cuando corresponde ══════════════════════════

def los_simbolos_solo_cuando_el_plan_los_pide():
    assert P.deducir("¿donde se valida el JWT en este proyecto?").needs_symbols
    assert not P.deducir("que es un indice de postgresql").needs_symbols
    assert not P.deducir("como evito un race condition").needs_symbols


def el_indice_de_simbolos_se_cachea_pero_caduca():
    import pipeline, time
    # La raiz indexada tiene que ser la de PRODUCCION, no la del test: el sello del cache
    # es el mtime maximo de sus .py, asi que tocar simbolos.py solo invalida si simbolos.py
    # esta dentro de esa raiz. Con `Path(__file__).parent` el test se indexaba a si mismo.
    raiz = _RAIZ_PROD
    a = pipeline._indice_de_simbolos(raiz)
    b = pipeline._indice_de_simbolos(raiz)
    assert a is b, "el indice no se esta cacheando"
    # El touch va sobre el simbolos.py DE VERDAD. Cuando colgaba de `raiz`, mover el
    # test creaba un archivo vacio nuevo y el assert pasaba igual.
    import simbolos as _s
    Path(_s.__file__).touch()
    time.sleep(0.01)
    c = pipeline._indice_de_simbolos(raiz)
    assert c is not a, "el cache no caduca cuando cambia el codigo"


def el_grafo_esta_off_y_lo_dice():
    si, motivo = config.activar("graph_retrieval", "general")
    assert not si
    assert "sin medir" in motivo or "apagada" in motivo, motivo


# ══ 8 · la abstencion sobrevive a la calibracion ═══════════════════════════

def seguir_absteniendose_con_todo_encendido():
    """Una mejora de retrieval no puede reducir la capacidad de decir 'no lo se'."""
    fuera = [("mencionado", "implementar consenso Raft con garantias de linealizabilidad"),
             ("ausente", "streaming de video en tiempo real con WebRTC"),
             ("ausente", "entrenar un modelo de machine learning con pytorch")]
    for vector in (False, True):
        for reranker in (False, True):
            for esperado, q in fuera:
                r = recuperacion.recuperar(q, plan=P.deducir(q), vector=vector,
                                           reranker=reranker)
                v = suficiencia.evaluar(q, [(t.trozo, t.puntuacion) for t in r.seleccionados],
                                        P.deducir(q))
                assert v.grado == esperado, \
                    f"vector={vector} reranker={reranker}: {q[:34]} → {v.grado}, esperaba {esperado}"


# ══ 9-10 · las metricas son del pipeline real, y la config es reproducible ══

def las_metricas_son_del_pipeline_real():
    for etapa, entrada in _ganancias().items():
        for familia, datos in entrada.items():
            assert datos.get("sobre") == "pipeline real (fase 3)", \
                f"{etapa}/{familia} se midio sobre otra cosa: {datos.get('sobre')}"


def ninguna_etapa_esta_on_sin_evidencia():
    """La regla de la fase: nada encendido 'porque ya existe'."""
    for etapa, (si, motivo) in config.resumen().items():
        if not si:
            continue
        assert ("medida" in motivo or "nucleo" in motivo or "a mano" in motivo), \
            f"{etapa} esta ON sin justificacion: {motivo}"


def la_configuracion_final_es_reproducible():
    import subprocess
    r = subprocess.run([sys.executable, str(Path(config.__file__))], cwd=_RAIZ_PROD,
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "reranker" in r.stdout and "vector_signal" in r.stdout


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
