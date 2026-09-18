# Los contratos de las demos

`444 tests, 0 rojas` no es el final de la verificación. El banco a nivel agente descubrió un
`plan.needs_code` roto que la suite entera no cubría — gastando dinero. La lección no es que
faltaran tests: es que **lo que se enseña tiene que estar bajo contrato**, no bajo captura de
pantalla.

Estas tres demos son el producto. Si una deja de cumplir, no hay demo.

## El contrato

`demos.CANONICAS` declara, por demo, qué se exige. `demos.correr(clave)` la ejecuta de verdad y
devuelve qué se observó y si cuadra. No hay interpretación por medio: los datos salen de la
`Ejecucion` real.

```bash
python3 demos.py todas          # las tres, con el candado puesto, $0
python3 demos.py construccion   # una
python3 tests/test_demos_contratos.py # los 27 contratos
```

| demo | exige |
|---|---|
| **proyecto** | hay proyecto · ≥10 archivos · estado `VERIFICADO` · integridad OK · **7 marcadores de CRUD** · hay URL de descarga |
| **conocimiento** | hay respuesta · hubo retrieval · **no** entrega código · suficiencia `cubierto` o `mencionado` |
| **construccion** | hay respuesta · hubo retrieval · entrega código · **se ejecutó** · estado `verde` · ≥1 propiedad verificada |
| **abstencion** | hay respuesta · hubo retrieval · **no** entrega código · suficiencia `mencionado` o `ausente` · **avisa antes de responder** |

## Verificado con modelo real

| demo | seg | coste | observado |
|---|---|---|---|
| conocimiento | 8 | $0.0063 | suficiencia `cubierto`, sin código |
| construccion | 19 | $0.0199 | **verde · 11 propiedades verificadas** |
| abstencion | 7 | $0.0063 | suficiencia `mencionado`, avisa primero, sin código |

**$0.0325 · 3 llamadas.** Las tres cumplen su contrato también fuera de la simulación.

## Qué comprueban los 27 casos

**Los tres contratos** · que la abstención avise **antes** de responder · que la demo de código
explique *qué hizo* antes de la tabla de evidencia · que el verde nunca se presente como "correcto".

**El panel de evidencia**: que `claim`, `observed`, `verified` y `not_verified` no se mezclen · que
sin ejecución no haya nada observado · que **nada pueda quedar VERIFIED sin que el modelo lo
declarara primero**.

**La traza**: que la vista pliegue las quince etapas internas de retrieval en una · que al plegar
**no se pierda tiempo** · que lo persistido siga entero.

**El coste**: que un doble no se disfrace de `$0.0000`.

**Contra el servidor real**, levantado en un puerto libre: que el panel y la traza lleguen por SSE ·
que la abstención sobreviva · que una pregunta fuera de las demos responda `SIN MODELO`.

**Que una demo no contamine a la siguiente**: dos pasadas dan el mismo resultado · la conceptual no
hereda la entrega de la de código · ninguna escribe en `salida/`.

**La página**: dos modos y uno etiquetado experimental · que el JavaScript **parsee**, porque un
error de sintaxis la deja en blanco sin que nadie se entere · y que se pueda leer en un móvil (meta
viewport y las cuatro capas apiladas en una columna por debajo de 560px).

## Dos bugs que encontraron estos contratos

**1. La página contradecía al backend.** La sección de código decía *"Código entregado, sin
evidencia de ejecución — nadie ha comprobado este código"* mientras la respuesta, dos centímetros
más abajo, decía *"TESTS EN VERDE · 6 de 6 marcadores"*. La causa: el veredicto de la vista salía de
un evento `verificar_codigo` que **el pipeline nunca emite** (emite un `Paso` llamado
`verificacion`), así que en modo pipeline siempre caía en la rama pesimista. Ahora lee lo
**observado** por el ejecutor, que es el mismo objeto que va a la traza.

**2. Una demo anunciaba una y corría otra.** La pregunta de `construccion` decía "división por cero"
y el reconocedor por texto se la llevaba al guion de `reparacion`: el chip anunciaba
`demo «reparacion»`. Ahora cada demo **declara** su guion en vez de re-descubrirlo, y un test falla
si la declaración y el texto no coinciden.

Los dos son el mismo patrón de siempre: algo se afirmaba y nada lo observaba.
