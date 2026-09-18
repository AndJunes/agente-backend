# Mirag — Auditoría de realidad

**Fecha:** 15/09/2026 · **Método:** ejecución, no lectura. Toda afirmación de este informe está
respaldada por un comando cuya salida está en `PROJECT_RUNTIME_EVIDENCE.md`.

**No se dio por buena** ninguna documentación, ningún nombre de archivo, ningún comentario y
ningún test que no se ejecutara. `FULL_VERSION_REPORT.md` (escrito ayer por mí mismo) se trató
como una afirmación a verificar, no como una fuente; **tres de sus afirmaciones resultaron falsas**
y están marcadas abajo.

---

## ⚠️ DOS COSAS QUE HAY QUE ARREGLAR HOY, ANTES DE SEGUIR

### 1. El servidor sirve tu API key a toda la red local — AHORA MISMO

```
$ curl -s -o /dev/null -w "%{http_code} %{size_download}" http://127.0.0.1:8000/.env
200 93
$ curl -s http://127.0.0.1:8000/.env
OPENROUTER_API_KEY=<REDACTADO — la clave real se sirve entera>
```

`server.py:102` hereda `SimpleHTTPRequestHandler` sin `directory=`, así que el document root es el
cwd — el mismo directorio donde vive `.env`. Y `server.py:198` hace
`ThreadingHTTPServer(("", 8000), ...)`: `""` es **0.0.0.0**, todas las interfaces, sin auth.

Cualquiera en tu misma Wi-Fi hace `curl http://<tu-ip>:8000/.env` y se lleva la clave. También se
sirven `trazas.jsonl` (200, 5.802 bytes — tus prompts), `index.html.bak` y `eval_cache.json`.

**Arreglo mínimo:** `ThreadingHTTPServer(("127.0.0.1", 8000), ...)`.

### 2. `skills.calcular` es `eval()` sobre texto que controla el modelo, en el proceso del servidor

```python
skills.py:144-145
def calcular(expresion: str) -> str:
    return str(eval(expresion))  # demo local; en produccion nunca uses eval
```

Está registrada en `SKILLS` y en `TOOLS`, o sea que el modelo puede invocarla en modo simple.
`__import__('os').environ['OPENROUTER_API_KEY']` es una "expresión aritmética" válida para esta
función. Sin subproceso, sin timeout, sin aislamiento — a diferencia de `verificar_codigo`, que al
menos tiene las tres cosas.

*(La auditoría fue read-only por tu instrucción, así que no toqué ninguna de las dos.)*

---

## 3. EL HALLAZGO ESTRUCTURAL: el benchmark mide un pipeline que el agente no usa

Existen **dos stacks de retrieval independientes**, y el que se mide no es el que alimenta al modelo.

| | Stack A — `hibrido.recuperar()` | Stack B — `rapido.recuperar()` |
|---|---|---|
| qué hace | filtro de metadatos → BM25 → vector? → RRF → reranker? | 3 llamadas sueltas a `rag.buscar` / `buscar_antipatrones` / `buscar_fallos` |
| quién lo mide | `banco_recuperacion.py:65` | **nadie** |
| quién lo gobierna | `config.py` + `benchmarks/ganancias.json` | nada: sin flags, sin umbrales |
| **qué llega al modelo** | **nada** | **todo** |

En `pipeline.py:132` se llama a `hibrido.recuperar()`, y su salida (`recuperados`) se usa en
exactamente dos sitios: `suficiencia.evaluar()` (:181) y `grafo.expandir()` (:169, que nunca
corre). El contexto que se le manda al modelo se reconstruye desde cero en `pipeline.py:188-189`
con `rapido.recuperar()` + `rapido._contexto()`.

**Comprobado empíricamente, no deducido** — mismo prompt, reranker ON y OFF, capturando el
`messages[-1]["content"]` real:

```
contexto con reranker ON : 8,535 caracteres · sha 00cb0796ccc4dfb6
contexto con reranker OFF: 8,535 caracteres · sha 00cb0796ccc4dfb6
¿IDENTICOS? SI — el reranker NO afecta a lo que ve el modelo
```

**Consecuencias concretas:**

- El reranker es la **única** etapa condicional encendida, justificada con `+0.0441 MRR` en
  `ganancias.json`. Esa mejora se aplica a un ranking que solo ve `suficiencia.evaluar`.
- Toda la comparativa de `FULL_VERSION_REPORT.md` (BM25 vs IDF, vector, RRF) describe un camino
  que ningún usuario recorre.
- Los cuatro modos toman su contexto del Stack B: `simple` vía tool calls del modelo a
  `skills.buscar_en_docs`, `rapido` en `rapido.py:253`, `pipeline` en `:188`, `arquitecto` vía
  tool calls.

**Discrepancia con la documentación:** `FULL_VERSION_REPORT.md` afirma *"BM25 gana +0.109 MRR"* y
presenta la tabla como si describiera el pipeline. Describe Stack A. El texto no es falso sobre lo
que midió; es falso sobre **a qué se aplica**.

---

## 4. Segundo hallazgo crítico: seguir las instrucciones del proyecto lo rompe

`rapido.guardar()` (`rapido.py:192-204`) vacía `salida/` con `viejo.unlink()`. `unlink()` **no
borra directorios**. ¿Cómo aparece un directorio ahí? Ejecutando el test generado — que es
literalmente lo que dice `salida/COMO_EJECUTAR.txt`.

Reproducción limpia en un tempdir:

```
1. guardar() → ['COMO_EJECUTAR.txt', 'm.py', 'test_m.py']
2. el usuario ejecuta lo que dice COMO_EJECUTAR.txt → [..., '__pycache__', ...]
3. siguiente tarea: ROTO → PermissionError: Operation not permitted: '.../__pycache__'
```

La excepción sale **después** de la llamada al modelo y después de verificar, en
`pipeline.py:279` / `server.py:145,171`. El usuario paga, el código se genera y se verifica, y
entonces todo se descarta con `Error: PermissionError: ...` en el navegador. **El trabajo se
pierde entero.** Y no se recupera solo: `salida/__pycache__` persiste, así que *todas* las tareas
de código siguientes fallan igual.

Esto rompió `test_full_pipeline.py` durante esta misma auditoría (exit=1). Es la prueba de que no
es teórico.

---

# 1. INVENTARIO REAL

36 archivos `.py` · 8.161 líneas · **cero dependencias externas** (verificado: no existe
`requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` ni `package.json`, y ningún import de
terceros en ningún archivo).

| Componente | Existe | Se importa | Se ejecuta en una petición | Estado |
|---|---|---|---|---|
| `agent.py` | Sí | 20 módulos | Sí | **VERIFIED** |
| `rag.py` | Sí | 18 módulos | Sí | **VERIFIED** |
| `skills.py` | Sí | 8 módulos | Sí | **VERIFIED** |
| `server.py` | Sí | — (entrypoint) | Sí | **VERIFIED** |
| `pipeline.py` | Sí | server:149 | Sí (modo por defecto) | **VERIFIED** |
| `rapido.py` | Sí | server, pipeline | Sí | **VERIFIED** |
| `arquitecto.py` | Sí | server:175 | Sí (modo arquitecto) | **CONNECTED BUT UNVERIFIED** |
| `estado.py` | Sí | server:121, pipeline:116 | Sí | **VERIFIED** |
| `auditoria.py` | Sí | server:187, agent:219 | Sí, los 4 modos | **VERIFIED** |
| `plan.py` | Sí | pipeline:126 | Sí | **PARTIAL** (solo `deducir`; `leer` nunca se llama en runtime) |
| `metadatos.py` | Sí | hibrido:127 | Sí | **PARTIAL** (filtra Stack A, que no llega al modelo) |
| `suficiencia.py` | Sí | pipeline:181 | Sí | **VERIFIED** |
| `hibrido.py` | Sí | pipeline:132 | Sí, pero su salida no llega al modelo | **ISOLATED (de facto)** |
| `traza.py` | Sí | pipeline, rapido | Sí | **VERIFIED** |
| `config.py` | Sí | 6 módulos | Sí (6 de 13 flags) | **PARTIAL** |
| `simbolos.py` | Sí | pipeline:149 | Condicional (`needs_symbols`) | **CONNECTED BUT UNVERIFIED** |
| `dobles.py` | Sí | **server:155** | Sí, cuando `MIRAG_OFFLINE=1` | **MOCKED, en producción** |
| `vectores.py` | Sí | hibrido:106 | **No** (flag OFF por medición) | **DISABLED** |
| `grafo.py` | Sí | pipeline:168 | **No** (flag OFF, sin medir) | **ISOLATED** |
| `arbol.py` | Sí | solo tests | **No** | **ISOLATED** |
| `cache.py` | Sí | solo tests | **No** | **ISOLATED** |
| `enrutador.py` | Sí | solo tests | **No** | **ISOLATED** |
| `banco.py` | Sí | solo tests | No (script) | **ISOLATED** |
| `banco_recuperacion.py` | Sí | nadie | No (script) | **ISOLATED** |
| `eval.py` | Sí | banco_recuperacion | No (script) | **ISOLATED** |
| `prueba_bucle.py` | Sí | nadie | No (script) | **ISOLATED** |
| `index.html` | Sí | servido por GET | Sí | **VERIFIED** |
| `conocimientos/` (19 cajas) | Sí | rag:83 | Sí | **VERIFIED** (247 trozos, 228 fichas) |
| `pruebas/app/` (fixture) | Sí | test_simbolos | No | fixture de test |
| `benchmarks/ganancias.json` | Sí | config:61 | Sí | **VERIFIED** |
| `benchmarks/comparativa.json` | Sí | **nadie** | No | **ISOLATED** |
| `benchmarks/baseline.json`, `final.json` | Sí | **nadie** | No | **ISOLATED** |
| `embeddings/` | **No existe** | — | — | **MISSING** (consistente: `VectorOpenRouter` nunca corrió) |

---

# 2. ARQUITECTURA REAL

## Flujo principal (modo `pipeline`, el default desde hoy)

```
USER (index.html:628, POST /chat)
  → server.do_POST (server.py:110)
  → estado.responder(pregunta) (server.py:121)        ← ATAJO: corta aquí si acierta, 0 llamadas
  → pipeline.ejecutar (server.py:164)
      → estado.responder otra vez (pipeline.py:116)   ← inalcanzable: server ya lo hizo
      → plan.deducir (pipeline.py:126)                ← determinista, 0 llamadas
      → hibrido.recuperar (pipeline.py:132)           ← SU SALIDA NO LLEGA AL MODELO
          → metadatos.filtrar → rag._ranking_bm25 → [vector OFF] → RRF → reranker
      → simbolos.indexar/buscar (pipeline.py:149)     ← solo si plan.needs_symbols
      → [grafo: nunca]
      → suficiencia.evaluar (pipeline.py:181)         ← consume la salida de hibrido
      → rapido.recuperar + _contexto (pipeline.py:188) ← EL CONTEXTO REAL SALE DE AQUI
      → agent.llm (pipeline.py:217)                   ← 1 llamada (o un doble si OFFLINE)
      → _leer_entrega → _verificar → rapido._evidencia (pipeline.py:224-262)
      → rapido.guardar (pipeline.py:279)              ← PUNTO DE FALLO, ver §4
      → traza.escribir → trazas_noche.jsonl
  → auditoria.aplicar (server.py:188)                 ← los 4 modos
  → SSE {tipo:"paso"}* + {tipo:"fin"} → index.html
```

## Flujos secundarios

| Modo | Entrada | Retrieval real | Evidencia | Estado |
|---|---|---|---|---|
| `simple` | `agent.run` (server:180) | tool calls del modelo → `rag.buscar*` | solo `auditoria` | **VERIFIED** |
| `rapido` | `rapido.implementar` (server:138) | `rapido.recuperar` | `_evidencia` completa | **VERIFIED** |
| `pipeline` | `pipeline.ejecutar` (server:164) | `rapido.recuperar` (¡no hibrido!) | `_evidencia` + `suficiencia` | **VERIFIED** |
| `arquitecto` | `arquitecto.disenar` (server:175) | tool calls → `rag.buscar*` | prosa + 1 check real | **CONNECTED BUT UNVERIFIED** |
| offline | `server.py:155` instala un doble | igual | igual | **MOCKED** |

## Código muerto o solo parcialmente conectado

- **Funciones con cero referencias:** `eval.cajas_recuperadas` (eval.py:166),
  `rapido._normalizar_cobertura` (rapido.py:176).
- **Módulos solo alcanzables desde tests:** `cache.py`, `arbol.py`, `enrutador.py`, `banco.py`.
- **`estado.responder` duplicado:** `server.py:121` y `pipeline.py:116`. El segundo es inalcanzable
  por la web porque el primero ya cortó.
- **`rapido_a_pasos`** (`server.py:14-62`) construye una lista `pasos` de 4-5 diccionarios en cada
  petición `rapido` y **la tira** (`server.py:139` se queda solo con `["respuesta"]`). Los pasos
  que ve el navegador vienen del callback `al_avanzar`.
- **`rapido.guardar` se llama 2-3 veces por petición** (server:26, server:145 o 171,
  pipeline:279): escribe el mismo entregable varias veces.
- **`rag._ranking_idf`** (rag.py:141) solo es alcanzable cuando `banco_recuperacion` cambia
  `rag.METODO` a mano.

---

# 3. ESTADO DE CADA FEATURE

| Feature | Estado | Por qué |
|---|---|---|
| Bucle del agente (`agent.run`) | **VERIFIED** | ejecutado en `prueba_bucle.py` (5 escenarios) y en los 10 casos manuales |
| Candado de gasto (`MIRAG_OFFLINE`) | **VERIFIED** | `test_cimientos` lo prueba en 4 casos; comprobado que `agent.OFFLINE=True` por defecto |
| Presupuesto por hilo | **VERIFIED** | `test_resiliencia.presupuesto_agotado_para_seguro` |
| Auditor de afirmaciones | **VERIFIED** | 15 casos en `test_auditoria`, + reproducción del bug original |
| Veredicto del ejecutor (4 estados) | **VERIFIED** | 6 casos ejecutados, incluido `pass` → `sin_evidencia` |
| Evidencia por marcadores | **VERIFIED** | caso manual 3 (3 verificadas) y 4 (1 refutada) |
| Suficiencia (sé cuándo no sé) | **VERIFIED** | 7/7 graduados, 1/49 falsos negativos, casos manuales 6 y 7 |
| ProjectState / atajos | **VERIFIED** | 13 casos en `estado.py --probar`, incluidas 6 órdenes de trabajo |
| BM25 | **PARTIAL** | implementado y medido, pero solo gobierna Stack A; el contexto del modelo usa `rag.buscar` con el mismo `_ranking`, así que el algoritmo sí llega — el *pipeline* de fusión no |
| Metadata filtering | **PARTIAL** | filtra Stack A (no llega al modelo). En Stack B solo se pasan `plan.domains` como `cajas` |
| Señal vectorial + RRF | **DISABLED** | flag OFF por medición (−0.0481 MRR). Nunca se instancia en runtime |
| Reranker (heurístico local) | **ISOLATED de facto** | flag ON, se ejecuta, y **no cambia el contexto del modelo** (SHA idéntico) |
| Reranker remoto | **PLACEHOLDER** | no existe implementación; solo se menciona en comentarios |
| Contextual chunks | **MISSING** | flag declarado en `config.py:45`, cero implementación, cero lectores |
| Symbol retrieval | **CONNECTED BUT UNVERIFIED** | corre (caso manual 8: 358 símbolos), pero depende de `plan.needs_symbols`, que solo un modelo real pone a `True`. Con dobles nunca se activa por esa vía |
| Semantic cache | **ISOLATED** | 417 líneas, 24 tests, **cero importadores en runtime**. Nivel "similar" OFF con medición que lo justifica |
| Knowledge Tree | **ISOLATED** | `arbol.py` completo y testeado, ningún importador de runtime, flag nunca leído |
| Graph retrieval | **ISOLATED** | importado en `pipeline.py:168` pero tras un flag que está OFF y **ausente de `ganancias.json`**, o sea que no puede encenderse solo |
| Model routing | **ISOLATED + PLACEHOLDER** | ningún importador de runtime; y los 4 modelos son el mismo string; `RESPALDOS` se vacía siempre por el filtro de `enrutador.py:104`, así que el reintento nunca puede ocurrir |
| Observabilidad | **PARTIAL** | ver §11 |
| Benchmark de retrieval | **VERIFIED pero mide otro pipeline** | ver §3 |
| Benchmark a nivel agente | **NOT VERIFIED** | `banco.py` nunca se ejecutó completo en esta sesión |
| UI | **PARTIAL** | ver §12 |
| Modo offline | **VERIFIED** | candado + dobles, 0 llamadas en 224 tests |
| ColBERT | **MISSING** | decisión documentada de no implementarlo. Correcto |

---

# 4. AGENTE PRINCIPAL

`agent.run` (`agent.py:152-217`), bucle de máximo 5 vueltas.

- **Memoria:** la lista `messages`. Todo se acumula ahí.
- **Recorte de contexto:** `_recortar` (`:137`) — si el total supera 40.000 caracteres, resume los
  resultados de tool antiguos dejando los 2 últimos enteros. Constantes sin justificar.
- **JSON inválido del modelo:** `json.loads(..., strict=False)` (`:182`) y el error **se le
  devuelve al modelo como resultado de la tool** en vez de propagarse (`:191-197`). Patrón correcto.
- **Tool inexistente:** `LookupError` con la lista de skills válidas (`:186-189`) — para que el
  modelo no repita la llamada imposible.
- **Presupuesto:** `PRESUPUESTO.comprobar()` **antes** de la petición HTTP (`agent.py:119`), no
  después. Correcto.
- **Candado offline:** primera línea de `llm()`, antes incluso del presupuesto.
- **Corte del bucle:** 5 vueltas → `"Me quede sin vueltas."`
- **Timeout:** 60s en `urlopen`. Sin reintentos. Sin streaming.
- **Cuando el retrieval no da evidencia:** solo en `pipeline` existe `suficiencia`. En `simple` y
  `arquitecto` **no hay nada**: el modelo recibe lo que haya y responde.
- **Cuando el código generado es inválido:** `_comprobar_sintaxis` (`rapido.py:65`) lo caza antes
  de ejecutar, gratis.

**Fragilidad:** `arquitecto._ejecutar_fase` llama a `agent.run` por fase, y el resultado de cada
fase se concatena al contexto de la siguiente (`arquitecto.py:203`) **sin validar ninguna de las
secciones que el prompt exige**. Nueve fases de prosa encadenada con un único check real
(`_hay_que_corregir`, `:156`), que además usa un `re.search(r"DEMOSTRADA|✗ FAIL|CRITICAL")` sobre
la prosa del modelo — un modelo que escriba "ninguna sospecha fue DEMOSTRADA" dispara el bucle de
corrección.

---

# 5. LLM / OPENROUTER

| | |
|---|---|
| Dónde | `agent.llm` (`agent.py:109`), **único punto del proyecto que abre un socket** |
| Llamadas por tarea | simple 1-5 · rapido 2-3 · pipeline 1-2 · arquitecto ~9-55 (**NOT VERIFIED**, nunca se corrió entero) |
| Selección de modelo | constante `agent.MODEL` (`:20`). **No hay routing activo** |
| Model routing | existe (`enrutador.py`) y **no está conectado a nada** |
| Fallback de modelos | `enrutador.RESPALDOS` siempre queda vacío por el filtro de `:104` → el bucle de reintento de `:117` es inalcanzable |
| Temperatura | **no se envía** — se usa el default del proveedor |
| max_tokens | `12000` hardcoded (`:121`). El `max_tokens` por clase del router nunca se lee |
| Timeout | 60s |
| Reintentos | **ninguno** |
| Streaming | **no** |
| Coste | real, de `usage.cost` de OpenRouter (`:56`). No inventado |
| Cache de llamadas | **solo `eval_cache.json`**, y solo para las reformulaciones del eval |

**A. Código que llama de verdad:** `agent.llm` y `vectores.VectorOpenRouter._pedir` (este último
nunca alcanzado).
**B. Preparación para el futuro:** `enrutador.py` entero, `VectorOpenRouter`.
**C. Mock:** `dobles.py` — **y es el camino por defecto** (`server.py:155`).
**D. Configuración sin efecto:** 7 de 13 flags de `config.py`; `COSTE_MAXIMO` (`config.py:23`)
declarado y nunca usado; `Ruta.max_tokens`.

---

# 6. RAG / RETRIEVAL

**Corpus:** `conocimientos/`, 19 archivos numerados + 3 meta. 247 trozos, 228 fichas, 240 fallos,
228 antipatrones, 19 cajas. Sin frontmatter en ningún archivo.

**Chunking:** `rag._secciones` (`:58`) parte por `## ` respetando code fences. El bug de los 5
trozos fantasma de la plantilla ADR está **arreglado y con test**. Las secciones `## Fuentes` se
descartan a propósito, así que **las fuentes bibliográficas son inalcanzables por retrieval**.
La línea `**Cubre del temario:**` está antes del primer `##`, así que **nunca entra en ningún
trozo** — `metadatos._temario()` la lee aparte, releyendo los archivos.

**Lexical / BM25:** `rag._ranking_bm25` (`:182`), k1=1.5 b=0.75 + coincidencia por prefijo de 5
para la morfología española. Es el método activo (`rag.METODO = "bm25"`). El IDF anterior sigue
en el archivo y solo es alcanzable desde el banco.

**Vector:** `VectorLocalHash` — n-gramas de caracteres + coseno, **explícitamente documentado como
señal léxica, no semántica** (medido: "readiness probe" 0.490 vs su sinónimo "health check" 0.034).
`VectorOpenRouter` existe, con caché versionada, y **nunca se ha ejecutado** (la carpeta
`embeddings/` no existe). Ambos **DISABLED** por medición.

**Hybrid / RRF:** implementado en `hibrido.py`, medido, y **su salida no llega al modelo** (§3).

**Metadata:** derivada, no escrita. `domain` real (la caja), `artifact_type` y `language`
derivables, `subdomain` asignado por keywords (99% cobertura), `technology` por diccionario de 21
entradas. **`difficulty`, `status`, `version` valen `None` a propósito: 0 ocurrencias en el
corpus.** Honesto y documentado.

**Reranker:** heurístico local, 5 pesos sin justificar (`hibrido.py:92-94`) y una ventana de
proximidad de 120 caracteres también sin justificar — en la única etapa que el banco declara
beneficiosa.

**Graph:** `grafo.py` convierte el grafo caja→caja en trozo→caja (407 aristas vs 182). Medido:
a 2 saltos alcanza 17 de 18 cajas, o sea que **no filtra nada por sí solo**. ISOLATED.

**Knowledge Tree:** `arbol.py`, coincide con BM25 en 9/10 consultas. Su único aporte real es
devolver `[]` cuando no sabe. ISOLATED.

**Symbols:** `simbolos.py` con `ast`, 358 símbolos del propio Mirag, 26 del fixture. Conectado
pero condicionado a `needs_symbols`.

**Cache:** `cache.py` completo, versionado por `corpus_hash + embedding_model + embedding_version +
model_version`, nivel "similar" OFF con una medición que lo justifica muy bien (0.949 para dos
preguntas *distintas* vs 0.873 para la *misma* reformulada). **Cero importadores de runtime.**

---

# 7. CONTEXT ENGINEERING

El contexto real (`rapido._contexto`, `rapido.py:234`) tiene exactamente cuatro partes:

```
PETICION DEL USUARIO: {pregunta}
=== CONOCIMIENTO RECUPERADO ===   rag.buscar(peticion, cajas)          k=3
=== ANTI-PATRONES (cubrir con un test CADA UNO) ===  buscar_antipatrones  k=6
=== MODOS DE FALLO CONOCIDOS ===  buscar_fallos                          k=5
```

- **Sin deduplicación** entre las tres búsquedas: un mismo concepto puede aparecer en las tres.
- **Sin presupuesto de tokens**: el tamaño es lo que salga. Medido hoy: 8.535 caracteres
  (~2.100 tokens) para una consulta normal; mediana histórica 3.257 tokens.
- **Sin historial de conversación**: cada petición es independiente. No hay multi-turno.
- Los símbolos se añaden aparte (`pipeline.py:190`) solo si se activaron.
- El aviso de cobertura se inyecta si `suficiencia` dice que no alcanza.

**Riesgos:** duplicación entre los tres bloques (alto, no medido); pérdida de relación entre
trozos (los `[NN]` se mandan como texto plano sin resolver); **truncado silencioso de la salida
de tests a 4.000 caracteres** (`skills.py:81`) — un test que imprima mucho antes de sus marcadores
**los pierde** y se reporta `SIN EVIDENCIA`.

---

# 8. TOOLS / SKILLS

| Tool | Existe | Registrada | Invocable | Probada | Error handling | Estado |
|---|---|---|---|---|---|---|
| `buscar_en_docs` | Sí | Sí | Sí | Sí | n/a | **VERIFIED** |
| `buscar_tradeoffs` | Sí | Sí | Sí | Sí | n/a | **VERIFIED** |
| `buscar_fallos` | Sí | Sí | Sí | Sí | n/a | **VERIFIED** |
| `buscar_antipatrones` | Sí | Sí | Sí | Sí | n/a | **VERIFIED** |
| `cajas_relacionadas` | Sí | Sí | Sí | Sí | devuelve lista válida si falla | **VERIFIED** |
| `verificar_codigo` | Sí | Sí | Sí | Sí (10+ casos) | allowlist, timeout, traversal | **VERIFIED** |
| `calcular` | Sí | Sí | Sí | **No** | ninguno | **BROKEN por diseño** (`eval`) |
| `hora_actual` | Sí | Sí | Sí | **No** | ninguno | **CONNECTED BUT UNVERIFIED** |
| `entregar_implementacion` | Sí | Sí (rapido/pipeline) | Sí | Sí | parser tolerante | **VERIFIED** |

**Allowlist:** `{node, python3}` — construida con `shutil.which()`, así que no miente sobre la
máquina. Pero **solo restringe `argv[0]`**: `python3 -c "..."` ejecuta Python arbitrario, y los
`archivos` son contenido arbitrario de todos modos. El propio docstring lo admite:
*"NO es un sandbox de verdad"*.

---

# 9. VERIFICACIÓN

Hoy, tras el arreglo de esta mañana, los términos significan cosas distintas y separadas:

| término | significa exactamente |
|---|---|
| `TESTS EN VERDE · N de N marcadores` | el comando salió con 0 **y** imprimió N marcadores, todos PASS |
| `FALLO: N de M marcadores fallaron` | algún marcador FAIL, **aunque el exit sea 0** |
| `SIN EVIDENCIA` | exit 0 sin marcadores: no se sabe qué se probó |
| `NO EJECUTADO` | ni siquiera corrió |
| `verificado` (evidencia) | el `test_id` que el modelo declaró apareció como PASS |
| `verificado en simulación` | pasó, pero contra una tecnología sustituida |
| `sin verificar` | el modelo lo declaró y su marcador no apareció |

**Dónde la UI podría mostrar PASS sin respaldo — buscado a propósito:**

1. **Arreglado hoy:** `analizarSkill` pintaba `completado` verde cuando había marcadores sin
   comparar `pasan` con `marcas.length`; `TEST:x:FAIL` con exit 0 salía como *"0 de 1 tests en
   verde"*.
2. **Sigue abierto:** en modo `arquitecto`, la evidencia es **prosa del modelo**. Las fases 1-7 no
   se validan contra nada. Si el modelo escribe "## Evidencia: DESCARTADA", nadie lo comprueba.
3. **Sigue abierto:** el truncado a 4.000 caracteres puede borrar marcadores reales y convertir
   una ejecución verde legítima en `SIN EVIDENCIA`. Es un falso negativo, no un falso positivo —
   menos grave, pero es ruido en la métrica.

---

# 10. PROJECT STATE

`estado.py` — diccionario construido en import time desde `agent.MODEL`, `skills.SKILLS`,
`rag.TROZOS` y una **lista de archivos escrita a mano** (`estado.py:38-40`).

- **Está sincronizado** en lo que deriva (modelo, skills, corpus).
- **No lo está** en lo que enumera a mano: la lista de archivos no incluye ninguno de los 14
  módulos nuevos, y hasta hoy la lista de modos decía 3 cuando había 4.
- **No hay indexación de repositorio**: `simbolos.py` la haría, pero `estado.py` no lo usa.
- Los atajos tenían cuatro patrones demasiado golosos (`salida`, `skills|herramientas|tools`,
  `areas`, `modos`); **arreglados hoy** con una guarda de órdenes de trabajo + patrones acotados,
  con 13 casos de test.

---

# 11. OBSERVABILIDAD

Campos que se escriben de verdad en `trazas_noche.jsonl` (verificado leyendo la última fila):
`cuando, version, tarea, modo, estado, llamadas, decision_simulada, tokens, coste_usd, segundos,
tokens_contexto, cajas, arreglado, propiedades, exito_verificado, exito_en_simulacion, valor`.

| métrica pedida | estado |
|---|---|
| query, modelo, llamadas, tokens, coste, latencia | **IMPLEMENTADA** |
| plan (cajas) | **PARCIAL** — solo `domains`, no el plan entero |
| verification / evidencia | **IMPLEMENTADA** |
| contexto (tamaño) | **IMPLEMENTADA** (estimación caracteres/4) |
| filtros, retrieval methods, candidate counts, chunks elegidos, reranker, cache, fallbacks | **PARCIAL** — existen como `Paso` en memoria y se emiten por SSE a la UI, pero **no se persisten**: `traza.escribir` no los recibe |
| graph, symbols, tree | **NO EXISTE** en la traza |
| cache_hit / cache_miss | **NO EXISTE** (el cache no está conectado) |
| model_selected / fallback de modelo | **NO EXISTE** (el router no está conectado) |

O sea: la observabilidad **en pantalla** es buena; la **persistida** es la de ayer más dos campos.
Las preguntas *"¿por qué recuperó esto?"* y *"¿dónde se va el tiempo?"* se pueden contestar en vivo
pero **no a posteriori**.

---

# 12. UI vs BACKEND

**Eventos que emite el backend:** `fase`, `pensamiento`, `skill`, `paso`, `gasto`, `fin`.
**Eventos que maneja la UI:** los mismos seis. **Sin discrepancias de contrato.**

Discrepancias reales encontradas:

1. **La UI conocía 5 estados del veredicto y el backend solo emitía 2** — arreglado hoy: ahora son
   4 estados compartidos (`verde/rojo/sin_evidencia/no_ejecutado`).
2. **`entregable.estado` venía de un cálculo distinto al de la UI** — arreglado ayer: la sección de
   código se pinta con el veredicto observado, no con la etiqueta del backend.
3. **El aviso de contradicción estaba limitado a `noverificado` y no disparaba en `advertencia`**
   — arreglado hoy.
4. **Sigue abierto:** la UI muestra las etapas de `hibrido` (filtro, bm25, rrf, reranker) con sus
   conteos y latencias **como si fueran el retrieval que alimenta al modelo**. No lo son (§3).
   Esta es hoy la discrepancia BACKEND REAL ≠ UI PRESENTADA más importante.
5. **`index.html.bak`** (18.758 bytes) sigue en el repo y se sirve por HTTP.

---

# 13. TESTS — ejecutados, no enumerados

Comando: `/opt/homebrew/bin/python3 <archivo>` con `MIRAG_OFFLINE` por defecto.

## VERIFIED BY EXECUTION

| archivo | exit | resultado |
|---|---|---|
| `test_cimientos.py` | 0 | 21 casos · TODO OK |
| `test_plan.py` | 0 | 22 casos · TODO OK |
| `test_metadatos.py` | 0 | 19 casos · TODO OK |
| `test_vectores.py` | 0 | 29 casos · TODO OK |
| `test_simbolos.py` | 0 | 18 casos · TODO OK |
| `test_cache.py` | 0 | 24 casos · TODO OK |
| `test_grafo_arbol.py` | 0 | 23 casos · TODO OK |
| `test_enrutador.py` | 0 | 13 casos · TODO OK |
| `test_auditoria.py` | 0 | 15 casos · TODO OK |
| `test_resiliencia.py` | 0 | 24 casos · TODO OK |
| **`test_full_pipeline.py`** | **1** | **16 casos · 1 FALLO** → `PermissionError: 'salida/__pycache__'` |
| `prueba_bucle.py` | 0 | TODO OK (5 escenarios, `node` real) |
| `estado.py --probar` | 0 | TODO OK, 13 casos |
| `auditoria.py` | 0 | 6 casos · TODO OK |
| `suficiencia.py` | 0 | 7/7 |
| `eval.py` | 0 | 0 llamadas, R@1 27/31 fácil, MRR duro 0.562 |

**224 casos, 1 suite en rojo** (por el bug de §4, no por el test).

## PRESENT BUT NOT EXECUTED

- `banco.py` — cuesta ~$1 y hace llamadas reales. No se ejecutó.
- `banco_recuperacion.py` — sí se ejecutó ayer; hoy no se volvió a correr.
- `pruebas/app/tests/test_auth.py` — fixture, se ejecuta dentro de `test_simbolos`.

## Tests demasiado débiles o que no prueban lo que dicen

1. **`test_cimientos.baseline_acepta_la_firma_real`** — comprueba que el string
   `"lambda *a, **kw: []"` está en el archivo. Es un test sobre el *texto fuente*, no sobre el
   comportamiento. No ejecuta el brazo baseline.
2. **`test_full_pipeline.r3_multisalto`** — calcula `cajas` y nunca lo usa; el único assert real
   es que el paso `grafo` tenga un `resumen` no vacío. No prueba multi-hop.
3. **Todos los casos de `test_full_pipeline`** son `SIMULATED`: prueban la máquina con dobles.
   Está declarado en el docstring, pero conviene no leerlos como validación del agente.
4. **`test_enrutador`** prueba 13 casos de un módulo que **nada importa en runtime**.
5. **`test_cache` y `test_grafo_arbol`** — 47 casos sobre módulos ISOLATED.
6. **Ningún test cubre `arquitecto.py`** salvo `prueba_bucle`, que usa un LLM falso y valida
   solo la orquestación.

---

# 14. PRUEBAS MANUALES (10 casos, offline, 0 coste)

| # | Caso | Flujo observado | Resultado |
|---|---|---|---|
| 1 | Conceptual | bm25→reranker→suficiencia=cubierto | OK, 43.8 ms |
| 2 | Corpus (outbox) | igual | OK, 25.0 ms — **pero la respuesta es la del fixture, no del corpus** |
| 3 | Generación de código | +verificación+evidencia | **3 verificadas**, 124 ms |
| 4 | Código que falla | verificacion=error | **1 refutada** — correcto |
| 5 | Tool failure (`bash`) | verificacion=error | **1 sin verificar** — correcto |
| 6 | Retrieval insuficiente (WebRTC) | suficiencia=**ausente**, fallback | *"El corpus no cubre webrtc"* |
| 7 | Multi-hop | suficiencia=**mencionado** | correcto, pero **grafo omitido** |
| 8 | Requiere símbolos | simbolos=**ejecutado** | 186 ms (el más lento) |
| 9 | Contexto enorme (56k chars) | no revienta | 54.6 ms |
| 10 | Respuesta malformada | entrega=error | no revienta |

**Observación importante del caso 2:** con el candado puesto, *cualquier* pregunta que no contenga
`calculator|calculadora|calculate(` recibe el párrafo fijo sobre índices de PostgreSQL
(`dobles.py:63`). La UI lo declara ("La decisión del modelo está simulada"), así que es honesto,
pero **el modo por defecto del servidor es un fixture**.

**Casos con modelo real medidos hoy** (`trazas_noche.jsonl`, 3 de 9 filas):

```
1 llamada · 4,854 tokens · $0.0065 · 6.5s  · sin_codigo
1 llamada · 7,218 tokens · $0.0117 · 27.2s · verde
2 llamadas · 13,628 tokens · $0.0311 · 34.9s · rojo
```

---

# 15. DEPENDENCIAS Y ENTORNO

**Cero dependencias declaradas y cero usadas.** Verificado: ningún archivo de dependencias existe
y no hay un solo import de terceros.

**Lo que "funciona en esta máquina" y el proyecto no garantiza:**

| Requisito | Estado | Riesgo |
|---|---|---|
| `node` en el PATH | presente (v25.8.1) | los fixtures de `prueba_bucle` y medio corpus asumen Node |
| `python3` en el PATH | presente | — |
| **certificados raíz TLS** | **solo en `/opt/homebrew/bin/python3`** | el `python3` por defecto **no puede hablar HTTPS**. Nada en el código lo comprueba ni lo dice al arrancar |
| `pytest` | **ausente** | ya no se promete (arreglado), pero medio corpus lo menciona |
| `.env` con `OPENROUTER_API_KEY` | presente | el import ya no falla sin él (arreglado) |
| Puerto 8000 libre | — | hardcoded, sin fallback |

---

# 16. PLACEHOLDERS, MOCKS Y SEAMS

| ARCHIVO:LÍNEA | pretende | hace realmente | falta |
|---|---|---|---|
| `server.py:155-164` | ejecutar el pipeline | con `MIRAG_OFFLINE=1` (default) instala un **doble** y responde con un fixture elegido por regex de 3 literales | nada en código; el problema es que es el default |
| `enrutador.py:27-32` | enrutar por clase de tarea | los 4 valores son **el mismo modelo** | datos reales de coste/éxito por modelo |
| `enrutador.py:104` | cadena de respaldo | filtra el único respaldo → **tupla vacía siempre** | más de un modelo en `RESPALDOS` |
| `enrutador.py:105` | `max_tokens` por clase | **nunca se lee**: `agent.py:121` lo hardcodea a 12000 | pasar `ruta.max_tokens` a `agent.llm` |
| `skills.py:145` | calculadora | `eval()` sin aislar | ver §Seguridad |
| `config.py:23` | `COSTE_MAXIMO` | **declarado y nunca usado** | borrarlo o usarlo |
| `config.py:45,46,47,52` | 4 flags | **declarados, ningún lector** | conectar o quitar |
| `config.py:33,35,37` | 3 flags del núcleo | **declarados, ningún lector**: las etapas corren incondicionalmente | quitar el flag o poner la guarda |
| `arbol.py:74-77` | subcategorías | `except Exception: subs = ()` **sin registrar nada** | acotar la excepción |
| `simbolos.py:191-194` | parsear .py | descarta el archivo **sin contar cuántos** | devolver el conteo |
| `prueba_bucle.py:87` | fases 1-7 | `"(fase N simulada)"` | es un harness, correcto |
| `arquitecto.py:1` | docstring | dice *"4 fases"*, son **9** | corregir |
| `dobles.py:*` | doble de test | correcto, pero **alcanzable desde `server.py`** | — |

**Constantes sin justificar que cambian el comportamiento:** `skills.TIMEOUT=30`,
`skills` truncado `[-4000:]`, `agent.max_tokens=12000`, `agent.RECIENTES=2/UMBRAL=40_000`,
`hibrido` proximidad `120` y los 5 pesos del reranker, los cuatro `k` distintos de `rag`,
`eval.PROFUNDIDAD=10` (que gobierna todos los números de `ganancias.json`).

**No hay ningún `TODO`, `FIXME`, `XXX` ni `HACK` en el código de producción.**

---

# 17. CÓDIGO QUE PARECE FUNCIONAR PERO NO

Los encontrados, por orden de cuánto engañan:

1. **El reranker no cambia el ranking que ve el modelo** — encendido por medición, ejecutándose,
   con su tarjeta en la UI, y el SHA del contexto es idéntico con él y sin él.
2. **El benchmark mide otro pipeline** — `banco_recuperacion.py` mide Stack A, el agente usa B.
3. **Model routing que no enruta** — nada lo importa; y aunque lo importara, los 4 modelos son el
   mismo y su `max_tokens` no se lee.
4. **Fallback de modelo que nunca puede activarse** — `RESPALDOS` siempre queda vacío.
5. **Cache que nunca recibe datos** — 417 líneas, 0 importadores de runtime.
6. **Graph que no afecta a resultados** — flag ausente de `ganancias.json`: no puede encenderse solo.
7. **Knowledge Tree que nadie consulta** — ningún importador de runtime.
8. **7 flags que nadie lee** — `config.py` imprime ON/off de etapas que ningún código consulta.
9. **`rapido_a_pasos` construye pasos y los tira** — el navegador los recibe por otro camino.
10. **`estado.responder` duplicado** — la copia de `pipeline.py:116` es inalcanzable desde la web.
11. **`benchmarks/comparativa.json`, `baseline.json`, `final.json`** — escritos, cero lectores.
12. **`trazas_noche.jsonl`** — escrito en cada petición, leído solo por un test.
13. **Tests sobre mocks presentados como validación** — 47 casos sobre módulos ISOLATED.

---

# 18. FLUJOS ROTOS O FRÁGILES

| severidad | problema |
|---|---|
| **CRÍTICO** | `.env` servido por HTTP en 0.0.0.0 sin auth |
| **CRÍTICO** | `skills.calcular` = `eval()` in-process sobre entrada del modelo |
| **CRÍTICO** | `rapido.guardar` revienta tras ejecutar el código entregado; rompe todas las tareas de código siguientes |
| **ALTO** | El subproceso de `verificar_codigo` hereda `OPENROUTER_API_KEY` |
| **ALTO** | Inyección por corpus/retrieval sin sanear; los separadores `=== TAREA ===` son falsificables desde un trozo |
| **ALTO** | El contexto del modelo no pasa por el pipeline medido (§3) |
| **ALTO** | `arquitecto`: 9 fases de prosa encadenada sin validación de secciones |
| **MEDIO** | `rapido.guardar` usa ruta relativa al cwd, no a `__file__` — borra un `salida/` ajeno si arrancas desde otro directorio |
| **MEDIO** | Truncado a 4.000 caracteres puede borrar marcadores y falsear `SIN EVIDENCIA` |
| **MEDIO** | `do_POST` lee `Content-Length` sin validar, **fuera** del `try`: mata el hilo sin responder |
| **MEDIO** | Sin límite de tamaño del cuerpo POST |
| **MEDIO** | `enrutador.llamar` mutaría el global `agent.MODEL` bajo `ThreadingHTTPServer` (latente) |
| **BAJO** | `hibrido._TIENDAS` usa `hash()` (aleatorizado por PYTHONHASHSEED) justo donde `vectores` documenta por qué no hacerlo |
| **BAJO** | Puerto 8000 hardcoded |

---

# 19. SEGURIDAD

Ver los dos CRÍTICOS de arriba. Además:

- **`verificar_codigo` — lo que está bien:** allowlist construida con `shutil.which`, guarda de
  path traversal con `is_relative_to` sobre un `TemporaryDirectory` fresco, timeout aplicado.
  Verificado que `bash -c ls` se rechaza.
- **Lo que no:** el subproceso hereda el entorno completo, con la clave. `python3 -c "..."` pasa la
  allowlist (solo mira `argv[0]`).
- **Inyección por corpus:** los trozos llegan al prompt **verbatim**, sin delimitadores ni
  etiquetado de "esto es dato, no instrucción". La ironía: `conocimientos/18-ai-backend.md`
  contiene ese consejo exacto y el código no lo sigue.
- **Secretos en logs:** no encontré ninguna ruta de fuga. `trazas*.jsonl` guarda tus prompts
  (`tarea[:120]`), no la clave.

---

# 20. COSTE Y PERFORMANCE

| | REAL MEDIDO | ESTIMADO | NO MEDIDO |
|---|---|---|---|
| llamadas/tarea | pipeline 1-2, rapido 2-3 | simple 1-5 | arquitecto |
| coste/tarea | $0.0065–$0.0311 (3 ejecuciones hoy) | $1.11 el plan de mañana | arquitecto |
| retrieval | 2.33 ms mediana (Stack A) | — | **Stack B, el que se usa de verdad** |
| pipeline completo | P50 31.9 ms · P95 167.7 ms (sin LLM) | — | con LLM |
| índice vectorial | 174 ms build, 0.62 ms consulta | — | — |
| consulta con LLM real | 6.5s / 27.2s / 34.9s | — | — |
| símbolos | ~160 ms (358 símbolos) | — | reindexado por petición: **no se cachea** |

---

# 21. DEUDA TÉCNICA

- **`rapido.py` (434 líneas)** mezcla retrieval, prompts, parsing, evidencia, persistencia y CLI.
- **`marcas_de` existe dos veces** con firmas distintas (`skills.py:113` y `auditoria.py:40`).
- **La tabla de iconos de evidencia está triplicada** en `server.py:39,46,88`.
- **Abstracción prematura:** `VectorStore` ABC con dos implementaciones, una de las cuales nunca
  ha corrido.
- **Complejidad sin conectar:** `cache.py` + `arbol.py` + `enrutador.py` + `grafo.py` = **1.086
  líneas** que ninguna petición toca.
- **Nombres engañosos:** `hibrido.recuperar` sugiere que es *el* retrieval; `banco_recuperacion`
  sugiere que mide el retrieval del agente.

---

# 22. QUÉ NO DEBERÍA TOCARSE TODAVÍA

Contratos que hoy funcionan y que romperlos costaría caro:

1. **`skills.veredicto(salida) -> (estado, detalle, marcas)`** — lo consumen 8 sitios. Es la base
   de toda la disciplina de evidencia. Si añadís un estado nuevo, hay que tocar `index.html`
   también.
2. **La cabecera de `verificar_codigo` es un contrato de string.** `veredicto` la parsea por
   prefijo. Cambiar el texto rompe silenciosamente todo lo de arriba.
3. **`agent.llm` es el único punto de red.** El candado offline y el presupuesto viven ahí. Si
   añadís streaming o reintentos, los dos hay que re-verificarlos.
4. **`agent.run` devuelve `{"pasos", "respuesta"}`** y el auditor se engancha en su return. Un
   return nuevo sin auditar reabre el bug de las afirmaciones.
5. **`rag.Trozo`** es un NamedTuple de 4 campos usado por 18 módulos. Añadir campos es seguro;
   reordenar no.
6. **El contrato SSE** (`fase`/`pensamiento`/`skill`/`paso`/`gasto`/`fin`) lo consume `index.html`.
7. **`_PorHilo` / `_Proxy` del presupuesto** — cualquier cosa que escriba globales de módulo por
   petición (como haría `enrutador`) reintroduce la race condition que esto resuelve.

---

# 23. MAPA DE RIESGO PARA FUTURAS FEATURES

| Feature | Depende de | Toca | Riesgo | Bloqueadores | Precondición |
|---|---|---|---|---|---|
| Conectar el retrieval medido al contexto | `hibrido`, `rapido._contexto` | `pipeline.py:188` | **ALTO** — cambia lo que ve el modelo en todos los modos | ninguno técnico | re-correr `banco.py` después: los números de hoy no aplican |
| Streaming | `agent.llm` | candado, presupuesto, SSE | ALTO | el coste llega en `usage` al final | re-verificar presupuesto |
| Multi-turno / memoria | `agent.run`, `server` | contexto, coste | ALTO | no hay historial hoy | presupuesto de tokens antes |
| Conectar `cache.py` | `vectores` | `pipeline` | MEDIO | el nivel "similar" está medido como peligroso | usar solo el exacto |
| Conectar `arbol`/`grafo` | `config`, `ganancias.json` | `pipeline` | MEDIO | no pueden encenderse solos: faltan en `ganancias.json` | medirlos primero |
| Model routing real | `enrutador`, `agent.MODEL` | `agent.llm` | **ALTO** | muta un global bajo servidor multihilo | pasar el modelo como argumento, no como global |
| Tools en paralelo | `agent.run` | bucle, presupuesto | ALTO | el bucle es estrictamente secuencial | — |
| Persistencia / multi-agente | todo | — | ALTO | no hay capa de estado | — |

---

# 24. MATRIZ FINAL

| Área | Estado real | Evidencia | Integrada | Testeada | Riesgo | Observación |
|---|---|---|---|---|---|---|
| Agent | VERIFIED | prueba_bucle + 10 casos | Sí | Sí | BAJO | bucle sólido, defensivo |
| LLM / OpenRouter | VERIFIED | 3 ejecuciones reales hoy | Sí | Parcial | MEDIO | sin reintentos ni streaming |
| RAG (corpus+chunking) | VERIFIED | 247 trozos, eval 0 llamadas | Sí | Sí | BAJO | `## Fuentes` inalcanzable |
| BM25 | PARTIAL | banco | Sí (vía `rag`) | Sí | MEDIO | mide Stack A |
| Vector | DISABLED | −0.0481 MRR medido | No | Sí (29 casos) | BAJO | honesto: no es semántico |
| Hybrid + RRF | ISOLATED de facto | SHA idéntico ON/OFF | **No llega al modelo** | Sí | **ALTO** | §3 |
| Metadata | PARTIAL | 99% subdominio | Solo Stack A | Sí | MEDIO | 3 campos `None` a propósito |
| Reranker | ISOLATED de facto | SHA idéntico | No llega al modelo | Sí | **ALTO** | única etapa "ON" |
| Contextual chunks | MISSING | — | No | No | BAJO | flag sin implementación |
| Symbols | CONNECTED BUT UNVERIFIED | caso 8, 358 símbolos | Condicional | Sí (18) | MEDIO | reindexa por petición |
| Cache | ISOLATED | 0 importadores runtime | No | Sí (24) | BAJO | bien construido, desconectado |
| Knowledge Tree | ISOLATED | 0 importadores runtime | No | Sí (23) | BAJO | coincide 9/10 con BM25 |
| Graph | ISOLATED | flag ausente de ganancias | No | Sí | BAJO | 2 saltos = 17/18 cajas |
| ProjectState | VERIFIED | 13 casos | Sí | Sí | BAJO | lista de archivos a mano, obsoleta |
| Model routing | ISOLATED + PLACEHOLDER | 0 importadores; 4 modelos iguales | No | Sí (13) | MEDIO | mutaría global bajo hilos |
| Verification | VERIFIED | 4 estados, 15 casos auditor | Sí | Sí | BAJO | lo mejor del proyecto |
| Tools | VERIFIED salvo `calcular` | 10+ casos | Sí | 7 de 9 | **CRÍTICO** | `eval()` |
| Observability | PARTIAL | traza de 17 campos | En pantalla sí, persistida no | Parcial | MEDIO | no se puede auditar a posteriori |
| Evaluation | VERIFIED | 0 llamadas, 49 casos | — | — | BAJO | set duro con margen real |
| Benchmark | VERIFIED pero mide otro pipeline | §3 | — | — | **ALTO** | |
| UI | PARTIAL | 6 eventos, sin discrepancia de contrato | Sí | Manual | MEDIO | presenta Stack A como si alimentara al modelo |
| Offline mode | VERIFIED | 224 tests, 0 llamadas | Sí | Sí | MEDIO | es el default y responde con fixtures |
| Error handling | VERIFIED | 24 casos de resiliencia | Sí | Sí | BAJO | muy bueno |
| Security | BROKEN | `curl /.env` → 200 | — | No | **CRÍTICO** | |

---

# 25. TOP 20 PROBLEMAS, por impacto técnico

1. **`.env` servido por HTTP en 0.0.0.0** · `curl /.env → 200, 93 bytes` · robo de la API key desde
   la LAN · **CRÍTICO** · bind a `127.0.0.1` + `directory=` a un subdirectorio.
2. **`skills.calcular` = `eval()`** · `skills.py:145` · RCE en el proceso del servidor dirigido por
   el modelo · **CRÍTICO** · `ast.literal_eval` o un parser aritmético.
3. **`rapido.guardar` revienta tras usar el código entregado** · reproducido en tempdir · toda
   tarea de código posterior falla y se pierde el trabajo pagado · **CRÍTICO** ·
   `shutil.rmtree`/`if viejo.is_file()`.
4. **El contexto del modelo no pasa por el pipeline medido** · SHA idéntico con reranker ON/OFF ·
   todas las mediciones describen un camino que nadie recorre · **ALTO** · usar `r.trozos` para
   construir el contexto.
5. **El subproceso hereda `OPENROUTER_API_KEY`** · `skills.py:73` sin `env=` · el código generado
   puede exfiltrar la clave · **ALTO** · `env={"PATH": ...}`.
6. **Inyección por corpus sin sanear** · `rapido.py:234` interpola verbatim · un trozo puede
   falsificar `=== TAREA ===` · **ALTO** · delimitar y declarar como datos.
7. **`arquitecto`: 9 fases de prosa sin validar** · `arquitecto.py:203` · errores compuestos sin
   puerta · **ALTO** · parsear las secciones que el propio prompt exige.
8. **El modo por defecto responde con fixtures** · `server.py:155` · cualquier pregunta sin
   "calculator" recibe el párrafo de índices de Postgres · **ALTO** · está declarado, pero debería
   avisar más fuerte o no ser el default.
9. **1.086 líneas ISOLATED** (`cache`+`arbol`+`enrutador`+`grafo`) · 0 importadores de runtime ·
   coste de mantenimiento sin beneficio · **MEDIO** · conectar o mover a `experimental/`.
10. **7 flags que nadie lee** · `config.py` · `config.py` imprime estados falsos · **MEDIO**.
11. **Truncado a 4.000 caracteres puede borrar marcadores** · `skills.py:81` · falso
    `SIN EVIDENCIA` · **MEDIO** · truncar por el medio conservando el final.
12. **`do_POST` sin validar `Content-Length`, fuera del `try`** · `server.py:116` · hilo muerto sin
    respuesta · **MEDIO**.
13. **Sin límite de tamaño del cuerpo POST** · agotamiento de memoria trivial · **MEDIO**.
14. **`rapido.guardar` relativo al cwd** · borra un `salida/` ajeno · **MEDIO**.
15. **La observabilidad no se persiste** · `traza.escribir` no recibe los `Paso` · no se puede
    auditar a posteriori · **MEDIO**.
16. **`enrutador` mutaría `agent.MODEL` global** · bajo `ThreadingHTTPServer` · race condition
    latente · **MEDIO**.
17. **Símbolos reindexados en cada petición** · ~160 ms · **BAJO**.
18. **El `python3` por defecto no tiene certificados** · nada lo comprueba al arrancar · **BAJO**.
19. **`index.html.bak` en el repo y servido** · **BAJO**.
20. **Tests que prueban texto fuente, no comportamiento** · `test_cimientos:116` · falsa confianza ·
    **BAJO**.

---

# 26. QUÉ ESTÁ REALMENTE BIEN

Con evidencia, no por cortesía:

- **La disciplina de evidencia es genuinamente buena.** `skills.veredicto` con 4 estados, el
  cruce `test_id`↔marcador de `_evidencia`, y el auditor de afirmaciones. Intenté romperla con 15
  casos y aguantó. Un `exit 0` sin marcadores ya no puede presentarse como verde.
- **El candado offline.** Un solo punto de red, comprobado antes del presupuesto, default cerrado.
  224 tests corren sin gastar un céntimo. Es la mejor decisión de arquitectura del proyecto.
- **El manejo de errores.** 24 casos de resiliencia en verde: vector caído → BM25, reranker roto →
  RRF, filtro vacío → corpus completo **registrado**, JSON cortado → error explicado.
- **`suficiencia.py`.** Distingue *mencionado* de *cubierto* con una señal real del corpus
  (título/ficha vs prosa). 7/7 graduados, 1/49 falsos negativos. Es una idea propia y funciona.
- **La honestidad de `vectores.py` y `cache.py`.** Los dos traen mediciones que argumentan **en
  contra** de sí mismos y se apagan solos. Es raro y es valioso.
- **El parser del plan.** 7 formas de entrada, incluida la reparación de JSON truncado por
  llaves equilibradas. 22 casos.
- **Cero dependencias, de verdad.** Verificado archivo por archivo.
- **Las guardas de path traversal**, tanto en `verificar_codigo` (`is_relative_to`) como en
  `guardar` (`Path(ruta).name`). Intenté escaparme y no pude.

---

# 27. ESTADO DEL PROYECTO EN UNA FRASE

> **Mirag es hoy un motor de evidencia sólido envuelto en un pipeline de retrieval que no está
> conectado a su propia salida.** Funcionan de verdad: el bucle del agente, el candado de gasto, la
> ejecución y verificación de código con su auditoría de afirmaciones, la detección de cobertura
> insuficiente, el manejo de errores y los atajos de estado. Están parcialmente integrados el
> retrieval híbrido y el filtrado por metadatos —se ejecutan y se miden, pero **el contexto que
> recibe el modelo se construye por otro camino**, así que el reranker y el benchmark describen un
> pipeline que ningún usuario recorre. Son andamiaje sin conectar `cache.py`, `arbol.py`,
> `grafo.py` y `enrutador.py` (1.086 líneas, cero importadores de runtime). Está mockeado el modo
> por defecto del servidor, que con el candado puesto responde con fixtures. **Los tres riesgos que
> hay que resolver antes de añadir nada: la API key servida por HTTP a toda la red, el `eval()` en
> el proceso del servidor, y que `guardar()` se rompe en cuanto ejecutás el código que te entrega.**

---

# 28. ARCHIVOS QUE OTRO AGENTE DEBERÍA LEER PRIMERO

## READ FIRST

1. **`skills.py`** — el veredicto de 4 estados y la ejecución real. Es el contrato del que cuelga
   toda la disciplina de evidencia, y la única tool peligrosa.
2. **`agent.py`** — el bucle, el candado offline, el presupuesto por hilo. Único punto de red.
3. **`pipeline.py`** — el flujo principal. **Leer las líneas 132 y 188 juntas**: ahí está la
   desconexión entre el retrieval medido y el contexto real.
4. **`server.py`** — el dispatch de los 4 modos, el atajo antes del dispatch, los dos CRÍTICOS de
   seguridad (líneas 102 y 198).
5. **`rapido.py`** — de aquí sale el contexto que ve el modelo (`recuperar` + `_contexto`) y la
   evidencia (`_evidencia`). También el bug de `guardar`.
6. **`auditoria.py`** — por qué una afirmación del modelo no se cree sola.
7. **`config.py`** — la compuerta por medición. Ojo: 7 de 13 flags no los lee nadie.
8. **`rag.py`** — chunking respetando fences, BM25, y los cuatro `buscar*` que son el retrieval real.
9. **`suficiencia.py`** — mención vs cobertura.
10. **`index.html`** — `analizarSkill` y `pasoDelPipeline`: la capa que históricamente era más
    honesta que el backend.

## READ IF MODIFYING RETRIEVAL
`rag.py`, `hibrido.py`, `metadatos.py`, `plan.py`, `rapido.py:227-238` (**el contexto real**),
`banco_recuperacion.py`, `eval.py`, `config.py`, `benchmarks/ganancias.json`.

## READ IF MODIFYING AGENT
`agent.py`, `pipeline.py`, `rapido.py`, `arquitecto.py`, `dobles.py`, `traza.py`,
`test_full_pipeline.py`, `prueba_bucle.py`.

## READ IF MODIFYING VERIFICATION
`skills.py:88-135` (`_cabecera` y `veredicto`), `rapido.py:140-175` (`_evidencia`),
`auditoria.py`, `test_auditoria.py`, `index.html` (`analizarSkill`).

## READ IF MODIFYING UI
`index.html`, `server.py:14-100` (los tres constructores de markdown),
`pipeline.py:48-82` (`Paso`/`Ejecucion`).

---

# RECUENTO FINAL

| Estado | Nº | Componentes |
|---|---|---|
| **VERIFIED** | 17 | agent, rag, skills, server, pipeline, rapido, estado, auditoria, suficiencia, traza, corpus, index.html, candado offline, presupuesto, evidencia, error handling, eval |
| **PARTIAL** | 6 | plan, metadatos, config, BM25, observabilidad, UI |
| **CONNECTED BUT UNVERIFIED** | 3 | arquitecto, simbolos, `hora_actual` |
| **ISOLATED** | 10 | cache, arbol, enrutador, grafo, banco, banco_recuperacion, prueba_bucle, hibrido *(de facto)*, reranker *(de facto)*, comparativa/baseline/final.json |
| **MOCKED** | 1 | `dobles.py` en el camino por defecto del servidor |
| **DISABLED** | 2 | señal vectorial, `VectorOpenRouter` |
| **PLACEHOLDER** | 3 | model routing, reranker remoto, `COSTE_MAXIMO` |
| **BROKEN** | 3 | `skills.calcular`, `rapido.guardar`, exposición de `.env` |
| **MISSING** | 3 | contextual chunks, ColBERT *(decisión consciente)*, `embeddings/` |
| **NOT VERIFIED** | 2 | benchmark a nivel agente, modo arquitecto de punta a punta |

**Total: 50 componentes clasificados.**
