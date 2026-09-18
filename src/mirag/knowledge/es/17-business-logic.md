# 17 · Business Logic

> La caja menos glamurosa y donde vive el valor real del producto. Aquí no hay frameworks que te salven:
> **modelar mal el negocio produce bugs que ninguna infraestructura arregla.**


**Cubre del temario:** `concepts` · `entities` · `workflows` · `state_machines` · `permissions` · `multi_tenancy` · `audit` · `failure_modes`

---

## Users, organizations y multi-tenancy

**Separa tres conceptos que la gente mezcla y luego no puede desenredar:**
- **Identidad** — quién es la persona (email, credenciales, MFA).
- **Cuenta/Usuario** — su perfil en tu sistema.
- **Membresía** — su pertenencia a una organización, **con un rol**.

**La regla de oro:** un usuario puede pertenecer a **varias** organizaciones con roles distintos.
Modelarlo como `usuario.organizacion_id` y `usuario.rol` parece más simple hoy y es una migración dolorosa
dentro de un año. La tabla `membresias(usuario_id, organizacion_id, rol)` desde el día uno cuesta lo mismo.

**Estrategias de multi-tenancy:**

| Modelo | Aislamiento | Coste | Cuándo |
|---|---|---|---|
| **Fila compartida** (`tenant_id` en cada tabla) | lógico | bajo | **el default**: SaaS con muchos clientes |
| **Esquema por tenant** | medio | medio | decenas o cientos de clientes grandes |
| **Base de datos por tenant** | fuerte | alto | enterprise, requisitos normativos, residencia de datos |

Con `tenant_id` compartido, **el riesgo es filtrar datos entre clientes**. No lo dejes a la disciplina de
cada desarrollador:
- **Row-Level Security de Postgres**, o
- un **repositorio base que inyecta el `tenant_id`** en toda query automáticamente, o como mínimo
- **tests que verifiquen explícitamente** que el tenant A no ve nada del B.

Un `WHERE tenant_id` olvidado en un endpoint nuevo es el incidente clásico de un SaaS, y es de los que
acaban en prensa.

> **Ficha** · **Cuándo:** el primer día de cualquier SaaS B2B ·
> **Patrón:** identidad, usuario y **membresía** como entidades separadas ·
> **Anti-patrón:** `usuario.organizacion_id` — la decisión que todo el mundo lamenta ·
> **Límites:** con `tenant_id` compartido, el aislamiento es lógico, no físico ·
> **Cómo falla:** un `WHERE tenant_id` olvidado en un endpoint nuevo filtra datos entre clientes ·
> **Decisión:** aplica el scope en la capa de datos (RLS o repositorio), no en cada endpoint ·
> **Trade-off:** aislamiento fuerte (DB por tenant, caro) vs compartido (barato, más riesgo) ·
> **Relacionado:** IDOR, RLS `[04, 06]`

---

## Roles y permisos

Base conceptual en `06-security.md`. Aquí, lo del modelado:

- **Roles predefinidos** (owner, admin, member, viewer) cubren el 90% y son comprensibles para el usuario.
  **Roles personalizados** con permisos granulares son una feature enterprise cara de construir y de
  explicar: no la hagas "por si acaso".
- **Permiso = acción + recurso** (`facturas:leer`, `usuarios:invitar`). Nómbralos consistentemente desde el
  principio.
- **Jerarquía y herencia:** los permisos de una carpeta se heredan a sus documentos. Es cómodo para el
  usuario y **caro de calcular**: con jerarquías profundas necesitas materializar el cierre transitivo o un
  motor tipo Zanzibar.
- **Casos límite que siempre aparecen tarde:** el último owner no se puede eliminar ni degradar; una
  invitación pendiente no es una membresía; ¿qué le pasa a lo que creó alguien que abandona la organización?
- **Permisos efectivos:** cuando hay roles, permisos directos y herencia, necesitas una función única que
  responda *"¿puede X hacer Y sobre Z?"* y **un endpoint de depuración que explique por qué**. Sin eso,
  cada duda de un cliente es una investigación manual.

> **Ficha** · **Cuándo:** en cuanto haya más de un tipo de usuario ·
> **Patrón:** roles predefinidos que cubren el 90% + permisos nombrados `recurso:accion` ·
> **Anti-patrón:** roles personalizados "por si acaso" antes de que un cliente los pida ·
> **Límites:** la herencia jerárquica es cara de calcular con árboles profundos ·
> **Cómo falla:** casos límite tardíos: el último owner, invitaciones pendientes, el que se va y deja recursos ·
> **Decisión:** una única función `puede(actor, accion, recurso)` **y un endpoint que explique por qué** ·
> **Trade-off:** granularidad vs comprensibilidad para quien configura ·
> **Relacionado:** RBAC/ABAC, autorización `[06]`

---

## State machines

**El patrón más rentable de esta caja.** Cualquier entidad con ciclo de vida (pedido, suscripción, envío,
solicitud, ticket, documento) debe ser una máquina de estados explícita.

```python
TRANSICIONES = {
    "borrador":       {"pendiente_pago", "cancelado"},
    "pendiente_pago": {"pagado", "cancelado", "expirado"},
    "pagado":         {"preparando", "reembolsado"},
    "preparando":     {"enviado", "reembolsado"},
    "enviado":        {"entregado", "devuelto"},
    "entregado":      {"devuelto"},
    # estados finales: cancelado, expirado, reembolsado, devuelto
}

def transicionar(pedido, nuevo, actor, motivo=None):
    if nuevo not in TRANSICIONES.get(pedido.estado, set()):
        raise TransicionInvalida(f"{pedido.estado} -> {nuevo}")
    registrar(pedido, de=pedido.estado, a=nuevo, actor=actor, motivo=motivo, en=now())
    pedido.estado = nuevo
```

**Por qué esto importa tanto:**
- **Los estados imposibles dejan de existir.** Un pedido no puede estar "enviado" sin haber estado "pagado".
- **Booleanos sueltos son el anti-patrón.** `pagado`, `enviado`, `cancelado` como tres booleanos permiten
  ocho combinaciones, de las cuales cinco no tienen sentido — y el código acaba lleno de `if` defensivos.
- **Cada transición es un punto natural** para disparar eventos, notificaciones y audit log.
- **Documenta el negocio** mejor que cualquier wiki: el diagrama *es* el código.
- **Concurrencia:** la transición debe ser atómica —
  `UPDATE pedidos SET estado='pagado' WHERE id=$1 AND estado='pendiente_pago'` y comprobar filas afectadas.
  Si no, dos webhooks simultáneos hacen la misma transición dos veces.

> **Ficha** · **Cuándo:** toda entidad con ciclo de vida ·
> **Patrón:** transiciones legales declaradas + registro de cada cambio con actor y motivo ·
> **Anti-patrón:** booleanos sueltos (`pagado`, `enviado`, `cancelado`) ·
> **Límites:** el modelo debe contemplar los estados intermedios que produce una saga `[08]` ·
> **Cómo falla:** dos eventos concurrentes aplican la misma transición dos veces ·
> **Decisión:** `UPDATE ... WHERE estado = 'anterior'` y comprobar filas afectadas ·
> **Trade-off:** rigidez vs eliminar estados imposibles por construcción ·
> **Relacionado:** pagos, audit logs `[07]`

---

## Workflows

Procesos de negocio de varios pasos que cruzan servicios, personas y tiempo (onboarding, aprobación de
gastos, devoluciones, alta de proveedores).

- **Pasos con estado persistido**, no variables en memoria: un workflow puede durar días y sobrevivir a
  despliegues y caídas.
- **Esperas humanas** (aprobaciones) y **temporales** (recordatorio a los 3 días, expiración a los 7) son
  parte del modelo, no un cron pegado con cinta.
- **Reanudable e idempotente:** si el worker muere en el paso 4, reanuda sin repetir los efectos de los
  pasos 1-3.
- **Compensaciones** cuando un paso tardío falla (`08-distributed-systems.md`).
- **Cuándo usar un motor de workflows** (Temporal, Step Functions, el Workflow DevKit): cuando hay muchos
  pasos, esperas largas y necesidad de reintentos durables. Para tres pasos, una máquina de estados y una
  cola sobran — meter un motor para eso es sobreingeniería.
- **Visibilidad obligatoria:** una pantalla donde soporte vea en qué paso está cada instancia y por qué está
  atascada. Sin eso, cada consulta de cliente es una consulta a la base de datos a mano.

> **Ficha** · **Cuándo:** procesos de varios pasos con esperas humanas o temporales ·
> **Patrón:** estado persistido por paso, reanudable e idempotente ·
> **Anti-patrón:** mantener el progreso en variables de memoria ·
> **Límites:** un workflow puede durar días y debe sobrevivir a despliegues ·
> **Cómo falla:** el worker muere en el paso 4 y al reanudar repite los efectos de los pasos 1-3 ·
> **Decisión:** con 3 pasos, máquina de estados y cola; un motor de workflows solo si hay muchos pasos y esperas largas ·
> **Trade-off:** motor durable (potente, otra pieza que operar) vs hecho a mano ·
> **Relacionado:** sagas, background jobs `[08, 15]`

---

## Inventario, pedidos y facturación

**Inventario** (detalle en `07-payments.md`):
- **Físico vs disponible vs reservado.** El stock disponible es `físico − reservado`. Modelarlo con un solo
  número es la causa del overselling.
- Las reservas **tienen TTL** y hay que liberarlas. Un job que expira reservas huérfanas es obligatorio.
- **Movimientos, no solo saldo:** un registro por entrada/salida con motivo. El saldo es la suma. Así puedes
  auditar, reconciliar y explicar cualquier descuadre. Es contabilidad aplicada al stock.

**Pedidos:**
- **Inmutable tras confirmarse**, con snapshot de precios, impuestos y datos de envío.
- Modificaciones posteriores son **documentos nuevos** (nota de crédito, pedido de reemplazo), no ediciones.
- Devoluciones y reembolsos parciales necesitan modelarse a nivel de **línea**, no de pedido.

**Facturación:** numeración **secuencial sin huecos** por serie y ejercicio (requisito legal en muchos
países — y ojo: un `SEQUENCE` de Postgres **deja huecos** al hacer rollback, así que hace falta otra
estrategia), inmutabilidad, y retención legal de años que convive con el derecho al borrado
(`15-files-data.md`).

> **Ficha** · **Cuándo:** cualquier recurso finito o documento legal ·
> **Patrón:** **movimientos, no solo saldo** — el stock es la suma de entradas y salidas ·
> **Anti-patrón:** un único número de stock que se sobrescribe ·
> **Límites:** la numeración de facturas debe ser secuencial **sin huecos** (un `SEQUENCE` los deja al hacer rollback) ·
> **Cómo falla:** un descuadre que nadie puede explicar porque no hay rastro de los cambios ·
> **Decisión:** los pedidos son inmutables tras confirmarse; las correcciones son documentos nuevos ·
> **Trade-off:** más filas y complejidad vs auditabilidad y capacidad de conciliar ·
> **Relacionado:** pagos, dinero, audit `[07]`

---

## Notifications

- **Preferencias por usuario y por canal y por tipo de evento.** No es un booleano global.
- **Deduplicación y agrupación:** si algo genera 50 eventos en un minuto, manda un resumen. Sin esto quemas
  el canal y el usuario desactiva todo.
- **Plantillas versionadas**, con i18n y zona horaria del destinatario (no mandes un push a las 4 de la
  mañana).
- **Idempotencia:** guarda qué notificación se envió por qué evento; un reintento del job no debe duplicar.
- **Un servicio central**, no cada módulo enviando por su cuenta (`16-integrations.md`).

> **Ficha** · **Cuándo:** en cuanto notifiques algo a un usuario ·
> **Patrón:** servicio central con preferencias por canal y tipo, deduplicación y agrupación ·
> **Anti-patrón:** que cada módulo envíe por su cuenta ·
> **Límites:** zona horaria y idioma del destinatario, no los tuyos ·
> **Cómo falla:** 50 eventos generan 50 notificaciones y el usuario desactiva todo ·
> **Decisión:** guarda qué se envió por qué evento: un reintento del job no debe duplicar ·
> **Trade-off:** inmediatez vs agrupación en resumen ·
> **Relacionado:** email, push, idempotencia `[08, 16]`

---

## Audit logs

**Quién hizo qué, cuándo, sobre qué y desde dónde.** Requisito normativo en muchos sectores y la
herramienta que más veces salva una investigación.

```
{actor_id, actor_tipo (usuario|sistema|api_key), accion, recurso_tipo, recurso_id,
 antes, despues, ip, user_agent, request_id, tenant_id, ocurrido_en}
```

- **Append-only.** Si se puede editar, no es un audit log. Idealmente en un almacén separado con permisos
  distintos, para que quien comprometa la app no pueda borrar sus huellas.
- **Distínguelo de los logs de aplicación:** el audit log es un **producto para el usuario y el auditor**
  (se consulta, se exporta, se conserva años), no material de depuración.
- **Registra también las lecturas** de datos sensibles si tu sector lo exige (sanidad, finanzas).
- **Automatízalo en la capa de datos** (hooks del ORM, triggers) en vez de confiar en que cada endpoint lo
  recuerde.

> **Ficha** · **Cuándo:** obligatorio con datos de terceros o requisitos normativos ·
> **Patrón:** append-only, en almacén separado, con actor, acción, antes/después y contexto ·
> **Anti-patrón:** confundirlo con los logs de aplicación ·
> **Límites:** si se puede editar, no es un audit log ·
> **Cómo falla:** quien compromete la app puede borrar sus huellas si comparten permisos ·
> **Decisión:** automatízalo en la capa de datos (hooks o triggers), no endpoint por endpoint ·
> **Trade-off:** volumen y coste vs poder responder "quién hizo esto y cuándo" ·
> **Relacionado:** cumplimiento, observabilidad `[06, 12]`

---

## Business rules: dónde viven

**El problema:** las reglas de negocio se dispersan entre el frontend, los controladores, los servicios, los
triggers de la base de datos y los jobs. Nadie sabe cuál gana.

**Principios:**
- **Una sola fuente de verdad por regla.** El frontend puede *duplicar* una validación para dar buena UX,
  pero **el servidor es siempre el que decide**.
- **Las reglas invariantes van en la base de datos** como constraints (`CHECK`, `UNIQUE`, FK). Es la única
  capa que nadie puede saltarse — ni un script, ni una migración, ni un bug de concurrencia.
- **Las reglas de dominio van en el dominio**, expresadas con el lenguaje del negocio
  (`puede_reembolsarse()`, no `if estado == 3 and dias < 30`).
- **Configuración vs código:** lo que cambia por cliente o por campaña (límites, porcentajes, plazos) va a
  configuración o a una tabla; lo estructural va en código. **No construyas un motor de reglas genérico
  salvo que el negocio realmente lo pida** — acabas escribiendo un lenguaje de programación peor, sin
  tests ni depurador.
- **Fechas, plazos y zonas horarias** son la fuente inagotable de bugs: "3 días hábiles" depende del país,
  "fin de mes" del calendario, y la medianoche del usuario no es la tuya. Centraliza esos cálculos en un
  solo módulo con tests exhaustivos.

> **Ficha** · **Cuándo:** al decidir dónde poner cada validación ·
> **Patrón:** invariantes como constraints de la DB; reglas de dominio en el dominio ·
> **Anti-patrón:** un motor de reglas genérico construido "por si acaso" ·
> **Límites:** la base de datos es la única capa que **nadie** puede saltarse ·
> **Cómo falla:** la misma regla implementada en tres sitios y las tres versiones divergen ·
> **Decisión:** lo que cambia por cliente o campaña va a configuración; lo estructural, a código ·
> **Trade-off:** configurable (flexible, más estados posibles) vs codificado (rígido, predecible) ·
> **Relacionado:** validación, constraints `[03, 04]`

---

## Entidades y agregados

El vocabulario de `[05]`, aplicado aquí: **la entidad tiene identidad que persiste** (un `Pedido` sigue
siendo el mismo aunque cambien todos sus campos); el **value object** se define por su valor y es
inmutable (`Dinero`, `Email`, `Direccion`).

**Usa más value objects.** Un tipo `Email` validado en el constructor elimina una familia entera de bugs,
porque a partir de ahí **es imposible** tener un email inválido circulando por el sistema:

```python
@dataclass(frozen=True)
class Email:
    valor: str
    def __post_init__(self):
        if "@" not in self.valor or len(self.valor) > 254:
            raise ValueError(f"email invalido: {self.valor}")

@dataclass(frozen=True)
class Dinero:
    centimos: int
    divisa: str
    def __add__(self, otro):
        if self.divisa != otro.divisa:                 # imposible sumar EUR + USD
            raise ValueError("divisas distintas")
        return Dinero(self.centimos + otro.centimos, self.divisa)
```

**El agregado** es el grupo de objetos con una **raíz** que es el único punto de entrada, y que define el
**límite de la consistencia transaccional**:

```
Pedido (raiz)                     <- se carga y se guarda entero
├── LineaDePedido  (interna)      <- nadie la modifica por fuera del Pedido
├── DireccionEnvio (value object)
└── cliente_id                    <- referencia por ID a OTRO agregado, no el objeto
```

**Las dos reglas que hacen que esto funcione:**

1. **Una transacción modifica un solo agregado.** Si necesitas cambiar dos, uno se actualiza por evento
   con consistencia eventual (`[08]`).
2. **Entre agregados se referencia por ID**, nunca por objeto. Así el agregado se carga completo sin
   arrastrar medio sistema, y el límite es real.

**Cómo elegir el tamaño del agregado:** lo más pequeño posible que mantenga sus invariantes. Si la regla
es *"el total del pedido es la suma de sus líneas"*, entonces líneas y pedido van juntos. Si es
*"un cliente no puede tener más de 5 pedidos activos"*, esa invariante **cruza agregados** y se resuelve
con consistencia eventual y compensación, no con una transacción gigante.

> **Ficha** · **Cuándo:** al modelar cualquier dominio con reglas propias ·
> **Patrón:** raíz de agregado como único punto de entrada; referencias por ID entre agregados ·
> **Anti-patrón:** agregados enormes que arrastran media base de datos en cada carga ·
> **Límites:** las invariantes que cruzan agregados **no** pueden garantizarse en una transacción ·
> **Cómo falla:** un agregado demasiado grande produce contención de locks y transacciones largas `[04]` ·
> **Decisión:** el límite del agregado es un buen candidato a límite de servicio `[05]` ·
> **Trade-off:** agregado grande (invariantes fáciles, poca concurrencia) vs pequeño (escala, consistencia eventual) ·
> **Relacionado:** DDD, service boundaries, sagas `[05, 08]`

---

## Inconsistencias de negocio: cómo falla la lógica

Los fallos de esta caja no producen errores: producen **datos que no cuadran**.

| Inconsistencia | Origen | Defensa |
|---|---|---|
| Stock negativo | check-then-act | update atómico condicional `[07]` |
| Pedido pagado sin cobro registrado | webhook perdido | conciliación `[07]` |
| Cobro sin pedido | se llamó al PSP antes de persistir | persistir intención primero |
| Suma de líneas ≠ total | se actualizó una parte | invariante dentro del agregado + constraint |
| Usuario sin organización | se borró la org sin cascada | FK con `ON DELETE` explícito |
| Último owner eliminado | falta la regla | constraint o comprobación en la transición |
| Estado imposible | booleanos sueltos | máquina de estados |
| Permiso fantasma | rol borrado pero membresías vivas | FK y revisión periódica |
| Factura con hueco en la numeración | `SEQUENCE` con rollback | contador transaccional propio |
| Doble notificación | reintento del job | dedupe por evento |
| Datos de otro tenant | falta el filtro | scope en la capa de datos |

**Cómo se detectan:** ninguna de estas dispara una alerta técnica. Hacen falta **comprobaciones de
invariantes** ejecutadas periódicamente, que es el equivalente de negocio a un health check:

```python
async def verificar_invariantes():          # cron diario, alerta si algo no cuadra
    descuadres = await db.fetch(
        "SELECT p.id FROM pedidos p "
        "JOIN lineas l ON l.pedido_id = p.id "
        "GROUP BY p.id, p.total_centimos "
        "HAVING SUM(l.subtotal_centimos) <> p.total_centimos")
    if descuadres:
        alertar("pedidos con total descuadrado", ids=[d["id"] for d in descuadres])
```

> **Ficha** · **Cuándo:** todo dominio con dinero, inventario o permisos ·
> **Patrón:** invariantes verificadas por un job periódico, con alerta ·
> **Anti-patrón:** confiar en que el código siempre las mantendrá ·
> **Límites:** detectar no es prevenir; la prevención va en constraints y transacciones ·
> **Cómo falla:** el descuadre se descubre meses después, en una auditoría o por un cliente ·
> **Decisión:** cada invariante crítica necesita defensa (constraint) **y** detección (verificación) ·
> **Trade-off:** coste de verificar vs descubrir tarde y no poder reconstruir qué pasó ·
> **Relacionado:** conciliación, audit logs, constraints `[04, 07, 12]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Cómo modelas usuarios y organizaciones en un SaaS B2B?**
Identidad, usuario y membresía separados; un usuario en varias organizaciones con roles distintos.
*Señal:* dices que `usuario.organizacion_id` es la decisión que todo el mundo lamenta, y explicas la
migración que evitas modelándolo bien desde el principio.

**Q: ¿Cómo garantizas el aislamiento entre tenants?**
`tenant_id` en todas las tablas, aplicado automáticamente (RLS o repositorio base), y tests explícitos de
fuga. *Señal:* dices que confiar en que cada desarrollador lo recuerde **falla siempre** y que la defensa
tiene que estar en la capa de datos.

**Q: ¿Por qué máquinas de estado en vez de booleanos?**
Porque eliminan estados imposibles, documentan el negocio, dan puntos naturales para eventos y auditoría, y
permiten transiciones atómicas. *Señal:* mencionas la transición condicional en SQL para evitar que dos
webhooks concurrentes la apliquen dos veces.

**Q: ¿Dónde pones la validación: frontend, API o base de datos?**
En las tres, con propósitos distintos: UX, autoridad y último recurso invariante. *Señal:* dices que la base
de datos es la única capa que nadie puede saltarse, y por eso las invariantes críticas van ahí como
constraints, no solo en el código.

**Q: ¿Qué guardas en un audit log y en qué se diferencia de los logs?**
Actor, acción, recurso, antes/después y contexto; append-only, con retención larga, pensado para auditores y
usuarios, no para depurar. *Señal:* propones almacenarlo separado con permisos distintos, porque si el
atacante puede borrarlo no sirve para nada.

**Trade-off central de esta caja:** *flexibilidad configurable vs simplicidad comprensible*. Cada regla que
conviertes en configurable multiplica los estados posibles del sistema, las combinaciones a probar y las
formas de que un cliente se configure algo incoherente. La postura senior es **codificar las reglas hasta
que un cliente real pague por la flexibilidad**, y entonces hacerla explícita y acotada.

---

## Fuentes

- Eric Evans, *Domain-Driven Design* — entidades, value objects y agregados.
- Vaughn Vernon, [Effective Aggregate Design](https://kalele.io/blog-posts/effective-aggregate-design/) — las reglas de tamaño y referencia por ID.
- [Martin Fowler — State Machine](https://martinfowler.com/bliki/StateMachine.html) y [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [PostgreSQL — Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) para aislamiento multi-tenant.
