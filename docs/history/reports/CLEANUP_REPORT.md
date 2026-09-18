# Fase 5 — Limpieza · $0.00

Cada componente ambiguo recibe **una** de cuatro etiquetas, y ninguna etiqueta se pone a mano sin
algo que la compruebe.

## La tabla

| componente | antes | decisión | después | test |
|---|---|---|---|---|
| `RETRIEVAL_PLAN` | bandera que nadie leía | **conectar** | apagada ⇒ `plan.VACIO`, sin acotar cajas | `test_banderas` sonda `plan de busqueda` |
| `HYBRID_RETRIEVAL` | bandera que nadie leía | **conectar** | apagada ⇒ sin ranking, orden del corpus | sonda: los `ids` cambian |
| `SUFICIENCIA` | bandera que nadie leía | **conectar** | apagada ⇒ `suficiencia.no_evaluado()` | sonda + `apagar_suficiencia_no_finge_cobertura` |
| `METADATA_ROUTING` | conectada | INTEGRATED | sin cambios | sonda: candidatos del filtro |
| `SYMBOL_RETRIEVAL` | conectada | INTEGRATED | sin cambios | sonda: estado del paso |
| `VECTOR_SIGNAL` | conectada, medida peor | INTEGRATED (`auto`→off) | sin cambios | sonda: candidatos de RRF |
| `RERANKER` | conectada, medida mejor | INTEGRATED (`auto`→on) | sin cambios | sonda: `usada` + ranking |
| `GRAPH_RETRIEVAL` | conectada | INTEGRATED (`auto`→off) | sin cambios | sonda con `needs_graph` verificado |
| `MODEL_ROUTING` | bandera con módulo suelto | **EXPERIMENTAL** | solo a mano, y la traza lo dice | `lo_experimental_..._lo_dice_en_el_motivo` |
| `SEMANTIC_CACHE` | bandera sin efecto | **EXPERIMENTAL** | solo a mano | `lo_no_conectado_no_se_enciende_solo` |
| `KNOWLEDGE_TREE` | bandera sin efecto | **EXPERIMENTAL** | solo a mano | idem |
| `CONTEXTUAL_CHUNKS` | bandera sin código | **NO IMPLEMENTADO** | no arranca ni a mano | `lo_no_implementado_no_arranca_ni_a_mano` |
| `COLBERT` | bandera sin código | **NO IMPLEMENTADO** | no arranca ni a mano | idem |
| `eval.cajas_recuperadas` | 0 usos | **REMOVED** | borrada | la suite entera sigue verde |
| `rapido._normalizar_cobertura` | 0 usos | **REMOVED** | borrada | ídem |
| `eval.tokens_de_contexto` | medía el contexto **anterior** a la Fase 2 | **arreglada** | pregunta a `construir_contexto` | 307 casos en verde |
| `arquitecto` | modo público | **EXPERIMENTAL** | etiquetado en UI (Fase 2) | `test_pipeline_unico`: dos modos públicos |
| `cache.py` / `arbol.py` | ISOLATED | **EXPERIMENTAL** | intactos, con sus 47 tests | suites propias |
| `enrutador.RESPALDOS` | parecía dar reintentos | **documentado** | el módulo declara que el reintento es inalcanzable | — |

## El mecanismo, que es lo que importa

`config.ESTADO_FLAGS` declara qué hace cada interruptor, y `test_banderas.py` lo comprueba
**conmutando cada bandera y mirando si cambia el resultado** — no grepeando el código.

Eso obligó a cablear de verdad las tres que había declarado `CONECTADO` sin serlo. Declararlas y no
conectarlas habría sido exactamente el defecto que la tabla existe para impedir, cometido dentro de
la tabla.

Y `config.activar()` cambió: una bandera `EXPERIMENTAL` **jamás se enciende sola**, ni con una
medición favorable, porque no está en el camino de producción. Encendida a mano sí arranca —
experimental es "probalo", no "está tapiado"— pero el motivo que va a la traza dice
`EXPERIMENTAL, encendida a mano (...)` en vez de un `ON` a secas. Una `NO IMPLEMENTADO` no arranca
de ninguna forma.

## Dos sondas que no probaban nada

Vale la pena dejarlas escritas porque son la forma típica de un test que pasa sin comprobar:

- la del **reranker** usaba una consulta cuyo top-3 no se reordena — daba "igual" y parecía bandera
  muerta. De seis consultas probadas, esa era la única que no cambiaba.
- la del **grafo** usaba una consulta con `needs_graph=False`: el grafo no corría en ningún caso.

Corregidas, y la del grafo lleva un `assert` que falla si la consulta deja de pedir grafo.

## Regresión

**307 casos, 16 suites, 0 rojas.** 296 al empezar la fase; los 11 nuevos son `test_banderas.py`.

`test_enrutador.py` se puso rojo a mitad de fase y **no se tocó el test**: la primera versión de la
regla dejaba el enrutador inarrancable incluso a propósito. El test tenía razón y la regla era
demasiado gruesa.
