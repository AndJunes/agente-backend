# Fase 2 — Unificación del pipeline

**Coste OpenRouter de la fase: $0.0000.** Todo se verificó con dobles, espías y comparación de
objetos. (La única llamada real —$0.0069— fue la comprobación manual de la UI al final, fuera del
trabajo de migración.)

---

## Before

```
simple     ──→ agent.run + tool calls ──→ rag.buscar*        ──→ contexto propio
rapido     ──→ rapido.recuperar()    ──→ rag.buscar* x3      ──→ contexto propio
pipeline   ──→ hibrido.recuperar()   ──→ [resultado TIRADO]
             └→ rapido.recuperar()   ──→ rag.buscar* x3      ──→ contexto real   ← el conflicto
arquitecto ──→ agent.run + tool calls ──→ rag.buscar*        ──→ contexto propio

banco_recuperacion ──→ hibrido.recuperar(indice=None) ──→ solo TROZOS            ← medía otra cosa
banco.py           ──→ rapido.implementar                                        ← medía el modo viejo
```

## After

```
                        ┌──────────────────────┐
                        │ recuperacion.recuperar│   ← fuente única
                        └──────────┬───────────┘
                    ┌──────────────┼──────────────┐
                    ↓              ↓              ↓
                 TROZOS      ANTIPATRONES      FALLOS
                    └──────────────┼──────────────┘
                                   ↓
                          RetrievalResult
                                   ↓
                   recuperacion.construir_contexto
                                   ↓
                                  LLM

PRODUCCIÓN   pipeline      ──→ recuperar() ──→ RetrievalResult ──→ ContextBuilder ──→ LLM
EXPERIMENTAL arquitecto    ──→ (orquestación propia, etiquetado en UI)
BENCHMARK    banco_recuperacion ──→ recuperar()   (la MISMA, los MISMOS tres índices)
BENCHMARK    banco.py           ──→ pipeline.ejecutar
```

## Removed

| modo | estado | qué pasó con su código |
|---|---|---|
| `simple` | retirado del dispatch público | `agent.run` sigue vivo como **motor interno** — lo usa `arquitecto` |
| `rapido` | retirado del dispatch público | `rapido.py` **no se borró**: sigue siendo la librería de la que el pipeline reutiliza `_evidencia`, `_como_lista`, `simulado`, `_comprobar_sintaxis`, `ENTREGAR`, `guardar` |

Pedir un modo retirado devuelve un rechazo explícito, no un error:
```
rapido → RETIRADO (rechazo explicito)
simple → RETIRADO (rechazo explicito)
```

## Experimental

`arquitecto` sigue disponible y aparece en la UI con una etiqueta **EXPERIMENTAL** y la frase
*"Sus fases no tienen el mismo nivel de verificación que Pipeline."* No se tocó su orquestación,
no se le añadieron validadores y no se gastó presupuesto en él.

## Retrieval — fuente de verdad

`recuperacion.recuperar(consulta, plan, familia, vector, reranker)` en
[recuperacion.py](recuperacion.py). Recorre los tres índices con el mismo ranking
(filtro de metadatos → BM25 → vector? → RRF → reranker?) y devuelve `RetrievalResult` con la
**procedencia de cada trozo**: de qué índice salió, en qué puesto, con qué puntuación y por qué
métodos pasó.

Los nombres de etapa llevan el índice (`bm25:conocimiento`, `bm25:antipatrones`, `bm25:fallos`).
Sin eso, tres llamadas producían tres pasos `bm25` idénticos y cualquier búsqueda por nombre se
quedaba con el primero — un test habría creído medir tres índices midiendo uno.

## Context — fuente de verdad

`recuperacion.construir_contexto(resultado, ...)`. Único sitio donde se decide qué entra al prompt:
orden, deduplicación por identidad, techo de 24.000 caracteres, símbolos, aviso de cobertura.
Devuelve además las medidas (chars, tokens, incluidos, descartados, SHA).

Hay un test que falla si alguien vuelve a llamar a `rapido._contexto` durante una petición.

## Benchmark — fuente de verdad

`banco_recuperacion.medir()` llama a `recuperacion.recuperar()`, la misma función, sobre los mismos
tres índices. Recall y MRR se calculan sobre la porción de **conocimiento**, que es contra la que
existen etiquetas en `eval.py`; los otros dos índices se ejecutan igual y se registran sus conteos
en `trozos_por_indice`.

`banco.py` (nivel agente) pasó de `rapido.implementar` a `pipeline.ejecutar`. El brazo baseline ya
no se arma monkeypatcheando `rapido.cajas_del_plan`: se pasa un plan con `domains=[]`.

---

## Verification

### La prueba decisiva

Misma consulta, capturando el `messages[-1]["content"]` real que recibe `agent.llm`:

| | reranker ON | reranker OFF | ¿idénticos? |
|---|---|---|---|
| **antes (Fase 0)** | sha `00cb0796ccc4dfb6` | sha `00cb0796ccc4dfb6` | **SÍ** — el reranker no llegaba al modelo |
| **ahora** | sha `db3af905bfde33dc`, 10.025 chars | sha `9e7bed6372d1e8d7`, 8.079 chars | **NO** |

### Los 18 casos de `test_pipeline_unico.py`

Identidad producción↔benchmark (compara **ids de trozos**, no que "hubo un paso de retrieval") ·
el banco recupera de los tres índices · el banco pasa por la función de producción · el reranker
cambia el prompt · un chunk seleccionado llega al modelo · un chunk descartado **no** llega ·
`rapido.recuperar` se llama 0 veces · `rapido._contexto` se llama 0 veces · la recuperación ocurre
**exactamente una vez** · las tres secciones están en el contexto · la procedencia se conserva ·
los anti-patrones quedan disponibles · dedup · techo de contexto · generar+verificar+entregar ·
el bucle de reparación sigue vivo · dos modos públicos · la UI no ofrece los retirados.

### Regression

**255 casos, 0 suites rojas.** Antes de la fase: 237. Los 18 nuevos son `test_pipeline_unico.py`.

Tres tests de `test_full_pipeline.py` fallaron durante la migración y se actualizaron **porque el
contrato cambió a propósito**: buscaban la etapa `"bm25"` y ahora es `"bm25:conocimiento"`. De
paso, `r3_multisalto` pasó a afirmar algo real —antes calculaba un conjunto de cajas a partir de
un detalle que era un string, salía vacío y no se comprobaba nada. Ahora exige que la consulta
toque ≥2 cajas y traiga anti-patrones.

Un test de `test_cimientos.py` se reescribió por el mismo motivo: comprobaba que el literal
`"lambda *a, **kw: []"` estuviera en `banco.py`, o sea que fijaba una implementación. Ahora ejecuta
los dos brazos y comprueba que producen trazas distinguibles y que el baseline no acota cajas.

### Números del benchmark, sobre el pipeline real

| configuración | R@1 | R@3 | MRR | MRR duro | ms |
|---|---|---|---|---|---|
| base (bm25) | 35/49 | 43/49 | 0.805 | 0.553 | 3.54 |
| + vector + RRF | 35/49 | 41/49 | 0.791 | **0.538** | 46.49 |
| + reranker | 37/49 | 44/49 | 0.829 | **0.634** | 9.90 |
| + vector + reranker | 39/49 | 43/49 | 0.845 | **0.651** | 8.79 |
| idf (el de antes) | 34/49 | 41/49 | 0.776 | 0.469 | 4.29 |

**Estos números no son comparables con los de ayer** y la compuerta se vació al empezar la fase
precisamente por eso: ahora se mide el camino real, con el plan activo y sobre tres índices. La
decisión de qué se enciende es de la Fase 3, con estos datos y no con los heredados.

---

## Remaining

| | estado |
|---|---|
| `cache.py`, `arbol.py`, `grafo.py`, `enrutador.py` | **ISOLATED** — sin cambios, se deciden en la Fase 5 |
| `vector_signal`, `reranker`, y los otros condicionales | **DISABLED** — la compuerta está vacía hasta la Fase 3 |
| Anti-patrones de cubrimiento obligatorio | **NOT VERIFIED** — `RetrievalResult.antipatrones` ya preserva identidad y procedencia, pero **nada comprueba todavía** que la entrega los cubra. Es trabajo de la Fase 4 y no se finge lo contrario |
| `arquitecto` | **EXPERIMENTAL** — etiquetado, sin validadores |
| 7 flags que nadie lee | sin tocar, Fase 5 |
| Benchmark a nivel agente (`banco.py`) | migrado estructuralmente, **medición real pendiente** de la Fase 7 |
| El modo offline responde con fixtures por regex | sin tocar, Fase 6 |

---

```
PRODUCTION PATH:
    USER → server.do_POST → estado.responder (atajo) → pipeline.ejecutar
         → plan.deducir → recuperacion.recuperar (3 índices) → RetrievalResult
         → simbolos? → grafo? → suficiencia → construir_contexto → agent.llm
         → entrega → verificar → reparar? → evidencia → persistencia → traza → SSE

RETRIEVAL SOURCE OF TRUTH:
    recuperacion.recuperar()          — recuperacion.py

CONTEXT SOURCE OF TRUTH:
    recuperacion.construir_contexto() — recuperacion.py

BENCHMARK SOURCE OF TRUTH:
    banco_recuperacion.medir() → recuperacion.recuperar()   (retrieval)
    banco.py correr()          → pipeline.ejecutar()        (agente)

PUBLIC MODES:
    pipeline

EXPERIMENTAL MODES:
    arquitecto
```
