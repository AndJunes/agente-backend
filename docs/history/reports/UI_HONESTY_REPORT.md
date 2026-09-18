# Fase 6 — UI honesta · $0.00

## El bug que cierra la fase

Con el candado offline puesto, el servidor elegía el fixture con una regex de tres literales:
**cualquier pregunta que no dijera "calculator" recibía un párrafo fijo y seguro sobre índices de
PostgreSQL.** Preguntar *"¿qué es Raft?"* devolvía esa explicación de índices, con un aviso de
"decisión simulada" debajo.

El aviso era cierto y el conjunto mentía igual. Un fixture que responde **con seguridad a la
pregunta equivocada** es exactamente lo que este proyecto existe para no hacer — y encima parece una
alucinación del modelo cuando es un fixture mal elegido.

## Cómo queda

`demos.py` mantiene **tres demos preparadas**, cada una con lo que demuestra:

| demo | qué demuestra |
|---|---|
| `conceptual` | retrieval visible: plan, tres índices, contexto, suficiencia |
| `codigo` | generar código, **ejecutarlo** y verificarlo con marcadores reales |
| `reparacion` | el bucle de arreglo: código roto, fallo observado, segunda pasada |

Y para cualquier otra pregunta **no se inventa nada**:

```
Antes  →  "¿Qué es Raft?"  →  "Un indice de PostgreSQL es una estructura que acelera..."
Ahora  →  "¿Qué es Raft?"  →  "El corpus MENCIONA raft pero no lo desarrolla..."
                              ⛔ SIN MODELO — el plan, la recuperación y el contexto de
                                 arriba son reales; la respuesta no existe y no se inventa.
```

Lo que **no** es simulado sigue corriendo y enseñándose entero: plan, recuperación sobre los tres
índices, contexto, veredicto de suficiencia. Es lo único honesto que se puede enseñar sin modelo, y
se enseña.

## Simulado ≠ sin modelo

Son dos estados distintos y confundirlos era el bug. Ahora hay dos chips y dos avisos:

| | chip | qué afirma |
|---|---|---|
| demo preparada | `simulado` 🧪 | la decisión viene de un guion fijo, pero **responde a lo que preguntaste**; lo recuperado, ejecutado y verificado es real |
| fuera de las demos | `sin modelo` ☁️ | no hay respuesta, y no se fabrica una |

El chip **sale de un evento emitido por el backend**, no de una suposición de la página. El test que
lo comprueba levanta el servidor real en un puerto libre y lee los eventos SSE — la primera versión
de ese test grepeaba `server.py`, que es justo el anti-patrón que el resto del proyecto persigue.

## Un detalle de orden que habría vuelto a morder

Las demos se reconocen **de lo más específico a lo más general**. Con el orden al revés,
*"crea calculator.py que use un índice"* se llevaba la demo conceptual: una petición de código
respondida con un párrafo sobre índices. El mismo error de la fase, en pequeño. Hay un test por cada
solapamiento.

## Modos retirados que seguían en la página

La UI conservaba avisos de `rapido` y `simple`, retirados en la Fase 2 — uno de ellos recomendaba
*"el modo rápido lo ejecuta y el arquitecto además lo revisa"*. Un aviso que menciona un modo
inexistente es ruido, no honestidad. Fuera, y un test impide que vuelvan.

Lo que queda, unificado para los dos modos que existen:
- **con código ejecutado**: *"Verde aquí significa se ejecutó y pasó, no es correcto"*, con el
  ejemplo del test de idempotencia secuencial que pasa con una condición de carrera dentro.
- **arquitecto**: aviso de experimental, *"lo que veas aquí es lo que dice el modelo, no evidencia
  de ejecución"*.

## Chips

Los cuatro que faltaban, con estilo propio: `simulado`, `sin modelo`, `experimental`, `desactivado`
— junto a los ocho que ya había (`ejecutando`, `completado`, `advertencia`, `error`,
`no verificado`, `omitido`, `fallback`, `evidencia insuficiente`).

## Regresión

**321 casos, 17 suites, 0 rojas.** 307 al empezar la fase; los 14 nuevos son `test_ui_honesta.py`.
