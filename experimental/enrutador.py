"""Elegir modelo segun lo que pide la tarea. Hoy: solo el enganche.

POR QUE ESTO ES UN ESQUELETO Y NO UNA POLITICA
    Un router de modelos no puede saber que modelo va mejor hasta que haya datos reales
    de coste, latencia y exito verificado por modelo. Esta noche no hay ninguno: todo
    corre con dobles. Asi que se construye la pieza — clasificador determinista, cadena
    de respaldo, registro de por que se eligio — y se deja APAGADA por defecto.

    Cuando haya trazas de verdad (varias tareas, varios modelos), la tabla de abajo se
    sustituye por lo medido. Mientras tanto, MODELOS es una preferencia declarada, no
    una conclusion.

EL COSTE NO SE INVENTA
    El proyecto no tiene tabla de precios y el coste real solo se conoce DESPUES de la
    respuesta (OpenRouter lo devuelve en usage.cost). Aqui se puede declarar un coste
    ESTIMADO por modelo para poder comparar antes de llamar, y va marcado como
    estimacion en todos los sitios. Nunca se escribe como coste facturado.
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
import re
from typing import NamedTuple

import agent
import config

# clase de tarea -> modelo preferido. Preferencia declarada, NO medida.
MODELOS = {
    "simple":        "anthropic/claude-haiku-4.5",
    "normal":        "anthropic/claude-haiku-4.5",
    "complex":       "anthropic/claude-haiku-4.5",
    "architectural": "anthropic/claude-haiku-4.5",
}
# Hoy son todos el mismo a proposito: cambiarlos sin datos seria elegir a ciegas.
# El enganche esta listo; la decision es de mañana.

# OJO — el reintento de aqui es INALCANZABLE hoy, y conviene saberlo antes de confiar en el:
# `respaldos` se calcula quitando el modelo elegido de esta lista, y como MODELOS son todos
# este mismo, la lista sale SIEMPRE vacia. No es un bug que arreglar a ciegas: meter un
# segundo modelo sin haber medido nada seria elegir al azar. Queda escrito para que nadie
# lea "hay respaldos" donde dice "hay una lista".
RESPALDOS = ["anthropic/claude-haiku-4.5"]

# $/1M tokens, ESTIMADO de la web publica. Solo para comparar antes de llamar.
COSTE_ESTIMADO = {"anthropic/claude-haiku-4.5": {"entrada": 1.0, "salida": 5.0}}

PALABRAS_ARQUITECTURA = re.compile(
    r"\b(arquitectura|diseña|diseñar|system design|escalar|migrar|trade-?off|"
    r"comparar|evaluar|estrategia|adr)\b", re.I)
PALABRAS_COMPLEJAS = re.compile(
    r"\b(concurren|race condition|idempot|transacc|distribu|consistencia|"
    r"seguridad|rendimiento|optimiz)\b", re.I)
PALABRAS_SIMPLES = re.compile(r"^\s*(que es|qué es|what is|define|definicion)\b", re.I)


class Ruta(NamedTuple):
    modelo: str
    clase: str
    motivo: str
    respaldos: tuple = ()
    max_tokens: int = 12000

    def coste_estimado(self, entrada=8000, salida=2000):
        """ESTIMACION, no coste facturado. Devuelve None si no hay tarifa."""
        t = COSTE_ESTIMADO.get(self.modelo)
        if not t:
            return None
        return round(entrada / 1e6 * t["entrada"] + salida / 1e6 * t["salida"], 5)


def clasificar(peticion, plan=None):
    """simple | normal | complex | architectural. Determinista y explicable."""
    texto = peticion or ""
    motivos = []

    if PALABRAS_ARQUITECTURA.search(texto):
        motivos.append("pide diseñar o comparar")
        clase = "architectural"
    elif PALABRAS_COMPLEJAS.search(texto):
        motivos.append("toca concurrencia, consistencia o seguridad")
        clase = "complex"
    elif PALABRAS_SIMPLES.match(texto.strip(" ¿¡\t\n")) and len(texto) < 90:
        motivos.append("definicion corta")
        clase = "simple"
    else:
        motivos.append("ni trivial ni de diseño")
        clase = "normal"

    if plan is not None:
        if plan.needs_code and clase == "simple":
            clase = "normal"
            motivos.append("pero hay que generar codigo")
        if len(plan.domains or ()) >= 4 and clase in ("simple", "normal"):
            clase = "complex"
            motivos.append(f"cruza {len(plan.domains)} areas")
        if plan.depth == "deep" and clase == "simple":
            clase = "normal"
            motivos.append("el plan pide profundidad")
    return clase, " · ".join(motivos)


def elegir(peticion, plan=None):
    """La ruta. Si el router esta apagado, devuelve el modelo de siempre y lo dice."""
    activo, motivo_flag = config.activar("model_routing")
    if not activo:
        return Ruta(agent.MODEL, "sin enrutar", f"router apagado ({motivo_flag})",
                    tuple(RESPALDOS))
    clase, motivo = clasificar(peticion, plan)
    modelo = MODELOS.get(clase, agent.MODEL)
    respaldos = tuple(m for m in RESPALDOS if m != modelo)
    tokens = {"simple": 4000, "normal": 12000, "complex": 12000,
              "architectural": 16000}[clase]
    return Ruta(modelo, clase, motivo, respaldos, tokens)


def llamar(messages, ruta, tools=None, llm=None):
    """Llama con respaldo: si el modelo elegido falla, se prueba el siguiente.

    Devuelve (mensaje, intentos) donde intentos explica que paso con cada modelo.
    """
    llamador = llm or (lambda m, t: agent.llm(m, tools=t))
    intentos = []
    for modelo in (ruta.modelo,) + tuple(ruta.respaldos):
        try:
            anterior, agent.MODEL = agent.MODEL, modelo
            try:
                msg = llamador(messages, tools)
            finally:
                agent.MODEL = anterior
            intentos.append({"modelo": modelo, "resultado": "ok"})
            return msg, intentos
        except agent.ModoOffline:
            raise                                  # el candado no se reintenta
        except Exception as e:
            intentos.append({"modelo": modelo, "resultado": "fallo",
                             "error": f"{type(e).__name__}: {e}"})
    raise RuntimeError(f"todos los modelos fallaron: {intentos}")


if __name__ == "__main__":
    ejemplos = [
        "¿Que es un indice de PostgreSQL?",
        "Crea calculator.py con tests",
        "como evito un race condition al reservar una plaza",
        "diseña la arquitectura de un sistema de pagos que escale",
    ]
    import plan as P
    for e in ejemplos:
        p = P.deducir(e)
        clase, motivo = clasificar(e, p)
        r = elegir(e, p)
        print(f"  {clase:<14} {motivo:<48} → {r.modelo.split('/')[-1]} "
              f"(max_tokens {r.max_tokens})")
    print(f"\n  estado del router: {config.activar('model_routing')[1]}")
