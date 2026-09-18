"""Eval de la recuperacion, midiendo el camino REAL del agente.

El agente no busca con la pregunta literal del usuario: el modelo la reformula antes
de llamar a la tool (query rewriting). Medir solo la busqueda en crudo es mas estricto
que la realidad, asi que se miden las dos y la diferencia es lo que aporta el modelo.

POR QUE HAY UN SET "DURO"
    El set original daba 31/31 en recall@3: estaba saturado. Contra un techo no se puede
    demostrar que nada mejore, asi que cualquier numero sobre el set facil es infalsificable.
    El set duro anade familias donde lo lexico sufre de verdad: parafrasis sin vocabulario
    comun, mezcla es/en, erratas y preguntas de varios saltos.

GRANULARIDAD
    El set facil se etiqueto por CAJA. Eso perdona un fallo real: recuperar la seccion
    equivocada de la caja correcta cuenta como acierto. El set duro se etiqueta por TROZO
    ("04 · Índices"), que es lo que de verdad se le manda al modelo. Las dos formas conviven:
    "04" acepta cualquier trozo de la caja 04.

COSTE
    Las reformulaciones se cachean en eval_cache.json. Con el candado offline puesto, un
    caso sin cachear se marca SIN CACHE en vez de llamar al modelo: correr el eval no
    cuesta dinero nunca por accidente.

    python3 eval.py                # offline, gratis
    MIRAG_OFFLINE=0 python3 eval.py --refrescar    # rehace las reformulaciones (CUESTA)
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import json
import statistics
import sys
from pathlib import Path

import agent
import rag

CACHE = Path(__file__).parent / "eval_cache.json"
PROFUNDIDAD = 10                      # hasta donde se mira para el MRR

# ── set original: etiquetado por caja, se conserva para poder comparar ───────
FACILES = [
    ("que es el outbox pattern", ["08"]), ("como funciona el reranking en RAG", ["18"]),
    ("diferencia entre liveness y readiness", ["12", "13", "10"]),
    ("como se evita el thundering herd", ["09"]),
    ("que es write skew", ["04"]), ("SLO y error budget", ["10"]),
    ("pagination con cursor", ["03"]), ("como guardo una contrasena de usuario", ["06"]),
    ("que es CORS y para que sirve", ["02"]), ("prompt injection en agentes", ["18"]),
    ("idempotency key para no cobrar dos veces", ["07", "03", "08"]),
    ("que es un circuit breaker", ["10"]),
    ("tipos de indices en postgres", ["04"]), ("blue green o canary", ["14"]),
    ("testcontainers para tests", ["11"]), ("N+1 queries", ["04"]),
    ("como funciona el GIL de python", ["01"]), ("multi-tenancy y aislamiento", ["17"]),
    ("fan out on write timeline", ["19"]), ("dead letter queue", ["08"]),
    ("que es SQL injection", ["06"]), ("como uso JWT", ["06"]), ("SSE o websocket", ["02"]),
    ("diferencia entre inner join y left join", ["04"]), ("que es coupling y cohesion", ["05"]),
    ("que dimensiones tiene un embedding", ["18"]), ("worker pool en python", ["01"]),
    ("como se escribe un ADR", ["19"]), ("checklist antes de desplegar", ["14"]),
    ("volumenes persistentes en kubernetes", ["13"]), ("CSV injection", ["15"]),
]

# ── set duro: etiquetado por TROZO, verificado leyendo el corpus ─────────────
# Cada respuesta se comprobo a mano: la seccion citada contesta de verdad la pregunta.
DUROS = [
    # parafrasis: describir el problema sin nombrar el concepto
    ("parafrasis", "mi servicio se queda esperando para siempre a otro que no responde",
     ["10 · Timeouts"]),
    ("parafrasis", "cuando un servicio va lento las peticiones se amontonan y tiran todo lo demas",
     ["09 · Backpressure", "10 · Bulkheads (mamparos)", "10 · Circuit breakers"]),
    ("parafrasis", "que el cliente no pague dos veces si le da dos veces al boton",
     ["07 · Idempotencia en pagos", "08 · Idempotencia (el pilar de todo)", "03 · Idempotency"]),
    ("parafrasis", "subir un archivo grande sin que pase por mi servidor",
     ["15 · El patrón correcto: presigned URLs", "15 · Multipart y uploads resumibles"]),
    ("parafrasis", "enterarme de que algo va mal antes de que me lo cuente un cliente",
     ["12 · Alerts", "10 · SLI, SLO, SLA y error budget"]),
    ("parafrasis", "la consulta tarda muchisimo cuando filtro por fecha y hay millones de filas",
     ["04 · Índices", "04 · Query optimization"]),
    ("parafrasis", "guardar quien hizo que y cuando para poder auditarlo despues",
     ["17 · Audit logs"]),
    ("parafrasis", "repartir el trabajo pesado para no bloquear la respuesta al usuario",
     ["15 · Background processing", "01 · Patrones de concurrencia"]),

    # mezcla es/en: como se escribe de verdad en el trabajo
    ("mixto", "como hago health check de un servicio",
     ["12 · Health checks", "10 · Implementación: health checks y apagado elegante"]),
    ("mixto", "cursor based pagination o offset para mi API", ["03 · Pagination"]),
    ("mixto", "necesito rate limiting en mi endpoint", ["03 · Rate limiting"]),
    ("mixto", "graceful shutdown de un pod sin cortar requests en vuelo",
     ["10 · Implementación: health checks y apagado elegante", "13 · Kubernetes",
      "14 · Estrategias de despliegue"]),

    # erratas: el usuario escribe rapido
    ("erratas", "idenpotencia en pagos", ["07 · Idempotencia en pagos"]),
    ("erratas", "indices en postgress", ["04 · Índices"]),
    ("erratas", "transaciones y aislamento en base de datos", ["04 · Transacciones y ACID"]),

    # varios saltos: la respuesta esta repartida
    ("multisalto", "como evito que dos usuarios reserven la misma plaza a la vez en postgres",
     ["04 · Locks y deadlocks", "04 · Transacciones y ACID"]),
    ("multisalto", "cobrar una sola vez aunque el cliente reintente y la red falle",
     ["07 · Idempotencia en pagos", "08 · Idempotencia (el pilar de todo)",
      "08 · Retries, backoff y sus peligros"]),
    ("multisalto", "publicar un evento y guardar en base de datos sin que se descuadren",
     ["08 · Outbox pattern (el problema de la doble escritura)"]),
]

# ── lo que el corpus NO cubre ────────────────────────────────────────────────
# No entran en recall: aqui no hay respuesta correcta que recuperar. Sirven para la
# etapa de suficiencia. El grado importa: 'mencionado' es el caso dificil, porque el
# retrieval SI devuelve algo con buena puntuacion y parece una respuesta.
SIN_COBERTURA = [
    ("mencionado", "implementar consenso Raft con garantias de linealizabilidad"),
    ("mencionado", "configurar un service mesh con mTLS entre servicios"),
    ("ausente", "streaming de video en tiempo real con WebRTC"),
    ("ausente", "entrenar un modelo de machine learning con pytorch"),
]

BUSQUEDAS = {"buscar_en_docs": "query", "buscar_tradeoffs": "tema", "buscar_fallos": "tema"}


def acierta(trozo, aceptables):
    """¿Este trozo es una respuesta valida? Acepta caja suelta o 'caja · titulo'."""
    numero = trozo.caja.split("·")[0].strip()
    for a in aceptables:
        if "·" in a:
            caja, _, titulo = a.partition("·")
            if numero == caja.strip() and trozo.titulo == titulo.strip():
                return True
        elif numero == a.strip():
            return True
    return False


def posiciones(consulta, aceptables, k=PROFUNDIDAD):
    """En que puestos del ranking aparece una respuesta valida (1 = el primero)."""
    if not consulta:
        return []
    hits = rag._ranking(rag.TROZOS, consulta, k)
    return [i for i, (t, _) in enumerate(hits, 1) if acierta(t, aceptables)]


def metricas(todas):
    """recall@1, recall@3 y MRR a partir de las posiciones de cada caso."""
    n = len(todas) or 1
    r1 = sum(1 for p in todas if p and p[0] == 1)
    r3 = sum(1 for p in todas if p and p[0] <= 3)
    mrr = sum(1 / p[0] for p in todas if p) / n
    return r1, r3, mrr


def reformular(pregunta, cache):
    """Lo que el modelo pide buscar de verdad. Con el candado puesto: nunca llama."""
    if pregunta in cache:
        return cache[pregunta], "cache"
    if agent.OFFLINE:
        return None, "sin cache"          # honesto: no lo sabemos, y no vamos a pagar por saberlo
    msg = agent.llm([{"role": "system", "content": agent.SYSTEM},
                     {"role": "user", "content": pregunta}])
    consulta = None
    for call in msg.get("tool_calls") or []:
        if (arg := BUSQUEDAS.get(call["function"]["name"])):
            consulta = json.loads(call["function"]["arguments"], strict=False).get(arg)
            break
    cache[pregunta] = consulta            # None = el modelo NO consulto los documentos
    return consulta, "nueva"


def tokens_de_contexto(consulta):
    """Lo que de verdad se le manda al modelo por esta consulta.

    Antes sumaba rag.buscar + buscar_antipatrones + buscar_fallos, o sea la forma del
    contexto ANTERIOR a la Fase 2. Desde que hay un solo ContextBuilder, esa suma medía
    un contexto que ya no se construye asi — el mismo error de medir una cosa y servir
    otra. Ahora pregunta a quien lo arma de verdad.
    """
    import plan as P
    import recuperacion
    r = recuperacion.recuperar(consulta, plan=P.deducir(consulta))
    return recuperacion.construir_contexto(r, peticion=consulta)[1]["tokens_aprox"]


def evaluar(casos, cache):
    """casos: [(familia, pregunta, aceptables)] -> filas con las dos mediciones."""
    filas, sin_cache = [], []
    for familia, pregunta, aceptables in casos:
        crudo = posiciones(pregunta, aceptables)
        consulta, origen = reformular(pregunta, cache)
        if origen == "sin cache":
            sin_cache.append(pregunta)
        reescrito = posiciones(consulta, aceptables) if consulta else []
        filas.append({"familia": familia, "pregunta": pregunta, "aceptables": aceptables,
                      "crudo": crudo, "consulta": consulta, "reescrito": reescrito,
                      "origen": origen})
    return filas, sin_cache


def tabla(titulo, filas):
    print(f"\n{titulo}")
    print(f"  {'familia':<14} {'n':>3}  {'R@1':>7} {'R@3':>7} {'MRR':>6}   "
          f"{'R@1':>7} {'R@3':>7} {'MRR':>6}")
    print(f"  {'':<14} {'':>3}  {'-- literal --':^22}   {'- reformulada -':^22}")
    familias = {}
    for f in filas:
        familias.setdefault(f["familia"], []).append(f)
    for familia, grupo in list(familias.items()) + ([("TOTAL", filas)] if len(familias) > 1 else []):
        n = len(grupo)
        c1, c3, cm = metricas([g["crudo"] for g in grupo])
        # solo se mide la reformulacion de los casos que la tienen: un caso sin cachear
        # no es un cero, es un dato que no tenemos. Poner 0.000 seria inventarlo.
        medidos = [g for g in grupo if g["origen"] != "sin cache"]
        izq = f"  {familia:<14} {n:>3}  {c1:>3}/{n:<3} {c3:>3}/{n:<3} {cm:>6.3f}   "
        if not medidos:
            print(izq + f"{'—':>7} {'—':>7} {'—':>6}   (sin medir)")
        else:
            m = len(medidos)
            r1, r3, rm = metricas([g["reescrito"] for g in medidos])
            print(izq + f"{r1:>3}/{m:<3} {r3:>3}/{m:<3} {rm:>6.3f}"
                  + ("" if m == n else f"   (solo {m} de {n} medidos)"))


def main():
    refrescar = "--refrescar" in sys.argv
    cache = {} if refrescar else (json.loads(CACHE.read_text()) if CACHE.exists() else {})

    faciles = [("facil", p, a) for p, a in FACILES]
    duros = [(fam, p, a) for fam, p, a in DUROS]

    f_faciles, sin1 = evaluar(faciles, cache)
    f_duros, sin2 = evaluar(duros, cache)

    if not agent.OFFLINE:
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))

    print(f"{len(rag.TROZOS)} trozos · {len(faciles)} casos faciles · {len(duros)} duros"
          f"{'  ·  OFFLINE (0 llamadas)' if agent.OFFLINE else '  ·  CON LLM'}")

    tabla("SET FACIL (etiquetado por caja — saturado, se conserva para comparar)", f_faciles)
    tabla("SET DURO (etiquetado por trozo — aqui es donde hay margen)", f_duros)

    contexto = [tokens_de_contexto(f["consulta"] or f["pregunta"]) for f in f_faciles + f_duros]
    print(f"\ncontexto recuperado: mediana {statistics.median(contexto):,.0f} tokens · "
          f"max {max(contexto):,} · min {min(contexto):,}")

    sin_cache = sin1 + sin2
    if sin_cache:
        print(f"\n{len(sin_cache)} casos SIN CACHE: no se midio la reformulacion y no se llamo "
              f"al modelo.\n  Para medirla: MIRAG_OFFLINE=0 python3 eval.py   (cuesta dinero)")

    fallos = [f for f in f_duros if not f["crudo"]]
    if fallos:
        print(f"\nel set duro no se recupera ni en {PROFUNDIDAD} puestos ({len(fallos)}):")
        for f in fallos:
            print(f"  ✗ [{f['familia']}] {f['pregunta']}")
            print(f"      esperaba: {', '.join(f['aceptables'])}")

    print(f"\nsin cobertura en el corpus ({len(SIN_COBERTURA)} casos): no entran en recall, "
          f"son para la etapa de suficiencia.")

    if "--guardar" in sys.argv:
        nombre = sys.argv[sys.argv.index("--guardar") + 1]
        guardar(nombre, f_faciles, f_duros, contexto)
    return f_faciles, f_duros


def guardar(nombre, f_faciles, f_duros, contexto):
    """Congela una medicion para poder comparar contra ella mas adelante."""
    # Este archivo YA vive en benchmarks/: colgar otro "benchmarks" de aqui creaba
    # benchmarks/benchmarks/ y la medicion se guardaba donde nadie la busca.
    carpeta = Path(__file__).resolve().parent
    carpeta.mkdir(exist_ok=True)

    def bloque(filas):
        por_familia = {}
        for f in filas:
            por_familia.setdefault(f["familia"], []).append(f)
        salida = {}
        for familia, grupo in list(por_familia.items()) + [("TOTAL", filas)]:
            r1, r3, mrr = metricas([g["crudo"] for g in grupo])
            salida[familia] = {"n": len(grupo), "recall_1": r1, "recall_3": r3,
                               "mrr": round(mrr, 4)}
        return salida

    datos = {
        "nombre": nombre,
        "trozos": len(rag.TROZOS),
        "medido_con": "pregunta literal (la reformulacion necesita LLM)",
        "llamadas_llm": 0 if agent.OFFLINE else None,
        "facil": bloque(f_faciles),
        "duro": bloque(f_duros),
        "contexto_tokens": {"mediana": statistics.median(contexto),
                            "max": max(contexto), "min": min(contexto)},
        "casos_duros": [{"familia": f["familia"], "pregunta": f["pregunta"],
                         "aceptables": f["aceptables"], "posiciones": f["crudo"]}
                        for f in f_duros],
    }
    destino = carpeta / f"{nombre}.json"
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    print(f"\ncongelado en benchmarks/{nombre}.json")


if __name__ == "__main__":
    main()
