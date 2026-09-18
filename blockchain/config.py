"""El candado de la capa, y las redes que este codigo sabe nombrar.

Stdlib puro a proposito: este modulo lo importa la fachada antes de saber si `stellar_sdk`
existe siquiera, y tiene que poder decir "la capa esta apagada" sin tocar el paquete.

`agent.OFFLINE` NO sirve aqui. Ese candado es un `if` dentro de `agent.llm()`: cubre el
modelo y los embeddings, no la red en general (`fixture_proyecto` y `sondas` ya abren
sockets sin pasar por el). Asi que la capa lleva el suyo, con la misma forma que
`vectores._impedimento()`, que es el patron que ya funciona en este repo.
"""

import os

# ── las redes que existen ────────────────────────────────────────────────────
# Mainnet no esta, y no es un olvido: mientras no este aqui, ninguna ruta de este
# codigo puede alcanzarla ni por accidente ni por una variable de entorno mal escrita.
TESTNET = "testnet"

REDES = {
    TESTNET: {
        "horizon": "https://horizon-testnet.stellar.org",
        "rpc": "https://soroban-testnet.stellar.org",
        "passphrase": "Test SDF Network ; September 2015",
        "friendbot": "https://friendbot.stellar.org",
        "explorador": "https://stellar.expert/explorer/testnet",
        # Identity Registry de Stellar 8004. Leido y verificado el 2026-09-16:
        # version() = "0.1.0", total_agents() = 26. Ver docs/blockchain.md.
        "identity_registry": "CDE3K4COIAGWNNJQQLL26SYI3KBJF5FUDHXG5FA6GYDJCG7T5V7FIWZH",
    },
}

APAGADA = "off"


class RedDesconocida(RuntimeError):
    """MIRAG_BLOCKCHAIN dice una red que este codigo no sabe nombrar.

    Lanza en vez de caer a un defecto: un defecto silencioso es exactamente como se
    acaba hablando con mainnet sin querer.
    """


def red():
    """La red configurada ahora mismo. Se lee cada vez, no al importar.

    Los tests cambian la variable entre casos, igual que hacen con `agent.OFFLINE`.
    """
    return os.environ.get("MIRAG_BLOCKCHAIN", APAGADA).strip().lower()


def impedimento():
    """Motivo por el que NO se puede hablar con Stellar ahora mismo, o '' si se puede."""
    r = red()
    if r in ("", APAGADA):
        return "MIRAG_BLOCKCHAIN esta en off: no se habla con Stellar"
    if r not in REDES:
        raise RedDesconocida(
            f"MIRAG_BLOCKCHAIN={r!r} no es una red que este codigo conozca. "
            f"Conocidas: {sorted(REDES)}. Mainnet no esta y es a proposito.")
    return ""


def disponible():
    return not impedimento()


def ajustes():
    """Los datos de la red activa. Lanza si no hay ninguna: nunca devuelve un defecto."""
    if motivo := impedimento():
        raise RuntimeError(motivo)
    return dict(REDES[red()])


def enlace_cuenta(direccion):
    return f"{ajustes()['explorador']}/account/{direccion}"


def enlace_tx(hash_tx):
    return f"{ajustes()['explorador']}/tx/{hash_tx}"


def enlace_contrato(contrato):
    return f"{ajustes()['explorador']}/contract/{contrato}"


if __name__ == "__main__":
    print(f"  red        {red()}")
    print(f"  impedimento {impedimento() or '(ninguno)'}")
    if disponible():
        for k, v in ajustes().items():
            print(f"  {k:18} {v}")
