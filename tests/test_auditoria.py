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
import sys

import agent
import auditoria
import dobles
import estado
import skills

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
