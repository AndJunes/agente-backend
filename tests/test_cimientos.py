"""Los cimientos: el candado de gasto, los interruptores y los cuatro bugs de la Fase 0.

Todo gratis y sin red. Si alguno de estos se pone rojo, cualquier medicion hecha
encima deja de valer, asi que corre esto antes que nada:

    python3 test_cimientos.py
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
import subprocess
import sys
import tempfile
from pathlib import Path

import agent
import config
import rag
import skills
import traza

AQUI = Path(__file__).parent
# La raiz de PRODUCCION, derivada de un modulo suyo: inmune a donde viva el test.
_RAIZ_PROD = Path(traza.__file__).resolve().parent
# Las rutas que apuntan a PRODUCCION se derivan de un modulo de produccion, nunca de
# __file__: asi siguen apuntando al sitio correcto viva donde viva este test. Cuando
# colgaban de `AQUI`, mover el test a tests/ los dejaba mirando una carpeta vacia y
# el test pasaba sin comprobar nada.
RAIZ = Path(traza.__file__).resolve().parent
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
    except Exception as e:                      # un error inesperado tambien es un fallo
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


# ── el candado de gasto ──────────────────────────────────────────────────────

def candado_muerde():
    """Con el candado puesto, llamar al modelo TIENE que fallar, no cobrar."""
    assert agent.OFFLINE, "el default debe ser offline: MIRAG_OFFLINE sin poner = candado puesto"
    try:
        agent.llm([{"role": "user", "content": "hola"}])
    except agent.ModoOffline:
        return
    raise AssertionError("la llamada atraveso el candado")


def candado_antes_del_presupuesto():
    """El candado va ANTES de tocar el presupuesto: ni siquiera cuenta la llamada."""
    antes = agent.PRESUPUESTO.llamadas
    try:
        agent.llm([{"role": "user", "content": "hola"}])
    except agent.ModoOffline:
        pass
    assert agent.PRESUPUESTO.llamadas == antes, "conto una llamada que nunca ocurrio"


def se_puede_abrir_a_proposito():
    r = subprocess.run([sys.executable, "-c", "import agent; print(agent.OFFLINE)"],
                       cwd=_RAIZ_PROD, capture_output=True, text=True,
                       env={**os.environ, "MIRAG_OFFLINE": "0"})
    assert r.stdout.strip() == "False", f"MIRAG_OFFLINE=0 no abre el candado: {r.stdout!r}"


def importa_sin_env():
    """Maquina limpia: sin .env el proyecto tiene que importarse igual."""
    codigo = "import agent, rag, skills, estado, traza, config; print(len(rag.TROZOS))"
    with tempfile.TemporaryDirectory() as tmp:
        env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
        env["HOME"] = tmp
        # `cwd` tiene que ser la RAIZ: estos subprocesos hacen `import <produccion>` y desde
        # tests/ no encontrarian nada. Cuando fallan, avisan de que la reorganizacion rompio
        # la importabilidad — son la red de seguridad, no un detalle.
        r = subprocess.run([sys.executable, "-c", codigo], cwd=_RAIZ_PROD,
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0, f"no importa sin clave: {r.stderr[-300:]}"


# ── los interruptores y la compuerta ─────────────────────────────────────────

def sin_medir_nace_apagada():
    si, motivo = config.activar("reranker", "general", ganancias={})
    assert not si, "una etapa sin medir no puede nacer encendida"
    assert "sin medir" in motivo, motivo


def medida_floja_no_pasa():
    tabla = {"reranker": {"general": {"delta_mrr": 0.005, "coste_normalizado": 0.0}}}
    si, motivo = config.activar("reranker", "general", ganancias=tabla)
    assert not si, "una mejora por debajo del umbral no deberia encender nada"
    assert "umbral" in motivo, motivo


def medida_cara_no_compensa():
    tabla = {"reranker": {"general": {"delta_mrr": 0.05, "coste_normalizado": 0.9}}}
    si, motivo = config.activar("reranker", "general", ganancias=tabla)
    assert not si, "si cuesta mas de lo que gana, no se enciende"
    assert "no compensa" in motivo, motivo


def medida_buena_enciende():
    tabla = {"reranker": {"general": {"delta_mrr": 0.08, "coste_normalizado": 0.01}}}
    si, motivo = config.activar("reranker", "general", ganancias=tabla)
    assert si, f"una mejora medida y barata deberia encenderse: {motivo}"


def el_motivo_siempre_existe():
    """La UI tiene que poder explicar por que NO se uso una etapa."""
    for etapa, (_, motivo) in config.resumen().items():
        assert motivo and len(motivo) > 8, f"{etapa} sin motivo legible: {motivo!r}"


# ── bug 1 · el brazo baseline del banco ──────────────────────────────────────

def los_dos_brazos_del_banco_corren_de_verdad():
    """De comportamiento, no de texto.

    La version anterior comprobaba que el string 'lambda *a, **kw: []' estuviera en
    banco.py. Eso fijaba una implementacion, no un comportamiento: cuando el banco se
    migro al pipeline, el test fallo sin que nada estuviera roto. Ahora se EJECUTAN los
    dos brazos con un doble y se comprueba que producen trazas distinguibles.
    """
    import banco, dobles, traza
    destino = traza.ARCHIVO.parent / "trazas_noche.jsonl"
    antes = len(traza.leer(destino))
    for brazo in ("baseline", "v2"):
        with dobles.usar(list(dobles.CODIGO_CALCULADORA) * 3):
            banco.correr(brazo, tareas=banco.TAREAS[:1])
    filas = traza.leer(destino)[antes:]
    assert len(filas) == 2, f"esperaba una traza por brazo, hay {len(filas)}"
    # La etiqueta lleva prefijo desde la Fase 7: `traza.VERSION` vale "v1.1" y el brazo se
    # llamaba igual, asi que las consultas normales del usuario se colaban en el brazo.
    assert {f["version"] for f in filas} == {"banco:baseline", "banco:v2"}, \
        [f["version"] for f in filas]
    assert all(banco._del_banco(f) for f in filas), "el filtro del banco no reconoce sus tareas"
    # el brazo baseline no acota por cajas; el otro si
    base = next(f for f in filas if f["version"] == "banco:baseline")
    assert base["cajas"] == [], f"el brazo baseline no deberia acotar: {base['cajas']}"


def el_banco_no_escribe_en_la_carpeta_de_produccion():
    """Diez ejecuciones sobre salida/ se llevan por delante la ultima entrega del usuario,
    y ademas dejan solo la ultima de las diez. Ya paso una vez."""
    import banco, dobles
    salida = RAIZ / "salida"
    salida.mkdir(exist_ok=True)
    marca = salida / "MARCA_BANCO.txt"
    marca.write_text("entrega del usuario")
    try:
        with dobles.usar(list(dobles.CODIGO_CALCULADORA) * 3):
            banco.correr("seco", tareas=banco.TAREAS[:1])
        assert marca.exists() and marca.read_text() == "entrega del usuario", \
            "el banco piso la carpeta de produccion"
    finally:
        marca.unlink(missing_ok=True)


def la_etiqueta_del_banco_no_colisiona_con_la_version_por_defecto():
    """Dos cosas distintas con el mismo nombre en el mismo fichero acaban comparandose."""
    import banco, traza
    assert not traza.VERSION.startswith("banco:"), traza.VERSION
    normal = {"tarea": "que es un indice de postgres", "version": traza.VERSION}
    assert not banco._del_banco(normal), "una consulta normal entra en el brazo del banco"
    del_banco = {"tarea": banco.TAREAS[0][1][:120], "version": "banco:v2"}
    assert banco._del_banco(del_banco), "una tarea del banco no se reconoce"


# ── bug 2 · la evidencia en simulacion ───────────────────────────────────────

def simulacion_no_desaparece():
    cuenta, exito, sim = traza.resumen([{"estado": "verificado en simulación"}] * 10)
    assert cuenta["verificado en simulación"] == 10, cuenta
    assert exito == 0.0, "demostrado contra una simulacion NO es demostrado"
    assert sim == 1.0, "pero tampoco es cero: tiene que verse aparte"


def evidencia_normal_sigue_igual():
    cuenta, exito, sim = traza.resumen(
        [{"estado": "verificado"}] * 3 + [{"estado": "refutado"}])
    assert exito == 0.75, exito
    assert sim == 0.0, sim


def estado_desconocido_no_revienta():
    cuenta, exito, _ = traza.resumen([{"estado": "algo que nadie previo"}])
    assert cuenta.get("algo que nadie previo") == 1, cuenta


# ── bug 3 · los trozos fantasma de la plantilla ADR ──────────────────────────

def sin_trozos_fantasma():
    fantasmas = [t.titulo for t in rag.TROZOS
                 if t.titulo in ("Estado", "Contexto", "Opciones consideradas", "Consecuencias")]
    assert not fantasmas, f"la plantilla ADR sigue colandose como secciones: {fantasmas}"


def la_ficha_del_adr_vuelve():
    adr = [t for t in rag.FICHAS if "ADR" in t.titulo]
    assert adr, "la seccion de ADRs sigue sin su ficha"


def el_corpus_no_se_rompio():
    assert len(rag.TROZOS) == 247, f"trozos esperados 247, hay {len(rag.TROZOS)}"
    assert len(rag.FICHAS) == 228, len(rag.FICHAS)
    assert len({t.caja for t in rag.TROZOS}) == 19
    assert all(t.texto.strip() for t in rag.TROZOS), "hay trozos vacios"


def las_busquedas_siguen_funcionando():
    """La API publica la usan rapido, skills, arquitecto y eval: romperla es regresion."""
    for fn, arg in ((rag.buscar, "indices"), (rag.buscar_fallos, "transacciones"),
                    (rag.buscar_tradeoffs, "cache"), (rag.buscar_antipatrones, "locks")):
        r = fn(arg)
        assert isinstance(r, str) and r.strip(), f"{fn.__name__} devolvio vacio"


# ── bug 4 · la allowlist mentia sobre esta maquina ───────────────────────────

def solo_interpretes_que_existen():
    import shutil
    for i in skills.INTERPRETES:
        assert shutil.which(i), f"{i} esta en la allowlist y no existe en esta maquina"


def la_descripcion_dice_la_verdad():
    """Lo que el modelo lee tiene que coincidir con lo que se puede ejecutar."""
    desc = next(t["function"] for t in skills.TOOLS
                if t["function"]["name"] == "verificar_codigo")["description"]
    for i in sorted(skills.INTERPRETES):
        assert i in desc, f"{i} se puede ejecutar pero no se le dice al modelo"
    assert "pytest" not in desc or "pytest" in skills.INTERPRETES, \
        "se le sigue recomendando al modelo un interprete que no esta instalado"


def ejecutar_de_verdad_sigue_dando_evidencia():
    r = skills.verificar_codigo({"t.py": "print('TEST:uno:PASS')"}, "python3 t.py")
    assert skills.veredicto(r)[0] == "verde", r[:120]
    assert "TEST:uno:PASS" in r


def comando_no_permitido_se_rechaza():
    r = skills.verificar_codigo({"t.py": "print(1)"}, "bash t.py")
    assert skills.veredicto(r)[0] == "no_ejecutado", r[:120]


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "_")) and fn.__module__ == "__main__":
            if nombre not in ("main",):
                probar(nombre.replace("_", " "), fn)

    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
