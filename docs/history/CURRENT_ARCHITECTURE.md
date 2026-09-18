# Mirag — arquitectura actual

Sistema RAG + agente en **Python de biblioteca estándar**. El núcleo —los 30 módulos de la raíz,
que son exactamente la cerradura de `server.py`— no tiene ninguna dependencia externa, verificado
recorriendo su AST: 0 imports fuera de stdlib. La capa `blockchain/` está fuera de esa cerradura,
tiene su propio entorno y declara `stellar-sdk`; `server.py` la importa perezosamente para que su
ausencia no pueda impedir el arranque.

## El camino de producción, entero

```
USUARIO
  │
  ├─ server.do_POST ─── ruta única, 127.0.0.1, lista blanca de GET
  │
  ├─ estado.responder ──────────── ¿pregunta por el propio Mirag? → respuesta directa, 0 llamadas
  │                                (con guarda: una orden de trabajo nunca se la lleva el atajo)
  ↓
pipeline.ejecutar            ← EL ÚNICO camino de producción
  │
  ├─ plan.deducir ───────────────── cajas, profundidad, needs_code/graph/symbols · 0 llamadas
  │
  ├─ recuperacion.recuperar ─────── FUENTE ÚNICA de retrieval
  │    ├─ conocimiento  (rag.TROZOS, 247)      k=3
  │    ├─ antipatrones  (rag.ANTIPATRONES, 228) k=6
  │    └─ fallos        (rag.FALLOS, 240)       k=5
  │    cada índice: filtro de metadatos → BM25 → vector? → RRF → reranker?
  │    → RetrievalResult, con la procedencia de CADA trozo
  │
  ├─ simbolos ──── solo si plan.needs_symbols · índice cacheado por (ruta, mtime)
  ├─ grafo ─────── solo si plan.needs_graph Y la compuerta lo permite
  ├─ suficiencia ─ cubierto / mencionado / ausente
  │
  ├─ recuperacion.construir_contexto ← FUENTE ÚNICA de contexto
  │    orden, dedup por identidad, techo de 24.000 chars, símbolos, aviso de cobertura
  │
  ├─ agent.llm ─── EL ÚNICO socket del proyecto. Primera línea: el candado offline
  │
  ├─ entrega → skills.verificar_codigo → skills.veredicto
  │    verde · rojo · sin_evidencia · no_ejecutado    ← lo decide la EJECUCIÓN
  │
  ├─ reparación ── como mucho una, y se registra en repair_attempts
  ├─ evidencia ─── cada propiedad declarada contra un marcador real
  ├─ obligaciones ─ los anti-patrones recuperados contra la evidencia
  ├─ persistencia ─ un paso que puede fallar SIN llevarse la respuesta
  └─ traza ─────── 32 campos de lo observado, a trazas_noche.jsonl
```

## Las tres fuentes únicas

Son la lección de la auditoría. El bug que la abrió fue **medir una cosa y servir otra**: el
benchmark evaluaba `hibrido.recuperar()` mientras el modelo recibía contexto de
`rapido.recuperar()`. Probado con el SHA del prompt real: idéntico con el reranker encendido y
apagado.

| | quién es | quién la consume |
|---|---|---|
| retrieval | `recuperacion.recuperar()` | producción **y** benchmark |
| contexto | `recuperacion.construir_contexto()` | producción **y** benchmark |
| veredicto de ejecución | `skills.veredicto()` | pipeline, UI y traza |

Hay tests que fallan si alguien vuelve a abrir un segundo camino.

## Modos

| modo | estado | qué es |
|---|---|---|
| `pipeline` | **PRODUCCIÓN** | todo lo de arriba |
| `arquitecto` | **EXPERIMENTAL** | orquestación propia, sin la disciplina de evidencia |

`simple` y `rapido` se retiraron en la Fase 2. Pedirlos devuelve un rechazo explícito, no un error.
`rapido.py` **no se borró**: es la librería de la que el pipeline reutiliza `_evidencia`,
`_como_lista`, `simulado`, `_comprobar_sintaxis`, `ENTREGAR` y `guardar`.

## La compuerta de medición

Ninguna etapa opcional está encendida por existir. `config.activar(etapa, familia)` lee
`benchmarks/ganancias.json`, y **una etapa sin medir nace apagada**.

| bandera | estado | por qué |
|---|---|---|
| BM25 + 3 índices | núcleo | el suelo; el IDF anterior daba 0.469 MRR duro frente a 0.553 |
| reranker | **ON** | +0.082 MRR duro por 0.006 de coste |
| vector local | **OFF** | −0.015 MRR y 13× más lento, pese a traer 38% de candidatos nuevos |
| RRF | ON, inerte | passthrough con una sola señal; es donde entraría el vector |
| símbolos | condicional | 0 ms cuando `needs_symbols` es falso |
| grafo | conectado, en auto off | +8 trozos sin evidencia de que ayuden |
| caché, árbol, routing | **EXPERIMENTAL** | existen y están testeados; no están en el camino |
| ColBERT, contextual chunks | **NO IMPLEMENTADO** | no arrancan ni a mano |

`tests/test_banderas.py` comprueba la tabla **conmutando cada bandera y mirando si cambia el resultado**.

## Seguridad

| | |
|---|---|
| servidor | `127.0.0.1` y lista blanca: solo `/` y `/index.html`. `/.env` → 404 |
| ejecución de código | lista de intérpretes construida con `shutil.which()`: nada de comandos que no existen |
| `calcular()` | evaluador sobre AST con lista blanca. `eval()` fuera |
| red | un solo socket en `agent.llm`, con el candado en la primera línea; `vectores._pedir` lleva el suyo |
| persistencia | limpieza recursiva y anclada a `Path(__file__).parent` |

## La rama de proyecto

Cuando `plan.needs_project` es cierto, `pipeline.ejecutar` toma una **rama**, no otro
pipeline. Los pasos 1-9 son idénticos — abrir un segundo camino es el bug que abrió la
auditoría y costó dos fases cerrar.

```
… contexto
   └─ ¿needs_project?
        espec + plano            1 llamada: qué archivos, qué exporta cada uno
        generación por grupos    3-4 llamadas: núcleo · dominio · tests · docs
        Proyecto.sellar()        a partir de aquí el árbol no cambia
        ├ estructura             ¿hay entrypoint? ¿hay tests? ¿hay __init__.py?
        ├ sintaxis               py_compile / node --check
        ├ importaciones          interno roto (ERROR) ≠ dependencia ausente (LÍMITE)
        ├ tests                  por la sonda: un marcador por test
        ├ comando documentado    el que el README le dice al usuario que escriba
        ├ crud                   HTTP real contra el servidor del proyecto
        └ certificado            derivar_estado(), el único sitio que lo decide
        manifiesto (sha256) → ZIP → reapertura → registro → /descarga?id=…
```

| módulo | responsabilidad |
|---|---|
| `proyecto.py` | el artefacto y **el único sitio donde nace una ruta** |
| `dependencias.py` | clasificar imports con AST y `sys.stdlib_module_names` |
| `sondas.py` | el arnés que escribe Mirag, con nonce por ejecución |
| `verificacion_proyecto.py` | la cadena y `derivar_estado` |
| `empaquetado.py` | ZIP determinista + 13 comprobaciones de integridad |
| `artefactos.py` | registro con ids opacos y aislamiento |
| `generador.py` | las 5-7 llamadas y el contrato de interfaces entre grupos |

**`rapido.guardar` no se usa aquí**: aplana las rutas con `Path(ruta).name` y vacía
`salida/` entera. Un proyecto va a `artefactos/<id>/`, con su propia carpeta.

## La capa de producto

Sobre el pipeline, tres cosas que son el producto y no adorno:

| | dónde | qué garantiza |
|---|---|---|
| `server.panel_evidencia()` | server.py | las cuatro capas, separadas; `VERIFIED` ⊆ `MODEL CLAIM` |
| `server._linea_de_tiempo()` | server.py | la traza legible; pliega el retrieval **sin perder tiempo** |
| `demos.CANONICAS` + `demos.correr()` | demos.py | las tres demos con contrato declarado y ejecutable |

La página consume esos tres como **datos**, no como markdown, y `tests/test_demos_contratos.py` los
comprueba contra el servidor real levantado en un puerto libre.

Regla que costó un bug encontrar: **lo observado por el ejecutor manda sobre cualquier etiqueta
calculada aparte.** La vista del código dependía de un evento que el pipeline no emite, y decía
"nadie ha comprobado este código" con seis marcadores en verde.

## Qué NO hay

Ni ColBERT, ni caché semántica integrada, ni grafo avanzado, ni reranker remoto, ni model routing
real, ni streaming, ni multi-turno. Nada de eso entra antes de que exista un solo camino verificable
— y eso es lo que estas fases construyeron.
