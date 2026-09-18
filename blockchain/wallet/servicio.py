"""La wallet del agente vista desde arriba: direccion, saldo, pagos entrantes, fondeo.

Lo que este modulo NO tiene, y es lo importante: **no hay `secreto()`**. La clave se queda
en `claves.py` y solo `client.invocar` recibe el Keypair. Hay un test que comprueba que
este modulo no expone nada con ese nombre.

Tampoco hay `pagar()`, `enviar()` ni `transferir()`. La capacidad de esta fase es recibir.
"""

from .. import config
from ..modelos import Pago, Wallet
from ..stellar import client
from . import claves


def direccion():
    return claves.direccion()


def wallet(agente="backend"):
    """El estado de la cuenta ahora mismo. Una cuenta sin fondear no existe: `existe=False`."""
    d = direccion()
    if not d:
        return None
    datos = client.cuenta(d)
    return Wallet(agente=agente, direccion=d, red=config.red(),
                  saldo=client.saldo_xlm(datos), existe=datos is not None)


def pagos(limite=5):
    d = direccion()
    if not d:
        return []
    return [Pago(p["hash"], p["de"], p["cantidad"], p["activo"], p["cuando"])
            for p in client.pagos_recibidos(d, limite)]


def ultimo_pago():
    p = pagos(1)
    return p[0] if p else None


def fondear_testnet():
    """Friendbot. El candado ya garantiza que la red es testnet; Friendbot no existe en otra."""
    d = direccion()
    if not d:
        raise claves.SinClave("no hay wallet configurada que fondear")
    return client.fondear(d)
