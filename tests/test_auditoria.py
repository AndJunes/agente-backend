"""Que ninguna afirmacion de exito llegue sin que la ejecucion la respalde.

Los dos primeros casos son, literales, las dos pruebas que encontraron los bugs.

    python3 test_auditoria.py
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

import agent
import auditoria
import dobles
import estado
import skills

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


# ── los dos prompts que encontraron los bugs ────────────────────────────────

PROMPT_TWO_SUM = """Construye una función en Python llamada two_sum(nums, target) que reciba
una lista de enteros y un target, y devuelva los índices de los dos números que suman el target.
- Ejecuta el código realmente.
- Muéstrame el código, los tests ejecutados y la evidencia de que pasaron.
- No marques el resultado como verificado si no ejecutaste los tests realmente."""

PROMPT_DIVIDE = """Crea una función Python divide(a: float, b: float) -> float.
Debe lanzar ValueError cuando b == 0.
IMPORTANTE: NO afirmes que un test pasó si la salida de ejecución no contiene evidencia
verificable de ese test. Si no puedes obtener esos marcadores desde la ejecución real,
responde EVIDENCIA INSUFICIENTE. No uses los resultados esperados del prompt como evidencia."""


def bug_2_el_prompt_de_divide_no_secuestra_el_atajo():
    """Contiene 'salida', 'tests' y 'ejecución': antes devolvia 0 llamadas y 0 trabajo."""
    assert estado.responder(PROMPT_DIVIDE) is None, \
        "el atajo volvio a secuestrar una orden de trabajo"


def bug_1_afirmar_sin_marcadores_lleva_aviso():
    """Tests que no imprimen marcadores + prosa que dice que pasaron."""
    guion = [dobles.tool("verificar_codigo",
                         {"archivos": {"t.py": "print('Todos los tests pasaron')"},
                          "comando": "python3 t.py"}),
             dobles.texto("Perfecto. Los 3 test cases pasaron realmente.")]
    with dobles.usar(guion):
        r = agent.run(PROMPT_TWO_SUM)
    assert "NO RESPALDADA" in r["respuesta"], r["respuesta"][:200]
    assert "Los 3 test cases pasaron realmente." in r["respuesta"], \
        "el texto del modelo tiene que conservarse entero"


# ── el ejecutor ya no dice verde cuando no sabe ─────────────────────────────

def un_script_vacio_nunca_es_verde():
    r = skills.verificar_codigo({"t.py": "pass"}, "python3 t.py")
    assert skills.veredicto(r)[0] == "sin_evidencia", r[:140]
    assert "NO afirmes" in r, "el string que lee el modelo tiene que decirselo"


def marcadores_en_verde_si_son_evidencia():
    r = skills.verificar_codigo({"t.py": "print('TEST:a:PASS')\nprint('TEST:b:PASS')"},
                                "python3 t.py")
    estado_, cabecera, marcas = skills.veredicto(r)
    assert estado_ == "verde" and len(marcas) == 2, (estado_, marcas)


def un_fail_con_exit_cero_es_rojo():
    """El test roto: imprime FAIL y sale con 0. Antes pasaba por verde."""
    r = skills.verificar_codigo({"t.py": "print('TEST:a:PASS')\nprint('TEST:b:FAIL')"},
                                "python3 t.py")
    assert skills.veredicto(r)[0] == "rojo", r[:140]


def lo_que_nunca_corrio_no_es_verde():
    """Los cinco caminos de 'nunca se ejecuto'. Todos contaban como verdes en Python."""
    for archivos, comando in (({"t.py": "x"}, "bash t.py"),
                              ({}, "python3 t.py"),
                              ({"t.py": "x"}, 'python3 "sin cerrar'),
                              ({"../fuera.py": "x"}, "python3 fuera.py"),
                              ({"t.py": "while True: pass"}, "python3 t.py")):
        r = skills.verificar_codigo(archivos, comando)
        assert skills.veredicto(r)[0] == "no_ejecutado", f"{comando}: {r[:90]}"


def la_cabecera_no_se_cuenta_como_evidencia():
    """El aviso de SIN EVIDENCIA menciona TEST:<id>:PASS; no puede contarse a si mismo."""
    r = skills.verificar_codigo({"t.py": "pass"}, "python3 t.py")
    assert skills.marcas_de(r) == {}, skills.marcas_de(r)


# ── el auditor no puede ser un falso positivo ───────────────────────────────

def una_afirmacion_respaldada_no_lleva_aviso():
    aviso, estado_ = auditoria.auditar(
        "Los 2 tests pasaron.",
        ["TESTS EN VERDE · 2 de 2 marcadores\n\nTEST:a:PASS\nTEST:b:PASS"])
    assert aviso is None and estado_ == "respaldada", (aviso, estado_)


def si_el_modelo_ya_avisa_no_se_le_avisa_encima():
    aviso, _ = auditoria.auditar("EVIDENCIA INSUFICIENTE: no hay marcadores.",
                                 ["SIN EVIDENCIA: ..."])
    assert aviso is None, aviso


def afirmar_sobre_un_fail_se_contradice():
    aviso, estado_ = auditoria.auditar(
        "Todos los tests pasaron.",
        ["FALLO: 1 de 2 marcadores fallaron\n\nTEST:a:PASS\nTEST:b:FAIL"])
    assert estado_ == "refutada" and "CONTRADICHA" in aviso, (estado_, aviso)


def propiedades_declaradas_y_ninguna_demostrada():
    aviso, estado_ = auditoria.auditar(
        "Aqui tienes.", ["SIN EVIDENCIA: ..."],
        propiedades_declaradas=[{"test_id": "a"}, {"test_id": "b"}])
    assert estado_ == "sin_respaldo" and "NINGUNA PROPIEDAD" in aviso, (estado_, aviso)


def sin_ejecucion_y_sin_afirmacion_no_pasa_nada():
    aviso, estado_ = auditoria.auditar("Aqui tienes el codigo.", [])
    assert aviso is None and estado_ == "sin_afirmacion"


def el_auditor_no_revienta_con_basura():
    for texto in ("", None, "x" * 5000, "😀", "```\nTEST:a:PASS\n```"):
        for salidas in ([], None, [""], [None], ["\x00"]):
            aviso, estado_ = auditoria.auditar(texto, salidas)
            assert estado_ in ("respaldada", "sin_respaldo", "refutada",
                               "no_ejecutado", "sin_afirmacion"), estado_


# ── declarar cero propiedades ya no es el camino silencioso ─────────────────

def cero_propiedades_deja_rastro():
    import rapido
    filas = rapido._evidencia([], "TESTS EN VERDE · 1 de 1 marcadores\n\nTEST:a:PASS",
                              ejecutado=True)
    assert len(filas) == 1 and filas[0]["estado"] == "sin verificar", filas
    assert "no declaro" in filas[0]["riesgo"], filas[0]["riesgo"]


# ── la regla llega al modelo ────────────────────────────────────────────────

def al_modelo_se_le_dice_la_regla():
    assert "TEST:<id>:PASS" in agent.SYSTEM, "el system prompt no menciona los marcadores"
    desc = next(t["function"] for t in skills.TOOLS
                if t["function"]["name"] == "verificar_codigo")["description"]
    assert "TEST:<id>:PASS" in desc, "la descripcion de verificar_codigo tampoco"


# ══ La ejecucion APAGADA · que apagarla no estrene una mentira ═══════════════
#
# Estos cinco casos son el contrapeso de todos los de arriba. Arriba se comprueba que
# cuando se ejecuta, la maquina no exagera lo que vio. Aqui, que cuando NO se ejecuta, no
# finge haberlo hecho — que es la forma facil de mentir al quitar una funcion.

def _apagada(fn):
    """Corre fn() con la ejecucion apagada y devuelve lo que salga, restaurando despues."""
    previo = os.environ.get("MIRAG_EJECUCION")
    try:
        os.environ["MIRAG_EJECUCION"] = "off"
        return fn()
    finally:
        if previo is None:
            os.environ.pop("MIRAG_EJECUCION", None)
        else:
            os.environ["MIRAG_EJECUCION"] = previo


def apagada_el_veredicto_es_no_ejecutado_y_nunca_sin_evidencia():
    """El fallo que este caso impide es sutil y por eso esta escrito aparte.

    `skills.veredicto("")` NO devuelve `no_ejecutado`: cae en su fallback y devuelve
    `sin_evidencia`, que significa "corrio y no imprimio ni un marcador". Si apagar la
    ejecucion se hubiera hecho devolviendo vacio, el sistema afirmaria que hubo una
    ejecucion muda. No la hubo. Son dos cosas distintas y el usuario tiene derecho a
    distinguirlas.
    """
    salida = _apagada(lambda: skills.verificar_codigo(
        {"test_x.py": "print('TEST:a:PASS')\n"}, "python3 test_x.py"))
    estado, cabecera, marcas = skills.veredicto(salida)
    assert estado == "no_ejecutado", f"apagada deberia dar no_ejecutado y da {estado!r}"
    assert estado != "sin_evidencia", "sin_evidencia afirma una ejecucion que no ocurrio"
    assert not marcas, "no puede haber marcadores de algo que no corrio"
    assert "MIRAG_EJECUCION" in salida, "el motivo no dice como se enciende"
    # y el marcador del guion NO puede aparecer: nadie lo imprimio
    assert "TEST:a:PASS" not in salida


def apagada_no_se_ejecuta_nada_aunque_el_comando_sea_valido():
    """El guard va ANTES de tocar el disco: ni se escribe el temporal."""
    testigo = {"corrio": False}
    guion = "import pathlib; pathlib.Path('/tmp/mirag_testigo_no_debe_existir').write_text('x')"
    import pathlib
    rastro = pathlib.Path("/tmp/mirag_testigo_no_debe_existir")
    rastro.unlink(missing_ok=True)
    _apagada(lambda: skills.verificar_codigo({"test_x.py": guion}, "python3 test_x.py"))
    assert not rastro.exists(), "se ejecuto el codigo con la ejecucion apagada"
    assert not testigo["corrio"]


def apagada_ningun_bucle_de_reparacion_llama_al_modelo():
    """El bucle de arreglo se dispara con "no verde". `no_ejecutado` no es verde.

    Sin la guarda, apagar la ejecucion hacia que CADA peticion de codigo gastara una
    llamada extra al modelo para "arreglar" un fallo que nadie habia visto, mandandole
    como SALIDA REAL el texto de que no se ejecuto nada. Se paga por reparar a ciegas.
    """
    import pipeline
    fuente = _Path(pipeline.__file__).read_text()
    i = fuente.index("if not verde")
    condicion = fuente[i:fuente.index(":", i)]
    assert "no_ejecutado" in condicion, \
        f"pipeline dispara el arreglo sin mirar si hubo ejecucion: {condicion!r}"

    import rapido
    fuente_r = _Path(rapido.__file__).read_text()
    j = fuente_r.index('arreglado = False')
    assert "no_ejecutado" in fuente_r[j:j + 400], \
        "rapido dispara el arreglo aunque no se haya ejecutado nada"


def apagada_el_proyecto_queda_generado_y_no_ejecutado():
    """GENERADO es "hay archivos y nada se ha llegado a ejecutar". Ese es el estado.

    EJECUTADO seria mentira, y estaba a un paso: derivar_estado lo devuelve en cuanto
    EXISTE una fase llamada "tests", con el motivo "el comando de tests corrio y no
    imprimio un solo marcador". Por eso con la ejecucion apagada no se anota esa fase.
    """
    import verificacion_proyecto as VP
    sin_ejecucion = (VP.Fase("estructura", "ok", "", 0.0),
                     VP.Fase("sintaxis", "ok", "", 0.0),
                     VP.Fase("ejecucion", "omitido", "la ejecucion esta apagada", 0.0))
    estado, por_que = VP.derivar_estado(sin_ejecucion, {}, (), ())
    assert estado == "GENERADO", f"sin ejecucion el estado deberia ser GENERADO, es {estado}"
    assert "nada se ha llegado a ejecutar" in por_que, por_que

    # y el contraste: si alguien anotara una fase "tests", saldria EJECUTADO. Este
    # assert no valida produccion, documenta POR QUE produccion no anota esa fase.
    con_fase_tests = sin_ejecucion + (VP.Fase("tests", "limitado", "", 0.0),)
    otro, _ = VP.derivar_estado(con_fase_tests, {}, (), ())
    assert otro == "EJECUTADO", "si esto cambia, la guarda de verificacion_proyecto sobra"


def apagada_la_sintaxis_se_sigue_comprobando_sin_ejecutar():
    """Apagar la ejecucion no puede apagar el analisis estatico.

    `_comprobar_sintaxis` usaba `python3 -m py_compile` en un proceso hijo. Con la
    ejecucion apagada ese camino devolvia `no_ejecutado`, que la funcion contaba como
    rojo: marcaba SINTAXIS ROTA sobre codigo valido y el proyecto salia FALLIDO sin
    motivo. Ahora Python se analiza con ast.parse en este proceso: no ejecuta nada.
    """
    import rapido
    bueno = {"a.py": "def f():\n    return 1\n"}
    malo = {"b.py": "def f(:\n"}
    assert _apagada(lambda: rapido._comprobar_sintaxis(bueno)) is None, \
        "codigo valido reportado como sintaxis rota con la ejecucion apagada"
    fallo = _apagada(lambda: rapido._comprobar_sintaxis(malo))
    assert fallo and "b.py" in fallo, f"un error de sintaxis real deberia cazarse: {fallo!r}"
    assert "NO EJECUTADO" not in (fallo or ""), \
        "el motivo confunde 'no se ejecuto' con 'la sintaxis esta rota'"


def ningun_import_de_produccion_enciende_la_ejecucion():
    """Encender la ejecucion tiene que ser una decision, no un efecto de importar algo.

    Este caso existe porque el fallo ocurrio: `demos.py` ponia la bandera en `on` al
    importarse, y `server.py:426` hace `import dobles, demos` DENTRO del handler para
    elegir el guion del modo offline. Resultado: la PRIMERA peticion del servidor
    encendia la ejecucion de codigo generado en produccion, de forma permanente, sin que
    nadie lo hubiera pedido y sin que se notara en ningun sitio.

    No se comprueba leyendo el codigo sino en un proceso limpio, importando lo que
    importa el servidor y preguntando por el impedimento despues.
    """
    guion = (
        "import os, sys\n"
        "os.environ.pop('MIRAG_EJECUCION', None)\n"
        "import server, pipeline, dobles, demos, rapido, skills\n"
        "print('APAGADA' if skills.impedimento_de_ejecucion() else 'ENCENDIDA')\n")
    r = subprocess.run([sys.executable, "-c", guion], cwd=str(_RAIZ_REPO),
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-400:]
    assert r.stdout.strip().endswith("APAGADA"), (
        "importar los modulos de produccion dejo la ejecucion ENCENDIDA: "
        "alguien puso la bandera como efecto de import\n" + r.stdout[-300:])


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
