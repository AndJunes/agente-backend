# Fase 4 — Hacer verificable todo lo que el pipeline afirma

**Coste de la fase: $0.0299 de un techo de $2.00.** Una sola llamada real, y el informe explica
abajo por qué hizo falta exactamente esa y ninguna más.

La regla de la fase: `MODEL CLAIM ≠ OBSERVED RESULT ≠ VERIFIED EVIDENCE`. La pregunta no era
*"¿tengo una propiedad llamada `reranker=True`?"* sino *"¿lo que guardé dice la verdad sobre lo que
acaba de pasar?"*.

---

## 1. Los tres casos nombrados del defecto sistémico

| # | afirmación | qué la observaba antes | ahora |
|---|---|---|---|
| 1 | el reranker mejora el contexto | nada: se medía un ranking descartado | cerrado en la Fase 2 (SHA distinto ON/OFF) |
| 2 | el pipeline repara el código | nada: 2 llamadas y la traza decía `arreglado: false` | `repair_attempts` y `arreglado` salen del estado de ejecución, con 3 tests |
| 3 | los tests verifican el entorno del usuario | nada: escribían en `salida/` y borraban su entrega | test de ciclo cerrado: entrega → suite completa → entrega intacta |

Y un cuarto que apareció durante la fase, en la sección 5.

## 2. El truncado destruía evidencia

`salida[-4000:]` conservaba el final. Una corrida que imprimía `TEST:x:PASS` temprano y luego 9.600
caracteres de ruido perdía el marcador: **verde pasaba a `sin_evidencia`**. Peor, un `FAIL` enterrado
en el medio desaparecía y **una corrida fallida se leía como verde**.

`skills._recortar_sin_perder_marcas()` conserva principio y final y re-adjunta los marcadores que se
hayan caído en el corte. Cuatro casos lo fijan: marcador temprano, marcador tardío, `FAIL` enterrado
(ahora `rojo`, antes invisible) y el aviso explícito de que la salida se recortó.

## 3. Anti-patrones: se cierra el hueco que abrió la Fase 2

`rapido.py` afirmaba desde hacía tiempo que los anti-patrones eran *"de cubrimiento OBLIGATORIO"* y
nadie lo comprobaba. `obligaciones.py` convierte cada anti-patrón recuperado en una obligación con
identidad y la cruza contra la evidencia. Cuatro estados, los cuatro alcanzables:

| estado | qué significa |
|---|---|
| `cubierta` | el modelo declaró una propiedad que lo trata **y** un marcador real la demostró |
| `declarada` | el modelo dijo que lo cubría y la ejecución no lo demostró |
| `no cubierta` | ninguna propiedad declarada lo trata |
| `no verificable` | el anti-patrón no tiene términos distintivos suficientes para cruzarlo |

Hacen falta **las dos cosas**: que el modelo lo declarara y que la ejecución lo demostrara. Un test
exige que con evidencia vacía **nada** salga `cubierta` — un falso "cubierta" sería la mentira de
siempre con ropa nueva.

## 4. La única llamada real de la fase, y qué movió

**Motivo:** los dobles prueban el mecanismo, pero las propiedades que cruza `obligaciones.cobertura`
las escribí yo. El cruce podía estar pasando **por construcción**. Eso es literalmente el defecto que
la fase persigue, cometido por mí, dentro del módulo que existe para evitarlo.

**1 llamada · $0.0299 · `reservar(conn, plaza_id, usuario)` con tests.** Resultado observado:

```
final_status=verde · 10 de 10 marcadores PASS · propiedades: 10 verificadas
antipatrones: {'no cubierta': 6}
```

Diez marcadores en verde, incluido un test `concurrencia` que lanza dos hilos sobre la misma plaza
— y **los seis anti-patrones sin cubrir**. Eso obligaba a elegir entre dos explicaciones, y la
investigación (offline, gratis) dio la respuesta.

## 5. El cuarto caso del defecto: mi propio texto

Los seis anti-patrones recuperados para una tarea de concurrencia fueron:

```
capa de integración · property-based testing · diagramas · E2E tests · requisitos · integration tests
```

**Ninguno habla de concurrencia.** El `no cubierta: 6` era honesto. Lo deshonesto era la frase que yo
había escrito en la tabla: *"El corpus los trajo porque aplican a esta tarea"*. Una afirmación fuerte
con nada detrás.

Antes de cambiar el texto probé si había un umbral que separase señal de relleno. **No lo hay:**

| consulta | top-1 recuperado | score |
|---|---|---|
| `Implementa reservar(...)· dos usuarios no pueden quedarse con la misma plaza` | "Diseñar una capa de integración" (irrelevante) | **10.63** |
| `API de reservas: dos usuarios no pueden quedarse con la misma plaza` | "Transacciones y ACID" (relevante) | **4.72** |

Un corte por score mataría el bueno y dejaría el malo. BM25 devuelve *k* resultados por consulta haya
o no relación: una consulta sobre diagramas de secuencia también recibe sus seis.

**Decisión: no se pone umbral y la tabla deja de afirmar relevancia.** Ahora dice que el buscador
devuelve un número fijo "relevantes o no", y se presenta como registro, no como veredicto. Dos tests
lo fijan, incluido uno que fallará si algún día los scores *sí* se vuelven separables — momento en el
que habría que medir un umbral en vez de descartarlo.

La causa de fondo (el índice de anti-patrones rinde mal con prompts largos de implementación) queda
**medida y abierta**, no tapada. No se arregla con presupuesto de esta fase.

## 6. La traza pasa de 17 a 32 campos

Los dos últimos los añadí porque los sufrí: para auditar la corrida real de la sección 4 tuve que
rebuscar en carpetas temporales, porque la traza guardaba `{'no cubierta': 6}` y no **cuáles** ni
**por qué**.

```
plan · filtros · retrieval · contexto · verificacion · antipatrones · cobertura_antipatrones
propiedades_detalle · antipatrones_detalle · repair_attempts · final_status · fallbacks
errores · model · model_route · tools · decision_simulada · coste_usd
```

Reglas que se mantienen: lo que no aplica es `null`, **no inventado** (`model_route: null` porque no
hay router); `decision_simulada` distingue un doble de una llamada real, y `model` dice
`"doble determinista"` en vez de fingir un modelo.

## 7. Fronteras de error

Cada etapa falla por separado y queda registrada por etapa. Probado: un fallo de persistencia
(`OSError: disco lleno`) deja `Paso("persistencia", estado="error")`, escribe el error en la traza
**y la respuesta y la evidencia llegan igual** — el trabajo ya estaba pagado y verificado. Un JSON de
entrega roto se registra bajo `etapa: entrega` sin contaminar las demás.

## 8. SSE y traza dicen lo mismo

Un test ejecuta una petición capturando los eventos emitidos y los compara con el estado persistido:
los `ids` de retrieval que vio la UI son los mismos que se guardaron, y el verde que pintó la
interfaz es el `final_status` del disco. Si divergen, falla.

## 9. Trazabilidad de punta a punta

Un chunk concreto se sigue por los cuatro sitios: `RetrievalResult` → paso de recuperación → prompt
real del modelo (`messages[-1]["content"]`) → traza persistida. El test nombra en qué eslabón se
rompe si se rompe.

## 10. `ProjectState` deriva del repositorio

`_modos_reales()` lee los modos del *dispatch del servidor* en vez de repetirlos a mano, y
`_simbolos()` saca 49 módulos / 32 clases / 259 funciones del índice real, con `NOT AVAILABLE` y
motivo si falla.

**Corrección a mi propia auditoría:** afirmé que la lista `archivos` de `estado.py` estaba escrita a
mano y desactualizada. **Es falso** — es un `glob` y devuelve los 43 módulos, incluidos
`recuperacion.py` y `obligaciones.py`.

## 11. Regresión

**296 casos, 15 suites, 0 rojas.** 270 al empezar la fase; los 26 nuevos son `test_evidencia.py`.

La suite completa se corrió **dos veces**: tras los cambios de evidencia y otra vez tras tocar
`traza.py` y `pipeline.py`. Es la regla que salió del incidente `simbolos=error`: una consulta pagada
no debe descubrir un bug que se descubre gratis.

## 12. Presupuesto

| | |
|---|---|
| Techo de la fase | $2.00 |
| Gastado | **$0.0299** (1 llamada) |
| Acumulado del sistema de 8 fases | $0.1663 |

No se gastó más porque no había más afirmaciones que solo un modelo real pudiera mover. Todo lo demás
—truncado, fronteras de error, SSE vs traza, trazabilidad, reparación— se demuestra mejor con dobles
deterministas que con una llamada, y sin pagar.

## 13. Lo que sigue sin estar verificado

| | |
|---|---|
| Relevancia del índice de anti-patrones en prompts largos | **medido y malo**, sección 5. Sin arreglar |
| La tabla por familia de `ganancias.json` | existe; runtime siempre pasa `familia="general"` |
| `arquitecto` | EXPERIMENTAL, sin validadores, cero presupuesto (Fase 5) |
| Modo offline por regex | responde con seguridad a la pregunta equivocada (Fase 6) |
| `banco.py` a nivel agente | migrado estructuralmente, medición real en la Fase 7 |
