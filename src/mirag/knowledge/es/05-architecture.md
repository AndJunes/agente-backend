# 05 · Architecture

> Arquitectura es el conjunto de decisiones que son caras de cambiar después. Por eso en una entrevista
> senior no te preguntan definiciones: te preguntan **qué elegiste, qué descartaste y por qué**.


**Cubre del temario:** `concepts` · `patterns` · `implementations` · `boundaries` · `dependencies` · `constraints` · `failure_modes` · `tradeoffs`

---

## Layered Architecture

La clásica de tres capas: **presentación → aplicación/dominio → datos**.

```
HTTP handler  →  Service  →  Repository  →  DB
```

- **Regla:** las dependencias van hacia abajo. Un repositorio no llama a un controlador.
- **Por qué sigue siendo lo más usado:** todo el mundo la entiende sin documentación.
- **Dónde se rompe:** cuando el "Service" se convierte en un archivo de 3.000 líneas que orquesta todo
  (*anemic domain model*: entidades que solo tienen getters y setters, y toda la lógica fuera). Ahí ya no
  tienes capas, tienes un script largo con carpetas.

> **Ficha** · **Cuándo:** el default razonable para casi cualquier servicio ·
> **Patrón:** dependencias en una sola dirección, siempre hacia abajo ·
> **Anti-patrón:** *anemic domain model* — entidades con solo getters y toda la lógica en un Service de 3.000 líneas ·
> **Límites:** no dice nada sobre cómo dividir *dentro* de cada capa ·
> **Cómo falla:** la capa de servicio se convierte en un cajón de sastre que nadie se atreve a tocar ·
> **Decisión:** si el dominio es CRUD, esto basta; no metas hexagonal por moda ·
> **Trade-off:** simplicidad universal vs acoplamiento del dominio al framework ·
> **Relacionado:** hexagonal, DDD, repository `[01]`

---

## Clean / Hexagonal / Ports & Adapters

Son la misma idea con nombres distintos: **el dominio no conoce la infraestructura.**

```
        HTTP        CLI         Cron
          \          |          /
           [  adaptadores de entrada  ]
                     |
              ┌──────────────┐
              │   DOMINIO    │   ← reglas de negocio puras, sin imports de framework
              │  (entidades, │
              │  casos de uso)│
              └──────────────┘
                     |
           [  adaptadores de salida  ]
          /          |          \
     Postgres      Stripe      S3
```

- **Port** = interfaz que define el dominio (`GuardaPedidos`, `CobraPagos`).
- **Adapter** = implementación concreta (`PostgresPedidos`, `StripePagos`).
- **Dependency inversion:** el dominio define la interfaz; la infraestructura la implementa. Por eso las
  flechas apuntan *hacia dentro*.

**Lo que ganas de verdad:** puedes testear todo el negocio sin levantar nada, y cambiar de proveedor de
pagos o de base de datos toca un archivo, no cincuenta.

**Lo que cuesta:** mucho boilerplate y capas de mapeo (entidad de dominio ↔ modelo de persistencia ↔ DTO).
**En un CRUD, esto es sobreingeniería pura.** La honestidad senior: aplica hexagonal donde hay lógica de
negocio real y compleja; en los módulos que solo leen y escriben, un repositorio directo es suficiente.

> **Ficha** · **Cuándo:** módulos con lógica de negocio compleja y proveedores intercambiables ·
> **Patrón:** el dominio define la interfaz (port); la infraestructura la implementa (adapter) ·
> **Anti-patrón:** aplicarlo a un CRUD — 40 archivos para leer un usuario ·
> **Límites:** exige capas de mapeo (dominio ↔ persistencia ↔ DTO) que hay que mantener ·
> **Cómo falla:** los "ports" acaban con la forma exacta del ORM y no has desacoplado nada ·
> **Decisión:** hexagonal donde hay reglas de negocio reales; repositorio directo donde solo hay lectura/escritura ·
> **Trade-off:** testabilidad y portabilidad vs boilerplate ·
> **Relacionado:** dependency inversion, repository, DDD `[11]`

---

## SOLID

| Principio | Qué significa de verdad | Cómo se ve en backend |
|---|---|---|
| **S**ingle Responsibility | una clase, **una razón para cambiar** | separar `CalculadoraDePrecios` de `EnviadorDeFacturas` |
| **O**pen/Closed | extender sin modificar | añadir un proveedor de pago nuevo implementando la interfaz |
| **L**iskov Substitution | una subclase debe poder sustituir a la base sin sorpresas | si `CuadradoRectangulo.setAncho` cambia el alto, lo has roto |
| **I**nterface Segregation | interfaces pequeñas y específicas | `Lector` y `Escritor` separados en vez de un `Repositorio` de 30 métodos |
| **D**ependency Inversion | depende de abstracciones, no de concreciones | el servicio recibe `EnviaEmails`, no `SendGridClient` |

**El matiz que importa:** SRP no es "una clase hace una cosa", es **"una clase responde a un solo actor"**.
Si el equipo de finanzas y el de marketing pueden pedir cambios en la misma clase, tiene dos razones para
cambiar y hay que separarla.

**Y el aviso:** SOLID aplicado sin criterio produce 40 archivos para leer un usuario de la base de datos.
El objetivo es cambiar de opinión barato, no coleccionar interfaces.

> **Ficha** · **Cuándo:** al revisar código que va a cambiar mucho ·
> **Patrón:** SRP entendido como "una razón para cambiar" = **un solo actor** que pide cambios ·
> **Anti-patrón:** una interfaz por clase "por si acaso" ·
> **Límites:** son heurísticas, no leyes; aplicarlas sin criterio multiplica archivos ·
> **Cómo falla:** violar Liskov rompe al sustituir una implementación por otra en producción ·
> **Decisión:** ¿dos departamentos pueden pedir cambios en la misma clase? Sepárala ·
> **Trade-off:** flexibilidad futura vs número de indirecciones que hay que leer hoy ·
> **Relacionado:** DI, design patterns, regla de tres `[01]`

---

## DDD (Domain-Driven Design)

**Estratégico** (lo que de verdad importa y casi nadie aplica):
- **Ubiquitous language:** el código usa las mismas palabras que el negocio. Si ellos dicen "póliza", tu
  clase no se llama `InsuranceRecord`.
- **Bounded context:** un modelo es válido *dentro de un contexto*. "Cliente" significa cosas distintas en
  Ventas, Facturación y Soporte — **y está bien que sean tres modelos distintos.** Forzar una única entidad
  `Cliente` compartida por toda la empresa es el origen del monolito imposible de mantener.
- **Context map:** cómo se relacionan los contextos (shared kernel, customer/supplier, anticorruption layer).
- **Anticorruption layer:** capa de traducción para que el modelo feo de un sistema externo (o legacy) no
  se filtre al tuyo.

**Táctico:**
- **Entity:** tiene identidad que persiste (un `Pedido` con su ID).
- **Value object:** se define por su valor, inmutable (`Dinero`, `Email`, `Direccion`). Úsalos más: un tipo
  `Email` validado en el constructor elimina una clase entera de bugs.
- **Aggregate:** un grupo de objetos con una **raíz** que es el único punto de entrada, y que define el
  **límite de la consistencia transaccional**. La regla: *una transacción modifica un solo agregado*; entre
  agregados, consistencia eventual vía eventos de dominio.
- **Domain event:** "algo relevante pasó" (`PedidoPagado`). La pieza que conecta DDD con arquitectura
  event-driven.
- **Repository:** colección de agregados; una por raíz de agregado, no una por tabla.

**Dónde está el valor real de DDD:** en decidir **los límites**. El resto (entidades, VOs) es buena práctica
de modelado que se puede aplicar sin llamarlo DDD.

> **Ficha** · **Cuándo:** dominios con reglas de negocio ricas y vocabulario propio ·
> **Patrón:** bounded contexts + ubiquitous language + agregados como límite transaccional ·
> **Anti-patrón:** una entidad `Cliente` única compartida por toda la empresa ·
> **Límites:** el valor está en el DDD estratégico (los límites), no en el catálogo táctico ·
> **Cómo falla:** aplicar entidades y value objects sin definir contextos = más ceremonia, mismo lío ·
> **Decisión:** una transacción modifica **un solo agregado**; entre agregados, eventos ·
> **Trade-off:** modelo fiel al negocio vs curva de aprendizaje del equipo ·
> **Relacionado:** service boundaries, event-driven, agregados `[08, 17]`

---

## Modular monolith vs microservicios

**La posición de consenso en 2026: empieza con un monolito modular.** La industria ya pasó por la resaca de
los microservicios prematuros.

**Modular monolith:** un despliegue, pero módulos con fronteras reales — cada módulo tiene su propio esquema
o al menos sus propias tablas, se comunican por interfaces públicas explícitas (o por eventos in-process),
y **está prohibido el join directo a las tablas de otro módulo**. Si las fronteras son de verdad, extraer
un módulo a servicio después es mecánico.

| | Monolito modular | Microservicios |
|---|---|---|
| Despliegue | uno | N pipelines |
| Transacciones | **ACID nativo** | sagas, consistencia eventual |
| Refactor de fronteras | un commit | migración coordinada entre equipos |
| Debugging | stack trace | **distributed tracing obligatorio** |
| Escalado | todo junto | por servicio |
| Fallos | cae todo | fallos parciales (y más modos de fallo) |
| Coste operativo | bajo | **alto: platform team necesario** |

**Cuándo microservicios sí:** equipos numerosos que se bloquean entre sí en el mismo repo, necesidades de
escalado radicalmente distintas (un servicio de transcodificación de vídeo vs un CRUD), requisitos de
aislamiento (PCI, datos sanitarios), o stacks tecnológicos distintos justificados.

**Cuándo NO:** "para escalar" cuando tienes 10.000 usuarios, "porque Netflix", o para arreglar un problema
organizativo. **Conway:** tu arquitectura acabará copiando tu organigrama; si el organigrama no soporta
microservicios, la arquitectura tampoco.

**El anti-patrón peor:** el **monolito distribuido** — N servicios que comparten base de datos y se llaman
en cadena síncrona. Tienes todos los costes de lo distribuido y ninguna de sus ventajas.

> **Ficha** · **Cuándo:** la decisión estructural más cara que vas a tomar ·
> **Patrón:** monolito modular con fronteras verificadas automáticamente ·
> **Anti-patrón:** **monolito distribuido** — N servicios que comparten base de datos ·
> **Límites:** microservicios exigen tracing, CI por servicio, service discovery y on-call ·
> **Cómo falla:** una feature típica toca tres servicios y necesita tres despliegues coordinados ·
> **Decisión:** ¿los equipos se bloquean entre sí en el mismo repo? Solo entonces separa ·
> **Trade-off:** coste de coordinación (monolito) vs coste operativo y de consistencia (distribuido) ·
> **Relacionado:** Conway, sagas, service boundaries `[08, 19]`

---

## Service boundaries

Cómo se trazan bien las fronteras:

- **Por capacidad de negocio**, no por capa técnica. `Facturación`, `Inventario`, `Envíos` — nunca un
  "servicio de base de datos" o un "servicio de validación".
- **Por límite transaccional.** Si dos cosas *tienen* que cambiar atómicamente, van juntas. Repartirlas
  entre servicios te condena a sagas.
- **Por ritmo de cambio.** Lo que cambia junto, vive junto.
- **Por propiedad de datos.** Cada dato tiene **un solo dueño** que lo escribe; los demás leen copias o
  preguntan. Dos servicios escribiendo la misma tabla es una frontera mal trazada.
- **Test de la frontera:** si una feature típica requiere tocar tres servicios y coordinar tres despliegues,
  las fronteras están mal.

> **Ficha** · **Cuándo:** al extraer un servicio o dividir un módulo ·
> **Patrón:** por capacidad de negocio, por límite transaccional y por propiedad del dato ·
> **Anti-patrón:** fronteras por capa técnica ("servicio de validación", "servicio de base de datos") ·
> **Límites:** lo que debe cambiar atómicamente no se puede separar sin pagar una saga ·
> **Cómo falla:** dos servicios escribiendo la misma tabla = frontera mal trazada, incidentes garantizados ·
> **Decisión:** cada dato tiene **un solo dueño** que escribe; los demás leen copias ·
> **Trade-off:** autonomía de equipos vs consistencia y latencia ·
> **Relacionado:** agregados, sagas, event-driven `[08]`

---

## CQRS

Separar el modelo de **escritura** (comandos) del de **lectura** (queries).

```
Comando → modelo de escritura (normalizado, validaciones) → eventos
                                                              ↓
                              modelo de lectura (desnormalizado, listo para pintar)
```

- **CQRS ligero:** mismo almacén, distintos modelos/DTOs para leer y escribir. Barato y suele bastar.
- **CQRS completo:** almacenes separados, sincronizados por eventos → **consistencia eventual** (el lector
  ve el cambio 200ms después). Tu UI tiene que estar diseñada para eso.
- **Cuándo merece la pena:** lecturas y escrituras con cargas o formas radicalmente distintas (un feed leído
  un millón de veces y escrito mil).
- **Event sourcing** (guardar los eventos como fuente de verdad en vez del estado) se menciona junto a CQRS
  pero es una decisión aparte y mucho más cara: versionado de eventos, replays, snapshots, y explicar a
  todo el mundo por qué no se puede hacer un simple `UPDATE`. **Excelente para dominios con auditoría real
  (banca, trading); un lastre para un CRUD.**

> **Ficha** · **Cuándo:** lecturas y escrituras con formas o cargas radicalmente distintas ·
> **Patrón:** empezar por CQRS ligero (mismo almacén, modelos distintos) ·
> **Anti-patrón:** almacenes separados sin que la UI esté diseñada para consistencia eventual ·
> **Límites:** el lector va por detrás del escritor; siempre ·
> **Cómo falla:** el usuario guarda, recarga y no ve su cambio ·
> **Decisión:** CQRS y event sourcing son decisiones **separadas**; no las adoptes juntas por inercia ·
> **Trade-off:** rendimiento de lectura vs complejidad y desfase ·
> **Relacionado:** event-driven, consistencia eventual `[08]`

---

## Event-driven architecture

Los servicios publican hechos; otros reaccionan. Detalles de mensajería en `08-distributed-systems.md`.

- **Event notification:** "pasó algo, ve a buscar los detalles". Payload mínimo, acoplamiento bajo, más
  chatter de red.
- **Event-carried state transfer:** el evento lleva los datos. El consumidor no necesita llamarte; a cambio,
  duplicas estado y tienes que versionar el esquema del evento con cuidado.
- **Ventajas:** desacoplamiento temporal (el consumidor puede estar caído), extensibilidad (añades un
  consumidor nuevo sin tocar al productor), y absorción de picos.
- **Costes reales:** el flujo deja de ser legible en el código (para saber qué pasa al pagar un pedido hay
  que buscar por todo el repo quién escucha), depuración difícil sin tracing, **orden y duplicados** que
  gestionar, y esquemas de evento que se convierten en una API pública que nadie versiona.

**Regla práctica:** eventos para *notificar hechos pasados* entre contextos; llamadas síncronas para
*pedir algo que necesitas ahora mismo*. Mezclar los dos criterios es como se construyen las cadenas de
eventos imposibles de seguir.

> **Ficha** · **Cuándo:** entre bounded contexts, para notificar hechos ya ocurridos ·
> **Patrón:** eventos para notificar; llamadas síncronas para pedir algo que necesitas ahora ·
> **Anti-patrón:** cadenas de eventos donde nadie puede explicar qué pasa al pagar un pedido ·
> **Límites:** el esquema del evento es una API pública que casi nadie versiona ·
> **Cómo falla:** el flujo deja de ser legible en el código; sin tracing es indepurable ·
> **Decisión:** *event notification* (payload mínimo) si quieres bajo acoplamiento; *state transfer* si
> quieres que el consumidor no te llame · **Trade-off:** desacoplamiento vs trazabilidad ·
> **Relacionado:** colas, outbox, sagas `[08, 12]`

---

## Dependency injection

Pasar las dependencias en vez de construirlas dentro.

```python
# mal: acoplado, intestable sin red
class ServicioPedidos:
    def __init__(self):
        self.pagos = StripeCliente(api_key=os.environ["STRIPE_KEY"])

# bien: inyectado, testeable con un doble
class ServicioPedidos:
    def __init__(self, pagos: PasarelaDePago):
        self.pagos = pagos
```

- **Constructor injection** es la forma por defecto: las dependencias son explícitas y el objeto nace válido.
- **No necesitas un framework de DI.** En lenguajes dinámicos, pasar argumentos y una función `build_app()`
  que arma el grafo en el arranque (*composition root*) es suficiente y mucho más legible.
- **El anti-patrón:** *service locator* (un contenedor global del que cada clase saca lo que necesita).
  Oculta las dependencias y convierte los errores de configuración en fallos en tiempo de ejecución.

> **Ficha** · **Cuándo:** siempre que algo dependa de I/O o de configuración ·
> **Patrón:** constructor injection + un `composition root` que arma el grafo al arrancar ·
> **Anti-patrón:** *service locator* — un contenedor global del que cada clase saca lo que quiere ·
> **Límites:** no necesitas framework de DI; en lenguajes dinámicos, pasar argumentos basta ·
> **Cómo falla:** dependencias ocultas convierten errores de configuración en fallos en runtime ·
> **Decisión:** si no puedes testear la clase sin red, la dependencia no está inyectada ·
> **Trade-off:** explicitud vs verbosidad en los constructores ·
> **Relacionado:** hexagonal, testing con dobles `[11]`

---

## Design patterns que usarás de verdad

- **Repository** — abstrae persistencia. Cuidado: si tu repositorio devuelve `QuerySet` del ORM, no has
  abstraído nada.
- **Unit of Work** — agrupa cambios y los confirma en una transacción. Es lo que hace la `session` de
  SQLAlchemy o el `DbContext` de EF.
- **Strategy** — un algoritmo intercambiable (proveedores de pago, políticas de precio).
- **Adapter / Anticorruption layer** — envuelve lo externo.
- **Decorator / Middleware** — logging, auth, retry, caching, sin tocar el core. Toda la pila HTTP moderna
  es esto.
- **Factory / Builder** — construcción compleja o dependiente de configuración.
- **Observer / Pub-Sub** — desacopla productor de consumidores.
- **Circuit breaker, Bulkhead, Retry** — patrones de resiliencia (`10-reliability.md`).
- **Saga / Outbox / Inbox** — patrones distribuidos (`08-distributed-systems.md`).
- **State machine** — para cualquier entidad con ciclo de vida (pedido, suscripción, envío).
  Ver `17-business-logic.md`. Modelar los estados y las transiciones legales explícitamente elimina una
  familia entera de bugs.

> **Ficha** · **Cuándo:** cuando reconozcas el problema, no antes ·
> **Patrón:** Repository, Unit of Work, Strategy, Adapter, Decorator, State machine ·
> **Anti-patrón:** Singleton como global disfrazado; patrones aplicados por nombre y no por problema ·
> **Límites:** un patrón mal elegido es más difícil de quitar que de poner ·
> **Cómo falla:** un "Repository" que devuelve el `QuerySet` del ORM no abstrae nada ·
> **Decisión:** la regla de tres — abstrae en el tercer caso ·
> **Trade-off:** vocabulario compartido vs indirección innecesaria ·
> **Relacionado:** resiliencia, patrones distribuidos, state machines `[08, 10, 17]`

---

## Trade-offs: cómo se razona en voz alta

Un senior no dice "usaría microservicios". Dice: **"depende de X; con estos datos elegiría Y, y lo cambiaría
si pasara Z."** El esquema mental:

1. **¿Cuáles son los requisitos no funcionales reales?** Latencia objetivo, volumen, disponibilidad,
   consistencia, cumplimiento normativo, tamaño y madurez del equipo.
2. **¿Qué es reversible y qué no?** (Jeff Bezos: puertas de una vía vs de dos vías.) Elegir el lenguaje o
   el esquema de la DB es casi irreversible; elegir una librería de logging no. Gasta el tiempo de decisión
   donde es irreversible.
3. **¿Cuál es el coste de equivocarse y cómo lo detecto pronto?**
4. **Documenta la decisión con un ADR.** Media página en el repo. Dentro de dos años alguien
   —seguramente tú— querrá saber por qué. La plantilla y cómo se justifica, en `[19]`.

**Las tensiones que se repiten siempre:**

| Tensión | Cuándo cae de cada lado |
|---|---|
| Consistencia fuerte ↔ disponibilidad | dinero y stock → fuerte; feeds y contadores → eventual |
| Acoplamiento ↔ duplicación | duplicar poco código entre servicios es mejor que compartir una librería que los acopla |
| Simplicidad ↔ flexibilidad | la flexibilidad no usada es solo complejidad |
| Ahora ↔ después | la deuda técnica es un préstamo: útil si sabes cuándo lo pagas |
| Build ↔ buy | construye lo que te diferencia; compra el resto (auth, pagos, email) |

> **Ficha** · **Cuándo:** en cada decisión estructural y en toda entrevista de diseño ·
> **Patrón:** distinguir decisiones reversibles de irreversibles y gastar el tiempo en las segundas ·
> **Anti-patrón:** enumerar opciones sin recomendar ninguna ·
> **Límites:** casi nunca tienes los datos que querrías; decide igual y escribe por qué ·
> **Cómo falla:** dos años después nadie recuerda por qué se eligió aquello y nadie se atreve a cambiarlo ·
> **Decisión:** documenta con un ADR `[19]` toda decisión cara de revertir ·
> **Trade-off:** velocidad de decisión vs análisis; el sobreanálisis también cuesta ·
> **Relacionado:** ADRs, system design `[19]`

---

## Coupling y cohesion

Los dos conceptos que subyacen a **todo** lo demás de esta caja, y que casi nadie sabe definir.

**Cohesión** (alta = buena): cuánto pertenecen juntas las cosas que están juntas. Un módulo `facturacion`
que calcula, emite y numera facturas tiene alta cohesión. Un módulo `utils` con 40 funciones sin relación
tiene cohesión cero.

**Acoplamiento** (bajo = bueno): cuánto necesita un módulo saber de otro para funcionar. No es binario,
es un espectro:

| Tipo de acoplamiento | Ejemplo | Gravedad |
|---|---|---|
| **De datos** | pasar un `id` como argumento | ✅ el mínimo inevitable |
| **De estructura** | pasar un objeto entero del que solo usas un campo | 🟡 aceptable |
| **De control** | pasar un flag que cambia el comportamiento del otro (`hacer(x, rapido=True)`) | 🟠 huele mal |
| **Común** | dos módulos leen y escriben el mismo global o la misma tabla | 🔴 grave |
| **De contenido** | un módulo toca las estructuras internas del otro | 🔴 grave |
| **Temporal** | A debe llamarse antes que B y nada lo impide | 🔴 invisible hasta que rompe |

**La regla:** *alta cohesión dentro, bajo acoplamiento fuera.* Es literalmente el criterio con el que se
decide qué va en qué módulo y dónde va la frontera de un servicio.

**Ley de Conway:** la arquitectura acabará copiando la estructura de comunicación de la organización.
La *maniobra inversa de Conway* es reorganizar los equipos para conseguir la arquitectura que quieres —
y es la razón por la que las migraciones a microservicios fracasan si el organigrama no cambia.

> **Ficha** · **Cuándo:** al decidir dónde poner un módulo o trazar una frontera ·
> **Patrón:** lo que cambia junto, vive junto; lo que cambia por motivos distintos, se separa ·
> **Anti-patrón:** el módulo `utils`/`common`/`shared` que acaba acoplando a todo el sistema ·
> **Límites:** reducir acoplamiento suele aumentar duplicación: hay que elegir ·
> **Cómo falla:** el acoplamiento temporal y el común no dan error, solo bugs raros e intermitentes ·
> **Decisión:** ¿un cambio típico toca tres módulos? Las fronteras están mal ·
> **Trade-off:** poca duplicación (acopla) vs independencia (duplica) — entre servicios, **duplica** ·
> **Relacionado:** service boundaries, bounded contexts, Conway `[19]`

---

## Implementación: cómo se ve en el árbol de archivos

**Monolito modular** — las fronteras son carpetas con API pública explícita:

```
src/
├── modulos/
│   ├── facturacion/
│   │   ├── api.py            # LO UNICO que otros modulos pueden importar
│   │   ├── dominio/          # entidades, value objects, reglas
│   │   ├── infraestructura/  # repositorios, clientes HTTP
│   │   └── tests/
│   ├── pedidos/
│   │   ├── api.py
│   │   └── ...
│   └── inventario/
├── plataforma/               # lo transversal: db, logging, config, auth
│   ├── db.py
│   └── observabilidad.py
└── main.py                   # composition root: arma el grafo de dependencias
```

**La regla que lo hace funcionar:** `pedidos` puede importar `facturacion.api`, **nunca**
`facturacion.dominio`. Y nada de joins SQL a las tablas de otro módulo. Sin verificación automática esto
se degrada en semanas, así que se comprueba en CI:

```python
# tests/test_arquitectura.py — falla el build si alguien cruza una frontera
import ast, pathlib

def test_los_modulos_solo_se_hablan_por_api():
    for archivo in pathlib.Path("src/modulos").rglob("*.py"):
        propio = archivo.relative_to("src/modulos").parts[0]
        for nodo in ast.walk(ast.parse(archivo.read_text())):
            if isinstance(nodo, ast.ImportFrom) and nodo.module:
                partes = nodo.module.split(".")
                if partes[0] == "modulos" and partes[1] != propio:
                    assert partes[2:3] == ["api"], f"{archivo} importa el interior de {partes[1]}"
```

**Hexagonal** — el dominio en el centro, sin imports del framework:

```
src/
├── dominio/          # cero imports de fastapi, sqlalchemy, stripe
│   ├── pedido.py     # entidades y reglas
│   └── puertos.py    # interfaces: GuardaPedidos, CobraPagos
├── aplicacion/       # casos de uso que orquestan el dominio
├── adaptadores/
│   ├── entrada/      # http/, cli/, consumidores de cola
│   └── salida/       # postgres/, stripe/, s3/
└── main.py
```

**El test que verifica que hexagonal es real:** `grep -r "import sqlalchemy\|import fastapi" src/dominio/`
debe devolver **cero líneas**. Si devuelve algo, tienes carpetas bonitas y arquitectura en capas normal.

> **Ficha** · **Cuándo:** al arrancar un proyecto o al modularizar uno existente ·
> **Patrón:** fronteras verificadas por tests de arquitectura en CI ·
> **Anti-patrón:** documentar las reglas en un wiki y confiar en la disciplina ·
> **Límites:** la estructura de carpetas no impide nada por sí sola; el lenguaje casi nunca la fuerza ·
> **Cómo falla:** a los seis meses hay imports cruzados por todas partes y nadie sabe cuándo empezó ·
> **Decisión:** si vas a extraer servicios algún día, empieza con `api.py` por módulo hoy ·
> **Trade-off:** rigidez (frena atajos legítimos) vs erosión (frena todo, más tarde) ·
> **Relacionado:** coupling, service boundaries, CI `[14]`

---

## Constraints: lo que decide la arquitectura de verdad

Los diagramas no eligen la arquitectura; estas cuatro cosas sí.

| Restricción | Cómo condiciona |
|---|---|
| **Tamaño y madurez del equipo** | 4 personas no pueden operar 12 microservicios: el on-call no existe. Conway manda |
| **Presupuesto** | multi-región cuesta más del doble; Kubernetes cuesta una persona a tiempo parcial, permanentemente |
| **Escala real (no la imaginada)** | con 100 RPS, una instancia con réplicas de lectura sobra |
| **Legacy** | rara vez partes de cero: hay una base de datos que otros sistemas leen, y un ERP que nadie toca |
| **Normativa** | PCI, RGPD o residencia de datos pueden **obligar** a aislar un servicio o una región `[07]` |
| **Plazo** | una arquitectura correcta entregada tarde puede ser peor que una simple a tiempo |

**Para convivir con legacy**, dos patrones:
- **Anticorruption layer** — una capa de traducción para que el modelo del sistema viejo no se filtre al nuevo.
- **Strangler fig** — el sistema nuevo intercepta el tráfico y va absorbiendo funcionalidad ruta a ruta,
  hasta que el viejo queda sin uso. Es la forma **realista** de migrar: nunca el big bang.

> **Ficha** · **Cuándo:** antes de dibujar la primera caja ·
> **Patrón:** strangler fig para migrar; ACL para aislar lo que no controlas ·
> **Anti-patrón:** la reescritura completa "que esta vez sí saldrá bien" ·
> **Límites:** no puedes elegir una arquitectura que tu equipo no pueda operar a las 3 de la mañana ·
> **Cómo falla:** la arquitectura ideal se abandona a medio migrar y conviven **dos** sistemas para siempre ·
> **Decisión:** elige la cosa más simple que cumpla los requisitos reales de escala y cumplimiento ·
> **Trade-off:** ambición técnica vs capacidad operativa del equipo ·
> **Relacionado:** Conway, system design, coste `[14, 19]`

---

## Cómo falla una arquitectura

No con un error: con una degradación que nadie declara.

| Síntoma | Qué significa |
|---|---|
| Un cambio pequeño toca 5 módulos | **fronteras mal trazadas** |
| Nadie toca cierto archivo | acoplamiento y falta de tests: miedo estructural |
| Los despliegues hay que coordinarlos | **monolito distribuido** |
| Todo pasa por un servicio central | punto único de fallo y cuello de botella organizativo |
| "Eso lo sabe solo Ana" | bus factor de 1 |
| Cada feature añade un `if` a la misma función | falta una abstracción (ahora sí, ya hay tres casos) |
| Los tests tardan 40 minutos | acoplamiento con la infraestructura |
| Nadie sabe qué pasa al pagar un pedido | cadena de eventos sin orquestación ni tracing |

**Deuda arquitectónica** se distingue de la deuda de código en que **no se paga refactorizando un archivo**:
exige migrar datos, coordinar equipos y desplegar en varias fases. Por eso se acumula: cada paso individual
parece demasiado caro.

> **Ficha** · **Cuándo:** en retrospectivas y al planificar trimestres ·
> **Patrón:** medir síntomas (lead time, número de módulos por PR, tiempo de CI) en vez de opinar ·
> **Anti-patrón:** "lo arreglamos cuando haya tiempo" — nunca lo hay ·
> **Límites:** la deuda arquitectónica no se ve en ninguna métrica de producción ·
> **Cómo falla:** la velocidad del equipo baja de forma gradual y nadie puede señalar la causa ·
> **Decisión:** si un cambio típico cruza tres módulos, la frontera es el trabajo, no la feature ·
> **Trade-off:** entregar hoy vs poder entregar dentro de un año ·
> **Relacionado:** coupling, DORA, ADRs `[14, 19]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Monolito o microservicios para un producto nuevo con 6 ingenieros?**
Monolito modular, con fronteras internas serias. *Señal:* mencionas Conway, el coste operativo (tracing,
CI/CD por servicio, service discovery, on-call), y que las fronteras bien hechas hacen la extracción
posterior mecánica. Un candidato que dice "microservicios siempre" no ha operado ninguno.

**Q: ¿Cómo decides dónde va la frontera entre dos servicios?**
Por capacidad de negocio, por límite transaccional y por propiedad de los datos. *Señal:* dices que si dos
cosas deben cambiar atómicamente no deben separarse, porque el precio es una saga con compensaciones.

**Q: ¿Qué es un aggregate y por qué importa?**
Un grupo de objetos con una raíz que es el límite de la consistencia transaccional. Importa porque define
qué puede cambiar atómicamente y qué necesita consistencia eventual. *Señal:* lo conectas con el diseño de
servicios: los límites de agregado son buenos candidatos a límites de servicio.

**Q: Tu compañero quiere event sourcing para el módulo de usuarios. ¿Qué dices?**
Que el coste (versionado de eventos, replays, snapshots, curva de aprendizaje, imposibilidad de un UPDATE
simple) rara vez se justifica en un CRUD, y que si lo que quiere es auditoría, una tabla de audit log
resuelve el 90% por el 5% del coste. *Señal:* separas event sourcing de CQRS, que mucha gente confunde.

**Q: ¿Cómo evitas que un monolito modular degenere en una bola de barro?**
Fronteras verificadas automáticamente: tests de arquitectura que fallan si un módulo importa el interior
de otro, esquemas de DB separados, revisión de PRs que cruzan módulos. *Señal:* dices que la disciplina sin
enforcement automático siempre pierde a los seis meses.

**Trade-off central de esta caja:** *coste de coordinación (monolito: todos en el mismo código) vs coste
operativo y de consistencia (distribuido: todos en la misma red)*. Los microservicios no eliminan la
complejidad, la mueven del compilador a la red — donde no hay tipos, no hay stack traces y los fallos son
parciales.

---

## Fuentes

- *Domain-Driven Design* (Eric Evans) y *Implementing DDD* (Vaughn Vernon) — bounded contexts y agregados.
- *Clean Architecture* (Robert C. Martin) — dependency rule.
- Alistair Cockburn, [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) — el original.
- [Martin Fowler — Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html), [Microservice Trade-Offs](https://martinfowler.com/articles/microservice-trade-offs.html)
- *Building Microservices* (Sam Newman) — cuándo NO separar.
- [ADR — Architecture Decision Records](https://adr.github.io/)
