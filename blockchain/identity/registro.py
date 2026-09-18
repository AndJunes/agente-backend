"""La identidad 8004 del agente: registrarla, leerla y —lo que importa— verificarla.

La ABI de abajo se leyo del WASM desplegado en testnet, no de documentacion. Lo que dice
la web publica estaba mal en un punto concreto: `register(caller)` **no** lleva
`metadata_uri`. Para registrar con metadata hay que usar `register_with_uri`. Ver
docs/blockchain.md.

    register_with_uri(caller: ADDRESS, agent_uri: STRING)  -> U32
    set_agent_wallet(caller, agent_id: U32, new_wallet)    -> Result<VOID, IdentityError>
    get_agent_wallet(agent_id: U32)                        -> Option<ADDRESS>
    agent_uri(agent_id: U32)                               -> Result<STRING, IdentityError>
    agent_exists(agent_id: U32)                            -> BOOL
    total_agents()                                         -> U32

**El vinculo identidad↔wallet no se afirma: se lee de vuelta.** `verificar()` llama a
`get_agent_wallet` y compara con la wallet que Mirag cree tener. Esa comparacion es toda
la diferencia entre "lo registre" y "esta registrado".
"""

from .. import config, metadata
from ..modelos import Identidad
from ..stellar import client
from ..wallet import claves

VAR_AGENT_ID = "STELLAR_AGENT_ID"
# Los hashes del registro no se pueden recalcular: o se guardan cuando ocurren, o se
# pierden. El agent_id si se podria buscar recorriendo el contrato, pero cuesta una
# lectura por agente; guardarlo es mas barato y ademas deja claro que es una AFIRMACION
# de Mirag que luego `identidad()` contrasta contra la cadena.
VAR_TX_REGISTRO = "STELLAR_TX_REGISTRO"
VAR_TX_WALLET = "STELLAR_TX_WALLET"


def _registro():
    return config.ajustes()["identity_registry"]


def agent_id_configurado():
    """El id que Mirag cree tener. Es una afirmacion, no una verificacion."""
    import os
    crudo = os.environ.get(VAR_AGENT_ID, "").strip()
    return int(crudo) if crudo.isdigit() else None


# ── lecturas ─────────────────────────────────────────────────────────────────

def _fuente():
    """Una direccion existente para originar las simulaciones. No firma nada."""
    d = claves.direccion()
    if not d:
        raise claves.SinClave("no hay direccion con la que simular una lectura")
    return d


def total():
    return client.leer("total_agents", fuente=_fuente(),
                       parse=client.scval.from_uint32)


def existe(agent_id):
    return client.leer("agent_exists", client.scval.to_uint32(agent_id),
                       fuente=_fuente(), parse=client.scval.from_bool)


def wallet_de(agent_id):
    """`get_agent_wallet(agent_id)` -> la direccion, o '' si el slot esta vacio."""
    v = client.leer("get_agent_wallet", client.scval.to_uint32(agent_id), fuente=_fuente())
    if v is None:
        return ""
    try:
        return client.scval.from_address(v).address
    except Exception:
        return ""          # SCV_VOID: registrado, pero sin wallet asociada


def uri_de(agent_id):
    try:
        v = client.leer("agent_uri", client.scval.to_uint32(agent_id), fuente=_fuente())
        return client.scval.from_string(v).decode() if v is not None else ""
    except Exception:
        return ""          # UriNotSet, o el agente no existe


# ── escrituras ───────────────────────────────────────────────────────────────

def registrar(wallet=""):
    """`register_with_uri`. Devuelve `(agent_id, hash_tx)`.

    El caller es el mismo keypair que sera la wallet: `set_agent_wallet` exige
    autorizacion del owner Y de la wallet, y con un solo keypair basta una firma. Es una
    decision, anotada en docs/blockchain.md, no un accidente.
    """
    kp = claves.firmante()
    uri = metadata.uri_del_backend(wallet or kp.public_key)
    agent_id, hash_tx = client.invocar(
        "register_with_uri",
        client.scval.to_address(kp.public_key),
        client.scval.to_string(uri),
        firmante=kp, parse=client.scval.from_uint32)
    return agent_id, hash_tx


def asociar_wallet(agent_id, wallet=""):
    """`set_agent_wallet`. Devuelve el hash. No comprueba nada: eso lo hace `verificar`."""
    kp = claves.firmante()
    _, hash_tx = client.invocar(
        "set_agent_wallet",
        client.scval.to_address(kp.public_key),
        client.scval.to_uint32(agent_id),
        client.scval.to_address(wallet or kp.public_key),
        firmante=kp)
    return hash_tx


# ── lo que ve la pagina ──────────────────────────────────────────────────────

def identidad(agente="backend", tx_registro=None, tx_wallet=None):
    """La identidad leida de la cadena, con `verificada` calculada, no afirmada.

    Devuelve None si no hay ningun agent_id configurado: eso no es un error, es que el
    agente todavia no se registro.
    """
    import os
    aid = agent_id_configurado()
    if aid is None:
        return None
    if tx_registro is None:
        tx_registro = os.environ.get(VAR_TX_REGISTRO, "").strip()
    if tx_wallet is None:
        tx_wallet = os.environ.get(VAR_TX_WALLET, "").strip()
    base = Identidad(agente=agente, agent_id=aid, registro=_registro(), red=config.red(),
                     tx_registro=tx_registro, tx_wallet=tx_wallet)
    mia = claves.direccion()
    if not existe(aid):
        return base._replace(motivo=f"el registro no conoce ningun agente #{aid}. "
                                    f"¿Se reseteo testnet?")
    en_cadena = wallet_de(aid)
    base = base._replace(wallet_en_cadena=en_cadena, uri=uri_de(aid))
    if not en_cadena:
        return base._replace(motivo=f"el agente #{aid} existe pero no tiene wallet asociada")
    if en_cadena != mia:
        return base._replace(motivo=f"la cadena dice que la wallet de #{aid} es "
                                    f"{en_cadena[:8]}… y Mirag usa {mia[:8]}…")
    return base._replace(verificada=True)
