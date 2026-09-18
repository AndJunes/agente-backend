# 02 · Web & Protocols

> Every backend is, at heart, a program that reads bytes from a socket and writes other bytes.
> This is the box people most "assume they already know", and the one they fail most often when asked in detail.

**Covers from the syllabus:** `concepts` · `protocols` · `headers` · `implementations` · `constraints`
· `failure_modes` · `tradeoffs`

---

## The full journey of a request

When someone types `https://api.tuapp.com/pedidos`, this is what happens, in order:

```
1. DNS      name -> IP            (~20-100ms if not cached)
2. TCP      3-way handshake       (1 RTT)
3. TLS      handshake             (1 RTT on TLS 1.3, 2 on TLS 1.2)
4. HTTP     request + response    (1 RTT + server time)
```

**Practical consequence:** a new connection costs 3-4 round trips before the first useful byte. That is why
keep-alive, connection pooling, HTTP/2 multiplexing and 0-RTT exist. If your backend opens a new TCP
connection to the database on every request, you are paying this thousands of times per second.

> **Card** · **When:** debugging first-connection latency or designing for distant clients ·
> **Pattern:** keep-alive and connection pooling to amortize the 3-4 round trips ·
> **Anti-pattern:** opening a new connection per request (to the DB or to an internal API) ·
> **Limits:** the handshake cannot be eliminated, only reused or moved closer ·
> **How it fails:** slow or badly cached DNS, and expired certificates that break step 3 ·
> **Decision:** if the client is far away, a CDN; if the target is internal, a pool ·
> **Trade-off:** persistent connections save latency and consume file descriptors ·
> **Related:** connection pooling, CDN, TLS `[01, 04, 09]`

---

## TCP/IP

- **3-way handshake:** SYN → SYN-ACK → ACK. One full round trip before any data is sent.
- **Flow control:** the receive window stops the sender from drowning the receiver.
- **Congestion control:** slow start, congestion avoidance. That is why a new connection starts slow and
  speeds up — and why persistent connections are faster than new ones even when the bandwidth is the
  same.
- **Head-of-line blocking:** TCP guarantees ordering. If packet 5 is lost, packets 6-10, already received,
  wait in the buffer until the retransmission of 5 arrives. **This is the problem QUIC solves.**
- **TIME_WAIT:** after closing, the socket stays in that state for ~60s. A server that opens and closes a huge
  number of outbound connections can run out of ephemeral ports. It shows up as "cannot assign requested address".

**Nagle's algorithm and `TCP_NODELAY`:** Nagle batches small packets so as not to waste headers, which
adds up to 200ms of latency. Almost every modern server enables `TCP_NODELAY` to turn it off.

> **Card** · **When:** debugging hung connections, resets or port exhaustion ·
> **Pattern:** `TCP_NODELAY` enabled and connections reused ·
> **Anti-pattern:** opening and closing thousands of outbound connections per second ·
> **Limits:** ~28,000 ephemeral ports per destination IP; `TIME_WAIT` of ~60s ·
> **How it fails:** "cannot assign requested address", and head-of-line blocking when a packet is lost ·
> **Decision:** if you need strict ordering, TCP; if you tolerate loss and want latency, UDP/QUIC ·
> **Trade-off:** reliability (TCP) vs latency under packet loss (QUIC) ·
> **Related:** HTTP/3, sockets, file descriptors `[01, 13]`

---

## DNS

- Hierarchical: root → TLD (`.com`) → authoritative (`tuapp.com`).
- **Record types you should know:** `A` (IPv4), `AAAA` (IPv6), `CNAME` (alias), `MX` (mail),
  `TXT` (verification, SPF/DKIM), `NS` (delegation), `SRV` (service+port), `CAA` (which CA may issue
  certificates for your domain).
- **TTL:** how long resolvers cache. **The TTL is your rollback time.** If you have a 24h TTL and want to
  move traffic, it will take you 24h. Before a migration, lower the TTL to 60s days in advance.
- **DNS as a load balancer:** round-robin DNS spreads load but doesn't know whether a node is down, and clients
  cache unpredictably. It works for geo-routing and slow failover, not for fine-grained balancing.
- **Classic trap:** old JVMs cached DNS forever (`networkaddress.cache.ttl=-1`). If the
  provider changes the load balancer's IP, your app keeps going to the old one. It has taken down entire companies.

> **Card** · **When:** in any migration, failover or change of provider ·
> **Pattern:** lower the TTL to 60s **days before** a planned migration ·
> **Anti-pattern:** caching DNS forever on the client (old JVMs did this) ·
> **Limits:** the TTL is your minimum rollback time; not all resolvers honor it the same way ·
> **How it fails:** the provider changes the load balancer's IP and your app keeps going to the old one ·
> **Decision:** DNS is for geo-routing and slow failover, not for fine-grained balancing ·
> **Trade-off:** high TTL = fewer lookups and less agility; low = more load and more control ·
> **Related:** load balancing, failover `[09, 10, 13]`

---

## TLS

- **What it gives you:** confidentiality (encryption), integrity (nobody tampered with it) and authenticity (you are talking
  to who you think you are). **It does not give you** authorization or protection against a compromised server.
- **How it works:** an asymmetric handshake (expensive) to agree on a symmetric session key (cheap), and
  the rest of the conversation uses the symmetric key.
- **TLS 1.3** (the current standard): 1-RTT handshake, 0-RTT on reconnection, removes legacy ciphers.
  If someone tells you they are using TLS 1.0/1.1 in 2026, that is an audit finding.
- **Certificates and the chain of trust:** your cert is signed by an intermediate CA, signed by a root
  that the operating system already ships. **Classic production mistake: serving the cert without the intermediate chain**
  — it works in your browser (which has it cached) and fails in `curl` and on other servers.
- **mTLS (mutual TLS):** the client presents a certificate too. It is the foundation of zero-trust between services
  and of service meshes.
- **TLS termination:** it usually terminates at the load balancer / ingress, and inside the network traffic travels in plaintext or
  over mTLS. This matters because **`X-Forwarded-Proto` and `X-Forwarded-For` are the only way for your
  app to know the original IP and scheme.**

> **Card** · **When:** always; inside the VPC too (mTLS) ·
> **Pattern:** TLS 1.3, full intermediate chain, and automated renewal ·
> **Anti-pattern:** serving the certificate without the intermediate chain (works in your browser, fails in `curl`) ·
> **Limits:** TLS does not give you authorization nor protect you from a compromised server ·
> **How it fails:** **expired certificate** — one of the most frequent causes of a total outage ·
> **Decision:** terminate TLS at the load balancer and use mTLS inside if you need zero-trust ·
> **Trade-off:** terminating at the edge simplifies things and forces you to trust the internal network ·
> **Related:** security headers, secrets, X-Forwarded-For `[06, 13, 14]`

---

## HTTP/1.1 · HTTP/2 · HTTP/3

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Transport | TCP | TCP | **QUIC over UDP** |
| Format | text | binary (frames) | binary (frames) |
| Concurrency | 1 request per connection (pipelining broken) | **multiplexing** over one connection | multiplexing without TCP HOL |
| Headers | repeated text | compressed (HPACK) | compressed (QPACK) |
| HOL blocking | yes, at the application level | solved at the app level, **persists in TCP** | truly solved |
| Server push | no | yes (deprecated in practice) | no |
| Handshake | TCP+TLS separate | TCP+TLS separate | **combined, 0-RTT possible** |

**What matters for backend:**

- HTTP/1.1 needed 6 parallel connections per domain and tricks like *domain sharding*. HTTP/2 makes them
  counterproductive.
- **HTTP/2 over a single TCP connection:** if a packet is lost, *all* the multiplexed streams wait.
  That is why HTTP/3 wins so big on poor mobile networks.
- **gRPC runs over HTTP/2** — that is why it needs end-to-end HTTP/2 support, and why old L7 load
  balancers break it.
- HTTP/3 is usually terminated by the CDN or the load balancer; your application server almost always speaks
  HTTP/1.1 or HTTP/2 behind it.

> **Card** · **When:** choosing a protocol between services or optimizing mobile clients ·
> **Pattern:** HTTP/2 or /3 at the edge, HTTP/1.1 or /2 inside ·
> **Anti-pattern:** domain sharding with HTTP/2 (counterproductive: it breaks multiplexing) ·
> **Limits:** HTTP/2 still runs over one TCP connection, so it inherits its head-of-line blocking ·
> **How it fails:** old L7 load balancers break gRPC because they don't speak HTTP/2 end to end ·
> **Decision:** gRPC between services, REST to the outside ·
> **Trade-off:** binary efficiency vs debuggability with text tools ·
> **Related:** gRPC, load balancing `[03, 09]`

---

## Methods, semantics and idempotency

| Method | Safe (doesn't mutate) | Idempotent | Cacheable | Use |
|---|---|---|---|---|
| GET | ✅ | ✅ | ✅ | read |
| HEAD | ✅ | ✅ | ✅ | metadata without a body |
| POST | ❌ | **❌** | rarely | create, actions |
| PUT | ❌ | ✅ | ❌ | full replacement |
| PATCH | ❌ | **❌** (unless you design it that way) | ❌ | partial update |
| DELETE | ❌ | ✅ | ❌ | delete |
| OPTIONS | ✅ | ✅ | ❌ | CORS preflight |

**Idempotent = repeating the call yields the same final state**, not the same response. A repeated `DELETE`
returns 404 the second time, but the final state is identical: it is still idempotent.

**Why it matters enormously:** clients and proxies automatically retry idempotent methods.
`POST` is not retried on its own, which is why you need **idempotency keys** (see `03-apis.md` and `07-payments.md`).

> **Card** · **When:** designing any endpoint the client may retry ·
> **Pattern:** idempotent methods by design; `Idempotency-Key` for the ones that aren't ·
> **Anti-pattern:** a `GET` that mutates state (prefetchers and crawlers will execute it) ·
> **Limits:** idempotent = same **final state**, not the same response ·
> **How it fails:** a proxy retries your POST and you charge twice ·
> **Decision:** POST/PATCH need an explicit idempotency key ·
> **Trade-off:** REST purity vs explicit, auditable action endpoints ·
> **Related:** idempotency keys, retries `[03, 07, 08]`

---

## Status codes a senior uses well

- **200 OK** / **201 Created** (with a `Location` header) / **202 Accepted** (asynchronous processing accepted,
  not done yet) / **204 No Content**.
- **301 vs 308** and **302 vs 307:** the new ones (307/308) **preserve the method**. A 301 on a POST can
  turn it into a GET. Use 308/307 if you don't want surprises.
- **304 Not Modified:** the response to a conditional request with `ETag`/`If-None-Match`. Saves bandwidth.
- **400** malformed · **401** not authenticated (*who you are*) · **403** authenticated but not allowed
  (*what you can do*) · **404** doesn't exist · **409** state conflict · **410** gone for good ·
  **422** valid syntax but semantically invalid · **429** rate limited (**with `Retry-After`**).
- **500** our error · **502** the upstream answered with garbage · **503** unavailable / overloaded
  (**with `Retry-After`**) · **504** upstream timeout.

**Seniority signal:** telling 401 from 403, using 409 for optimistic concurrency conflicts, returning
`Retry-After` on 429/503, and **not returning 200 with `{"error": ...}` inside**. That last one breaks all
automatic retries, circuit breakers and the metrics of your own stack.

> **Card** · **When:** on every response; it is the contract machines read ·
> **Pattern:** 429 and 503 **always** with `Retry-After`; 409 for concurrency conflicts ·
> **Anti-pattern:** returning 200 with `{"error": ...}` inside — it breaks retries, breakers and metrics ·
> **Limits:** the code is a narrow channel: it needs a structured error body ·
> **How it fails:** clients that retry a 400 forever because they can't tell permanent from transient ·
> **Decision:** 401 = I don't know who you are; 403 = I know who you are and you can't ·
> **Trade-off:** granularity of codes vs simplicity for the consumer ·
> **Related:** error contracts, circuit breakers `[03, 10]`

---

## Headers that matter

**Request:** `Authorization`, `Content-Type`, `Accept`, `Accept-Encoding`, `If-None-Match`,
`Idempotency-Key`, `User-Agent`, `X-Request-Id` (correlation, see `12-observability.md`),
`X-Forwarded-For` / `Forwarded`.

**Response:** `Content-Type`, `Cache-Control`, `ETag`, `Location`, `Retry-After`, `Set-Cookie`,
`Content-Encoding`, `Vary`, and the security ones (`06-security.md`).

**`Vary` is the header everybody forgets.** It tells the cache "this response depends on this header".
If you serve different content based on `Accept-Language` or `Authorization` and you don't set `Vary`, the CDN will serve one
user's response to another. **That is a data leak, not just a cache bug.**

> **Card** · **When:** on every response that is cacheable or depends on the user ·
> **Pattern:** `Vary` declared whenever the response depends on a header ·
> **Anti-pattern:** cacheable per-user content without `Vary: Authorization` ·
> **Limits:** maximum header size (~8-16 KB on most servers) ·
> **How it fails:** **the CDN serves one user's response to another** — it's a data leak, not just a bug ·
> **Decision:** if it varies per user, `Cache-Control: private` or don't cache ·
> **Trade-off:** cacheability vs personalization ·
> **Related:** HTTP cache, CDN `[09]`

---

## HTTP caching

```
Cache-Control: public, max-age=3600, stale-while-revalidate=86400
Cache-Control: private, no-cache            # always revalidates, but may store
Cache-Control: no-store                     # never store (sensitive data)
```

- `max-age` (fresh) · `s-maxage` (only for shared caches/CDN) · `must-revalidate`.
- **`no-cache` ≠ `no-store`.** `no-cache` means "store it but ask me before using it";
  `no-store` means "don't even write it down". Mixing them up is a junior mistake.
- **Conditional validation:** `ETag` + `If-None-Match` (or `Last-Modified` + `If-Modified-Since`) → 304.
- **`stale-while-revalidate`:** serves the stale copy while refreshing in the background. Cache-hit latency with
  almost fresh data. Widely used on CDNs.

> **Card** · **When:** for everything that is read far more than it is written ·
> **Pattern:** `ETag` + `If-None-Match` for cheap revalidation; `stale-while-revalidate` at the edge ·
> **Anti-pattern:** confusing `no-cache` (stores but revalidates) with `no-store` (never store) ·
> **Limits:** invalidating what has already been distributed is impossible: you can only wait for the TTL or purge by tag ·
> **How it fails:** a long `max-age` on a resource that changed leaves users with stale data for days ·
> **Decision:** sensitive data → `no-store`; versioned static assets → a huge `max-age` ·
> **Trade-off:** freshness vs latency and origin cost ·
> **Related:** CDN, caching, invalidation `[09]`

---

## REST vs GraphQL vs gRPC vs WebSockets vs SSE

| | REST | GraphQL | gRPC | WebSocket | SSE |
|---|---|---|---|---|---|
| Transport | HTTP | HTTP (1 endpoint) | HTTP/2 | TCP (upgrade) | HTTP |
| Format | JSON | JSON | Protobuf (binary) | whatever you want | text |
| Direction | req/res | req/res | req/res + streaming | **bidirectional** | **server → client** |
| HTTP cache | ✅ native | ❌ hard (everything is POST) | ❌ | ❌ | partial |
| Typing | OpenAPI (optional) | **mandatory schema** | **.proto contract** | none | none |
| Typical use | public APIs, CRUD | frontends with many views | **between microservices** | chat, collaboration, games | notifications, LLM tokens, progress |

**REST** wins on simplicity, cacheability and tooling. Its real problem is over-fetching/under-fetching
and the explosion of custom-made endpoints.

**GraphQL** gives the client exactly what it asks for. The prices you pay: the **N+1 problem** (solved with
DataLoader/batching), the difficulty of caching, rate limiting by *query cost* instead of per request,
and the fact that a maliciously nested query can take you down (you need depth/complexity limits and persisted queries).

**gRPC** is the standard for **service-to-service**: strong contract, binary, fast, native streaming, codegen
in every language. Don't use it facing the browser (you need grpc-web and a proxy).

**WebSocket vs SSE** is the comparison that comes up most:
- SSE runs over plain HTTP, reconnects on its own (with `Last-Event-ID`), goes through proxies without trouble, and is
  **unidirectional**. For streaming LLM tokens, notifications or progress bars, SSE is
  simpler and sufficient.
- WebSocket is bidirectional and low-latency, but it is a stateful connection: it complicates load balancing
  (you need sticky sessions or a backplane such as Redis pub/sub), deployments (everyone reconnects at the
  same time) and horizontal scaling.

**Rule:** if the client only listens, SSE. If the client talks constantly, WebSocket.

> **Card** · **When:** starting an API or adding real time ·
> **Pattern:** REST to the outside, gRPC inside, SSE for unidirectional streaming ·
> **Anti-pattern:** WebSocket for notifications the client only listens to ·
> **Limits:** GraphQL can't be cached with HTTP; WebSocket requires state and sticky sessions ·
> **How it fails:** a malicious nested GraphQL query takes down the server if there are no depth limits ·
> **Decision:** does the client only listen? SSE. Does it talk constantly? WebSocket ·
> **Trade-off:** client flexibility vs the server's operational cost ·
> **Related:** API design, cost-based rate limiting `[03, 18]`

---

## CORS

By default, the browser blocks cross-origin requests made from JS. **CORS is the server granting explicit
permission.** Origin = scheme + host + port; changing any of the three makes it cross-origin.

- **Simple request:** GET/POST/HEAD with basic headers → the browser sends it and then checks
  `Access-Control-Allow-Origin` on the response. (The request *has already reached* your server.)
- **Preflight:** anything else (PUT, DELETE, `Content-Type: application/json`, a custom header such as
  `Authorization`) triggers a prior `OPTIONS`. Answer with `Allow-Methods`, `Allow-Headers` and
  `Max-Age` (it caches the preflight and saves you a round trip per request).
- **With credentials:** if the client sends cookies, you need `Access-Control-Allow-Credentials: true` and
  **you cannot use `Allow-Origin: *`** — you have to return the specific origin (and therefore validate it against
  an allowlist, never reflect the header without checking).

**What you must be crystal clear about:** *CORS is not security for your API.* It only protects the user in the
browser. `curl` and any backend ignore CORS completely. **Your API is protected with authentication and
authorization, not with CORS.**

> **Card** · **When:** when a browser calls your API from another origin ·
> **Pattern:** an explicit allowlist of origins + `Max-Age` to cache the preflight ·
> **Anti-pattern:** reflecting the `Origin` header without validation, or `*` with credentials (it isn't even valid) ·
> **Limits:** **CORS does not protect your API**: it only protects the user in the browser ·
> **How it fails:** in a "simple request" the request **has already executed** on your server; the browser only
> hides the response · **Decision:** protect with authentication and authorization, never with CORS ·
> **Trade-off:** permissiveness (less friction during development) vs attack surface ·
> **Related:** CSRF, cookies, authorization `[06]`

---

## Content negotiation, compression and transfer

- **Negotiation:** `Accept: application/json` / `Accept-Language` / `Accept-Encoding`. The server chooses and
  responds with `Content-Type` and **`Vary`**.
- **Compression:** gzip (universal), **brotli** (better ratio, today's standard for text), zstd (fast, on the rise).
  Compress text (JSON, HTML, CSS, JS); **don't compress** what is already compressed (images, video, zip).
- **Risk:** compressing responses that mix a secret with user input enables BREACH-style attacks.
  That is why responses that include CSRF tokens alongside reflected input are not compressed.
- **`Transfer-Encoding: chunked`:** you send without knowing the total size. The basis of streaming.
- **Request smuggling:** when a proxy and your server interpret `Content-Length` and `Transfer-Encoding`
  differently, an attacker can sneak one request inside another. It is mitigated by rejecting requests with
  both headers and keeping the stack up to date.

> **Card** · **When:** on text responses of meaningful size ·
> **Pattern:** brotli for text, precompressed at build time for static assets ·
> **Anti-pattern:** compressing images, video or zip (you burn CPU and gain nothing) ·
> **Limits:** compression costs CPU on every dynamic response ·
> **How it fails:** **request smuggling** when the proxy and the server interpret `Content-Length`
> and `Transfer-Encoding` differently · **Decision:** medium level for dynamic content, maximum for static assets ·
> **Trade-off:** bandwidth vs CPU; and compression + reflected secrets = BREACH ·
> **Related:** performance, streaming `[09]`

---

## Uploads, downloads and streaming

**Uploads:**
- `multipart/form-data` for small/medium files.
- **Presigned URLs**: the client uploads directly to S3/GCS with a signed, temporary URL. **Your backend never
  touches the bytes.** It is the correct default pattern (see `15-files-data.md`).
- **Multipart upload / resumable** for large files: split into chunks, upload in parallel, retry only the
  failed chunk.
- Limits: maximum size, validate the **real type** (magic bytes, not the extension or the `Content-Type`), and
  never serve uploaded content from your main domain.

**Downloads:** `Content-Disposition: attachment; filename="..."`, **Range requests** (`Accept-Ranges: bytes`)
to resume and to seek in video, and presigned URLs so you don't proxy gigabytes through your app.

**Streaming:** send as you generate, with `chunked` or SSE. Key for LLM responses (the user sees
tokens instantly instead of waiting 20s) and for large CSV exports. **Careful:** once you are streaming,
you can no longer change the status code halfway — an error after the first byte can only be communicated
inside the stream itself.

> **Card** · **When:** any file whose size is not bounded ·
> **Pattern:** presigned URLs straight to object storage; the backend only signs `[15]` ·
> **Anti-pattern:** proxying gigabytes through your application ·
> **Limits:** once the stream has started **you can no longer change the status code** ·
> **How it fails:** an error halfway through a stream can only be communicated inside the stream itself ·
> **Decision:** if the client expects a progressive result (LLM tokens, export), streaming ·
> **Trade-off:** perceived latency (streaming) vs simplicity of error handling ·
> **Related:** presigned URLs, SSE, background jobs `[15, 18]`

---

## Cookies

```
Set-Cookie: sid=abc; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=3600; Domain=.tuapp.com
```

- **`HttpOnly`:** JS cannot read it. It is your defense against session theft via XSS. **Mandatory** for
  session cookies.
- **`Secure`:** HTTPS only.
- **`SameSite`:** `Strict` (never cross-site) · `Lax` (sent on top-level GET navigation; **it is the default
  in modern browsers**) · `None` (requires `Secure`; needed for embedded contexts).
  SameSite mitigates CSRF but **does not eliminate it** — see `06-security.md`.
- **Scope:** `Domain` and `Path` define who it is sent to. Setting `Domain=.tuapp.com` shares it with all
  subdomains, including that less secure marketing subdomain. Think twice.

> **Card** · **When:** browser sessions ·
> **Pattern:** `HttpOnly; Secure; SameSite=Lax` as the mandatory minimum ·
> **Anti-pattern:** `Domain=.tuapp.com` sharing the session with less secure subdomains ·
> **Limits:** ~4 KB per cookie and a maximum per domain; they travel on **every** request ·
> **How it fails:** without `HttpOnly`, any XSS steals the session ·
> **Decision:** an opaque session token in the cookie; never data in the value ·
> **Trade-off:** cookies (convenient, require CSRF defense) vs bearer tokens (no CSRF, require storing them properly) ·
> **Related:** sessions, CSRF, XSS `[06]`

---

## Implementation: server, proxy and middleware

Between the socket and your function there are three pieces, and mixing up their responsibilities causes incidents.

```nginx
# Reverse proxy: what nginx/Envoy does in front of your app
server {
    listen 443 ssl http2;
    client_max_body_size 10m;          # payload limit: rejects before it touches your app
    proxy_read_timeout 30s;            # how long it waits for your backend
    location / {
        proxy_pass http://app:8000;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;   # without this your app thinks everything is HTTP
        proxy_set_header X-Request-Id      $request_id;
    }
}
```

**The proxy does buffering**, and that protects you from slow clients (slowloris): it receives the full request
and only then takes up one of your workers. That is why an application server is **never** exposed directly.

```python
# Middleware: the chain that wraps every request. Order matters.
@app.middleware("http")
async def request_context(request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except BusinessError as e:
        response = JSONResponse({"code": e.code}, status_code=409)
    response.headers["X-Request-Id"] = request_id
    log.info("request", extra={"request_id": request_id, "path": request.url.path,
                               "status": response.status_code,
                               "ms": round((time.perf_counter() - start) * 1000)})
    return response
```

**Typical order (from the outside in):** request-id → logging/tracing → CORS → compression →
authentication → rate limiting → routes. Putting authentication *after* rate limiting means spending
quota on requests that aren't even authenticated.

> **Card** · **When:** in every HTTP service ·
> **Pattern:** cross-cutting concerns (logs, auth, tracing) in middleware, never copied per endpoint ·
> **Anti-pattern:** business logic in middleware, or exposing the app server directly to the internet ·
> **Limits:** every middleware adds latency to **all** requests ·
> **How it fails:** without `X-Forwarded-Proto`, your app generates `http://` URLs behind an LB with TLS ·
> **Decision:** what applies to every route goes in middleware; the rest, in the endpoint ·
> **Trade-off:** a generic middleware is convenient and hides the cost it adds ·
> **Related:** reverse proxy, correlation IDs, rate limiting `[03, 12, 13]`

---

## Limits and timeouts of the HTTP layer

The numbers you have to set **explicitly**, because the defaults are bad or infinite.

| Limit | Typical value | What happens if you don't set it |
|---|---|---|
| Body size | 1-10 MB | a 2 GB POST exhausts your memory |
| Header size | 8-16 KB | header bombing |
| JSON depth/size | 20 levels / 1 MB | a deeply nested JSON takes down the parser |
| Client read timeout | 10-30 s | slowloris: connections open forever |
| Upstream timeout | < the client's | ghost work nobody will ever read |
| Concurrent connections | based on memory | OOM under a spike |
| Keep-alive idle | 60-75 s | idle file descriptors piling up |

**The golden rule of timeouts:** the client's timeout **greater** than the server's, and the server's greater
than its dependencies'. If you invert it, you are retrying while the caller above has already given up `[10]`.

> **Card** · **When:** before the first production deployment ·
> **Pattern:** limits in the proxy (cheap, before reaching your app) and in the app as well ·
> **Anti-pattern:** trusting the framework defaults, which are usually unlimited ·
> **Limits:** rejecting early saves resources but returns 413/431, which must be documented ·
> **How it fails:** without a body limit, a single client exhausts the container's memory ·
> **Decision:** if the size is not bounded by design, it goes through a direct upload to storage `[15]` ·
> **Trade-off:** permissiveness (fewer errors for legitimate clients) vs resilience ·
> **Related:** backpressure, load shedding, timeouts `[09, 10]`

---

## Failure modes: HTTP in production

| Symptom | Usual cause | Where to look |
|---|---|---|
| **502 Bad Gateway** | your app died, or returned something the proxy doesn't understand | app logs, OOMKilled |
| **504 Gateway Timeout** | your app takes longer than `proxy_read_timeout` | trace of the slow request |
| **503** | no healthy backends | readiness probe, deployment in progress |
| **Connection reset** | the peer closed: timeout, crash, or connection limit | `dmesg`, LB limits |
| **499 / client closed** | the user left before you responded | p99 latency |
| **502 on every deploy** | missing connection draining or `preStop` | rolling update configuration `[13]` |
| **Works in curl, fails in the browser** | CORS, or a certificate without the intermediate chain | browser console |
| **Works in the browser, fails in curl** | missing intermediate chain (the browser had it cached) | `openssl s_client -showcerts` |
| **TLS handshake failure** | incompatible version or cipher, or misconfigured SNI | `openssl s_client` |
| **Malformed request** | request smuggling, or a client that doesn't respect the protocol | proxy logs |

> **Card** · **When:** in any incident that shows up as an HTTP error ·
> **Pattern:** always tell "my app failed" (my own 5xx) apart from "the network or the proxy failed" (502/504) ·
> **Anti-pattern:** retrying a 504 without knowing whether the operation ran ·
> **Limits:** a 504 does **not** tell you whether the work completed: it may have run in full ·
> **How it fails:** the worst case is the ambiguous timeout — hence idempotency `[08]` ·
> **Decision:** if the operation mutates state, it needs an idempotency key before it can be retried ·
> **Trade-off:** retrying improves the success rate and risks duplicates ·
> **Related:** idempotency, circuit breakers, graceful shutdown `[08, 10, 13]`

---

## Interview questions and trade-offs

**Q: What exactly happens when I type a URL and hit enter?**
The most classic question there is. Walk through: DNS (with caching at several levels) → TCP handshake → TLS
handshake → HTTP request → the LB routes it → your app → DB → response → render. *Signal:* you mention the round
trips and where the time is lost, not just the list of steps.

**Q: WebSocket or SSE for streaming LLM responses?**
SSE. It is unidirectional, runs over plain HTTP, reconnects on its own, and goes through proxies and load balancers without sticky
sessions. *Signal:* you mention that WebSocket adds server-side state and complicates deployments and horizontal
scaling, and that you gain nothing if the client only listens.

**Q: Does CORS protect your API?**
No. It protects the user in the browser. A non-browser client ignores it. *Signal:* you explain that in a
"simple request" the request **arrives and executes** on your server; what the browser blocks is the JS
reading the response. That is why a mutating API must never rely on CORS for protection.

**Q: Why didn't HTTP/2 completely eliminate head-of-line blocking?**
Because it multiplexes at the application level but still runs over a single TCP connection, and TCP guarantees ordering: one
lost packet blocks every stream. HTTP/3 fixes it because QUIC manages independent streams
over UDP. *Signal:* you connect this to mobile networks with packet loss, where the difference is huge.

**Q: Is PATCH idempotent?**
Not by default, although it can be designed to be. A PATCH of `{"$inc": {"counter": 1}}` clearly
isn't. *Signal:* you tie it to the fact that POST/PATCH need an explicit `Idempotency-Key` if the client is going to retry.

**Core trade-off of this box:** *simplicity and cacheability (REST/HTTP) vs efficiency and a strong contract
(gRPC/Protobuf) vs client flexibility (GraphQL)*. The senior answer is almost always **REST to the
outside, gRPC inside**, and GraphQL only if you have many clients with very different data needs
and a team to sustain its operational complexity.

---

## Sources

- RFC 9110 (HTTP Semantics) · RFC 9111 (Caching) · RFC 9112 (HTTP/1.1) · RFC 9113 (HTTP/2) · RFC 9114 (HTTP/3)
- [MDN HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP) — the practical reference for headers and CORS.
- RFC 8446 (TLS 1.3) · RFC 6265bis (Cookies, `SameSite`)
- [High Performance Browser Networking](https://hpbn.co/) — Ilya Grigorik, on TCP, TLS and HTTP.
