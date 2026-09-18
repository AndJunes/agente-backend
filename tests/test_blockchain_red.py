"""La parte de la capa que necesita `stellar-sdk`. Con dobles: sigue sin tocar la red.

    uv run --project blockchain python tests/test_blockchain_red.py

Si el SDK no está instalado, este archivo **no se disfraza de verde**: imprime `OMITIDO`
en voz alta, dice cuántos casos no se ejecutaron, y sale con 0 sólo porque la suite normal
corre a propósito en un intérprete sin el venv. La palabra `OMITIDO` es lo que hace que el
resumen de la suite lo distinga de `TODO OK`.
"""

import sys as _sys
from pathlib import Path as _Path
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
for _d in (_RAIZ_REPO, _RAIZ_REPO / "experimental", _RAIZ_REPO / "benchmarks"):
    _sys.path.insert(0, str(_d))

import os
import sys

RAIZ = _RAIZ_REPO
casos = []

try:
    import stellar_sdk                                    # noqa: F401
    HAY_SDK = True
except ImportError:
    HAY_SDK = False


def probar(nombre, fn):
    anterior = dict(os.environ)
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))
    finally:
        os.environ.clear()
        os.environ.update(anterior)


# ══ el candado, ahora con el SDK presente ════════════════════════════════════

def con_la_capa_apagada_el_cliente_no_sale_a_la_red():
    """La prueba de fuego: el SDK está, la clave está, y aun así no se llama a nadie."""
    os.environ["MIRAG_BLOCKCHAIN"] = "off"
    from blockchain.stellar import client
    for llamada in (lambda: client.cuenta("G" + "A" * 55),
                    lambda: client.pagos_recibidos("G" + "A" * 55),
                    lambda: client.fondear("G" + "A" * 55),
                    lambda: client.leer("version", fuente="G" + "A" * 55)):
        try:
            llamada()
        except RuntimeError as e:
            assert "off" in str(e), e
            continue
        raise AssertionError("una llamada salió a la red con el candado puesto")


def el_estrangulamiento_no_se_puede_esquivar():
    """Si alguien parchea `_pedir`, TODAS las rutas de red tienen que notarlo."""
    os.environ["MIRAG_BLOCKCHAIN"] = "testnet"
    from blockchain.stellar import client
    llamadas = []
    original = client._pedir
    # Un dict vacio sirve a las tres: `cuenta` lo devuelve tal cual, `pagos_recibidos`
    # lo itera (vacio) y `fondear` le hace .get(). Asi cada ruta sigue su curso entera
    # sin que ninguna toque la red.
    def espia(que, fn):
        llamadas.append(que)
        return {}
    client._pedir = espia
    try:
        client.cuenta("G" + "A" * 55)
        client.pagos_recibidos("G" + "A" * 55)
        client.fondear("G" + "A" * 55)
    finally:
        client._pedir = original
    assert len(llamadas) == 3, f"alguna ruta esquivó _pedir: {llamadas}"


def mainnet_sigue_sin_ser_alcanzable_con_el_sdk_puesto():
    os.environ["MIRAG_BLOCKCHAIN"] = "mainnet"
    from blockchain import config
    from blockchain.stellar import client
    try:
        client.cuenta("G" + "A" * 55)
    except config.RedDesconocida:
        return
    raise AssertionError("con el SDK instalado se pudo pedir mainnet")


# ══ las claves ═══════════════════════════════════════════════════════════════

def sin_clave_se_dice_y_no_se_revienta():
    os.environ.pop("STELLAR_SECRET_KEY", None)
    os.environ.pop("STELLAR_PUBLIC_KEY", None)
    from blockchain.wallet import claves
    assert not claves.hay_secreto() and claves.direccion() == ""
    assert not claves.puede_firmar()
    try:
        claves.firmante()
    except claves.SinClave as e:
        assert "STELLAR_SECRET_KEY" in str(e)
        return
    raise AssertionError("firmante() devolvió algo sin clave configurada")


def una_clave_invalida_no_se_ecoa_en_el_error():
    """Un mensaje de error que repite la clave la publica en los logs."""
    from blockchain.wallet import claves
    basura = "SBASURAQUENOESUNACLAVEVALIDAPEROSEPARECEMUCHOAUNA1234567"
    os.environ["STELLAR_SECRET_KEY"] = basura
    try:
        claves.firmante()
    except claves.SinClave as e:
        assert basura not in str(e), f"el error ecoa la clave: {e}"
        return
    raise AssertionError("una clave basura fue aceptada como válida")


def la_direccion_se_deriva_del_secreto():
    """Así no pueden desincronizarse pública y secreta."""
    from blockchain.wallet import claves
    pub, sec = claves.generar()
    os.environ["STELLAR_SECRET_KEY"] = sec
    os.environ["STELLAR_PUBLIC_KEY"] = "G" + "Z" * 55      # mentira a propósito
    assert claves.direccion() == pub, "gana la variable en vez del secreto"


def generar_da_una_clave_distinta_cada_vez():
    from blockchain.wallet import claves
    a, _ = claves.generar()
    b, _ = claves.generar()
    assert a != b and a.startswith("G") and len(a) == 56


# ══ la metadata, contra el formato real del contrato ═════════════════════════

def el_uri_que_generamos_lo_entiende_el_estandar():
    from blockchain import metadata
    u = metadata.uri_del_backend("G" + "A" * 55)
    doc = metadata.de_uri(u)
    assert doc["type"].endswith("#registration-v1")
    assert len(u) < metadata.MAXIMO_URI


# ══ el registro, sin tocar la red ════════════════════════════════════════════

def la_identidad_no_se_afirma_sin_leer_la_cadena():
    """El corazón de la fase: `verificada` sale de `get_agent_wallet`, no de la config."""
    os.environ["MIRAG_BLOCKCHAIN"] = "testnet"
    os.environ["STELLAR_AGENT_ID"] = "26"
    from blockchain.wallet import claves
    pub, sec = claves.generar()
    os.environ["STELLAR_SECRET_KEY"] = sec
    from blockchain.identity import registro

    leidas = []
    _existe, _wallet, _uri = registro.existe, registro.wallet_de, registro.uri_de
    registro.existe = lambda a: (leidas.append(("existe", a)), True)[1]
    registro.uri_de = lambda a: ""
    try:
        registro.wallet_de = lambda a: (leidas.append(("wallet", a)), pub)[1]
        i = registro.identidad()
        assert i.verificada, f"la cadena decía la misma wallet y salió sin verificar: {i.motivo}"
        assert ("wallet", 26) in leidas, "dijo 'verificada' sin llamar a get_agent_wallet"

        registro.wallet_de = lambda a: "G" + "Q" * 55      # la cadena dice otra cosa
        i = registro.identidad()
        assert not i.verificada, "la cadena decía OTRA wallet y salió verificada igual"
        assert i.motivo, "no verificada y sin decir por qué"

        registro.wallet_de = lambda a: ""                   # registrada, sin wallet
        assert not registro.identidad().verificada
    finally:
        registro.existe, registro.wallet_de, registro.uri_de = _existe, _wallet, _uri


def sin_agent_id_no_hay_identidad_pero_tampoco_error():
    os.environ["MIRAG_BLOCKCHAIN"] = "testnet"
    os.environ.pop("STELLAR_AGENT_ID", None)
    from blockchain.identity import registro
    assert registro.agent_id_configurado() is None
    assert registro.identidad() is None


def un_reset_de_testnet_se_nota_y_se_explica():
    """Si el contrato ya no conoce al agente, hay que decirlo, no enseñar la wallet sola."""
    os.environ["MIRAG_BLOCKCHAIN"] = "testnet"
    os.environ["STELLAR_AGENT_ID"] = "26"
    from blockchain.wallet import claves
    _, sec = claves.generar()
    os.environ["STELLAR_SECRET_KEY"] = sec
    from blockchain.identity import registro
    _existe = registro.existe
    registro.existe = lambda a: False
    try:
        i = registro.identidad()
        assert not i.verificada and "testnet" in i.motivo.lower()
    finally:
        registro.existe = _existe


if __name__ == "__main__":
    # Se cuenta lo que hay, no lo que yo recuerde que habia: un numero escrito a mano
    # aqui es una afirmacion que nada observa, que es justo el defecto que perseguimos.
    pruebas = [n for n, f in globals().items()
               if callable(f) and getattr(f, "__module__", "") == "__main__"
               and not n.startswith(("probar", "_"))]
    if not HAY_SDK:
        print("  OMITIDO: sin stellar-sdk en este interprete.")
        print("  Para correrlo: uv run --project blockchain python tests/test_blockchain_red.py")
        print(f"\n0 casos · OMITIDO ({len(pruebas)} sin ejecutar)")
        sys.exit(0)
    for nombre in pruebas:
        probar(nombre.replace("_", " "), globals()[nombre])
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
