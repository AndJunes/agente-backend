# 04 · Databases

> La caja donde más se cae en entrevistas senior y donde más dinero se pierde en producción.
> Regla empírica citada por casi todos los equipos de Postgres: **el 80% de los problemas de rendimiento
> son índices que faltan, el 15% queries mal diseñadas y el 5% gestión de conexiones.**


**Cubre del temario:** `concepts` · `modeling` · `queries` · `indexing` · `transactions` · `scaling` · `caching` · `implementations` · `failure_modes` · `tradeoffs`

---

## Relacional vs NoSQL: cómo se elige de verdad

La pregunta no es "¿cuál es mejor?" sino **"¿qué garantías necesito y qué patrón de acceso tengo?"**

| Necesitas | Elige |
|---|---|
| Transacciones multi-entidad, integridad referencial, queries ad-hoc | **PostgreSQL** |
| Escrituras masivas, escala horizontal, esquema por documento | MongoDB, DynamoDB |
| Latencia sub-ms, estructuras en memoria, TTL | **Redis** |
| Escritura brutal, alta disponibilidad, sin joins | Cassandra (LSM) |
| Analítica sobre columnas, agregaciones sobre billones de filas | ClickHouse, BigQuery (columnar) |
| Búsqueda full-text, facetas, relevancia | Elasticsearch / OpenSearch |
| Similitud vectorial | pgvector, Qdrant, Pinecone (ver `18-ai-backend.md`) |

**La postura senior en 2026: empieza con Postgres.** Hace JSON (JSONB con índices GIN), full-text search,
vectores (pgvector), colas (SKIP LOCKED), geoespacial (PostGIS) y time-series (TimescaleDB). Introducir
un segundo motor es introducir un problema de consistencia entre dos fuentes de verdad. **Hazlo cuando el
patrón de acceso lo exija de verdad, no por moda.**

> **Ficha** · **Cuándo:** al empezar un servicio o al notar que el motor actual no encaja ·
> **Patrón:** empezar con Postgres; añadir motores solo cuando el patrón de acceso lo exija ·
> **Anti-patrón:** elegir NoSQL "para escalar" con 10.000 usuarios ·
> **Límites:** cada motor extra es otra fuente de verdad que sincronizar y operar ·
> **Cómo falla:** dos almacenes con el mismo dato acaban discrepando, y nadie sabe cuál manda ·
> **Decisión:** ¿necesitas transacciones multi-entidad y queries ad-hoc? Relacional ·
> **Trade-off:** flexibilidad de esquema vs garantías de integridad ·
> **Relacionado:** CAP, sharding, vector databases `[08, 18]`

---

## Data modeling

**Normalización** (1NF → 3NF): cada dato en un solo sitio. Evita anomalías de actualización.
**Desnormalización**: duplicas a propósito para no hacer joins. Pagas con consistencia y con tener que
actualizar en varios sitios.

**La regla:** *normaliza hasta que duela, desnormaliza hasta que funcione.* Y cuando desnormalices, que haya
una única fuente de verdad y el resto sea derivado (materialized view, campo calculado con trigger, proyección
actualizada por eventos).

**Relaciones:**
- **1:N** → foreign key en el lado N. Trivial.
- **N:M** → tabla intermedia (`usuarios_roles`). Añade ahí los atributos de la relación (`asignado_en`).
- **1:1** → normalmente es la misma tabla; sepárala solo si hay columnas enormes o permisos distintos.
- **Jerarquías** → adjacency list (`parent_id`, simple, consultas recursivas con `WITH RECURSIVE`),
  materialized path, o nested sets. Para árboles poco profundos, adjacency list y ya.

**Decisiones que te perseguirán años:**
- **Claves primarias:** `BIGINT` autoincremental (compacto, ordenado, pero revela volumen y complica el
  sharding) vs **UUIDv4** (distribuido pero aleatorio → **fragmenta el índice B-tree y destroza la
  localidad de escritura**) vs **UUIDv7/ULID** (ordenados por tiempo: lo mejor de ambos). **En 2026, la
  respuesta por defecto es UUIDv7.**
- **Soft delete** (`deleted_at`): conserva historial pero **contamina todas las queries** y rompe los
  `UNIQUE`. Si lo usas, hazlo con vistas o con un filtro por defecto en el ORM, y usa índices parciales.
- **Dinero:** `NUMERIC`/`DECIMAL` o enteros de céntimos. **Nunca `FLOAT`.** `0.1 + 0.2 != 0.3`.
- **Tiempo:** `TIMESTAMPTZ` siempre, guarda en UTC, convierte en el borde. Guardar `TIMESTAMP` sin zona
  es un bug esperando al cambio de hora.
- **Enums:** tipo enum nativo (rígido: añadir valores requiere migración) vs tabla de lookup (flexible,
  con FK) vs `TEXT` con `CHECK`. Para valores que cambian con el negocio, tabla.

> **Ficha** · **Cuándo:** antes de la primera migración; después es caro ·
> **Patrón:** UUIDv7 como clave, `TIMESTAMPTZ` en UTC, dinero en enteros o `DECIMAL` ·
> **Anti-patrón:** `FLOAT` para dinero, `TIMESTAMP` sin zona, y UUIDv4 como PK (fragmenta el B-tree) ·
> **Límites:** el soft delete contamina todas las queries y rompe los `UNIQUE` ·
> **Cómo falla:** `0.1 + 0.2 != 0.3` descuadra la contabilidad de forma imperceptible durante meses ·
> **Decisión:** normaliza hasta que duela, desnormaliza hasta que funcione ·
> **Trade-off:** integridad (normalizado) vs velocidad de lectura (desnormalizado) ·
> **Relacionado:** multi-tenancy, migraciones `[17]`

---

## Índices

**Qué es un índice:** una estructura ordenada (normalmente B-tree) que evita leer toda la tabla. Acelera
lecturas y **ralentiza escrituras** (cada INSERT/UPDATE mantiene todos los índices) y ocupa disco.

**Tipos en PostgreSQL:**

| Tipo | Para qué |
|---|---|
| **B-tree** | el 95% de los casos: `=`, `<`, `>`, `BETWEEN`, `ORDER BY`, prefijos de `LIKE 'abc%'` |
| **Hash** | solo igualdad; rara vez merece la pena |
| **GIN** | contenido "dentro de" algo: JSONB, arrays, full-text search |
| **GiST** | geoespacial, rangos, vecinos más cercanos |
| **BRIN** | tablas enormes **naturalmente ordenadas** (logs por fecha); índice diminuto |
| **Índice parcial** | `WHERE activo = true` — más pequeño y más rápido |
| **Índice de expresión** | `ON usuarios (lower(email))` para búsquedas case-insensitive |
| **Covering / INCLUDE** | añade columnas al índice para conseguir un **index-only scan** |

**Las reglas que hay que saber decir:**

1. **Regla del prefijo izquierdo.** Un índice `(a, b, c)` sirve para `WHERE a`, `WHERE a AND b`,
   `WHERE a AND b AND c` — **pero no para `WHERE b`**. El orden de las columnas es la decisión clave.
2. **Orden de columnas:** primero igualdad, luego rango, luego las de `ORDER BY`. Un índice
   `(estado, creado_en)` sirve para `WHERE estado='x' ORDER BY creado_en`; al revés, no.
3. **Selectividad.** Indexar una columna booleana con 50/50 no sirve de nada: el planner preferirá el scan.
   Ahí es donde un índice *parcial* sí aporta.
4. **Un índice que no se usa es puro coste.** `pg_stat_user_indexes` te dice cuáles tienen `idx_scan = 0`.
5. **Funciones matan índices.** `WHERE DATE(creado_en) = '2026-01-01'` no usa el índice sobre `creado_en`;
   `WHERE creado_en >= '2026-01-01' AND creado_en < '2026-01-02'` sí. Igual con `WHERE campo + 0 = 5`
   o con un tipo distinto que fuerza cast implícito.
6. **En producción, `CREATE INDEX CONCURRENTLY`.** El `CREATE INDEX` normal **bloquea escrituras** en la
   tabla entera. Con tablas grandes eso es una caída.

**Leer un plan:**
```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```
Busca: `Seq Scan` sobre tablas grandes (falta índice), diferencia grande entre `rows` estimadas y reales
(estadísticas desactualizadas → `ANALYZE`), `Nested Loop` con muchas iteraciones, y `Sort` con
`external merge Disk` (sube `work_mem`).

> **Ficha** · **Cuándo:** con cada filtro, join u orden que expongas ·
> **Patrón:** orden de columnas = igualdad primero, luego rango, luego `ORDER BY` ·
> **Anti-patrón:** `WHERE DATE(creado_en) = ...` — una función sobre la columna anula el índice ·
> **Límites:** cada índice ralentiza las escrituras y ocupa disco ·
> **Cómo falla:** `CREATE INDEX` sin `CONCURRENTLY` **bloquea escrituras** en toda la tabla ·
> **Decisión:** regla del prefijo izquierdo: `(a,b,c)` no sirve para `WHERE b` ·
> **Trade-off:** velocidad de lectura vs coste de escritura y almacenamiento ·
> **Relacionado:** query optimization, pagination `[03, 09]`

---

## Transacciones y ACID

- **Atomicity** — todo o nada.
- **Consistency** — las invariantes (constraints, FKs) se respetan antes y después.
- **Isolation** — las transacciones concurrentes no se pisan (hasta el nivel que elijas).
- **Durability** — commit confirmado = sobrevive a un corte de luz (WAL + fsync).

### Isolation levels y las anomalías

| Nivel | Dirty read | Non-repeatable read | Phantom read | Write skew |
|---|---|---|---|---|
| Read Uncommitted | posible | posible | posible | posible |
| **Read Committed** (default Postgres) | no | posible | posible | posible |
| **Repeatable Read** (default MySQL/InnoDB) | no | no | no* | posible |
| **Serializable** | no | no | no | no |

- **Dirty read:** lees algo no confirmado. Postgres nunca lo permite.
- **Non-repeatable read:** lees la misma fila dos veces en una transacción y ha cambiado.
- **Phantom read:** repites una query con rango y aparecen filas nuevas.
- **Write skew:** dos transacciones leen el mismo estado, deciden por separado y juntas rompen una invariante.
  El ejemplo canónico: dos médicos de guardia se dan de baja a la vez; cada uno lee "hay 2 de guardia", los
  dos se van, y el hospital se queda sin nadie. **Ningún nivel por debajo de Serializable lo evita.**

\* En Postgres, Repeatable Read usa snapshot isolation y evita los phantoms clásicos, pero **no** el write skew.

**Cómo se resuelve en la práctica sin pagar Serializable:**
- `SELECT ... FOR UPDATE` — lock pesimista sobre las filas leídas.
- Un `UNIQUE` o un `CHECK` que haga imposible el estado inválido (deja que la DB haga cumplir la invariante).
- **Optimistic locking**: columna `version`, y `UPDATE ... WHERE version = $1`; si afecta 0 filas, alguien
  se te adelantó → 409 al cliente.

**Reglas de oro con transacciones:**
- **Cortas.** Una transacción abierta mientras llamas a una API externa es cómo se agota un connection pool
  y cómo aparecen locks eternos.
- **Nunca hagas I/O externo dentro de una transacción** (llamadas HTTP, envío de emails). Usa el
  **outbox pattern** (`08-distributed-systems.md`).
- **Orden consistente** al tocar varias filas, para no provocar deadlocks.

> **Ficha** · **Cuándo:** siempre que dos escrituras deban ocurrir juntas o ninguna ·
> **Patrón:** transacciones cortas; invariantes críticas como constraints de la DB ·
> **Anti-patrón:** llamar a una API externa dentro de una transacción abierta ·
> **Límites:** Read Committed (default de Postgres) **no** evita el write skew ·
> **Cómo falla:** dos transacciones leen el mismo estado y juntas rompen una invariante ·
> **Decisión:** ¿basta un `UNIQUE` o un `CHECK`? Entonces no necesitas Serializable ·
> **Trade-off:** aislamiento fuerte (correcto, lento, más abortos) vs débil (rápido, anomalías) ·
> **Relacionado:** locks, outbox, sagas `[08]`

---

## Locks y deadlocks

- **Row locks** (`FOR UPDATE`, `FOR NO KEY UPDATE`) vs **table locks** (los toman los DDL).
- **MVCC:** Postgres no bloquea lecturas. Cada transacción ve un snapshot; los **lectores nunca bloquean a
  los escritores ni al revés**. El precio es el **vacuum**: las versiones viejas (dead tuples) hay que
  limpiarlas, y si el autovacuum no da abasto la tabla se hincha (**bloat**) y las queries se degradan.
- **Deadlock:** Postgres lo detecta y mata a una de las dos transacciones con un error. **Tu aplicación debe
  reintentar** esa transacción: no es un bug de la DB, es el comportamiento esperado.
- **Lock queue trampa:** un `ALTER TABLE` que espera un lock **bloquea a todas las queries que llegan
  detrás**, aunque no entren en conflicto entre sí. Por eso las migraciones se hacen con
  `lock_timeout` corto y reintentos.
- **`SELECT ... FOR UPDATE SKIP LOCKED`:** cómo se implementa una **cola de trabajos dentro de Postgres**
  sin Redis ni Kafka. Varios workers cogen filas distintas sin bloquearse. Saber esto es un plus real.

> **Ficha** · **Cuándo:** con escrituras concurrentes sobre las mismas filas ·
> **Patrón:** orden consistente de adquisición + `SELECT ... FOR UPDATE SKIP LOCKED` para colas ·
> **Anti-patrón:** un `ALTER TABLE` en hora punta: bloquea a todo lo que llega detrás ·
> **Límites:** MVCC evita que lectores y escritores se bloqueen, y a cambio genera dead tuples ·
> **Cómo falla:** el autovacuum no da abasto, la tabla se hincha (bloat) y todo se degrada ·
> **Decisión:** los deadlocks son esperados: **tu aplicación debe reintentar la transacción** ·
> **Trade-off:** lock pesimista (serializa, seguro) vs optimista (concurrente, con reintentos) ·
> **Relacionado:** idempotencia, colas en Postgres `[08]`

---

## Migrations

**El principio que lo gobierna todo: en producción el código viejo y el nuevo conviven unos minutos (o días,
si haces canary). La migración debe ser compatible con ambos.**

**Expand / contract (el único patrón seguro):**
1. **Expand:** añade la columna nueva *nullable*, sin tocar la vieja. Despliega código que escribe en las dos.
2. **Backfill:** rellena en lotes (`UPDATE ... WHERE id BETWEEN` en batches con pausas), nunca de golpe.
3. **Migrate:** despliega código que lee de la nueva.
4. **Contract:** cuando nadie use la vieja, bórrala (en otro despliegue).

**Operaciones peligrosas en Postgres (bloquean):**
- Añadir columna **con default no volátil** → en PG 11+ ya no reescribe la tabla (antes sí). Aun así,
  añadir `NOT NULL` sin default sobre tabla con datos falla.
- `ALTER COLUMN TYPE` → reescribe la tabla entera. Con millones de filas, es downtime.
- Añadir una FK → toma un lock fuerte y valida todo. Hazlo en dos pasos: `NOT VALID` y luego
  `VALIDATE CONSTRAINT` (que no bloquea escrituras).
- `CREATE INDEX` sin `CONCURRENTLY`.

**Reglas operativas:** migraciones versionadas en el repo, idempotentes, **siempre con rollback pensado**
(aunque sea "no se puede, hay que restaurar"), probadas contra una copia del volumen de producción, y
separadas del despliegue de código para poder revertir una sin la otra.

> **Ficha** · **Cuándo:** todo cambio de esquema en producción ·
> **Patrón:** expand/contract en despliegues separados, con backfill en lotes ·
> **Anti-patrón:** añadir columna, migrar datos y borrar la vieja en el mismo despliegue ·
> **Límites:** durante un rolling update **conviven dos versiones del código** ·
> **Cómo falla:** `ALTER COLUMN TYPE` reescribe la tabla entera: downtime con millones de filas ·
> **Decisión:** FK nuevas como `NOT VALID` y después `VALIDATE`, para no bloquear ·
> **Trade-off:** varios despliegues coordinados a cambio de cero downtime ·
> **Relacionado:** estrategias de despliegue, rollback `[14]`

---

## Replication, sharding y escalado

**Replicación**
- **Síncrona:** el commit espera a la réplica. Cero pérdida de datos, mayor latencia, y si la réplica cae
  puedes bloquear las escrituras.
- **Asíncrona:** commit inmediato, la réplica va por detrás (**replication lag**). Es el default.
- **El bug clásico:** escribes y lees inmediatamente de una réplica → el usuario no ve su propio cambio.
  Soluciones: leer de la primaria tras escribir ("read-your-writes"), sticky por sesión durante N segundos,
  o esperar al LSN.

**Read replicas**: escalan lecturas, no escrituras. Y no son un backup (un `DELETE` se replica al instante).

**Particionado (dentro de una DB):** dividir una tabla grande por rango (fecha), lista o hash. Ventaja
enorme: borrar datos viejos es `DROP PARTITION` (instantáneo) en vez de un `DELETE` masivo que genera bloat.

**Sharding (entre DBs):** repartir los datos por una **shard key**. Lo que pierdes: joins entre shards,
transacciones globales, `UNIQUE` global y agregaciones. Lo que ganas: escalar escrituras.
- **Elegir la shard key es la decisión más irreversible que existe.** Debe repartir uniformemente y alinearse
  con tu patrón de consulta (normalmente `tenant_id` o `user_id`).
- **Hotspots:** si un tenant es el 40% del tráfico, has creado un cuello de botella con pasos extra.
- **Re-sharding** es un proyecto, no una tarea. Consistent hashing lo hace menos doloroso.
- **Regla senior:** *sharding es el último recurso.* Antes: índices, caching, read replicas, particionado,
  archivar datos fríos, y hardware más grande. Una sola instancia de Postgres bien afinada aguanta muchísimo
  más de lo que la gente cree.

> **Ficha** · **Cuándo:** cuando una sola instancia deja de dar ·
> **Patrón:** vertical → read replicas → particionado → archivar → **y solo entonces** sharding ·
> **Anti-patrón:** shardear antes de haber puesto índices y cache ·
> **Límites:** las réplicas escalan lecturas, nunca escrituras; el sharding te quita joins y `UNIQUE` global ·
> **Cómo falla:** escribes y lees de la réplica: el usuario no ve su propio cambio ·
> **Decisión:** la shard key es la decisión más irreversible que vas a tomar ·
> **Trade-off:** escala de escritura vs pérdida de garantías y complejidad operativa ·
> **Relacionado:** consistencia eventual, CAP `[08, 19]`

---

## Query optimization

**El proceso:**
1. **Mide, no adivines.** `pg_stat_statements` ordenado por `total_exec_time` te dice qué queries consumen
   de verdad — muchas veces es una query rápida ejecutada un millón de veces, no la lenta.
2. `EXPLAIN (ANALYZE, BUFFERS)` sobre las top 5.
3. Índice, reescritura o cambio de modelo.

**Los problemas recurrentes:**

- **N+1.** Cargas 100 pedidos y luego 1 query por pedido para el cliente. Solución: `JOIN`, `IN (...)`,
  o el eager loading de tu ORM (`select_related`/`joinedload`/`includes`). **Es el bug de rendimiento
  número uno de cualquier app con ORM.**
- **`SELECT *`** trae columnas grandes que no usas e impide index-only scans.
- **`OFFSET` grande** — usa keyset pagination (`03-apis.md`).
- **`COUNT(*)` exacto sobre tablas enormes** — es un scan. Usa una estimación de `pg_class.reltuples`,
  un contador mantenido, o di "más de 10.000" como hace Google.
- **`LIKE '%texto%'`** no usa índice B-tree. Necesitas GIN con `pg_trgm` o full-text search.
- **`OR` entre columnas distintas** suele impedir el uso de índices; a veces `UNION ALL` es más rápido.
- **Estadísticas desactualizadas** → el planner elige mal. `ANALYZE` y revisa el autovacuum.

> **Ficha** · **Cuándo:** cuando `pg_stat_statements` señale al culpable ·
> **Patrón:** medir por **tiempo total**, no por tiempo medio — suele ganar una query rápida ejecutada un millón de veces ·
> **Anti-patrón:** añadir índices a ciegas sin leer el plan ·
> **Límites:** `EXPLAIN` sin `ANALYZE` es una estimación, no la realidad ·
> **Cómo falla:** el **N+1** es el bug de rendimiento número uno de cualquier app con ORM ·
> **Decisión:** si las filas estimadas y las reales difieren mucho, el problema son las estadísticas ·
> **Trade-off:** desnormalizar acelera lecturas y añade trabajo de consistencia ·
> **Relacionado:** índices, caching, profiling `[09]`

---

## Connection pooling

Cada conexión a Postgres es **un proceso del sistema operativo** con su memoria. Mil conexiones no es
"mucha concurrencia", es un servidor muriéndose por context switching.

- **Pool de aplicación** (HikariCP, SQLAlchemy pool, pgx): reutiliza conexiones dentro del proceso.
- **Pooler externo** (**PgBouncer**, el estándar; Supavisor y el pooling nativo de PG 18 como alternativas):
  multiplexa miles de clientes sobre pocas conexiones reales.
- **Modos de PgBouncer:** `session` (una conexión por sesión de cliente), **`transaction`** (se devuelve al
  pool al acabar cada transacción — **el que da el multiplexado real y el que se usa**), `statement` (muy
  restrictivo).
- **Trampa de `transaction` mode:** rompe lo que depende de la sesión — prepared statements, `SET`,
  advisory locks, `LISTEN/NOTIFY`, temp tables. Muchos ORMs necesitan configuración específica.
- **Números orientativos:** `max_connections` en Postgres bajo (100-200) *porque* tienes pooler delante.
  El tamaño del pool de app se acerca más a `núcleos × 2 + husos de disco` que a "cuantas más mejor".
- **`idle_in_transaction_session_timeout`** agresivo: mata transacciones colgadas que bloquean el pool y
  el vacuum. Es una de las configuraciones que más incidentes evita.
- **Serverless + Postgres = problema clásico:** cada invocación quiere su conexión. Necesitas pooler
  externo sí o sí (o un driver HTTP).

> **Ficha** · **Cuándo:** desde el primer día, y obligatorio en serverless ·
> **Patrón:** PgBouncer en modo `transaction` + pool de app dimensionado por cores ·
> **Anti-patrón:** subir el pool "para ir más rápido" — pasado el óptimo, el throughput **baja** ·
> **Límites:** el modo `transaction` rompe prepared statements, `SET`, `LISTEN/NOTIFY` y temp tables ·
> **Cómo falla:** una transacción colgada agota el pool y todo se ve como latencia, no como error ·
> **Decisión:** `idle_in_transaction_session_timeout` agresivo, siempre ·
> **Trade-off:** multiplexado (más clientes) vs funciones de sesión que dejas de poder usar ·
> **Relacionado:** ley de Little, serverless `[09, 13]`

---

## Redis (lo esencial)

Single-threaded para comandos (así que todo comando es atómico), en memoria, con persistencia opcional
(RDB snapshots / AOF).

- **Estructuras:** strings, hashes, lists (colas), sets, **sorted sets** (rankings, colas por prioridad,
  rate limiting por ventana), streams (log append-only con consumer groups), HyperLogLog (conteo único
  aproximado), bitmaps.
- **Usos reales:** cache, sesiones, rate limiting, locks distribuidos, colas simples, pub/sub, leaderboards.
- **Cuidado:** `KEYS *` bloquea el servidor entero — usa `SCAN`. Las políticas de `maxmemory` (`allkeys-lru`
  vs `noeviction`) definen si Redis tira datos o empieza a dar errores cuando se llena.
- **Locks distribuidos:** `SET key valor NX PX 30000` y borrar solo si el valor es tuyo (script Lua).
  Redlock existe pero es discutido; para corrección estricta, un lock en Postgres es más seguro.

> **Ficha** · **Cuándo:** cache, sesiones, rate limiting, colas simples, rankings ·
> **Patrón:** todo con TTL; estructuras nativas (sorted sets) en vez de serializar JSON ·
> **Anti-patrón:** `KEYS *` en producción — bloquea el servidor entero (usa `SCAN`) ·
> **Límites:** single-threaded: un comando lento bloquea a todos los demás ·
> **Cómo falla:** con `maxmemory` alcanzada, o evicta datos que creías persistentes o empieza a dar errores ·
> **Decisión:** ¿los datos deben sobrevivir? Entonces Redis no es la fuente de verdad ·
> **Trade-off:** latencia sub-milisegundo vs durabilidad y coste de RAM ·
> **Relacionado:** caching, distributed locks `[08, 09]`

---

## Queries: joins, agregaciones y cómo se leen

**Los tipos de join**, que se preguntan constantemente:

```sql
-- INNER: solo las filas que casan en ambas tablas
SELECT p.id, c.email FROM pedidos p INNER JOIN clientes c ON c.id = p.cliente_id;

-- LEFT: todas las de la izquierda; NULL donde no hay pareja
SELECT c.email, p.id FROM clientes c LEFT JOIN pedidos p ON p.cliente_id = c.id;
--   ^ el patron para "clientes SIN pedidos": LEFT JOIN + WHERE p.id IS NULL

-- CROSS: producto cartesiano. Casi siempre es un bug (olvidar el ON)
```

**Agregaciones y la regla que todo el mundo rompe:** en `GROUP BY`, cada columna del `SELECT` debe estar
agrupada o agregada. `WHERE` filtra **antes** de agrupar; `HAVING`, **después**.

```sql
SELECT c.pais,
       COUNT(*)                      AS pedidos,
       SUM(p.total_centimos)         AS facturado,
       AVG(p.total_centimos)::int    AS ticket_medio
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.creado_en >= now() - interval '30 days'   -- filtra filas (usa indice)
GROUP BY c.pais
HAVING COUNT(*) > 100                              -- filtra grupos (no usa indice)
ORDER BY facturado DESC;
```

**Window functions** — agregar *sin* colapsar filas. Es lo que separa a quien sabe SQL de quien lo padece:

```sql
-- El ultimo pedido de cada cliente, sin subqueries correlacionadas
SELECT * FROM (
  SELECT p.*, ROW_NUMBER() OVER (PARTITION BY cliente_id ORDER BY creado_en DESC) AS n
  FROM pedidos p
) t WHERE n = 1;

-- Total acumulado por dia
SELECT dia, SUM(importe) OVER (ORDER BY dia) AS acumulado FROM ventas_diarias;
```

**CTEs y recursividad** para jerarquías (organigramas, categorías anidadas, comentarios):

```sql
WITH RECURSIVE arbol AS (
  SELECT id, nombre, padre_id, 1 AS nivel FROM categorias WHERE padre_id IS NULL
  UNION ALL
  SELECT c.id, c.nombre, c.padre_id, a.nivel + 1
  FROM categorias c JOIN arbol a ON c.padre_id = a.id
)
SELECT * FROM arbol ORDER BY nivel;
```

**Cómo se ejecuta un join** (y por qué a veces es lentísimo): *nested loop* (bueno si un lado es diminuto
y el otro tiene índice), *hash join* (bueno para tablas grandes sin orden; necesita memoria) y *merge
join* (si ambos vienen ordenados). El planner elige según estadísticas; **si elige mal, casi siempre es
porque las estadísticas están desactualizadas**.

> **Ficha** · **Cuándo:** en cualquier consulta que cruce tablas o resuma datos ·
> **Patrón:** window functions en vez de subqueries correlacionadas; `EXISTS` en vez de `IN` con subquery grande ·
> **Anti-patrón:** `SELECT *` con joins (colisión de nombres y columnas que no usas), y agregar en la
> aplicación lo que la DB agrega mejor · **Límites:** `HAVING` no usa índices; un hash join grande se va a disco ·
> **Cómo falla:** olvidar el `ON` produce un producto cartesiano que parece un cuelgue ·
> **Decisión:** si la agregación es cara y se repite, materialized view `[09]` ·
> **Trade-off:** hacer el trabajo en la DB (rápido, acopla) vs en la app (portable, mueve más datos) ·
> **Relacionado:** índices, query optimization, EXPLAIN `[09]`

---

## Implementaciones: qué cambia entre motores

| | PostgreSQL | MySQL / InnoDB | MongoDB | Redis |
|---|---|---|---|---|
| Aislamiento por defecto | Read Committed | **Repeatable Read** | por operación / transacciones multi-doc | comandos atómicos |
| Índices | B-tree, GIN, GiST, BRIN, parcial, expresión | B-tree, fulltext | B-tree, compuestos, TTL | n/a (estructuras) |
| JSON | **JSONB con índices GIN** | JSON (menos potente) | nativo | strings |
| Concurrencia | MVCC, lectores no bloquean | MVCC + gap locks | por documento | single-thread |
| Escalado horizontal | réplicas, particiones, extensiones | réplicas, Vitess | sharding nativo | Cluster |
| Fuerte en | integridad, queries complejas, extensiones | lecturas simples a gran escala, ecosistema | esquema flexible, documentos | latencia mínima |
| Trampa | bloat y autovacuum | **gap locks** producen deadlocks inesperados | sin joins reales; consistencia laxa por defecto | no es fuente de verdad |

**MySQL:** el aislamiento por defecto es más estricto que el de Postgres, pero los *gap locks* de
Repeatable Read bloquean rangos que no esperas y generan deadlocks sorprendentes. Su `utf8` histórico
**no es UTF-8 real** — hay que usar `utf8mb4` o los emojis rompen la inserción.

**MongoDB:** sin joins reales (`$lookup` existe y es caro). Modelas embebiendo lo que se lee junto, con
el límite duro de **16 MB por documento**. Las transacciones multi-documento existen desde la 4.0 pero
son caras: si las necesitas a menudo, el modelo de documentos no era el adecuado.

> **Ficha** · **Cuándo:** al heredar un sistema con otro motor o al evaluar migrar ·
> **Patrón:** conocer el aislamiento por defecto **del motor concreto** antes de razonar sobre concurrencia ·
> **Anti-patrón:** asumir que el SQL de Postgres funciona igual en MySQL ·
> **Límites:** 16 MB por documento en Mongo; `utf8` de MySQL no es UTF-8 ·
> **Cómo falla:** un patrón de bloqueo que funcionaba en Postgres produce deadlocks en MySQL ·
> **Decisión:** por defecto Postgres, salvo razón concreta y medida ·
> **Trade-off:** ecosistema y familiaridad vs capacidades del motor ·
> **Relacionado:** transacciones, isolation levels `[08]`

---

## Cómo falla una base de datos

| Fallo | Síntoma | Qué haces |
|---|---|---|
| **Pool agotado** | latencia alta sin CPU alta | timeout de adquisición, `idle_in_transaction_timeout` |
| **Deadlock** | error de transacción abortada | **reintentar** la transacción en la app |
| **Bloat / autovacuum atrasado** | degradación lenta y progresiva | subir agresividad del autovacuum, `VACUUM FULL` en ventana |
| **Transaction ID wraparound** | la base entra en modo solo-lectura | vigilar `age(datfrozenxid)` antes de llegar |
| **Replication lag** | el usuario no ve su escritura | leer de la primaria tras escribir |
| **Disco lleno** | escrituras fallan, WAL no rota | alertar al 70%, archivar particiones viejas |
| **Corrupción de datos** | errores de checksum, páginas ilegibles | activar `data_checksums`, restaurar desde backup + PITR `[10]` |
| **Conexión caída a mitad de transacción** | estado ambiguo para el cliente | idempotencia: el reintento debe ser seguro `[08]` |
| **Plan que cambia de golpe** | una query rápida pasa a tardar segundos | `ANALYZE`, revisar si creció la tabla o cambió la cardinalidad |

**Sobre la corrupción:** es rara pero real (hardware, bugs del sistema de archivos, fallos de energía).
Postgres la detecta si activas `data_checksums` **al inicializar el cluster** — activarlo después es
costoso. Sin checksums, la corrupción silenciosa se propaga a los backups y no te enteras hasta que
lees esa página. **Por eso restaurar backups periódicamente no es paranoia: es cómo detectas esto.**

> **Ficha** · **Cuándo:** al montar la monitorización de la base de datos ·
> **Patrón:** alertar sobre tendencias (bloat, lag, edad de transacción, disco) antes del umbral duro ·
> **Anti-patrón:** monitorizar solo CPU y memoria de la instancia ·
> **Límites:** una réplica **no** es un backup: replica también el `DROP TABLE` ·
> **Cómo falla:** la corrupción silenciosa se copia a los backups si nunca los restauras ·
> **Decisión:** `data_checksums` activado desde la creación del cluster ·
> **Trade-off:** checksums cuestan algo de CPU y detectan lo que de otro modo pierdes ·
> **Relacionado:** backups, PITR, disaster recovery `[10, 12]`

---

## Preguntas de entrevista y trade-offs

**Q: Una query que iba bien ahora tarda 8 segundos. ¿Cómo lo investigas?**
`pg_stat_statements` para confirmar cuál es → `EXPLAIN (ANALYZE, BUFFERS)` → compara filas estimadas vs
reales → mira si cambió el plan (estadísticas viejas, tabla que creció, índice que dejó de usarse), si hay
bloat por autovacuum insuficiente, o si es contención de locks. *Señal:* preguntas primero **qué cambió**
(volumen, despliegue, datos) en vez de saltar a añadir un índice.

**Q: ¿Qué es write skew y qué nivel de aislamiento lo evita?**
Dos transacciones leen el mismo estado, escriben filas distintas y juntas violan una invariante. Solo
Serializable lo previene. *Señal:* das el ejemplo de los dos médicos de guardia y añades que en la práctica
se resuelve más barato con `SELECT FOR UPDATE` o con un constraint que haga el estado inválido imposible.

**Q: ¿UUID o autoincremental como primary key?**
UUIDv7 (ordenado por tiempo): evita la fragmentación del índice de UUIDv4 y no revela volumen de negocio
como el autoincremental. *Señal:* explicas **por qué** UUIDv4 duele — inserciones aleatorias en el B-tree,
peor localidad, índices más grandes — y que en un sistema distribuido generar IDs en el cliente te evita
un round trip.

**Q: ¿Cómo añades una columna NOT NULL a una tabla de 500 millones de filas sin downtime?**
Expand/contract: añadir nullable → desplegar código que escribe en ambas → backfill en lotes → añadir el
constraint como `NOT VALID` y luego `VALIDATE` → contraer. *Señal:* mencionas `lock_timeout`, que el
backfill va en batches con pausas para no saturar la replicación, y que el código viejo y el nuevo conviven.

**Q: Tienes 2.000 conexiones a Postgres y el servidor va fatal. ¿Qué haces?**
PgBouncer en transaction mode, bajar `max_connections`, dimensionar el pool de app en función de cores, y
poner `idle_in_transaction_session_timeout`. *Señal:* explicas que cada conexión es un proceso y que más
conexiones ≠ más throughput — pasado el punto óptimo, el rendimiento *baja*.

**Q: ¿Cuándo shardearías?**
Casi nunca; primero índices, cache, réplicas de lectura, particionado y archivado. *Señal:* hablas de la
shard key como decisión irreversible, de hotspots por tenant, y de lo que pierdes (joins, transacciones
globales, unicidad global).

**Trade-off central de esta caja:** *consistencia y facilidad de consulta (relacional, una sola instancia)
vs escala de escritura y disponibilidad (distribuido, desnormalizado)*. Cada paso hacia la escala te quita
garantías que tu código tendrá que reimplementar a mano — peor y con más bugs que la base de datos.

---

## Fuentes

- [PostgreSQL docs](https://www.postgresql.org/docs/current/) — MVCC, isolation levels, índices, `EXPLAIN`.
- *Designing Data-Intensive Applications* (Martin Kleppmann) — la referencia sobre almacenamiento, réplicas y consistencia.
- [Use The Index, Luke](https://use-the-index-luke.com/) — cómo funcionan los índices B-tree en la práctica.
- [PgBouncer docs](https://www.pgbouncer.org/config.html) — modos de pooling y sus limitaciones.
- [PostgreSQL Connection Pooling en 2026: PgBouncer vs pooling nativo](https://postgresqlhtx.com/postgresql-connection-pooling-in-2026-when-to-use-pgbouncer-vs-built-in-pooling/)
