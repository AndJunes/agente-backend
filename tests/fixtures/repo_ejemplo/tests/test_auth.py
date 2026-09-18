"""Pruebas del fixture. Sin pytest, como todo aqui: se corre solo.

    python3 pruebas/app/tests/test_auth.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # para importar auth.py

import auth   # noqa: E402

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def token_recien_emitido_vale():
    servicio = auth.AuthService()
    payload = auth.validate_token(servicio.issue_token("u1"))
    assert payload["sub"] == "u1", payload


def firma_con_otro_secreto_no_cuela():
    malo = auth.firmar({"sub": "u1", "exp": 9999999999}, b"otro-secreto")
    try:
        auth.validate_token(malo)
    except ValueError as e:
        assert "firma" in str(e), e
        return
    raise AssertionError("acepto un token firmado con otro secreto")


def token_caducado_se_rechaza():
    viejo = auth.firmar({"sub": "u1", "exp": 0})
    try:
        auth.validate_token(viejo)
    except ValueError as e:
        assert "caducado" in str(e), e
        return
    raise AssertionError("acepto un token caducado")


def basura_no_revienta_con_otra_excepcion():
    """Un token roto tiene que dar ValueError, no un IndexError cualquiera."""
    for basura in ("", "sin-puntos", "a.b.c", None):
        try:
            auth.validate_token(basura)
        except ValueError:
            continue
        raise AssertionError(f"acepto basura: {basura!r}")


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "_")) and fn.__module__ == "__main__":
            probar(nombre.replace("_", " "), fn)

    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
