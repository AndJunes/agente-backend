# 12 · Observability

> Monitoring responde a preguntas que **ya sabías** que ibas a hacer (¿está caído?). Observability te deja
> responder a las que **no anticipaste** (¿por qué solo falla para los usuarios de este plan desde iOS?).
> La diferencia es la cardinalidad y el contexto que guardas.


**Cubre del temario:** `logging` · `metrics` · `tracing` · `alerting` · `dashboards` · `implementations` · `failure_modes`

---

## Los tres pilares (y el cuarto)

| | Qué es | Coste | Responde a |
|---|---|---|---|
| **Logs** | eventos discretos con contexto | alto (volumen) | ¿qué pasó exactamente aquí? |
| **Metrics** | series temporales numéricas agregadas | bajo | ¿cómo va el sistema en general? |
| **Traces** | el recorrido de una request por los servicios | medio | ¿dónde se fue el tiempo? |
| **Profiles** | dónde se gasta CPU/memoria en el código | medio | ¿qué función concreta cuesta? |

**La regla de uso:** las **métricas** te dicen que algo va mal y disparan la alerta. Las **trazas** te dicen
dónde. Los **logs** te dicen qué pasó exactamente. El *profiling continuo* te dice qué línea. Usarlos en ese
orden es lo que separa una investigación de 10 minutos de una de 4 horas.

> **Ficha** · **Cuándo:** al diseñar la observabilidad de un servicio ·
> **Patrón:** métricas para alertar → trazas para localizar → logs para el detalle → profiler para la línea ·
> **Anti-patrón:** intentar investigar todo con `grep` sobre logs ·
> **Límites:** los tres cuestan dinero y crecen con el tráfico ·
> **Cómo falla:** sin correlación entre ellos, cada pilar es una isla y la investigación se alarga horas ·
> **Decisión:** el `trace_id` es lo que los une; sin él tienes tres herramientas inconexas ·
> **Trade-off:** granularidad vs coste ·
> **Relacionado:** correlation IDs, tracing `[10]`

---

## OpenTelemetry

En 2026 es el estándar de facto: **graduó en la CNCF en mayo de 2026**, el mismo estatus que Kubernetes y
Prometheus. Traces, metrics y logs son estables en los SDKs principales; el *profiling* entró en alpha
pública en marzo de 2026 y todavía no se recomienda para cargas críticas.

**Por qué importa:** instrumentas **una vez** con una API neutral y decides el backend después
(Grafana, Datadog, Honeycomb, Jaeger…). Te quita el vendor lock-in de la observabilidad, que era el
argumento comercial de todos los proveedores.

**Arquitectura:**
```
Tu app (SDK OTel) → OTel Collector → uno o varios backends
                        ↑
            aquí filtras, samplas, enriqueces y rediriges
            sin volver a tocar ni desplegar la aplicación
```

- **Auto-instrumentación** para frameworks, clientes HTTP y drivers de DB: te da el 80% gratis.
- **Instrumentación manual** para lo que importa de tu dominio (spans de negocio, atributos como `plan`,
  `tenant_id`).
- **Semantic conventions:** nombres estandarizados (`http.request.method`, `db.system`) para que las
  herramientas entiendan tus datos sin configuración.

> **Ficha** · **Cuándo:** en cualquier servicio nuevo, en 2026 ·
> **Patrón:** instrumentar con la API neutral y decidir el backend después ·
> **Anti-patrón:** instrumentar con el SDK propietario de un proveedor ·
> **Límites:** el profiling entró en alpha en marzo de 2026: aún no para cargas críticas ·
> **Cómo falla:** sin Collector, cambiar de backend obliga a redesplegar todos los servicios ·
> **Decisión:** el Collector es donde filtras, sampleas y enriqueces sin tocar la app ·
> **Trade-off:** una pieza más que operar vs independencia del proveedor ·
> **Relacionado:** sampling, semantic conventions `[13]`

---

## Structured logs

**La regla de 2026: JSON estructurado, con campos consistentes, siempre.** Los logs en texto libre no se
pueden consultar de forma fiable.

```json
{"ts":"2026-09-15T04:12:33Z","level":"error","service":"api","env":"prod",
 "trace_id":"4bf92f...","span_id":"00f067...","request_id":"req_01J8XZ",
 "user_id":"u_42","tenant_id":"t_7","event":"pago_fallido",
 "importe":5000,"divisa":"EUR","proveedor":"stripe","codigo":"card_declined",
 "duracion_ms":842}
```

**Lo que hace bueno a un log:**
- **`trace_id` y `span_id` inyectados automáticamente** por la librería. Sin eso no puedes saltar de un log
  a la traza completa, que es el 80% del valor.
- **Campos, no frases.** `"pago fallido de 50 EUR para u_42"` no se agrega; los campos sí.
- **Niveles con criterio:** `ERROR` = algo requiere acción humana. Si tu `ERROR` incluye validaciones de
  usuario, nadie mirará los errores. `WARN` = anómalo pero tolerado. `INFO` = hitos de negocio.
  `DEBUG` = apagado en producción (o activable por muestreo).
- **Nunca loguees secretos ni PII**: contraseñas, tokens, tarjetas, emails completos según tu política.
  Redacta en la capa de logging, no confiando en que cada dev se acuerde.
- **Sampling de logs** en endpoints de altísimo volumen: loguea el 1% de los éxitos y el 100% de los errores.

> **Ficha** · **Cuándo:** siempre; el texto libre no se consulta de forma fiable ·
> **Patrón:** JSON con campos consistentes y `trace_id` inyectado automáticamente ·
> **Anti-patrón:** frases en vez de campos, y `ERROR` para validaciones de usuario ·
> **Límites:** el volumen de logs puede costar más que la infraestructura ·
> **Cómo falla:** un log del request completo acaba conteniendo tokens o tarjetas `[06, 07]` ·
> **Decisión:** redacta en la capa de logging, no confiando en que cada dev lo recuerde ·
> **Trade-off:** detalle vs coste y riesgo de filtrar datos ·
> **Relacionado:** correlation IDs, PII `[06, 15]`

---

## Metrics

**Tipos:** `counter` (solo sube: requests, errores) · `gauge` (sube y baja: conexiones activas, uso de
memoria) · `histogram` (distribución: latencias — **el que necesitas para percentiles**) · `summary`.

**Las cuatro señales de oro (Google SRE):**
1. **Latencia** — y separa la de las peticiones con éxito de la de los errores (un 500 instantáneo puede
   mejorarte la media y ocultar el problema).
2. **Tráfico** — RPS, mensajes por segundo.
3. **Errores** — ratio, no valor absoluto.
4. **Saturación** — lo lleno que está el recurso más limitado (CPU, memoria, pool, cola).

También se usa **RED** (Rate, Errors, Duration) para servicios y **USE** (Utilization, Saturation, Errors)
para recursos.

**La trampa de la cardinalidad:** cada combinación única de etiquetas es una serie temporal. Poner
`user_id` como label en Prometheus con un millón de usuarios te tumba el sistema de métricas y te cuesta una
fortuna. **Alta cardinalidad va en trazas y logs, no en métricas.** Es uno de los errores más caros y más
preguntados.

**Histogramas y percentiles:** no se puede calcular el p99 global promediando los p99 de cada instancia.
Por eso los histogramas guardan buckets y el percentil se calcula sobre la suma de buckets.

> **Ficha** · **Cuándo:** para alertar y para ver tendencias ·
> **Patrón:** las cuatro señales de oro con histogramas (no medias) ·
> **Anti-patrón:** etiquetas de alta cardinalidad (`user_id`, `request_id`, URLs con IDs) ·
> **Límites:** cada combinación de etiquetas es una serie temporal ·
> **Cómo falla:** la explosión de cardinalidad tumba el backend de métricas y dispara la factura ·
> **Decisión:** separa la latencia de éxitos de la de errores (un 500 instantáneo mejora la media y oculta el problema) ·
> **Trade-off:** dimensiones útiles vs coste ·
> **Relacionado:** percentiles, SLOs `[09, 10]`

---

## Distributed tracing

Una **traza** es un árbol de **spans**; cada span es una operación con inicio, fin, atributos y eventos.
El **contexto** (`traceparent`, del estándar W3C Trace Context) se propaga por los headers HTTP y por los
mensajes de las colas.

**Lo que resuelve:** en microservicios, "la request tardó 3 segundos" es inútil. La traza te enseña que 2,7s
se fueron en una llamada al servicio de inventario que a su vez hizo 47 queries — el N+1 **hecho visible**.

**Sampling:**
- **Head-based:** decides al principio (ej. 1% de todo). Barato y simple, pero **puedes perder justo la
  request que falló**.
- **Tail-based:** decides al final, cuando ya sabes cómo fue: **te quedas el 100% de los errores y de las
  lentas**, y un porcentaje de las normales. Mucho mejor señal por euro; necesita el Collector, que debe
  buffear la traza entera. **Es la recomendación de 2026** para equilibrar coste y visibilidad.
- **Propaga el contexto también por las colas** (mete `traceparent` en los headers del mensaje) o perderás
  la traza en cuanto algo se vuelva asíncrono.

> **Ficha** · **Cuándo:** en cuanto haya más de un servicio o trabajo asíncrono ·
> **Patrón:** tail-based sampling — quédate el 100% de errores y lentas ·
> **Anti-patrón:** head-based al 1% que descarta justo la petición que falló ·
> **Límites:** el tail-based exige buffear la traza completa antes de decidir ·
> **Cómo falla:** sin propagar el contexto por las colas, la traza se corta ·
> **Decisión:** propaga `traceparent` también en los headers de los mensajes ·
> **Trade-off:** coste de almacenamiento vs poder investigar el caso raro ·
> **Relacionado:** colas, W3C Trace Context `[08]`

---

## Correlation IDs

- **`request_id`** generado en el borde (o aceptado del cliente si confías) y propagado a **todo**: logs,
  llamadas salientes, mensajes de cola, y devuelto en la respuesta y en los errores.
- **Regla de oro:** el usuario reporta un problema con un ID que aparece en su pantalla, y tú encuentras
  toda la historia con una sola búsqueda. Sin esto, el soporte es adivinación.
- Con OpenTelemetry, el `trace_id` cumple esta función; mantén también un `request_id` legible para el
  soporte humano.
- Añade **identificadores de negocio** como atributos: `tenant_id`, `pedido_id`, `plan`. Son los que
  permiten responder "¿esto afecta solo a los clientes enterprise?".

> **Ficha** · **Cuándo:** en toda petición que entre al sistema ·
> **Patrón:** generar en el borde, propagar a todo, devolver en la respuesta y en los errores ·
> **Anti-patrón:** que cada servicio genere el suyo y no se propague ·
> **Límites:** solo sirve si **todos** los componentes lo respetan ·
> **Cómo falla:** el usuario reporta un problema y no hay forma de encontrar su petición ·
> **Decisión:** añade identificadores de negocio (`tenant_id`, `pedido_id`) como atributos ·
> **Trade-off:** un campo más en cada log a cambio de investigaciones de minutos en vez de horas ·
> **Relacionado:** tracing, error contracts `[03]`

---

## Health checks

```
GET /health/live    → ¿el proceso está vivo?   (sin dependencias; para liveness)
GET /health/ready   → ¿puede atender tráfico?  (DB, cache, migraciones; para readiness)
GET /health/startup → ¿ya terminó de arrancar?
```

**El error clásico:** meter las dependencias en la liveness. Si la base de datos parpadea, Kubernetes
**reinicia todos tus pods a la vez** y convierte una degradación en una caída total. Dependencias → readiness.

**Distingue duro de blando:** si la DB principal cae, no estás listo. Si el servicio de recomendaciones cae,
sigues listo pero degradado. Un health check que se pone en rojo por una dependencia opcional causa
incidentes que no existían.

> **Ficha** · **Cuándo:** todo servicio bajo un orquestador o balanceador ·
> **Patrón:** `live` sin dependencias · `ready` con dependencias duras y blandas separadas ·
> **Anti-patrón:** meter la base de datos en la liveness ·
> **Límites:** un check que solo hace ping al puerto declara sano a un servicio inútil ·
> **Cómo falla:** la DB parpadea y Kubernetes **reinicia todos los pods**, convirtiendo una degradación en caída ·
> **Decisión:** dependencia opcional caída = sigues listo, degradado ·
> **Trade-off:** checks profundos (detectan más) vs riesgo de reinicios en cascada ·
> **Relacionado:** probes, graceful shutdown `[10, 13]`

---

## Alerts

**La regla: alerta sobre síntomas que afectan al usuario, no sobre causas.** "La CPU está al 90%" no es un
problema si nadie lo nota; "el 5% de los checkouts fallan" siempre lo es.

- **Basadas en SLO y error budget** (`10-reliability.md`): alerta cuando el ritmo de consumo del presupuesto
  de error implica incumplir el objetivo — **burn rate alerting**. Es lo que evita alertar por cada pico
  irrelevante.
- **Accionables:** cada alerta debe tener una acción clara y un runbook. Si la respuesta es "mirar y no hacer
  nada", bórrala.
- **Fatiga de alertas:** es el fallo más común y el más grave. Un equipo que recibe 50 alertas al día deja
  de mirarlas y se pierde la importante. **Menos alertas y mejores > más alertas.**
- **Niveles:** página (despierta a alguien, solo si hay impacto en usuarios y es urgente) vs ticket
  (se mira en horario laboral) vs solo dashboard.

> **Ficha** · **Cuándo:** al definir el on-call ·
> **Patrón:** alertas por burn rate del error budget, con runbook y dueño ·
> **Anti-patrón:** 50 alertas al día — la gente deja de mirarlas y se pierde la importante ·
> **Límites:** alertar sobre causas (CPU) genera ruido; sobre síntomas, señal ·
> **Cómo falla:** **fatiga de alertas**: el fallo más común y el más grave ·
> **Decisión:** página (despierta a alguien) solo con impacto real y urgente; el resto, ticket ·
> **Trade-off:** detectar antes vs despertar a la gente por nada ·
> **Relacionado:** SLOs, incident response `[10]`

---

## Dashboards y error tracking

**Dashboards:**
- Uno de **visión general por servicio** (las cuatro señales de oro) que se pueda leer en 10 segundos.
- Uno de **recorrido de usuario** (embudo de negocio: registros, checkouts, pagos), que suele detectar
  incidentes antes que los técnicos.
- Dashboards de investigación, creados durante los incidentes y conservados.
- **Un dashboard que nadie mira durante un incidente es un dashboard mal diseñado.**

**Error tracking** (Sentry y similares): agrupa excepciones por huella, con stack, versión de release,
usuario afectado y breadcrumbs. Complementa a los logs porque **deduplica y cuenta**: "este error afectó a
1.243 usuarios desde la v2.4.1" es accionable; 1.243 líneas de log no lo son.

**Retención típica (2026):** métricas 12+ meses (tendencias y capacity planning), trazas 7-30 días,
logs 14-90 días con archivado en frío a partir de los 30. El coste de la observabilidad puede superar al de
la propia infraestructura: por eso se samplea, se controla la cardinalidad y se filtra en el Collector.

> **Ficha** · **Cuándo:** antes del primer incidente, no durante ·
> **Patrón:** uno de visión general legible en 10 segundos + uno de recorrido de negocio ·
> **Anti-patrón:** 40 gráficas que nadie mira cuando hay prisa ·
> **Límites:** un dashboard muestra lo que ya sabías que querías ver ·
> **Cómo falla:** durante el incidente nadie encuentra la gráfica relevante ·
> **Decisión:** el error tracking deduplica y cuenta: "afectó a 1.243 usuarios" es accionable, 1.243 líneas de log no ·
> **Trade-off:** más paneles vs claridad bajo presión ·
> **Relacionado:** métricas de negocio, incident response `[10]`

---

## Implementación: instrumentar un servicio

```python
# 1) Arranque: una sola vez, con los atributos que identifican al servicio
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

FastAPIInstrumentor.instrument_app(app)      # HTTP entrante: gratis
AsyncPGInstrumentor().instrument()           # queries: gratis
tracer = trace.get_tracer("pedidos")
medidor = metrics.get_meter("pedidos")

pedidos_creados = medidor.create_counter("pedidos_creados_total")
duracion_cobro  = medidor.create_histogram("cobro_duracion_ms")   # histograma -> percentiles

# 2) Spans manuales SOLO para lo que importa del dominio
async def crear_pedido(actor, body):
    with tracer.start_as_current_span("crear_pedido") as span:
        span.set_attribute("tenant_id", actor.tenant_id)     # alta cardinalidad: OK en trazas
        span.set_attribute("plan", actor.plan)
        pedido = await servicio.crear(actor, body)
        span.set_attribute("pedido.total_centimos", pedido.total.centimos)
        pedidos_creados.add(1, {"plan": actor.plan})         # BAJA cardinalidad en metricas
        return pedido

# 3) Logs con trace_id inyectado automaticamente
import structlog
def anadir_traza(_, __, evento):
    ctx = trace.get_current_span().get_span_context()
    if ctx.is_valid:
        evento["trace_id"] = format(ctx.trace_id, "032x")
        evento["span_id"] = format(ctx.span_id, "016x")
    return evento

structlog.configure(processors=[anadir_traza, structlog.processors.JSONRenderer()])
```

**La regla de oro de los atributos:** `tenant_id`, `user_id` y `pedido_id` van en **trazas y logs**
(alta cardinalidad, ahí es barato). En **métricas** solo etiquetas de baja cardinalidad (`plan`, `region`,
`status_code`) — cada combinación única es una serie temporal, y `user_id` con un millón de usuarios te
tumba el backend de métricas y la factura.

**Propagar el contexto por una cola** (si no, pierdes la traza en cuanto algo se vuelve asíncrono):

```python
from opentelemetry.propagate import inject, extract

# productor
cabeceras = {}
inject(cabeceras)                                    # mete traceparent
await broker.publicar(evento, headers=cabeceras)

# consumidor
ctx = extract(mensaje.headers)
with tracer.start_as_current_span("procesar_pedido", context=ctx):
    await procesar(mensaje)
```

> **Ficha** · **Cuándo:** todo servicio, desde el primer despliegue ·
> **Patrón:** auto-instrumentación para el 80% + spans manuales para el dominio ·
> **Anti-patrón:** `user_id` como etiqueta de métrica ·
> **Límites:** cada span y cada etiqueta cuestan almacenamiento y dinero ·
> **Cómo falla:** sin propagar el contexto a las colas, la traza se corta y el flujo asíncrono es invisible ·
> **Decisión:** si el dato identifica a **uno**, va en traza o log; si agrupa a **muchos**, en métrica ·
> **Trade-off:** granularidad vs coste y cardinalidad ·
> **Relacionado:** cardinalidad, colas, correlation IDs `[08]`

---

## Monitorizar en producción: qué hay que tener montado

Lo mínimo el día que un servicio recibe tráfico real:

- **Dashboard por servicio** con las cuatro señales de oro, comparado con la semana anterior.
- **Alertas basadas en SLO** (burn rate), no en umbrales técnicos arbitrarios `[10]`.
- **Un dashboard de negocio**: registros, pedidos, pagos por minuto. **Suele detectar incidentes antes que
  las métricas técnicas** — si los pedidos caen a cero y la CPU está normal, algo está roto de una forma
  que tu monitorización técnica no ve.
- **Marcar los despliegues en las gráficas.** Hace obvio el "¿qué cambió?", que es la primera pregunta
  de todo incidente `[10]`.

**Qué observar para detectar cada tipo de fallo:**

| Fallo | Señal que lo delata | Dónde |
|---|---|---|
| Dependencia degradada | latencia de salida por dependencia | métrica + traza |
| Pool agotado | conexiones en uso / espera de adquisición | métrica |
| Cola atascada | **consumer lag** y edad del mensaje más viejo | métrica `[08]` |
| Outbox parado | antigüedad del evento sin publicar | métrica `[08]` |
| Memory leak | memoria creciente entre reinicios | métrica |
| Bucle de reintentos | ratio de reintentos sobre peticiones | métrica |
| Fuga de datos / IDOR | **nada** — por eso hace falta audit log `[17]` | audit |
| Cambio de plan en la DB | p99 de una query concreta | métrica + `pg_stat_statements` |
| Certificado por caducar | días restantes | check sintético |
| Coste desbocado | gasto por servicio y por día | alerta de presupuesto `[13]` |

**Lo que no se ve en las métricas** es lo más peligroso: fugas de datos, corrupción silenciosa y
consumidores que procesan mal pero sin errores. Para eso hacen falta audit logs y conciliación `[07, 17]`.

> **Ficha** · **Cuándo:** antes de que el servicio reciba tráfico real ·
> **Patrón:** alertar sobre síntomas de usuario; dashboards de negocio junto a los técnicos ·
> **Anti-patrón:** alertar por CPU alta — si nadie lo nota, no es un problema ·
> **Límites:** los fallos silenciosos no aparecen en ninguna métrica ·
> **Cómo falla:** el sistema "funciona" mientras lleva dos horas de retraso procesando ·
> **Decisión:** si una alerta no tiene acción clara y runbook, bórrala ·
> **Trade-off:** cobertura de alertas vs fatiga (y la fatiga es lo que hace que se ignore la importante) ·
> **Relacionado:** SLOs, incident response, coste `[10, 13]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Diferencia entre monitoring y observability?**
Monitoring comprueba condiciones conocidas de antemano; observability permite investigar lo desconocido
gracias al contexto y la alta cardinalidad. *Señal:* lo aterrizas — con monitoring sabes que el error rate
subió; con observability descubres que solo afecta a los usuarios de un tenant concreto tras un despliegue.

**Q: Llega una alerta de latencia alta. ¿Cuál es tu proceso?**
Confirmar impacto real en usuarios → mirar las señales de oro para acotar el servicio → traza de una request
lenta para ver dónde se va el tiempo → logs de ese span → correlacionar con despliegues y cambios recientes.
*Señal:* empiezas por el impacto y por "¿qué cambió?", no por hipótesis técnicas sueltas.

**Q: ¿Por qué no poner `user_id` como etiqueta de una métrica?**
Explosión de cardinalidad: cada valor crea una serie temporal nueva. *Señal:* dices dónde sí va esa
información (trazas y logs) y que es uno de los errores que más dinero cuesta en facturas de observabilidad.

**Q: ¿Head-based o tail-based sampling?**
Tail-based si puedes permitirte el Collector: te quedas con los errores y las lentas, que son las que
importan. *Señal:* mencionas el coste (hay que buffear la traza completa hasta decidir) y que head-based
tiene la pega de descartar precisamente el caso interesante.

**Q: ¿Qué metes en la liveness probe?**
Nada externo. Solo que el proceso responde. *Señal:* explicas el fallo en cascada — dependencias en la
liveness convierten una degradación de la DB en un reinicio masivo de todos los pods.

**Trade-off central de esta caja:** *visibilidad vs coste y ruido*. Guardarlo todo es carísimo e
inutilizable; guardar poco te deja ciego justo cuando importa. El equilibrio de 2026 es: métricas baratas y
de baja cardinalidad para alertar, trazas con tail-sampling para investigar, logs estructurados y muestreados
para el detalle, y todo correlacionado por `trace_id`.

---

## Fuentes

- [OpenTelemetry docs](https://opentelemetry.io/docs/) — graduó en la CNCF en mayo de 2026.
- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) (señales de oro) y [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) (burn rate).
- [W3C Trace Context](https://www.w3.org/TR/trace-context/) — el estándar de propagación.
- [OpenTelemetry Best Practices 2026: cómo controlar el coste](https://www.apica.io/blog/opentelemetry-best-practices-for-improving-your-monitoring-and-observability/)
- [Observability in 2026: distributed tracing y OpenTelemetry](https://dev.to/zny10289/observability-in-2026-distributed-tracing-replaced-logs-and-opentelemetry-won-8lm)
