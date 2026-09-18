# Estado actual de Mirag

Una etiqueta por componente, y ninguna puesta a mano sin algo que la compruebe.

`INTEGRADO` está en el camino de producción y hay un test que lo demuestra ·
`CONDICIONAL` corre solo cuando algo lo pide · `EXPERIMENTAL` existe, funciona, **no** está en el
camino · `DESACTIVADO` se midió y perdió · `NO IMPLEMENTADO` no hay código detrás.

## Retrieval y contexto

| componente | estado | evidencia |
|---|---|---|
| `recuperacion.recuperar()` | **INTEGRADO** | fuente única; producción y benchmark la comparten, y hay test de identidad por ids de trozo |
| `construir_contexto()` | **INTEGRADO** | fuente única del prompt; test que falla si alguien vuelve a `rapido._contexto` |
| Tres índices | **INTEGRADO** | 366 trozos distintos; `antipatrones` aporta 150 |
| Filtro de metadatos | **INTEGRADO** | sonda de bandera: cambia los candidatos |
| BM25 | **INTEGRADO** | 0.553 MRR duro frente a 0.469 del IDF anterior |
| RRF | **INTEGRADO, inerte** | passthrough con una sola señal. Es donde entraría el vector |
| Reranker | **INTEGRADO** | +0.082 MRR duro por 0.006 de coste. Con una regresión conocida en paráfrasis (0.490→0.427), escrita, no enterrada |
| Vector local | **DESACTIVADO** | −0.015 MRR y 13× más lento, pese a traer 38% de candidatos nuevos |
| Símbolos | **CONDICIONAL** | solo con `needs_symbols`; 0 ms si no toca; índice cacheado (154→5 ms) |
| Grafo | **INTEGRADO, en auto off** | +8 trozos sin evidencia de que ayuden |
| Plan de recuperación | **INTEGRADO** | apagarlo deja `plan.VACIO`; el detector de código mide 11/11 con 1 falso positivo sobre 49 |
| Suficiencia | **INTEGRADO** | cubierto/mencionado/ausente; sobrevive al modelo real (demo C) |
| Caché semántica, árbol | **EXPERIMENTAL** | existen, 47 tests, fuera del camino |
| Model routing | **EXPERIMENTAL** | no gobierna `agent.llm`; su reintento es inalcanzable por construcción y el módulo lo dice |
| ColBERT, contextual chunks | **NO IMPLEMENTADO** | no arrancan ni a mano |

## Evidencia y verificación

| | estado | evidencia |
|---|---|---|
| Veredicto de 4 estados | **INTEGRADO** | `verde` · `rojo` · `sin_evidencia` · `no_ejecutado`, decididos por la ejecución |
| Marcadores a prueba de truncado | **INTEGRADO** | un `FAIL` enterrado en 12.000 chars ya no desaparece |
| Evidencia por propiedad | **INTEGRADO** | cada `test_id` declarado contra un marcador real |
| Cobertura de anti-patrones | **INTEGRADO, con límite** | los 4 estados alcanzables. **No se puede afirmar que los anti-patrones recuperados apliquen**: BM25 devuelve *k* haya o no relación, y los scores no separan (10.63 irrelevante vs 4.72 relevante). La tabla ya no lo afirma |
| Auditor de afirmaciones | **INTEGRADO** | contradice arriba, deja el texto del modelo entero |
| Bucle de reparación | **INTEGRADO** | como mucho uno; `repair_attempts` sale del estado, no del texto |
| Traza | **INTEGRADO** | 32 campos, con el texto de las propiedades y de la cobertura |

## Producto

| | estado | evidencia |
|---|---|---|
| Panel de evidencia de 4 capas | **INTEGRADO** | `MODEL CLAIM` / `OBSERVED` / `VERIFIED` / `NOT VERIFIED`; test: nada llega a VERIFIED sin declararse |
| Tres demos canónicas | **INTEGRADO** | contrato declarado y comprobado; cumplen también con modelo real ($0.0325) |
| Retrieval en una tarjeta | **INTEGRADO** | 23 tarjetas → 9; las 15 etapas internas detrás de *Ver detalles* |
| Traza legible | **INTEGRADO** | una fila por etapa; test de que al plegar no se pierde tiempo |
| Coste honesto | **INTEGRADO** | `SIMULADO · $0` / `SIN MODELO · $0`, nunca `$0.0000` de un doble |
| Respuesta de código con *qué se hizo* | **INTEGRADO** | antes saltaba de la pregunta a la tabla de evidencia |

## Generación de proyectos

| componente | estado | evidencia |
|---|---|---|
| `ProyectoArtefacto` | **INTEGRADO** | fuente única del workspace, el manifiesto y el ZIP |
| Seguridad de rutas | **INTEGRADO** | 16 ataques rechazados (`../`, absolutas, `~`, NUL, `.env`, `__pycache__`, profundidad) |
| Import roto ≠ dependencia ausente | **INTEGRADO** | solo AST + `sys.stdlib_module_names`; FastAPI → `VALIDADO`, nunca `VERIFICADO` |
| Sonda de CRUD con nonce | **INTEGRADO** | caza un servidor cuyo PUT no persiste |
| Estado global | **INTEGRADO** | `derivar_estado` es la única función que lo decide; hay un test que recorre el AST de los 59 módulos |
| ZIP + gate de integridad | **INTEGRADO** | 13 comprobaciones; 7 manipulaciones rechazadas |
| Registro de artefactos | **INTEGRADO** | ids opacos, aislamiento A/B, descargas concurrentes |
| `GET /descarga` | **INTEGRADO** | el id nunca toca un `Path`; 400/409/410 según el caso |
| `do_HEAD` | **ARREGLADO** | filtraba existencia y tamaño de `.env`; sobrevivió a la auditoría porque los tests usaban GET |

## Interfaz

| | estado |
|---|---|
| Modo `pipeline` | **PRODUCCIÓN** |
| Modo `arquitecto` | **EXPERIMENTAL**, etiquetado en la UI |
| `simple`, `rapido` | **RETIRADOS**: rechazo explícito, no un error |
| Demos offline | **INTEGRADO**: tres preparadas; cualquier otra pregunta → `SIN MODELO` |
| Chips | 12, todos alimentados por eventos del backend |

## Seguridad

| | estado | evidencia |
|---|---|---|
| Servidor | **ARREGLADO** | `127.0.0.1`, lista blanca. `/.env`, `/trazas.jsonl`, `/server.py` → 404 (verificado con curl) |
| `calcular()` | **ARREGLADO** | AST con lista blanca; 9 ataques, 0 colados |
| Intérpretes | **ARREGLADO** | lista construida con `shutil.which()`: `pytest` ya no se ofrece por no existir |
| Persistencia | **ARREGLADO** | limpieza recursiva, anclada; no mata la respuesta si falla |
| Candado de red | **ARREGLADO** | un solo socket, con guarda; `vectores._pedir` lleva la suya |
| Dependencias | **0 externas** | AST de los 47 módulos |

## Tests

**444 casos, 20 suites, 0 rojas.** Sin pytest: cada archivo es su propio runner, 0 llamadas al
modelo.

## Lo que sigue sin resolver

1. **Relevancia del índice de anti-patrones con prompts largos.** Medido y malo. Sin arreglar.
2. **La tabla por familia de `ganancias.json` no se usa en runtime**: `pipeline.ejecutar` siempre
   pasa `familia="general"`. Solo esa fila es load-bearing.
3. **`needs_code=True` no garantiza entrega.** El modelo a veces responde en prosa aunque se le
   ofrezca la herramienta. Observado 1 de 5 en el banco con modelo real.
6. **Acotar por cajas no demostró ganancia a nivel agente**: 1/5 verde en los dos brazos, éxito
   verificado 0.36 (baseline) frente a 0.20, con n=5 — indistinguible del ruido. Sí reduce el
   contexto un 21%.
4. **`arquitecto` sin validar**: experimental por decisión, no por descuido.
5. **El detector `needs_graph` falla una de cada tres** consultas multi-salto.
