# ¿Cuántas veces de diez el modelo produce un proyecto que pasa sus propios tests?

**Cero.**

```
VERIFICADO   0/10
PARCIAL      2/10
VALIDADO     1/10
FALLIDO      7/10
```

10 corridas independientes, misma petición, modelo real (`claude-haiku-4.5`).
**$1.5161 · $0.1516 de media · 146 s de mediana · 5,4 llamadas por corrida.**

---

## Las diez, una por una

| # | estado | archivos | marcadores | rep. | dónde se rompió |
|---|---|---|---|---|---|
| 1 | `FALLIDO` | 19 | — | 0 | **sintaxis**: `src/app.py:66` — una cadena sin cerrar |
| 2 | `PARCIAL` | 17 | 26/42 | 2 | tests: 16 en FAIL tras dos reparaciones |
| 3 | `FALLIDO` | 14 | — | 0 | estructura: sin archivos de tests |
| 4 | `VALIDADO` | 20 | — | 0 | **importó `urllib2`**, que es de Python 2 |
| 5 | `FALLIDO` | 12 | — | 0 | estructura: sin archivos de tests |
| 6 | `FALLIDO` | 12 | — | 0 | estructura: sin archivos de tests |
| 7 | `FALLIDO` | 7 | — | 0 | estructura: sin archivos de tests |
| 8 | `FALLIDO` | 19 | — | 2 | importaciones: `libros_api/__init__.py` no define `crear_servidor` |
| 9 | `PARCIAL` | 18 | **56/56** | 1 | el CRUD no se pudo ejercitar: faltan las 7 operaciones |
| 10 | `FALLIDO` | 11 | — | 0 | estructura: sin archivos de tests |

Mediana de 15 archivos, de 7 a 20. Ninguna corrida agotó el tope de llamadas.

## Dónde se rompe, ordenado

| fase | veces | ¿de quién es el problema? |
|---|---|---|
| **estructura** (sin tests) | **5** | del modelo: el plano los pide y el grupo `tests` devuelve 0 archivos |
| tests en rojo | 2 | del modelo: su código no pasa sus propios tests |
| importaciones | 1 | del modelo: promete un símbolo que no define |
| sintaxis | 1 | del modelo: una cadena sin cerrar |
| dependencia ausente | 1 | `urllib2`, que no existe en Python 3 |

**Ninguna se rompió en Mirag.** Las diez llegaron a empaquetarse y las diez pasaron las
13 comprobaciones de integridad: `integridad del ZIP: 10/10`, `descargables: 10/10`.

## Lo más interesante: la corrida 9

```
ok      estructura        ok      sintaxis        ok      importaciones
fallo   tests             ok      reparacion:1    ok      tests (tras arreglo)
fallo   comando documentado                       fallo   crud
→ PARCIAL · 56/56 marcadores
```

**Los 56 marcadores de sus propios tests pasan**, la reparación funcionó, y aun así el
estado es `PARCIAL`. El motivo está escrito: *"los tests pasan, pero el CRUD no se pudo
ejercitar entero: faltan 7 operaciones"*. La sonda de integración de Mirag no consiguió
levantar su servidor, así que **no hay ni una prueba de que la API responda por HTTP**.

Sospeché que era un bug mío —que una fase reparada siguiera contando como rota— y no lo
es: el estado es correcto. Un proyecto cuyos tests pasan pero cuya API no se puede
arrancar no está verificado, y decirlo es justamente el trabajo.

## Lo que esto dice, y lo que no

**Dice** que la máquina funciona: genera, detecta el fallo real en cada caso, repara
cuando puede, empaqueta, comprueba la integridad y entrega el ZIP etiquetado como lo que
es. En diez de diez el estado se correspondió con la evidencia observada. En ninguna dijo
`VERIFICADO` sin serlo.

**No dice** que Mirag sepa generar una API REST por dominios que funcione a la primera.
Con esta petición, este modelo y esta máquina: **0 de 10**. La demo canónica que sale en
verde usa un proyecto escrito a mano en `fixture_proyecto.py`, y la tarjeta lo marca como
`decisión simulada` por eso.

## Dos errores míos que encontró la primera medición

La primera tanda fue inválida y conviene decir por qué.

**1. El presupuesto era acumulado, no por corrida.** `agent.PRESUPUESTO` acumula dentro
del proceso y solo se reinicia en `server.do_POST`. Con `LIMITE_USD=1.00`, el banco se
quedó sin margen en la séptima y las corridas 7-10 salieron como `EXCEPCION` sin haber
ocurrido. Arreglado: el medidor reinicia el tope por corrida, como hace el servidor.

**2. Dejaba que el modelo decidiera si el proyecto lleva tests.** Tu propio prompt lo dice
—*"NO CONFIAR EN EL LLM PARA LA ESTRUCTURA"*— y yo lo estaba haciendo: si el plano venía
sin `tests/`, se generaban trece archivos y se suspendían después. Ahora `completar_plano`
añade las entradas que faltan y el modelo solo pone el contenido.

Ese arreglo **no resolvió el problema**, y ahí está lo interesante: en las corridas que
fallan, el plano **sí** trae los 6 archivos de tests y es la generación del grupo la que
devuelve cero. Medido:

```
especificacion    22 archivos planeados, con tests/__init__.py, tests/test_models.py …
generacion:nucleo    11 archivos
generacion:dominio    4 archivos
generacion:tests      0 archivos     ← aquí
generacion:docs       1 archivos
→ FALLIDO: estructura incompleta, no hay ningun archivo de tests
```

## Una causa que todavía no está observada

`0 archivos` era un silencio: no distinguía *"el modelo contestó en prosa"* de *"el JSON
del tool-call venía cortado"*. Ya está instrumentado —el paso ahora registra cuál de las
dos fue, con el tamaño y el final del JSON crudo— pero **la corrida de diagnóstico salió
bien y no llegué a capturar un fallo con la instrumentación puesta**. Así que la causa
concreta sigue sin observarse, y lo digo en vez de suponerla.

La hipótesis razonable, sin respaldo todavía: seis archivos de tests en una sola llamada
es el grupo más grande del plano, y el más propenso a cortarse. Si se confirma, el arreglo
es partir `tests` en dos llamadas — pero eso se decide **cuando haya un caso observado**,
no ahora.

## Contexto

| | |
|---|---|
| tests de Mirag | **444 casos, 20 suites, 0 rojas** |
| coste de esta medición | $1.5161 + $0.46 de diagnósticos |
| acumulado del proyecto | **~$4.7** (ver abajo) |
| datos crudos | `benchmarks/proyectos.json`, una entrada por corrida |
| reproducir | `python3 banco_proyectos.py 10` (`--seco` para el guion, $0) |

## Un tercer error mío, que encontró el propio banco

Al cuadrar el gasto, la suma de `coste_usd` de las trazas daba **$7,08** y el gasto real
era ~$4,7. La diferencia no era un redondeo:

```
coste_usd de la primera tanda:  0.153 · 0.309 · 0.465 · 0.622 · 0.786 · 0.942
llamadas:                           4 ·     9 ·    14 ·    20 ·    25 ·    30
```

Son **acumulados**, no costes por corrida. `traza.escribir` lee `agent.PRESUPUESTO`
directamente, que acumula por proceso; el servidor lo reinicia en cada petición, pero un
script que ejecuta varias seguidas no. Así que cada fila anotaba el total corrido y sumar
la columna contaba la primera corrida seis veces: **$2,3 de más**.

Es exactamente el patrón de siempre —el número registrado no es lo que pasó— en la
columna que se usa para controlar el presupuesto. Arreglado: la traza anota el delta de
esa ejecución, con un test que corre tres seguidas en el mismo proceso y exige
`[1, 1, 1]` en vez de `[1, 2, 3]`.

## Qué haría con esto

1. **Capturar un fallo del grupo `tests` con la instrumentación puesta.** Es una corrida
   de $0.15 y decide si el arreglo es partir la llamada o cambiar el prompt.
2. **No enseñar la demo con modelo real todavía.** 0 de 10 no es una demo; es un
   diagnóstico. La versión con guion sí se puede enseñar, marcada como simulada.
3. **No tocar la petición para que salga mejor.** Pedir algo más fácil subiría el número
   sin cambiar nada real.
