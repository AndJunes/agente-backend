# Ejemplo de salida de `arquitecto.py`

Generado con:

```bash
python3 arquitecto.py "Necesito un sistema de reservas para 200 gimnasios. Cada gimnasio
tiene clases con plazas limitadas y los usuarios reservan desde una app movil.
Pico los lunes a las 8:00 cuando se abren las reservas de la semana."
```

5 fases · 982 lineas · ~7.500 palabras · unos 8 minutos.
Las lineas `🔧` son las llamadas reales a las skills.

---


══════════════════════════════════════════════════════════════════════
1 · Entender
══════════════════════════════════════════════════════════════════════
# EXTRACCIÓN DEL PROBLEMA: SISTEMA DE RESERVAS DE GIMNASIOS

## (a) REQUISITOS FUNCIONALES

| Capacidad | Descripción |
|-----------|-------------|
| Crear/gestionar reservas | Usuario reserva una plaza en una clase específica |
| Validar disponibilidad | No permitir reserva si no hay plazas libres |
| Consultar clases | Listar clases disponibles, horarios, plazas |
| Cancelar reservas | Usuario cancela su reserva |
| Gestionar catálogo | 200 gimnasios, cada uno con clases y horarios |
| Autenticación/perfil | Usuario móvil debe identificarse |

---

## (b) REQUISITOS NO FUNCIONALES

| Dimensión | Valor/Expectativa |
|-----------|-------------------|
| **Escala** | 200 gimnasios, N usuarios (desconocido) |
| **Pico de carga** | Lunes 8:00 AM: ráfaga de reservas simultáneas |
| **Latencia objetivo** | No especificada → ASUMIR <2s para reserva (retail estándar) |
| **Consistencia** | CRÍTICA: no vender 2 veces la misma plaza |
| **Disponibilidad** | Alta (pico es momento crítico; caída = ingresos perdidos) |
| **Durabilidad** | Total: confirmación de reserva es contrato |
| **Normativa** | Probablemente GDPR (datos personales); quizá protección de menores |
| **Coste** | No mencionado → ASUMIR tolerable pero relevante |

---

## (c) SUPUESTOS EXPLÍCITOS

| Supuesto | Justificación |
|----------|---------------|
| **N usuarios activos desconocido** | "200 gimnasios" dice oferta, no demanda. ¿100 usuarios o 100k? Asumo **modelo de competencia**: múltiples usuarios por clase en pico → congestión probable |
| **1 reserva = 1 plaza** | No hay "reserva grupal" mencionada |
| **Cancelación siempre permitida** | Sin restricción de ventana temporal |
| **Gimnasios son independientes** | No hay reservas cross-gimnasios |
| **Pico es predecible** | "Lunes 8:00" es patrón regular, no sorpresa |
| **Usuario móvil = única interfaz** | No hay web, admin, integraciones mencionadas aquí |
| **Plazas fijas por clase** | No overflow, no cola de espera |

---

## (d) TIPO DE PROBLEMA

**Transaccional de alto volumen con consistencia crítica:**
- Operación: read-check-write atómico (validar plaza disponible → reservar)
- Patrón: **race condition natural** en pico (múltiples usuarios ven misma plaza libre)
- Lectura dominante fuera de pico; escritura explosiva en pico
- Semejante a: venta de entradas, banca de pagos, overbooking prevention

---

## PREGUNTA CLAVE QUE CAMBIA EL DISEÑO

**¿Aceptamos sobreventa (race condition ocasional) o la prohibimos totalmente?**

Respuesta = afecta:
- Arquitectura de transacciones (locks vs. optimistic)
- Infraestructura (cluster de BD o serverless)
- Coste operacional
- UX (reintentos, error handling)

*Si toleramos "muy raramente quedan 2 personas sin plaza": diseño simple.*
*Si es zero-tolerance: complejidad + coste.*

══════════════════════════════════════════════════════════════════════
2 · Asociar
══════════════════════════════════════════════════════════════════════
  🔧 cajas_relacionadas({'caja': 'Databases'})
  🔧 cajas_relacionadas({'caja': 'Distributed Systems'})
  🔧 cajas_relacionadas({'caja': 'APIs'})
  🔧 cajas_relacionadas({'caja': 'Performance'})
  🔧 cajas_relacionadas({'caja': 'Reliability'})
  🔧 cajas_relacionadas({'caja': 'Security'})
  🔧 cajas_relacionadas({'caja': 'Architecture'})
  🔧 buscar_en_docs({'query': 'transacciones ACID consistencia strict serializability'})
  🔧 buscar_en_docs({'query': 'race condition overbooking reservas concurrencia'})
  🔧 buscar_en_docs({'query': 'lock pessimistic optimistic versioning timestamps'})
  🔧 buscar_en_docs({'query': 'eventual consistency eventual conflictos distribuidos'})
  🔧 buscar_en_docs({'query': 'idempotencia retry transacciones at-least-once'})
  🔧 buscar_en_docs({'query': 'circuit breaker timeout fallback alta disponibilidad'})
---

## FASE 2 · ASOCIAR: Mapa de Áreas y Dependencias

### (a) TABLA: ÁREAS CLAVE Y SUS APORTES AL PROBLEMA

| Caja | Aportes Concretos | Razón |
|------|------------------|-------|
| **04 · Databases** | Transacciones ACID / Isolation levels / Locks pesimistas vs optimistas | Núcleo: validar "plaza disponible" y reservar son una operación atómica. Read Committed (Postgres) ≠ Repeatable Read (MySQL). Write skew en pico. |
| **08 · Distributed Systems** | CAP (CP vs AP) / Outbox pattern / At-least-once delivery / Idempotencia | Si hay múltiples BD o cache: consistency garantizada vs eventual. Confirmación de reserva es evento crítico. |
| **03 · APIs** | Rate limiting / HTTP status codes (409 conflicto, 429 sobrecarga) | Contrato móvil-servidor. Pico de lunes 8:00 requiere rechazo elegante, no crash. |
| **09 · Performance** | Backpressure / Load shedding / Connection pooling | Pico predecible: no sobrecargar BD ni workers. Rechazar 429 es mejor que latencia infinita. |
| **10 · Reliability** | Circuit breaker / Timeouts / Degradación / Cascadas de fallo | Dependencias externas (si existen: SMS, email de confirmación). Fallos de la BD no caen la app. |
| **06 · Security** | Autenticación / Rate limiting por usuario | Usuario móvil debe identificarse. Privacidad de datos personales (GDPR aludido). |
| **05 · Architecture** | Monolito vs microservicios / System boundaries | 200 gimnasios: ¿un servicio único o separado por gimnasio? Decisión de fronteras. |
| **12 · Observability** | Logging / Tracing / Métricas (p99, lag de transacciones) | Monitorear el pico de las 8:00, detectar anomalías. Critical: race condition observable. |

---

### (b) DEPENDENCIAS CRÍTICAS: Qué necesita a qué

```
RAÍZ DEL PROBLEMA: Evitar la race condition de sobreventa
                            ↓
            ┌───────────────┴───────────────┐
            ↓                               ↓
    [04 Databases]             [08 Distributed Systems]
     Transacciones                Idempotencia
     Isolation levels             At-least-once
     Locks & MVCC                 Outbox pattern
            │                               │
            ├──────────────┬────────────────┤
            │              │                │
            ↓              ↓                ↓
   [09 Performance]   [10 Reliability]   [03 APIs]
   Backpressure       Circuit breaker    HTTP 409/429
   Load shedding      Timeouts           Retry semantics
   Connection pool                       Idempotent operations
            │              │                │
            └──────────────┴────────────────┘
                        ↓
            [12 Observability]
            Métricas del pico
            Detectar anomalías
            P99 latencies
```

---

### (c) PUNTOS DE INTERSECCIÓN CRÍTICOS

| Intersección | Concepto Emergente | Por qué importa |
|---|---|---|
| **DB + Performance** | Connection pooling / Índices sobre (`gimnasio_id`, `clase_id`, `plazas_libres`) | Pico: 1000+ queries/s contra las mismas tablas. Pool exhausto = timeout en cascada. |
| **DB + Distributed Systems** | Idempotencia de transacciones + retry de la app | Si app reintenta una reserva (timeout), BD no puede vender dos veces la misma plaza. |
| **DB + Reliability** | Deadlock handling + automatic retry | Write skew en lunes 8:00: dos usuarios leen "hay plazas", ambos insertan → deadlock. App debe reintentar. |
| **APIs + Reliability** | 409 Conflict para optimistic locking, 429 Rate limit | Conflicto de concurrencia no es error; es `409`. Saturación del pico no es `500`: es `429 + Retry-After`. |
| **APIs + Security** | Rate limiting por usuario + autenticación | Evitar ataque por agotamiento de sesiones. Cada usuario tiene derecho a X reservas en N minutos. |
| **Distributed Systems + Performance** | Eventual consistency de caches vs Strong consistency de inventario | Cache de horarios puede ser eventual; plaza disponible es strong consistency crítica. |

---

### (d) SUPUESTO EXPLÍCITO PARA ESTA FASE

**Asumimos que los requisitos del Problema son reales y el sistema comienza como monolito modular (03 caja 05):** una BD central para los 200 gimnasios, una API REST que expone las operaciones, con lógica de negocio en Python/Node/Go según tu equipo. Escalado horizontal de la app, pero BD única (replicada para alta disponibilidad). **Revisaremos esta suposición en fases 3 y 4 si el pico es irresisible.**

══════════════════════════════════════════════════════════════════════
3 · Decidir
══════════════════════════════════════════════════════════════════════
  🔧 buscar_tradeoffs({'tema': 'Pessimistic locking vs Optimistic locking for inventory management'})
  🔧 buscar_tradeoffs({'tema': 'Single master database vs Multi-region replication for high availability'})
  🔧 buscar_tradeoffs({'tema': 'Rate limiting strategy: token bucket vs sliding window vs fixed window'})
  🔧 buscar_tradeoffs({'tema': 'Handling database connection exhaustion under spike load'})
  🔧 buscar_tradeoffs({'tema': 'Eventual consistency cache vs strong consistency for inventory plazas'})
  🔧 buscar_en_docs({'query': 'Inventory reservation race condition pessimistic vs optimistic locking'})
  🔧 buscar_en_docs({'query': 'Database isolation levels and write skew'})
  🔧 buscar_en_docs({'query': 'Queue based backpressure spike load handling'})
Perfecto. Ahora tengo el material para decisiones precisas sobre el problema de sobreventa. Voy a escribir las decisiones concretas.

---

## FASE 3 · RAZONAR: Decisiones Clave

### **D1: Control de sobreventa — Pessimistic locking vs Optimistic**

**Contexto:** La invariante es "nunca vender la misma plaza dos veces". En el pico de las 8:00 (lunes), múltiples usuarios verán plazas disponibles simultáneamente. Debo evitar que dos INSERT de reserva ocurran cuando el stock está a 1.

| Aspecto | Pessimistic (SELECT FOR UPDATE) | Optimistic (versión en BD) |
|---|---|---|
| **Cómo funciona** | Bloquea la fila de clase mientras se reserva → otra transacción espera | Lee versión; intenta UPDATE; si versión no coincide, falla con 0 filas → 409 al cliente |
| **En pico** | 1.000 transacciones blocadas esperando 1 fila = cuello de botella = latencia explota | 1.000 transacciones legítimas en paralelo; algunas fallan con 409 → cliente reintenta |
| **Pool de conexiones** | Se agota por transacciones colgadas → timeout en cascada | Transacciones ultra-cortas → pool disponible |
| **UX** | Usuario espera; después, o tiene plaza o no (pero sin ambigüedad) | Usuario puede ver 409; la app reintenta transparente (o falla si reintentos agotados) |
| **Implementación** | Trivial en SQL | Trivial en SQL; requiere idempotencia en la app |
| **Recuperación de fallo** | Si cae la transacción, plaza queda libre (bien); si se cuelga, es un problema | Si cae la app, el cliente reintenta; sin estado en la BD |

**Decisión:** **OPTIMISTIC LOCKING** (versión en fila `plazas_version`).  
**Motivo:** El pico es predecible (lunes 8:00) y el volumen es una ráfaga. Pessimistic convierte la ráfaga en serialización: 5.000 usuarios llegan casi a la vez, 4.999 quedan bloqueados en el lock, su conexión se abre durante 30+ segundos, el pool se agota, todos ven timeout. Optimistic deja que la ráfaga ocurra en paralelo; parte de ella falla con 409 (correcto, hay menos plazas que usuarios), y cada usuario reintenta atomicamente. Esto consume menos conexiones de BD y menos latencia para quienes **sí** consiguen plaza. [**Caja 04 · Databases**]  
**Trade-off:** Clientes deben interpretar 409 (conflicto) como "reintenta" y ser idempotentes. La BD debe estar optimizada para estos reintentos.  
**Qué me haría cambiar:** Si el requisito fuera "una y solo una confirmación por usuario sin que vea error nunca", recurriría a pessimistic + queue (aceptar latencia para garantía de UX).

---

### **D2: Isolation level — Read Committed vs Repeatable Read**

**Contexto:** Postgres por defecto es Read Committed; MySQL por defecto es Repeatable Read. En este problema, dos transacciones concurrentes pueden leer "hay plazas" y luego ambas escribir, causando write skew.

| Aspecto | Read Committed (Postgres default) | Repeatable Read (MySQL default) |
|---|---|---|
| **Write skew** | Posible: dos transacciones leen mismo estado, escriben en filas distintas, juntas rompen invariante | Posible: snapshot isolation evita phantoms clásicos pero no write skew |
| **En plazas_libres** | Transacción A lee 1 plaza libre, T.B lee 1 plaza libre, ambas insertan reserva → stock negativo (problema) | Igual (write skew no se previene) |
| **Solución práctica** | Usar `SELECT ... FOR UPDATE` o versión + optimistic locking | Igual: necesitas constraint o versión |
| **Velocidad** | Rápido (lee commits globales sin snapshot) | Algo más lento (mantiene snapshot) |

**Decisión:** **Read Committed + Optimistic Locking con versión** en Postgres.  
**Motivo:** El `UNIQUE` sobre (`clase_id`, `usuario_id`) previene duplicados por usuario; la columna `version` previene write skew global. Read Committed es el default de Postgres y es suficiente con estas guardrails. [**Caja 04**]  
**Trade-off:** Asumo que el motor es Postgres; si es MySQL, documentar que Repeatable Read sigue permitiendo write skew.  
**Qué me haría cambiar:** Si apareciera inconsistencia en producción, escalar a Serializable (pero medirlo primero).

---

### **D3: Manejo de pico — Queue + Load shedding vs Escalado horizontal directo**

**Contexto:** Lunes 8:00, 5.000+ usuarios intentan reservar simultáneamente. Si no asoto la BD, puedo recibir todos; si los recibo todos, el pool de conexiones se satura.

| Aspecto | Queue-based | Horizontal escalado directo |
|---|---|---|
| **Flujo** | Cliente → LB → API → Queue → Workers → BD | Cliente → LB → API instancias → BD |
| **En pico** | API acepta 10 RPS que puede procesar; rechaza el resto con 429 Retry-After | API lanza todo al pool; pool se agota; timeouts para todos |
| **Load shedding** | Explícito: "vuelve en 2s" (cliente sabe qué hacer) | Implícito: timeout 30s (cliente frustrado, reintentos ciegos) |
| **BD throughput** | Controlado (p.ej., 100 reservas/s); nunca sobrecargada | Incontrolado; congestión y deadlocks |
| **Latencia p50** | 100ms (para quien es aceptado) | 500ms+ (todo el mundo espera) |
| **Coste infra** | Fijo (workers dimensionados para pico) | Variable (o sobreprovisionado o insuficiente) |

**Decisión:** **Queue + Load shedding (429 Retry-After)**.  
**Motivo:** El pico es **predecible** (lunes 8:00), lo que significa que puedo acotar workers y conexiones de BD. Una BD con 100 conexiones activas procesando 100 reservas/s es más rápida y más sana que una intentando procesar 5.000 transacciones concurrentes. El cliente móvil entiende 429: es lo que hace Spotify el día de Black Friday. [**Cajas 09 · Performance + 03 · APIs**]  
**Trade-off:** Requiero una cola (Redis o Kafka) y workers explícitos. La latencia p50 es determinista pero no es cero.  
**Qué me haría cambiar:** Si los usuarios exigieran garantía de procesamiento en <1s, cambiaría a escalado horizontal (aceptaría mayor coste infra).

---

### **D4: Fuente de verdad de plazas — BD única vs Cache L1**

**Contexto:** Listar clases disponibles es 90% del tráfico; reservar es 10%. En pico, todos preguntan por la misma clase (p.ej., "yoga lunes 8:00").

| Aspecto | BD única | Cache (Redis) eventual |
|---|---|---|
| **Lectura de plazas** | Query a BD cada vez | Query a Redis (1ms); consulta BD en background |
| **Consistencia** | Fuerte: si reservo ahora, el siguiente lee lo correcto | Eventual: lag de 100-500ms; el usuario ve "2 plazas" pero quedan 0 |
| **En pico** | 5.000 queries/s a BD → satura o se degradan | 5.000 queries/s a Redis → <1ms; BD recibe 100 escrituras/s |
| **Thundering herd** | N/A | Si la clave expira, 5.000 clientes hacen query a BD a la vez |

**Decisión:** **BD única para plazas (consistencia fuerte); Redis cache-aside para listados de clases (eventual OK)**.  
**Motivo:** Las plazas son inventario y tienen que ser fuertes. Los listados de clases (horarios, instrctor) no cambian varias veces por segundo, así que cache eventual es segura. La separación es clara: fuente de verdad = BD, acelerador = cache. [**Cajas 04 + 09 · Performance**]  
**Trade-off:** Una query más en el happy path (check en BD después de cache); pero para los datos dinámicos (plazas_libres en tiempo real) es correcto.  
**Qué me haría cambiar:** Si la latencia de 2 queries fuera crítica, usaría BD + materialized view y refresco cada 10s (eventual, pero controlado).

---

### **D5: Idempotencia — Almacenar fingerprint + deduplicación vs Nada**

**Contexto:** Cliente reintenta una reserva (timeout, 409, conectividad caída). Si no me protejo, inserto dos reservas. Si sí, devuelvo la primera.

| Aspecto | Deduplicación (fingerprint) | Sin deduplicación |
|---|---|---|
| **Cómo** | Cliente envía `idempotency_key` (UUID generado); app almacena hash de (user_id, clase_id, key) | App confía en que cliente solo intenta una vez |
| **Reintento** | Cliente reintenta con mismo key → app devuelve resultado anterior | Cliente reintenta → BD rechaza con `UNIQUE(user_id, clase_id)` |
| **UX** | Transparente: cliente reintenta, obtiene reserva sin error | Cliente reintenta, ve 409 o error → confusión |
| **Storage** | Tabla extra `dedup_keys` con TTL 24h | N/A |

**Decisión:** **Deduplicación via `idempotency_key`**.  
**Motivo:** Cumple con requisito de API robusta (Caja 03) y es el patrón de pago/reservas en la industria. La tabla de dedup es pequeña (1 clave por intento fallido + reintentos) y la query es rápida (hash). El beneficio es que el cliente **nunca ve un error por reintento**: si falló, reintenta con el mismo key y obtiene el resultado anterior. [**Cajas 03 · APIs + 08 · Distributed Systems**]  
**Trade-off:** Complejidad (+1 tabla, +1 query, TTL); pero es <100 líneas de código.  
**Qué me haría cambiar:** Si la escala de clientes fuera masiva (10M usuarios), evaluaría usar una BD en caché (Redis) en lugar de tabla SQL para las dedup_keys.

---

### **D6: Notificación de confirmación — Async outbox vs Sync dentro de transacción**

**Contexto:** Al hacer reserva, debo:  
1. Insertar fila en BD  
2. Enviar SMS/email de confirmación  

Si hago (2) dentro de la transacción y falla, aborto la reserva. Si hago (2) fuera y falla, la reserva existe pero el usuario no se entera.

| Aspecto | Outbox pattern (async) | Sync dentro de transacción |
|---|---|---|
| **Seguridad** | Reserva confirmada en BD; notificación enviada por worker. Si falla SMS, BD tiene log y puedo reintentar. | SMS enviado dentro de transacción; si falla, se revierte todo |
| **Latencia de respuesta** | API responde en 10ms; SMS se envía en background | API espera a SMS (1-3s) → 2-3s para usuario |
| **Fallos** | SMS falla: usuario tiene reserva, espera; worker reintenta en 1 min | SMS falla: usuario ve error; duda si reservó o no |
| **Deadlock risk** | Ninguno: transacción corta (solo BD) | Alto: transacción abierta mientras se llama a SMS |

**Decisión:** **Async outbox pattern**.  
**Motivo:** La confirmación de reserva es **contrato** con el usuario, así que debe estar en BD antes de responder. El SMS es un nice-to-have. El outbox pattern (Caja 08 · Distributed Systems) garantiza que si la reserva está en BD, la notificación se enviará (eventualmente). Responder rápido al usuario es mejor UX que esperar al SMS.  
**Trade-off:** Requiero una cola y workers; el usuario ve confirmación antes que el SMS (pero es correcto).  
**Qué me haría cambiar:** Si el SMS fuese **crítico** para la operación (p.ej., verifica 2FA), entonces estaría dentro de la transacción (pero pagaría latencia).

---

## ARQUITECTURA GLOBAL EN UNA LÍNEA

**Monolito modular (Python/Node/Go) con transacciones cortas en Postgres (optimistic locking), queue + workers para reservas (backpressure explícita con 429), Redis para cache de listados, deduplicación por `idempotency_key`, outbox async para notificaciones.**

══════════════════════════════════════════════════════════════════════
4 · Diseñar
══════════════════════════════════════════════════════════════════════
  🔧 buscar_en_docs({'query': 'optimistic locking versión base de datos implementación'})
  🔧 buscar_en_docs({'query': 'outbox pattern evento transacción asincronía garantías'})
  🔧 buscar_en_docs({'query': 'idempotency key API deduplicación fingerprint'})
Perfecto. Ya tengo el contexto. Ahora aplico las decisiones al diseño concreto.

---

## FASE 4 · ARQUITECTURA DETALLADA

### API

| Endpoint | Método | Función | Status OK | Status Error |
|---|---|---|---|---|
| `/user/login` | POST | Autenticar usuario móvil | 200 + JWT | 401 |
| `/gyms` | GET | Listar 200 gimnasios + info | 200 | 429 si pico |
| `/gyms/{gym_id}/classes` | GET | Listar clases del gimnasio (horarios, plazas libres) | 200 | 404, 429 |
| `/gyms/{gym_id}/classes/{class_id}` | GET | Detalle de 1 clase + plazas (cached eventual, <500ms lag) | 200 | 404 |
| `/reservations` | POST | **Crear reserva atómicamente** | 201 + `{reservation_id}` | 409, 429 |
| `/reservations/{res_id}` | GET | Obtener reserva del usuario | 200 | 404 |
| `/reservations/{res_id}` | DELETE | Cancelar reserva (libera plaza) | 204 | 404 |

**Cabeceras clave:**

| Cabecera | Dirección | Propósito |
|---|---|---|
| `Authorization: Bearer {jwt}` | → | Token del usuario (sub=user_id, tenant_id=gym_id o empty) |
| `Idempotency-Key` | → | UUID generado por cliente para deduplicación en POST/DELETE [Caja 03] |
| `X-Trace-Id` | → | Para tracing distribuido (correlacionar logs) [Caja 12] |
| `Retry-After` | ← | Segundos de espera si recibe 429 [Caja 03] |
| `X-RateLimit-Remaining` | ← | Cuotas disponibles del usuario |
| `ETag` / `Cache-Control` | ← | Para GET listados (cache eventual OK) |

**Detalles de POST `/reservations`:**

```
Entrada:
{
  "gym_id": "gym_123",
  "class_id": "class_456",
  "idempotency_key": "uuid-v4" // OBLIGATORIO
}

Salida 201:
{
  "reservation_id": "res_789",
  "gym_id": "gym_123",
  "class_id": "class_456",
  "user_id": "usr_001",
  "status": "confirmed",
  "created_at": "2025-01-13T08:05:12Z"
}

Errores:
409 Conflict: { "code": "NO_SPOTS_AVAILABLE", "message": "No hay plazas. Reintenta." }
429 Too Many Requests: { "Retry-After": "2" }
400 Bad Request: { "code": "INVALID_CLASS", "message": "Clase no existe o no está disponible" }
```

**Semántica:**
- POST es **NO idempotente por defecto**, pero con `Idempotency-Key` se vuelve idempotente [Caja 02, 07].
- Cliente siempre genera `Idempotency-Key` (UUID v4). Si la red falla, reintenta con la misma clave.
- App devuelve `409` si la clase está llena, **no** `400`. Es una decisión de negocio, no un input inválido [Caja 03].
- La respuesta es inmediata (<100ms) gracias a optimistic locking (sin locks bloqueadores).

---

### Datos

**Tablas clave:**

#### `gyms`
```sql
CREATE TABLE gyms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  location TEXT,
  phone TEXT,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  deleted_at TIMESTAMP NULL -- soft delete
);
CREATE INDEX idx_gyms_deleted ON gyms(deleted_at);
```

#### `classes`
```sql
CREATE TABLE classes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id),
  name TEXT NOT NULL,              -- "Yoga", "Spinning", etc.
  instructor TEXT,
  schedule_start TIMESTAMP NOT NULL, -- cuando comienza la clase
  schedule_end TIMESTAMP NOT NULL,
  max_spots INT NOT NULL CHECK (max_spots > 0),
  plazas_libres INT NOT NULL CHECK (plazas_libres >= 0 AND plazas_libres <= max_spots),
  plazas_version BIGINT NOT NULL DEFAULT 1, -- [OPTIMISTIC LOCKING] [Caja 04]
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  deleted_at TIMESTAMP NULL
);

-- ÍNDICES CRÍTICOS: los queries en pico están aquí
CREATE INDEX idx_classes_gym_deleted ON classes(gym_id, deleted_at);
CREATE INDEX idx_classes_schedule ON classes(schedule_start, gym_id);
-- Para buscar "clases disponibles en un rango de horario"
CREATE INDEX idx_classes_available ON classes(gym_id, schedule_start)
  WHERE deleted_at IS NULL AND schedule_start > now();
```

#### `reservations`
```sql
CREATE TABLE reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,           -- usuario autenticado
  class_id UUID NOT NULL REFERENCES classes(id),
  gym_id UUID NOT NULL REFERENCES gyms(id), -- desnormalizado para queries
  status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
    DEFAULT 'confirmed',
  reservation_version BIGINT NOT NULL DEFAULT 1, -- para cancelación idempotente
  created_at TIMESTAMP DEFAULT now(),
  cancelled_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE(class_id, user_id, status)  -- un usuario no puede reservar 2x la misma clase confirmada
);

CREATE INDEX idx_reservations_user ON reservations(user_id, status, created_at DESC);
CREATE INDEX idx_reservations_class ON reservations(class_id, status);
-- Para encontrar rápido si el usuario ya tiene reserva en esta clase
CREATE INDEX idx_reservations_unique_user_class 
  ON reservations(class_id, user_id) WHERE status = 'confirmed';
```

#### `idempotency_requests` (Deduplicación)
```sql
CREATE TABLE idempotency_requests (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  idempotency_key TEXT NOT NULL,
  method TEXT NOT NULL,             -- 'POST' o 'DELETE'
  endpoint TEXT NOT NULL,           -- '/reservations' o '/reservations/{id}'
  request_hash BYTEA NOT NULL,      -- SHA256(request body) para variantes
  response_json JSONB NOT NULL,     -- respuesta anterior (si ya procesamos)
  response_status INT,              -- 201, 204, 409, etc.
  created_at TIMESTAMP DEFAULT now(),
  expires_at TIMESTAMP DEFAULT now() + INTERVAL '24 hours', -- TTL
  PRIMARY KEY (user_id, idempotency_key, method),
  UNIQUE (user_id, idempotency_key)
);

CREATE INDEX idx_idempotency_expires ON idempotency_requests(expires_at);
-- Limpiar diariamente: DELETE FROM idempotency_requests WHERE expires_at < now()
```

#### `outbox` (Eventos para notificaciones)
```sql
CREATE TABLE outbox (
  id BIGSERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,         -- 'reservation.created', 'reservation.cancelled'
  event_version INT NOT NULL DEFAULT 1, -- versionado de esquema [Caja 08]
  aggregate_id UUID NOT NULL,       -- reservations.id
  aggregate_type TEXT NOT NULL,     -- 'Reservation'
  payload JSONB NOT NULL,
  metadata JSONB,                   -- tenant_id, user_id, trace_id
  created_at TIMESTAMP DEFAULT now(),
  published_at TIMESTAMP NULL,      -- NULL mientras no se publique
  retry_count INT DEFAULT 0,
  last_error TEXT NULL,
  PRIMARY KEY (id)
);

CREATE INDEX idx_outbox_unpublished 
  ON outbox(created_at) WHERE published_at IS NULL;
CREATE INDEX idx_outbox_created ON outbox(created_at DESC);
-- El relay lee: SELECT * FROM outbox WHERE published_at IS NULL ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED;
```

#### `audit_log` (Trazabilidad GDPR)
```sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  action TEXT NOT NULL,             -- 'reservation_created', 'reservation_cancelled'
  resource_id UUID,
  resource_type TEXT,               -- 'Reservation'
  changes JSONB,                    -- antes/después
  actor_ip TEXT,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (id)
);

CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);
```

---

### Asincronia

**Matriz: qué sale del request y quién lo procesa**

| Evento | Trigger | Cola | Job | Garantía | Dedup |
|---|---|---|---|---|---|
| **Reserva creada** | `POST /reservations` OK (201) | Outbox local | Relay + SMS worker | At-least-once | Event ID |
| **Reserva cancelada** | `DELETE /reservations/{id}` OK (204) | Outbox local | Relay + SMS worker | At-least-once | Event ID |
| **Notificación enviada** | Consumidor recibe evento | N/A (confirmación síncrona) | SMS/Email provider | At-least-once | Message ID |

**Flujo de POST `/reservations` (happy path):**

```
Cliente                     API                    BD Postgres            Outbox Relay         SMS API
  |                          |                        |                       |                  |
  |--- POST /reservations ---|>                      |                       |                  |
  |  (idempotency_key=X)      |                       |                       |                  |
  |                          BEGIN TRANSACTION       |                       |                  |
  |                          |--- INSERT dedup ----->|                       |                  |
  |                          |    (si existe,        |                       |                  |
  |                          |     devuelve cached)  |                       |                  |
  |                          |                       |                       |                  |
  |                          |--- SELECT ... FOR------|>                     |                  |
  |                          |    UPDATE NOWAIT       |                      |                  |
  |                          |    (bloquea fila)      |                      |                  |
  |                          |                       |                      |                  |
  |                          |--- UPDATE classes ---|->|[optimistic]         |                  |
  |                          |    WHERE version=V    | |plazas_libres -= 1   |                  |
  |                          |    AND plazas...>0    | |version += 1         |                  |
  |                          |    RETURNING *        | |                     |                  |
  |                          |                       |                      |                  |
  |                          |[0 filas UPDATE]       |                      |                  |
  |                          |--- ROLLBACK -----------|                      |                  |
  |                          |<--- 409 --------------|                      |                  |
  |<--- 409 Conflict --------|                       |                      |                  |
  |    {retry after 2s}      |                       |                      |                  |
  |                          |                       |                      |                  |
  [Cliente espera 2s, reintenta con mismo key]      |                      |                  |
  |                          |                       |                      |                  |
  |--- POST /reservations ---|>                      |                       |                  |
  |  (idempotency_key=X)      |                       |                       |                  |
  |                          |--- SELECT dedup ------|>  [existe, status OK]|                  |
  |                          |<--- cached response ---|                      |                  |
  |                          |    201 + res_id       |                       |                  |
  |<--- 201 Created ---------|                       |                       |                  |
  |    {reservation_id}      |                       |                       |                  |
  |                          |                       |                       |                  |
  |                          |[Background: Relay lea outbox]                 |                  |
  |                          |    pub.published_at=null          |           |                  |
  |                          |    ---------->|       |---------->|           |                  |
  |                          |               |       |    INSERT outbox     |                  |
  |                          |               |       |    event_type='res.created'
  |                          |               |       |           |
  |                          |               |       |           |---[async]----->|SMS: "Tu reserva"
  |                          |               |       |           |                 |
  |                          |               |       |<-- ack ---|                 |
  |                          |               |       |                           |
```

**Estructura del evento (Outbox):**

```json
{
  "id": "evt_789abcdef",         // generado por BD, PK de dedup
  "event_type": "reservation.created",
  "event_version": 1,
  "aggregate_id": "res_123",
  "aggregate_type": "Reservation",
  "payload": {
    "reservation_id": "res_123",
    "user_id": "usr_001",
    "class_id": "class_456",
    "gym_id": "gym_123",
    "class_name": "Yoga Vinyasa",
    "class_start": "2025-01-13T10:00:00Z",
    "status": "confirmed"
  },
  "metadata": {
    "tenant_id": "gym_123",
    "user_email": "user@example.com",
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
  },
  "created_at": "2025-01-13T08:05:12Z",
  "published_at": null
}
```

**Relay (worker que publica outbox):**

Pseudo-código:
```python
async def relay_outbox():
    """Cron cada 2s. Lee outbox no publicados, publica, marca."""
    while True:
        events = await db.query("""
            SELECT * FROM outbox
            WHERE published_at IS NULL
            ORDER BY created_at ASC
            LIMIT 100
            FOR UPDATE SKIP LOCKED
        """)
        
        for evt in events:
            try:
                # Publicar a broker (Redis + Pub/Sub o Kafka)
                await broker.publish(evt['event_type'], evt)
                
                # Marcar como publicado
                await db.execute(
                    "UPDATE outbox SET published_at=now() WHERE id=$1",
                    evt['id']
                )
            except Exception as e:
                # Reintentar: exp backoff, max 5 reintentos
                await db.execute(
                    "UPDATE outbox SET retry_count=retry_count+1, last_error=$1 WHERE id=$2",
                    str(e), evt['id']
                )
                if evt['retry_count'] >= 5:
                    await alert("Outbox stuck:", evt['id'])  # alerta manual
        
        await asyncio.sleep(2)
```

**Consumer (SMS worker):**

```python
async def handle_reservation_created(event: dict):
    """Suscriptor a 'reservation.created'."""
    # At-least-once: puede llegar dos veces
    msg_id = f"sms:{event['id']}:{event['payload']['user_id']}"
    
    # Inbox pattern: dedup en la misma transacción
    if await db.query("SELECT 1 FROM sms_sent WHERE message_id=$1", msg_id):
        return  # ya lo enviamos
    
    async with db.transaction():
        # Enviar SMS
        sms_resp = await sms_provider.send(
            to=event['metadata']['user_phone'],
            body=f"Reserva confirmada: {event['payload']['class_name']} "
                 f"a las {event['payload']['class_start']}",
            idempotency_key=msg_id  # la mayoría de SMS APIs lo soportan
        )
        
        # Registrar envío (dedup para la próxima)
        await db.execute(
            "INSERT INTO sms_sent(message_id, event_id, provider_id, sent_at) "
            "VALUES($1, $2, $3, now())",
            msg_id, event['id'], sms_resp['id']
        )
```

---

### Seguridad

[**Caja 06 · Security**]

#### Autenticación

```
POST /user/login
{
  "email": "user@example.com",
  "password": "xxx",
  "gym_id": "gym_123"  // opcional: si no está, la app deja elegir
}

Response 200:
{
  "access_token": "eyJhbGc...",  // JWT
  "expires_in": 3600,            // 1 hora
  "refresh_token": "ref_xxx",    // opcionalmente, para renovar
  "user_id": "usr_001",
  "gym_id": "gym_123"
}
```

**JWT payload (HS256 o RS256):**
```json
{
  "sub": "usr_001",
  "gym_id": "gym_123",
  "email": "user@example.com",
  "iat": 1673625912,
  "exp": 1673629512,
  "iss": "gym-reservations",
  "aud": "mobile-app"
}
```

**Middleware de validación:**
- Verificar firma (clave secreta en env).
- Verificar `exp` (no expirado).
- Extraer `sub` (user_id) y `gym_id` para guardar en contexto de request.

#### Autorización (por objeto)

| Recurso | Regla |
|---|---|
| `GET /gyms` | Público (sin autenticación) |
| `GET /gyms/{gym_id}/classes` | Público |
| `POST /reservations` para clase en `gym_id` | Requiere JWT; el `gym_id` del JWT debe coincidir |
| `GET /reservations/{res_id}` | Requiere JWT; `reservations.user_id == JWT.sub` |
| `DELETE /reservations/{res_id}` | Requiere JWT; `reservations.user_id == JWT.sub` |

**Pseudocódigo de autorización:**
```python
def require_auth(f):
    @wraps(f)
    async def wrapper(request):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return 401, {"code": "TOKEN_EXPIRED"}
        except jwt.InvalidSignatureError:
            return 401, {"code": "INVALID_TOKEN"}
        
        request.user_id = payload['sub']
        request.gym_id = payload['gym_id']
        return await f(request)
    return wrapper

def check_reservation_ownership(res_id: str, user_id: str):
    """Verificar que user_id es el propietario de la reserva."""
    res = db.query("SELECT user_id FROM reservations WHERE id=$1", res_id)
    if not res or res.user_id != user_id:
        raise ForbiddenError("No eres el propietario")
```

#### Rate limiting por usuario
[**Caja 03 · APIs**]

```
Global: 100 req/s por IP (protección contra ataques DDoS)
Por usuario autenticado:
  - 10 GET /reservations por segundo
  - 1 POST /reservations por segundo (anti-spam)
  - 5 reservas por día (límite de negocio: nadie reserva >5 clases/día)

Implementación: Redis + token bucket
```

**Pseudocódigo:**
```python
async def rate_limit_by_user(user_id: str, action: str) -> bool:
    """True si permitido, False si bloqueado."""
    key = f"rl:{user_id}:{action}"
    limit = RATE_LIMITS.get(action, {})  # p.ej., {"per_sec": 1, "per_day": 5}
    
    # Check per-second
    current = await redis.incr(key + ":sec")
    if current == 1:
        await redis.expire(key + ":sec", 1)  # reset cada segundo
    if current > limit['per_sec']:
        return False  # 429
    
    # Check per-day
    current_day = await redis.incr(key + ":day")
    if current_day == 1:
        await redis.expire(key + ":day", 86400)  # reset cada día
    if current_day > limit.get('per_day', float('inf')):
        return False  # 429
    
    return True
```

#### Aislamiento multi-tenant

Cada usuario pertenece a un gimnasio (`gym_id` en JWT). Las queries deben filtrar siempre por `gym_id`:

```sql
-- ❌ MALO: el usuario ve clases de TODOS los gimnasios
SELECT * FROM classes WHERE class_id=$1;

-- ✅ BUENO: solo ve su gimnasio
SELECT * FROM classes WHERE id=$1 AND gym_id=$2;

-- ✅ BUENO: ver reservas del usuario solo de su gimnasio
SELECT * FROM reservations 
WHERE user_id=$1 AND gym_id=$2 AND status='confirmed';
```

#### Privacidad y GDPR

- **No guardar contraseñas:** usar bcrypt con salt (salt factor 12).
- **Encriptación en tránsito:** HTTPS siempre (TLS 1.2+).
- **Encriptación en reposo:** tokens de refresh cifrados en BD (AES-256 en nivel de campo).
- **Derecho al olvido:** endpoint para borrar datos del usuario (soft delete en audit).
- **Logs:** nunca guardar tokens, contraseñas, emails en texto plano.

---

### Fiabilidad

[**Cajas 10 · Reliability + 12 · Observability**]

#### Timeouts y Reintentos

| Componente | Timeout | Reintentos | Backoff |
|---|---|---|---|
| **API → BD (query)** | 5s | 0 (inmediato fallo) | N/A |
| **API → SMS provider** | 10s | 3 veces | Exp: 1s, 2s, 4s |
| **Relay → Broker (publish)** | 5s | 5 veces | Exp: 100ms, 500ms, 1s, 2s, 4s |
| **Client → API (HTTP)** | 30s | 3 veces (solo GET, HEAD, DELETE) | Exp + jitter |

**Pseudocódigo de reintentos con jitter:**
```python
async def retry_with_backoff(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(fn(), timeout=10)
        except asyncio.TimeoutError as e:
            if attempt == max_retries - 1:
                raise
            delay = (2 ** attempt) + random.uniform(0, 1)  # exp + jitter
            await asyncio.sleep(delay)
        except Exception as e:
            raise  # no reintentar otros errores
```

#### Circuit Breaker (dependencias externas)

```
Estados:
- CLOSED (normal): 0% de fallos, deja pasar
- OPEN (fallando): >50% de fallos en última ventana, rechaza inmediato con 503
- HALF_OPEN (recuperando): deja pasar 1 request de prueba

Parámetros:
- failure_threshold: 50% de fallos en las últimas 100 requests
- success_threshold: 5 éxitos seguidos para cerrarse
- timeout: 30s en OPEN antes de intentar HALF_OPEN
```

**Dónde aplicar:**
- SMS provider: si falla, envía a DLQ (dead letter queue) para reintento manual.
- Cache (Redis): si cae, caemos a BD (más lento pero funciona).
- Autenticación externa: si está suscrito a un IdP, fallar abierto (permitir con token viejo si existe).

#### Degradación graceful

```python
async def get_classes(gym_id: str, cached=True):
    """Listar clases. Si cache falla, vamos a BD."""
    if cached:
        try:
            return await redis.get(f"classes:{gym_id}") or []
        except redis.ConnectionError:
            logger.warning("Redis down, fallback to DB")
    
    # Fallback
    return await db.query("SELECT * FROM classes WHERE gym_id=$1", gym_id)

# En el endpoint:
@app.get("/gyms/{gym_id}/classes")
async def list_classes(gym_id: str):
    if circuit_breaker.is_open():
        return 503, {"code": "SERVICE_DEGRADED", "message": "Listando sin cache"}
    return await get_classes(gym_id)
```

#### Cascadas de fallo

**Problema:** API saturada → agota workers → connection pool lleno → queries cuelgan → API cuelga más.

**Solución:** load shedding explícito (rechazar con 429 antes de que el sistema se colapse).

```python
async def middleware_load_shed(request):
    """Si la BD está saturada, rechaza proactivamente."""
    active_connections = await db.pool.status()['active']
    max_connections = 100
    
    if active_connections > max_connections * 0.8:  # 80% threshold
        return 429, {
            "code": "LOAD_SHEDDING",
            "message": "Sistema saturado. Reintenta en 5s.",
            "retry_after": 5
        }
    
    return await app(request)
```

#### Métricas y Alertas

**Tablas de observabilidad:**

| Métrica | Objetivo | Umbral de alerta |
|---|---|---|
| **Latencia p50/p99 de POST /reservations** | <100ms / <500ms | p99 > 1s |
| **Tasa de 409 (Conflict) en pico** | 10-30% (normal en race) | >50% = problema |
| **Tasa de 429 (Rate limit)** | <1% en no-pico | >5% = sobrecarga real |
| **Lag de relay (outbox unpublished)** | <5s | >30s = relay muerto |
| **Errores en SMS provider** | <0.1% | >1% = proveedor caído |
| **Pool de conexiones disponible** | >20 | <5 = próximo timeout |
| **Duración de transacciones** | <50ms | >100ms = contención |

**Logs estructurados (JSON):**
```json
{
  "timestamp": "2025-01-13T08:05:12.345Z",
  "level": "INFO",
  "event": "reservation_created",
  "user_id": "usr_001",
  "reservation_id": "res_789",
  "class_id": "class_456",
  "gym_id": "gym_123",
  "duration_ms": 45,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "abc123def456"
}
```

**Alertas críticas (PagerDuty):**
- P99 latencia > 2s (indica congestión).
- Tasa de error > 5%.
- Lag de relay > 5 minutos.
- 3+ fallos SMS consecutivos en una hora.
- Menos del 10% de pool de conexiones disponible.

---

**FIN DE FASE 4**

Acabas de ver el esquema técnico concreto: tablas, índices, flujos, códigos de status, timeouts, dedup, eventos. Ninguno de estos es trivial; cada decisión evita un fallo específico. La **fase 5 te toca identificar qué puede salir mal** en cada uno.

══════════════════════════════════════════════════════════════════════
5 · Validar
══════════════════════════════════════════════════════════════════════
  🔧 buscar_fallos({'tema': 'Optimistic locking en Postgres: write skew, race conditions, conflictos en pico'})
  🔧 buscar_fallos({'tema': 'Outbox pattern: relay stuck, eventos duplicados, lag acumulativo'})
  🔧 buscar_fallos({'tema': 'Queue + load shedding con 429: cómo fallan los reintentos del cliente, thundering herd'})
  🔧 buscar_fallos({'tema': 'Connection pooling en Postgres: agotamiento, deadlocks, transacciones largas'})
  🔧 buscar_fallos({'tema': 'Deduplicación por idempotency_key: TTL expira antes de que el cliente reintente, colisiones de hash'})
  🔧 buscar_fallos({'tema': 'JWT y autorización por tenant: token hijacking, lateral movement entre gimnasios'})
Tengo material abundante. Ahora voy a sintetizar solo los **fallos concretos de ESTE diseño específico** (no genéricos), sus síntomas y mitigaciones.

---

## QUÉ PUEDE SALIR MAL

| Fallo | Dónde | Síntoma | Mitigación en el Diseño |
|---|---|---|---|
| **Write skew en optimistic locking bajo pico** | `POST /reservations` | Dos usuarios leen `version=1`, ambos leen `plazas_libres>0`, ambos hacen UPDATE: uno gana, otro ve 409. Si hay >1 plaza pero el stock sube (cancelaciones), race condition de lectura desactualizada. | El UPDATE condicional por versión lo atrapa (correcto). **Pero:** si el pico es tan alto que los 409 abruman al cliente, el retry pool explota. Mitigación: el `Retry-After` debe ser exponencial + jitter; monitorizar % de 409. |
| **Pool agotado por transacciones colgadas** | Relay (outbox) | Relay intenta publicar a broker lento; transacción abierta esperando respuesta; una conexión muere esperando. Pool desciende en espiral. | El diseño usa conexión corta (`FOR UPDATE SKIP LOCKED` sin esperar). **Pero:** si el broker (Redis/Kafka) está caído, `publish()` tarda timeout (5s). La transacción se cuelga. Mitigación: timeout en el publish **dentro** de la transacción; si falla, reintenta en siguiente ciclo (la fila queda no publicada). |
| **Outbox lag crece sin alertar** | Relay (worker) | Relay funciona pero está 3 horas atrasado; usuarios piensan que su SMS fallo. El lag no genera error, solo demora. | El diseño no tiene métrica de antigüedad del evento no publicado. Mitigación: alerta por `max(outbox.created_at - now()) > 5 min WHERE published_at IS NULL`. |
| **Thundering herd en dedup keys** | Deduplicación | Si 1.000 usuarios reintenta con el mismo `idempotency_key` (no es imposible si es determinístico en el cliente), la tabla de dedup recibe 1.000 queries al mismo `(user_id, key)`. Contención. | El diseño usa índice `UNIQUE(user_id, idempotency_key)` que serializa. Mitigación: acceptable porque la query es rápida (PK lookup); si es un problema, pasar dedup a Redis con TTL. |
| **TTL de dedup expira antes de reintento** | Deduplicación | Cliente reintenta después de 25 horas; la fila de dedup se borró (TTL 24h). Reintento crea segunda reserva. | Mitigación: TTL debe ser mayor que el timeout máximo del cliente (p.ej., 7 días). Documentar en el cliente. **Pero:** esto requiere que la app conozca la duración de los reintentos del cliente. Si no se coordina, es un problema. |
| **JWT hijacking por falta de estado de sesión** | Autenticación | Token expedido; usuario cambia contraseña; el viejo token sigue siendo válido hasta que expira (1 hora). | El diseño acepta esto (no hay revocación de JWT). Mitigación: usar refresh tokens con TTL muy corto (15 min) y acortar exp (15 min); o mantener una blacklist de tokens revocados (consulta más en cada request). El trade-off es latencia. **Recomendación:** si es crítico, refactor a sesiones en Redis. |
| **Lateral movement entre gimnasios** | Autorización | Usuario en `gym_id=123` manipula JWT para cambiar a `gym_id=456`. Si el middleware valida pero la query no filtra, ve datos de otro gimnasio. | El diseño **requiere** que todo endpoint filtre por JWT.gym_id. **Pero:** es fácil olvidarlo. Mitigación: hacer la verificación a nivel de repositorio (scope automático), no a nivel de endpoint. Si se olvida un endpoint, el scope lo detecta. |
| **IDOR en GET /reservations/{res_id}** | Autorización | Usuario A adivina el UUID de la reserva de usuario B y lo recupera. | El diseño requiere `WHERE reservations.user_id = JWT.sub`. Mitigación: implementar como *[Caja 06]* requiere: test obligatorio `test_el_usuario_a_no_puede_leer_lo_del_usuario_b()`. |
| **Deadlock en update simultáneo** | BD | Dos transacciones actualizan `classes` y `reservations` en orden distinto → circular wait. | Postgres lo detecta y aborta una. El diseño requiere reintentar en la app. Mitigación: transacciones ultra-cortas (el UPDATE de optimistic locking es rápido) reduce probabilidad. Pero puede pasar. Implementar retry automático en la app. |
| **Disco lleno de outbox** | Outbox table | Si el relay está muerto y no se limpia, `outbox` crece indefinidamente → disk 100% → BD no puede escribir → cascada. | El diseño no tiene limpieza (archivado). Mitigación: job periódico que archive eventos publicados hace >30 días a una tabla `outbox_archive`, o borra si no importa la auditoría. |
| **429 rate limit demasiado agresivo en pico** | Load shedding | Sistema rechaza el 70% de requests en las 8:00 del lunes; usuarios ven "servidor saturado". | El diseño es correcto en principio (backpressure es mejor que timeout). **Pero:** no hay tuning. Mitigación: medir `p99(latencia cuando no hacemos load shedding)` en stage/prod, ajustar el threshold dinámicamente. Si la BD puede procesar 1.000 req/s, deja que pasen 1.000, rechaza el resto. |
| **Client retries ciegos sin backoff** | APIs + Reliability | Cliente móvil recibe 429, reintenta inmediatamente; 5.000 clientes reintentando creando retry storm. | El diseño incluye `Retry-After` en la respuesta 429. Mitigación: **educación del cliente**: obligar a respetar Retry-After en el SDK. Si no lo hace, el retry storm explota el pico aún más. |
| **Idempotencia del DELETE no garantizada** | DELETE /reservations/{res_id} | Usuario cancela; timeout; reintenta con mismo idempotency_key; la app la busca en dedup_keys pero no existe (TTL expiró). Crea segundo DELETE. | Mitigación: la tabla `reservations` tiene `status` ('confirmed', 'cancelled'). El UNIQUE es sobre `(class_id, user_id, status)`. Un segundo DELETE intenta cambiar de 'cancelled' a 'cancelled' → no cambia nada (seguro). Pero el usuario recibe error. Mejor: guardar el resultado anterior en dedup_keys (respuesta) para devolverlo. |
| **Write skew en cancelación simultánea** | DELETE /reservations (dos clientes) | Usuario tiene 1 reserva. Dos clientes (app web + móvil con sesión duplicada) intentan cancelar. Ambos leen `status='confirmed'`, ambos hacen UPDATE. | El UPDATE es condicional por `status`. Primera transacción lo cambia a 'cancelled'; segunda ve 0 filas y falla (correcto, es 409 o `NOT_FOUND`). Mitigación: aceptable. |
| **Constraint violation por datos stale** | Autorización | Usuario borra la clase antes de que alguien confirme la reserva (race condition de negocio). El INSERT de reserva falla con FK violation. | El diseño debe manejar esto en la app. Mitigación: devolver 400 o 404 al usuario (la clase ya no existe). Traducir FK violation a error de negocio. |

---

## QUÉ NO CUBRE

| Límite | Por qué es un límite | Punto de rediseño |
|---|---|---|
| **Créditos/prepago** | El diseño no previene sobreventa a nivel de usuario (un usuario intenta reservar 100 clases en 1 segundo). Solo previene sobreventa de una clase. | Si el requisito es "máx 5 reservas por usuario por día", hay que agregar `UPDATE users SET reserved_today = reserved_today + 1 WHERE id=$1 AND reserved_today < 5`. Eso es otra transacción atómica. El pico sigue siendo resoluble, pero sumamos contención. |
| **Cancelaciones con ventana de reembolso** | El diseño permite cancelar siempre. Si hay política "solo devuelves dinero si cancelas >24h antes", la lógica de negocio va en la app, no en la BD. | Riesgo: olvidar la ventana y dejar cancelaciones fuera de política. Mitigación: constraint o check en la app + audit trail. |
| **Waitlist** | Si una clase está llena, el diseño rechaza con 409. No hay cola de espera. | Si el requisito es "dejame en lista de espera y avísame si se cancela", rediseñar: tabla `waitlist` con triggers en `reservations.status = 'cancelled'` para promover el primero. Eso es complejo y lento. |
| **Sobreventa real (overbooking)** | El diseño **no** permite sobreventa. Si hay 30 plazas y 35 usuarios al mismo tiempo ven "hay plaza", algunos verán 409. | Si el requisito es "aceptar hasta un 5% más (overbooking)" para cubrir cancelaciones, agregar lógica: `plazas_libres < 0 OR plazas_libres <= max_spots * 1.05`. Viola la invariante "no sobrevender", pero a nivel de negocio es aceptable. |
| **Multi-gimnasio en una transacción** | El diseño asume 1 reserva = 1 clase. No hay "compra de pase de 10 clases" atómicamente. | Si es requisito, las transacciones se vuelven más largas y el pico es más complejo. El optimistic locking sigue funcionando, pero hay más retries por write skew. |
| **Cancelaciones automáticas si no asistes** | El diseño no marca "asistencia". Sin eso, no hay auto-cancelación. | Si es requisito, necesita: check-in en la clase, job que después de 2h sin check-in cancela automáticamente. Eso complica el dominio. |
| **Datos de histórico + GDPR** | El diseño tiene `audit_log` pero no hay plan de expiración (derecho al olvido). | Si es requisito cumplir GDPR, hay que: permitir borrado de datos personales del usuario (soft delete en usuario + refrencias en cascada). El audit log debe poder anonimizarse. |
| **Escalabilidad horizontal de escritura (sharding)** | El diseño es monolito con una sola BD. Si escala más allá de 10K reservas/s, necesitas sharding (por gym_id, user_id, etc.). | Punto de rediseño: partir la tabla `reservations` por `hash(class_id) mod N` shards. Mucho más complejo. Pero el pico de lunes 8:00 de 200 gimnasios probablemente no llega ahí. |
| **Notificaciones en tiempo real** | El SMS/email es async outbox + worker. Si se requiere WebSocket para notificación real-time ("tu reserva está confirmada"), agregar broker en memoria (p.ej., Redis Pub/Sub) al que se suscriba la app móvil. | El outbox patrón sigue funcionando; solo agregamos un publisher a Redis además del SMS worker. |

---

## VEREDICTO

**¿Está listo para construirse?** **SÍ, con 4 pre-checklist antes de ir a producción.**

**Resolverías antes:**

1. **Monitorización de alertas críticas:** outbox lag, pool exhausto, % de 409, latencia p99 > 1s. Sin estas, descubrirás fallos en vivo. [**Caja 12**]
2. **Tests de fallo y concurrencia:** test de "usuario A no ve a usuario B" (IDOR), test de "reintento con mismo idempotency_key no duplica", test de "429 respeta Retry-After", test de "deadlock se reintenta sin error al usuario". [**Caja 11**]
3. **Plan de rollback BD:** `plazas_version` y esquema de dedup requieren migraciones. Ensayar rollback sin perder datos. [**Cajas 04 + 14**]
4. **Política de rate limit tuneada en staging:** Medir latencia real del pico simulado (5K usuarios simultáneos a lunes 8:00) y ajustar el threshold de 429 antes de producción. [**Cajas 09 + 12**]

**Lo que te haría repensar:** Si en testing de carga el p99 de latencia es >2s o el % de 409 es >60%, regresar a D1 y considerar pessimistic locking + queue explícita (acepta latencia pero garantiza menos 409). Hoy el trade-off es optimistic, pero la métrica te dirá.
