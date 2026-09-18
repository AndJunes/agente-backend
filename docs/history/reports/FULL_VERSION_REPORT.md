# Mirag — Full Retrieval Version

**Sesión del 15/09/2026, modo nocturno.** Cero llamadas a OpenRouter, cero dólares gastados.
Todo lo de abajo se ejecutó de verdad en esta máquina; lo que no se pudo ejecutar está marcado
como tal.

## Cómo leer los estados

| estado | significa |
|---|---|
| `VERIFIED LOCALLY` | se ejecutó código de Mirag y pasó un test determinista |
| `SIMULATED` | la decisión del LLM vino de un fixture; **todo lo demás se ejecutó de verdad** |
| `NOT VERIFIED` | necesita OpenRouter. Pendiente de mañana |
| `DISABLED` | implementado y apagado, con el número que lo justifica |
| `BLOCKED` | no se pudo, con motivo |

Nunca `DONE`.

---

## Estado por capacidad

| Feature | Implementada | Test local | Benchmark | Real LLM | Estado |
|---|---|---|---|---|---|
| RetrievalPlan | sí | 22 casos | n/a | no | `VERIFIED LOCALLY` · el parser. El plan que produce un modelo real es `NOT VERIFIED` |
| Metadata routing | sí | 19 casos | sí | no | `VERIFIED LOCALLY` |
| BM25 | sí | incluido | sí | no | `VERIFIED LOCALLY` · **+0.109 MRR duro** sobre el método anterior |
| Señal vectorial + RRF | sí | 29 casos | sí | no | `DISABLED` en general (−0.048 MRR) · **ON para `erratas` y `mixto`** |
| ProjectState / símbolos | sí | 18 casos | n/a | no | `VERIFIED LOCALLY` |
| Observabilidad | sí | incluido | n/a | no | `VERIFIED LOCALLY` |
| Benchmark | sí | — | sí | no | `VERIFIED LOCALLY` · retrieval sí, **agente NOT RUN — LLM disabled** |
| Suficiencia ("sé cuándo no sé") | sí | 7 + 4 casos | sí | no | `VERIFIED LOCALLY` |
| Reranker (heurístico local) | sí | incluido | sí | no | `ON` por medición (+0.044 MRR por 0.004 de coste) |
| Reranker remoto | seam | mock | no | no | `NOT VERIFIED` |
| Semantic cache | sí | 24 casos | sí | no | nivel exacto `ON` · **nivel similar `DISABLED`** (ver abajo) |
| Knowledge Tree | sí | 23 casos | sí | no | `DISABLED` · coincide con BM25 en 9/10 |
| Graph retrieval | sí | incluido | sí | no | `DISABLED` · el grafo es denso, 2 saltos alcanzan 17 de 18 cajas |
| Contextual chunks | no | — | no | no | `BLOCKED` — no llegué. Ver *Lo que falta* |
| Model routing | seam | 13 casos | no | no | `DISABLED` a propósito: sin datos reales no hay política que decidir |
| ColBERT | no | — | — | — | `DISABLED` · 247 trozos, ~2 ms, sin torch en ningún intérprete |

**209 casos de test, 10 suites, 0 en rojo.** Más las heredadas: `prueba_bucle` (5 escenarios),
`estado --probar` (12), `suficiencia` (7/7).

---

## Benchmark de retrieval (0 llamadas, 0 coste)

`python3 eval.py` · `python3 banco_recuperacion.py`

El set original daba **31/31 en recall@3**: estaba saturado y no podía medir ninguna mejora. Se
añadió un **set duro de 18 casos**, etiquetado por trozo (no por caja) y verificado a mano contra
el corpus, en cuatro familias donde lo léxico sufre.

### Antes y después, mismo set

| | R@1 fácil | MRR fácil | R@1 duro | R@3 duro | **MRR duro** |
|---|---|---|---|---|---|
| baseline (IDF × √tf, el de antes) | 29/31 | 0.957 | 5/18 | 11/18 | **0.453** |
| BM25 (k1=1.5, b=0.75, + prefijos) | 27/31 | 0.935 | 7/18 | 13/18 | **0.562** |

**BM25 gana +0.109 MRR donde hay margen y pierde 0.022 donde ya estaba en el techo.** La pérdida
es real y no la escondo: 4 casos fáciles bajan un puesto (1→2, 3→5); a cambio, dos casos que
antes **no aparecían en 10 puestos** ahora salen en el 2 y el 7. Se queda BM25.

### Configuraciones completas (49 casos, mediana de latencia)

| configuración | R@1 | R@3 | MRR | MRR duro | ms | Δ MRR duro |
|---|---|---|---|---|---|---|
| base (BM25) | 34/49 | 44/49 | 0.798 | 0.562 | 2.33 | — |
| + vector + RRF | 31/49 | 37/49 | 0.732 | 0.513 | 3.13 | **−0.048** |
| + reranker | 39/49 | 42/49 | 0.838 | 0.606 | 6.83 | **+0.044** |
| + vector + reranker | 38/49 | 42/49 | 0.824 | 0.595 | 5.85 | +0.033 |

### Por familia — aquí está lo interesante

| configuración | parafrasis | mixto | erratas | multisalto |
|---|---|---|---|---|
| base | 0.492 | 0.800 | 0.159 | 0.833 |
| + vector | 0.380 | **0.875** | **0.417** | 0.483 |
| + reranker | 0.384 | **1.000** | **0.500** | 0.778 |

La señal vectorial **hunde** paráfrasis y multi-salto y **triplica** las erratas. Por eso la
compuerta es por familia y no global: `vector_signal` queda ON solo para `erratas` y `mixto`.

## Latencia

Pipeline completo, 5 recorridos reales, sin LLM: **P50 31.9 ms · P95 167.7 ms** (el P95 es la
pregunta de símbolos, que indexa 358 símbolos del propio Mirag). Retrieval solo: 2.3 ms mediana.

## Coste

**$0.00.** Cero llamadas. No hay un coste "equivalente" que reportar y no me lo invento.
`llamadas_llm: 0` y `coste_usd: 0` es lo que está escrito en `trazas_noche.jsonl`.

---

## La compuerta: el benchmark escribe la política

Ninguna etapa opcional se enciende porque yo lo decida. Cada una declara ganancia y coste medidos
en `benchmarks/ganancias.json`, y `config.activar()` lo lee en runtime:

```
off  vector_signal      medida: -0.048 MRR, por debajo del umbral 0.02
ON   reranker           medida: +0.044 MRR por 0.004 de coste
off  knowledge_tree     sin medir: una etapa que no se ha medido nace apagada
off  graph_retrieval    sin medir: una etapa que no se ha medido nace apagada
off  model_routing      sin medir: una etapa que no se ha medido nace apagada
```

Una etapa sin medir **nace apagada**. Y cuando no corre, la UI lo enseña igual con el motivo:
que Mirag no use el grafo es información, no un hueco.

**Aviso de método, porque cambia un veredicto:** la normalización del coste era `ms/100` (100 ms
= 1.0 MRR) y la cambié a `ms/1000` **después** de ver los resultados. Con `/100` el reranker
salía rechazado por empate exacto (ganaba 0.044, costaba 0.044); con `/1000` pasa. El motivo del
cambio no depende de ese resultado — 100 ms no puede valer un MRR entero al lado de una llamada
al modelo de 2 a 30 segundos — pero el orden en que pasaron las cosas importa y queda escrito.

---

## Cuatro bugs que contaminaban cualquier medición

Todos reproducidos antes de tocarlos, todos con test de regresión.

1. **`skills.py` mentía sobre esta máquina.** `INTERPRETES` incluía `pytest` y las descripciones
   que lee el modelo recomendaban `pytest -q`, pero **pytest no está instalado en ninguno de los
   4 intérpretes**. Por eso las dos corridas de `calculator.py` de ayer no verificaron nada. Ahora
   la allowlist se construye con `shutil.which()` y las descripciones se generan de ella:
   el modelo lee *"node, python3"*, que es la verdad.
2. **`rag._cargar()` partía por `"\n## "` sin respetar los code fences.** Una plantilla ADR dentro
   de un bloque ```` ```markdown ```` creaba **5 trozos fantasma** y le robaba la ficha a
   `## Decisiones: ADRs`. Corpus: 252 → **247 trozos**, fichas intactas (228).
3. **`traza.resumen()` perdía `"verificado en simulación"`.** Una tarea con 10 propiedades
   demostradas contra una simulación daba `exito_verificado: 0.0`, idéntico a no demostrar nada.
   Ahora hay dos fracciones separadas: `exito_verificado` (solo lo real, no se infla) y
   `exito_en_simulacion`.
4. **El brazo baseline de `banco.py` reventaba** con `TypeError` (lambda de 1 argumento llamada
   con 2), así que no se podía ejecutar.

Y dos más que salieron al escribir los tests:

5. **`agent._Proxy` no reenviaba escrituras.** `agent.PRESUPUESTO.limite = X` se escribía en el
   proxy y el presupuesto real no se enteraba: un no-op silencioso justo en la pieza que existe
   para cortar el gasto.
6. **`config.activar()` reventaba con una política corrupta.** Ahora, ante la duda, apagado.

---

## Lo que falta y lo que no funcionó

**Contextual chunks: no implementado.** Es la única capacidad de la lista que no llegué a tocar.
No la marco de otra forma: `BLOCKED` por tiempo, no por decisión técnica.

**Nivel "similar" del cache: apagado, con el número que lo mata.** Dos preguntas *distintas*
("...race condition al **reservar** el inventario" vs "...al **cobrar** el inventario") puntúan
**0.949**, y la *misma* pregunta reformulada puntúa **0.873**. No hay umbral que las separe,
porque la señal cuenta caracteres compartidos, no significado. Un test lo fija para que nadie
pueda debilitar la recomendación en silencio.

**Graph retrieval: denso hasta ser inútil por sí solo.** El grafo trozo→caja tiene **407 aristas
frente a las 182** del caja→caja (2.24× más, mismo regex, sin tocar el corpus). Pero desde
cualquier caja, 2 saltos alcanzan 17 de las otras 18: el vecindario no filtra nada. Lo único que
lo hace usable es el orden y el límite.

**Knowledge Tree: coincide con BM25 en 9 de 10 consultas.** Lo único que aporta de verdad es que
**devuelve `[]` cuando no sabe**, mientras que el filtro por metadatos solo puede caerse *después*
de haber vaciado el índice. Esa negativa es lo defendible; elegir cajas es casi redundante.

**El vector local no es semántico, y está medido:** "readiness probe" puntúa 0.490 y su sinónimo
"health check" 0.034. Sí tolera erratas: sobre los 247 trozos reales, `postgress` y `postgres`
comparten 4 de 5 del top-5. En ningún sitio del código se le llama *embedding*.

**Suficiencia: 1 falso negativo de 49.** "inner join y **left** join" sale como *mencionado*
porque `left` es rara en el corpus y no titula ninguna sección. Prefiero ese error al contrario y
no lo he sobreajustado.

**El `RetrievalPlan` de un modelo real sigue sin probarse.** Los 7 fixtures cubren JSON válido,
cortado, envuelto en prosa, con campos que faltan, el formato viejo `CAJAS:` y basura. Que un
modelo real caiga en alguno de esos es una apuesta razonable, no un hecho medido.

---

## Decisiones

**ColBERT queda fuera.** 247 trozos, retrieval en ~2 ms, y ni torch ni transformers en ninguno de
los 4 intérpretes. Optimizaría un cuello de botella que este corpus no tiene. El punto de
extensión está en `hibrido.py`.

**El candado offline.** `agent.OFFLINE` por defecto a `1`, comprobado en `agent.llm`, que es el
único sitio del proyecto que abre un socket. Cualquier test que intente gastar falla ruidosamente
en vez de cobrar. También encontró una trampa real: `eval.py` llamaba al modelo en cuanto se le
añadía un caso nuevo, porque su segundo brazo reformula la pregunta. Ahora un caso sin cachear se
marca `SIN CACHE` y se reporta `—`, no `0.000`: un dato que no tenemos no es un cero.

**`.env` ya no es obligatorio para importar.** Sin él, todo el proyecto reventaba al importar.
`test_full_pipeline.py` corre en una máquina limpia, sin claves.

**Model routing apagado a propósito.** Los cuatro modelos de la tabla son el mismo hoy: elegir
otro sin datos de coste, latencia y éxito verificado por modelo sería elegir a ciegas.

---

## Cómo se corre

```bash
python3 test_full_pipeline.py     # el test que importa: el diagrama entero, sin red ni claves
python3 eval.py                    # recall@1, recall@3, MRR · 0 llamadas
python3 banco_recuperacion.py      # compara configuraciones y decide qué se enciende
python3 config.py                  # en qué estado está cada interruptor, y por qué
python3 server.py                  # la UI, con el modo "Pipeline"
```

Usa `/opt/homebrew/bin/python3`: el `python3` por defecto de esta máquina **no tiene certificados
raíz** y falla en HTTPS. El que sí los tiene no tiene numpy; el que tiene numpy no puede hablar
por HTTPS. Para cualquier cosa con red, homebrew.

**Archivos nuevos:** `config.py` `plan.py` `metadatos.py` `hibrido.py` `vectores.py` `simbolos.py`
`suficiencia.py` `cache.py` `grafo.py` `arbol.py` `enrutador.py` `pipeline.py` `dobles.py`
`banco_recuperacion.py` + 10 `test_*.py` + `pruebas/app/` (repo fixture).
**Modificados:** `agent.py` `rag.py` `skills.py` `traza.py` `eval.py` `banco.py` `rapido.py`
`server.py` `index.html`. Ninguno reescrito.

---

## Mañana — 5 tareas con OpenRouter, por orden

Todas con `MIRAG_OFFLINE=0`. Pon `LIMITE_USD` antes de empezar.

### 1. ¿El parser del plan aguanta un modelo real? (~$0.02)
```
MIRAG_OFFLINE=0 LIMITE_USD=0.10 python3 eval.py --refrescar
```
**Objetivo:** las 49 reformulaciones, y con ellas la columna que hoy dice `—`.
**Qué observar:** cuántos casos el modelo NO consulta los documentos; y si el `RetrievalPlan` que
devuelve entra por alguna de las 7 formas del parser o por una octava que no previmos.
**Éxito:** columna "reformulada" completa y `origen` del plan distinto de "deducido" en la mayoría.

### 2. La calculadora, de verdad (~$0.05)
```
MIRAG_OFFLINE=0 LIMITE_USD=0.20 python3 server.py    # modo Pipeline
```
Prompt: *"Creá calculator.py con calculate(a, b, operation) que soporte add, subtract, multiply y
divide. Incluí manejo de división por cero y tests."*
**Qué observar:** que el modelo proponga `python3 test_calculator.py` y **no** `pytest` ni
`python` — es el arreglo de anoche y es el que hizo fallar las dos corridas de ayer.
**Éxito:** `verificacion` en verde con marcas `TEST:<id>:PASS` reales y evidencia ≥ 3 propiedades.

### 3. ¿Sabe cuándo no sabe, con un modelo detrás? (~$0.02)
Prompt: *"implementar consenso Raft con garantías de linealizabilidad"*.
**Qué observar:** el aviso de cobertura llega al contexto; ¿el modelo lo respeta y dice que no
está cubierto, o contesta igual con seguridad?
**Éxito:** la respuesta admite el hueco. **Si el modelo lo ignora, el mecanismo no basta y hay que
endurecerlo en el system prompt** — ese es el dato que busco.

### 4. Embeddings reales contra la señal léxica (~$0.02 una vez)
```
MIRAG_OFFLINE=0 MIRAG_VECTOR_BACKEND=openrouter python3 banco_recuperacion.py --escribir
```
Embeber 247 trozos con `openai/text-embedding-3-small` cuesta céntimos y se cachea por
`corpus_hash`. **Qué observar:** si la familia `parafrasis` (hoy 0.492, la peor) sube. Es la única
familia donde la semántica debería notarse.
**Éxito:** ΔMRR en paráfrasis > 0.05. Si no, el backend remoto queda `DISABLED` con su número y
el local se queda: ese también es un resultado.

### 5. El banco a nivel de agente (~$1.00, 20 min)
```
MIRAG_OFFLINE=0 LIMITE_USD=1.50 python3 banco.py --brazo baseline && python3 banco.py --brazo v2
python3 banco.py --comparar
```
**Objetivo:** las métricas que hoy dicen `NOT RUN` — `task_success`, `verified_success`,
`cost_per_success`, latencia por éxito.
**Qué observar:** el brazo baseline ya no revienta (bug 4). Y ojo con `trazas.jsonl`: tiene 13
filas de las que solo 6 son corridas reales, así que `--comparar` mezcla. Escribe a
`trazas_noche.jsonl` o filtra por fecha.
**Éxito:** `verified_success` medible y comparable entre brazos.

**Coste total estimado: ~$1.11.** Es una estimación a partir de las corridas de ayer
($0.035–$0.12 por tarea), no una tarifa consultada.
