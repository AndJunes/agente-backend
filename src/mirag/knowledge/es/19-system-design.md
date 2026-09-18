# 19 · System Design

> La entrevista de system design no evalúa si sabes la respuesta: evalúa **cómo piensas cuando el problema
> es ambiguo**. Se juzga si haces las preguntas correctas, si justificas con números y si reconoces los
> trade-offs de tu propia solución.


**Cubre del temario:** `requirements` · `capacity` · `architecture` · `bottlenecks` · `failure_scenarios` · `tradeoffs` · `decisions` · `diagrams`

---

## El guion de una entrevista de 45 minutos

| Fase | Tiempo | Qué haces |
|---|---|---|
| 1. Requisitos | 5-8 min | preguntar y acotar el alcance |
| 2. Estimaciones | 3-5 min | números que justifiquen las decisiones |
| 3. API y modelo de datos | 5-8 min | el contrato y las entidades |
| 4. Diseño de alto nivel | 10 min | el dibujo con las piezas |
| 5. Profundizar | 10-15 min | el entrevistador elige un punto |
| 6. Cuellos de botella y fallos | 5 min | qué se rompe primero y cómo lo mitigas |

**El error número uno: empezar a dibujar cajas en el minuto uno.** Un senior dedica los primeros minutos a
acotar. El problema siempre está deliberadamente mal definido para ver si lo detectas.

> **Ficha** · **Cuándo:** toda entrevista de diseño ·
> **Patrón:** requisitos → estimaciones → API y datos → alto nivel → profundizar → fallos ·
> **Anti-patrón:** empezar a dibujar cajas en el minuto uno ·
> **Límites:** 45 minutos no dan para todo: acota en voz alta lo que dejas fuera ·
> **Cómo falla:** te quedas sin tiempo en la parte que de verdad evaluaban ·
> **Decisión:** el problema siempre está mal definido a propósito, para ver si lo detectas ·
> **Trade-off:** amplitud vs profundidad ·
> **Relacionado:** requisitos, comunicación `[05]`

---

## 1. Requisitos

**Funcionales — qué hace.** Acota agresivamente: *"¿Incluimos comentarios y likes, o me centro en publicar
y leer el feed?"* Es correcto y deseable dejar cosas fuera explícitamente.

**No funcionales — las que determinan la arquitectura.** Estas son las preguntas que separan a un senior:
- **Escala:** ¿usuarios activos al día? ¿lecturas vs escrituras? ¿picos?
- **Latencia objetivo:** ¿p99 de 100ms o de 2 segundos? Cambia todo el diseño.
- **Consistencia:** ¿el usuario debe ver su propio cambio al instante? ¿y los demás?
- **Disponibilidad:** ¿qué pasa si está caído 10 minutos? ¿es aceptable?
- **Durabilidad:** ¿se puede perder un dato? (Un "me gusta", quizá. Una transferencia, jamás.)
- **Multi-región, normativa, retención, coste.**

**La pregunta más rentable que puedes hacer:** *"¿Qué es lo que **no** puede fallar aquí?"* La respuesta te
dice dónde gastar consistencia y redundancia, y dónde puedes ser barato.

> **Ficha** · **Cuándo:** los primeros 5-8 minutos, siempre ·
> **Patrón:** funcionales acotados + no funcionales concretos (latencia, consistencia, escala) ·
> **Anti-patrón:** asumir requisitos en silencio ·
> **Límites:** sin números objetivo, ninguna decisión posterior se puede justificar ·
> **Cómo falla:** diseñas para 1M de usuarios cuando había 10.000, o al revés ·
> **Decisión:** la pregunta más rentable es **"¿qué es lo que NO puede fallar aquí?"** ·
> **Trade-off:** acotar (entregas algo completo) vs abarcar (cubres más, superficial) ·
> **Relacionado:** SLOs, consistencia `[10]`

---

## 2. Estimaciones (capacity planning)

No se trata de precisión, sino de **órdenes de magnitud que justifiquen decisiones**.

**Números de referencia que conviene tener memorizados:**
```
1 día ≈ 86.400 s ≈ 10^5 s        →  1M eventos/día ≈ 12/s  (mucho menos de lo que la gente cree)
1 millón de usuarios activos, 10 acciones/día ≈ 115 RPS de media
Pico ≈ 2-5× la media (o 10× si hay eventos puntuales)
1 KB por fila × 1.000M filas = 1 TB
Un Postgres bien afinado: miles de queries simples/s en una sola instancia
Redis: ~100.000 ops/s por nodo
Una NIC de 1 Gbps ≈ 125 MB/s
```

**El cálculo tipo:**
```
10M usuarios activos al día · 20 lecturas = 200M lecturas/día ≈ 2.300 RPS de media, ~10.000 en pico
Ratio lectura/escritura 100:1  →  ~23 escrituras/s  ← una sola primaria lo absorbe sin despeinarse
Almacenamiento: 200M posts/año · 2 KB = 400 GB/año
```

**La conclusión que más impresiona:** *"Con estos números, una sola instancia de Postgres con réplicas de
lectura sirve. No necesitamos sharding y me ahorro toda su complejidad."* Diseñar para una escala que no
tienes es el error más común y más caro — y reconocerlo demuestra criterio, no falta de ambición.

> **Ficha** · **Cuándo:** antes de elegir tecnología ·
> **Patrón:** órdenes de magnitud que **justifiquen** decisiones, no precisión ·
> **Anti-patrón:** saltar a sharding sin calcular si cabe en una instancia ·
> **Límites:** son estimaciones: dilo y pon el margen ·
> **Cómo falla:** 1M de eventos al día son 12/s — mucha gente los trata como si fueran miles ·
> **Decisión:** calcula el ratio lectura/escritura: decide caches y réplicas ·
> **Trade-off:** diseñar para 10× (prudente) vs para 100× (sobreingeniería) ·
> **Relacionado:** escalado, coste `[09, 13]`

---

## 3. API y modelo de datos

Define el contrato antes que la infraestructura: te fuerza a concretar el comportamiento.

```
POST /posts            {contenido}          → 201 {id}
GET  /feed?cursor=...&limit=20              → 200 {items, next_cursor}
POST /posts/{id}/likes                      → 204   (idempotente)
```

Luego las entidades, las relaciones y **el patrón de acceso dominante**, que es lo que decide el modelo:
*"El 99% del tráfico es leer el feed de un usuario, así que optimizo para eso aunque escribir sea más caro."*

Aquí se colocan las decisiones de `04-databases.md`: claves, índices, particionado y qué se desnormaliza.

> **Ficha** · **Cuándo:** antes de dibujar la infraestructura ·
> **Patrón:** definir el contrato fuerza a concretar el comportamiento ·
> **Anti-patrón:** elegir base de datos antes de saber el patrón de acceso ·
> **Límites:** el modelo condiciona todo lo demás y es lo más caro de cambiar ·
> **Cómo falla:** un modelo que no soporta la consulta dominante obliga a rediseñar entero ·
> **Decisión:** optimiza para el patrón de acceso que domina el tráfico ·
> **Trade-off:** normalizado vs desnormalizado según lectura/escritura ·
> **Relacionado:** data modeling, índices `[04]`

---

## 4. Diseño de alto nivel

```
Cliente → CDN → LB/API Gateway → Servicios (stateless)
                                     ├── Cache (Redis)
                                     ├── DB primaria + réplicas
                                     ├── Cola → Workers
                                     └── Object storage
```

Empieza simple y **evoluciona en voz alta**: *"Esto aguanta X. Cuando lleguemos a Y, el cuello de botella
será Z, y entonces añadiría W."* Esa narrativa vale más que dibujar la arquitectura final de golpe.

**Las piezas y cuándo las justificas:**
- **CDN** — estáticos y respuestas cacheables; latencia global.
- **Load balancer** — reparto y salud (`09-performance.md`).
- **Servicios stateless** — para poder escalar horizontal (`09-performance.md`).
- **Cache** — cuando el ratio lectura/escritura es alto (`09-performance.md`).
- **Cola** — cuando algo puede ser asíncrono o hay picos que absorber (`08-distributed-systems.md`).
- **Réplicas de lectura** — para descargar la primaria, aceptando lag.
- **Sharding** — solo cuando la escritura no cabe en una máquina.

> **Ficha** · **Cuándo:** el centro de la conversación ·
> **Patrón:** empezar simple y **evolucionar en voz alta** ("esto aguanta X; a Y el cuello será Z") ·
> **Anti-patrón:** dibujar la arquitectura final de una empresa madura desde el minuto uno ·
> **Límites:** cada pieza que añades es una que tendrás que justificar ·
> **Cómo falla:** añadir Kafka, Kubernetes y microservicios sin que ningún requisito los pida ·
> **Decisión:** justifica cada componente con el requisito que lo obliga ·
> **Trade-off:** simplicidad vs preparación para crecer ·
> **Relacionado:** arquitectura, componentes `[05]`

---

## 5. Profundizar: los patrones que se repiten

**Fan-out on write vs on read** (el clásico del feed/timeline):
- **On write (push):** al publicar, escribes en el timeline de cada seguidor. Lectura instantánea; escritura
  carísima para cuentas con millones de seguidores (*el problema de la celebridad*).
- **On read (pull):** al leer, consultas las publicaciones de a quién sigues y mezclas. Escritura barata,
  lectura cara.
- **Híbrido (la respuesta real):** push para usuarios normales, pull para las celebridades, mezclando en
  lectura. **Saber que la respuesta es híbrida es la señal.**

**Otros patrones recurrentes:**
- **Generación de IDs únicos distribuidos:** Snowflake (timestamp + máquina + secuencia) o UUIDv7 — ordenados
  en el tiempo, generables sin coordinación (`04-databases.md`).
- **Rate limiting distribuido:** token bucket en Redis (`03-apis.md`).
- **Búsqueda:** índice invertido aparte (Elasticsearch), alimentado por eventos desde la fuente de verdad.
  Nunca es la misma base de datos.
- **Notificaciones:** cola + workers + preferencias + deduplicación (`16-integrations.md`).
- **Deduplicación e idempotencia:** en todo lo que reintenta (`08-distributed-systems.md`).
- **Trabajos programados a escala:** una cola con tiempo de visibilidad, no un cron por servidor.

> **Ficha** · **Cuándo:** cuando el entrevistador elige un punto ·
> **Patrón:** fan-out híbrido, IDs distribuidos, rate limiting, búsqueda con índice aparte ·
> **Anti-patrón:** fan-out puro on-write sin considerar el problema de la celebridad ·
> **Límites:** cada patrón resuelve un caso y crea trabajo nuevo ·
> **Cómo falla:** una cuenta con 50M de seguidores hace inviable el fan-out on write ·
> **Decisión:** en feeds la respuesta casi siempre es **híbrida** ·
> **Trade-off:** coste en escritura vs coste en lectura ·
> **Relacionado:** caching, colas, sharding `[04, 08, 09]`

---

## 6. Cuellos de botella, fallos y coste

**Identifica el cuello de botella antes de que te lo pregunten.** *"Aquí el límite es la escritura en la
primaria; a partir de N escrituras/s habría que particionar por tenant."*

**Escenarios de fallo — recorre cada pieza:**

| Si cae... | ¿Qué pasa? ¿Cómo lo mitigo? |
|---|---|
| Una instancia de la app | el LB la saca; stateless, sin impacto |
| La cache | **thundering herd** contra la DB → single-flight, TTL con jitter, y dimensionar para sobrevivir un rato sin cache |
| La primaria | failover a una réplica; ventana de escrituras perdidas = replication lag |
| La cola | el productor debe encolar localmente o rechazar con gracia |
| Un servicio externo | breaker + fallback + degradación (`10-reliability.md`) |
| Una AZ entera | multi-AZ desde el principio |

**Y el coste**, que casi nadie menciona y siempre suma puntos: *"Esto son unos X € al mes; el 70% se va en
la base de datos. Si el coste fuera un problema, movería los datos fríos a almacenamiento barato con
lifecycle rules y bajaría la retención de logs."*

> **Ficha** · **Cuándo:** los últimos minutos, y anticípate ·
> **Patrón:** recorre cada pieza preguntando "¿qué pasa si esta cae?" ·
> **Anti-patrón:** presentar un diseño sin nombrar su límite ·
> **Límites:** no puedes eliminar los fallos, solo acotar su radio ·
> **Cómo falla:** si cae la cache, el 100% del tráfico va a la DB: hay que dimensionar para eso ·
> **Decisión:** menciona el coste aproximado y qué harías si fuera un problema ·
> **Trade-off:** redundancia vs coste ·
> **Relacionado:** degradación, thundering herd `[09, 10]`

---

## Cómo se comunica (lo que realmente puntúan)

- **Piensa en voz alta.** El silencio no se puede evaluar.
- **Da una recomendación, no un catálogo.** *"Usaría Postgres porque X"*, no *"podríamos usar Postgres,
  Mongo, Cassandra o DynamoDB"*.
- **Nombra el trade-off que estás aceptando.** Toda decisión tiene un coste; nombrarlo demuestra que sabes
  lo que estás comprando.
- **Acepta las pistas.** Si el entrevistador insiste en algo, es porque quiere verte ahí. No te aferres.
- **Corrígete si te equivocas.** Rectificar en voz alta es una señal positiva, no negativa.
- **Di lo que no sabes** y cómo lo averiguarías. Inventar se detecta al instante.

> **Ficha** · **Cuándo:** durante toda la entrevista ·
> **Patrón:** pensar en voz alta, recomendar en vez de listar, nombrar el trade-off que aceptas ·
> **Anti-patrón:** silencio largo, o enumerar cuatro opciones sin elegir ·
> **Límites:** no puedes saberlo todo; lo que se evalúa es cómo razonas cuando no lo sabes ·
> **Cómo falla:** inventar se detecta al instante y cuesta más que decir "no lo sé, lo comprobaría así" ·
> **Decisión:** acepta las pistas del entrevistador: señalan lo que quieren ver ·
> **Trade-off:** seguridad al afirmar vs honestidad sobre la incertidumbre ·
> **Relacionado:** trade-offs, ADRs `[05]`

---

## Decisiones: ADRs y cómo se justifican

Un diseño sin decisiones registradas es un diseño que nadie podrá cuestionar ni cambiar después, porque
nadie sabrá **por qué** es así.

**Architecture Decision Record** — media página, en el repo, junto al código:

```markdown
# ADR-014: Cursor pagination en la API de pedidos

## Estado
Aceptada · 2026-09-15 · Sustituye a ADR-006

## Contexto
La API pagina con OFFSET. Con 40M de pedidos, la pagina 2000 tarda 4s y los clientes
ven duplicados al insertarse filas mientras paginan.

## Opciones consideradas
1. Mantener OFFSET y limitar a 100 paginas — no resuelve los duplicados
2. Cursor/keyset sobre (creado_en, id) — rendimiento constante, sin saltar a pagina N
3. Precalcular paginas en Redis — complejidad y memoria altas para poco beneficio

## Decisión
Opción 2. El caso de uso real es scroll infinito; nadie salta a la pagina 2000.

## Consecuencias
+ Latencia constante sin importar la profundidad
+ Sin duplicados al insertar
- No se puede mostrar "pagina 7 de 340"; el back-office usará un endpoint aparte
- Breaking change: v1 mantiene OFFSET hasta su sunset (2027-03)
```

**Las tres partes que la gente se salta y son las importantes:** las **opciones descartadas** (para que
nadie repita el análisis), las **consecuencias negativas** (un ADR sin contras es marketing, no una
decisión), y la **fecha con estado** (para saber si sigue vigente).

**Cómo se justifica una decisión en voz alta**, que es lo que evalúan en la entrevista:

1. **¿Qué requisito no funcional la fuerza?** Latencia, consistencia, coste, cumplimiento `[05]`.
2. **¿Es reversible?** Gasta el análisis en las que no lo son (esquema de datos, shard key, lenguaje).
3. **¿Cuál es el coste de equivocarse y cómo lo detecto pronto?**
4. **¿Qué tendría que pasar para que cambiara de opinión?** Si no sabes responder, no has decidido: has
   elegido por defecto.

> **Ficha** · **Cuándo:** toda decisión cara de revertir ·
> **Patrón:** ADR corto en el repo, con opciones descartadas y consecuencias negativas ·
> **Anti-patrón:** decidir en una reunión y no dejar rastro ·
> **Límites:** un ADR documenta la decisión, no garantiza que fuera buena ·
> **Cómo falla:** dos años después nadie se atreve a cambiar algo porque nadie sabe por qué está así ·
> **Decisión:** distingue puertas de una vía (irreversibles) de las de dos vías ·
> **Trade-off:** tiempo de documentar vs coste de re-derivar el contexto más tarde ·
> **Relacionado:** trade-offs, arquitectura `[05]`

---

## Diagramas: qué dibujar y con qué nivel

**El modelo C4** da el vocabulario para no mezclar niveles, que es el error más común al dibujar:

| Nivel | Qué muestra | Para quién |
|---|---|---|
| **1 · Contexto** | tu sistema, sus usuarios y los sistemas externos | negocio y onboarding |
| **2 · Contenedores** | procesos desplegables: API, worker, DB, cola | **el nivel más útil a diario** |
| **3 · Componentes** | módulos dentro de un contenedor | al diseñar un servicio |
| **4 · Código** | clases | casi nunca merece la pena |

**Contenedores** — el que se dibuja en una entrevista:

```
                        ┌──────────┐
   navegador ──HTTPS──► │   CDN    │
                        └────┬─────┘
                             ▼
                      ┌─────────────┐        ┌──────────────┐
                      │ API (x3)    │───────►│ Postgres     │
                      │ FastAPI     │        │ primaria     │
                      └──┬───────┬──┘        └──────┬───────┘
                         │       │                  │ replicación
                    ┌────▼──┐ ┌──▼────┐      ┌──────▼───────┐
                    │ Redis │ │ Kafka │      │ réplica lect.│
                    └───────┘ └───┬───┘      └──────────────┘
                                  ▼
                            ┌──────────┐      ┌─────────┐
                            │ Workers  │─────►│   S3    │
                            └──────────┘      └─────────┘
```

**Diagrama de secuencia** — para flujos donde el **orden** y los fallos son lo importante (un cobro,
un login OAuth, una saga). Es el que de verdad explica un sistema asíncrono:

```
Cliente      API        Postgres     Stripe      Cola      Worker
  │  POST /pagos │           │          │          │          │
  ├─────────────►│  INSERT   │          │          │          │
  │              ├──────────►│ (intento pendiente) │          │
  │              ├───── create PaymentIntent ─────►│          │
  │              │           │  ◄── client_secret ─┤          │
  │ ◄── 201 ─────┤           │          │          │          │
  │                                     │          │          │
  │        webhook payment_intent.succeeded        │          │
  │              │◄──────────────────────┤          │          │
  │              ├── dedupe + transición ►│          │          │
  │              ├────── outbox ─────────────────►│          │
  │              │                                 ├─────────►│ enviar email
```

**Reglas para que un diagrama sirva:** una leyenda si usas formas distintas · las flechas indican
**quién inicia**, no por dónde van los datos · etiqueta el protocolo (HTTPS, gRPC, AMQP) · marca lo
**síncrono vs asíncrono**, que es la información que más se pierde · y máximo ~10 cajas por diagrama:
si no cabe, es que hacen falta dos niveles.

**Manténlos en el repo como texto** (Mermaid, PlantUML, D2) y no como imágenes sueltas: así se revisan
en la PR y no se quedan obsoletos en cuanto alguien cambia algo.

> **Ficha** · **Cuándo:** al diseñar, al hacer onboarding y en toda entrevista de sistema ·
> **Patrón:** C4 nivel 2 para la estructura, secuencia para los flujos con orden ·
> **Anti-patrón:** un único diagrama con 40 cajas mezclando infraestructura y clases ·
> **Límites:** un diagrama muestra estructura, no comportamiento bajo fallo ·
> **Cómo falla:** los diagramas como imagen se desactualizan en semanas y engañan más que ayudan ·
> **Decisión:** diagramas como texto versionado, revisados en la PR ·
> **Trade-off:** detalle vs legibilidad — un diagrama ilegible no comunica nada ·
> **Relacionado:** ADRs, arquitectura, onboarding `[05]`

---

## Preguntas de entrevista y trade-offs

**Q: Diseña un acortador de URLs.**
Lo esencial: generación de IDs (contador en base62 o hash con manejo de colisiones), lectura dominante
(ratio 100:1 o más → cache agresiva y CDN), redirección 301 vs 302 (**302 si quieres seguir contando
clics**; el 301 lo cachea el navegador y pierdes las analíticas), y almacenamiento key-value simple.
*Señal:* calculas que las escrituras son pocas y las lecturas muchísimas, y diseñas en consecuencia.

**Q: Diseña el feed de una red social.**
Fan-out híbrido, cache del timeline, paginación por cursor, y un límite explícito (*"solo los últimos 1.000
posts"*). *Señal:* identificas el problema de la celebridad por tu cuenta y propones el híbrido.

**Q: Diseña un sistema de chat.**
WebSocket con un backplane (Redis pub/sub) para que los usuarios conectados a réplicas distintas se vean,
persistencia de mensajes con orden por conversación, acuses de recibo, y presencia con TTL. *Señal:* hablas
del estado de las conexiones y de qué pasa en un despliegue (todos se reconectan a la vez: hace falta
reconexión escalonada).

**Q: Diseña un rate limiter distribuido.**
Token bucket en Redis con script Lua atómico, clave por usuario/API key, headers informativos y decisión
fail-open/fail-closed. *Señal:* explicas por qué no puede ser en memoria del proceso (cada réplica
permitiría el límite entero).

**Q: El sistema debe soportar 10× más tráfico el mes que viene. ¿Qué haces?**
Medir dónde está el límite actual, escalar lo stateless horizontalmente, cachear, mover trabajo a colas, y
solo entonces plantear cambios estructurales. *Señal:* empiezas midiendo en vez de rediseñando, y mencionas
una prueba de carga para encontrar el límite real antes de tocar nada (`11-testing.md`).

**Trade-off central de esta caja:** *diseñar para hoy vs diseñar para la escala imaginada*. El sobrediseño
mata más productos que el subdiseño: cuesta dinero, ralentiza al equipo y añade modos de fallo para un
tráfico que quizá nunca llegue. Lo que se valora es **diseñar para 10× el tráfico actual, dejando claro qué
cambiarías a 100×**.

---

## Fuentes

- [The System Design Primer](https://github.com/donnemartin/system-design-primer) — el repositorio de referencia.
- Jeff Dean, *Latency Numbers Every Programmer Should Know* — la base de toda estimación `[01]`.
- [C4 Model](https://c4model.com/) — niveles de diagrama sin mezclarlos.
- [ADR — Architecture Decision Records](https://adr.github.io/) · [Mermaid](https://mermaid.js.org/) para diagramas como texto.
- [5 Backend System Design Patterns Every Engineer Should Understand (2026)](https://medium.com/@naishasaxena2310/5-backend-system-design-patterns-every-engineer-should-actually-understand-3a9bfcb48115)
