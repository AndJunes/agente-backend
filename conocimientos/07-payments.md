# 07 · Payments

> Aquí los bugs se miden en dinero real y en llamadas de clientes enfadados. La regla que lo gobierna todo:
> **nunca confíes en el cliente, el estado lo manda el webhook, y todo debe ser idempotente.**


**Cubre del temario:** `concepts` · `providers` · `checkout` · `subscriptions` · `webhooks` · `refunds` · `implementations` · `state_machines` · `failure_modes` · `constraints` · `tradeoffs`

---

## Cómo funciona un pago por dentro

```
Comprador → Merchant (tú) → PSP (Stripe) → Adquirente → Red (Visa) → Emisor (banco del comprador)
```

**Dos fases que hay que distinguir siempre:**

1. **Autorización** — el banco reserva el importe y devuelve un código. El dinero **no se ha movido**.
   La reserva caduca (típicamente ~7 días).
2. **Captura** — reclamas el dinero autorizado. Puede ser inmediata (lo normal en e-commerce digital) o
   diferida (envías el producto y capturas al expedir: es el modelo correcto para bienes físicos).
3. **Settlement / payout** — días después, el dinero llega a tu cuenta, agrupado y menos comisiones. **La
   fecha del pago y la fecha del ingreso no coinciden nunca**, y por eso la conciliación es un problema real.

**Conceptos que debes manejar:** 3D Secure / SCA (autenticación del titular; **obligatoria en Europa por
PSD2**, y añade un paso interactivo que tu flujo debe soportar), autorización parcial, reintentos por
`insufficient_funds`, y *network tokens*.

> **Ficha** · **Cuándo:** antes de escribir la primera línea de integración ·
> **Patrón:** distinguir siempre autorización (reserva) de captura (cobro) y de liquidación (ingreso) ·
> **Anti-patrón:** capturar al autorizar cuando envías bienes físicos días después ·
> **Límites:** la autorización caduca (~7 días); la liquidación llega días más tarde y agrupada ·
> **Cómo falla:** la fecha del pago y la del ingreso nunca coinciden → conciliación descuadrada ·
> **Decisión:** digital → captura inmediata; físico → captura al expedir ·
> **Trade-off:** capturar pronto (menos impagos) vs capturar al enviar (menos reembolsos y disputas) ·
> **Relacionado:** state machines, conciliación `[17]`

---

## Stripe: el modelo mental

**PaymentIntent** es el objeto central: representa **la intención de cobrar** y sobrevive a los reintentos,
a la autenticación 3DS y a los fallos. Es una máquina de estados:

```
requires_payment_method → requires_confirmation → requires_action (3DS)
   → processing → succeeded
                └→ canceled
```

**Los dos caminos de integración:**
- **Checkout Session** (hosted): Stripe pone la página. Menos control, **muchísima menos superficie PCI**,
  y es lo recomendado por defecto en 2026.
- **Payment Element + PaymentIntent** (embebido): tú controlas la UI, los datos de tarjeta nunca tocan tu
  servidor (van directos a Stripe vía JS).

**Objetos que debes conocer:** `Customer`, `PaymentMethod`, `SetupIntent` (guardar tarjeta sin cobrar),
`Invoice`, `Subscription`, `Price`/`Product`, `Refund`, `Dispute`, `Payout`, `Event`.

**Otros PSP:** **Mercado Pago** domina LatAm (Preferences + webhooks IPN, y métodos locales como PIX,
OXXO, boleto, con flujos **asíncronos** donde el usuario paga horas después). **PayPal** usa orders +
capture. El modelo mental es el mismo: intención → autorización → captura → webhook como fuente de verdad.

> **Ficha** · **Cuándo:** al elegir profundidad de integración ·
> **Patrón:** Checkout hosted por defecto; Payment Element si necesitas controlar la UI ·
> **Anti-patrón:** montar tu propio formulario de tarjeta y multiplicar el alcance PCI ·
> **Límites:** el PaymentIntent es la fuente de verdad del **cobro**; tu sistema lo es del **acceso** ·
> **Cómo falla:** guardar solo "pagado: sí" pierde el estado real (requires_action, processing) ·
> **Decisión:** guarda `customer_id`, `subscription_id` y estado; no llames a la API en cada request ·
> **Trade-off:** control de la experiencia vs superficie de cumplimiento ·
> **Relacionado:** PCI, checkout `[06]`

---

## La regla de oro: el webhook es la fuente de verdad

**Nunca marques un pedido como pagado porque el navegador volvió a tu `success_url`.** El usuario puede
cerrar la pestaña, perder la conexión, o falsear la vuelta. El redirect es UX; **el webhook es el hecho.**

```python
@app.post("/webhooks/stripe")
def webhook(request):
    # 1) VERIFICAR LA FIRMA sobre el body CRUDO (ver 06-security.md)
    evento = stripe.Webhook.construct_event(request.body_crudo,
                                            request.headers["Stripe-Signature"],
                                            WEBHOOK_SECRET)
    # 2) DEDUPLICAR: at-least-once significa que este evento puede llegar dos veces
    if ya_procesado(evento["id"]):
        return 200
    # 3) Responder rápido: encolar y procesar en background
    encolar(evento)
    marcar_procesado(evento["id"])
    return 200
```

**Los cinco mandamientos del webhook de pagos:**
1. **Verifica la firma** siempre, sobre el body crudo.
2. **Deduplica por `event.id`** — la entrega es at-least-once, los duplicados están garantizados.
3. **Responde 200 en segundos.** Si tardas, el PSP reintenta y te llegan duplicados en cascada.
   Encola y procesa asíncronamente.
4. **Tolera desorden.** `payment_intent.succeeded` puede llegar *antes* que `checkout.session.completed`.
   Tu lógica debe basarse en el estado del objeto, no en el orden de llegada.
5. **Reconcilia igualmente.** Un job periódico que compara tus pedidos pendientes con el estado real en la
   API del PSP te salva de los webhooks perdidos. **Los webhooks fallan; la reconciliación es tu red.**

**Eventos que realmente importan:** `checkout.session.completed`, `payment_intent.succeeded`,
`payment_intent.payment_failed`, `invoice.paid`, `invoice.payment_failed`,
`customer.subscription.created/updated/deleted`, `charge.refunded`, `charge.dispute.created`.

> **Ficha** · **Cuándo:** siempre; es el error de diseño más caro de esta caja ·
> **Patrón:** verificar firma → deduplicar por `event.id` → encolar → responder 200 rápido ·
> **Anti-patrón:** marcar el pedido como pagado en el `success_url` del navegador ·
> **Límites:** entrega **at-least-once** y **sin orden garantizado** ·
> **Cómo falla:** el usuario cierra la pestaña tras pagar y el pedido se queda sin confirmar ·
> **Decisión:** basa la lógica en el estado del objeto, nunca en la secuencia de eventos ·
> **Trade-off:** confiar solo en webhooks (correcto, asíncrono) vs UX inmediata ·
> **Relacionado:** webhooks, idempotencia, conciliación `[03, 08, 16]`

---

## Idempotencia en pagos

**Doble capa, las dos obligatorias:**

- **Hacia el PSP:** manda `Idempotency-Key` en todos los POST (Stripe la soporta y la recomienda). Si la red
  falla y no sabes si el cobro ocurrió, **reintenta con la misma clave**: o te devuelve el resultado original
  o ejecuta una sola vez. Sin esto, un timeout = riesgo de cobrar dos veces.
- **Hacia dentro:** tu propio endpoint de "pagar" necesita su idempotency key (ver `03-apis.md`), insertada
  en la misma transacción que la operación.

**La clave debe derivar de la intención del negocio** (por ejemplo `pedido_id + intento`), no ser un UUID
nuevo en cada reintento — si generas una clave nueva al reintentar, la idempotencia no sirve de nada.

> **Ficha** · **Cuándo:** en toda llamada que mueva dinero, en ambas direcciones ·
> **Patrón:** clave derivada de la intención (`pedido_id`), en la misma transacción que el efecto ·
> **Anti-patrón:** generar un UUID nuevo en cada reintento — anula la protección por completo ·
> **Límites:** protege dentro de la ventana de retención de la clave (24 h - 7 días) ·
> **Cómo falla:** un timeout sin idempotency key deja un cobro en estado desconocido ·
> **Decisión:** ante un timeout, **reintenta con la misma clave**; nunca asumas que falló ·
> **Trade-off:** una escritura extra por operación a cambio de no cobrar dos veces ·
> **Relacionado:** idempotencia, retries `[03, 08]`

---

## Modelar el estado: máquinas de estado, no booleanos

El error más caro de esta caja es `pedido.pagado = True`. Usa estados explícitos y **transiciones legales**:

```
Pedido:    borrador → pendiente_pago → pagado → preparando → enviado → entregado
                            ↓            ↓
                        cancelado    reembolsado

Pago:      iniciado → autorizado → capturado → liquidado
                 ↓         ↓            ↓
              fallido   expirado    reembolsado/disputado
```

**Reglas:**
- Cada transición se **valida** (`de_estado → a_estado` permitido) y se **registra** con timestamp, actor y
  motivo. Eso es tu audit log y tu soporte al cliente.
- **Nunca borres ni sobrescribas** un registro de pago. Corrige con un registro nuevo (como en contabilidad:
  los asientos se compensan, no se borran).
- El estado del pedido y el del pago son **máquinas separadas** que se sincronizan por eventos.

> **Ficha** · **Cuándo:** pedido, pago, suscripción, envío, devolución ·
> **Patrón:** transiciones legales validadas + registro de cada cambio con actor y motivo ·
> **Anti-patrón:** `pedido.pagado = True`; tres booleanos permiten ocho estados, cinco imposibles ·
> **Límites:** el estado del pedido y el del pago son máquinas **distintas** que se sincronizan por eventos ·
> **Cómo falla:** dos webhooks simultáneos aplican la misma transición dos veces ·
> **Decisión:** transición atómica — `UPDATE ... WHERE estado = 'anterior'` y comprobar filas afectadas ·
> **Trade-off:** rigidez del modelo vs estados inválidos imposibles ·
> **Relacionado:** state machines, audit logs `[17]`

---

## Dinero: cómo se representa

- **Enteros en la unidad mínima** (céntimos) o `DECIMAL` con escala fija. **Jamás float.**
- **Guarda siempre la divisa** junto al importe. Un `total: 1000` sin divisa es un bug esperando.
  Ojo: hay divisas con **cero decimales** (JPY, CLP) y con tres (KWD/BHD) — asumir "×100" siempre es un bug.
- **Redondeo:** define la política (half-up, banker's) y aplícala en un solo sitio. Nunca redondees en medio
  de una cadena de cálculos.
- **Nunca sumes importes de divisas distintas.** Un value object `Dinero(importe, divisa)` que lo impida en
  el constructor elimina toda esta familia de errores.
- **Tipos de cambio:** guarda la tasa y el momento usados en cada transacción. "Recalcular con la tasa de
  hoy" cambia el histórico y destroza la contabilidad.

> **Ficha** · **Cuándo:** en el primer commit que toque importes ·
> **Patrón:** value object `Dinero(importe_entero, divisa)` que impide sumar divisas distintas ·
> **Anti-patrón:** `FLOAT`, e importes sin divisa ·
> **Límites:** hay divisas con **cero decimales** (JPY, CLP) y con tres (KWD): "×100" no siempre vale ·
> **Cómo falla:** errores de redondeo que descuadran la contabilidad de forma imperceptible ·
> **Decisión:** congela el tipo de cambio usado en la transacción; nunca recalcules el histórico ·
> **Trade-off:** un tipo propio es más verboso y elimina una familia entera de bugs ·
> **Relacionado:** data modeling, facturación `[04, 17]`

---

## Subscriptions & billing

**Conceptos:** `Product` (qué vendes) → `Price` (cuánto y cada cuánto) → `Subscription` (quién lo tiene) →
`Invoice` (el cobro de un periodo) → `PaymentIntent` (el intento de cobro de esa factura).

**Lo difícil no es cobrar, es el ciclo de vida:**
- **Proration (prorrateo):** si suben de plan a mitad de mes, se cobra la diferencia proporcional. Si bajan,
  normalmente se aplica al siguiente periodo o se genera saldo a favor. **Deja que el PSP lo calcule**, esta
  aritmética tiene más casos límite de los que crees.
- **Trials:** con o sin tarjeta; qué pasa al acabar; recordatorio obligatorio en algunas jurisdicciones.
- **Dunning:** la gestión del fallo de cobro. Las tarjetas caducan y fallan constantemente
  (**es la principal causa de churn involuntario**). Secuencia: reintentos inteligentes escalonados
  (día 1, 3, 5, 7), emails al cliente, *grace period* con servicio activo, y por fin suspensión.
- **Upgrades/downgrades/pausa/cancelación**: ¿inmediata o a fin de periodo? ¿Se reembolsa? Decide, documéntalo
  y modélalo; no lo improvises en un `if`.

**La regla arquitectónica:** el PSP tiene la verdad del **cobro**; tu sistema tiene la verdad del **acceso**.
Guarda `stripe_customer_id`, `subscription_id`, estado y fecha de fin de periodo, y **decide el acceso con
tus datos** (actualizados por webhook), no llamando a la API de Stripe en cada request.

> **Ficha** · **Cuándo:** cualquier modelo recurrente ·
> **Patrón:** el PSP calcula el prorrateo; tú guardas estado y fin de periodo para decidir el acceso ·
> **Anti-patrón:** implementar el prorrateo a mano ·
> **Límites:** las tarjetas caducan y fallan constantemente ·
> **Cómo falla:** el **churn involuntario** por fallo de cobro es la principal fuga de ingresos ·
> **Decisión:** dunning con reintentos escalonados, avisos y periodo de gracia antes de suspender ·
> **Trade-off:** cortar rápido (protege ingresos) vs periodo de gracia (retiene clientes) ·
> **Relacionado:** webhooks, permisos de acceso `[17]`

---

## Refunds, chargebacks y disputas

- **Refund (reembolso):** tú devuelves el dinero voluntariamente. Total o parcial. Tarda días en llegar al
  cliente — comunícalo o tendrás tickets de soporte.
- **Chargeback / dispute:** el cliente reclama a **su banco**. Es un proceso adversarial: te retiran el
  dinero *y* una comisión, y tienes un plazo para presentar evidencia (recibos, logs de entrega, IP, ToS
  aceptados). **Por eso guardas trazas de todo.**
- **Ratio de disputas:** si supera cierto umbral (~0,75-1%), la red te puede penalizar o expulsar.
- **Escuchar `charge.dispute.created`** y reaccionar (suspender el servicio, abrir un caso interno) es parte
  del diseño, no un extra.

> **Ficha** · **Cuándo:** desde el día uno; llegarán ·
> **Patrón:** escuchar `charge.dispute.created` y reaccionar automáticamente ·
> **Anti-patrón:** no guardar evidencia (logs de entrega, IP, aceptación de términos) ·
> **Límites:** la disputa la resuelve el banco, no tú; hay plazo para aportar pruebas ·
> **Cómo falla:** superar el ~0,75-1% de ratio de disputas puede costarte la cuenta con la red ·
> **Decisión:** un reembolso voluntario suele salir más barato que perder una disputa ·
> **Trade-off:** política de reembolso generosa (menos disputas, más coste directo) ·
> **Relacionado:** audit logs, evidencia `[17]`

---

## Carritos, pedidos e inventario

**Carrito:** efímero, puede vivir en Redis con TTL. **Los precios se recalculan en el servidor al hacer
checkout** — nunca confíes en el precio que manda el cliente. (Manipular el precio en el request es el
ataque más antiguo del e-commerce y sigue funcionando en sitios reales.)

**Pedido:** inmutable una vez confirmado. Guarda un **snapshot** de lo comprado (nombre, precio, impuestos
en ese momento). Si mañana cambias el precio del producto, la factura antigua no puede cambiar.

**Inventario y la condición de carrera clásica:**
```sql
-- MAL: comprobar y luego actualizar (dos usuarios pueden pasar el check a la vez)
SELECT stock FROM productos WHERE id = 1;     -- 1
UPDATE productos SET stock = stock - 1 ...;   -- se vende dos veces

-- BIEN: condición atómica, y el resultado dice si lo lograste
UPDATE productos SET stock = stock - 1
WHERE id = 1 AND stock >= 1;                  -- 0 filas afectadas = sin stock
```
Para carritos y ventas flash: **reserva con TTL** (restas al añadir, liberas si no paga en N minutos) y
un job que expira reservas. Con mucha concurrencia sobre un mismo SKU, el lock optimista y los reintentos
funcionan mejor que un lock pesimista que serializa a todos los compradores.

> **Ficha** · **Cuándo:** e-commerce y cualquier recurso limitado ·
> **Patrón:** `UPDATE stock = stock - 1 WHERE id = $1 AND stock >= 1` y comprobar filas afectadas ·
> **Anti-patrón:** `SELECT` y luego `UPDATE` — check-then-act es una race condition ·
> **Límites:** las reservas necesitan TTL y un job que las expire ·
> **Cómo falla:** **vender más stock del que tienes** en una venta flash ·
> **Decisión:** el precio se recalcula **siempre** en el servidor al hacer checkout ·
> **Trade-off:** lock pesimista (serializa a los compradores) vs optimista con reintentos ·
> **Relacionado:** transacciones, inventario `[04, 17]`

---

## Taxes, cupones y pricing

- **Impuestos:** dependen del **tipo de producto y de la jurisdicción del comprador**, y en la UE el IVA
  digital B2C se aplica en el país del cliente (con validación de VAT para el reverse charge B2B). No lo
  implementes a mano: Stripe Tax, Avalara o TaxJar. Guarda **qué tasa se aplicó y por qué** en el pedido.
- **Precio con o sin impuestos incluidos** es una decisión de producto que afecta a todos los cálculos.
- **Cupones:** valida en servidor — vigencia, usos máximos (globales y por usuario), acumulación,
  aplicabilidad a productos concretos y mínimo de compra. **El uso debe consumirse atómicamente** o un
  cupón de un solo uso se canjea mil veces en paralelo.
- **Pricing:** por unidad, escalonado (tiers), por volumen, por uso medido (metered), freemium. El **modelo
  por uso** obliga a agregar eventos de consumo de forma fiable e idempotente — es un problema de sistemas
  distribuidos disfrazado de facturación.

> **Ficha** · **Cuándo:** antes de vender en más de un país ·
> **Patrón:** delegar el cálculo fiscal (Stripe Tax, Avalara) y **guardar la tasa aplicada** ·
> **Anti-patrón:** implementar IVA por país a mano ·
> **Límites:** en la UE el IVA digital B2C se aplica en el país del cliente; B2B cambia con VAT válido ·
> **Cómo falla:** un cupón de un solo uso se canjea mil veces en paralelo sin consumo atómico ·
> **Decisión:** el uso del cupón se consume en la misma transacción que el pedido ·
> **Trade-off:** motor externo (correcto, coste por transacción) vs propio (barato, riesgo fiscal) ·
> **Relacionado:** business rules, transacciones `[04, 17]`

---

## PCI DSS y cumplimiento

- **Si los datos de tarjeta nunca tocan tu servidor** (Stripe Elements, Checkout hosted), caes en el
  cuestionario más simple (SAQ A) y te ahorras una auditoría cara. **Esta es la razón técnica y económica de
  usar el widget del PSP.**
- **Nunca guardes el PAN completo, el CVV (jamás, ni cifrado) ni la banda.** Guarda el `payment_method_id`
  del PSP, los últimos 4 dígitos y la marca — suficiente para la UI.
- **Loguea con cuidado:** un log del request completo puede acabar conteniendo un número de tarjeta.
- **Retención:** facturas y registros contables tienen plazos legales de conservación (varios años), que
  chocan con "borrar todo" del RGPD. La solución habitual: anonimizar datos personales pero conservar el
  registro financiero.

> **Ficha** · **Cuándo:** antes de decidir cómo capturas la tarjeta ·
> **Patrón:** los datos de tarjeta **nunca** tocan tu servidor → SAQ A ·
> **Anti-patrón:** guardar el PAN; guardar el CVV es una violación grave, cifrado o no ·
> **Límites:** la retención contable (años) choca con el derecho al borrado del RGPD ·
> **Cómo falla:** un log del request completo acaba conteniendo un número de tarjeta ·
> **Decisión:** guarda `payment_method_id`, últimos 4 y marca; nada más ·
> **Trade-off:** control de UX vs coste de auditoría y riesgo legal ·
> **Relacionado:** cumplimiento, logs, retención `[06, 15]`

---

## Implementación: el flujo completo de un cobro

```python
# 1) INICIAR: creamos la intencion y la guardamos ANTES de llamar al proveedor.
async def iniciar_pago(pedido_id: str, actor: Usuario) -> str:
    async with uow.transaccion() as tx:
        pedido = await tx.pedidos.bloquear(pedido_id)          # SELECT ... FOR UPDATE
        if pedido.estado != "pendiente_pago":
            raise TransicionInvalida(pedido.estado)

        intento = await tx.pagos.crear(pedido_id=pedido.id, estado="iniciado",
                                       importe=pedido.total, divisa=pedido.divisa)
        # la clave de idempotencia se DERIVA del negocio, no es un uuid nuevo
        clave = f"pago:{pedido.id}:{intento.numero_de_intento}"

    pi = await stripe.PaymentIntent.create(                     # fuera de la transaccion
        amount=pedido.total.centimos, currency=pedido.divisa.lower(),
        metadata={"pedido_id": pedido.id, "tenant_id": actor.tenant_id},
        idempotency_key=clave)

    await repo.pagos.guardar_referencia(intento.id, pi.id)
    return pi.client_secret

# 2) CONFIRMAR: solo el webhook cambia el estado. El navegador no decide nada.
async def manejar_evento(evento: dict):
    if await repo.eventos.ya_procesado(evento["id"]):           # at-least-once -> dedup
        return
    pi = evento["data"]["object"]
    pedido_id = pi["metadata"]["pedido_id"]

    async with uow.transaccion() as tx:
        await tx.eventos.marcar_procesado(evento["id"])         # MISMA transaccion que el efecto
        pedido = await tx.pedidos.bloquear(pedido_id)

        if evento["type"] == "payment_intent.succeeded":
            # transicion condicional: si otro webhook ya lo hizo, afecta 0 filas y salimos
            if not await tx.pedidos.transicionar(pedido, "pendiente_pago", "pagado"):
                return
            await tx.outbox.publicar("PedidoPagado", {"pedido_id": pedido_id})   # [08]
        elif evento["type"] == "payment_intent.payment_failed":
            await tx.pedidos.transicionar(pedido, "pendiente_pago", "pago_fallido")
```

**Las cinco cosas que hacen esto correcto:** la intención se persiste antes de llamar fuera · la clave de
idempotencia deriva del negocio · la llamada externa queda **fuera** de la transacción · la deduplicación
y el efecto van **dentro** de la misma · y la transición es condicional, así que el desorden y los
duplicados no rompen nada.

**La conciliación**, que es lo que salva cuando los webhooks se pierden:

```python
async def conciliar():   # cron cada 15 min
    for pago in await repo.pagos.pendientes(antiguedad_minima="10 minutes"):
        pi = await stripe.PaymentIntent.retrieve(pago.referencia_externa)
        if pi.status != pago.estado_equivalente:
            await manejar_evento(sintetizar_evento(pi))   # reutiliza el mismo camino
```

> **Ficha** · **Cuándo:** plantilla de cualquier integración de cobro ·
> **Patrón:** persistir intención → llamar fuera con clave → confirmar por webhook → conciliar por cron ·
> **Anti-patrón:** llamar a Stripe dentro de una transacción abierta ·
> **Límites:** entre la llamada y el webhook hay una ventana donde el estado es desconocido ·
> **Cómo falla:** sin conciliación, un webhook perdido deja un pedido pagado como pendiente para siempre ·
> **Decisión:** los webhooks son el camino feliz; la conciliación es la garantía ·
> **Trade-off:** un cron extra a cambio de no depender de la entrega de un tercero ·
> **Relacionado:** outbox, idempotencia, webhooks `[03, 08, 16]`

---

## Cómo falla un sistema de pagos

| Fallo | Por qué pasa | Cómo se evita |
|---|---|---|
| **Cobro duplicado** | reintento tras timeout sin clave | idempotency key derivada del pedido |
| **Cobrado sin pedido** | el webhook llegó y el pedido no existe o falló al guardar | la intención se persiste **antes** de llamar |
| **Pedido pagado que sigue "pendiente"** | webhook perdido | conciliación periódica |
| **Doble transición** | dos webhooks simultáneos | `UPDATE ... WHERE estado = anterior` |
| **Eventos desordenados** | `succeeded` antes que `checkout.completed` | lógica basada en estado, no en secuencia |
| **Precio manipulado** | se confió en el importe del cliente | recalcular en el servidor |
| **Overselling** | check-then-act sobre el stock | update atómico condicional |
| **Firma inválida** | se firmó el body parseado | HMAC sobre bytes crudos |
| **Reembolso duplicado** | reintento del job sin clave | idempotencia también en reembolsos |
| **Descuadre contable** | la fecha de pago ≠ fecha de liquidación | conciliar contra el informe de payouts |
| **Divisa equivocada** | importe sin divisa asociada | value object `Dinero` |
| **Tarjeta en los logs** | se logueó el request completo | redacción en la capa de logging `[06]` |

**El estado ambiguo es el problema central de esta caja:** ante un timeout **no sabes** si el cobro
ocurrió. No puedes eliminarlo — solo hacerlo seguro con idempotencia y descubrible con conciliación.

> **Ficha** · **Cuándo:** revisión previa a cobrar dinero real ·
> **Patrón:** cada fila de esta tabla debería tener un test ·
> **Anti-patrón:** probar solo el camino feliz en el sandbox del proveedor ·
> **Límites:** el sandbox no reproduce timeouts reales ni duplicados: simúlalos tú ·
> **Cómo falla:** los fallos de dinero se detectan tarde, por soporte o por contabilidad ·
> **Decisión:** alerta sobre pagos en estado intermedio con más de N minutos de antigüedad ·
> **Trade-off:** más comprobaciones y conciliación vs velocidad de entrega ·
> **Relacionado:** testing de integraciones, observabilidad `[11, 12]`

---

## Preguntas de entrevista y trade-offs

**Q: Un usuario pulsa "pagar" dos veces. ¿Cómo garantizas que no se cobre dos veces?**
Idempotency key derivada del pedido tanto en tu endpoint como hacia el PSP, insertada en la misma transacción
que la operación, y respuesta cacheada para el reintento. *Señal:* mencionas que el problema no es solo el
doble clic — es el **timeout de red**, donde no sabes si el cobro ocurrió, y ahí la clave es lo único que
te salva.

**Q: Llega el webhook `payment_intent.succeeded` dos veces y desordenado. ¿Qué haces?**
Verificar firma, deduplicar por `event.id`, y que la lógica sea idempotente y basada en el estado del objeto
en vez del orden de eventos. *Señal:* dices que at-least-once es la garantía real y que el desorden es normal,
no una anomalía, y añades la reconciliación periódica como red de seguridad.

**Q: ¿Por qué no marcar el pedido como pagado en el `success_url`?**
Porque el redirect depende del navegador del usuario y es manipulable; el webhook es la confirmación
del PSP. *Señal:* explicas la UX práctica — muestras "procesando" al volver y confirmas cuando llega el
webhook — en vez de dejar al usuario mirando una pantalla ambigua.

**Q: ¿Cómo evitas vender más stock del que tienes en un flash sale?**
`UPDATE ... WHERE stock >= 1` atómico y comprobar filas afectadas, o reservas con TTL. *Señal:* identificas
el check-then-act como race condition, y mencionas que con mucha contención sobre un solo SKU conviene medir
si el lock serializa a todos los compradores.

**Q: ¿Cómo representas el dinero?**
Enteros en la unidad mínima o DECIMAL, siempre con divisa, en un value object. *Señal:* mencionas las divisas
de cero y tres decimales y que el tipo de cambio se congela en el momento de la transacción.

**Q: ¿Qué guardas de una tarjeta?**
Nada sensible: el token del PSP, últimos 4 y marca. *Señal:* conectas esto con el alcance PCI y con el
argumento de negocio (SAQ A frente a una auditoría completa), que es lo que convence a un CTO.

**Trade-off central de esta caja:** *control de la experiencia vs superficie de riesgo y cumplimiento*.
Cada paso que acercas los datos de tarjeta a tu servidor te da control de UX y te multiplica el coste legal,
de auditoría y de incidentes. El consenso senior es delegar todo lo que se pueda al PSP y quedarte con el
modelo de negocio: pedidos, acceso, conciliación y estado.

---

## Fuentes

- [Stripe Docs — Payment Intents](https://docs.stripe.com/payments/payment-intents) · [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) · [Webhooks](https://docs.stripe.com/webhooks)
- [Guía de integración Stripe a calidad de producción, 2026](https://tomodahinata.com/en/blog/stripe-checkout-sessions-payments-production-guide-2026) — Checkout Sessions, webhooks e idempotencia.
- [Stripe Webhooks 2026: buenas prácticas](https://apiscout.dev/guides/stripe-webhooks-complete-guide-2026)
- [Mercado Pago — Checkout API](https://www.mercadopago.com.ar/developers/es/docs) · [PCI DSS v4.0](https://www.pcisecuritystandards.org/)
- Martin Fowler, [Patterns for Accounting](https://martinfowler.com/eaaDev/AccountingNarrative.html) — por qué los asientos se compensan y no se borran.
