# Auditoría contra el temario — estado tras la conversión

Comparación de los documentos contra el temario de 19 cajas (**157 subcategorías**) y contra el formato
`knowledge_item` de 15 campos.

## Antes y después

| | Antes | Ahora |
|---|---|---|
| Cajas | 20 (una fuera del temario) | **19, en el orden y con los nombres del temario** |
| Subcategorías cubiertas | 120 / 157 (76%) | **157 / 157** |
| Parciales | 35 | 0 |
| Ausentes | 2 | 0 |
| Campos del esquema explícitos | 4 / 15 | **15 / 15** |
| Documentos con fuentes | 1 / 20 | **19 / 19** |
| Líneas | 5.123 | **8.735** |
| Fichas (knowledge_items con los 15 campos) | 0 | **228** |
| Bloques de código | 59 | **105** |

## Qué se añadió, por caja

| Caja | Secciones nuevas |
|---|---|
| 01 Fundamentals | `tests` (property-based y cómo probar concurrencia) · patrones de concurrencia (worker pool, fan-out/in, pipeline) · tabla de latencias como ítem propio · consistent hashing implementado |
| 02 Web & Protocols | `implementations` (nginx, middleware y su orden) · `constraints` (tabla de límites y timeouts) · `failure_modes` (502/504/reset/TLS) |
| 03 APIs | endpoint completo de principio a fin · cómo falla una API en producción |
| 04 Databases | **joins, agregaciones, window functions y CTEs recursivas** · qué cambia entre Postgres/MySQL/Mongo/Redis · fallos incluida la corrupción silenciosa |
| 05 Architecture | **coupling y cohesion** (nunca se habían definido) · estructuras de carpetas reales con test de arquitectura · `constraints` (equipo, presupuesto, legacy, strangler fig) · cómo falla una arquitectura |
| 06 Security | pila de seguridad en código (authn/authz/RLS) · `constraints` (cumplimiento y threat modeling con STRIDE) · cómo falla en la práctica · respuesta a incidentes de seguridad |
| 07 Payments | flujo completo de un cobro en código, con conciliación · cómo falla un sistema de pagos |
| 08 Distributed Systems | **esquema y versionado de eventos** · productor con outbox y consumidor idempotente en código · cómo falla un sistema distribuido |
| 09 Performance | las técnicas en código (single-flight, batching, bulkhead, streaming) · diagnosticar un incidente · orden de intervención al escalar |
| 10 Reliability | health checks y graceful shutdown en código · circuit breaker implementado · debugging de incidentes · data recovery |
| 11 Testing | `failure_scenarios` (casos adversariales, tests de IDOR y de idempotencia, fuzzing) |
| 12 Observability | instrumentación con OpenTelemetry en código · qué monitorizar y qué señal delata cada fallo |
| 13 Cloud & Infrastructure | volúmenes y estado en contenedores · coste (dónde se va el dinero) |
| 14 DevOps | checklist de despliegue · checklist de producción de un servicio nuevo |
| 15 Files & Data | cómo falla el manejo de archivos · consistencia entre archivo y registro |
| 16 Integrations | cómo falla una integración · fiabilidad heredada de las dependencias |
| 17 Business Logic | **entidades y agregados** · inconsistencias de negocio y verificación de invariantes |
| 18 AI Backend | **embeddings** como ítem propio · cómo falla un sistema de IA |
| 19 System Design | **ADRs** con plantilla · **diagramas** (C4 y secuencia) |

## Los dos desajustes estructurales, resueltos

1. **La caja 20 (Producción) se disolvió** en devops (checklists), reliability (debugging, recovery),
   observability (monitorización), performance (incidentes y escalado), cloud (coste) y security
   (incidentes de seguridad). Ya no hay solapamiento con reliability.
2. **Cajas autocontenidas vs referencias cruzadas:** se optó por **referencias**. Cada concepto se
   desarrolla en una sola caja y las demás enlazan con `[NN]`. Las subcategorías que el temario pide por
   caja (`constraints`, `failure_modes`, `implementations`) ahora **sí existen en cada caja**, pero
   tratando lo específico de esa caja en lugar de repetir lo de otra.

## Efecto en el RAG

| | Antes | Ahora |
|---|---|---|
| Trozos | 212 | 271 |
| Tamaño mediano | 1.196 car. | 1.853 car. |
| top-1 | 21/23 | **28/31** |
| recall@3 | 22/23 | **30/31** |

El único fallo del set de prueba: *"cómo se escribe un ADR"* devuelve la caja 05 (que los menciona) en vez
de la 19 (que los desarrolla). El resultado sigue siendo relevante, pero es un caso donde dos cajas
compiten por el mismo término.
