# Cómo ver Mirag funcionando

## Arrancar

```bash
/opt/homebrew/bin/python3 server.py
```

Abre <http://127.0.0.1:8000>. Escucha **solo en loopback**: `/` y `/index.html` son las dos únicas
rutas que existen; cualquier otra devuelve 404.

## Sin gastar un céntimo

Con `MIRAG_OFFLINE=1` (el valor por defecto) hay **tres demos preparadas**. La decisión del modelo
viene de un guion fijo, y la página lo marca con el chip `simulado`. Todo lo demás —plan,
recuperación, contexto, ejecución, verificación— es real.

| pregunta | qué vas a ver |
|---|---|
| `¿Qué es un índice de PostgreSQL y cuándo no sirve?` | el retrieval entero: plan, tres índices, contexto, suficiencia |
| `Crea calculator.py con calculate(a, b, operation) y sus tests` | genera código, **lo ejecuta** y lo verifica con marcadores reales |
| `Crea una función divide(a, b) que maneje la división por cero, con tests` | el bucle de reparación: falla, se arregla, se vuelve a ejecutar |

**Cualquier otra pregunta offline responde `SIN MODELO`** y no inventa nada. Eso es deliberado:
antes, preguntar *"¿qué es Raft?"* devolvía un párrafo seguro sobre índices de PostgreSQL.

## Con modelo real

```bash
MIRAG_OFFLINE=0 LIMITE_USD=0.50 /opt/homebrew/bin/python3 server.py
```

Las cinco demos del release, **medidas** (Fase 7, $0.0438 en total):

| demo | pregunta | seg | coste | resultado observado |
|---|---|---|---|---|
| A · conceptual | ¿Qué es un índice de PostgreSQL y cuándo deja de servir? | 10,1 | $0.0061 | 14 trozos, 2.833 tok, suficiencia `cubierto` |
| B · código | Crea calculator.py … con marcadores `TEST:<id>:PASS` | 18,1 | $0.0183 | **verde · 11 de 11 marcadores · 9 propiedades verificadas** |
| C · fuera del corpus | ¿Cómo implemento consenso Raft…? | 17,4 | $0.0064 | suficiencia `mencionado` → la respuesta empieza avisando |
| D · multi-salto | ¿Qué relación hay entre el outbox pattern y la idempotencia en pagos? | 42,3 | $0.0071 | 4 cajas, 3.408 tok |
| E · símbolos | ¿Dónde se decide si una etapa del pipeline se ejecuta? | 9,2 | $0.0059 | **5 símbolos** del propio repo en el contexto |

La demo C es la importante: el corpus no cubre Raft, el pipeline lo dice **antes** de responder, y
lo dice también con el modelo real delante.

## Qué mirar en la pantalla

Cada etapa es una tarjeta con su estado y su procedencia. Lo que hay que leer:

- **`evidencia de ejecución` vs `lo dice el modelo`** — la insignia de cada tarjeta. Es la
  diferencia entre lo que ocurrió y lo que alguien afirma.
- **el chip de verificación** — `verde` solo si hubo marcadores y todos pasaron.
  `sin evidencia` si el comando terminó bien pero no imprimió ninguno: eso **no** es aprobar.
- **la tabla de evidencia** — una fila por propiedad declarada, con el estado que decidió la
  ejecución, no el modelo.
- **la tabla de anti-patrones** — qué trajo el corpus y qué demostró la ejecución. Dice
  explícitamente que el buscador devuelve un número fijo *"relevantes o no"*, porque no hay
  medición que diga cuáles aplican.
- **el aviso de afirmación no respaldada** — si el modelo dice "los tests pasaron" y no hay
  marcadores, sale un banner encima y **el texto del modelo se deja entero** para que lo juzgues.

## Las trazas

Cada ejecución escribe una línea con 32 campos en `trazas_noche.jsonl`:

```bash
/opt/homebrew/bin/python3 traza.py
```

Incluye el plan, los ids de los trozos recuperados, las medidas del contexto, el veredicto de
ejecución con sus marcadores, las propiedades con su texto, la cobertura de anti-patrones, los
intentos de reparación, los fallbacks y los errores por etapa. `decision_simulada` distingue un
doble de una llamada real, y `model_route` es `null` porque no hay router — no se inventa.

## Los tests

```bash
for f in test_*.py; do /opt/homebrew/bin/python3 "$f"; done
```

Sin pytest: cada archivo es su propio runner. No hacen ni una llamada al modelo.

---

# Las tres demos, por comando

```bash
python3 demos.py todas
```

Ejecuta las tres canónicas con el candado puesto (**$0**) y enseña, por cada una, qué se exigía y
qué se observó. Con `MIRAG_OFFLINE=0` corren contra el modelo real.

```bash
python3 demos.py conocimiento     # el corpus contesta
python3 demos.py construccion     # genera, ejecuta y verifica
python3 demos.py abstencion       # dice que no sabe
python3 demos.py proyecto         # genera un PROYECTO entero y lo empaqueta
```

## La demo de proyecto, con todos los números

```bash
python3 demos/demo_proyecto.py              # offline determinista, $0
python3 demos/demo_proyecto.py --online     # con modelo real
python3 demos/demo_proyecto.py --romper hash # fuerza un fallo de integridad, para verlo
```

Hace lo mismo que el servidor, sin navegador: ejecuta la petición, genera el proyecto, lo
verifica **ejecutándolo**, lo empaqueta, reabre el ZIP, lo descomprime en un temporal y
corre sus tests ahí — que es exactamente lo que hará quien lo descargue.

```
proyecto      libros-api · 14 archivos · 391 lineas
estado        VERIFICADO
marcadores    16/16
zip           8,408 bytes · e5376f382fbf950c236cebe6
integridad    13 comprobaciones, todas OK
tiempo        2.9s
```

Y con `--romper` se ven los caminos de fallo, que es lo que hace que existan:

```
❌ los hashes del ZIP == los del artefacto   app/main.py: hash distinto
⛔ No hay descarga: no se puede demostrar que el ZIP sea lo que se verifico.
```

Lo que se exige de cada una está en [DEMO_CONTRACTS.md](DEMO_CONTRACTS.md) y lo comprueba
`tests/test_demos_contratos.py`. En la página, los tres botones bajo la caja de texto lanzan exactamente
esas tres.

## Cómo leer lo que sale

**El panel de evidencia** es lo primero que hay que mirar. Cuatro bloques que no comparten sitio a
propósito:

| bloque | qué es | qué **no** es |
|---|---|---|
| `MODEL CLAIM` | lo que el modelo dijo que cubriría | un hecho |
| `OBSERVED` | el comando, su resultado y sus marcadores | una opinión |
| `VERIFIED` | declarado **y** demostrado | garantía de que el código sea correcto |
| `NOT VERIFIED` | declarado y no demostrado | que esté mal — significa que nadie lo probó |

**La tarjeta de recuperación** resume en una línea: cuántos fragmentos, de qué índices, por qué
etapas. Las etapas apagadas aparecen con su motivo (`vector: desactivado`), porque que Mirag **no**
usara algo es información. El detalle completo va detrás de *Ver detalles*.

**Qué pasó, en orden** es la traza legible: una fila por etapa, con su tiempo. Las quince etapas
internas del retrieval se pliegan en una — sin perder el tiempo que costaron.

**La tarjeta del proyecto** tiene tres estados y ninguno se escribe a mano:

| | cuándo | botón |
|---|---|---|
| `Proyecto listo para descargar` | integridad OK **y** estado `VERIFICADO` | sí |
| `la verificación no está completa` | integridad OK, estado `PARCIAL`/`VALIDADO` | sí — el ZIP es lo que se generó, y eso sí se puede afirmar |
| `ARTIFACT INTEGRITY ERROR` | los hashes no cuadran | **no**, y no hay de dónde sacarlo |

El árbol sale del manifiesto y el botón usa la URL que manda el backend: la página no la
compone, así que un fallo de integridad no puede acabar en un enlace que funciona por
accidente.

**El coste** no finge precisión: una ejecución simulada dice `SIMULADO · $0`, no `$0.0000`.
