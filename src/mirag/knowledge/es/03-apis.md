# 03 · APIs

> Una API es un contrato con gente que no puedes llamar por teléfono. Todo el diseño gira alrededor de
> una idea: **una vez que alguien depende de ti, romper el contrato es caro.**


**Cubre del temario:** `concepts` · `patterns` · `protocols` · `implementations` · `security` · `failure_modes` · `tradeoffs`

---

## API design: los principios que se notan

**1. Modela recursos, no acciones.** `POST /pedidos/123/cancelar` es más honesto que meterlo en un `PATCH`
genérico. El REST purista diría `PATCH /pedidos/123 {"estado":"cancelado"}`, pero las **acciones con efectos
de negocio** (cancelar, reembolsar, publicar) merecen su propio endpoint: son auditables, permisos distintos,
y el contrato es explícito. Ser pragmático aquí es señal de seniority, no de ignorancia.

**2. Consistencia por encima de elegancia.** `snake_case` o `camelCase`, da igual cuál — pero **el mismo en
toda la API**. Fechas siempre ISO-8601 en UTC (`2026-09-14T22:31:00Z`). IDs siempre strings (un entero se
desborda en JavaScript a partir de 2^53). Plurales siempre en las colecciones.

**3. El principio de menor sorpresa.** Si `GET /pedidos` devuelve `{"data": [...]}`, que `GET /usuarios`
no devuelva un array pelado.

**4. Diseña para el cliente, no para tu esquema de base de datos.** Exponer tus tablas tal cual acopla tu
API a tu modelo interno y te impide refactorizar nunca más.

**5. Nunca rompas sin avisar.** Lo que **no** es breaking: añadir un campo opcional en la respuesta, añadir
un endpoint, añadir un valor de enum *si el cliente lo trata como desconocido*. Lo que **sí** es breaking:
quitar o renombrar un campo, cambiar un tipo, hacer obligatorio un parámetro, cambiar el significado de algo,
cambiar códigos de error.

> **Ficha** · **Cuándo:** antes de escribir el primer endpoint ·
> **Patrón:** recursos para el CRUD, endpoints de acción explícitos para operaciones de negocio ·
> **Anti-patrón:** exponer tus tablas tal cual — te impide refactorizar la base de datos nunca más ·
> **Límites:** una vez publicada, la API es un contrato que no controlas cuándo se deja de usar ·
> **Cómo falla:** IDs numéricos grandes se corrompen en JavaScript (por encima de 2^53) ·
> **Decisión:** consistencia > elegancia; el mismo estilo en toda la API aunque no sea el ideal ·
> **Trade-off:** pureza REST vs claridad para el consumidor ·
> **Relacionado:** versioning, error contracts, OpenAPI `[02]`

---

## Versioning

| Estrategia | Ejemplo | Pros | Contras |
|---|---|---|---|
| En la URL | `/v1/pedidos` | obvio, cacheable, fácil de enrutar | "no es REST puro", duplica rutas |
| En header | `Accept: application/vnd.api.v2+json` | URLs limpias | invisible, difícil de probar en navegador |
| Por fecha | `Stripe-Version: 2026-08-01` | granular, sin saltos grandes | complejo de mantener |
| Sin versión | evolución aditiva | sin duplicar nada | te obliga a no romper jamás |

**La respuesta práctica: `/v1` en la URL** para cambios grandes, y **evolución aditiva** dentro de v1 para
todo lo demás. Es lo que hace casi todo el mundo porque es lo que se entiende sin documentación.

**El modelo de Stripe** (versión por fecha fijada por cuenta, con capa de transformación que convierte la
respuesta moderna al formato antiguo) es el estado del arte, pero exige mantener *shims* de traducción
durante años. Mencionarlo en una entrevista demuestra que conoces el problema de verdad.

**Política de deprecación seria:** anuncias → devuelves headers `Deprecation` y `Sunset` → mides quién sigue
usando la versión vieja (por client ID, no por adivinanza) → avisas directamente a esos clientes → apagas.
Nunca apagues algo que no puedas medir.

> **Ficha** · **Cuándo:** desde el día uno, aunque solo tengas v1 ·
> **Patrón:** `/v1` para cambios estructurales + evolución aditiva dentro de la versión ·
> **Anti-patrón:** apagar una versión sin poder medir quién la usa ·
> **Límites:** cada versión viva multiplica el coste de mantenimiento y de pruebas ·
> **Cómo falla:** añadir un valor de enum rompe a clientes que hacen `switch` exhaustivo ·
> **Decisión:** ¿es breaking? Quitar/renombrar campo, cambiar tipo, hacer obligatorio un parámetro, sí ·
> **Trade-off:** libertad para evolucionar vs estabilidad para los consumidores ·
> **Relacionado:** deprecación, contract testing `[11]`

---

## Pagination

**Offset / page (`?page=3&limit=20` → `LIMIT 20 OFFSET 40`)**
- ✅ Simple, permite saltar a una página concreta, muestra total de páginas.
- ❌ **Se degrada brutalmente**: `OFFSET 100000` obliga a la DB a leer y descartar 100.000 filas.
- ❌ **Inconsistente**: si se inserta una fila mientras paginas, ves elementos repetidos o te saltas otros.

**Cursor / keyset (`?after=eyJpZCI6MTIzfQ`)**
```sql
-- en vez de OFFSET, filtras por la posición del último visto
SELECT * FROM pedidos
WHERE (creado_en, id) < ($1, $2)     -- tupla para desempatar
ORDER BY creado_en DESC, id DESC
LIMIT 20;
```
- ✅ **Rendimiento constante** sin importar la profundidad (usa el índice directamente).
- ✅ Estable ante inserciones.
- ❌ No puedes saltar a "la página 50" ni mostrar el total fácilmente.

**La regla:** cursor por defecto para feeds, listados grandes y APIs públicas. Offset solo para back-offices
con pocos datos donde el usuario quiere ver "página 7 de 12".

**Detalles que delatan experiencia:** el cursor debe ser **opaco** (base64 de un JSON, no el ID en claro)
para poder cambiar la implementación; el orden debe ser **total** (añade el `id` como desempate o verás
duplicados); y devuelve siempre `has_more` en vez de obligar al cliente a pedir una página vacía.

> **Ficha** · **Cuándo:** toda colección que pueda crecer ·
> **Patrón:** keyset/cursor con orden total `(creado_en, id)` y cursor opaco en base64 ·
> **Anti-patrón:** `OFFSET 100000` — la DB lee y descarta 100.000 filas ·
> **Límites:** con cursor no puedes saltar a "la página 50" ni dar el total barato ·
> **Cómo falla:** sin desempate por `id` ves elementos duplicados o te saltas otros al insertar ·
> **Decisión:** feeds y APIs públicas → cursor; back-office pequeño → offset ·
> **Trade-off:** navegabilidad (offset) vs rendimiento constante (cursor) ·
> **Relacionado:** índices, query optimization `[04]`

---

## Filtering, sorting, searching

```
GET /pedidos?estado=pagado&creado_desde=2026-01-01&sort=-creado_en&fields=id,total
```

- **Allowlist obligatoria** de campos filtrables y ordenables. Permitir `sort` arbitrario es invitar a un
  full scan sobre una columna sin índice — es un DoS trivial.
- **Sintaxis:** `-campo` para descendente es el convenio más legible. Para operadores, `precio[gte]=100` o
  `filter[precio][gte]=100`. No inventes un mini-lenguaje de query salvo que tengas un motivo muy bueno.
- **Sparse fieldsets** (`?fields=`) reducen payload; útil en móvil.
- **Cada filtro que expones es un índice que te comprometes a mantener.** Piénsalo antes de añadirlo.

> **Ficha** · **Cuándo:** al exponer listados ·
> **Patrón:** allowlist de campos filtrables y ordenables ·
> **Anti-patrón:** permitir `sort` arbitrario: full scan sobre una columna sin índice = DoS trivial ·
> **Límites:** cada filtro que expones es un índice que te comprometes a mantener ·
> **Cómo falla:** un cliente ordena por una columna sin índice y satura la base de datos ·
> **Decisión:** si necesitas búsqueda de texto real, índice invertido aparte, no `LIKE '%x%'` ·
> **Trade-off:** flexibilidad para el cliente vs previsibilidad del rendimiento ·
> **Relacionado:** índices, full-text search `[04]`

---

## Validation

**Valida en el borde, confía dentro.** Un único punto de validación a la entrada (schema) y a partir de ahí
el dominio trabaja con tipos ya válidos.

- **Declarativa con schema**: Pydantic (Python), Zod (TS), JSON Schema. Genera documentación y errores
  consistentes gratis.
- **Niveles:** sintáctica (¿es un email?) → semántica (¿ese `producto_id` existe?) → de negocio (¿hay stock?).
  Los tres devuelven códigos distintos: 400 / 422 / 409.
- **Allowlist, no denylist.** Rechaza campos desconocidos (`additionalProperties: false`) o al menos ignóralos
  explícitamente; nunca los pases al ORM directamente — eso es **mass assignment** y es como alguien se hace
  administrador mandando `{"rol":"admin"}`.
- **Límites en todo:** longitud de strings, tamaño de arrays, profundidad del JSON, tamaño del body. Sin
  límites, un JSON anidado 10.000 niveles te tumba el parser.

> **Ficha** · **Cuándo:** en el borde, antes de tocar el dominio ·
> **Patrón:** schema declarativo (Pydantic/Zod) que rechaza campos desconocidos ·
> **Anti-patrón:** **mass assignment** — pasar el body al ORM directamente (`{"rol":"admin"}`) ·
> **Límites:** la validación sintáctica no sustituye a las invariantes de negocio ni a los constraints de la DB ·
> **Cómo falla:** sin límites de tamaño y profundidad, un JSON anidado tumba el parser ·
> **Decisión:** 400 sintáctico · 422 semántico · 409 conflicto de estado ·
> **Trade-off:** estricto (rompe clientes tolerantes) vs permisivo (bugs silenciosos) ·
> **Relacionado:** error contracts, business rules `[17]`

---

## Serialization

- **JSON** es el default. Trampas: no tiene tipo fecha (usa strings ISO), los enteros grandes se rompen en
  JS (manda IDs como string), y `NaN`/`Infinity` no son válidos.
- **Protobuf / Avro**: binario, compacto, con schema y evolución controlada. Para servicio-a-servicio y colas.
- **MessagePack / CBOR**: JSON binario, sin schema. Poco ganas frente a JSON+gzip.
- **Regla de oro:** nunca serialices tu entidad de dominio directamente. Un DTO explícito evita filtrar
  `password_hash` el día que alguien añade ese campo al modelo. **Esta fuga es de las más comunes que existen.**

> **Ficha** · **Cuándo:** en cada respuesta ·
> **Patrón:** DTO explícito por endpoint, nunca la entidad de dominio ·
> **Anti-patrón:** serializar el modelo del ORM — el día que alguien añade `password_hash`, lo filtras ·
> **Límites:** JSON no tiene tipo fecha ni enteros grandes seguros ·
> **Cómo falla:** fuga de campos sensibles al añadir una columna, sin que ningún test lo note ·
> **Decisión:** binario (Protobuf) entre servicios; JSON de cara al mundo ·
> **Trade-off:** mantener DTOs es trabajo repetitivo y es lo que evita la fuga ·
> **Relacionado:** DTOs, gRPC `[02, 05]`

---

## Error contracts

Un contrato de errores bueno es lo que diferencia una API usable de una que odias. Usa **RFC 9457**
(*Problem Details for HTTP APIs*, la actualización de la RFC 7807):

```json
{
  "type": "https://api.tuapp.com/errors/saldo-insuficiente",
  "title": "Saldo insuficiente",
  "status": 409,
  "detail": "La cuenta 42 tiene 30.00 EUR y la operación requiere 50.00 EUR",
  "instance": "/cuentas/42/transferencias",
  "request_id": "req_01J8XZ...",
  "errors": [
    {"campo": "importe", "codigo": "max_excedido", "mensaje": "Máximo 30.00"}
  ]
}
```

**Reglas:**
- **Un código de error estable y machine-readable** (`saldo-insuficiente`), porque el `mensaje` humano
  cambiará y los clientes acabarán parseando strings si no les das otra cosa.
- **Devuelve todos los errores de validación a la vez**, no el primero. El cliente no puede hacer 8 viajes.
- **Incluye el `request_id`** para que el usuario te lo pegue en el ticket y tú lo busques en los logs.
- **Nunca filtres internals**: stack traces, queries SQL, rutas de archivos o nombres de tablas en la
  respuesta son una fuga de información.

> **Ficha** · **Cuándo:** en el primer endpoint, no cuando ya hay veinte ·
> **Patrón:** RFC 9457 con código estable machine-readable + `request_id` ·
> **Anti-patrón:** devolver stack traces, SQL o rutas de archivo en la respuesta ·
> **Límites:** los mensajes humanos cambian; solo el código es contrato ·
> **Cómo falla:** sin código estable, los clientes parsean strings y rompes al traducir el mensaje ·
> **Decisión:** devuelve **todos** los errores de validación a la vez, no el primero ·
> **Trade-off:** detalle útil para el cliente vs no filtrar información interna ·
> **Relacionado:** códigos de estado, correlation IDs `[02, 12]`

---

## OpenAPI / Swagger

- **Contract-first vs code-first.** Contract-first (escribes el YAML, generas servidor y clientes) da mejor
  diseño y permite trabajar en paralelo con el frontend. Code-first (anotas el código, se genera el spec)
  es más rápido y **no se desincroniza**, que es el fallo mortal del contract-first mal mantenido.
- **Lo que ganas con un spec real:** SDKs generados, mocks para el frontend, tests de contrato,
  documentación viva, y validación de request/response en el gateway.
- **La prueba de fuego:** si tu OpenAPI no está generado o validado en CI, está desactualizado. Un spec que
  miente es peor que no tener spec.

> **Ficha** · **Cuándo:** cualquier API con más de un consumidor ·
> **Patrón:** el spec se genera o se valida **en CI**; si no, miente ·
> **Anti-patrón:** un YAML escrito a mano que nadie actualiza — peor que no tener spec ·
> **Límites:** el spec describe forma, no semántica ni reglas de negocio ·
> **Cómo falla:** el frontend implementa contra un spec desactualizado y falla en integración ·
> **Decisión:** contract-first si hay equipos en paralelo; code-first si el riesgo es la desincronización ·
> **Trade-off:** diseño cuidado (contract-first) vs veracidad garantizada (code-first) ·
> **Relacionado:** contract testing, SDKs `[11]`

---

## Idempotency

El mecanismo que hace que los reintentos sean seguros. **Obligatorio en cualquier endpoint que mueva dinero
o cree recursos.**

```
POST /pagos
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

**Implementación correcta:**
1. El **cliente** genera la clave (UUID) y la reutiliza en todos los reintentos de *esa misma intención*.
2. El servidor intenta insertar la clave en una tabla con `UNIQUE`, **dentro de la misma transacción** que
   la operación de negocio.
3. Si la clave ya existe y la operación terminó → devuelve **la respuesta guardada**, con el mismo status.
4. Si existe pero está en curso → `409` o `425`, para que el cliente reintente más tarde.
5. Guarda también un hash del body: si llega la misma clave con un body distinto, es un bug del cliente →
   `422`. No ejecutes nada.
6. Dale TTL (24h-7 días es lo habitual) y limpia.

**El error clásico:** guardar la clave *después* de ejecutar. Si el proceso muere en medio, has cobrado sin
registrar la clave y el reintento cobra otra vez. **Misma transacción o no sirve de nada.**

> **Ficha** · **Cuándo:** todo endpoint que mueva dinero o cree recursos ·
> **Patrón:** clave del cliente + `UNIQUE` **en la misma transacción** que la operación ·
> **Anti-patrón:** guardar la clave *después* de ejecutar — si el proceso muere, cobras dos veces ·
> **Límites:** la clave necesita TTL y limpieza; el almacén crece ·
> **Cómo falla:** un cliente que genera una clave nueva en cada reintento anula la protección ·
> **Decisión:** deriva la clave de la intención de negocio (`pedido_id`), no de un UUID nuevo ·
> **Trade-off:** una escritura extra por operación a cambio de que el reintento sea seguro ·
> **Relacionado:** retries, outbox, pagos `[07, 08]`

---

## Rate limiting

| Algoritmo | Cómo va | Trade-off |
|---|---|---|
| Fixed window | contador por minuto | simple; permite **doble ráfaga** en el borde de la ventana |
| Sliding window log | timestamps de cada request | exacto; caro en memoria |
| **Sliding window counter** | interpola dos ventanas | buena aproximación, barato — **el default sensato** |
| **Token bucket** | tokens que se rellenan a ritmo fijo | permite ráfagas controladas; el más usado en APIs |
| Leaky bucket | cola de salida a ritmo constante | suaviza el tráfico; añade latencia |

**Detalles de producción:**
- **¿Por qué limitas?** Por IP (anónimos), por API key o user (autenticados), por endpoint (los caros valen
  más), y por **coste** en el caso de GraphQL o LLMs (no todas las requests cuestan igual).
- **Distribuido:** el contador vive en Redis, no en memoria del proceso, o cada réplica permitirá el límite
  entero. `INCR` + `EXPIRE` en un script Lua para que sea atómico.
- **Comunícalo bien:** `429` + `Retry-After` + headers `RateLimit-Limit`, `RateLimit-Remaining`,
  `RateLimit-Reset` (RFC 9238 los estandariza).
- **Fail-open vs fail-closed:** si Redis se cae, ¿dejas pasar todo o bloqueas todo? Para rate limiting de
  abuso normalmente **fail-open** (prefieres servir de más que caerte); para límites de facturación o
  seguridad, fail-closed.

> **Ficha** · **Cuándo:** toda API pública, y las internas caras ·
> **Patrón:** token bucket en Redis (permite ráfagas) + headers `RateLimit-*` ·
> **Anti-patrón:** contador en memoria del proceso: cada réplica permite el límite entero ·
> **Límites:** el contador distribuido añade un round trip a Redis por petición ·
> **Cómo falla:** si Redis cae, decides entre dejar pasar todo (fail-open) o bloquear todo ·
> **Decisión:** abuso → fail-open; facturación o seguridad → fail-closed ·
> **Trade-off:** proteger el sistema vs cortar a clientes legítimos que crecieron ·
> **Relacionado:** backpressure, load shedding `[09]`

---

## API keys, gateways, webhooks y SDKs

**API keys**
- Formato con prefijo (`sk_live_...`, `pk_test_...`): permite detectar el tipo de un vistazo y que GitHub
  las detecte en secret scanning.
- **Guarda solo el hash** (como una contraseña). Enseña la clave completa una única vez.
- Scopes, rotación sin downtime (dos claves activas a la vez), y last_used_at para poder limpiar.

**API gateway** — lo que centralizas ahí: TLS, autenticación, rate limiting, routing, versionado, CORS,
logging/tracing, transformación, y caching. **Cuidado con el anti-patrón:** meter lógica de negocio en el
gateway lo convierte en un ESB y en un punto único de fallo que nadie quiere tocar.

**Webhooks (siendo tú el emisor)** — ver también `16-integrations.md`:
- **Firma HMAC** del body con un secreto compartido + **timestamp dentro de la firma** para evitar replay.
  El receptor compara con `hmac.compare_digest` (comparación en tiempo constante).
- **At-least-once**: incluye un `event_id` estable para que el receptor deduplique.
- **Reintentos con backoff exponencial** y dead-letter tras N fallos; un endpoint para reenviar manualmente.
- **Manda el evento, no solo el ID**, pero que el receptor pueda confirmar con un GET (los eventos pueden
  llegar desordenados, así que incluye una versión o timestamp del recurso).
- Timeout corto (5-10s): el receptor debe responder 200 rápido y procesar en background.

**SDKs** — si publicas API pública, genera los SDKs desde OpenAPI. Deben traer por defecto: retries con
backoff y jitter, timeouts, paginación automática (iteradores), errores tipados, e idempotency keys
automáticas en los POST.

> **Ficha** · **Cuándo:** al abrir la API a terceros ·
> **Patrón:** claves con prefijo (`sk_live_`), **guardadas hasheadas**, con scopes y rotación solapada ·
> **Anti-patrón:** meter lógica de negocio en el gateway: lo convierte en un ESB intocable ·
> **Límites:** los webhooks son at-least-once y llegan desordenados ·
> **Cómo falla:** firmar el body ya parseado en vez del crudo rompe la verificación del receptor ·
> **Decisión:** si el receptor debe reaccionar rápido, manda evento + permite confirmar con un GET ·
> **Trade-off:** webhooks (tiempo real, entrega incierta) vs polling (simple, con retraso) ·
> **Relacionado:** webhook signatures, integraciones `[06, 16]`

---

## Implementación: un endpoint completo de principio a fin

Todo lo anterior, junto, en el endpoint que más se pregunta: crear un recurso de forma idempotente.

```python
from pydantic import BaseModel, Field

class CrearPedido(BaseModel):                 # validation + serialization
    model_config = {"extra": "forbid"}        # rechaza campos desconocidos -> no mass assignment
    producto_id: str
    unidades: int = Field(gt=0, le=100)       # los limites, en el schema

class PedidoCreado(BaseModel):                # DTO de salida: nunca la entidad del ORM
    id: str
    estado: str
    total_centimos: int
    divisa: str

@router.post("/v1/pedidos", status_code=201, response_model=PedidoCreado)
async def crear_pedido(
    body: CrearPedido,
    idem: str = Header(alias="Idempotency-Key"),      # obligatoria: es una operacion que muta
    actor: Usuario = Depends(autenticar),
):
    autorizar(actor, "pedidos:crear")                  # authz explicita, por objeto

    async with uow.transaccion() as tx:                # idempotencia y efecto: MISMA transaccion
        existente = await tx.reservar_idempotencia(idem, hash_body(body), actor.tenant_id)
        if existente:
            return existente.respuesta                 # reintento: devuelve lo guardado

        pedido = await servicio.crear(actor, body)     # el dominio, sin saber de HTTP
        await tx.guardar_respuesta_idempotente(idem, pedido)
        return PedidoCreado.model_validate(pedido)
```

**Lo que hace bien, en orden:** valida con schema estricto → autentica → **autoriza sobre el objeto** →
abre una transacción → reserva la idempotencia y ejecuta **juntas** → devuelve un DTO explícito.
Los errores de negocio suben como excepciones tipadas y el middleware `[02]` las traduce a 409/422 con
el contrato de error.

> **Ficha** · **Cuándo:** plantilla para cualquier endpoint que cree o modifique ·
> **Patrón:** el handler orquesta (validar, autorizar, transaccionar); el dominio no conoce HTTP ·
> **Anti-patrón:** lógica de negocio dentro del controlador, o el ORM asomando en la respuesta ·
> **Límites:** la transacción debe ser corta — nada de llamadas HTTP externas dentro `[04]` ·
> **Cómo falla:** si la idempotencia se guarda fuera de la transacción, un crash duplica el efecto ·
> **Decisión:** `Idempotency-Key` obligatoria en POST que mutan dinero o inventario ·
> **Trade-off:** más ceremonia por endpoint a cambio de que los reintentos sean seguros ·
> **Relacionado:** idempotencia, autorización, unit of work `[04, 05, 06]`

---

## Cómo falla una API en producción

| Fallo | Causa | Mitigación |
|---|---|---|
| Recursos duplicados | el cliente reintentó un POST | `Idempotency-Key` |
| Datos de otro cliente | falta de filtro por tenant/owner (**IDOR**) | scoping en el repositorio `[06, 17]` |
| Petición lenta que no acaba | sin timeout en una dependencia | timeouts en cascada `[10]` |
| 500 al añadir un campo | el cliente no tolera campos desconocidos | evolución aditiva + clientes tolerantes |
| El cliente se queda colgado | respuesta enorme sin paginar | límite duro de `limit` |
| Rompes sin querer | cambio no declarado breaking | contract testing en CI `[11]` |
| Fuga de campos sensibles | serializar la entidad del ORM | DTOs explícitos |
| Abuso de un cliente | sin rate limiting por clave | token bucket + 429 con `Retry-After` |

> **Ficha** · **Cuándo:** revisión previa a exponer una API ·
> **Patrón:** cada fila de esta tabla debería tener un test que la cubra ·
> **Anti-patrón:** descubrir el IDOR por un informe de un cliente ·
> **Límites:** ningún contrato protege de un cambio semántico (mismo campo, otro significado) ·
> **Cómo falla:** los fallos silenciosos (fuga, IDOR) no generan errores: nadie se entera ·
> **Decisión:** los tests de autorización cruzada son obligatorios, no opcionales ·
> **Trade-off:** validación estricta rompe clientes descuidados y detecta bugs antes ·
> **Relacionado:** IDOR, contract testing, error contracts `[06, 11, 17]`

---

## Preguntas de entrevista y trade-offs

**Q: Diseña la paginación de un feed con millones de elementos.**
Cursor-based con keyset sobre un índice `(creado_en DESC, id DESC)`, cursor opaco en base64, `has_more` en la
respuesta. *Señal:* explicas por qué `OFFSET` se degrada (la DB lee y descarta) y por qué se producen
duplicados al insertar mientras paginas.

**Q: ¿Cómo garantizas que cobrar dos veces sea imposible si el cliente reintenta?**
Idempotency key generada por el cliente, insertada con `UNIQUE` **en la misma transacción** que el cobro, y
respuesta cacheada para los reintentos. *Señal:* mencionas el hash del body para detectar reuso incorrecto de
la clave, y que el orden importa (guardar antes de ejecutar, no después).

**Q: ¿Cómo versionas sin romper a nadie?**
`/v1` para cambios estructurales, evolución aditiva dentro de la versión, headers `Deprecation`/`Sunset`,
y **métricas de uso por cliente** antes de apagar nada. *Señal:* sabes distinguir qué cambios son breaking y
cuáles no, y mencionas que añadir un valor de enum rompe a clientes que hacen `switch` exhaustivo.

**Q: ¿REST o GraphQL para tu próxima API pública?**
REST, salvo que tengas clientes muy heterogéneos. *Señal:* argumentas con cacheabilidad HTTP, rate limiting
por request vs por coste, y el hecho de que GraphQL traslada complejidad del cliente al servidor (N+1,
límites de profundidad, persisted queries) que alguien tiene que operar.

**Q: Tu API pública empieza a recibir 50× tráfico de un cliente. ¿Qué haces?**
Rate limit por API key con token bucket en Redis, 429 con `Retry-After`, y un tier distinto si es un cliente
legítimo que creció. *Señal:* separas abuso de crecimiento, mencionas fail-open y que el límite debe ser
visible en headers para que el cliente pueda auto-regularse en vez de martillear.

**Trade-off central de esta caja:** *flexibilidad para el cliente vs poder operar y evolucionar la API*.
Cada capacidad que expones (filtros arbitrarios, queries anidadas, campos dinámicos) es una promesa de
rendimiento que tendrás que sostener con índices, límites y caches durante años.

---

## Fuentes

- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html) (sustituye a la RFC 7807)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Stripe API reference](https://docs.stripe.com/api) — el referente de idempotencia y versionado por fecha.
- [Google API Design Guide](https://cloud.google.com/apis/design) — convenciones de recursos y errores.
- [RFC 9238 — RateLimit header fields](https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-08.html)
