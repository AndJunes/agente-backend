# 16 · Integrations

> Integrar con un tercero es **aceptar sus fallos como tuyos** a ojos del usuario. Todo lo de esta caja se
> reduce a una idea: *asume que el servicio externo va a fallar, va a ser lento y va a cambiar sin avisarte.*


**Cubre del temario:** `external_apis` · `webhooks` · `oauth` · `email` · `notifications` · `storage` · `implementations` · `failure_modes` · `tradeoffs`

---

## Principios para consumir APIs de terceros

**1. Envuélvelo en un adaptador.** Nunca llames al SDK de un proveedor desde tu lógica de negocio. Una
interfaz propia (`PasarelaDePago`, `EnviaEmails`) te permite cambiar de proveedor, testear sin red, y que
sus tipos raros no infecten tu dominio. Es el *anticorruption layer* de `05-architecture.md`.

**2. Timeout, retry con backoff, circuit breaker.** Siempre los tres (`10-reliability.md`). Un proveedor
lento sin timeout tumba tu servicio.

**3. Todo lo que no sea imprescindible para responder, va a una cola.** El usuario no debe esperar a que
tu proveedor de email responda para completar un registro.

**4. Idempotencia en las dos direcciones.** Manda idempotency keys y trata sus webhooks como duplicables.

**5. Cachea agresivamente lo que cambia poco** (catálogos, tipos de cambio, configuración) y ten un valor
por defecto para cuando no estén disponibles.

**6. Observa la integración como si fuera tuya:** métricas de latencia, error rate y cuota por proveedor,
con alertas propias. Cuando un proveedor se degrada, quieres enterarte tú antes que por Twitter.

**7. Aísla las credenciales por entorno** y ten claves de sandbox separadas. El incidente clásico es mandar
correos de prueba a clientes reales.

> **Ficha** · **Cuándo:** toda dependencia externa ·
> **Patrón:** adaptador propio + timeout + retry + breaker + métricas por proveedor ·
> **Anti-patrón:** llamar al SDK del proveedor desde la lógica de negocio ·
> **Límites:** aceptas sus fallos como tuyos a ojos del usuario ·
> **Cómo falla:** el proveedor cambia su API y tu dominio, acoplado a sus tipos, se rompe entero ·
> **Decisión:** lo que no sea imprescindible para responder, va a una cola ·
> **Trade-off:** capa de adaptación (horas hoy) vs reescritura el día que cambies de proveedor ·
> **Relacionado:** anticorruption layer, breakers `[05, 10]`

---

## Manejo de fallos de APIs externas

| Situación | Respuesta correcta |
|---|---|
| Timeout / 5xx | retry con backoff + jitter, breaker si persiste |
| 429 rate limited | respetar `Retry-After`, **encolar**, throttling propio |
| 4xx de validación | **no reintentar**; es un bug tuyo, loguea con contexto |
| 401/403 | refrescar credenciales una vez; si sigue, alerta (clave rotada o revocada) |
| Respuesta inesperada | validar contra un esquema y fallar de forma controlada |
| Proveedor caído del todo | degradar (`10-reliability.md`), encolar para después, o modo manual |

**Rate limiting propio hacia fuera:** si el proveedor te limita a 100 req/s, implementa tu propio token
bucket **antes** de llamar. Es mucho mejor auto-regularte que consumir tu cuota en reintentos y que te
bloqueen. Con varias réplicas, el contador va en Redis.

**El patrón de la cola de salida:** para operaciones no interactivas (sincronizar un CRM, enviar
notificaciones), no llames directamente: encola. Ganas reintentos, control de ritmo, visibilidad y
resistencia a caídas del proveedor, todo gratis.

> **Ficha** · **Cuándo:** al integrar cualquier proveedor ·
> **Patrón:** clasificar el error (transitorio / permanente / cuota) y responder distinto a cada uno ·
> **Anti-patrón:** reintentar un 400 de validación ·
> **Límites:** un timeout no te dice si la operación se ejecutó al otro lado ·
> **Cómo falla:** consumes tu cuota en reintentos y el proveedor te bloquea ·
> **Decisión:** implementa tu propio rate limit **antes** de llamar, no después de que te limiten ·
> **Trade-off:** auto-regularte (más lento) vs agotar la cuota ·
> **Relacionado:** rate limiting, idempotencia `[03, 08]`

---

## OAuth para integraciones (tú como cliente)

Cuando tu app accede a la cuenta de un usuario en otro servicio (Google Drive, Slack, GitHub):

- **Authorization Code + PKCE** (`06-security.md`). Guarda `access_token` (corto) y **`refresh_token`
  (largo y sensible: cifrado en la base de datos, nunca en logs)**.
- **Refresco:** renueva **antes** de que caduque, no cuando falle. Y protege contra el refresco concurrente
  (dos workers refrescando a la vez invalidan el token del otro): un lock o un `UPDATE ... RETURNING`
  atómico.
- **Revocación:** el usuario puede desconectar la app en cualquier momento. Maneja el 401 permanente:
  marca la conexión como rota y **pide al usuario que reconecte** en la UI, en vez de reintentar en bucle.
- **Scopes mínimos.** Pedir permisos de más reduce la conversión y aumenta el riesgo.
- **Multi-cuenta:** un usuario puede conectar dos cuentas del mismo proveedor. Modela la conexión como
  entidad propia desde el principio; reconvertirlo después es doloroso.

> **Ficha** · **Cuándo:** al acceder a la cuenta de un usuario en otro servicio ·
> **Patrón:** Authorization Code + PKCE; refresh proactivo con lock ·
> **Anti-patrón:** guardar el refresh token sin cifrar, o refrescar solo cuando falla ·
> **Límites:** el usuario puede revocar la conexión en cualquier momento ·
> **Cómo falla:** dos workers refrescan a la vez y se invalidan el token mutuamente — intermitente y dificilísimo de diagnosticar ·
> **Decisión:** ante un 401 permanente, marca la conexión rota y pide reconectar en la UI ·
> **Trade-off:** scopes amplios (menos fricción futura) vs mínimos (más confianza, menos riesgo) ·
> **Relacionado:** OAuth2, secrets `[06]`

---

## Webhooks entrantes (tú como receptor)

Es la otra mitad de `03-apis.md` y lo que más se pregunta en integraciones.

```python
@app.post("/webhooks/proveedor")
def recibir(request):
    verificar_firma(request.body_crudo, request.headers["X-Signature"])   # 1
    evento = json.loads(request.body_crudo)
    if ya_procesado(evento["id"]):                                        # 2
        return 200
    encolar(evento)                                                       # 3
    return 200                                                            # 4
```

1. **Verifica la firma HMAC sobre el body crudo** y comprueba el timestamp (anti-replay).
   Comparación en tiempo constante (`06-security.md`).
2. **Deduplica por ID de evento** — la entrega es at-least-once.
3. **Encola y procesa en background.**
4. **Responde 200 rápido** (segundos). Si tardas, el proveedor reintenta y te llegan duplicados en cascada.

**Además:**
- **Tolera el desorden**: los eventos pueden llegar en orden distinto al que ocurrieron. Basa la lógica en
  el estado, no en la secuencia.
- **Reconcilia periódicamente** con la API del proveedor: **los webhooks se pierden**. Un job que compara
  estados es tu red de seguridad.
- **Guarda el evento crudo** antes de procesarlo. Cuando algo salga mal, querrás reprocesar.
- **Endpoint público sin autenticación de usuario**: protégelo con rate limiting y no filtres información
  en los errores.

> **Ficha** · **Cuándo:** todo proveedor que te notifique eventos ·
> **Patrón:** firma → dedupe → encolar → 200 rápido, y conciliación periódica ·
> **Anti-patrón:** procesar de forma síncrona dentro del handler ·
> **Límites:** at-least-once, sin orden garantizado, y **los webhooks se pierden** ·
> **Cómo falla:** tardas en responder, el proveedor reintenta y te llegan duplicados en cascada ·
> **Decisión:** guarda el evento crudo antes de procesarlo, para poder reprocesar ·
> **Trade-off:** tiempo real (webhooks) vs fiabilidad (polling y conciliación) ·
> **Relacionado:** firmas HMAC, idempotencia `[06, 08]`

---

## Email

- **Proveedores:** SendGrid, Postmark, SES, Resend. **No montes tu propio SMTP**: la entregabilidad es un
  problema de reputación de IP que lleva años construir.
- **Entregabilidad (lo que separa a quien ha sufrido esto):** **SPF** (qué servidores pueden enviar por tu
  dominio), **DKIM** (firma criptográfica del mensaje) y **DMARC** (qué hacer si fallan y dónde reportar).
  Sin los tres, acabas en spam.
- **Transaccional vs marketing:** sepáralos en **dominios o subdominios distintos**. Si tu campaña de
  marketing quema la reputación, no quieres que se caigan los emails de recuperación de contraseña.
- **Bounces y quejas:** procesa los webhooks de rebote. Seguir enviando a direcciones que rebotan destruye
  tu reputación. Mantén una **lista de supresión** y respétala.
- **Asíncrono siempre**, con reintentos. Y **idempotencia**: guarda qué email se envió por qué evento, o un
  reintento del job manda tres copias al usuario.
- **Plantillas versionadas**, con texto plano además de HTML, y enlaces con tokens de un solo uso y caducidad.

> **Ficha** · **Cuándo:** verificación, recuperación, notificaciones, facturas ·
> **Patrón:** proveedor gestionado + SPF, DKIM y DMARC + dominios separados ·
> **Anti-patrón:** montar tu propio SMTP; mezclar transaccional y marketing en el mismo dominio ·
> **Límites:** la entregabilidad es reputación acumulada, no configuración ·
> **Cómo falla:** seguir enviando a direcciones que rebotan destruye tu reputación ·
> **Decisión:** procesa los webhooks de rebote y mantén lista de supresión ·
> **Trade-off:** un dominio (simple) vs separados (protege lo crítico) ·
> **Relacionado:** colas, idempotencia `[08]`

---

## SMS y push

**SMS** (Twilio, MessageBird):
- Caro por mensaje y con reglas por país (remitentes registrados, plantillas aprobadas, horarios permitidos).
- **Fraude de bombeo de SMS (*SMS pumping*):** un atacante abusa de tu "enviar código" para generar tráfico
  a números premium y te vacía el presupuesto. **Rate limiting por número, por IP y por cuenta, geo-bloqueo
  y CAPTCHA** son obligatorios en cualquier endpoint que dispare un SMS.
- No sirve para MFA de alta seguridad (SIM swapping), pero sigue siendo el más accesible.

**Push** (APNs para iOS, FCM para Android):
- Los tokens de dispositivo **caducan y se invalidan**: procesa las respuestas de baja y limpia, o
  desperdicias cuota enviando a dispositivos muertos.
- Un usuario tiene varios dispositivos; modela `usuario → N tokens`.
- **No metas datos sensibles en el payload**: se ve en la pantalla bloqueada.
- Respeta preferencias y horarios: el push es el canal más fácil de quemar.

**Regla transversal de notificaciones:** centraliza en un **servicio de notificaciones** con preferencias
por usuario y canal, plantillas, deduplicación y agrupación (*digest*). Si cada módulo envía por su cuenta,
acabas mandando cinco notificaciones del mismo evento.

> **Ficha** · **Cuándo:** verificación, alertas, notificaciones móviles ·
> **Patrón:** rate limiting multinivel (número, IP, cuenta) y control de gasto ·
> **Anti-patrón:** un endpoint "enviar código" sin límites ·
> **Límites:** reglas por país, remitentes registrados, tokens de push que caducan ·
> **Cómo falla:** **SMS pumping** — fraude que genera tráfico a números premium y vacía tu presupuesto ·
> **Decisión:** limpia los tokens de push inválidos o desperdicias cuota en dispositivos muertos ·
> **Trade-off:** fricción (CAPTCHA, límites) vs coste del fraude ·
> **Relacionado:** rate limiting, coste `[03, 13]`

---

## Maps, social login y almacenamiento en la nube

**Maps** (Google Maps, Mapbox): **cachea agresivamente** — geocodificar la misma dirección mil veces es tirar
dinero (y a menudo lo prohíben sus términos, que a veces restringen el almacenamiento de resultados: léelos).
Vigila la cuota, ten un plan para cuando se agote, y no metas la API key con permisos amplios en el cliente.

**Social login** (Google, Apple, GitHub): usa **OIDC**, valida el `id_token` contra el JWKS, y decide la
política de **vinculación de cuentas** — si alguien se registró con email y luego entra con Google usando el
mismo email, ¿es la misma cuenta? **Vincular automáticamente por email es un vector de apropiación de
cuentas si el proveedor no verifica el email** (comprueba el claim `email_verified`). "Sign in with Apple"
además puede ocultar el email real con un relay.

**Cloud storage del usuario** (Drive, Dropbox): APIs con cuotas agresivas, paginación por cursor y webhooks
de cambios con su propio modelo. Sincronizar bidireccionalmente es un problema de consistencia distribuida
con conflictos reales — subestimarlo es un error clásico de planificación.

**CRMs y analytics** (Salesforce, HubSpot, Segment): límites de API bajos, así que **batching y colas**.
Y cuidado con enviar PII a herramientas de analítica: es un asunto legal, no solo técnico.

> **Ficha** · **Cuándo:** integraciones de producto habituales ·
> **Patrón:** cachear resultados caros (geocoding) y validar `email_verified` en social login ·
> **Anti-patrón:** **vincular cuentas por email automáticamente** sin comprobar que el proveedor lo verificó ·
> **Límites:** algunos términos de servicio restringen almacenar resultados: léelos ·
> **Cómo falla:** apropiación de cuenta si alguien registra un proveedor con un email ajeno no verificado ·
> **Decisión:** define desde el principio la política de vinculación de cuentas ·
> **Trade-off:** conveniencia del usuario vs riesgo de apropiación ·
> **Relacionado:** OIDC, coste de cuotas `[06]`

---

## Diseñar una capa de integración que envejezca bien

```
dominio  →  interfaz propia  →  adaptador  →  cliente HTTP con políticas  →  proveedor
                                                (timeout, retry, breaker,
                                                 rate limit, métricas, logs)
```

- **Un cliente HTTP compartido con las políticas ya puestas**, para no depender de que cada dev se acuerde.
- **Registro de proveedores y feature flags** para poder cambiar de proveedor o apagarlo en caliente.
- **Modo sandbox / fake** para desarrollo y tests, seleccionable por configuración.
- **Guarda las peticiones y respuestas** (redactadas) de las integraciones críticas: cuando el proveedor
  diga "nosotros no recibimos eso", tú tendrás la evidencia.
- **Contrato verificado periódicamente** (`11-testing.md`): un test programado contra el sandbox real detecta
  cambios del proveedor antes que tus usuarios.

> **Ficha** · **Cuándo:** desde la segunda integración ·
> **Patrón:** cliente HTTP compartido con las políticas puestas + modo fake para tests ·
> **Anti-patrón:** que cada integración implemente sus propios reintentos a su manera ·
> **Límites:** guardar peticiones y respuestas ocupa espacio: redacta y pon retención ·
> **Cómo falla:** el proveedor dice "nosotros no recibimos eso" y no tienes evidencia ·
> **Decisión:** guarda request/response redactados de las integraciones críticas ·
> **Trade-off:** abstracción común vs usar funciones específicas de cada proveedor ·
> **Relacionado:** adaptadores, contract testing `[05, 11]`

---

## Cómo falla una integración

| Fallo | Síntoma | Mitigación |
|---|---|---|
| **Proveedor caído** | errores en cascada en tu API | breaker + fallback + cola `[10]` |
| **Proveedor lento** | tus workers agotados | timeout agresivo (lento es peor que caído) |
| **Rate limit** | 429 masivos | throttling propio antes de llamar |
| **Cuota agotada** | fallos a mitad de mes | alertas de consumo, plan de degradación |
| **Webhook perdido** | estado desincronizado en silencio | conciliación periódica |
| **Webhook duplicado** | efecto aplicado dos veces | dedupe por `event_id` |
| **Token revocado** | 401 permanente en bucle | marcar conexión rota, pedir reconexión |
| **Refresco concurrente** | desconexiones intermitentes | lock o update atómico al refrescar |
| **Cambio de API sin avisar** | errores de parseo nuevos | validación de esquema + test de contrato programado |
| **Deprecación** | funciona hasta que deja de funcionar | vigilar avisos y headers `Sunset` `[03]` |
| **Datos inesperados** | campos nulos que "nunca" lo son | validar la respuesta, no confiar |

**La regla que resume la caja:** *trata a todo proveedor como si fuera a fallar hoy.* Las tres defensas que
más incidentes evitan son el **timeout** (que impide que te arrastre), la **cola** (que absorbe su caída)
y la **conciliación** (que detecta lo que se perdió sin que nadie lo notara).

**Presupuesto de fiabilidad heredado:** tu disponibilidad no puede superar la de las dependencias que
están en tu camino crítico. Si tu pasarela de pagos promete 99,9% y la llamas de forma síncrona en el
checkout, tu checkout **no puede** ser más fiable que eso — salvo que lo hagas asíncrono o tengas
alternativa (`[10]`).

> **Ficha** · **Cuándo:** al añadir cualquier proveedor al camino crítico ·
> **Patrón:** calcular la fiabilidad heredada y decidir si esa dependencia puede ser síncrona ·
> **Anti-patrón:** prometer un SLO mejor que el de tus dependencias síncronas ·
> **Límites:** no controlas su disponibilidad, solo tu reacción ·
> **Cómo falla:** una caída de un tercero se convierte en una caída tuya a ojos del usuario ·
> **Decisión:** ¿puede esperar? Entonces cola. ¿No? Entonces necesita fallback ·
> **Trade-off:** funcionalidad rica (más dependencias) vs fiabilidad ·
> **Relacionado:** SLOs, degradación, colas `[08, 10]`

---

## Preguntas de entrevista y trade-offs

**Q: Tu proveedor de pagos empieza a tardar 20 segundos. ¿Qué pasa y qué haces?**
Sin timeout, agoto workers y caigo. Con timeout + breaker, fallo rápido, encolo el intento y muestro
"procesando" al usuario. *Señal:* mencionas que después habrá que reconciliar, porque algunas de esas
llamadas con timeout **sí se ejecutaron** en el proveedor: de ahí la idempotency key.

**Q: ¿Cómo garantizas no procesar dos veces un webhook?**
Firma + deduplicación por `event.id` en la misma transacción que el efecto + lógica idempotente.
*Señal:* añades que hay que tolerar el desorden y que la reconciliación periódica cubre los eventos perdidos,
que es la parte que casi nadie menciona.

**Q: Un usuario dice que no recibe tus emails. ¿Por dónde empiezas?**
Estado en el proveedor (entregado, rebotado, marcado como spam), lista de supresión, y configuración de
SPF/DKIM/DMARC del dominio. *Señal:* hablas de reputación de IP/dominio y de separar transaccional de
marketing — demuestra experiencia real.

**Q: ¿Cómo guardas los refresh tokens de OAuth de tus usuarios?**
Cifrados en la base de datos (a nivel de campo), nunca en logs, con refresco proactivo y manejo del caso
"revocado por el usuario". *Señal:* mencionas el refresco concurrente como bug real, que rompe la conexión
de forma intermitente y es dificilísimo de diagnosticar.

**Q: ¿Cómo evitas que te vacíen el presupuesto de SMS?**
Rate limiting multinivel (número, IP, cuenta), geo-restricciones, CAPTCHA y alertas de gasto. *Señal:*
conoces el término *SMS pumping* y que es un fraude activo, no una hipótesis.

**Trade-off central de esta caja:** *acoplamiento vs velocidad de entrega*. Usar el SDK del proveedor
directamente es rapidísimo hoy y carísimo el día que cambies, falle o cambien su API. La capa de adaptación
cuesta unas horas al principio y es lo que te permite sobrevivir a la deprecación, a la caída y a la
renegociación de precios sin reescribir el producto.

---

## Fuentes

- [Stripe — Webhooks best practices](https://docs.stripe.com/webhooks/best-practices) y [GitHub — Securing webhooks](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- [RFC 9700 — OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html)
- [SPF, DKIM y DMARC](https://www.rfc-editor.org/rfc/rfc7489.html) — entregabilidad de correo.
- [Twilio — SMS pumping fraud](https://www.twilio.com/docs/verify/preventing-toll-fraud)
- [AWS Builders' Library — Avoiding fallback in distributed systems](https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/)
