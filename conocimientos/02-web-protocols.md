# 02 · Web & Protocols

> Todo backend es, en el fondo, un programa que lee bytes de un socket y escribe otros bytes.
> Esta caja es la que más "se asume sabida" y la que más gente falla cuando se pregunta en detalle.

**Cubre del temario:** `concepts` · `protocols` · `headers` · `implementations` · `constraints`
· `failure_modes` · `tradeoffs`

---

## El viaje completo de una request

Cuando alguien escribe `https://api.tuapp.com/pedidos` pasa esto, en orden:

```
1. DNS      nombre -> IP          (~20-100ms si no está cacheado)
2. TCP      3-way handshake       (1 RTT)
3. TLS      handshake             (1 RTT en TLS 1.3, 2 en TLS 1.2)
4. HTTP     request + response    (1 RTT + tiempo de servidor)
```

**Consecuencia práctica:** una conexión nueva cuesta 3-4 round trips antes del primer byte útil. Por eso
existen keep-alive, connection pooling, HTTP/2 multiplexing y 0-RTT. Si tu backend abre una conexión TCP
nueva a la base de datos en cada request, estás pagando esto miles de veces por segundo.

> **Ficha** · **Cuándo:** al depurar latencia de primera conexión o diseñar para clientes lejanos ·
> **Patrón:** keep-alive y connection pooling para amortizar los 3-4 round trips ·
> **Anti-patrón:** abrir conexión nueva por request (a la DB o a una API interna) ·
> **Límites:** el handshake no se puede eliminar, solo reutilizar o acercar ·
> **Cómo falla:** DNS lento o cacheado mal, y certificados caducados que rompen el paso 3 ·
> **Decisión:** si el cliente está lejos, CDN; si el destino es interno, pool ·
> **Trade-off:** conexiones persistentes ahorran latencia y consumen file descriptors ·
> **Relacionado:** connection pooling, CDN, TLS `[01, 04, 09]`

---

## TCP/IP

- **3-way handshake:** SYN → SYN-ACK → ACK. Una ida y vuelta completa antes de mandar datos.
- **Control de flujo (flow control):** la ventana de recepción evita que el emisor ahogue al receptor.
- **Control de congestión:** slow start, congestion avoidance. Por eso una conexión nueva empieza lenta y
  acelera — y por eso las conexiones persistentes son más rápidas que las nuevas aunque el ancho de banda
  sea el mismo.
- **Head-of-line blocking:** TCP garantiza orden. Si se pierde el paquete 5, los paquetes 6-10 ya recibidos
  esperan en el buffer hasta que llegue la retransmisión del 5. **Este es el problema que QUIC resuelve.**
- **TIME_WAIT:** tras cerrar, el socket queda ~60s en ese estado. Un servidor que abre y cierra muchísimas
  conexiones salientes puede quedarse sin puertos efímeros. Se ve como "cannot assign requested address".

**Nagle's algorithm y `TCP_NODELAY`:** Nagle agrupa paquetes pequeños para no desperdiciar cabeceras, lo
que añade hasta 200ms de latencia. Casi todo servidor moderno activa `TCP_NODELAY` para desactivarlo.

> **Ficha** · **Cuándo:** al depurar conexiones colgadas, resets o agotamiento de puertos ·
> **Patrón:** `TCP_NODELAY` activado y conexiones reutilizadas ·
> **Anti-patrón:** abrir y cerrar miles de conexiones salientes por segundo ·
> **Límites:** ~28.000 puertos efímeros por IP de destino; `TIME_WAIT` de ~60s ·
> **Cómo falla:** "cannot assign requested address", y head-of-line blocking al perder un paquete ·
> **Decisión:** si necesitas orden estricto, TCP; si toleras pérdida y quieres latencia, UDP/QUIC ·
> **Trade-off:** fiabilidad (TCP) vs latencia bajo pérdida de paquetes (QUIC) ·
> **Relacionado:** HTTP/3, sockets, file descriptors `[01, 13]`

---

## DNS

- Jerárquico: root → TLD (`.com`) → autoritativo (`tuapp.com`).
- **Tipos de registro que debes conocer:** `A` (IPv4), `AAAA` (IPv6), `CNAME` (alias), `MX` (correo),
  `TXT` (verificación, SPF/DKIM), `NS` (delegación), `SRV` (servicio+puerto), `CAA` (qué CA puede emitir
  certificados para tu dominio).
- **TTL:** cuánto cachean los resolvers. **El TTL es tu tiempo de rollback.** Si tienes TTL de 24h y quieres
  mover el tráfico, tardarás 24h. Antes de una migración, baja el TTL a 60s con días de antelación.
- **DNS como load balancer:** round-robin DNS reparte pero no sabe si un nodo está caído, y los clientes
  cachean de forma impredecible. Sirve para geo-routing y failover lento, no para balanceo fino.
- **Trampa clásica:** las JVM antiguas cacheaban DNS para siempre (`networkaddress.cache.ttl=-1`). Si el
  proveedor cambia la IP del balanceador, tu app sigue yendo a la vieja. Ha tumbado a empresas enteras.

> **Ficha** · **Cuándo:** en cualquier migración, failover o cambio de proveedor ·
> **Patrón:** bajar el TTL a 60s **días antes** de una migración planificada ·
> **Anti-patrón:** cachear DNS para siempre en el cliente (la JVM antigua lo hacía) ·
> **Límites:** el TTL es tu tiempo mínimo de rollback; los resolvers no lo respetan todos igual ·
> **Cómo falla:** el proveedor cambia la IP del balanceador y tu app sigue yendo a la vieja ·
> **Decisión:** DNS sirve para geo-routing y failover lento, no para balanceo fino ·
> **Trade-off:** TTL alto = menos consultas y peor agilidad; bajo = más carga y más control ·
> **Relacionado:** load balancing, failover `[09, 10, 13]`

---

## TLS

- **Qué te da:** confidencialidad (cifrado), integridad (nadie lo alteró) y autenticidad (hablas con quien
  crees). **No te da** autorización ni protección contra un servidor comprometido.
- **Cómo funciona:** handshake asimétrico (caro) para acordar una clave de sesión simétrica (barata), y
  el resto de la conversación va con la simétrica.
- **TLS 1.3** (el estándar actual): 1-RTT de handshake, 0-RTT en reconexión, elimina cifrados legacy.
  Si alguien te dice que usa TLS 1.0/1.1 en 2026, eso es un hallazgo de auditoría.
- **Certificados y cadena de confianza:** tu cert está firmado por una CA intermedia, firmada por una raíz
  que el sistema operativo ya trae. **Error clásico de producción: servir el cert sin la cadena intermedia**
  — funciona en tu navegador (que la tiene cacheada) y falla en `curl` y en otros servidores.
- **mTLS (mutual TLS):** también el cliente presenta certificado. Es la base de zero-trust entre servicios
  y de los service meshes.
- **Terminación TLS:** normalmente termina en el load balancer / ingress, y dentro de la red va en claro o
  con mTLS. Importa saberlo porque **`X-Forwarded-Proto` y `X-Forwarded-For` son la única forma de que tu
  app sepa la IP y el esquema originales.**

> **Ficha** · **Cuándo:** siempre; también dentro de la VPC (mTLS) ·
> **Patrón:** TLS 1.3, cadena intermedia completa, y renovación automatizada ·
> **Anti-patrón:** servir el certificado sin la cadena intermedia (funciona en tu navegador, falla en `curl`) ·
> **Límites:** TLS no te da autorización ni te protege de un servidor comprometido ·
> **Cómo falla:** **certificado caducado** — una de las causas más frecuentes de caída total ·
> **Decisión:** termina TLS en el balanceador y usa mTLS hacia dentro si necesitas zero-trust ·
> **Trade-off:** terminar en el borde simplifica y te obliga a confiar en la red interna ·
> **Relacionado:** security headers, secrets, X-Forwarded-For `[06, 13, 14]`

---

## HTTP/1.1 · HTTP/2 · HTTP/3

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Transporte | TCP | TCP | **QUIC sobre UDP** |
| Formato | texto | binario (frames) | binario (frames) |
| Concurrencia | 1 request por conexión (pipelining roto) | **multiplexing** en una conexión | multiplexing sin HOL de TCP |
| Cabeceras | texto repetido | comprimidas (HPACK) | comprimidas (QPACK) |
| HOL blocking | sí, a nivel de aplicación | resuelto en app, **persiste en TCP** | resuelto de verdad |
| Server push | no | sí (deprecado en la práctica) | no |
| Handshake | TCP+TLS separados | TCP+TLS separados | **combinado, 0-RTT posible** |

**Lo importante para backend:**

- HTTP/1.1 necesitaba 6 conexiones paralelas por dominio y trucos como el *domain sharding*. HTTP/2 los hace
  contraproducentes.
- **HTTP/2 sobre una sola conexión TCP:** si se pierde un paquete, *todos* los streams multiplexados esperan.
  Por eso en redes móviles malas HTTP/3 gana tanto.
- **gRPC va sobre HTTP/2** — por eso necesita soporte de HTTP/2 extremo a extremo, y por eso los balanceadores
  L7 antiguos lo rompen.
- HTTP/3 lo terminan normalmente el CDN o el load balancer; tu servidor de aplicación casi siempre habla
  HTTP/1.1 o HTTP/2 por detrás.

> **Ficha** · **Cuándo:** al elegir protocolo entre servicios o al optimizar clientes móviles ·
> **Patrón:** HTTP/2 o /3 en el borde, HTTP/1.1 o /2 hacia dentro ·
> **Anti-patrón:** domain sharding con HTTP/2 (contraproducente: rompe el multiplexado) ·
> **Límites:** HTTP/2 sigue sobre una conexión TCP, así que hereda su head-of-line blocking ·
> **Cómo falla:** balanceadores L7 antiguos rompen gRPC porque no hablan HTTP/2 extremo a extremo ·
> **Decisión:** gRPC entre servicios, REST hacia fuera ·
> **Trade-off:** eficiencia binaria vs depurabilidad con herramientas de texto ·
> **Relacionado:** gRPC, load balancing `[03, 09]`

---

## Métodos, semántica e idempotencia

| Método | Seguro (no muta) | Idempotente | Cacheable | Uso |
|---|---|---|---|---|
| GET | ✅ | ✅ | ✅ | leer |
| HEAD | ✅ | ✅ | ✅ | metadatos sin cuerpo |
| POST | ❌ | **❌** | raramente | crear, acciones |
| PUT | ❌ | ✅ | ❌ | reemplazar completo |
| PATCH | ❌ | **❌** (salvo que lo diseñes así) | ❌ | modificar parcial |
| DELETE | ❌ | ✅ | ❌ | borrar |
| OPTIONS | ✅ | ✅ | ❌ | preflight CORS |

**Idempotente = repetir la llamada da el mismo estado final**, no la misma respuesta. Un `DELETE` repetido
devuelve 404 la segunda vez pero el estado final es idéntico: sigue siendo idempotente.

**Por qué importa muchísimo:** los clientes y proxies reintentan automáticamente los métodos idempotentes.
`POST` no se reintenta solo, y por eso necesitas **idempotency keys** (ver `03-apis.md` y `07-payments.md`).

> **Ficha** · **Cuándo:** al diseñar cualquier endpoint que el cliente pueda reintentar ·
> **Patrón:** métodos idempotentes por diseño; `Idempotency-Key` para los que no lo son ·
> **Anti-patrón:** un `GET` que muta estado (lo ejecutan los prefetchers y los crawlers) ·
> **Límites:** idempotente = mismo **estado final**, no misma respuesta ·
> **Cómo falla:** un proxy reintenta tu POST y cobras dos veces ·
> **Decisión:** POST/PATCH necesitan clave de idempotencia explícita ·
> **Trade-off:** pureza REST vs endpoints de acción explícitos y auditables ·
> **Relacionado:** idempotency keys, retries `[03, 07, 08]`

---

## Códigos de estado que un senior usa bien

- **200 OK** / **201 Created** (con header `Location`) / **202 Accepted** (procesamiento asíncrono aceptado,
  aún no hecho) / **204 No Content**.
- **301 vs 308** y **302 vs 307:** los nuevos (307/308) **preservan el método**. Un 301 sobre un POST puede
  convertirlo en GET. Usa 308/307 si no quieres sorpresas.
- **304 Not Modified:** respuesta a un condicional con `ETag`/`If-None-Match`. Ahorra ancho de banda.
- **400** malformado · **401** no autenticado (*quién eres*) · **403** autenticado pero sin permiso
  (*qué puedes*) · **404** no existe · **409** conflicto de estado · **410** se fue para siempre ·
  **422** sintaxis válida pero semánticamente inválido · **429** rate limited (**con `Retry-After`**).
- **500** error nuestro · **502** el upstream respondió basura · **503** no disponible / sobrecargado
  (**con `Retry-After`**) · **504** timeout del upstream.

**Señal de seniority:** distinguir 401 de 403, usar 409 para conflictos de concurrencia optimista, devolver
`Retry-After` en 429/503, y **no devolver 200 con `{"error": ...}` dentro**. Esto último rompe todos los
retries automáticos, los circuit breakers y las métricas de tu propio stack.

> **Ficha** · **Cuándo:** en cada respuesta; es el contrato que leen máquinas ·
> **Patrón:** 429 y 503 **siempre** con `Retry-After`; 409 para conflictos de concurrencia ·
> **Anti-patrón:** devolver 200 con `{"error": ...}` dentro — rompe retries, breakers y métricas ·
> **Límites:** el código es un canal estrecho: necesita un cuerpo de error estructurado ·
> **Cómo falla:** clientes que reintentan un 400 eternamente porque no distinguen permanente de transitorio ·
> **Decisión:** 401 = no sé quién eres; 403 = sé quién eres y no puedes ·
> **Trade-off:** granularidad de códigos vs simplicidad para el consumidor ·
> **Relacionado:** error contracts, circuit breakers `[03, 10]`

---

## Headers que importan

**De request:** `Authorization`, `Content-Type`, `Accept`, `Accept-Encoding`, `If-None-Match`,
`Idempotency-Key`, `User-Agent`, `X-Request-Id` (correlación, ver `12-observability.md`),
`X-Forwarded-For` / `Forwarded`.

**De response:** `Content-Type`, `Cache-Control`, `ETag`, `Location`, `Retry-After`, `Set-Cookie`,
`Content-Encoding`, `Vary`, y los de seguridad (`06-security.md`).

**`Vary` es el header que todo el mundo olvida.** Le dice a la cache "esta respuesta depende de tal header".
Si sirves contenido distinto según `Accept-Language` o `Authorization` y no pones `Vary`, el CDN servirá la
respuesta de un usuario a otro. **Es una fuga de datos, no solo un bug de cache.**

> **Ficha** · **Cuándo:** en toda respuesta cacheable o que dependa del usuario ·
> **Patrón:** `Vary` declarado siempre que la respuesta dependa de un header ·
> **Anti-patrón:** contenido por usuario cacheable sin `Vary: Authorization` ·
> **Límites:** tamaño máximo de headers (~8-16 KB en la mayoría de servidores) ·
> **Cómo falla:** **el CDN sirve la respuesta de un usuario a otro** — es fuga de datos, no solo un bug ·
> **Decisión:** si varía por usuario, `Cache-Control: private` o no cachear ·
> **Trade-off:** cacheabilidad vs personalización ·
> **Relacionado:** cache HTTP, CDN `[09]`

---

## Cache HTTP

```
Cache-Control: public, max-age=3600, stale-while-revalidate=86400
Cache-Control: private, no-cache            # revalida siempre, pero puede guardar
Cache-Control: no-store                     # no guardar nunca (datos sensibles)
```

- `max-age` (fresco) · `s-maxage` (solo para caches compartidas/CDN) · `must-revalidate`.
- **`no-cache` ≠ `no-store`.** `no-cache` significa "guárdalo pero pregúntame antes de usarlo";
  `no-store` es "ni lo escribas". Confundirlos es error de junior.
- **Validación condicional:** `ETag` + `If-None-Match` (o `Last-Modified` + `If-Modified-Since`) → 304.
- **`stale-while-revalidate`:** sirve lo viejo mientras refresca por detrás. Latencia de cache hit con datos
  casi frescos. Muy usado en CDN.

> **Ficha** · **Cuándo:** en todo lo que se lee mucho más de lo que se escribe ·
> **Patrón:** `ETag` + `If-None-Match` para revalidar barato; `stale-while-revalidate` en el borde ·
> **Anti-patrón:** confundir `no-cache` (guarda pero revalida) con `no-store` (no guardar nunca) ·
> **Límites:** invalidar lo ya repartido es imposible: solo puedes esperar al TTL o purgar por tag ·
> **Cómo falla:** un `max-age` largo en un recurso que cambió deja usuarios con datos viejos días ·
> **Decisión:** datos sensibles → `no-store`; estáticos versionados → `max-age` enorme ·
> **Trade-off:** frescura vs latencia y coste de origen ·
> **Relacionado:** CDN, caching, invalidación `[09]`

---

## REST vs GraphQL vs gRPC vs WebSockets vs SSE

| | REST | GraphQL | gRPC | WebSocket | SSE |
|---|---|---|---|---|---|
| Transporte | HTTP | HTTP (1 endpoint) | HTTP/2 | TCP (upgrade) | HTTP |
| Formato | JSON | JSON | Protobuf (binario) | lo que quieras | texto |
| Dirección | req/res | req/res | req/res + streaming | **bidireccional** | **servidor → cliente** |
| Cache HTTP | ✅ nativa | ❌ difícil (todo POST) | ❌ | ❌ | parcial |
| Tipado | OpenAPI (opcional) | **schema obligatorio** | **contrato .proto** | ninguno | ninguno |
| Uso típico | APIs públicas, CRUD | frontends con muchas vistas | **entre microservicios** | chat, colaboración, juegos | notificaciones, tokens de LLM, progreso |

**REST** gana en simplicidad, cacheabilidad y herramientas. Su problema real es over-fetching/under-fetching
y la explosión de endpoints a medida.

**GraphQL** te da al cliente exactamente lo que pide. Precios que pagas: el **problema N+1** (se resuelve con
DataLoader/batching), la dificultad de cachear, el rate limiting por *coste de query* en vez de por request,
y que una query maliciosamente anidada puede tumbarte (necesitas depth/complexity limits y persisted queries).

**gRPC** es lo estándar **service-to-service**: contrato fuerte, binario, rápido, streaming nativo, codegen
en todos los lenguajes. No lo uses de cara al navegador (necesitas grpc-web y un proxy).

**WebSocket vs SSE** es la comparación que más cae:
- SSE va sobre HTTP normal, reconecta solo (con `Last-Event-ID`), atraviesa proxies sin problema, y es
  **unidireccional**. Para streaming de tokens de un LLM, notificaciones o barras de progreso, SSE es
  más simple y suficiente.
- WebSocket es bidireccional y de baja latencia, pero es una conexión con estado: complica el balanceo
  (necesitas sticky sessions o un backplane tipo Redis pub/sub), los despliegues (todos se reconectan a la
  vez) y el escalado horizontal.

**Regla:** si el cliente solo escucha, SSE. Si el cliente habla constantemente, WebSocket.

> **Ficha** · **Cuándo:** al empezar una API o al añadir tiempo real ·
> **Patrón:** REST hacia fuera, gRPC hacia dentro, SSE para streaming unidireccional ·
> **Anti-patrón:** WebSocket para notificaciones que el cliente solo escucha ·
> **Límites:** GraphQL no se cachea con HTTP; WebSocket exige estado y sticky sessions ·
> **Cómo falla:** una query GraphQL anidada maliciosa tumba el servidor sin límites de profundidad ·
> **Decisión:** ¿el cliente solo escucha? SSE. ¿Habla constantemente? WebSocket ·
> **Trade-off:** flexibilidad del cliente vs coste operativo del servidor ·
> **Relacionado:** API design, rate limiting por coste `[03, 18]`

---

## CORS

El navegador bloquea por defecto las peticiones cross-origin desde JS. **CORS es el servidor dando permiso
explícito.** Origen = esquema + host + puerto; cambiar cualquiera de los tres lo hace cross-origin.

- **Simple request:** GET/POST/HEAD con headers básicos → el navegador la manda y luego comprueba
  `Access-Control-Allow-Origin` en la respuesta. (La request *ya llegó* a tu servidor.)
- **Preflight:** cualquier otra cosa (PUT, DELETE, `Content-Type: application/json`, header custom como
  `Authorization`) dispara un `OPTIONS` previo. Responde con `Allow-Methods`, `Allow-Headers` y
  `Max-Age` (cachea el preflight y te ahorra un round trip por request).
- **Con credenciales:** si el cliente manda cookies, necesitas `Access-Control-Allow-Credentials: true` y
  **no puedes usar `Allow-Origin: *`** — hay que devolver el origen concreto (y por tanto validarlo contra
  una allowlist, nunca reflejar el header sin comprobar).

**Lo que hay que tener clarísimo:** *CORS no es seguridad para tu API.* Solo protege al usuario en el
navegador. `curl` y cualquier backend ignoran CORS por completo. **Tu API se protege con autenticación y
autorización, no con CORS.**

> **Ficha** · **Cuándo:** cuando un navegador llama a tu API desde otro origen ·
> **Patrón:** allowlist explícita de orígenes + `Max-Age` para cachear el preflight ·
> **Anti-patrón:** reflejar el header `Origin` sin validar, o `*` con credenciales (ni siquiera es válido) ·
> **Límites:** **CORS no protege tu API**: solo protege al usuario en el navegador ·
> **Cómo falla:** en un "simple request" la petición **ya se ejecutó** en tu servidor; el navegador solo
> oculta la respuesta · **Decisión:** protege con autenticación y autorización, nunca con CORS ·
> **Trade-off:** permisividad (menos fricción en desarrollo) vs superficie de ataque ·
> **Relacionado:** CSRF, cookies, autorización `[06]`

---

## Content negotiation, compresión y transferencia

- **Negociación:** `Accept: application/json` / `Accept-Language` / `Accept-Encoding`. El servidor elige y
  responde con `Content-Type` y **`Vary`**.
- **Compresión:** gzip (universal), **brotli** (mejor ratio, estándar hoy para texto), zstd (rápido, en auge).
  Comprime texto (JSON, HTML, CSS, JS); **no comprimas** lo ya comprimido (imágenes, vídeo, zip).
- **Riesgo:** comprimir respuestas que mezclan secreto y entrada del usuario permite ataques tipo BREACH.
  Por eso no se comprimen respuestas que incluyan tokens CSRF junto a input reflejado.
- **`Transfer-Encoding: chunked`:** mandas sin saber el tamaño total. Base del streaming.
- **Request smuggling:** cuando un proxy y tu servidor interpretan `Content-Length` y `Transfer-Encoding`
  de forma distinta, un atacante puede colar una request dentro de otra. Se mitiga rechazando requests con
  ambos headers y manteniendo el stack actualizado.

> **Ficha** · **Cuándo:** en respuestas de texto de tamaño apreciable ·
> **Patrón:** brotli para texto, precomprimido en build para estáticos ·
> **Anti-patrón:** comprimir imágenes, vídeo o zip (gastas CPU sin ganar nada) ·
> **Límites:** comprimir cuesta CPU en cada respuesta dinámica ·
> **Cómo falla:** **request smuggling** cuando proxy y servidor interpretan distinto `Content-Length`
> y `Transfer-Encoding` · **Decisión:** nivel medio en dinámico, máximo en estáticos ·
> **Trade-off:** ancho de banda vs CPU; y compresión + secretos reflejados = BREACH ·
> **Relacionado:** performance, streaming `[09]`

---

## Uploads, downloads y streaming

**Uploads:**
- `multipart/form-data` para archivos pequeños/medianos.
- **Presigned URLs**: el cliente sube directo a S3/GCS con una URL firmada y temporal. **Tu backend nunca
  toca los bytes.** Es el patrón correcto por defecto (ver `15-files-data.md`).
- **Multipart upload / resumable** para archivos grandes: trocear, subir en paralelo, reintentar solo el
  trozo fallido.
- Límites: tamaño máximo, validar el **tipo real** (magic bytes, no la extensión ni el `Content-Type`), y
  nunca servir lo subido desde tu dominio principal.

**Downloads:** `Content-Disposition: attachment; filename="..."`, **Range requests** (`Accept-Ranges: bytes`)
para reanudar y para seek de vídeo, y presigned URLs para no proxyficar gigabytes por tu app.

**Streaming:** manda a medida que generas, con `chunked` o SSE. Clave en respuestas de LLM (el usuario ve
tokens al instante en vez de esperar 20s) y en exports grandes de CSV. **Cuidado:** si haces streaming,
ya no puedes cambiar el status code a mitad — un error después del primer byte solo se puede comunicar
dentro del propio stream.

> **Ficha** · **Cuándo:** cualquier archivo cuyo tamaño no esté acotado ·
> **Patrón:** presigned URLs directas al object storage; el backend solo firma `[15]` ·
> **Anti-patrón:** proxyficar gigabytes por tu aplicación ·
> **Límites:** una vez empezado el stream **ya no puedes cambiar el status code** ·
> **Cómo falla:** un error a mitad de un stream solo se puede comunicar dentro del propio stream ·
> **Decisión:** si el cliente espera resultado progresivo (tokens de LLM, export), streaming ·
> **Trade-off:** latencia percibida (streaming) vs simplicidad del manejo de errores ·
> **Relacionado:** presigned URLs, SSE, background jobs `[15, 18]`

---

## Cookies

```
Set-Cookie: sid=abc; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=3600; Domain=.tuapp.com
```

- **`HttpOnly`:** JS no puede leerla. Es tu defensa contra robo de sesión vía XSS. **Obligatorio** para
  cookies de sesión.
- **`Secure`:** solo por HTTPS.
- **`SameSite`:** `Strict` (nunca cross-site) · `Lax` (se envía en navegación top-level GET; **es el default
  en los navegadores modernos**) · `None` (requiere `Secure`; necesario para contextos embebidos).
  SameSite mitiga CSRF pero **no lo elimina** — ver `06-security.md`.
- **Scope:** `Domain` y `Path` definen a quién se manda. Poner `Domain=.tuapp.com` la comparte con todos los
  subdominios, incluido ese subdominio de marketing con menos seguridad. Piénsalo dos veces.

> **Ficha** · **Cuándo:** sesiones de navegador ·
> **Patrón:** `HttpOnly; Secure; SameSite=Lax` como mínimo obligatorio ·
> **Anti-patrón:** `Domain=.tuapp.com` compartiendo la sesión con subdominios menos seguros ·
> **Límites:** ~4 KB por cookie y un máximo por dominio; viajan en **cada** request ·
> **Cómo falla:** sin `HttpOnly`, cualquier XSS roba la sesión ·
> **Decisión:** token de sesión opaco en cookie; nunca datos en el valor ·
> **Trade-off:** cookies (cómodas, exigen defensa CSRF) vs bearer tokens (sin CSRF, exigen guardarlos bien) ·
> **Relacionado:** sessions, CSRF, XSS `[06]`

---

## Implementación: servidor, proxy y middleware

Entre el socket y tu función hay tres piezas, y confundir sus responsabilidades causa incidentes.

```nginx
# Reverse proxy: lo que hace nginx/Envoy delante de tu app
server {
    listen 443 ssl http2;
    client_max_body_size 10m;          # limite de payload: rechaza antes de tocar tu app
    proxy_read_timeout 30s;            # cuanto espera a tu backend
    location / {
        proxy_pass http://app:8000;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;   # sin esto tu app cree que todo es HTTP
        proxy_set_header X-Request-Id      $request_id;
    }
}
```

**El proxy hace buffering**, y eso te protege de clientes lentos (slowloris): recibe la request completa
y solo entonces ocupa un worker tuyo. Por eso un servidor de aplicación **nunca** se expone directo.

```python
# Middleware: la cadena que envuelve cada request. El orden importa.
@app.middleware("http")
async def contexto(request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    inicio = time.perf_counter()
    try:
        respuesta = await call_next(request)
    except ErrorDeNegocio as e:
        respuesta = JSONResponse({"codigo": e.codigo}, status_code=409)
    respuesta.headers["X-Request-Id"] = request_id
    log.info("request", extra={"request_id": request_id, "ruta": request.url.path,
                               "estado": respuesta.status_code,
                               "ms": round((time.perf_counter() - inicio) * 1000)})
    return respuesta
```

**Orden típico (de fuera hacia dentro):** request-id → logging/tracing → CORS → compresión →
autenticación → rate limiting → rutas. Poner autenticación *después* de rate limiting significa gastar
cuota en peticiones que ni siquiera están autenticadas.

> **Ficha** · **Cuándo:** en todo servicio HTTP ·
> **Patrón:** cross-cutting concerns (logs, auth, tracing) en middleware, nunca copiados por endpoint ·
> **Anti-patrón:** lógica de negocio en el middleware, o exponer el servidor de app directo a internet ·
> **Límites:** cada middleware suma latencia a **todas** las peticiones ·
> **Cómo falla:** sin `X-Forwarded-Proto`, tu app genera URLs `http://` detrás de un LB con TLS ·
> **Decisión:** lo que aplica a todas las rutas va en middleware; lo demás, en el endpoint ·
> **Trade-off:** un middleware genérico es cómodo y oculta el coste que añade ·
> **Relacionado:** reverse proxy, correlation IDs, rate limiting `[03, 12, 13]`

---

## Límites y timeouts de la capa HTTP

Los números que hay que fijar **explícitamente**, porque los defaults son malos o infinitos.

| Límite | Valor típico | Qué pasa si no lo pones |
|---|---|---|
| Tamaño de body | 1-10 MB | un POST de 2 GB agota tu memoria |
| Tamaño de headers | 8-16 KB | header bombing |
| Profundidad/tamaño del JSON | 20 niveles / 1 MB | un JSON anidado tumba el parser |
| Timeout de lectura del cliente | 10-30 s | slowloris: conexiones abiertas para siempre |
| Timeout hacia el upstream | < el del cliente | trabajo fantasma que nadie leerá |
| Conexiones concurrentes | según memoria | OOM bajo pico |
| Keep-alive idle | 60-75 s | file descriptors ociosos acumulados |

**La regla de oro de los timeouts:** el del cliente **mayor** que el del servidor, y el del servidor mayor
que el de sus dependencias. Si se invierte, reintentas mientras el de arriba ya se rindió `[10]`.

> **Ficha** · **Cuándo:** antes del primer despliegue a producción ·
> **Patrón:** límites en el proxy (barato, antes de llegar a tu app) y también en la app ·
> **Anti-patrón:** confiar en los defaults del framework, que suelen ser ilimitados ·
> **Límites:** rechazar pronto ahorra recursos pero devuelve 413/431, que hay que documentar ·
> **Cómo falla:** sin límite de body, un solo cliente te agota la memoria del contenedor ·
> **Decisión:** si el tamaño no está acotado por diseño, va por upload directo a storage `[15]` ·
> **Trade-off:** permisividad (menos errores para clientes legítimos) vs resiliencia ·
> **Relacionado:** backpressure, load shedding, timeouts `[09, 10]`

---

## Cómo falla HTTP en producción

| Síntoma | Causa habitual | Dónde mirar |
|---|---|---|
| **502 Bad Gateway** | tu app murió, o devolvió algo que el proxy no entiende | logs de la app, OOMKilled |
| **504 Gateway Timeout** | tu app tarda más que `proxy_read_timeout` | traza de la request lenta |
| **503** | no hay backends sanos | readiness probe, despliegue en curso |
| **Connection reset** | el peer cerró: timeout, crash, o límite de conexiones | `dmesg`, límites del LB |
| **499 / client closed** | el usuario se fue antes de que respondieras | latencia p99 |
| **502 en cada despliegue** | falta connection draining o `preStop` | configuración de rolling update `[13]` |
| **Funciona en curl, falla en el navegador** | CORS o certificado sin cadena intermedia | consola del navegador |
| **Funciona en el navegador, falla en curl** | cadena intermedia ausente (el navegador la tenía cacheada) | `openssl s_client -showcerts` |
| **TLS handshake failure** | versión o cifrado incompatible, o SNI mal configurado | `openssl s_client` |
| **Malformed request** | request smuggling, o un cliente que no respeta el protocolo | logs del proxy |

> **Ficha** · **Cuándo:** en cualquier incidente que se manifieste como error HTTP ·
> **Patrón:** distinguir siempre "mi app falló" (5xx propio) de "la red o el proxy falló" (502/504) ·
> **Anti-patrón:** reintentar un 504 sin saber si la operación se ejecutó ·
> **Límites:** un 504 **no** te dice si el trabajo se completó: puede haberse ejecutado entero ·
> **Cómo falla:** el caso peor es el timeout ambiguo — de ahí la idempotencia `[08]` ·
> **Decisión:** si la operación muta estado, necesita clave de idempotencia antes de poder reintentarla ·
> **Trade-off:** reintentar mejora la tasa de éxito y arriesga duplicados ·
> **Relacionado:** idempotencia, circuit breakers, graceful shutdown `[08, 10, 13]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Qué pasa exactamente cuando escribo una URL y pulso enter?**
La pregunta más clásica que existe. Recorre: DNS (con cache en varios niveles) → TCP handshake → TLS
handshake → request HTTP → el LB enruta → tu app → DB → respuesta → render. *Señal:* mencionas los round
trips y dónde se pierde el tiempo, no solo la lista de pasos.

**Q: ¿WebSocket o SSE para streaming de respuestas de un LLM?**
SSE. Es unidireccional, va sobre HTTP normal, reconecta solo, atraviesa proxies y balanceadores sin sticky
sessions. *Señal:* mencionas que WebSocket añade estado en el servidor y complica despliegues y escalado
horizontal, y que no ganas nada si el cliente solo escucha.

**Q: ¿CORS protege tu API?**
No. Protege al usuario en el navegador. Un cliente no-navegador la ignora. *Señal:* explicas que en un
"simple request" la petición **llega y se ejecuta** en tu servidor; lo que bloquea el navegador es que el JS
lea la respuesta. Por eso una API mutante nunca debe depender de CORS para protegerse.

**Q: ¿Por qué HTTP/2 no eliminó del todo el head-of-line blocking?**
Porque multiplexa a nivel de aplicación pero sigue sobre una única conexión TCP, y TCP garantiza orden: un
paquete perdido bloquea todos los streams. HTTP/3 lo arregla porque QUIC gestiona streams independientes
sobre UDP. *Señal:* conectas esto con redes móviles con pérdida de paquetes, donde la diferencia es enorme.

**Q: ¿PATCH es idempotente?**
Por defecto no, aunque puede diseñarse para serlo. Un PATCH de `{"$inc": {"contador": 1}}` claramente no lo
es. *Señal:* lo unes a que POST/PATCH necesitan `Idempotency-Key` explícita si el cliente va a reintentar.

**Trade-off central de esta caja:** *simplicidad y cacheabilidad (REST/HTTP) vs eficiencia y contrato fuerte
(gRPC/Protobuf) vs flexibilidad del cliente (GraphQL)*. La respuesta senior casi siempre es **REST hacia
fuera, gRPC hacia dentro**, y GraphQL solo si tienes muchos clientes con necesidades de datos muy distintas
y equipo para sostener su complejidad operativa.

---

## Fuentes

- RFC 9110 (HTTP Semantics) · RFC 9111 (Caching) · RFC 9112 (HTTP/1.1) · RFC 9113 (HTTP/2) · RFC 9114 (HTTP/3)
- [MDN HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP) — la referencia práctica de headers y CORS.
- RFC 8446 (TLS 1.3) · RFC 6265bis (Cookies, `SameSite`)
- [High Performance Browser Networking](https://hpbn.co/) — Ilya Grigorik, sobre TCP, TLS y HTTP.
