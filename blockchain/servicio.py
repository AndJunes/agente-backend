"""Junta identidad y wallet en el `Estado` que ve la pagina.

Importar este modulo importa `stellar_sdk`. Por eso la fachada (`blockchain/__init__.py`)
lo importa DENTRO de `estado()` y no arriba: asi `import blockchain` sigue funcionando en
una maquina sin el paquete, que es lo que hace que las 21 suites del core no necesiten el
venv.
"""

from . import config
from .identity import registro
from .modelos import Estado
from .wallet import claves, servicio as wallet_servicio


def leer_estado(agente="backend"):
    """Todo lo que se puede saber ahora mismo. Lo que no se sabe se dice, no se rellena."""
    ajustes = config.ajustes()
    explorador = ajustes["explorador"]

    if not claves.direccion():
        return Estado(disponible=False,
                      motivo=(f"la capa esta encendida pero no hay wallet: falta "
                              f"{claves.VAR_SECRETA} (o {claves.VAR_PUBLICA}) en .env"),
                      enlaces={"registro": f"{explorador}/contract/"
                                           f"{ajustes['identity_registry']}"})

    w = wallet_servicio.wallet(agente)
    pago = wallet_servicio.ultimo_pago() if (w and w.existe) else None

    try:
        ident = registro.identidad(agente)
    except Exception as e:
        # Un reset de testnet, el contrato caido, el RPC sin responder. Se dice el motivo
        # en vez de enseñar la wallet como si la identidad estuviera bien.
        ident = None
        motivo_ident = f"no se pudo leer el registro 8004: {type(e).__name__}: {e}"
    else:
        motivo_ident = ""

    enlaces = {"cuenta": f"{explorador}/account/{w.direccion}" if w else "",
               "registro": f"{explorador}/contract/{ajustes['identity_registry']}",
               "tx": f"{explorador}/tx/{pago.hash_tx}" if pago else ""}

    return Estado(disponible=True, motivo=motivo_ident, identidad=ident, wallet=w,
                  ultimo_pago=pago, enlaces={k: v for k, v in enlaces.items() if v})
