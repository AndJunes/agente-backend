"""Respuestas fijas de Stellar, para probar sin red y sin SDK.

Mismo papel que `dobles.py` del core hace con el modelo: la suite entera tiene que poder
correr con el intérprete del sistema, sin `stellar-sdk` instalado, sin salir a internet y
en tiempo constante.

Los datos NO son inventados: son la forma exacta que devuelven Horizon y el contrato,
copiada de lecturas reales del 2026-09-16.
"""

from . import config, metadata
from .modelos import Estado, Identidad, Pago, Wallet

# Una direccion y un hash con la forma correcta. La wallet es la del agente #1 del
# registro de testnet, que existe de verdad; el resto es relleno con forma valida.
WALLET = "GDAOXABLEOFZP2M4PRM7N6YKOKXWMPFOSLU35WL5ZQY4PQFHF3VCIDS6"
PAGADOR = "GCCWEPP2MFAUF5HWICYGXDVPBVSHFQWSLQOAMNARLDQIWC2AZVGNRSQV"
TX_REGISTRO = "8f2a1c0b" + "0" * 56
TX_WALLET = "c91e4d73" + "0" * 56
TX_PAGO = "a17b93ec" + "0" * 56
AGENT_ID = 26


def estado(verificada=True, con_pago=True, saldo="10005.0000000"):
    """El estado que veria la pagina con todo funcionando."""
    registro = config.REDES[config.TESTNET]["identity_registry"]
    ident = Identidad(
        agente="backend", agent_id=AGENT_ID, registro=registro, red=config.TESTNET,
        wallet_en_cadena=WALLET if verificada else "",
        uri=metadata.uri_del_backend(WALLET),
        tx_registro=TX_REGISTRO, tx_wallet=TX_WALLET,
        verificada=verificada,
        motivo="" if verificada else "get_agent_wallet no devolvio ninguna direccion")
    wallet = Wallet("backend", WALLET, config.TESTNET, saldo, True)
    pago = Pago(TX_PAGO, PAGADOR, "5.0000000", "XLM", "2026-09-16T12:00:00Z") if con_pago else None
    return Estado(True, "", ident, wallet, pago, {
        "cuenta": f"{config.REDES[config.TESTNET]['explorador']}/account/{WALLET}",
        "registro": f"{config.REDES[config.TESTNET]['explorador']}/contract/{registro}",
        "tx": f"{config.REDES[config.TESTNET]['explorador']}/tx/{TX_PAGO}",
    })


def sin_identidad():
    """Wallet fondeada, pero todavia sin registrar en el 8004."""
    e = estado()
    return e._replace(identidad=None)


def no_verificada():
    """Lo peligroso: hay identidad, pero la cadena no confirma el vinculo.

    La pagina tiene que enseñar esto como NO verificado, no como bueno.
    """
    return estado(verificada=False, con_pago=False)
