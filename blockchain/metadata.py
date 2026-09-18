"""El JSON de identidad del agente, y su data URI.

La forma NO me la invente: es la que usan los agentes ya registrados en el Identity
Registry de testnet. Leida del agente #0 el 2026-09-16 (ver docs/blockchain.md). El campo
`type` es el que fija el estandar 8004.

`agent_uri` en el contrato es un STRING, y lo que la gente guarda ahi es un
`data:application/json;base64,...`: la metadata viaja EN la cadena, sin servidor que
mantener. Por eso hay un tope duro de tamaño.
"""

import base64
import json

TIPO = "https://eips.ethereum.org/EIPS/eip-8004#registration-v1"
# El data URI entra en un STRING de Soroban. 8 KB es el limite que documenta el ecosistema;
# nos quedamos muy por debajo a proposito: esta metadata describe un agente, no lo contiene.
MAXIMO_URI = 8 * 1024

BACKEND = {
    "name": "Mirag Backend Agent",
    "description": ("Agente de ingenieria backend: recupera del corpus, genera un proyecto "
                    "multiarchivo, lo ejecuta, lo prueba y lo empaqueta verificado."),
    "role": "backend",
    "version": "1.0.0",
    "capabilities": ["backend-generation", "project-generation", "code-verification"],
}


def documento(agente=None, wallet=""):
    """El JSON de registro. Sin servicios de pago: esta fase no cobra nada.

    `wallet` va tambien aqui, ademas de en su slot dedicado del contrato: el slot es la
    verdad (`get_agent_wallet`), esto es solo para que un lector humano del URI lo vea.
    """
    a = dict(agente or BACKEND)
    doc = {"type": TIPO, "name": a["name"], "description": a["description"],
           "role": a["role"], "version": a["version"], "capabilities": a["capabilities"]}
    if wallet:
        doc["agentWallet"] = wallet
    return doc


def a_uri(doc):
    """El data URI que se guarda en la cadena. Lanza si no cabe: mejor aqui que on-chain."""
    crudo = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode()
    uri = "data:application/json;base64," + base64.b64encode(crudo).decode()
    if len(uri) > MAXIMO_URI:
        raise ValueError(f"la metadata ocupa {len(uri)} y el tope es {MAXIMO_URI}")
    return uri


def de_uri(uri):
    """Deshace `a_uri`. Devuelve None si el URI no es un data URI que sepamos leer.

    Tolerante a proposito: el URI lo escribio otro (o una version anterior de esto), y
    que no se pueda leer es informacion, no una excepcion.
    """
    marca = "data:application/json;base64,"
    if not (uri or "").startswith(marca):
        return None
    try:
        return json.loads(base64.b64decode(uri[len(marca):]))
    except (ValueError, TypeError):
        return None


def uri_del_backend(wallet=""):
    return a_uri(documento(BACKEND, wallet))


if __name__ == "__main__":
    u = uri_del_backend("G" + "A" * 55)
    print(f"  uri: {len(u)} bytes de {MAXIMO_URI}")
    print(f"  {u[:90]}...")
    print(f"  ida y vuelta: {de_uri(u) == documento(BACKEND, 'G' + 'A' * 55)}")
