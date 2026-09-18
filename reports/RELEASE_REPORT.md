# Fase 7 — Release

## Release gate

| criterio | resultado | evidencia |
|---|---|---|
| ninguna suite roja | **PASA** | 331 casos, 17 suites |
| la UI no afirma lo que el backend no hizo | **PASA** | los chips salen de eventos SSE; test que levanta el servidor real y los compara con la traza |
| ningún mock pasa por real | **PASA** | `decision_simulada` en la traza, chips `simulado` / `sin modelo`, y `SIN MODELO` para lo que no es demo |
| el retrieval medido es el usado | **PASA** | fuente única; test de identidad por ids de trozo entre producción y benchmark |
| una respuesta no se pierde por un error posterior | **PASA** | fallo de persistencia inyectado: `Paso("persistencia", error)`, respuesta y evidencia intactas |
| no hay secretos accesibles por HTTP | **PASA** | `/.env`, `/trazas.jsonl`, `/eval_cache.json`, `/server.py`, `/../.env` → 404, verificado con curl |
| ninguna tool ejecuta código arbitrario | **PASA** | lista blanca por `shutil.which()`, sin `shell=True`; canario en disco sobrevive a `;`, `&&` y `\|` |
| el modo real se ejecutó | **PASA** | 5 demos + 10 tareas de banco con `MIRAG_OFFLINE=0` |

## Seguridad — regresiones

```
/.env                      404      /trazas.jsonl        404
/trazas_noche.jsonl        404      /eval_cache.json     404
/index.html.bak            404      /server.py           404
/../.env                   404      /benchmarks/…json    404
/index.html                200
bind: 127.0.0.1:8000 · desde 192.168.100.6 → sin conexión
calcular(): 9 ataques, 0 colados · 2+3*4 = 14
imports fuera de stdlib: NINGUNO (47 módulos)
```

Un hallazgo que resultó no serlo, y vale la pena por cómo se resolvió: `python3 t.py; rm -rf .`
parecía colarse. **No se cuela** — `subprocess.run` corre sin `shell=True`, así que el `;` llega
como argumento literal y `python3` sale con exit 2. **Mi sonda era mala**: buscaba el texto
"no permitido" y el rechazo llegaba por otra vía, así que confundía *rechazado* con *ejecutado y
falló*. El test que quedó comprueba un canario en disco, no un mensaje.

## Rendimiento (sin modelo, offline)

| | mediana | máximo |
|---|---|---|
| retrieval sobre los tres índices | 19,1 ms | 41,2 ms |
| pipeline completo salvo el modelo | 9,7 ms | 12,8 ms |
| índice de símbolos, 1ª vs 2ª | 192 ms → **55 ms** | cache por `(ruta, mtime)` |

## Las 5 demos con modelo real — $0.0438

| demo | seg | coste | resultado observado |
|---|---|---|---|
| A conceptual | 10,1 | $0.0061 | 14 trozos, 2.833 tok, suficiencia `cubierto` |
| B código | 18,1 | $0.0183 | **verde · 11 de 11 marcadores · 9 propiedades verificadas** |
| C fuera del corpus | 17,4 | $0.0064 | suficiencia `mencionado`: la respuesta empieza avisando |
| D multi-salto | 42,3 | $0.0071 | 4 cajas, 3.408 tok |
| E símbolos | 9,2 | $0.0059 | **5 símbolos** del propio repo en el contexto |

Cinco de cinco sin un solo error de etapa. La C es la que importa: la abstención aguanta con el
modelo real delante.

## `banco.py` — la medición a nivel agente

Cinco tareas de concurrencia en Node.js, dos brazos, sobre `pipeline.ejecutar`. El brazo
`baseline` va sin acotar por cajas; `v1.1` con el filtro de metadatos activo.

| | baseline | v1.1 | |
|---|---|---|---|
| entregan código | 4/5 | **5/5** | v1.1 mejor |
| **verde** | **1/5** | **1/5** | igual |
| éxito verificado medio | **0.36** | 0.20 | baseline mejor |
| contexto medio | 3.789 tok | **2.991 tok** | v1.1 −21% |
| latencia total | **330 s** | 524 s | baseline mejor |
| coste | **$0.2906** | $0.3391 | baseline mejor |
| llamadas | 8 | 10 | |

### Lo que esto dice, y lo que no

**No hay evidencia de que acotar por cajas haga de Mirag una herramienta mejor.** Reduce el
contexto un 21% y hace la entrega más consistente (5/5 frente a 4/5), y a cambio es más lento, más
caro y no mejora lo verificado — si acaso lo empeora. Con **n=5** esa diferencia no es
distinguible del ruido, así que la lectura honesta es *"no se demostró ganancia"*, no *"el filtro
es malo"*.

Es exactamente el tipo de resultado por el que existe este banco. La métrica de retrieval decía
que el filtro ayuda; la métrica de **agente** no lo confirma. Son preguntas distintas y ahora se
pueden hacer las dos.

**Lo que sí se confirmó, y es lo más importante de esta tabla:** de diez ejecuciones con modelo
real sobre problemas de concurrencia, **dos terminaron en verde**. Los cuatro estados del veredicto
aparecieron solos, sin que nadie los provocara:

```
VERDE           8 propiedades verificadas
ROJO            el código se ejecutó y falló
SIN_EVIDENCIA   terminó sin error y no imprimió un solo marcador
NO_EJECUTADO    ni siquiera llegó a correr
```

`SIN_EVIDENCIA` es el que valida el diseño entero: **antes de la Fase 1, ese caso devolvía
"TESTS EN VERDE"** porque el exit code era 0. Ahora sale a la luz con modelo real y se llama por su
nombre.

### El bug que costó dinero encontrar

La primera pasada del banco midió el pipeline con `plan.needs_code` roto: **3 de 5 tareas no
generaron código**, y la tabla habría dicho algo sobre retrieval cuando el problema era el detector.
Se arregló (5/11 → 11/11 aciertos, 5 → 1 falsos positivos) y **se volvieron a correr los dos
brazos**. Los números de arriba son los de después.

## Tests

**331 casos, 17 suites, 0 rojas.** Ninguna hace una llamada al modelo. La suite completa se ejecutó
con un canario en `salida/`: la carpeta de producción queda intacta.

| | casos | | casos |
|---|---|---|---|
| `test_vectores` | 30 | `test_plan` | 27 |
| `test_evidencia` | 26 | `test_cache` | 24 |
| `test_resiliencia` | 24 | `test_cimientos` | 23 |
| `test_grafo_arbol` | 23 | `test_metadatos` | 19 |
| `test_pipeline_unico` | 18 | `test_simbolos` | 18 |
| `test_full_pipeline` | 16 | `test_auditoria` | 15 |
| `test_calibracion` | 15 | `test_seguridad` | 15 |
| `test_ui_honesta` | 14 | `test_enrutador` | 13 |
| `test_banderas` | 11 | | |

## Presupuesto de las 8 fases

| fase | techo | gastado |
|---|---|---|
| 0 · tomar control | $0 | $0 |
| 1 · seguridad | $0 | $0 |
| 2 · un solo pipeline | $0 | $0 |
| 3 · calibrar retrieval | $2 | $0.0753 |
| 4 · evidencia y observabilidad | $2 | $0.0299 |
| 5 · limpieza | $0 | $0 |
| 6 · UI honesta | $0 | $0 |
| 7 · release | $3 + $5 | **$1.1131** |
| | **$12** | **$1.2183** |

El grueso de la Fase 7 es el banco: **$0.8981 en dos corridas completas de los dos brazos**, porque
la primera midió el pipeline con el detector roto y volver a medir era la única salida honesta.

## Veredicto

**READY**, con estas cinco cosas escritas y no enterradas:

1. **Los anti-patrones recuperados no se sabe si aplican.** Medido: el top-1 irrelevante puntúa
   10.63 y uno relevante 4.72. No hay umbral defendible, así que la tabla dice qué trajo el corpus
   y deja de afirmar que aplica.
2. **La tabla por familia de `ganancias.json` no se usa en runtime.** Solo la fila `general` es
   load-bearing.
3. **El filtro por cajas no demostró ganancia a nivel agente** (arriba).
4. **`needs_code=True` no garantiza entrega**: el modelo a veces responde en prosa aunque se le
   ofrezca la herramienta. Observado 1 de 5 en el brazo baseline.
5. **`arquitecto` es experimental por decisión**, no por descuido: cero validadores, cero
   presupuesto, etiquetado en la UI.

## La prueba que abrió la auditoría, invertida

```
antes   contexto con reranker ON = contexto con reranker OFF   sha 00cb0796ccc4dfb6 (idénticos)
ahora   contexto con reranker ON ≠ contexto con reranker OFF   db3af905… (10.025) vs 9e7bed63… (8.079)
```

El retrieval que se mide es el que ve el modelo. Todo lo demás colgaba de ahí.

---

# Fase 8 — Productizar antes de añadir nada pesado

**Coste: $0.0325.** Tres llamadas, una por demo canónica, para comprobar que los contratos se
cumplen también fuera de la simulación. Ninguna tecnología nueva de retrieval, y **ni un parámetro
de BM25, RRF, reranker o símbolos tocado**.

## El cambio de fondo

La página era un panel de benchmarking: **23 tarjetas por consulta**, de las cuales 15 eran
internals de retrieval (`filtro:conocimiento`, `bm25:antipatrones`, `rrf:fallos`…) antes de que
ocurriera nada interesante. Ahora son **9**, y la recuperación cabe en una línea:

```
14 fragmentos recuperados · conocimiento:3 · antipatrones:6 · fallos:5 · bm25 → rrf → reranker
vector: desactivado
```

Los quince eventos se siguen emitiendo y siguen enteros en la traza — lo que cambió es la vista.
Hay un test que lo comprueba por los dos lados: que lleguen, y que la traza los conserve.

## El panel de evidencia

Cuatro capas que no comparten sitio, porque mezclarlas fue durante mucho tiempo la forma de que una
afirmación del modelo pareciera un hecho:

| | de dónde sale |
|---|---|
| `MODEL CLAIM` | lo que el modelo declaró que cubriría |
| `OBSERVED` | comando, resultado y marcadores, tal cual los vio el ejecutor |
| `VERIFIED` | declarado **y** demostrado |
| `NOT VERIFIED` | declarado y no demostrado — no es "está mal", es "nadie lo probó" |

Un test exige que `VERIFIED` sea **subconjunto** de `MODEL CLAIM`: nada puede quedar verificado sin
que el modelo lo declarara primero.

## Dos bugs que encontró esta fase

**1. La página contradecía al backend — el criterio que el release gate prohíbe expresamente.**
La sección de código decía *"Código entregado, sin evidencia de ejecución: nadie ha comprobado este
código"* mientras la respuesta, justo debajo, decía *"TESTS EN VERDE · 6 de 6 marcadores"*.

La causa: la vista sacaba su veredicto de un evento `verificar_codigo` que **el pipeline nunca
emite** — emite un `Paso` llamado `verificacion`. Así que en modo producción caía **siempre** en la
rama pesimista. Ahora lee lo observado por el ejecutor, que es el mismo objeto que va a la traza.

Es el patrón de siempre en una capa nueva: dos fuentes para el mismo hecho, y la que se enseña no es
la que ocurre.

**2. Una demo anunciaba una cosa y corría otra.** La pregunta de `construccion` mencionaba "división
por cero", y el reconocedor por texto se la llevaba al guion de `reparacion`: el chip anunciaba
`demo «reparacion»`. Ahora cada demo **declara** su guion, y un test falla si la declaración y el
texto no coinciden.

## Otras cosas que se arreglaron porque se vieron

- **Una tarea de código empezaba con dos líneas en blanco y saltaba a la tabla de evidencia.** Las
  decisiones del modelo —el *por qué*— no se enseñaban en ninguna parte. Ahora la respuesta abre con
  `## Qué se hizo` y una línea sobre lo que de verdad pasó al ejecutar.
- **Los anti-patrones decían "no cubierta"** sobre cosas que probablemente ni venían a cuento. Ahora
  son `RECOVERED` / `VERIFIED` / `NOT VERIFIED`: describen la relación con la entrega, no afirman
  que el anti-patrón aplique.
- **"De qué se compone el proyecto" volcaba 49 nombres de archivo en 52 líneas.** Ahora son 7 con
  por dónde entrar, y un recuento del resto.
- **El coste de un doble decía `$0.0000`**, que se lee como una ejecución real muy barata. Ahora
  `SIMULADO · $0` o `SIN MODELO · $0`, que son cosas distintas entre sí y de una llamada real.
- **Los ejemplos de la página** eran de modos retirados. Ahora son las tres demos canónicas, las
  mismas que están bajo contrato.

## Las tres demos, con modelo real

| demo | seg | coste | observado | contrato |
|---|---|---|---|---|
| conocimiento | 8 | $0.0063 | suficiencia `cubierto`, sin código | ✅ |
| construccion | 19 | $0.0199 | **verde · 11 propiedades verificadas** | ✅ |
| abstencion | 7 | $0.0063 | `mencionado`, avisa primero, sin código | ✅ |

## Tests

**359 casos, 18 suites, 0 rojas.** 331 al empezar la fase; 27 nuevos en
`test_demos_contratos.py` y uno en `test_evidencia.py`. Entre ellos, uno que ejecuta `node --check` sobre el JavaScript de la
página: un error de sintaxis la deja en blanco y ninguna prueba de backend se entera.

Regresiones de seguridad repetidas tras los cambios: `/.env`, `/trazas_noche.jsonl`, `/server.py`,
`/demos.py` → 404; `/index.html` → 200.

## Un defecto de registro, encontrado al cuadrar el presupuesto

Al sumar el gasto de la fase, el acumulado **no se movía**. Las tres llamadas reales de las demos
habían costado $0.0325 y no aparecían por ninguna parte.

La causa: `pipeline.ejecutar(guardar=False)` — que significa *"no escribas los archivos en disco"* —
**silenciaba también el registro**. Dos cosas distintas detrás de un mismo parámetro, así que tres
ejecuciones pagadas ocurrieron sin que nada las anotara. Es el defecto que ha recorrido todo este
proyecto, otra vez, en la última capa que quedaba.

Ahora el registro depende de si hubo gasto, no de si se querían archivos: **una llamada real siempre
deja traza**; un doble, que no cuesta nada, no ensucia el fichero. Verificado con una llamada real y
`guardar=False`: 427 → 428 trazas, `$0.0072`, `decision_simulada: false`.

## Presupuesto acumulado

| | |
|---|---|
| Fases 0–7 | $1.2183 |
| Fase 8 | **$0.0397** (3 demos + 1 verificación del registro) |
| **Total** | **$1.2580** |

## Lo que sigue sin resolver

Lo mismo que antes de esta fase, sin añadir nada: la relevancia de los anti-patrones recuperados ·
la tabla por familia sin usar en runtime · el filtro por cajas sin ganancia demostrada a nivel
agente · `needs_code=True` sin garantía de entrega · `arquitecto` experimental.

## Un último hallazgo, ya cerrado

Al verificar la página a 375×812 apareció que **no tenía `<meta name="viewport">`**: un móvil la
renderizaba a 980px y la enseñaba en miniatura — el panel de evidencia era ilegible aunque su grid
colapsara bien. Añadido, más una media query que apila las cuatro capas en una columna y hace que
tablas y bloques de código se desplacen **ellos**, no la página. Verificado en el navegador:
`scrollWidth == innerWidth`, sin desbordamiento horizontal. Dos tests lo fijan.

---

# Fase 9 — Mirag entrega proyectos, no archivos sueltos

La capacidad que cambia lo que Mirag *es*: de producir una respuesta con archivos sueltos a
producir un **artefacto ejecutable y verificable** que se descarga y funciona.

```
Creá una API REST de libros con CRUD completo. Arquitectura por dominios:
separá router, service, repository, schemas y models. Agregá tests.
        ↓
libros-api · 14 archivos · VERIFICADO · 16/16 marcadores · [ Descargar ZIP ]
        ↓  descomprimir y ejecutar
Ran 9 tests in 0.520s — OK
```

Detalle en [PROJECT_GENERATION_REPORT.md](PROJECT_GENERATION_REPORT.md) y
[PROJECT_ARTIFACT_INTEGRITY_REPORT.md](PROJECT_ARTIFACT_INTEGRITY_REPORT.md).

## Un agujero de seguridad que estaba vivo

Al añadir la ruta de descarga apareció que **`do_HEAD` nunca se había cerrado**:

```
GET  /.env → 404        HEAD /.env → 200 · Content-Length: 93 · Last-Modified
GET  /server.py → 404   HEAD /server.py → 200
```

`do_GET` estaba sobreescrito con lista blanca; `do_HEAD` seguía siendo el heredado, que
pasa por `translate_path()` y responde sobre el directorio entero. No filtraba el cuerpo,
pero sí que el archivo existe, cuánto mide y cuándo se tocó. Y el docstring afirmaba *"Una
sola ruta. Ni una más."*

**Sobrevivió a toda la auditoría porque los 15 tests de seguridad preguntaban con GET.**
Una prueba que solo usa un método solo demuestra ese método. Cerrado, con dos tests.

También: `do_POST` no validaba su ruta, así que `POST /descarga` ejecutaba el agente.

## Cuatro defectos que encontró el modelo real, y no los dobles

Cada corrida real costó ~$0.15 y encontró algo que el guion determinista no podía:

| # | qué pasó | qué destapó |
|---|---|---|
| 1 | el modelo generó 11 archivos **sin tests** → `FALLIDO` | el contrato no exigía tests, y el plano no se validaba hasta después de generar todo |
| 2 | escribió `python -m unittest` | el contrato no decía qué intérpretes **existen** en esta máquina (`shutil.which`) |
| 3 | declaró `depende_de: ["libros_api/api"]`, sin extensión | `Proyecto.obtener()` **lanzaba** al consultar una ruta imposible y mataba la generación entera |
| 4 | `from libros_api import crear_servidor` contra un `__init__.py` que no lo reexporta | **el bucle de reparación estaba escrito y sin cablear** |

El cuarto es el más instructivo: `generador.reparador()` y `certificar(reparador=)`
existían, y `pipeline` nunca pasaba el argumento. Declarado pero no conectado — el mismo
patrón que esta serie de fases lleva persiguiendo desde el principio, esta vez en código
que acababa de escribir. Ahora hay dos tests: uno que pasa un reparador falso y **exige
que lo llamen**, y otro que comprueba por AST que el pipeline lo conecta.

Los cuatro son honestos en un sentido que importa: **en ninguno el sistema dijo que estaba
verificado**. Dijo `FALLIDO` con el motivo real, y el ZIP se ofreció igual etiquetado como
lo que era.

## Un VERIFICADO falso que produjo mi propio código

La primera versión de `derivar_estado` dio verde con esta cadena:

```
tests   SIN EVIDENCIA: el comando termino sin error y no imprimio ningun marcador
crud    TESTS EN VERDE · 7 de 7
=> VERIFICADO
```

Los 9 tests del proyecto corrieron **mudos** y los 7 marcadores del CRUD arrastraron el
estado. Una fase sin evidencia tapada por otra que sí la tuvo.

Dos arreglos: los tests pasan siempre por la sonda (un marcador por test, así la evidencia
no depende de que al modelo se le ocurra imprimirla) y `derivar_estado` rechaza
`VERIFICADO` si cualquier fase se ejecutó y quedó muda.

## El titular honesto

Las capturas de `VERIFICADO` de esta fase salen del guion offline, cuyo proyecto escribí
yo. **Con modelo real, cero corridas llegaron a `VERIFICADO`**: dos `FALLIDO` y una
`PARCIAL` con 16 de 49 marcadores tras dos reparaciones.

Lo demostrado es la máquina: genera, ejecuta, repara, empaqueta, comprueba la integridad,
sirve el ZIP — y **dice la verdad cuando el proyecto no sale**. Lo no demostrado es que el
modelo acierte a la primera en una tarea de este tamaño. La tarjeta lo distingue con el
chip `simulado` y una frase explícita; hay un test que lo fija.

## Tests

**444 casos, 20 suites, 0 rojas.** 359 al empezar la fase. Las dos suites nuevas son
`test_proyecto.py` (32) y `test_empaquetado.py` (30), más 6 contratos de demo, 8 del
detector y 2 de seguridad.

Las dos que definen el producto:

- `lo_que_se_descarga_es_lo_que_se_verifico` — genera por HTTP, descarga por HTTP, reabre
  el ZIP y compara los hashes uno a uno con el árbol que se pintó.
- `el_zip_descargado_se_descomprime_y_sus_tests_pasan` — la promesa entera.

**0 dependencias externas en 59 módulos**, verificado por AST.
