# 08 · Distributed Systems

> Un sistema distribuido es aquel en el que el fallo de una máquina que no sabías que existía puede dejar
> inutilizable la tuya (Lamport). Todo en esta caja existe porque **la red falla, los mensajes se duplican
> y el orden no está garantizado.**


**Cubre del temario:** `concepts` · `messaging` · `events` · `patterns` · `reliability` · `idempotency` · `implementations` · `failure_modes` · `tradeoffs`

---

## Las falacias de la computación distribuida

Los ocho supuestos falsos que todo el mundo asume al principio:
la red es fiable · la latencia es cero · el ancho de banda es infinito · la red es segura · la topología no
cambia · hay un solo administrador · el transporte no cuesta · la red es homogénea.

**Cada patrón de esta caja es la respuesta a una de estas falacias.**

> **Ficha** · **Cuándo:** al diseñar cualquier cosa que cruce la red ·
> **Patrón:** asumir fallo, latencia y duplicados como estado normal, no excepcional ·
> **Anti-patrón:** tratar una llamada remota como una llamada a función ·
> **Límites:** no puedes distinguir "lento" de "caído" desde fuera ·
> **Cómo falla:** un timeout ambiguo: no sabes si la operación se ejecutó ·
> **Decisión:** todo lo remoto necesita timeout, reintento acotado e idempotencia ·
> **Trade-off:** las garantías locales (ACID) se pagan carísimas en distribuido ·
> **Relacionado:** timeouts, idempotencia `[10]`

---

## CAP, PACELC y consistencia

**CAP:** ante una **partición de red** (P), eliges entre **consistencia** (C) y **disponibilidad** (A).
No es "elige 2 de 3": las particiones ocurren, así que en la práctica eliges entre **CP** y **AP**.

- **CP** — ante la duda, rechaza escribir. Bancos, inventario, reservas. (Postgres con replicación síncrona,
  etcd, ZooKeeper.)
- **AP** — sigue aceptando escrituras y reconcilia después. Carritos, feeds, contadores, DNS.
  (Cassandra, DynamoDB en modo eventual.)

**PACELC** completa la idea: *if Partition then A or C, Else Latency or Consistency*. Es decir, **incluso sin
partición** eliges entre latencia y consistencia. Es el trade-off que vives a diario con las read replicas.

**El espectro de consistencia:**
- **Strong / linearizable:** todos ven la última escritura. Caro, requiere coordinación.
- **Sequential / causal:** se respeta el orden causal, no hay reloj global.
- **Read-your-writes:** al menos *tú* ves lo que acabas de escribir. **Lo mínimo que espera un usuario.**
- **Monotonic reads:** no ves el tiempo ir hacia atrás.
- **Eventual:** si dejas de escribir, converge. No dice cuándo.

**Consenso** (Raft, Paxos): cómo un grupo de nodos acuerda un valor pese a fallos. Necesitas **quórum**
(mayoría: `N/2 + 1`), por eso los clusters son impares (3, 5). Raft es el que se usa hoy (etcd, Consul,
CockroachDB) porque es comprensible. **Lo que debes saber decir:** consenso es caro (round trips entre
nodos), así que se usa para metadatos y coordinación, no para el camino crítico de cada request.

> **Ficha** · **Cuándo:** al elegir motor y modelo de replicación ·
> **Patrón:** consistencia fuerte donde hay dinero o stock; eventual en el resto ·
> **Anti-patrón:** "elegimos 2 de 3" — las particiones ocurren, solo eliges C o A ·
> **Límites:** PACELC: incluso **sin** partición eliges entre latencia y consistencia ·
> **Cómo falla:** el usuario escribe, lee de una réplica y no ve su propio cambio ·
> **Decisión:** read-your-writes es el mínimo que espera un usuario ·
> **Trade-off:** coordinación (correcto, lento) vs disponibilidad (rápido, reconciliar después) ·
> **Relacionado:** replicación, consenso `[04]`

---

## Message queues y brokers

**Por qué una cola:** desacoplar en el tiempo (el consumidor puede estar caído), absorber picos
(buffer), reintentar sin bloquear al usuario, y paralelizar trabajo.

| | **Kafka** | **RabbitMQ** | **SQS / Pub-Sub** |
|---|---|---|---|
| Modelo | **log particionado y persistente** | broker con colas y exchanges | servicio gestionado |
| Retención | por tiempo/tamaño; **se puede releer** | se borra al consumir (ack) | días |
| Orden | **garantizado dentro de una partición** | por cola (se pierde con múltiples consumidores) | FIFO opcional |
| Throughput | altísimo | alto | alto, elástico |
| Routing | el consumidor elige topic/partición | **exchanges: direct, topic, fanout, headers** | básico |
| Fuerte en | event streaming, replay, múltiples consumidores independientes | task queues, routing complejo, prioridades | simplicidad operativa |

**Conceptos de Kafka que se preguntan:**
- **Partición** = unidad de paralelismo y de orden. El orden solo se garantiza **dentro** de una partición,
  por eso la **partition key** (normalmente `user_id`, `pedido_id`) decide qué eventos van ordenados juntos.
- **Consumer group:** cada partición la consume **un solo** miembro del grupo. Más consumidores que
  particiones = consumidores ociosos. **Tu paralelismo máximo es el número de particiones.**
- **Offset:** el puntero de lectura. Commitearlo antes de procesar = at-most-once (pierdes mensajes);
  después = at-least-once (duplicas). **Elige después, y hazte idempotente.**
- **Consumer lag:** la métrica de salud número uno de un consumidor. Si crece sin parar, no das abasto.

> **Ficha** · **Cuándo:** desacoplar en el tiempo, absorber picos, paralelizar ·
> **Patrón:** partition key que agrupe lo que debe ir ordenado (`pedido_id`) ·
> **Anti-patrón:** añadir consumidores por encima del número de particiones (quedan ociosos) ·
> **Límites:** el orden **solo** se garantiza dentro de una partición ·
> **Cómo falla:** el consumer lag crece y nadie lo vigila hasta que hay horas de retraso ·
> **Decisión:** Kafka para streaming y replay; RabbitMQ para colas de tareas con routing ·
> **Trade-off:** paralelismo vs orden — son directamente opuestos ·
> **Relacionado:** DLQ, consumer lag, backpressure `[09, 12]`

---

## Delivery semantics

| Garantía | Qué significa | Realidad |
|---|---|---|
| **At-most-once** | 0 o 1 veces | pierdes mensajes; casi nunca aceptable |
| **At-least-once** | 1 o más veces | **el estándar de la industria**; duplicados garantizados |
| **Exactly-once** | exactamente 1 | **imposible extremo a extremo** en el caso general |

**"Exactly-once" existe solo dentro de un sistema con transacciones** (Kafka transactions entre topics de
Kafka). En cuanto hay un efecto externo (cobrar, enviar un email, llamar a una API), lo único alcanzable es
**at-least-once + procesamiento idempotente**, que produce un resultado *efectivamente* único.

**Esta es una pregunta trampa muy común.** La respuesta correcta es: *"exactly-once delivery no existe;
exactly-once processing se consigue con at-least-once más idempotencia."*

> **Ficha** · **Cuándo:** al definir las garantías de cualquier consumidor ·
> **Patrón:** at-least-once + procesamiento idempotente = *efectivamente* una vez ·
> **Anti-patrón:** prometer exactly-once extremo a extremo ·
> **Límites:** exactly-once solo existe dentro de un sistema transaccional (Kafka↔Kafka) ·
> **Cómo falla:** commitear el offset **antes** de procesar pierde mensajes en silencio ·
> **Decisión:** commitea después de procesar y hazte idempotente ·
> **Trade-off:** perder mensajes vs duplicarlos ·
> **Relacionado:** idempotencia, outbox `[03]`

---

## Idempotencia (el pilar de todo)

Procesar el mismo mensaje dos veces debe dar el mismo estado final.

**Estrategias, de mejor a peor:**
1. **Operaciones naturalmente idempotentes.** `SET estado = 'pagado'` lo es; `saldo = saldo + 10` no.
   Rediseñar la operación es siempre mejor que añadir infraestructura.
2. **Tabla de deduplicación (inbox pattern).** `INSERT INTO procesados(message_id) ON CONFLICT DO NOTHING`
   **en la misma transacción** que el efecto. Si el insert no añade fila, ya estaba procesado.
3. **Actualización condicional / versión.** `UPDATE ... WHERE version = $1`.
4. **Upsert con clave natural.** `ON CONFLICT (pedido_id) DO UPDATE`.

**El detalle que lo hace correcto: la deduplicación y el efecto tienen que estar en la misma transacción.**
Si marcas "procesado" en Redis y luego escribes en Postgres, un crash entre medias te deja inconsistente.

> **Ficha** · **Cuándo:** en todo consumidor y todo endpoint que mute ·
> **Patrón:** rediseñar la operación para que sea naturalmente idempotente antes de añadir infraestructura ·
> **Anti-patrón:** marcar "procesado" en Redis y escribir el efecto en Postgres ·
> **Límites:** solo funciona si dedupe y efecto comparten transacción ·
> **Cómo falla:** un crash entre las dos escrituras deja el sistema inconsistente ·
> **Decisión:** `SET estado='pagado'` es idempotente; `saldo = saldo + 10` no ·
> **Trade-off:** una escritura extra a cambio de reintentos seguros ·
> **Relacionado:** inbox pattern, idempotency keys `[03, 07]`

---

## Outbox pattern (el problema de la doble escritura)

**El problema:** quieres guardar el pedido en la DB **y** publicar `PedidoCreado` en la cola. Son dos
sistemas: no hay transacción común.

- Si publicas primero y la DB falla → evento de un pedido que no existe.
- Si guardas primero y el broker falla → pedido sin evento; nadie se entera.
- Y los commits distribuidos (2PC/XA) son lentos, frágiles y hoy se evitan.

**La solución — convertir dos escrituras en una:**

```sql
BEGIN;
  INSERT INTO pedidos (...) VALUES (...);
  INSERT INTO outbox (id, tipo, payload, creado_en)
       VALUES (gen_random_uuid(), 'PedidoCreado', '{...}', now());
COMMIT;                      -- atómico: o están los dos, o ninguno
```

Después, un **relay** lee la tabla `outbox` y publica al broker (marcando o borrando lo enviado). Si el relay
falla, reintenta; si publica dos veces, el consumidor deduplica (at-least-once otra vez).

**Cómo se lee el outbox:**
- **Polling** con `SELECT ... FOR UPDATE SKIP LOCKED` — simple, suficiente para la mayoría.
- **CDC (Change Data Capture)** leyendo el WAL con Debezium — menos latencia y sin carga de polling, pero
  es infraestructura nueva que operar.

**Inbox pattern** es el espejo en el consumidor: guardas el `message_id` recibido en la misma transacción
que el efecto, para deduplicar.

**Detalles de producción:** archiva o borra los eventos publicados (la tabla crece rápido), y vigila el lag
del relay como métrica de primera clase.

> **Ficha** · **Cuándo:** cada vez que guardes estado **y** publiques un evento ·
> **Patrón:** insertar el evento en una tabla dentro de la misma transacción; un relay lo publica ·
> **Anti-patrón:** publicar al broker antes del commit, o usar 2PC ·
> **Límites:** el relay puede publicar dos veces → el consumidor debe deduplicar ·
> **Cómo falla:** la tabla outbox crece sin archivar y el lag del relay pasa desapercibido ·
> **Decisión:** polling con `SKIP LOCKED` para empezar; CDC si necesitas menos latencia ·
> **Trade-off:** latencia del polling vs complejidad operativa del CDC ·
> **Relacionado:** transacciones, idempotencia, eventos `[04, 07]`

---

## Sagas (transacciones distribuidas)

Cuando una operación de negocio cruza varios servicios y no puedes tener una transacción ACID global,
la partes en pasos locales, **cada uno con su compensación**.

```
Crear pedido → Reservar stock → Cobrar → Programar envío
    ↓ fallo en "Cobrar"
Compensar: liberar stock  →  cancelar pedido
```

**Dos estilos:**
- **Coreografía:** cada servicio escucha eventos y reacciona. Sin coordinador, bajo acoplamiento, pero
  **nadie conoce el flujo completo** — para entenderlo hay que leer cinco repos. Se vuelve inmanejable a
  partir de 4-5 pasos.
- **Orquestación:** un orquestador dirige explícitamente. El flujo es legible y depurable en un sitio; el
  precio es un componente central que debe ser durable (aquí entran Temporal, AWS Step Functions, o el
  Workflow DevKit).

**Lo que hay que entender de verdad:** una compensación **no es un rollback**. No borra lo que pasó: aplica
una acción inversa en el negocio (un reembolso, no un "des-cobro"). Y hay pasos que **no se pueden
compensar** (un email enviado, un SMS) — esos van al final, o se diseñan como reversibles.

**Además:** las sagas exponen estados intermedios visibles (alguien puede ver el pedido "reservado pero no
pagado"), así que la UI y el modelo deben contemplarlos.

> **Ficha** · **Cuándo:** una operación de negocio cruza varios servicios ·
> **Patrón:** orquestación con coordinador durable si hay más de 3-4 pasos ·
> **Anti-patrón:** coreografía con 6 servicios: nadie puede explicar el flujo completo ·
> **Límites:** una compensación **no es un rollback**: hay pasos no compensables ·
> **Cómo falla:** un estado intermedio visible (reservado pero no pagado) que la UI no contempla ·
> **Decisión:** ordena los pasos irreversibles al final ·
> **Trade-off:** autonomía (coreografía) vs trazabilidad (orquestación) ·
> **Relacionado:** service boundaries, state machines `[05, 17]`

---

## Retries, backoff y sus peligros

```python
for intento in range(max_intentos):
    try:
        return llamar()
    except ErrorTransitorio:
        if intento == max_intentos - 1:
            raise
        espera = min(base * (2 ** intento), tope)
        time.sleep(espera * (0.5 + random.random() / 2))   # JITTER: imprescindible
```

- **Solo reintenta lo transitorio.** Un 400 o un 401 no mejoran reintentando; un 429/503/timeout sí.
- **Backoff exponencial + jitter.** Sin jitter, mil clientes que fallan a la vez reintentan a la vez y
  provocan una **retry storm** que remata al servicio que se estaba recuperando.
- **Presupuesto de reintentos.** Reintentar en cada capa multiplica: 3 niveles × 3 reintentos = 27 llamadas.
  **Reintenta en un solo nivel**, idealmente el más cercano al fallo, y limita el ratio global de retries.
- **Respeta `Retry-After`** cuando el servidor te lo da.
- **Timeout siempre menor que el del que te llama**, o reintentarás mientras el cliente de arriba ya se rindió.
- **Combina con circuit breaker** (`10-reliability.md`): si el destino está caído, deja de intentarlo.

> **Ficha** · **Cuándo:** toda llamada remota que pueda fallar de forma transitoria ·
> **Patrón:** backoff exponencial **con jitter** y presupuesto global de reintentos ·
> **Anti-patrón:** reintentar en tres capas: 3×3×3 = 27 llamadas por petición ·
> **Límites:** reintentar solo es seguro si la operación es idempotente ·
> **Cómo falla:** **retry storm** — todos reintentan a la vez y rematan al servicio que se recuperaba ·
> **Decisión:** reintenta en una sola capa, la más cercana al fallo ·
> **Trade-off:** tasa de éxito vs carga sobre un sistema ya degradado ·
> **Relacionado:** circuit breakers, timeouts `[10]`

---

## Dead-letter queues

Mensajes que fallan repetidamente van a una cola aparte en vez de bloquear el consumo.

- **Por qué es obligatorio:** sin DLQ, un solo mensaje envenenado (*poison message*) que siempre falla
  bloquea la partición o la cola entera, y el lag crece hasta el infinito.
- **Qué guardar:** el mensaje original, el error, el número de intentos y el stack. Sin eso, la DLQ es un
  agujero negro.
- **Operativa:** alerta cuando entren mensajes, herramienta para inspeccionar y **reprocesar** tras arreglar
  el bug. Una DLQ que nadie mira es basura acumulada con coste.

> **Ficha** · **Cuándo:** obligatorio en todo consumidor ·
> **Patrón:** DLQ con mensaje original, error, intentos y stack; alerta al primer ingreso ·
> **Anti-patrón:** una DLQ que nadie mira ·
> **Límites:** al reprocesar, ese mensaje llega fuera de orden ·
> **Cómo falla:** sin DLQ, un **poison message** bloquea la partición y el lag crece sin fin ·
> **Decisión:** N reintentos y a la DLQ; nunca reintentos infinitos en línea ·
> **Trade-off:** descartar (avanzas) vs bloquear (no pierdes orden) ·
> **Relacionado:** consumer lag, alertas `[12]`

---

## Distributed locks

**Primero: evítalos.** La mayoría de "necesito un lock" se resuelve mejor con una operación atómica en la
base de datos, un `UNIQUE`, una partición por key (que serializa naturalmente) o idempotencia.

Si de verdad lo necesitas:
- **Redis:** `SET lock valor NX PX 30000`, y liberar **solo si el valor es tuyo** (script Lua). Redlock es
  discutido: bajo pausas de GC o relojes desajustados puede dar dos titulares a la vez.
- **Postgres advisory locks** — `pg_advisory_lock`: correcto y transaccional, sin infraestructura nueva.
- **etcd / ZooKeeper** — consenso real, la opción correcta si necesitas garantías fuertes.

**La verdad incómoda:** un lock distribuido con TTL **no garantiza exclusión mutua** si el titular se congela
(GC pause) más que el TTL. Para corrección estricta necesitas **fencing tokens**: un número creciente que el
recurso protegido comprueba y rechaza si es viejo.

> **Ficha** · **Cuándo:** último recurso, cuando no hay alternativa atómica ·
> **Patrón:** primero intenta un `UNIQUE`, un update atómico o partición por key ·
> **Anti-patrón:** confiar en un lock con TTL para garantizar corrección ·
> **Límites:** si el titular se congela (GC) más que el TTL, **hay dos titulares a la vez** ·
> **Cómo falla:** dos procesos creen tener el lock y ambos escriben ·
> **Decisión:** para corrección estricta necesitas **fencing tokens** ·
> **Trade-off:** simplicidad (Redis) vs corrección real (etcd/Postgres con fencing) ·
> **Relacionado:** locks de base de datos, idempotencia `[04]`

---

## Eventual consistency en la práctica

- **Read-your-writes:** tras escribir, lee de la primaria durante unos segundos, o guarda el LSN/versión
  y espera a que la réplica llegue.
- **Consistencia en la UI:** actualización optimista (pinta el resultado esperado y corrige si falla) o un
  estado "procesando" honesto. Lo peor es mentir y luego contradecirte.
- **CRDTs:** estructuras que convergen sin coordinación (contadores, sets). Base de la edición colaborativa.
- **Vector clocks / Lamport timestamps:** para establecer causalidad sin reloj global. **Los relojes de
  pared no son fiables entre máquinas** (drift, NTP, saltos hacia atrás): nunca ordenes eventos distribuidos
  por `now()`.

> **Ficha** · **Cuándo:** con réplicas, caches o proyecciones ·
> **Patrón:** read-your-writes por sesión; UI optimista con corrección visible ·
> **Anti-patrón:** ordenar eventos distribuidos por `now()` ·
> **Límites:** "eventual" no dice **cuándo**; mide el lag y ponle objetivo ·
> **Cómo falla:** el usuario guarda, recarga y ve datos viejos ·
> **Decisión:** para causalidad usa versiones o vector clocks, nunca timestamps ·
> **Trade-off:** latencia baja (leer réplicas) vs ver siempre lo último ·
> **Relacionado:** CAP, replicación, CQRS `[04, 05]`

---

## Eventos: esquema, versionado y contrato

**Un evento publicado es una API pública.** La diferencia es que casi nadie lo versiona, y por eso los
sistemas event-driven se rompen en silencio.

```json
{
  "event_id": "01J8XZ...",              // unico y estable -> el consumidor deduplica con esto
  "event_type": "pedido.pagado",
  "event_version": 2,                    // version del ESQUEMA, no del recurso
  "occurred_at": "2026-09-15T04:12:33Z", // cuando paso de verdad (no cuando se publico)
  "producer": "servicio-pagos",
  "trace_id": "4bf92f...",               // propaga el contexto de tracing [12]
  "tenant_id": "t_7",
  "resource": {"id": "ped_123", "version": 4},   // version del recurso -> detectar desorden
  "data": { "total_centimos": 5000, "divisa": "EUR" }
}
```

**Las reglas de evolución**, iguales que en una API REST (`[03]`):

- **Compatible:** añadir un campo opcional, añadir un tipo de evento nuevo.
- **Breaking:** quitar o renombrar un campo, cambiar un tipo, **cambiar el significado**.
- Para un cambio breaking: publica `v2` **en paralelo** a `v1`, migra a los consumidores, y retira `v1`
  cuando puedas demostrar que nadie lo consume.

**Nombra el evento como un hecho pasado** (`pedido.pagado`, no `pagar_pedido`): un evento notifica algo
que **ya ocurrió**, no ordena algo. Si tu "evento" es una orden, lo que quieres es un comando o una
llamada síncrona.

**Dos estilos de payload:**

| | Notification | State transfer |
|---|---|---|
| Payload | mínimo (solo el id) | el estado relevante |
| El consumidor | te llama para los detalles | no necesita llamarte |
| Acoplamiento | bajo | alto en el esquema |
| Coste | más tráfico y latencia | duplicación de datos |
| Riesgo | el recurso ya cambió cuando lo consultas | payload obsoleto si llega tarde |

**Schema registry** (Avro/Protobuf con Confluent, o JSON Schema en tu repo): valida al publicar que el
evento cumple el contrato y bloquea cambios incompatibles en CI. Sin él, el contrato existe solo en la
cabeza de quien lo escribió.

> **Ficha** · **Cuándo:** antes de publicar el primer evento ·
> **Patrón:** supervivencia por diseño — `event_id`, versión de esquema, versión de recurso y `trace_id` ·
> **Anti-patrón:** publicar el modelo interno de tu base de datos como evento ·
> **Límites:** una vez publicado, no puedes retirar un evento del consumo de otros ·
> **Cómo falla:** un consumidor asume orden y llega `pagado` antes que `creado` ·
> **Decisión:** incluye la versión del recurso para que el consumidor descarte lo viejo ·
> **Trade-off:** payload rico (autónomo) vs mínimo (desacoplado del esquema) ·
> **Relacionado:** versionado de APIs, contract testing, tracing `[03, 11, 12]`

---

## Implementación: productor y consumidor correctos

**Productor con outbox** — el relay que convierte dos escrituras en una:

```python
SQL_PENDIENTES = (
    "SELECT * FROM outbox WHERE publicado_en IS NULL "
    "ORDER BY creado_en LIMIT 100 "
    "FOR UPDATE SKIP LOCKED"        # varios relays cogen filas distintas sin bloquearse
)

async def relay_outbox():
    while True:
        async with uow.transaccion() as tx:
            for e in await tx.execute(SQL_PENDIENTES):
                await broker.publicar(e.tipo, e.payload, key=e.particion_key)
                await tx.execute("UPDATE outbox SET publicado_en = now() WHERE id = $1", e.id)
        await asyncio.sleep(0.5)
```

**Consumidor idempotente** — el inbox: deduplicación y efecto en la misma transacción:

```python
async def consumir(mensaje):
    for intento in range(3):
        try:
            async with uow.transaccion() as tx:
                # si ya estaba, no inserta y devuelve 0 filas -> ya procesado
                nuevo = await tx.execute(
                    "INSERT INTO procesados (event_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    mensaje.event_id)
                if nuevo.rowcount == 0:
                    return await mensaje.ack()          # duplicado: ack y fuera

                await aplicar_efecto(tx, mensaje)       # MISMA transaccion que el dedupe
            return await mensaje.ack()                  # ack DESPUES de procesar
        except ErrorTransitorio:
            await asyncio.sleep((2 ** intento) * random.uniform(0.5, 1.5))   # backoff + jitter
        except Exception as e:
            await dlq.enviar(mensaje, error=e, intentos=intento + 1)   # poison -> DLQ
            return await mensaje.ack()
```

**Los cinco detalles que lo hacen correcto:** `SKIP LOCKED` permite varios relays · el ack va **después**
de procesar · dedupe y efecto comparten transacción · los errores transitorios reintentan con jitter ·
los permanentes van a la DLQ en vez de bloquear la partición para siempre.

> **Ficha** · **Cuándo:** plantilla de cualquier consumidor de cola ·
> **Patrón:** dedupe + efecto en una transacción; ack al final; DLQ para lo envenenado ·
> **Anti-patrón:** `ack` al recibir "para no bloquear la cola" — pierdes mensajes ·
> **Límites:** el mensaje puede reentregarse aunque el proceso hiciera todo bien (ack perdido) ·
> **Cómo falla:** sin `ON CONFLICT DO NOTHING`, dos entregas simultáneas aplican el efecto dos veces ·
> **Decisión:** si el efecto no puede ser idempotente, guarda el resultado y devuélvelo ·
> **Trade-off:** procesar en lote (throughput) vs uno a uno (aislamiento de fallos) ·
> **Relacionado:** outbox, DLQ, retries `[04]`

---

## Cómo falla un sistema distribuido

| Fallo | Síntoma | Mitigación |
|---|---|---|
| **Timeout ambiguo** | no sabes si se ejecutó | idempotencia + conciliación `[07]` |
| **Partición de red** | dos mitades operando por separado | quórum, fencing |
| **Split-brain** | dos primarios aceptando escrituras | consenso (Raft), fencing tokens |
| **Duplicados** | efecto aplicado dos veces | dedupe por `event_id` |
| **Desorden** | `pagado` antes que `creado` | lógica por estado + versión de recurso |
| **Poison message** | lag creciendo, consumidor en bucle | DLQ tras N intentos |
| **Retry storm** | el servicio no logra recuperarse | backoff con jitter + circuit breaker `[10]` |
| **Consumer lag** | los efectos llegan con horas de retraso | alertar por lag, escalar consumidores |
| **Reloj desajustado** | eventos ordenados mal | nunca ordenar por `now()` entre máquinas |
| **Fallo en cascada** | todo cae por un servicio lento | timeouts, bulkheads, degradación `[10]` |
| **Outbox atascado** | nadie recibe eventos y la DB está bien | monitorizar antigüedad del evento sin publicar |

**El patrón común:** los fallos distribuidos son **parciales y silenciosos**. Nada devuelve un error;
simplemente el sistema deja de estar de acuerdo consigo mismo. Por eso la observabilidad (`[12]`) no es
un extra en arquitecturas distribuidas: es la única forma de saber que algo va mal.

> **Ficha** · **Cuándo:** al montar la monitorización de un sistema con colas ·
> **Patrón:** alertar por **consumer lag** y por antigüedad del mensaje más viejo, no solo por errores ·
> **Anti-patrón:** dar por bueno que "no hay errores en los logs" ·
> **Límites:** no puedes distinguir un consumidor lento de uno parado sin mirar el lag ·
> **Cómo falla:** el sistema "funciona" pero lleva dos horas de retraso y nadie lo sabe ·
> **Decisión:** cada cola necesita dueño, alerta de lag y runbook ·
> **Trade-off:** más alertas vs detección tardía ·
> **Relacionado:** observabilidad, DLQ, SLOs `[10, 12]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Se puede garantizar exactly-once?**
No en la entrega extremo a extremo. Se consigue at-least-once + idempotencia en el consumidor. *Señal:*
explicas que el problema es el ack perdido: el productor no sabe si el mensaje llegó, así que reenvía; y
que "exactly-once" de Kafka aplica solo dentro de Kafka.

**Q: Guardas un pedido y publicas un evento. ¿Cómo garantizas que pasen los dos o ninguno?**
Outbox pattern: insertar el evento en una tabla dentro de la misma transacción, y un relay lo publica.
*Señal:* mencionas por qué 2PC se descartó (lento, frágil, bloquea si el coordinador cae) y que el relay
puede duplicar, lo que devuelve la pelota a la idempotencia del consumidor.

**Q: ¿Kafka o RabbitMQ?**
Kafka para event streaming, replay y varios consumidores independientes del mismo flujo; RabbitMQ para
colas de tareas con routing y prioridades. *Señal:* mencionas que el paralelismo en Kafka está limitado por
el número de particiones y que la partition key determina el orden, que es la decisión de diseño de verdad.

**Q: Un consumidor tiene 4 millones de mensajes de lag. ¿Qué haces?**
Primero mides si es un pico o una degradación; miras si hay poison messages, si el procesamiento se volvió
lento (una query nueva, un servicio externo lento), y si puedes escalar consumidores (limitado por
particiones). *Señal:* sabes que añadir consumidores por encima del número de particiones no hace nada, y
propones batching o procesamiento paralelo dentro del consumidor si no puedes reparticionar.

**Q: ¿Qué es write skew / cómo se compensa una saga?**
(Ver también `04-databases.md`.) Una compensación aplica una acción inversa de negocio, no un rollback
técnico. *Señal:* señalas los pasos no compensables y dices que se ordenan al final del flujo.

**Q: ¿Por qué el jitter en los reintentos?**
Porque sin él, todos los clientes que fallaron a la vez reintentan a la vez y crean una onda que impide
que el servicio se recupere. *Señal:* mencionas el presupuesto de reintentos y el peligro de reintentar en
varias capas a la vez.

**Trade-off central de esta caja:** *garantías vs coordinación*. Cada garantía fuerte (orden total,
consistencia estricta, exclusión mutua) se paga con coordinación, y la coordinación cuesta latencia y
disponibilidad. El diseño senior consiste en **exigir garantías fuertes solo donde el negocio las necesita
de verdad** (dinero, stock) y aceptar consistencia eventual en todo lo demás.

---

## Fuentes

- *Designing Data-Intensive Applications* (Martin Kleppmann) — la referencia de esta caja.
- [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html) y [Saga](https://microservices.io/patterns/data/saga.html) — Chris Richardson.
- [Outbox pattern: buenas prácticas 2026](https://www.sachith.co.uk/outbox-pattern-for-reliable-events-best-practices-in-2025-practical-guide-may-8-2026/)
- [Idempotency Patterns: Building Retry-Safe Distributed Systems](https://backendbytes.com/articles/idempotency-patterns-distributed-systems/)
- Martin Kleppmann, [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) — por qué Redlock no garantiza exclusión.
- [AWS Builders' Library — Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
