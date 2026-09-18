# 09 · Performance

> La primera regla: **mide antes de tocar nada.** La intuición sobre dónde está el cuello de botella es
> sistemáticamente incorrecta. La segunda: optimizar lo que no es el cuello de botella **no mejora nada**
> (ley de Amdahl).


**Cubre del temario:** `concepts` · `caching` · `optimization` · `scaling` · `profiling` · `implementations` · `bottlenecks` · `tradeoffs`

---

## Cómo se mide de verdad

**Percentiles, no medias.** Una media de 100ms puede esconder que el 1% de tus usuarios espera 8 segundos.
Y ese 1% son, casi siempre, los clientes con más datos: los más valiosos.

- **p50** (mediana): la experiencia típica.
- **p95 / p99**: la experiencia mala. **Es la que define tu reputación.**
- **p99.9**: donde viven el GC, los reintentos y los timeouts.
- **Latencia de cola (tail latency):** si una página hace 10 llamadas internas en paralelo y cada una tiene
  p99 de 1s, **la probabilidad de que la página entera supere 1s es ~10%**, no 1%. Por eso el p99 de tus
  dependencias se convierte en el p50 de tu producto.

**Las métricas que importan:** latencia (por percentil), **throughput** (RPS), **saturación** (uso de CPU,
memoria, pool, cola) y **error rate**. Ver los *four golden signals* en `12-observability.md`.

**La ley de Little:** `concurrencia = throughput × latencia`. Si atiendes 100 RPS con 200ms de latencia,
tienes ~20 requests en vuelo. Es cómo dimensionas pools y workers sin adivinar.

**La ley de Amdahl:** si algo ocupa el 20% del tiempo y lo haces infinitamente rápido, ganas como mucho un
20%. **Ataca siempre lo que domina el perfil.**

> **Ficha** · **Cuándo:** antes de tocar una sola línea para optimizar ·
> **Patrón:** percentiles (p50/p95/p99) e histogramas, nunca medias ·
> **Anti-patrón:** promediar los p99 de varias instancias — matemáticamente no significa nada ·
> **Límites:** la ley de Amdahl acota lo que puedes ganar optimizando una parte ·
> **Cómo falla:** una media de 100 ms esconde que el 1% espera 8 segundos ·
> **Decisión:** usa la ley de Little (`concurrencia = throughput × latencia`) para dimensionar pools ·
> **Trade-off:** medir cuesta (cardinalidad, almacenamiento) y no medir cuesta más ·
> **Relacionado:** métricas, SLOs `[10, 12]`

---

## Profiling y análisis de cuellos de botella

**El orden correcto de investigación:**
1. **¿Dónde se va el tiempo?** Distributed tracing para ver el desglose por servicio (`12-observability.md`).
2. **¿Es CPU, I/O, memoria o contención?** Cada una tiene una firma distinta:
   - CPU al 100% → profiler de CPU, flame graph.
   - CPU baja pero lento → **estás esperando**: DB, red, lock, pool agotado.
   - Memoria creciendo → leak o cache sin límite.
   - Picos periódicos → GC, cron, expiración de cache sincronizada.
3. **Profiler:** flame graphs (`py-spy`, `async-profiler`, `pprof`), *continuous profiling* en producción
   (Pyroscope, Parca — y OpenTelemetry profiling, que en 2026 está en alpha).
4. **Base de datos:** `pg_stat_statements` ordenado por tiempo total — la culpable suele ser una query
   "rápida" ejecutada un millón de veces, no la lenta.

**Los cuellos de botella reales en una app típica, por frecuencia:**
1. **N+1 queries** (`04-databases.md`) — el campeón absoluto.
2. Falta de índice o índice inservible.
3. Llamadas externas síncronas sin timeout ni caché.
4. Serialización de payloads enormes (traer 10.000 filas para pintar 20).
5. Connection pool agotado (se ve como latencia, es una cola).
6. Trabajo que debería ser asíncrono hecho dentro del request (enviar email, generar PDF, redimensionar).

> **Ficha** · **Cuándo:** cuando las métricas señalan pero no explican ·
> **Patrón:** métricas → trazas → logs → profiler, en ese orden ·
> **Anti-patrón:** optimizar por intuición sin perfilar ·
> **Límites:** el profiling en producción añade overhead; el continuo lo minimiza ·
> **Cómo falla:** la culpable suele ser una query rápida ejecutada un millón de veces, no la lenta ·
> **Decisión:** ordena `pg_stat_statements` por **tiempo total**, no por media ·
> **Trade-off:** overhead de instrumentación vs ceguera ·
> **Relacionado:** N+1, tracing `[04, 12]`

---

## Caching

**La jerarquía completa**, de más cerca a más lejos:

```
Navegador → CDN → Reverse proxy → Cache de aplicación (in-process) → Redis → DB (buffer pool)
```

**Patrones:**

| Patrón | Cómo | Cuándo |
|---|---|---|
| **Cache-aside** (lazy) | la app mira la cache; si falla, va a la DB y la rellena | **el default**; simple y robusto |
| Read-through | la cache va a la DB por ti | menos código, menos control |
| Write-through | escribes en cache y DB a la vez | lecturas siempre frescas, escrituras más lentas |
| Write-behind | escribes en cache, se vuelca luego | rapidísimo; **puedes perder datos** |
| Refresh-ahead | refresca antes de expirar | evita el miss en claves calientes |

**Invalidación — "uno de los dos problemas difíciles de la informática":**
- **TTL** es la estrategia más robusta porque falla de forma predecible. Empieza siempre por aquí.
- **Invalidación explícita al escribir** es más fresca pero se olvida en el endpoint nuevo.
- **Versionado de claves** (`producto:42:v7`) evita borrar: cambias la versión y la vieja caduca sola.
- **Cachea el resultado, no el proceso**, y **nunca caches datos con permisos distintos bajo la misma clave**
  (fuga entre usuarios). Si depende del usuario, la clave lo incluye.

**Las tres patologías clásicas:**
- **Thundering herd / stampede:** expira una clave caliente y 5.000 requests van a la DB a la vez.
  Solución: *single-flight* (solo uno regenera, el resto espera), TTL con jitter, o `stale-while-revalidate`.
- **Cache penetration:** consultas de claves que no existen pasan siempre a la DB. Solución: cachear el
  "no existe" con TTL corto, o un bloom filter.
- **Hot key:** una clave concentra el tráfico y satura un nodo de Redis. Solución: replicar la clave con
  sufijos, o cachearla también en memoria local del proceso.

**Métrica clave:** **hit ratio**. Una cache con 20% de aciertos añade latencia y complejidad sin dar nada;
por debajo de ~80-90% en lecturas calientes, replantéate la clave o el TTL.

> **Ficha** · **Cuándo:** ratio lectura/escritura alto y datos que toleran algo de desfase ·
> **Patrón:** cache-aside + TTL con jitter + single-flight ·
> **Anti-patrón:** cachear datos con permisos distintos bajo la misma clave — es una fuga ·
> **Límites:** invalidar es el problema difícil; el TTL falla de forma predecible y por eso se prefiere ·
> **Cómo falla:** **thundering herd** al expirar una clave caliente ·
> **Decisión:** si el hit ratio no supera ~80-90%, la cache añade latencia sin dar nada ·
> **Trade-off:** frescura vs latencia y carga de origen ·
> **Relacionado:** CDN, Redis, invalidación `[02, 04]`

---

## CDN y cache HTTP

- Sirve estáticos y **también respuestas de API cacheables** desde el borde (`s-maxage`).
- **Cache key:** URL + los headers de `Vary`. Si varías por `Authorization` sin declararlo, sirves datos
  de un usuario a otro (**incidente de seguridad**, ver `02-web-protocols.md`).
- **Purga** por tag/surrogate key en vez de por URL: invalidas "todo lo del producto 42" de una vez.
- **Origin shield** y `stale-while-revalidate` / `stale-if-error`: el CDN sigue sirviendo contenido
  ligeramente viejo mientras tu origen se recupera. **Es una de las mejores defensas contra un pico.**

> **Ficha** · **Cuándo:** estáticos, y también respuestas de API cacheables ·
> **Patrón:** purga por tag y `stale-while-revalidate` / `stale-if-error` ·
> **Anti-patrón:** variar por `Authorization` sin declarar `Vary` ·
> **Límites:** no puedes recuperar lo ya servido; solo purgar lo que queda ·
> **Cómo falla:** el CDN sirve contenido de un usuario a otro ·
> **Decisión:** `stale-if-error` es una de las mejores defensas ante un pico en el origen ·
> **Trade-off:** latencia mínima en el borde vs datos ligeramente viejos ·
> **Relacionado:** cache HTTP, headers `[02]`

---

## Optimización de base de datos

Resumen operativo (el detalle está en `04-databases.md`):
índices correctos y con el orden correcto · matar el N+1 · `SELECT` solo de las columnas necesarias ·
keyset pagination · **batching** (una query con `IN (...)` en vez de 100) · materialized views para
agregaciones caras · particionado para tablas enormes · read replicas para descargar lecturas ·
`work_mem` y el resto de parámetros ajustados · **vigilar el bloat y el autovacuum**.

**Los dos consejos que más rendimiento dan por unidad de esfuerzo:**
1. **Batch.** Convertir N llamadas en una es casi siempre una mejora de orden de magnitud, porque el coste
   dominante es el round trip, no el trabajo.
2. **Mueve el trabajo fuera del request.** Si el usuario no necesita el resultado ahora, va a una cola.

> **Ficha** · **Cuándo:** casi siempre es aquí donde está el cuello de botella ·
> **Patrón:** batching (`IN (...)`) y mover trabajo fuera del request ·
> **Anti-patrón:** el N+1, y traer 10.000 filas para pintar 20 ·
> **Límites:** las materialized views quedan desfasadas hasta que se refrescan ·
> **Cómo falla:** una query pierde su índice al crecer la tabla y cambiar el plan ·
> **Decisión:** si el usuario no necesita el resultado ahora, va a una cola ·
> **Trade-off:** desnormalizar acelera lecturas y añade trabajo de consistencia ·
> **Relacionado:** índices, N+1, colas `[04, 08]`

---

## Connection pools

Un pool mal dimensionado se manifiesta como **latencia**, pero es una **cola**:
`tiempo total = espera por conexión + tiempo de query`.

- **Más grande no es mejor.** Pasado el punto óptimo (aproximadamente `cores × 2` para la DB), añadir
  conexiones *baja* el throughput por context switching y contención de locks.
- Dimensiona con la ley de Little: si necesitas 500 RPS y cada query tarda 20ms, necesitas ~10 conexiones
  ocupadas de media. Deja margen para picos, no 100×.
- **Timeouts obligatorios:** de adquisición (fallar rápido si el pool está lleno), de query, y de conexión
  ociosa. Sin timeout de adquisición, una query lenta produce un colapso en cascada.
- **Pools separados** para trabajo crítico y para batch/reporting. Si el informe mensual agota el pool, tu
  API se cae. Eso es un **bulkhead** (`10-reliability.md`).

> **Ficha** · **Cuándo:** toda conexión a base de datos o servicio externo ·
> **Patrón:** dimensionar con la ley de Little y **separar pools** por criticidad ·
> **Anti-patrón:** un pool gigante compartido entre la API y los informes ·
> **Límites:** pasado el óptimo (~cores × 2 en la DB), más conexiones **bajan** el throughput ·
> **Cómo falla:** se ve como latencia, pero es una cola esperando conexión ·
> **Decisión:** timeout de adquisición corto: fallar rápido es mejor que colapsar ·
> **Trade-off:** aislamiento (pools separados) vs aprovechamiento ·
> **Relacionado:** bulkheads, PgBouncer `[04, 10]`

---

## Load balancing

**Algoritmos:** round robin · **least connections** (mejor con requests de duración variable) ·
weighted (nodos heterogéneos) · **consistent hashing** (afinidad de cache o sesión) · EWMA / least response
time (el más inteligente, elige por latencia observada).

- **L4 (TCP) vs L7 (HTTP):** L4 es rápido y opaco; L7 entiende rutas, headers y puede hacer retries,
  routing por path y terminación TLS.
- **Health checks:** *liveness* (¿está vivo?) vs *readiness* (¿puede recibir tráfico?). Un check que solo
  hace ping al puerto declarará sano a un servicio cuya DB está caída.
- **Connection draining:** al retirar un nodo, deja de mandarle tráfico nuevo pero **termina lo que está en
  vuelo**. Sin esto, cada despliegue produce errores 502 visibles.
- **Sticky sessions:** necesarias para WebSocket, pero desequilibran la carga y complican el escalado.
  Mejor: estado fuera del proceso (Redis) y nodos intercambiables.

> **Ficha** · **Cuándo:** desde la segunda instancia ·
> **Patrón:** least-connections o EWMA + readiness probes + connection draining ·
> **Anti-patrón:** health check que solo hace ping al puerto ·
> **Límites:** las sticky sessions desequilibran la carga y complican el escalado ·
> **Cómo falla:** sin draining, **cada despliegue genera 502 visibles** ·
> **Decisión:** estado fuera del proceso para que los nodos sean intercambiables ·
> **Trade-off:** afinidad (cache local caliente) vs reparto uniforme ·
> **Relacionado:** health checks, despliegues `[12, 13, 14]`

---

## Escalado horizontal vs vertical

| | Vertical (máquina más grande) | Horizontal (más máquinas) |
|---|---|---|
| Complejidad | **ninguna** | estado compartido, coordinación, LB |
| Techo | físico y caro (la curva de precio es peor que lineal) | prácticamente ilimitado |
| Disponibilidad | **punto único de fallo** | tolerancia a fallos |
| Coste | salta a escalones grandes | granular |

**El consejo pragmático:** escala vertical primero — es una línea de Terraform y compra años. Escala
horizontal cuando necesites **disponibilidad** (no solo capacidad) o cuando el vertical se acabe.

**Requisito del horizontal: los servicios deben ser stateless.** Sesión en Redis, archivos en S3, nada en
disco local, nada en memoria del proceso que deba sobrevivir. Si un nodo cualquiera puede atender cualquier
request, escalar es trivial.

**Autoscaling:** escala por la métrica que refleja la saturación real (RPS, profundidad de cola, latencia),
no solo por CPU. Ojo con el *flapping*: pon cooldowns y escala hacia abajo mucho más despacio que hacia
arriba. Y recuerda que **arrancar una instancia tarda** — si el pico es más rápido que tu tiempo de arranque,
el autoscaling no te salva (necesitas capacidad de reserva o una cola que absorba).

> **Ficha** · **Cuándo:** al llegar al límite de capacidad ·
> **Patrón:** vertical primero (una línea, compra años), horizontal cuando necesites disponibilidad ·
> **Anti-patrón:** arquitectura distribuida para un tráfico que cabe en una máquina ·
> **Límites:** el horizontal exige servicios **stateless** ·
> **Cómo falla:** el escalado no sirve si el cuello está en la base de datos compartida ·
> **Decisión:** ¿necesitas capacidad o tolerancia a fallos? Solo lo segundo obliga a horizontal ·
> **Trade-off:** simplicidad vs disponibilidad ·
> **Relacionado:** stateless, autoscaling `[13]`

---

## Compresión

- **brotli** para texto (mejor ratio), **gzip** como universal, **zstd** cuando controlas ambos extremos
  (muy rápido y buen ratio).
- Nivel de compresión: comprimir al máximo gasta CPU en tu servidor. Para contenido dinámico, un nivel medio
  suele ser el óptimo; para estáticos, precomprime al máximo **en build**, no en cada request.
- **No comprimas** lo ya comprimido, ni respuestas diminutas (el overhead supera la ganancia).
- **Compresión en la base de datos y en la cola**: payloads más pequeños = más cosas en el buffer pool,
  menos I/O, menos ancho de banda. A veces es la optimización más barata.

> **Ficha** · **Cuándo:** respuestas de texto de tamaño apreciable ·
> **Patrón:** brotli para texto; precomprimir estáticos en build ·
> **Anti-patrón:** comprimir lo ya comprimido, o al máximo nivel en cada respuesta dinámica ·
> **Límites:** comprimir cuesta CPU en el camino crítico ·
> **Cómo falla:** comprimir secretos junto a input reflejado abre la puerta a BREACH ·
> **Decisión:** nivel medio en dinámico, máximo en estático ·
> **Trade-off:** ancho de banda vs CPU ·
> **Relacionado:** content negotiation `[02]`

---

## Backpressure

**Qué es:** cuando el productor va más rápido que el consumidor, alguien tiene que frenar. Si nadie frena,
se acumula memoria hasta el OOM y el sistema no se degrada: **colapsa**.

- **Colas acotadas.** Una cola ilimitada solo cambia el punto donde explotas, y mientras tanto añade latencia
  a todo lo que hay dentro.
- **Load shedding:** rechaza pronto (429/503) lo que no vas a poder atender. **Es mejor servir bien al 80%
  que fatal al 100%.** Prioriza: tira primero el tráfico de menos valor (batch, bots, reintentos).
- **Timeouts y deadlines propagadas:** si el cliente ya se rindió, tu servidor no debería seguir trabajando.
  Propagar el deadline por toda la cadena evita trabajo fantasma que solo consume recursos.
- **Streaming con control de flujo:** TCP ya lo hace; en tu app, procesa en lotes y no cargues todo en memoria.
- **Concurrencia limitada** (semáforos, pools): es la forma más simple de backpressure.

**El fallo típico sin backpressure:** llega un pico, la cola crece, la latencia sube, los clientes hacen
timeout **y reintentan**, lo que duplica la carga sobre un sistema ya saturado. Es una espiral de la muerte,
y es exactamente lo que previenen el load shedding y el circuit breaker.

> **Ficha** · **Cuándo:** cualquier sistema con colas o productores rápidos ·
> **Patrón:** colas **acotadas**, load shedding, concurrencia limitada, deadlines propagadas ·
> **Anti-patrón:** cola ilimitada — solo cambia el punto donde explotas, y añade latencia mientras tanto ·
> **Límites:** rechazar pronto significa devolver errores a usuarios legítimos ·
> **Cómo falla:** espiral de la muerte — timeout, reintento, más carga, más timeout ·
> **Decisión:** es mejor servir bien al 80% que fatal al 100% ·
> **Trade-off:** disponibilidad parcial vs colapso total ·
> **Relacionado:** rate limiting, circuit breakers `[03, 10]`

---

## Implementación: las técnicas, en código

**Cache-aside con single-flight** — el patrón por defecto, protegido contra el thundering herd:

```python
_en_curso: dict[str, asyncio.Future] = {}

async def con_cache(clave: str, ttl: int, calcular):
    if (valor := await redis.get(clave)) is not None:
        return json.loads(valor)

    # single-flight: si ya hay alguien calculando esta clave, espera a su resultado
    if clave in _en_curso:
        return await _en_curso[clave]

    fut = _en_curso[clave] = asyncio.get_event_loop().create_future()
    try:
        valor = await calcular()
        jitter = random.uniform(0.8, 1.2)          # TTL con jitter: evita expiracion sincronizada
        await redis.setex(clave, int(ttl * jitter), json.dumps(valor))
        fut.set_result(valor)
        return valor
    except Exception as e:
        fut.set_exception(e)
        raise
    finally:
        _en_curso.pop(clave, None)
```

**Matar un N+1 con batching** (el patrón DataLoader, que también resuelve el N+1 de GraphQL):

```python
# MAL: 1 + N queries
pedidos = await repo.pedidos.listar(limite=100)
for p in pedidos:
    p.cliente = await repo.clientes.get(p.cliente_id)     # 100 queries

# BIEN: 2 queries
pedidos = await repo.pedidos.listar(limite=100)
ids = {p.cliente_id for p in pedidos}
clientes = {c.id: c for c in await repo.clientes.get_muchos(ids)}   # WHERE id = ANY($1)
for p in pedidos:
    p.cliente = clientes[p.cliente_id]
```

**Limitar concurrencia hacia una dependencia** (bulkhead, `[10]`):

```python
class ClienteLimitado:
    def __init__(self, sem_max=10, timeout=2.0):
        self._sem = asyncio.Semaphore(sem_max)     # como mucho 10 en vuelo
        self._timeout = timeout

    async def get(self, url):
        async with self._sem:                      # si esta lleno, espera (backpressure)
            return await asyncio.wait_for(self._http.get(url), self._timeout)
```

**Streaming de una exportación grande** — memoria constante en vez de lineal:

```python
async def exportar_csv():
    async def filas():
        yield "id,total,divisa\n"
        async for p in repo.pedidos.iterar(lote=1000):   # cursor del servidor, no fetchall
            yield f"{p.id},{p.total},{p.divisa}\n"
    return StreamingResponse(filas(), media_type="text/csv")
```

> **Ficha** · **Cuándo:** las cuatro aparecen en casi cualquier servicio con carga ·
> **Patrón:** cachear con single-flight y jitter; batchear; acotar concurrencia; hacer streaming ·
> **Anti-patrón:** cache sin TTL, bucle de queries, concurrencia ilimitada, `fetchall()` ·
> **Límites:** el single-flight en memoria solo protege **dentro de un proceso**; con N réplicas hacen falta N regeneraciones o un lock distribuido ·
> **Cómo falla:** sin jitter, mil claves creadas a la vez expiran a la vez ·
> **Decisión:** batchear siempre que el coste dominante sea el round trip ·
> **Trade-off:** batching mejora throughput y empeora la latencia individual ·
> **Relacionado:** N+1, bulkheads, backpressure `[04, 10]`

---

## Diagnosticar un incidente de rendimiento

Síntoma típico: *"la aplicación va lenta"*. El orden que funciona:

1. **¿Lenta para quién y dónde?** ¿Un endpoint o todos? ¿Todos los usuarios o los que tienen muchos
   datos? ¿De golpe o gradual?
   - **De golpe** → un cambio: despliegue, configuración, pico de tráfico, un vecino ruidoso.
   - **Gradual** → crecimiento: datos, bloat, memory leak, un índice que dejó de ser selectivo,
     cache que perdió efectividad.
2. **¿Saturación o espera?** CPU alta = tu código. CPU baja y lento = **estás esperando** algo:
   base de datos, red, lock, o una cola en un pool.
3. **Traza de una petición lenta real** (`[12]`) y mira dónde se va el tiempo.
4. **Mitiga:** escalar, subir límites, activar cache, apagar la feature cara, rate limit al causante.
5. **Arregla de verdad** después, con el incidente ya cerrado.

| Firma | Causa probable |
|---|---|
| p50 bien, p99 fatal | GC, cache miss, usuarios con muchos datos, un shard lento |
| Todo lento a la vez | dependencia compartida: DB, cache, red |
| Lento solo al desplegar | cache fría, JIT sin calentar, connection pool vacío |
| Lento y con picos periódicos | cron, expiración sincronizada de cache, autovacuum |
| Latencia alta con CPU baja | cola en algún pool, o espera a un servicio externo |
| Empeora con el tiempo desde el arranque | memory leak, conexiones sin cerrar, fragmentación |

> **Ficha** · **Cuándo:** ante cualquier alerta de latencia ·
> **Patrón:** acotar antes de hipotetizar; preguntar **qué cambió** ·
> **Anti-patrón:** cambiar tres cosas a la vez bajo presión y no saber cuál funcionó ·
> **Límites:** sin trazas ni percentiles solo puedes adivinar ·
> **Cómo falla:** se optimiza lo que no era el cuello de botella y no mejora nada (Amdahl) ·
> **Decisión:** mitiga primero, diagnostica después ·
> **Trade-off:** mitigación rápida (pierdes evidencia) vs investigar (los usuarios siguen sufriendo) ·
> **Relacionado:** tracing, incident response `[10, 12]`

---

## Escalar en producción: el orden de intervención

De lo más barato a lo más caro. **Saltarse pasos es cómo se acaba con un sharding innecesario.**

1. **Medir** y encontrar el límite real (prueba de carga, `[11]`).
2. **Arreglar lo obvio:** índice que falta, N+1, query sin límite, trabajo síncrono que debería ser cola.
3. **Cachear.**
4. **Escalar vertical** — una línea de Terraform; compra meses o años.
5. **Escalar horizontal** lo stateless.
6. **Réplicas de lectura.**
7. **Particionado y archivado** de datos fríos.
8. **Sharding o separar servicios** — el último recurso (`[04]`).

**Señales de que se acerca el límite:** la latencia sube antes que la CPU (cola en un pool) · connection
pool al máximo · consumer lag creciendo · disco llenándose a ritmo constante · el autoscaling siempre al
tope. **Vigila tendencias, no valores instantáneos:** el objetivo es enterarte con semanas de margen.

**Autoscaling:** escala por la métrica que refleja saturación real (RPS, profundidad de cola, latencia),
no solo por CPU. Pon cooldowns, escala hacia abajo mucho más despacio que hacia arriba, y recuerda que
**arrancar una instancia tarda**: si el pico es más rápido que tu tiempo de arranque, necesitas capacidad
de reserva o una cola que absorba.

> **Ficha** · **Cuándo:** al planificar capacidad o ante crecimiento sostenido ·
> **Patrón:** agotar las opciones baratas antes de las estructurales ·
> **Anti-patrón:** shardear o partir en microservicios antes de haber puesto un índice ·
> **Límites:** el escalado horizontal exige servicios stateless; el vertical tiene techo físico ·
> **Cómo falla:** el autoscaling no llega a tiempo porque el arranque tarda más que el pico ·
> **Decisión:** ¿necesitas capacidad o disponibilidad? Solo lo segundo obliga a horizontal ·
> **Trade-off:** coste de infraestructura vs coste de ingeniería para optimizar ·
> **Relacionado:** capacity planning, sharding, coste `[04, 13, 19]`

---

## Preguntas de entrevista y trade-offs

**Q: Tu endpoint tarda 2s en p99 y 80ms en p50. ¿Qué investigas?**
Algo que solo pasa en algunos casos: usuarios con muchos datos (N+1 que escala con el volumen), cache miss,
GC, contención de pool, o un shard lento. *Señal:* dices que la media no sirve y que lo primero es un trace
de una request lenta concreta, no un cambio a ciegas.

**Q: ¿Cómo evitas el thundering herd al expirar una cache caliente?**
Single-flight (solo un hilo regenera, los demás esperan o sirven lo viejo), TTL con jitter y
`stale-while-revalidate`. *Señal:* mencionas que el problema no es la cache, es que **la DB recibe de golpe
todo el tráfico que la cache le estaba ocultando**, y que hay que dimensionar pensando en eso.

**Q: ¿Aumentar el pool de conexiones mejora el rendimiento?**
Hasta un punto; después lo empeora. *Señal:* explicas la ley de Little para dimensionar, y que la DB tiene
un óptimo cercano a `cores × 2` porque más conexiones compiten por los mismos recursos.

**Q: ¿Qué es backpressure y cómo lo implementas?**
Frenar al productor cuando el consumidor no da abasto: colas acotadas, load shedding, concurrencia limitada
y deadlines propagadas. *Señal:* describes la espiral de reintentos y dices que rechazar rápido es una
decisión de diseño deliberada, no un fallo.

**Q: Te piden "hacer la app más rápida". ¿Por dónde empiezas?**
Definir qué significa rápido (qué endpoint, qué percentil, qué objetivo), medir, y atacar lo que domina el
perfil. *Señal:* citas Amdahl y preguntas por el objetivo de negocio antes de tocar código — optimizar sin
un número objetivo es no saber cuándo parar.

**Trade-off central de esta caja:** *latencia vs frescura vs coste*. Cachear es cambiar frescura por
latencia; escalar es cambiar dinero por capacidad; el batching cambia latencia individual por throughput
global. No existe "más rápido" a secas — existe **qué estás dispuesto a pagar y en qué moneda**.

---

## Fuentes

- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) — las cuatro señales de oro.
- Gil Tene, *How NOT to Measure Latency* — por qué las medias y el coordinated omission engañan.
- [Brendan Gregg — Flame Graphs](https://www.brendangregg.com/flamegraphs.html) y el método USE.
- [AWS Builders' Library — Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)
- [PostgreSQL Performance Tuning Checklist 2026](https://dev.to/_d7eb1c1703182e3ce1782/postgresql-performance-tuning-checklist-2026-complete-guide-65a)
