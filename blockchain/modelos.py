"""Lo que la capa devuelve hacia arriba. Stdlib puro: el core puede leerlo sin el SDK.

La regla que gobierna este archivo: **ningun objeto de aqui puede llevar una clave
privada**. Ni un campo, ni un default, ni un `__repr__` que la saque de algun sitio. Si
alguna vez hace falta firmar, la clave se queda en `wallet/claves.py` y aqui llega el
resultado de la firma, nunca la clave.
"""

import re
from typing import NamedTuple

# Un keypair de Stellar en texto: 56 caracteres base32. El publico empieza por G, el
# secreto por S. `SEMILLA` existe para poder AFIRMAR que un secreto no esta donde no debe.
PUBLICA = re.compile(r"\AG[A-Z2-7]{55}\Z")
SEMILLA = re.compile(r"S[A-Z2-7]{55}")
CONTRATO = re.compile(r"\AC[A-Z2-7]{55}\Z")


def es_publica(texto):
    return bool(PUBLICA.match(texto or ""))


def es_contrato(texto):
    return bool(CONTRATO.match(texto or ""))


def hay_semilla(texto):
    """¿Aparece algo con forma de clave secreta en este texto?

    Se usa como red de seguridad antes de escribir a disco, a una respuesta HTTP o a la
    pagina. Da falsos positivos posibles (56 chars base32 que no sean una clave) y eso
    esta bien: el coste de un falso positivo es una alarma, el de un falso negativo es
    publicar una clave.
    """
    return bool(SEMILLA.search(texto or ""))


class Wallet(NamedTuple):
    """La cuenta Stellar del agente. Solo lo publico."""
    agente: str
    direccion: str
    red: str
    saldo: str = ""          # en XLM, como lo da Horizon ("5.0000000"); "" = no leido
    existe: bool = False     # una cuenta sin fondear NO existe en el ledger

    def resumen(self):
        return {"agente": self.agente, "direccion": self.direccion, "red": self.red,
                "saldo": self.saldo, "existe": self.existe}


class Pago(NamedTuple):
    """Un pago entrante, tal como lo cuenta Horizon."""
    hash_tx: str
    de: str
    cantidad: str
    activo: str
    cuando: str

    def resumen(self):
        return {"hash": self.hash_tx, "de": self.de, "cantidad": self.cantidad,
                "activo": self.activo, "cuando": self.cuando}


class Identidad(NamedTuple):
    """La identidad 8004 del agente, y —lo importante— de donde sale cada dato.

    `wallet_en_cadena` es lo que devolvio `get_agent_wallet(agent_id)`. `verificada` es
    esa direccion comparada con la wallet que Mirag cree tener. Se guardan separadas a
    proposito: una cosa es lo que Mirag afirma y otra lo que la cadena dice.
    """
    agente: str
    agent_id: int | None
    registro: str                    # el contrato Identity Registry
    red: str
    wallet_en_cadena: str = ""
    uri: str = ""
    tx_registro: str = ""
    tx_wallet: str = ""
    verificada: bool = False
    motivo: str = ""                 # por que NO esta verificada, si no lo esta

    def resumen(self):
        return {"agente": self.agente, "agent_id": self.agent_id, "registro": self.registro,
                "red": self.red, "wallet_en_cadena": self.wallet_en_cadena,
                "uri": self.uri[:120], "tx_registro": self.tx_registro,
                "tx_wallet": self.tx_wallet, "verificada": self.verificada,
                "motivo": self.motivo}


class Estado(NamedTuple):
    """Lo que ve la pagina. Un solo objeto, con `disponible` siempre presente."""
    disponible: bool
    motivo: str = ""
    identidad: Identidad | None = None
    wallet: Wallet | None = None
    ultimo_pago: Pago | None = None
    enlaces: dict = {}

    def para_la_pagina(self):
        """El JSON que sale por HTTP. Lanza si detecta una semilla: mejor caer que filtrar."""
        d = {"disponible": self.disponible, "motivo": self.motivo,
             "identidad": self.identidad.resumen() if self.identidad else None,
             "wallet": self.wallet.resumen() if self.wallet else None,
             "ultimo_pago": self.ultimo_pago.resumen() if self.ultimo_pago else None,
             "enlaces": dict(self.enlaces)}
        import json
        crudo = json.dumps(d, ensure_ascii=False)
        if hay_semilla(crudo):
            raise RuntimeError(
                "hay algo con forma de clave secreta en lo que iba a salir por HTTP")
        return d


def apagada(motivo):
    return Estado(disponible=False, motivo=motivo, enlaces={})


if __name__ == "__main__":
    w = Wallet("backend", "G" + "A" * 55, "testnet", "5.0000000", True)
    e = Estado(True, "", None, w, None, {})
    print("  ", e.para_la_pagina())
    print("  es_publica:", es_publica(w.direccion), "| hay_semilla:", hay_semilla("S" + "A" * 55))
