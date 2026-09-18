"""El enrutador de modelos: clasificacion, respaldo y honestidad sobre el coste.

    python3 test_enrutador.py
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
import config
import enrutador as E
import plan as P

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def clasifica_simple():
    clase, _ = E.clasificar("¿Que es un indice de PostgreSQL?")
    assert clase == "simple", clase


def clasifica_normal():
    clase, _ = E.clasificar("Crea un archivo calculator.py con sus tests")
    assert clase in ("normal", "complex"), clase


def clasifica_complejo():
    clase, motivo = E.clasificar("como evito un race condition al reservar una plaza")
    assert clase == "complex", f"{clase} · {motivo}"


def clasifica_arquitectura():
    clase, _ = E.clasificar("diseña la arquitectura de un sistema de pagos que escale")
    assert clase == "architectural", clase


def el_plan_sube_la_clase():
    """Una pregunta corta que cruza cuatro areas ya no es simple."""
    simple = P.deducir("que es un indice")._replace(domains=["04"])
    ancho = P.deducir("que es un indice")._replace(domains=["04", "08", "09", "10"])
    a, _ = E.clasificar("¿Que es un indice?", simple)
    b, motivo = E.clasificar("¿Que es un indice?", ancho)
    assert a == "simple" and b == "complex", f"{a} / {b} · {motivo}"


def siempre_hay_motivo():
    for texto in ("", "x", "que es esto", "diseña algo", "race condition"):
        clase, motivo = E.clasificar(texto)
        assert clase in ("simple", "normal", "complex", "architectural"), clase
        assert motivo, f"{texto!r} sin motivo"


def apagado_devuelve_el_de_siempre():
    r = E.elegir("lo que sea")
    assert r.modelo == agent.MODEL
    assert "apagado" in r.motivo, r.motivo


def encendido_a_mano_enruta():
    import importlib, os
    os.environ["MIRAG_MODEL_ROUTING"] = "on"
    importlib.reload(config)
    importlib.reload(E)
    try:
        r = E.elegir("diseña la arquitectura de un sistema de pagos")
        assert r.clase == "architectural", r.clase
        assert r.max_tokens == 16000, r.max_tokens
    finally:
        del os.environ["MIRAG_MODEL_ROUTING"]
        importlib.reload(config)
        importlib.reload(E)


def el_respaldo_entra_cuando_falla_el_principal():
    intentos_vistos = []

    def llm_falso(messages, tools):
        intentos_vistos.append(agent.MODEL)
        if len(intentos_vistos) == 1:
            raise RuntimeError("503 del proveedor")
        return {"role": "assistant", "content": "ok"}

    ruta = E.Ruta("modelo/principal", "normal", "prueba", ("modelo/respaldo",))
    msg, intentos = E.llamar([{"role": "user", "content": "x"}], ruta, llm=llm_falso)
    assert msg["content"] == "ok"
    assert len(intentos) == 2 and intentos[0]["resultado"] == "fallo", intentos
    assert intentos_vistos == ["modelo/principal", "modelo/respaldo"], intentos_vistos


def si_fallan_todos_se_dice():
    def siempre_falla(messages, tools):
        raise RuntimeError("caido")
    ruta = E.Ruta("a", "normal", "x", ("b",))
    try:
        E.llamar([], ruta, llm=siempre_falla)
        raise AssertionError("deberia haber lanzado")
    except RuntimeError as e:
        assert "todos los modelos fallaron" in str(e), str(e)


def el_modelo_global_se_restaura():
    original = agent.MODEL

    def llm_falso(messages, tools):
        return {"role": "assistant", "content": "ok"}
    E.llamar([], E.Ruta("otro/modelo", "normal", "x"), llm=llm_falso)
    assert agent.MODEL == original, f"dejo MODEL en {agent.MODEL}"


def el_candado_no_se_reintenta():
    """Si el candado offline salta, no hay que probar el siguiente modelo: no es un fallo."""
    def candado(messages, tools):
        raise agent.ModoOffline("candado")
    try:
        E.llamar([], E.Ruta("a", "normal", "x", ("b",)), llm=candado)
        raise AssertionError("deberia propagar ModoOffline")
    except agent.ModoOffline:
        pass


def el_coste_va_marcado_como_estimacion():
    r = E.Ruta(agent.MODEL, "normal", "x")
    c = r.coste_estimado()
    assert c is None or isinstance(c, float)
    assert "ESTIMACION" in E.Ruta.coste_estimado.__doc__, \
        "el coste estimado tiene que decir que es una estimacion"
    assert E.Ruta("modelo/sin/tarifa", "normal", "x").coste_estimado() is None, \
        "sin tarifa conocida hay que devolver None, no inventar un numero"


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
