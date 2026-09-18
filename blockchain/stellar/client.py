"""El unico sitio de la capa donde se abre un socket, y el unico que importa stellar_sdk.

Lleva el candado aunque quien llama ya lo haya comprobado, por la misma razon que lo lleva
`vectores._pedir`: este es el UNICO punto donde se sale a la red, y una ruta nueva que
llegue aqui sin pasar por los otros hablaria con Stellar en silencio.

La regla exacta —y la que comprueba un test por AST— es sobre el SOCKET, no sobre el
paquete: ningun otro `.py` de blockchain/ puede nombrar `Server`, `SorobanServer`,
`ContractClient`, `urlopen` ni `requests`. `wallet/claves.py` si importa `Keypair`, que es
criptografia pura y no abre nada; esa es la unica excepcion y esta declarada en el test.
"""

import json
import urllib.parse
import urllib.request

from stellar_sdk import Keypair, Network, Server, SorobanServer, scval
from stellar_sdk.contract import ContractClient
from stellar_sdk.exceptions import NotFoundError

from .. import config

TIEMPO = 20          # una demo que se cuelga 5 minutos no sirve para enseñar nada
COMISION = 1_000_000  # 0.1 XLM de techo: Soroban cobra por recursos, no por operacion
AGENTE_HTTP = "Mirag/1.0 (+stdlib urllib)"


def _pedir(que, fn):
    """Toda salida a la red pasa por aqui. Sin excepciones."""
    if motivo := config.impedimento():
        raise RuntimeError(f"{que}: {motivo}")
    return fn()


def _ajustes():
    return config.ajustes()


def horizon():
    return Server(horizon_url=_ajustes()["horizon"])


def soroban():
    return SorobanServer(_ajustes()["rpc"])


def passphrase():
    return _ajustes()["passphrase"]


# ── cuentas ──────────────────────────────────────────────────────────────────

def cuenta(direccion):
    """Los datos de la cuenta, o None si no existe todavia en el ledger.

    En Stellar una cuenta sin fondear NO existe: no es un saldo de cero, es un 404. La
    diferencia importa para la pagina, asi que se devuelve None y no un saldo falso.
    """
    def ir():
        try:
            return horizon().accounts().account_id(direccion).call()
        except NotFoundError:
            return None
    return _pedir("leer la cuenta", ir)


def saldo_xlm(datos_cuenta):
    for b in (datos_cuenta or {}).get("balances", []):
        if b.get("asset_type") == "native":
            return b.get("balance", "")
    return ""


def pagos_recibidos(direccion, limite=5):
    """Los pagos ENTRANTES mas recientes. Los salientes y las creaciones se descartan."""
    def ir():
        r = horizon().payments().for_account(direccion).order(desc=True) \
                     .limit(min(limite * 4, 50)).call()
        return r.get("_embedded", {}).get("records", [])
    filas = []
    for p in _pedir("leer los pagos", ir):
        if p.get("type") not in ("payment", "create_account"):
            continue
        destino = p.get("to") or p.get("account")
        if destino != direccion:
            continue
        filas.append({
            "hash": p.get("transaction_hash", ""),
            "de": p.get("from") or p.get("funder", ""),
            "cantidad": p.get("amount") or p.get("starting_balance", ""),
            "activo": "XLM" if p.get("asset_type", "native") == "native"
                      else p.get("asset_code", "?"),
            "cuando": p.get("created_at", ""),
        })
        if len(filas) >= limite:
            break
    return filas


def fondear(direccion):
    """Friendbot. Solo existe en testnet, y el candado ya garantiza que estamos ahi."""
    def ir():
        url = _ajustes()["friendbot"] + "?" + urllib.parse.urlencode({"addr": direccion})
        # Friendbot devuelve 403 al User-Agent por defecto de urllib ("Python-urllib/3.x"):
        # hay un filtro delante que lo toma por un bot. Comprobado: el mismo GET con curl
        # da 200 y con urllib sin cabecera da 403.
        peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE_HTTP})
        with urllib.request.urlopen(peticion, timeout=TIEMPO) as r:
            return json.loads(r.read())
    respuesta = _pedir("fondear con friendbot", ir)
    return respuesta.get("hash") or respuesta.get("id", "")


# ── contrato ─────────────────────────────────────────────────────────────────

def _cliente():
    a = _ajustes()
    return ContractClient(a["identity_registry"], a["rpc"], a["passphrase"])


def leer(funcion, *args, fuente, parse=None):
    """Una lectura del contrato: simulate, sin firmar, sin enviar, sin coste.

    `fuente` es una direccion que exista en el ledger; se usa solo como origen de la
    simulacion y no firma nada.
    """
    def ir():
        return _cliente().invoke(funcion, list(args), parse_result_xdr_fn=parse,
                                 source=fuente).result()
    return _pedir(f"leer {funcion}()", ir)


def invocar(funcion, *args, firmante, parse=None):
    """Una escritura: se firma y se envia. Devuelve `(resultado, hash_de_la_transaccion)`.

    `firmante` es un Keypair. Es el unico sitio de todo el repo donde se firma algo, y la
    clave llega ya construida desde wallet/claves.py: aqui no se lee ninguna variable de
    entorno ni se toca ningun archivo.

    El hash NO lo devuelve `sign_and_submit` —que devuelve el valor de retorno de la
    funcion del contrato— sino que queda en `send_transaction_response`. Sin el hash no
    hay nada que enseñar en el explorador, asi que se saca explicitamente.
    """
    def ir():
        tx = _cliente().invoke(funcion, list(args), source=firmante.public_key,
                               signer=firmante, base_fee=COMISION,
                               parse_result_xdr_fn=parse)
        resultado = tx.sign_and_submit()
        envio = tx.send_transaction_response
        return resultado, (getattr(envio, "hash", "") if envio else "")
    return _pedir(f"invocar {funcion}()", ir)


__all__ = ["cuenta", "saldo_xlm", "pagos_recibidos", "fondear", "leer", "invocar",
           "Keypair", "Network", "scval", "passphrase"]
