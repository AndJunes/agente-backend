"""La fachada: lo unico que el core de Mirag conoce de esta capa.

    server.py  ──importa perezosamente──▶  blockchain.estado()  ──▶  Estado

Dos reglas que este archivo existe para cumplir:

1. **Importar esto NO importa `stellar_sdk`.** Solo `config`, `modelos`, `metadata` y
   `dobles`, que son stdlib puro. El SDK entra cuando —y solo cuando— alguien pide hablar
   con la red de verdad. Por eso `python3 -c "import server"` sigue funcionando con el
   intérprete del sistema y sin el paquete instalado, y por eso las 21 suites del core no
   necesitan el venv.

2. **Nunca lanza hacia arriba.** Si la capa esta apagada, si falta el SDK, si la red no
   contesta o si el contrato ya no existe tras un reset de testnet, se devuelve un
   `Estado(disponible=False, motivo=...)`. El servidor no se cae por esto y la pagina
   tiene algo honesto que enseñar.
"""

from . import config, dobles, metadata, modelos
from .config import RedDesconocida
from .modelos import Estado, Identidad, Pago, Wallet

__all__ = ["estado", "disponible", "config", "metadata", "modelos", "dobles",
           "Estado", "Identidad", "Pago", "Wallet", "RedDesconocida"]

AGENTE = "backend"


def disponible():
    """¿Se puede hablar con Stellar ahora mismo? No lanza nunca."""
    try:
        return config.disponible()
    except RedDesconocida:
        return False


def estado(agente=AGENTE, simular=None):
    """Todo lo que la pagina necesita saber, en un objeto.

    `simular=True` fuerza los dobles. Con `None` se decide por el candado: si la capa esta
    apagada no hay nada real que leer, asi que tampoco se simula — se dice que esta
    apagada. Un doble que se enciende solo seria la UI mintiendo.
    """
    if simular:
        return dobles.estado()
    try:
        motivo = config.impedimento()
    except RedDesconocida as e:
        return modelos.apagada(str(e))
    if motivo:
        return modelos.apagada(motivo)
    try:
        from .servicio import leer_estado          # aqui, y solo aqui, entra el SDK
    except ImportError as e:
        return modelos.apagada(
            f"la capa esta encendida pero falta su dependencia: {e}. "
            f"Instalala con: uv sync --project blockchain")
    try:
        return leer_estado(agente)
    except Exception as e:                          # la red, el contrato, un reset de testnet
        return modelos.apagada(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    e = estado()
    print(f"  disponible: {e.disponible} · {e.motivo}")
    print(f"  simulado:   {estado(simular=True).wallet.direccion}")
