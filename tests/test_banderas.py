"""Cada interruptor hace lo que dice, o dice que no hace nada.

Una bandera que nadie lee es una mentira sobre lo que se puede configurar: pones
MIRAG_SEMANTIC_CACHE=on, no pasa nada, y nada te lo dice. Estos tests comprueban
`config.ESTADO_FLAGS` APAGANDO Y ENCENDIENDO cada una y mirando si algo cambia —
no leyendo el codigo fuente, que es donde empiezan estas mentiras.

    python3 test_banderas.py
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
import subprocess
import sys
from pathlib import Path

import config

AQUI = Path(__file__).parent
# La raiz de PRODUCCION, derivada de un modulo suyo: inmune a donde viva el test.
_RAIZ_PROD = Path(config.__file__).resolve().parent
casos = []

# Una sonda por bandera CONECTADA: codigo cuya salida tiene que cambiar al conmutarla.
SONDAS = {
    "RETRIEVAL_PLAN": """
import pipeline, dobles
with dobles.usar(dobles.DECISION_SIMPLE):
    e = pipeline.ejecutar('como evito un race condition al reservar una plaza', guardar=False)
print([p.detalle['origen'] for p in e.pasos if p.nombre == 'plan de busqueda'])""",
    "METADATA_ROUTING": """
import plan as P, recuperacion
q = 'como evito un race condition al reservar una plaza'
r = recuperacion.recuperar(q, plan=P.deducir(q))
print([e.candidatos for e in r.etapas if e.nombre.startswith('filtro')])""",
    "HYBRID_RETRIEVAL": """
import plan as P, recuperacion
q = 'race condition al reservar una plaza'
print(recuperacion.recuperar(q, plan=P.deducir(q)).ids()[:3])""",
    "SYMBOL_RETRIEVAL": """
import pipeline, dobles
with dobles.usar(dobles.DECISION_SIMPLE):
    e = pipeline.ejecutar('donde se valida el JWT en este proyecto', guardar=False)
print([p.estado for p in e.pasos if p.nombre == 'simbolos'])""",
    "SUFICIENCIA": """
import pipeline, dobles
with dobles.usar(dobles.DECISION_SIMPLE):
    e = pipeline.ejecutar('implementar consenso Raft', guardar=False)
print([p.resumen[:24] for p in e.pasos if p.nombre == 'suficiencia'])""",
    "VECTOR_SIGNAL": """
import plan as P, recuperacion
q = 'race condition al reservar una plaza'
r = recuperacion.recuperar(q, plan=P.deducir(q))
print([(e.nombre, e.candidatos) for e in r.etapas if 'rrf' in e.nombre])""",
    # Ojo con la consulta: hay preguntas cuyo top no reordena el reranker, y una sonda
    # asi da 'igual' y parece que la bandera no hace nada. Se mira el ranking COMPLETO y
    # ademas el 'usada' de la etapa, que es el registro de la decision.
    "RERANKER": """
import plan as P, recuperacion
q = 'como evito un race condition al reservar una plaza en postgres'
r = recuperacion.recuperar(q, plan=P.deducir(q))
print([e.usada for e in r.etapas if e.nombre.startswith('reranker')], r.ids())""",
    # El grafo ademas exige plan.needs_graph: con una consulta que no lo pide, la bandera
    # no cambia nada y la sonda mentiria. Esta si lo pide (comprobado abajo).
    "GRAPH_RETRIEVAL": """
import plan as P, pipeline, dobles
q = 'que relacion hay entre el outbox pattern y la idempotencia en pagos'
assert P.deducir(q).needs_graph, 'la sonda dejo de pedir grafo: ya no prueba nada'
with dobles.usar(dobles.DECISION_SIMPLE):
    e = pipeline.ejecutar(q, guardar=False)
print([(p.estado, p.resumen[:30]) for p in e.pasos if p.nombre == 'grafo'])""",
}


def probar(nombre, fn):
    try:
        fn(); casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _correr(codigo, flag, valor):
    env = {**os.environ, "MIRAG_" + flag: valor, "MIRAG_OFFLINE": "1"}
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True,
                       env=env, cwd=_RAIZ_PROD, timeout=300)
    assert r.returncode == 0, f"{flag}={valor} revienta: {r.stderr.strip()[-200:]}"
    return r.stdout.strip()


def _cambia(flag):
    sonda = SONDAS[flag]
    return _correr(sonda, flag, "on") != _correr(sonda, flag, "off")


def cada_conectada_cambia_algo():
    """Lo esencial: si la declaro CONECTADA, conmutarla tiene que cambiar el resultado."""
    mentirosas = [f for f, (e, _) in config.ESTADO_FLAGS.items()
                  if e == config.CONECTADO and not _cambia(f)]
    assert not mentirosas, f"declaradas CONECTADO y no hacen nada: {mentirosas}"


def toda_conectada_tiene_sonda():
    """Sin sonda no hay prueba, y sin prueba la etiqueta es una promesa."""
    conectadas = {f for f, (e, _) in config.ESTADO_FLAGS.items() if e == config.CONECTADO}
    assert conectadas <= set(SONDAS), f"sin sonda: {conectadas - set(SONDAS)}"


def lo_no_conectado_no_se_enciende_solo():
    """En 'auto' jamas: una medicion buena no basta si no esta en el camino de produccion."""
    for flag, (est, _) in config.ESTADO_FLAGS.items():
        if est == config.CONECTADO:
            continue
        si, motivo = config.activar(flag.lower())
        assert si is False, f"{flag} se enciende sola estando {est}"
        assert est.lower() in motivo, f"{flag}: el motivo no dice que esta {est}: {motivo!r}"


def lo_no_implementado_no_arranca_ni_a_mano():
    """EXPERIMENTAL = probalo si querés. NO IMPLEMENTADO = no hay nada detras."""
    for flag, (est, _) in config.ESTADO_FLAGS.items():
        if est != config.NO_IMPLEMENTADO:
            continue
        si, motivo = config.activar(flag.lower(), ganancias={})
        assert si is False, f"{flag} arranca y no hay codigo detras"


def lo_experimental_encendido_a_mano_lo_dice_en_el_motivo():
    """Sin esto la traza diria 'ON' a secas sobre algo que no esta en produccion."""
    import os
    os.environ["MIRAG_MODEL_ROUTING"] = "on"
    try:
        import importlib
        import config as c
        importlib.reload(c)
        si, motivo = c.activar("model_routing")
        assert si is True, "no se puede probar lo experimental ni queriendo"
        assert "EXPERIMENTAL" in motivo, motivo
    finally:
        del os.environ["MIRAG_MODEL_ROUTING"]
        importlib.reload(c)


def poner_una_bandera_muerta_avisa():
    avisos = config.avisos_de_banderas({"MIRAG_SEMANTIC_CACHE": "on", "MIRAG_COLBERT": "on"})
    assert len(avisos) == 2, avisos
    assert all("no hace nada" in a for a in avisos)


def una_bandera_viva_no_avisa():
    assert config.avisos_de_banderas({"MIRAG_RERANKER": "on"}) == []


def todas_las_banderas_estan_declaradas():
    """Una bandera nueva sin fila en la tabla se cuela sin que nadie la clasifique."""
    declaradas = set(config.ESTADO_FLAGS)
    reales = {n for n, v in vars(config).items()
              if n.isupper() and isinstance(v, str) and v in ("on", "off", "auto")}
    assert reales <= declaradas, f"banderas sin clasificar: {reales - declaradas}"
    assert declaradas <= reales | {"CONTEXTUAL_CHUNKS"}, \
        f"clasificadas pero inexistentes: {declaradas - reales}"


def el_estado_de_una_desconocida_es_no_implementado():
    est, motivo = config.estado_de("INVENTADA")
    assert est == config.NO_IMPLEMENTADO and "desconocida" in motivo


def apagar_suficiencia_no_finge_cobertura():
    """`suficiente=True` con la etapa apagada no puede leerse como 'el corpus lo cubre'."""
    import suficiencia
    v = suficiencia.no_evaluado("apagada a mano")
    assert v.grado == "no evaluado" and v.señales["evaluado"] is False
    assert v.frase() == "", "avisa de una cobertura que nadie evaluo"


def el_plan_vacio_dice_que_esta_vacio():
    import plan
    assert plan.VACIO.origen == "sin plan (RETRIEVAL_PLAN=off)"
    assert not plan.VACIO.domains, "un plan 'vacio' que acota cajas no esta vacio"


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
