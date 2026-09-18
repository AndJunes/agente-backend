"""Un solo sitio para los interruptores del pipeline.

Dos tipos de etapa, y se tratan distinto a proposito:

  NUCLEO       encendido salvo que lo apagues. Es el cerebro del retrieval.
  CONDICIONAL  en 'auto': NO lo decido yo, lo decide la medicion. Una etapa sin
               medir nace apagada, y una que mide peor que lo que cuesta se apaga
               sola. La politica la escribe benchmarks/ganancias.json, no este archivo.

Cada interruptor acepta on / off / auto por variable de entorno:
    MIRAG_RERANKER=on python3 test_pipeline.py
"""

import json
import os
from pathlib import Path

CARPETA = Path(__file__).parent
GANANCIAS = CARPETA / "benchmarks" / "ganancias.json"

# lo que hace falta para que una etapa condicional se encienda sola
UMBRAL_MRR = 0.02          # menos de esto no es mejora, es ruido
COSTE_MAXIMO = 1.0         # ganancia tiene que superar al coste normalizado


def _modo(nombre, defecto="auto"):
    """on = siempre · off = nunca · auto = que decida la medicion."""
    v = os.environ.get("MIRAG_" + nombre, defecto).strip().lower()
    return v if v in ("on", "off", "auto") else defecto


# ── nucleo: encendido salvo que lo apagues ──────────────────────────────────
RETRIEVAL_PLAN   = _modo("RETRIEVAL_PLAN", "on")
METADATA_ROUTING = _modo("METADATA_ROUTING", "on")
HYBRID_RETRIEVAL = _modo("HYBRID_RETRIEVAL", "on")
SYMBOL_RETRIEVAL = _modo("SYMBOL_RETRIEVAL", "on")   # ademas exige plan.needs_symbols
SUFICIENCIA      = _modo("SUFICIENCIA", "on")

# ── condicionales: en auto, decide ganancias.json ───────────────────────────
# El BM25 es el suelo y siempre corre (HYBRID_RETRIEVAL). La SEÑAL VECTORIAL es otra
# cosa: es una segunda opinion que solo entra si se demuestra que aporta. Fusionar una
# señal mala con una buena empeora las dos.
VECTOR_SIGNAL     = _modo("VECTOR_SIGNAL")
RERANKER          = _modo("RERANKER")
CONTEXTUAL_CHUNKS = _modo("CONTEXTUAL_CHUNKS")
SEMANTIC_CACHE    = _modo("SEMANTIC_CACHE")
KNOWLEDGE_TREE    = _modo("KNOWLEDGE_TREE")
GRAPH_RETRIEVAL   = _modo("GRAPH_RETRIEVAL")
MODEL_ROUTING     = _modo("MODEL_ROUTING")

# ── fuera, con el punto de extension puesto ─────────────────────────────────
COLBERT = _modo("COLBERT", "off")

# ── que hace REALMENTE cada interruptor ─────────────────────────────────────
# Una bandera que nadie lee es una mentira sobre lo que se puede configurar: pones
# MIRAG_SEMANTIC_CACHE=on, no pasa nada, y nada te lo dice. Aqui queda declarado, y
# hay un test que lo comprueba APAGANDO Y ENCENDIENDO cada una y mirando si cambia
# algo — no leyendo el codigo fuente, que es donde empiezan estas mentiras.
CONECTADO = "CONECTADO"          # cambiarla cambia lo que hace el pipeline
EXPERIMENTAL = "EXPERIMENTAL"    # el modulo existe y funciona, pero no esta en el camino
NO_IMPLEMENTADO = "NO IMPLEMENTADO"

ESTADO_FLAGS = {
    "RETRIEVAL_PLAN":    (CONECTADO, "pipeline.ejecutar deduce el plan o lo deja vacio"),
    "METADATA_ROUTING":  (CONECTADO, "hibrido.recuperar filtra por metadatos"),
    "HYBRID_RETRIEVAL":  (CONECTADO, "recuperacion.recuperar; apagado deja solo el orden del corpus"),
    "SYMBOL_RETRIEVAL":  (CONECTADO, "pipeline.ejecutar, ademas exige plan.needs_symbols"),
    "SUFICIENCIA":       (CONECTADO, "pipeline.ejecutar decide el aviso de cobertura"),
    "VECTOR_SIGNAL":     (CONECTADO, "hibrido.recuperar; medido peor que BM25, en auto queda off"),
    "RERANKER":          (CONECTADO, "hibrido.recuperar; medido +0.082 MRR duro"),
    "GRAPH_RETRIEVAL":   (CONECTADO, "pipeline.ejecutar expande por grafo"),
    "MODEL_ROUTING":     (EXPERIMENTAL, "enrutador.py lo lee, pero no gobierna agent.llm"),
    "SEMANTIC_CACHE":    (EXPERIMENTAL, "cache.py existe y esta testeado; no esta en el pipeline"),
    "KNOWLEDGE_TREE":    (EXPERIMENTAL, "arbol.py existe y esta testeado; no esta en el pipeline"),
    "CONTEXTUAL_CHUNKS": (NO_IMPLEMENTADO, "no hay codigo detras de esta bandera"),
    "COLBERT":           (NO_IMPLEMENTADO, "punto de extension, sin implementacion"),
}


def estado_de(flag):
    """(estado, motivo). Lo que de verdad pasa si tocas esta bandera."""
    return ESTADO_FLAGS.get(flag.upper(), (NO_IMPLEMENTADO, "bandera desconocida"))


def avisos_de_banderas(entorno=None):
    """MIRAG_X puesto a mano en una bandera que no hace nada: hay que decirlo."""
    entorno = os.environ if entorno is None else entorno
    fuera = []
    for flag, (est, motivo) in ESTADO_FLAGS.items():
        if est != CONECTADO and ("MIRAG_" + flag) in entorno:
            fuera.append(f"MIRAG_{flag} esta puesta y no hace nada: {est} — {motivo}")
    return fuera

# local = n-gramas de caracteres, sin red, gratis, NO semantico
# openrouter = embeddings de verdad, con coste y latencia de red
VECTOR_BACKEND = os.environ.get("MIRAG_VECTOR_BACKEND", "local").strip().lower()


def _ganancias():
    try:
        return json.loads(GANANCIAS.read_text())
    except (OSError, ValueError):
        return {}                      # sin mediciones: todo lo 'auto' queda apagado


def activar(etapa, familia="general", ganancias=None):
    """¿Se ejecuta esta etapa? Devuelve (si_o_no, motivo) — el motivo va a la traza.

    El motivo importa tanto como la decision: en la UI hay que poder explicar por que
    Mirag NO uso el reranker, y 'no lo he medido todavia' es una respuesta legitima.
    """
    modo = globals().get(etapa.upper(), "auto")
    var = "MIRAG_" + etapa.upper()
    a_mano = var in os.environ          # distinguir lo que pediste de lo que viene por defecto
    estado, por_que = estado_de(etapa)
    if estado == NO_IMPLEMENTADO:
        # No hay codigo detras: encenderla daria un "ON" en la traza y una UI que afirma
        # algo que no ocurre. Nunca arranca, ni a mano.
        return False, f"no implementado: {por_que}"
    if estado == EXPERIMENTAL and not a_mano:
        # Se puede probar a proposito (MIRAG_X=on), pero jamas se enciende sola: en 'auto'
        # una medicion buena no basta, porque no esta en el camino de produccion.
        return False, f"experimental: {por_que}"
    if modo == "on":
        if estado == EXPERIMENTAL:
            # Sin esto la traza diria "ON" a secas y se leeria como produccion.
            return True, f"EXPERIMENTAL, encendida a mano ({var}=on): {por_que}"
        return True, f"encendida a mano ({var}=on)" if a_mano else "del nucleo: siempre activa"
    if modo == "off":
        return False, f"apagada a mano ({var}=off)" if a_mano else "apagada por defecto"

    tabla = _ganancias() if ganancias is None else ganancias
    # una politica ilegible o con la forma cambiada NO puede encender nada: ante la
    # duda, apagado. Es el mismo criterio que 'sin medir'.
    try:
        entrada = tabla.get(etapa) or {}
        medida = entrada.get(familia) or entrada.get("general")
    except AttributeError:
        return False, "la medicion no se pudo leer: se deja apagada"
    if medida is None:
        return False, "sin medir: una etapa que no se ha medido nace apagada"
    try:
        delta = float(medida["delta_mrr"])
        coste = float(medida.get("coste_normalizado", 0.0))
    except (AttributeError, TypeError, KeyError, ValueError):
        return False, "la medicion no se pudo leer: se deja apagada"
    if delta < UMBRAL_MRR:
        return False, f"medida: +{delta:.3f} MRR, por debajo del umbral {UMBRAL_MRR}"
    if delta <= coste:
        return False, f"medida: +{delta:.3f} MRR pero cuesta {coste:.3f}: no compensa"
    return True, f"medida: +{delta:.3f} MRR por {coste:.3f} de coste"


def resumen():
    """Para el informe y para la UI: en que estado esta cada interruptor."""
    etapas = ["retrieval_plan", "metadata_routing", "hybrid_retrieval", "symbol_retrieval",
              "suficiencia", "vector_signal", "reranker", "contextual_chunks", "semantic_cache",
              "knowledge_tree", "graph_retrieval", "model_routing", "colbert"]
    return {e: activar(e) for e in etapas}


if __name__ == "__main__":
    print(f"vector backend: {VECTOR_BACKEND}\n")
    for etapa, (si, motivo) in resumen().items():
        print(f"  {'ON ' if si else 'off'}  {etapa:<18} {motivo}")
