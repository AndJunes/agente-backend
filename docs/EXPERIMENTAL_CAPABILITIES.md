# Capacidades experimentales

Lo que está aquí **existe, funciona y tiene tests** — y **no está en el camino de producción**.
Ninguna de estas cosas puede aparecer como `VERIFIED` ni influir en una respuesta sin que la traza
lo diga.

## Qué significa cada etiqueta

| etiqueta | qué puede hacer | se enciende sola |
|---|---|---|
| `CONECTADO` | cambiar lo que hace el pipeline | sí, si la medición lo justifica |
| `EXPERIMENTAL` | probarse a mano (`MIRAG_X=on`), con aviso en la traza | **nunca** |
| `NO IMPLEMENTADO` | nada: no hay código detrás | **nunca, ni a mano** |

La diferencia entre las dos últimas importa: *experimental* es "probalo si querés", *no
implementado* es "no hay nada que probar". `config.activar()` las trata distinto y hay tests que lo
fijan.

## Lo experimental, uno por uno

### `arquitecto` — modo de la UI
Orquestación propia en varias fases. Etiquetado `EXPERIMENTAL` en la interfaz con la frase *"Sus
fases no tienen el mismo nivel de verificación que Pipeline."* No se le añadieron validadores ni se
gastó presupuesto en él. Distingue `MODEL CLAIM` de `OBSERVED EVIDENCE` como el resto, pero sus
etapas no pasan por la disciplina de evidencia de la Fase 4.

### `enrutador.py` — elegir modelo por tipo de tarea
El módulo funciona y tiene 13 tests. **No gobierna `agent.llm`.** Y dos cosas que hay que saber
antes de confiar en él:

- Los cuatro modelos de `MODELOS` son **el mismo**, a propósito: cambiarlos sin datos por modelo
  sería elegir a ciegas.
- **El reintento es inalcanzable por construcción.** `respaldos` se calcula quitando el modelo
  elegido de `RESPALDOS`, y como todos los modelos son ese mismo, la lista sale siempre vacía. Está
  escrito en el propio módulo para que nadie lea "hay respaldos" donde dice "hay una lista".

Encenderlo a mano da el motivo `EXPERIMENTAL, encendida a mano (...)`, nunca un `ON` a secas.

### `cache.py` — caché semántica
Existe, 24 tests, no está en el pipeline. Sin medir si ahorra algo sobre el camino real.

### `arbol.py` — knowledge tree
Existe, testeado junto al grafo (23 casos), no está en el pipeline. Sin medir.

### `grafo.py` — expansión por grafo
**Este sí está conectado** (`GRAPH_RETRIEVAL`), con la salvedad de que además exige
`plan.needs_graph`. Calibrado en la Fase 3: añade **+8 trozos por consulta en ~0,1–1 ms** y **no hay
evidencia de que esos 8 ayuden**. A 2 saltos alcanza 17 de 18 cajas, o sea que por sí solo no filtra
nada. En `auto` queda apagado por falta de medición favorable.

Dato secundario de la calibración: de tres consultas multi-hop, el detector `needs_graph` acertó
dos. Falla una de cada tres.

### `COLBERT` y `CONTEXTUAL_CHUNKS`
`NO IMPLEMENTADO`. Son puntos de extensión sin código. No arrancan ni poniéndolos a mano.

## Cómo se comprueba todo esto

`tests/test_banderas.py` (11 casos) verifica la tabla **conmutando cada bandera y mirando si cambia el
resultado** — no leyendo el código fuente, que es justo donde empiezan estas mentiras. Si alguien
declara algo `CONECTADO` y no hace nada, falla. Si añade una bandera sin clasificarla, falla.

Dos sondas fallaron al escribirlas y conviene recordar por qué, porque son la forma típica de
escribir un test que no prueba nada:

- la del **reranker** usaba una consulta cuyo top-3 no se reordena: daba "igual" y parecía que la
  bandera estaba muerta;
- la del **grafo** usaba una consulta con `needs_graph=False`, así que el grafo no corría en ningún
  caso.

Las dos sondas llevan ahora un comentario y la del grafo un `assert` que falla si la consulta deja
de pedir grafo.
