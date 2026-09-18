# Mirag genera proyectos, no archivos sueltos

Una frase entra. Sale un proyecto de 14 archivos con sus capas, sus tests y su README,
**ejecutado y verificado**, empaquetado en un ZIP que se descomprime y funciona sin editar
nada.

```
Creá una API REST de libros con CRUD completo. Arquitectura por dominios:
separá router, service, repository, schemas y models. Agregá tests.
        ↓  2,8 s offline · 5 llamadas al modelo
libros-api · 14 archivos · 391 líneas · VERIFICADO · 16/16 marcadores
[ Descargar ZIP ]  8.409 bytes · 13 comprobaciones de integridad
        ↓  descomprimir y ejecutar
Ran 9 tests in 0.520s — OK
```

## Lo que se probó antes de escribir una línea

Tres suposiciones sostenían el diseño entero. Las tres se verificaron **ejecutando**.

**1. Un proyecto stdlib ejercita CRUD real dentro del verificador que ya existía.**
`skills.verificar_codigo` valida rutas con `is_relative_to` y crea subdirectorios desde
antes de esto: ya sabía ejecutar árboles. Un proyecto de 3 archivos con
`http.server` + `sqlite3`: **0,59 s de los 30 de límite, 8 de 8 marcadores**, POST/GET/
GET-id/PUT/DELETE contra sockets reales.

**2. El ZIP puede ser determinista y comprobable.** `zipfile` + `ZipInfo(date_time` fijo`)`
+ orden alfabético: mismos bytes en dos construcciones, reabrible, hashes que cuadran y
que **detectan un archivo cambiado**.

**3. Un import interno roto se distingue de una dependencia ausente, solo con AST.** Es lo
que hace honesto el caso FastAPI.

## Una precondición que bloqueaba todo

El detector de "me piden código" **no entendía el imperativo rioplatense**, que es como
escribe el usuario:

```
needs_code=False   Creá una API REST de libros con CRUD...
needs_code=True    Crea una API REST de libros con CRUD...     ← solo cambia la tilde
```

La petición canónica de esta misma fase, tecleada por el usuario, no habría disparado
nada. Medido tras el arreglo: **11/11 en castellano, 9/9 en rioplatense, 1 falso positivo
sobre 49** consultas conceptuales (el mismo de antes, `worker pool en python`).

Y un detector nuevo, `plan.pide_proyecto`, medido contra tres conjuntos:

| conjunto | resultado |
|---|---|
| peticiones de proyecto | 6/7 |
| peticiones de un archivo suelto | **10/10** |
| consultas conceptuales | **49/49** |

Cero falsos positivos. El que falla —*"Armá un bot de Telegram con comandos y
persistencia"*— es genuinamente ambiguo, y está **documentado con su test** en vez de
forzar el umbral y abrir falsos positivos.

## La arquitectura

```
petición → plan → retrieval (3 índices) → contexto        ← todo esto ya existía
    │
    └─ plan.needs_project ?
         └─ espec + plano  →  generación por grupos  →  Proyecto (sellado)
                                    ↓
            estructura → sintaxis → imports → tests → comando del README → CRUD
                                    ↓
                       certificado (estado derivado de evidencia)
                                    ↓
                     manifiesto con hashes → ZIP → reapertura → registro
```

**Una rama dentro de `pipeline.ejecutar`, no un pipeline paralelo.** Abrir un segundo
camino es el bug que abrió la auditoría y costó dos fases cerrar. Los pasos 1–9 son
idénticos; lo único que cambia es que en vez de pedir un archivo se pide un plano.

### Los módulos nuevos

| | qué hace |
|---|---|
| `proyecto.py` | el artefacto, el árbol, y **el único sitio donde nace una ruta** |
| `dependencias.py` | clasifica cada import: interno / stdlib / externo |
| `sondas.py` | el arnés de pruebas **que escribe Mirag**, con nonce por ejecución |
| `verificacion_proyecto.py` | la cadena, y la única función que decide el estado |
| `empaquetado.py` | el ZIP y las 13 comprobaciones de integridad |
| `artefactos.py` | el registro: ids opacos, aislamiento, ciclo de vida |
| `generador.py` | espec + plano + grupos + reparación selectiva |
| `fixture_proyecto.py` | el proyecto de la demo, en texto, que **se ejecuta de verdad** |

`rapido.guardar` **no se usa** para proyectos: aplana las rutas con `Path(ruta).name` y
vacía `salida/` entera, así que `app/libros/router.py` y `tests/test_libros.py`
colisionarían después de borrar lo anterior.

## Por qué el CRUD es evidencia y no autoevaluación

Si los tests de integración los escribe el mismo modelo que escribió el código, el modelo
puede aprobarse a sí mismo. **El arnés lo escribe Mirag**, y sus identificadores llevan un
nonce generado en Python en cada ejecución: `TEST:crud_persiste_a3f19c2b:PASS`. El modelo
no puede adivinarlo, así que no puede fabricarlo.

Y la sonda no comprueba que exista un handler de PUT: comprueba que **el PUT persista**.
Con un servidor cuyo update no escribe:

```
PASS  crud_crear      PASS  crud_listar     PASS  crud_obtener
FAIL  crud_actualizar FAIL  crud_persiste   PASS  crud_borrar   PASS  crud_borrado
```

## Import roto ≠ dependencia ausente

```
INTERNO  app.core.bd                      ✓ resuelve
INTERNO  app.libros.inexistente           ✗ ERROR    → se repara
EXTERNO  fastapi                          no instalado → LÍMITE, no es un bug del proyecto
stdlib   json · sqlite3 · http.server
```

**La gravedad es la frontera.** Un `ERROR` puede llevar a `FALLIDO`; un `LÍMITE` pone un
**techo** al estado y nunca lo hunde. Sin esta distinción, el bucle de reparación se
pondría a "arreglar" imports que están bien.

Un proyecto FastAPI, trazado entero: se genera, compila, su grafo de imports resuelve, y
el estado queda en **`VALIDADO`** con este motivo literal:

> *el código compila y su grafo de imports resuelve, pero no se pudo ejecutar: fastapi no
> está instalado en esta máquina. El proyecto puede estar bien; aquí no hay evidencia de
> que lo esté.*

Hay un test, `fastapi_jamas_llega_a_verificado`, que lo fija.

## El estado, derivado de evidencia

| estado | qué lo produce |
|---|---|
| `FALLIDO` | estructura rota, no compila, o quedan imports internos rotos |
| `GENERADO` | hay archivos y nada se pudo ejecutar |
| `VALIDADO` | compila y resuelve; no ejecutable aquí por dependencias ausentes |
| `EJECUTADO` | corrió y **no imprimió un solo marcador** — eso no es aprobar |
| `PARCIAL` | hay marcadores en FAIL, o una fase se ejecutó y quedó muda |
| `VERIFICADO` | todos los marcadores pasan, incluido el CRUD entero por HTTP |

`derivar_estado()` es la **única** función que devuelve estos literales, y hay un test que
recorre el AST de los 59 módulos buscando `return` de uno de ellos fuera de su sitio.
`skills.veredicto` existe porque el verde estuvo re-derivado en ocho sitios; no se repite.

## Un VERIFICADO falso que produjo mi propio código

La primera versión dio `VERIFICADO` con esta cadena:

```
tests   SIN EVIDENCIA: el comando termino sin error y no imprimio ningun marcador
crud    TESTS EN VERDE · 7 de 7
=> VERIFICADO
```

Los 9 tests del proyecto corrieron y no produjeron evidencia, y **los 7 marcadores del
CRUD arrastraron el estado**. Una fase muda, tapada en silencio por otra que sí habló —
exactamente lo que este proyecto existe para no hacer.

Dos arreglos: los tests del proyecto pasan **siempre** por la sonda (que emite un marcador
por test, así la evidencia no depende de que al modelo se le ocurra imprimirla), y
`derivar_estado` rechaza `VERIFICADO` si cualquier fase se ejecutó y quedó muda. El test
`una_fase_muda_no_puede_quedar_tapada` lo fija.

Ahora son **16 marcadores**: 9 de los tests del proyecto + 7 del CRUD.

Y una fase más, `comando documentado`: se ejecuta **el comando que el README le dice al
usuario que escriba**, porque es el que va a escribir quien descomprima el ZIP. Si falla,
el estado baja a `PARCIAL` aunque todo lo demás esté verde.

## Lo que NO está demostrado, y es lo más importante de este informe

Las cifras de arriba —14 archivos, 16/16 marcadores, `VERIFICADO`— salen de la demo
**offline**, cuyo proyecto está escrito a mano en `fixture_proyecto.py`. Con modelo real,
esta misma tarea no ha llegado nunca a `VERIFICADO`:

| corridas | estado | coste |
|---|---|---|
| 21 | `VERIFICADO` | **$0.00 — todas con el guion** |
| 2 | `FALLIDO` | $0.145 · modelo real |
| 1 | `PARCIAL` · 16/49 marcadores · 2 reparaciones | $0.196 · modelo real |

**Cero `VERIFICADO` con modelo real.** La maquinaria entera funciona —plan, generación por
grupos, imports, ejecución, reparación, empaquetado, integridad, descarga— y lo que está
demostrado es *eso*: que la máquina hace lo que dice y **no miente cuando el proyecto no
sale bien**. Lo que no está demostrado es que el modelo produzca un proyecto que pase sus
propios tests a la primera.

La última corrida es la que mejor lo cuenta: imports resueltos, tests en rojo, dos
reparaciones que tocaron 1 y 2 archivos, y sigue en rojo por un `Libro(...)` cuya firma no
cuadra con sus propios tests. Estado final `PARCIAL`, ZIP ofrecido con sus 13
comprobaciones en verde y etiquetado como lo que es.

Por eso la tarjeta de la página distingue los dos casos. Un `VERIFICADO` salido del guion
sale como **`Proyecto listo — decisión simulada`**, con esta frase:

> *El código lo escribió un guion fijo, no el modelo: lo que se ejecutó, verificó y
> empaquetó es real, pero esto no demuestra que el modelo genere un proyecto así.*

Hay un test que lo fija, `un_verificado_con_guion_se_marca_como_simulado`.

## Coste

| | |
|---|---|
| llamadas por proyecto | **5** (espec+plano, núcleo, dominio, tests, docs) |
| tope duro | `generador.MAX_LLAMADAS = 7` |
| offline determinista | **$0**, 2,8 s |

La consistencia entre llamadas la sostiene el contrato de interfaces: cada grupo recibe
qué exporta cada archivo ya generado y qué está pendiente, más el **código real** de sus
dependencias directas. El prompt no crece con el proyecto. Y después se comprueba con AST:
declarar no es cumplir.
