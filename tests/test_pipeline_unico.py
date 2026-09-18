"""Que exista UN SOLO camino de produccion, y que se pueda demostrar.

Estos tests no comprueban que "aparecio un paso de retrieval". Comparan los datos:
ids de trozos, rankings, contenido del prompt. Si vuelven a existir dos fuentes de
contexto, alguno de estos se pone rojo.

    python3 test_pipeline_unico.py
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
import hashlib
from pathlib import Path

import importlib
import os
import sys

import agent
import banco_recuperacion
import config
import dobles
import hibrido
import pipeline
import plan as P
import rag
import rapido
import recuperacion
import skills

# La ejecucion real esta APAGADA por defecto (skills.impedimento_de_ejecucion): en
# produccion este agente entrega el codigo y sus casos de test sin correrlos, y de eso se
# encarga el agente de QA. Estos casos existen para demostrar que cuando SI se ejecuta, la
# maquina no miente sobre lo que vio — asi que la encienden a proposito.
# La bandera se lee en cada llamada, no al importar, justo para permitir esto.
os.environ.setdefault("MIRAG_EJECUCION", "on")

casos = []
CONSULTA = "como evito un race condition al reservar una plaza en postgres"


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


class Espia(dobles.Doble):
    """Captura el contenido EXACTO que se le manda al modelo."""
    def __init__(self, guion, **kw):
        super().__init__(guion, **kw)
        self.contexto = None

    def __call__(self, messages, tools=None):
        if self.contexto is None:
            self.contexto = messages[-1]["content"]
        return super().__call__(messages, tools)


def _ejecutar(consulta=CONSULTA, guion=None):
    espia = Espia(list(guion or dobles.DECISION_SIMPLE))
    with dobles.usar(espia):
        e = pipeline.ejecutar(consulta, guardar=False)
    return e, espia


def _paso(e, nombre):
    return next((p for p in e.pasos if p.nombre == nombre), None)


# ══ 1 · IDENTIDAD: produccion y benchmark recuperan lo mismo ═════════════════

def produccion_y_benchmark_usan_la_misma_funcion():
    """No basta con que ambos 'hagan retrieval': tienen que dar los mismos trozos."""
    plan_ = P.deducir(CONSULTA)
    del_banco = recuperacion.recuperar(CONSULTA, plan=plan_, familia="general")
    e, _ = _ejecutar()
    de_produccion = _paso(e, "recuperacion").detalle["ids"]
    assert de_produccion == del_banco.ids(), (
        f"divergen:\n  produccion: {de_produccion[:4]}\n  banco:      {del_banco.ids()[:4]}")


def el_banco_recupera_de_los_tres_indices():
    """Medía solo TROZOS mientras produccion usaba tres. Ese era el bug original."""
    m = banco_recuperacion.medir("prueba", vector=False, reranker=False)
    conteos = m["trozos_por_indice"]
    assert set(conteos) == {"conocimiento", "antipatrones", "fallos"}, conteos
    assert all(v > 0 for v in conteos.values()), conteos


def el_banco_llama_a_la_funcion_de_produccion():
    llamadas = []
    original = recuperacion.recuperar
    recuperacion.recuperar = lambda *a, **k: (llamadas.append(1), original(*a, **k))[1]
    try:
        banco_recuperacion.medir("prueba", vector=False, reranker=False)
        assert llamadas, "el banco no pasa por recuperacion.recuperar()"
    finally:
        recuperacion.recuperar = original


# ══ 2 · EL RERANKER CAMBIA LO QUE VE EL MODELO ══════════════════════════════

def _contexto_con_reranker(encendido):
    os.environ["MIRAG_RERANKER"] = "on" if encendido else "off"
    try:
        for mod in (config, hibrido, recuperacion, pipeline):
            importlib.reload(mod)
        _, espia = _ejecutar()
        return espia.contexto or ""
    finally:
        os.environ.pop("MIRAG_RERANKER", None)
        for mod in (config, hibrido, recuperacion, pipeline):
            importlib.reload(mod)


def el_reranker_cambia_el_prompt_del_modelo():
    """LA prueba. Antes los dos SHA eran identicos: el reranker mejoraba un ranking
    que nadie leia."""
    a, b = _contexto_con_reranker(True), _contexto_con_reranker(False)
    assert a and b, "no se capturo el contexto"
    assert a != b, (
        f"el reranker NO llega al modelo: mismo SHA "
        f"{hashlib.sha256(a.encode()).hexdigest()[:16]}")


# ══ 3 · UN CHUNK SE PUEDE RASTREAR HASTA EL PROMPT ══════════════════════════

def un_chunk_seleccionado_llega_al_modelo():
    e, espia = _ejecutar()
    ids = _paso(e, "recuperacion").detalle["ids"]
    assert ids, "no se recupero nada"
    plan_ = P.deducir(CONSULTA)
    r = recuperacion.recuperar(CONSULTA, plan=plan_)
    primero = r.seleccionados[0]
    assert primero.trozo.titulo in espia.contexto, \
        f"el trozo mejor puntuado ({primero.trozo.titulo}) no esta en el prompt"


def un_chunk_descartado_no_llega_al_modelo():
    """Un trozo que el retrieval NO eligio no puede aparecer en el prompt."""
    plan_ = P.deducir(CONSULTA)
    r = recuperacion.recuperar(CONSULTA, plan=plan_)
    elegidos = {t.trozo.titulo for t in r.seleccionados}
    descartado = next((t.titulo for t in rag.TROZOS
                       if t.titulo not in elegidos and len(t.titulo) > 14), None)
    assert descartado, "no se encontro un trozo descartado con el que probar"
    _, espia = _ejecutar()
    assert descartado not in espia.contexto, \
        f"un trozo descartado ({descartado!r}) llego al prompt"


# ══ 4 · NO HAY DOBLE RETRIEVAL ══════════════════════════════════════════════

def no_hay_una_segunda_recuperacion():
    """rapido.recuperar() no puede ejecutarse en una peticion de pipeline."""
    llamadas = []
    original = rapido.recuperar
    rapido.recuperar = lambda *a, **k: (llamadas.append(1), original(*a, **k))[1]
    try:
        _ejecutar()
        assert not llamadas, \
            f"rapido.recuperar() se llamo {len(llamadas)} veces: hay un segundo retrieval"
    finally:
        rapido.recuperar = original


def el_contexto_no_lo_arma_nadie_mas():
    llamadas = []
    original = rapido._contexto
    rapido._contexto = lambda *a, **k: (llamadas.append(1), original(*a, **k))[1]
    try:
        _ejecutar()
        assert not llamadas, "rapido._contexto() sigue armando el prompt"
    finally:
        rapido._contexto = original


def la_recuperacion_ocurre_una_sola_vez():
    llamadas = []
    original = recuperacion.recuperar
    recuperacion.recuperar = lambda *a, **k: (llamadas.append(1), original(*a, **k))[1]
    try:
        _ejecutar()
        assert len(llamadas) == 1, f"se recupero {len(llamadas)} veces, deberia ser 1"
    finally:
        recuperacion.recuperar = original


# ══ 5 · LOS TRES INDICES SE PRESERVAN ═══════════════════════════════════════

def el_contexto_trae_las_tres_secciones():
    _, espia = _ejecutar()
    for etiqueta in recuperacion.ETIQUETAS.values():
        assert etiqueta in espia.contexto, f"falta la seccion {etiqueta!r}"


def la_procedencia_de_cada_trozo_se_conserva():
    r = recuperacion.recuperar(CONSULTA, plan=P.deducir(CONSULTA))
    for tr in r.seleccionados:
        assert tr.indice in ("conocimiento", "antipatrones", "fallos"), tr.indice
        assert tr.puesto >= 1 and tr.metodos, tr


def los_antipatrones_quedan_disponibles_sin_fingir_verificacion():
    """La fase de evidencia los necesitara. Hoy NO se afirma que esten cubiertos."""
    r = recuperacion.recuperar(CONSULTA, plan=P.deducir(CONSULTA))
    assert r.antipatrones, "no se preservaron los anti-patrones"
    assert all(t.indice == "antipatrones" for t in r.antipatrones)


def el_contexto_deduplica():
    r = recuperacion.recuperar(CONSULTA, plan=P.deducir(CONSULTA))
    _, medidas = recuperacion.construir_contexto(r)
    claves = {(t.trozo.caja, t.trozo.titulo) for t in r.seleccionados}
    assert medidas["incluidos"] == len(claves), \
        f"incluidos {medidas['incluidos']} vs unicos {len(claves)}"


def el_contexto_tiene_techo():
    r = recuperacion.recuperar(CONSULTA, plan=P.deducir(CONSULTA))
    ctx, medidas = recuperacion.construir_contexto(r, limite=500)
    assert len(ctx) <= 560, len(ctx)
    assert medidas["descartados"], "se recorto sin registrarlo"


# ══ 6 · LAS CAPACIDADES DE RAPIDO SIGUEN DENTRO DEL PIPELINE ════════════════

def genera_verifica_y_entrega():
    e, _ = _ejecutar("Crea calculator.py con calculate y tests", dobles.CODIGO_CALCULADORA)
    assert e.entrega, "no hubo entrega"
    assert skills.veredicto(e.salida)[0] == "verde", e.salida[:90]
    assert len([x for x in e.evidencia if x["estado"] == "verificado"]) == 3


def el_bucle_de_reparacion_sigue_vivo():
    e, _ = _ejecutar("Crea calculator.py con division por cero",
                     dobles.CODIGO_ROTO_LUEGO_ARREGLADO)
    assert any("arreglo" in p.nombre for p in e.pasos), "se perdio la reparacion"
    assert skills.veredicto(e.salida)[0] == "verde", e.salida[:90]


# ══ 7 · MODOS PUBLICOS ══════════════════════════════════════════════════════

def solo_hay_dos_modos_publicos():
    fuente = str(Path(__import__("server").__file__).resolve())
    t = open(fuente).read()
    assert 'modo == "pipeline"' in t
    assert 'modo == "arquitecto"' in t
    assert 'modo == "rapido"' not in t, "rapido sigue siendo un modo publico"
    assert 'peticion.get("modo", "pipeline")' in t, "el default no es pipeline"


def la_ui_no_ofrece_los_modos_retirados():
    t = open(str(Path(__import__("server").__file__).resolve().parent / "index.html")).read()
    assert 'value="simple"' not in t, "la UI sigue ofreciendo simple"
    assert 'value="rapido"' not in t, "la UI sigue ofreciendo rapido"
    assert 'value="pipeline"' in t and 'value="arquitecto"' in t


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and getattr(fn, "__module__", "") == "__main__" \
                and not nombre.startswith(("probar", "Espia", "_")):
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
