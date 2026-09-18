# Arquitectura

Mirag responde preguntas de ingeniería backend y construye código, y siempre separa tres
cosas: lo que el modelo **afirma**, lo que la máquina **observó** y lo que está **demostrado**.
Este documento explica cómo está organizado el código para cumplir esa promesa.

## Principios

1. **Decide la ejecución, nunca el modelo.** El estado de un fragmento de código se deriva de una
   ejecución (exit code + marcadores `TEST:<id>:PASS|FAIL`) en un único lugar:
   `mirag/execution/verdict.py`. Los estados de los proyectos también se derivan en un único
   lugar: `StatusDeriver` en `mirag/projects/certification.py`.
2. **Ninguna etapa corre por costumbre.** El `FeatureGate` enciende las etapas opcionales de
   retrieval solo cuando un benchmark midió que ayudan (`resources/feature_gains.json`).
   Una etapa que no corre se reporta igual, con su motivo.
3. **Un retrieval, un contexto.** `RetrievalService` es el único retrieval que usan producción
   y benchmarks; `ContextBuilder` es el único lugar que decide qué entra en un prompt.
4. **Offline por defecto.** El `LLMGateway` se niega a llamar a un modelo real salvo que
   `MIRAG_OFFLINE=0`. Las demos usan un modelo guionado y determinista, y se etiquetan SIMULADO.
5. **Runtime de biblioteca estándar.** El núcleo tiene cero dependencias de terceros (lo verifica
   `tests/architecture`). La capa opcional de Stellar declara `stellar-sdk` como extra.
6. **Todo texto que ve el usuario está localizado.** Hoy hay dos locales (`en`, `es`), con una
   carpeta cada uno.

## Capas

```
            ┌──────────────────────────────────────────────────────────┐
 frontera   │ api/ (router HTTP, SSE, validación)      cli.py          │
            ├──────────────────────────────────────────────────────────┤
 aplicación │ container.py (composition root)                          │
            │ pipeline/ (QuestionPipeline + etapas)   agent/ (loop,    │
            │ presentation/ (markdown, paneles)         architect)     │
            │ offline/ (catálogo de demos, scripts, contratos)         │
            │ self_knowledge/ (atajo del estado del proyecto)          │
            ├──────────────────────────────────────────────────────────┤
 dominio    │ retrieval/  execution/  evidence/  projects/  tools/     │
            │ features/   llm/                                         │
            ├──────────────────────────────────────────────────────────┤
 base       │ core/ (settings, errores, texto)   i18n/   paths.py      │
            └──────────────────────────────────────────────────────────┘
   opcional: integrations/blockchain/ (lazy)   fuera de producción: experimental/
```

Las dependencias solo apuntan hacia abajo. `tests/architecture/test_architecture.py` lo hace
cumplir: el dominio nunca importa el pipeline, la API, el container ni la presentación; `core`
no importa nada más de Mirag; nada importa `experimental`; la capa de blockchain solo la importa
el container, de forma lazy.

## El camino de un request

```
POST /api/v1/chat ─▶ ChatService
   ├─ ProjectStateResponder  "¿qué modelo usás?" → se responde con hechos, 0 llamadas
   ├─ ¿offline? → DemoCatalog elige un guion (o "sin modelo")  → LLMGateway(ScriptedChatModel)
   └─ QuestionPipeline.run
        1  project_state
        2  retrieval_plan         PlanDeducer (determinista) — o EMPTY_PLAN si está desactivado
        3-5 retrieval             RetrievalService: 3 índices × (filter → BM25 → vector? → RRF → reranker?)
        6  symbols                solo si el plan pide búsqueda de código
        7  graph                  solo si está medido Y el plan pide relaciones
        8  sufficiency            covered / mentioned / absent — avisa antes de responder
        9  context                ContextBuilder
        10 model                  LLMGateway.chat
        11 rama de código         entregar → sintaxis → ejecutar → reparar una vez → evidencia → anti-patrones
           o rama de proyecto     especificar → generar por grupos → certificar (probes) → empaquetar → artefacto
        12 trace                  TraceWriter (JSONL)
   └─ ClaimAuditor               la prosa final se contrasta con los marcadores que realmente corrieron
   └─ evento done                respuesta + panel de evidencia + timeline + costo + proyecto/entregable
```

## SOLID, en concreto

| Principio | Dónde se ve |
|---|---|
| Responsabilidad única | `CorpusParser` parsea, `Bm25Ranker` rankea, `MetadataFilter` filtra, `HybridRetriever` orquesta un índice, `RetrievalService` los tres índices, `ContextBuilder` arma el prompt. `CodeRunner` ejecuta, `SyntaxChecker` chequea, `ExecutionResult` decide. `ZipBuilder` construye y `ZipInspector` inspecciona - a propósito, con criterios independientes. |
| Abierto/cerrado | Las herramientas nuevas son nuevos objetos `Tool` en un `ToolRegistry`; los rankers nuevos heredan de `Ranker`; los backends vectoriales nuevos heredan de `VectorStore`; los idiomas nuevos son nuevas carpetas de locale - ninguno edita código existente. |
| Liskov | `LocalHashVectorStore` y `OpenRouterVectorStore` son intercambiables detrás de `VectorStore`; `ScriptedChatModel` y `OpenRouterChatModel`, detrás de `ChatModel`. El pipeline no puede distinguir un guion de un modelo (salvo por el flag `simulated`, que reporta). |
| Segregación de interfaces | `ChatModel` tiene un solo método (`complete`). `Repairer` es un único callable. Los presenters reciben solo lo que leen. |
| Inversión de dependencias | Los servicios reciben a sus colaboradores por constructor; `container.py` es el único lugar que elige clases concretas. Los tests arman el mismo grafo con sus propios settings. |

## Paquetes

| Paquete | Responsabilidad |
|---|---|
| `core` | `Settings` (se lee una sola vez del entorno), errores de dominio, helpers de texto, medición de tiempos |
| `i18n` | Registro de locales, catálogos de mensajes, léxico y formato de corpus por locale |
| `features` | Feature flags y el gate de medición |
| `llm` | Puerto del modelo de chat, adaptador de OpenRouter, doble guionado, gateway (lock + presupuesto) |
| `retrieval` | Parseo del corpus, ranking, metadatos, vectores, reranker, retrieval híbrido, servicio, contexto, plan, suficiencia, grafo, símbolos, búsquedas tipadas, motor por locale |
| `execution` | Descubrimiento de intérpretes, runner en sandbox, chequeo de sintaxis, calculadora, el veredicto |
| `evidence` | Filas de evidencia, detección de simulaciones, obligaciones de anti-patrones, auditoría de afirmaciones |
| `tools` | Abstracción de herramienta, registro y herramientas incorporadas |
| `projects` | Modelo de proyecto y política de rutas, análisis de dependencias, probes, certificación, empaquetado, artefactos, generación |
| `pipeline` | El orquestador de producción y sus etapas |
| `agent` | Loop de tool calling y el workflow experimental de arquitecto |
| `presentation` | Respuestas en Markdown y paneles JSON, localizados |
| `offline` | Catálogo de demos, guiones predefinidos, el fixture books-api, contratos de las demos |
| `self_knowledge` | Respuestas sobre el propio Mirag a partir de hechos reales |
| `api` | Servidor HTTP, router, validación de requests, caso de uso de chat |
| `integrations/blockchain` | Identidad Stellar opcional (lazy, nunca tira abajo el servidor) |
| `experimental` | Caché semántica, árbol de conocimiento, router de modelos - con tests, sin conectar |

## Datos de runtime

Todo lo que Mirag escribe va bajo `MIRAG_DATA_DIR` (por defecto `<repo>/var` en un checkout,
`~/.mirag` cuando está instalado): `output/` (el último entregable de un solo archivo),
`artifacts/<id>/` (proyectos generados), `traces/pipeline.jsonl`, `embeddings/` (caché de
vectores remotos). En runtime nunca se escribe en la carpeta del paquete.

## Puntos de extensión

- **Un locale nuevo**: agregar `locales/<xx>/{messages,ui,lexicon,corpus}.json` y
  `knowledge/<xx>/`, y después agregar el código a `SUPPORTED_LOCALES`. Los tests de i18n
  verifican la paridad de claves.
- **Una herramienta nueva**: construir un `FunctionTool` y agregarlo en `tools/builtin.py`.
- **Una etapa de retrieval nueva**: declararla en `features/flags.py`, conectarla en
  `HybridRetriever`, medirla con `benchmarks/calibrate_stages.py` y dejar que decida el gate.
- **Un proveedor de modelos nuevo**: implementar `ChatModel` y pasar un `model_builder` a
  `build_container`.
