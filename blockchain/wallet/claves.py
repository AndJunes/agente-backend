"""La clave secreta del agente. El unico archivo del repositorio que la ve.

Reglas, y lo que las hace cumplir:

    la clave no sale de aqui          `firmante()` devuelve un Keypair, nunca la cadena.
                                      No existe ninguna funcion que devuelva el secreto.
    no se imprime                     `__repr__` de este modulo no la toca; ningun print
                                      de la capa la recibe.
    no llega a la pagina              `modelos.Estado.para_la_pagina()` LANZA si detecta
                                      algo con forma de semilla en el JSON de salida.
    no se cuela en un ZIP             `empaquetado.SECRETOS` la caza.
    ningun modulo de la raiz la ve    hay un test por AST que lo comprueba.

Tres tests comprueban estas frases. Si alguna deja de ser verdad, se ponen rojos.
"""

import os

VAR_SECRETA = "STELLAR_SECRET_KEY"
VAR_PUBLICA = "STELLAR_PUBLIC_KEY"


class SinClave(RuntimeError):
    """No hay clave configurada. Es una condicion normal, no un fallo del programa."""


def hay_secreto():
    return bool(os.environ.get(VAR_SECRETA, "").strip())


def direccion():
    """La direccion publica del agente, o '' si no hay ninguna configurada.

    Se prefiere derivarla del secreto —asi no pueden desincronizarse— y se cae a
    STELLAR_PUBLIC_KEY cuando solo hay direccion, que es el caso de solo-lectura.
    """
    if hay_secreto():
        return firmante().public_key
    return os.environ.get(VAR_PUBLICA, "").strip()


def firmante():
    """El Keypair con el que se firma. Lo consume `client.invocar` y nadie mas.

    Devolver un Keypair y no una cadena es deliberado: un Keypair no se interpola en un
    f-string sin que se note, y no acaba en un log por descuido.
    """
    crudo = os.environ.get(VAR_SECRETA, "").strip()
    if not crudo:
        raise SinClave(
            f"no hay {VAR_SECRETA}. Para la demo: genera una con "
            f"`python demos/blockchain_agent_demo.py --crear` y ponla en .env")
    from stellar_sdk import Keypair                       # el SDK, solo aqui dentro
    try:
        return Keypair.from_secret(crudo)
    except Exception as e:
        # Sin el valor en el mensaje: un error que ecoa la clave la publica en los logs.
        raise SinClave(f"{VAR_SECRETA} no es una clave secreta de Stellar valida "
                       f"({type(e).__name__})") from None


def puede_firmar():
    try:
        firmante()
        return True
    except SinClave:
        return False


def generar():
    """Un keypair nuevo. Devuelve `(publica, secreta)` UNA sola vez.

    Es la UNICA funcion de todo el repositorio que devuelve un secreto, y vive aqui para
    que ese hecho sea localizable en un solo archivo. La llama la demo con `--crear`, con
    el operador delante, para que copie la clave a `.env` a mano. No se persiste, no se
    registra y no vuelve a poder leerse.
    """
    from stellar_sdk import Keypair
    kp = Keypair.random()
    return kp.public_key, kp.secret
