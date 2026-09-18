# 10 · Reliability

> La pregunta no es "¿cómo evito que falle?" sino **"¿cómo se comporta cuando falle?"**. Todo sistema
> suficientemente grande está permanentemente en un estado de fallo parcial. La fiabilidad es diseñar para
> que eso no sea visible.


**Cubre del temario:** `concepts` · `patterns` · `failure_modes` · `recovery` · `implementations` · `tradeoffs`

---

## Timeouts

**El fallo más común en backend es no tener timeout.** Una llamada sin timeout no falla: **se queda colgada**,
ocupa un worker o una conexión del pool, y propaga el bloqueo hacia arriba hasta agotar todo.

**Los que hay que configurar (todos, explícitamente):**
- **Connect timeout** (establecer TCP): corto, 1-3s.
- **Read/request timeout** (esperar la respuesta): según el p99 real del servicio + margen.
- **Total / deadline**: el tope global, incluyendo reintentos.
- **Timeout de query** en la base de datos (`statement_timeout` en Postgres) y de **adquisición del pool**.
- **Idle timeout** en conexiones ociosas.

**Las dos reglas que se preguntan:**
1. **El timeout del cliente debe ser mayor que el del servidor**, o el cliente se rinde mientras el servidor
   sigue trabajando (trabajo fantasma que consume recursos sin beneficiar a nadie).
2. **Propaga deadlines.** Si al usuario le quedan 200ms, no lances una llamada interna con timeout de 5s.
   gRPC lo hace nativo; en HTTP se pasa como header y se respeta. **Sin deadline propagada, tu sistema sigue
   procesando peticiones que nadie va a leer.**

**Cómo elegir el valor:** mira el p99 real de la dependencia y añade margen. Un timeout demasiado alto no
protege; uno demasiado bajo convierte lentitud puntual en errores.

> **Ficha** · **Cuándo:** toda llamada saliente, sin excepción ·
> **Patrón:** timeout de conexión, de lectura, total, de query y de adquisición de pool ·
> **Anti-patrón:** confiar en el default del cliente HTTP, que suele ser infinito ·
> **Límites:** un timeout no cancela el trabajo del otro lado: solo deja de esperarlo ·
> **Cómo falla:** sin timeout la llamada **no falla, se cuelga**, y agota tus workers ·
> **Decisión:** el del cliente mayor que el del servidor, y este mayor que el de sus dependencias ·
> **Trade-off:** timeout corto (protege, corta peticiones lentas legítimas) vs largo ·
> **Relacionado:** deadlines, retries, pools `[08, 09]`

---

## Retries

Cubierto en profundidad en `08-distributed-systems.md`. El resumen que hay que saber decir:

- Solo lo **transitorio** e **idempotente**.
- **Backoff exponencial + jitter**, siempre.
- **Presupuesto de reintentos** (p. ej. máximo 10% del tráfico) y **reintentar en una sola capa**.
- Respetar `Retry-After`.
- **Combinado con circuit breaker**, o los reintentos rematan a un servicio que se estaba recuperando.

> **Ficha** · **Cuándo:** solo para errores transitorios de operaciones idempotentes ·
> **Patrón:** backoff exponencial con jitter, presupuesto global, respetar `Retry-After` ·
> **Anti-patrón:** reintentar en varias capas a la vez ·
> **Límites:** reintentar un error permanente solo multiplica la carga ·
> **Cómo falla:** retry storm que impide recuperarse al servicio caído ·
> **Decisión:** combínalo **siempre** con circuit breaker ·
> **Trade-off:** tasa de éxito vs carga añadida ·
> **Relacionado:** idempotencia, breakers `[08]`

---

## Circuit breakers

Un interruptor que **deja de llamar a un servicio que está caído**, para no desperdiciar recursos ni empeorar
su situación.

```
CERRADO ──(demasiados fallos)──► ABIERTO ──(pasa el tiempo)──► SEMIABIERTO
   ▲                                                               │
   └──────────(las pruebas tienen éxito)───────────────────────────┘
                              (fallan) → vuelve a ABIERTO
```

- **Cerrado:** todo pasa, se cuentan los fallos.
- **Abierto:** se rechaza **inmediatamente** sin intentar (fail fast). Aquí es donde devuelves la respuesta
  degradada.
- **Semiabierto:** deja pasar unas pocas peticiones de prueba para ver si el otro se recuperó.

**Por qué importa de verdad:** sin breaker, un servicio lento consume todos tus workers esperando, y **tu**
servicio cae por culpa del suyo. Con breaker, fallas rápido y sigues sirviendo el resto de funcionalidad.
Es la defensa principal contra el **fallo en cascada**.

**Configuración:** umbral por *ratio* de fallos (no por número absoluto), ventana deslizante, mínimo de
peticiones antes de decidir (si no, 2 fallos de 2 abren el circuito sin motivo), y tiempo de apertura.
**Un breaker por dependencia**, nunca uno global.

> **Ficha** · **Cuándo:** toda dependencia externa ·
> **Patrón:** uno por dependencia, por ratio de fallos y con mínimo de peticiones ·
> **Anti-patrón:** breaker global, o abrir tras 2 fallos de 2 ·
> **Límites:** protege de un servicio degradado, no de uno que devuelve datos erróneos ·
> **Cómo falla:** **lento es peor que caído** — sin breaker, consume todos tus workers ·
> **Decisión:** en abierto, devuelve fallback si existe; si no, falla rápido ·
> **Trade-off:** cortar pronto vs cortar a un servicio que se estaba recuperando ·
> **Relacionado:** timeouts, bulkheads, degradación `[08]`

---

## Bulkheads (mamparos)

Del casco de un barco: compartimentos estancos para que una vía de agua no hunda el barco entero.

- **Pools separados por dependencia.** Si el servicio de recomendaciones se vuelve lento, que agote *su*
  pool de 10 conexiones, no los 100 workers que también sirven el checkout.
- **Colas y workers separados por prioridad.** El batch nocturno no comparte cola con los pagos.
- **Aislamiento por tenant** para que un cliente ruidoso no degrade a los demás (el problema del *noisy
  neighbor*).
- **Límite de concurrencia por endpoint**: el endpoint caro de exportar informes no puede consumir toda la
  capacidad.

**La idea clave:** los bulkheads **limitan el radio de impacto**. Sin ellos, cualquier fallo tiende a
convertirse en un fallo total.

> **Ficha** · **Cuándo:** cuando varias funcionalidades comparten recursos ·
> **Patrón:** pools, colas y límites de concurrencia **separados** por dependencia y por criticidad ·
> **Anti-patrón:** un único pool compartido entre el checkout y los informes ·
> **Límites:** aislar reduce el aprovechamiento: reservas capacidad que a veces no se usa ·
> **Cómo falla:** el informe mensual agota el pool y tira la API ·
> **Decisión:** aísla por **radio de impacto**, no por comodidad de configuración ·
> **Trade-off:** utilización vs aislamiento ·
> **Relacionado:** connection pools, multi-tenancy `[09, 17]`

---

## Graceful degradation

**Diseña qué se puede perder.** No todas las funcionalidades valen lo mismo:

| Nivel | Ejemplo | Si falla |
|---|---|---|
| Crítico | login, checkout, pago | el producto está caído |
| Importante | búsqueda, historial | degradar (cache, resultados parciales) |
| Opcional | recomendaciones, avatares, analítica | **omitir en silencio** |

**Patrones:**
- **Fallback:** si la personalización falla, sirve el contenido genérico.
- **Cache viejo mejor que error** (`stale-if-error`): servir datos de hace 10 minutos es infinitamente mejor
  que un 500.
- **Funcionalidad reducida:** el e-commerce que no puede calcular envío exacto muestra una estimación y
  deja comprar.
- **Cola en vez de rechazo:** si no puedes procesar ahora, acepta (202) y procesa después — **solo si el
  usuario puede esperar**.
- **Feature flags como interruptores de emergencia:** apagar la función que está causando el problema es
  a menudo la mitigación más rápida que existe.

> **Ficha** · **Cuándo:** al clasificar funcionalidades por criticidad ·
> **Patrón:** crítico / importante / opcional, con fallback definido para cada nivel ·
> **Anti-patrón:** que una caída de recomendaciones impida completar una compra ·
> **Límites:** degradar exige que producto acepte de antemano qué se puede perder ·
> **Cómo falla:** nadie decidió qué es prescindible, así que todo es crítico y todo cae junto ·
> **Decisión:** cache viejo > error; respuesta parcial > página en blanco ·
> **Trade-off:** experiencia completa vs disponibilidad ·
> **Relacionado:** breakers, stale-if-error, feature flags `[09, 14]`

---

## Failover y redundancia

- **Activo-pasivo:** un standby que toma el relevo. Más simple; el failover tarda y el standby está
  desaprovechado (y a menudo no se ha probado nunca — **el failover que no se ensaya no funciona**).
- **Activo-activo:** todos sirven tráfico. Mejor uso de recursos y failover instantáneo; exige gestionar
  consistencia y conflictos.
- **Multi-AZ** es el mínimo razonable. **Multi-región** multiplica el coste y la complejidad (replicación,
  latencia, split-brain) — se justifica por requisitos de negocio o normativos, no por instinto.
- **Split-brain:** dos nodos creen ser el primario a la vez y ambos aceptan escrituras. Se previene con
  quórum y *fencing* (`08-distributed-systems.md`).
- **Elimina los puntos únicos de fallo**, pero recuerda que redundar también añade modos de fallo nuevos
  (el propio mecanismo de failover puede ser la causa del incidente).

> **Ficha** · **Cuándo:** al definir la disponibilidad objetivo ·
> **Patrón:** multi-AZ como mínimo, y **ensayar el failover** periódicamente ·
> **Anti-patrón:** un standby que nunca se ha probado ·
> **Límites:** redundar añade modos de fallo nuevos: el propio mecanismo puede ser la causa ·
> **Cómo falla:** **split-brain** — dos nodos se creen primarios y ambos aceptan escrituras ·
> **Decisión:** multi-región solo si el negocio o la normativa lo exigen ·
> **Trade-off:** disponibilidad vs coste y complejidad ·
> **Relacionado:** consenso, quórum, replicación `[04, 08]`

---

## Backups y disaster recovery

**Los dos números que definen todo:**
- **RPO** (Recovery Point Objective): cuántos datos puedes permitirte perder. RPO de 1h = backups cada hora.
- **RTO** (Recovery Time Objective): cuánto puedes estar caído. RTO de 15 min exige una infraestructura
  distinta (y más cara) que uno de 24h.

**Reglas:**
- **La regla 3-2-1:** 3 copias, en 2 medios distintos, 1 fuera del sitio.
- **Un backup no probado no es un backup.** Programa restauraciones reales periódicas y **mide cuánto tardan**
  — ahí es donde te enteras de que tu RTO era una fantasía.
- **Point-in-time recovery** (con WAL archiving en Postgres) te permite volver al instante anterior al
  `DELETE` sin `WHERE`. Es lo que salva de los errores humanos, que son la causa más frecuente.
- **Una réplica no es un backup.** Un `DROP TABLE` se replica en milisegundos. Tampoco lo es el versionado
  de S3 si el atacante tiene permisos para borrarlo.
- **Protege los backups:** cifrados, con acceso separado y a ser posible inmutables (object lock). El
  ransomware moderno ataca los backups primero.
- **Documenta el runbook de restauración** y que no dependa de una sola persona.

> **Ficha** · **Cuándo:** antes de tener datos que importen ·
> **Patrón:** 3-2-1, PITR, restauraciones de prueba programadas y cronometradas ·
> **Anti-patrón:** tratar una read replica como backup ·
> **Límites:** tu RTO real es el que mediste restaurando, no el que pusiste en la diapositiva ·
> **Cómo falla:** el ransomware ataca primero los backups: hazlos inmutables ·
> **Decisión:** RPO y RTO se derivan del negocio y determinan el coste ·
> **Trade-off:** frecuencia y retención vs coste de almacenamiento ·
> **Relacionado:** data recovery, corrupción `[04]`

---

## SLI, SLO, SLA y error budget

- **SLI** (Indicator): la medida. *"Porcentaje de peticiones a `/checkout` con éxito y por debajo de 500ms."*
- **SLO** (Objective): el objetivo interno. *"99,9% durante 30 días."*
- **SLA** (Agreement): el contrato con el cliente, con penalizaciones. **Siempre más laxo que tu SLO**, para
  tener margen antes de incumplir legalmente.

**Error budget:** con un SLO del 99,9% mensual, tienes **43,2 minutos** de fallo al mes. Ese presupuesto es
un recurso que se gasta:
- Si te sobra → puedes desplegar más rápido y asumir más riesgo.
- Si se agota → se congelan las features y todo el esfuerzo va a fiabilidad.

**Esto es lo importante culturalmente:** convierte la discusión "¿features o estabilidad?" en un dato
objetivo en vez de una pelea de opiniones entre producto e ingeniería.

**Los nueves, para tenerlos en la cabeza:**

| Disponibilidad | Caída al mes | Al año |
|---|---|---|
| 99% | 7,2 horas | 3,65 días |
| 99,9% | 43,2 minutos | 8,76 horas |
| 99,99% | 4,3 minutos | 52,6 minutos |
| 99,999% | 26 segundos | 5,26 minutos |

**El matiz senior:** cada nueve extra multiplica el coste aproximadamente por diez, y tu disponibilidad está
limitada por la de tus dependencias. Si tu cloud te da 99,95%, prometer 99,99% es prometer algo que no
controlas. **Elige el SLO según lo que el usuario nota y el negocio necesita, no por vanidad.**

> **Ficha** · **Cuándo:** al definir qué significa "funcionando" ·
> **Patrón:** 2-4 recorridos críticos con SLI medibles, SLO interno y SLA más laxo ·
> **Anti-patrón:** un SLO del 100% — implica no poder desplegar nunca ·
> **Límites:** tu disponibilidad está acotada por la de tus dependencias ·
> **Cómo falla:** alertar por umbrales técnicos genera ruido; hay que alertar por burn rate ·
> **Decisión:** ¿queda error budget? Despliega. ¿Se agotó? Todo a fiabilidad ·
> **Trade-off:** cada nueve cuesta ~10× más que el anterior ·
> **Relacionado:** alertas, métricas `[12]`

---

## Incident response

**Roles** (aunque seáis pocos): *Incident Commander* (coordina y decide, **no** depura), *Operations*
(ejecuta), *Communications* (informa a clientes y a negocio). Lo importante es que **una sola persona
coordine** y que quien depura no sea quien responde a los stakeholders.

**El flujo:**
1. **Detectar** (alerta o reporte).
2. **Triar**: ¿impacto real? ¿cuántos usuarios? ¿está empeorando?
3. **Mitigar primero, diagnosticar después.** Rollback, feature flag, escalar, redirigir tráfico.
   **El objetivo es parar el dolor, no entender la causa.** Este es el error más común de los ingenieros
   buenos: se enganchan al puzzle mientras los usuarios sufren.
4. **Comunicar** pronto y a menudo, aunque sea "seguimos investigando". El silencio es lo que enfada.
5. **Resolver** y confirmar con datos que se acabó.
6. **Postmortem.**

**Postmortem sin culpables (blameless):** el objetivo es el sistema, no la persona. Nadie "causó" el
incidente por escribir un comando: **el sistema permitió que un comando causara un incidente.** Si se busca
culpables, la gente esconde información y pierdes la capacidad de aprender.

Un postmortem útil tiene: cronología con datos, impacto cuantificado (usuarios, dinero, duración), causas
contribuyentes (en plural — casi nunca hay una sola), **qué funcionó bien**, y **acciones con dueño y fecha**.
Un postmortem sin acciones asignadas es un documento que nadie leerá.

> **Ficha** · **Cuándo:** en cuanto haya usuarios reales ·
> **Patrón:** un coordinador que no depura, comunicación temprana, postmortem sin culpables ·
> **Anti-patrón:** buscar culpables — la gente esconde información y dejas de aprender ·
> **Límites:** el proceso no sustituye a tener runbooks y accesos preparados ·
> **Cómo falla:** un postmortem sin acciones con dueño y fecha no cambia nada ·
> **Decisión:** mitigar siempre antes que entender ·
> **Trade-off:** rigor del proceso vs agilidad en equipos pequeños ·
> **Relacionado:** debugging de incidentes, alertas `[12]`

---

## Chaos engineering

Inyectar fallos **a propósito y de forma controlada** para descubrir debilidades antes de que las descubra
la realidad.

- **El método:** formula una hipótesis ("si muere una réplica, la latencia p99 no sube más de 50ms"),
  inyecta el fallo en un **radio de impacto pequeño**, mide, y ten un botón de parada.
- **Experimentos típicos:** matar instancias, añadir latencia de red, provocar pérdida de paquetes, llenar
  discos, caer una AZ entera, degradar una dependencia externa.
- **Requisito previo:** buena observabilidad y capacidad de parar el experimento. Hacer chaos sin poder medir
  qué pasa es solo romper cosas.
- **Empieza en staging**, y en producción solo cuando el equipo tenga confianza y controles.
- **Los "game days"** (simulacros de incidente) dan casi todo el valor con mucho menos riesgo: practicas el
  proceso, descubres que el runbook está desactualizado y que nadie sabe dónde están los backups.

> **Ficha** · **Cuándo:** cuando ya tienes observabilidad y confianza ·
> **Patrón:** hipótesis explícita, radio de impacto pequeño, botón de parada ·
> **Anti-patrón:** romper cosas en producción sin poder medir qué pasa ·
> **Límites:** requiere madurez previa; sin métricas es solo vandalismo ·
> **Cómo falla:** el experimento provoca un incidente real por falta de contención ·
> **Decisión:** empieza con **game days** (simulacros): casi todo el valor, mucho menos riesgo ·
> **Trade-off:** riesgo controlado hoy vs sorpresa no controlada mañana ·
> **Relacionado:** failover, runbooks, observabilidad `[12]`

---

## Implementación: health checks y apagado elegante

Las dos piezas que todo servicio necesita y que casi nadie hace bien.

```python
@app.get("/health/live")          # LIVENESS: ¿el proceso responde? NADA externo aqui.
async def live():
    return {"status": "ok"}

@app.get("/health/ready")         # READINESS: ¿puedo atender trafico?
async def ready():
    dependencias = {}
    try:
        await asyncio.wait_for(db.execute("SELECT 1"), timeout=1.0)
        dependencias["db"] = "ok"
    except Exception:
        dependencias["db"] = "fail"
        return JSONResponse({"status": "not_ready", "deps": dependencias}, 503)

    try:                          # dependencia BLANDA: si falla, seguimos listos
        await asyncio.wait_for(cache.ping(), timeout=0.5)
        dependencias["cache"] = "ok"
    except Exception:
        dependencias["cache"] = "degraded"

    if apagandose.is_set():       # durante el shutdown decimos "no" ANTES de cerrar
        return JSONResponse({"status": "draining"}, 503)
    return {"status": "ready", "deps": dependencias}
```

**El error que causa incidentes:** meter la base de datos en la *liveness*. Si la DB parpadea, Kubernetes
**reinicia todos tus pods a la vez** y convierte una degradación en una caída total.

**Apagado elegante** — el motivo de que cada despliegue genere 502 si no lo haces:

```python
apagandose = asyncio.Event()

async def shutdown(sig):
    apagandose.set()              # 1) readiness pasa a 503
    await asyncio.sleep(5)        # 2) margen para que el LB deje de mandarnos trafico
    await servidor.shutdown()     # 3) terminar las peticiones en vuelo
    await db.close(); await broker.close()   # 4) cerrar recursos

loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown(signal.SIGTERM)))
```

El orden importa: el balanceador tarda unos segundos en enterarse de que ya no estás listo. Si cierras
antes de ese margen, recibes tráfico que ya no puedes servir.

> **Ficha** · **Cuándo:** todo servicio, antes del primer despliegue ·
> **Patrón:** liveness sin dependencias · readiness con dependencias duras y blandas separadas · drenaje antes de cerrar ·
> **Anti-patrón:** un solo `/health` usado para las dos cosas ·
> **Límites:** Kubernetes manda SIGTERM y quita del Service **a la vez**, sin orden garantizado ·
> **Cómo falla:** sin margen de drenaje, cada despliegue produce 502 visibles para el usuario ·
> **Decisión:** ¿la dependencia rota impide servir? Dura. ¿Solo degrada? Blanda ·
> **Trade-off:** readiness estricta (menos errores servidos) vs disponibilidad aparente ·
> **Relacionado:** probes, despliegues, load balancing `[09, 13, 14]`

---

## Implementación: circuit breaker y timeouts en cascada

```python
class CircuitBreaker:
    def __init__(self, umbral=0.5, minimo=20, ventana=60, apertura=30):
        self.umbral, self.minimo = umbral, minimo          # ratio de fallos, no numero absoluto
        self.ventana, self.apertura = ventana, apertura
        self.estado, self.abierto_desde = "cerrado", None
        self.eventos = deque()                              # (timestamp, ok?)

    async def llamar(self, fn, *, fallback=None):
        if self.estado == "abierto":
            if time.monotonic() - self.abierto_desde < self.apertura:
                if fallback is not None:
                    return fallback()                       # degradar, no esperar
                raise CircuitoAbierto()                     # fail fast
            self.estado = "semiabierto"                     # toca probar

        try:
            r = await fn()
        except Exception:
            self._registrar(False)
            if self.estado == "semiabierto":
                self._abrir()
            raise
        self._registrar(True)
        if self.estado == "semiabierto":
            self.estado, self.eventos = "cerrado", deque()
        return r

    def _registrar(self, ok):
        ahora = time.monotonic()
        self.eventos.append((ahora, ok))
        while self.eventos and ahora - self.eventos[0][0] > self.ventana:
            self.eventos.popleft()
        if len(self.eventos) >= self.minimo:
            fallos = sum(1 for _, o in self.eventos if not o) / len(self.eventos)
            if fallos >= self.umbral:
                self._abrir()

    def _abrir(self):
        self.estado, self.abierto_desde = "abierto", time.monotonic()
```

**El `minimo` es lo que casi todo el mundo olvida:** sin él, 2 fallos de 2 peticiones abren el circuito
sin ninguna evidencia estadística.

**Deadline propagada** — que el trabajo no siga cuando ya nadie lo espera:

```python
async def manejar(request):
    presupuesto = float(request.headers.get("X-Deadline-Ms", 3000)) / 1000
    inicio = time.monotonic()

    def restante():
        return max(0.0, presupuesto - (time.monotonic() - inicio))

    perfil = await asyncio.wait_for(servicio_a.get(), timeout=min(1.0, restante()))
    if restante() < 0.2:                       # ya no da tiempo: degrada en vez de fallar
        return respuesta_parcial(perfil)
    extras = await asyncio.wait_for(servicio_b.get(), timeout=restante())
    return respuesta_completa(perfil, extras)
```

> **Ficha** · **Cuándo:** toda llamada a una dependencia externa o a otro servicio ·
> **Patrón:** un breaker **por dependencia**, con ratio, ventana y mínimo de peticiones ·
> **Anti-patrón:** un breaker global, o abrir por número absoluto de fallos ·
> **Límites:** el breaker no distingue "el servicio está mal" de "esta petición concreta es mala" ·
> **Cómo falla:** sin breaker, un servicio **lento** (no caído) consume todos tus workers ·
> **Decisión:** si hay fallback razonable, degrada; si no, falla rápido ·
> **Trade-off:** abrir pronto (proteges) vs abrir tarde (no cortas a un servicio que iba bien) ·
> **Relacionado:** retries, bulkheads, degradación `[08, 09]`

---

## Debugging de incidentes

**El orden correcto, y la disciplina de no saltárselo:**

1. **¿Hay impacto real?** ¿Cuántos usuarios, qué funcionalidad, está empeorando?
2. **Mitigar.** Rollback, feature flag, escalar, redirigir. **Antes de entender.**
3. **¿Qué cambió?** Despliegue, migración, configuración, feature flag, pico de tráfico, un proveedor,
   un certificado caducado, un disco lleno. **El 90% de los incidentes tienen un cambio reciente detrás.**
4. **Acotar por capas:** ¿afecta a todos o a un subconjunto (una región, un tenant, una versión)?
   ¿todos los endpoints o uno? ¿empieza en tu servicio o en una dependencia?
5. **Métricas → trazas → logs → profiler.** De lo agregado a lo concreto.
6. **Verificar la hipótesis** antes de aplicar el arreglo. Bajo presión se cambian tres cosas a la vez y
   luego nadie sabe cuál funcionó.

**Los sospechosos habituales, por frecuencia real:** disco lleno · certificado caducado · secreto rotado
que alguien no actualizó · connection pool agotado · OOM y reinicios · cambio de configuración sin revisar ·
un cron que colisiona · un proveedor externo degradado · una query que perdió su índice al crecer la
tabla · thundering herd tras caer la cache.

**Lo que NO hay que hacer:** reiniciar sin mirar nada (destruyes la evidencia), tocar producción a mano
sin registrarlo, o investigar en solitario sin comunicar.

> **Ficha** · **Cuándo:** desde el minuto uno de cualquier incidente ·
> **Patrón:** mitigar → comunicar → acotar → diagnosticar → postmortem ·
> **Anti-patrón:** engancharse al puzzle técnico mientras los usuarios siguen afectados ·
> **Límites:** mitigar rápido a veces destruye la evidencia necesaria para entender ·
> **Cómo falla:** sin coordinador, tres personas tocan producción a la vez ·
> **Decisión:** declara el incidente pronto; declarar de más es barato, de menos es carísimo ·
> **Trade-off:** velocidad de mitigación vs conservar evidencia ·
> **Relacionado:** observabilidad, rollback, postmortem `[12, 14]`

---

## Data recovery

- **Restaurar con backup + PITR** al instante anterior al error.
- **El caso más común es humano:** un `UPDATE` o `DELETE` sin `WHERE`. Medidas preventivas baratas:
  ejecutar siempre dentro de una transacción explícita, comprobar antes con un `SELECT` de la misma
  condición, y **prohibir la escritura directa en producción** salvo procedimiento revisado.
- **Restauración parcial:** restaura el backup en una instancia aparte y copia solo las filas afectadas,
  en vez de revertir toda la base de datos (que descartaría todo lo ocurrido después).
- **Mide el tiempo real de restauración** con un ensayo. Es la única forma de saber si tu RTO es real.
- **Después, reconcilia:** los sistemas externos (pagos, emails enviados, mensajes publicados) **no
  vuelven atrás con tu base de datos**. Restaurar puede dejarte inconsistente con el mundo exterior.

> **Ficha** · **Cuándo:** tras pérdida o corrupción de datos ·
> **Patrón:** restaurar en paralelo y copiar lo afectado, no revertir en bloque ·
> **Anti-patrón:** restaurar encima de producción sin evaluar qué se pierde en el camino ·
> **Límites:** PITR solo llega hasta donde llega tu retención de WAL ·
> **Cómo falla:** el postmortem culpa a la persona en vez de preguntar por qué el sistema lo permitió ·
> **Decisión:** ¿el daño es acotado? Restauración parcial. ¿Es total? Restauración completa ·
> **Trade-off:** volver atrás (pierdes lo posterior) vs reparar en caliente (más lento, más riesgo) ·
> **Relacionado:** backups, corrupción, postmortem `[04]`

---

## Preguntas de entrevista y trade-offs

**Q: Un servicio del que dependes se vuelve lento (no falla, tarda 30s). ¿Qué pasa en tu sistema?**
Sin timeout ni breaker, se agotan tus workers esperando y **caes tú también**. Con timeout agresivo, breaker
y fallback, fallas rápido y degradas esa funcionalidad. *Señal:* señalas que **lento es peor que caído**,
porque un servicio caído falla rápido y uno lento consume tus recursos.

**Q: ¿Qué es un error budget y para qué sirve?**
El margen de fallo que permite tu SLO. Sirve para decidir objetivamente cuándo priorizar fiabilidad sobre
features. *Señal:* explicas que convierte una discusión política en un dato, y que un SLO del 100% es una
señal de inmadurez: implica no poder desplegar nunca.

**Q: ¿Una read replica es un backup?**
No. Replica también los errores: un `DROP TABLE` llega a la réplica al instante. *Señal:* mencionas PITR
para volver a un punto anterior y que lo que de verdad importa es haber **probado** la restauración y
cronometrado el RTO.

**Q: ¿Cómo evitas un fallo en cascada?**
Timeouts en todas partes, circuit breakers por dependencia, bulkheads para aislar pools, load shedding y
degradación con gracia. *Señal:* mencionas la espiral de reintentos y que hay que reintentar en una sola capa
con presupuesto limitado.

**Q: ¿Qué haces primero en un incidente?**
Mitigar. Rollback o feature flag, y luego investigar con calma. *Señal:* dices explícitamente que entender la
causa raíz **no es el objetivo durante el incidente**, y que primero se declara el incidente y se asigna un
coordinador.

**Trade-off central de esta caja:** *fiabilidad vs coste y velocidad*. Cada nueve cuesta aproximadamente diez
veces más que el anterior y ralentiza la entrega. La decisión senior es elegir el nivel **que el negocio
necesita**, medirlo con SLOs, y gastar el error budget deliberadamente en vez de perseguir una perfección
que nadie está pagando.

---

## Fuentes

- [Google SRE Book](https://sre.google/sre-book/table-of-contents/) y [SRE Workbook](https://sre.google/workbook/table-of-contents/) — SLOs, error budgets, postmortems sin culpables.
- [AWS Builders' Library](https://aws.amazon.com/builders-library/) — timeouts, reintentos, circuit breakers y aislamiento en la práctica.
- Michael Nygard, *Release It!* — el origen de circuit breaker y bulkhead como patrones nombrados.
- [Principles of Chaos Engineering](https://principlesofchaos.org/)
