# 11 · Testing

> Los tests no están para "tener cobertura". Están para **poder cambiar el código sin miedo**. Cualquier
> test que no aumente tu confianza al desplegar es coste sin beneficio.


**Cubre del temario:** `concepts` · `unit` · `integration` · `e2e` · `contract` · `load` · `implementations` · `failure_scenarios`

---

## La pirámide (y por qué se discute)

```
        /\        E2E            pocos, lentos, frágiles, altísima confianza
       /  \       Integración    los que más valor dan en backend
      /____\      Unitarios      muchos, rápidos, baratos
```

**El matiz senior:** la pirámide clásica viene de una época con E2E carísimos. Hoy, con testcontainers y
bases de datos en Docker, **los tests de integración son rápidos y son los que más confianza dan en backend**
— porque el 90% de los bugs reales están en las fronteras (SQL mal escrito, serialización, transacciones,
configuración), no en la lógica pura.

La forma que defiende mucha gente hoy es el **trofeo de tests**: pocos unitarios (solo para lógica compleja),
**muchos de integración**, unos pocos E2E, y una base ancha de análisis estático (tipos y linters), que
es el test más barato que existe.

> **Ficha** · **Cuándo:** al decidir dónde invertir esfuerzo de testing ·
> **Patrón:** trofeo de tests — base de análisis estático, muchos de integración, pocos E2E ·
> **Anti-patrón:** miles de unitarios con mocks que no prueban ninguna frontera real ·
> **Límites:** la pirámide clásica viene de cuando los E2E eran carísimos ·
> **Cómo falla:** suite verde y producción rota porque nada probó el SQL de verdad ·
> **Decisión:** en backend, los bugs viven en las fronteras: prioriza integración ·
> **Trade-off:** velocidad de feedback vs confianza ·
> **Relacionado:** testcontainers, contract testing `[04]`

---

## Unit tests

Prueban una unidad aislada, sin I/O. Deben correr en milisegundos.

```python
def test_precio_con_descuento_por_volumen():
    # Arrange
    carrito = Carrito([Linea(producto="A", unidades=10, precio=Dinero(100, "EUR"))])
    # Act
    total = calcular_total(carrito, descuentos=[DescuentoPorVolumen(minimo=10, porcentaje=10)])
    # Assert
    assert total == Dinero(900, "EUR")
```

**Reglas:**
- **Arrange / Act / Assert.** Un test que no se lee en tres bloques está haciendo demasiado.
- **Prueba comportamiento, no implementación.** Si renombrar un método privado rompe 40 tests, esos tests
  están acoplados a *cómo* y no a *qué*. Son un freno al refactor, que es justo lo contrario de su función.
- **Un motivo de fallo por test.** El nombre debe decir qué se rompió sin abrir el archivo.
- **Deterministas.** Nada de `now()`, `random()` ni red sin control: inyecta un reloj y una semilla.
- **Dónde aportan de verdad:** lógica de negocio con muchas ramas — cálculo de precios, impuestos, reglas de
  permisos, máquinas de estado. Para un controlador que solo llama a un servicio, un test unitario con tres
  mocks no prueba nada útil.

> **Ficha** · **Cuándo:** lógica de negocio con muchas ramas ·
> **Patrón:** Arrange/Act/Assert, deterministas, un motivo de fallo por test ·
> **Anti-patrón:** testear implementación — renombrar un método privado rompe 40 tests ·
> **Límites:** no detectan nada de integración, serialización ni SQL ·
> **Cómo falla:** tests acoplados a la estructura bloquean el refactor, que es justo lo que debían permitir ·
> **Decisión:** inyecta reloj y semilla; nunca `now()` ni `random()` directos ·
> **Trade-off:** aislamiento (rápido) vs realismo ·
> **Relacionado:** property-based, dobles `[01]`

---

## Integration tests

Prueban tu código **contra las dependencias reales**: base de datos, cache, broker.

```python
# testcontainers: Postgres real, efímero, idéntico al de producción
@pytest.fixture(scope="session")
def db():
    with PostgresContainer("postgres:17") as pg:
        aplicar_migraciones(pg.get_connection_url())
        yield pg

def test_pedido_no_se_duplica_con_la_misma_idempotency_key(db):
    crear_pedido(db, key="abc", importe=100)
    crear_pedido(db, key="abc", importe=100)          # reintento
    assert contar_pedidos(db) == 1                    # y el cobro fue uno solo
```

**Por qué son los más valiosos en backend:** verifican lo que un mock nunca verifica — que el SQL es válido,
que el índice único existe, que la transacción hace rollback, que el ORM genera lo que crees, que la
migración corre.

**Aislamiento entre tests:** cada test en una transacción que se revierte al final (rápido), o truncar
tablas entre tests (más lento pero más realista). **Nunca** dependas del orden ni del estado dejado por otro
test: es la principal causa de suites que fallan solo en CI.

> **Ficha** · **Cuándo:** todo lo que cruce una frontera (DB, HTTP, cola) ·
> **Patrón:** testcontainers con el **mismo motor y versión** que producción, aplicando las migraciones reales ·
> **Anti-patrón:** SQLite para testear lo que en producción es Postgres ·
> **Límites:** más lentos; hay que aislar el estado entre tests ·
> **Cómo falla:** dependencia del orden de ejecución → verde en local, rojo en CI ·
> **Decisión:** transacción que se revierte por test, o truncado entre tests ·
> **Trade-off:** segundos por test a cambio de detectar los bugs que de verdad ocurren ·
> **Relacionado:** migraciones, fixtures `[04]`

---

## E2E tests

Todo el sistema: HTTP real, base de datos real, servicios externos simulados.

- **Pocos y solo para los caminos críticos de negocio**: registro, login, checkout, la acción que da dinero.
- **Son frágiles y lentos.** Cada E2E que añades es un peaje que pagas en cada PR, para siempre.
- **La regla:** si un E2E falla, tiene que significar "el producto está roto", no "cambió un selector".
- **Datos:** cada ejecución crea los suyos con identificadores únicos, y limpia. Depender de una base de
  datos precargada es cómo los E2E empiezan a fallar aleatoriamente.

> **Ficha** · **Cuándo:** solo los caminos que pagan las facturas ·
> **Patrón:** pocos, con datos propios por ejecución y limpieza al final ·
> **Anti-patrón:** cubrir toda la funcionalidad con E2E ·
> **Límites:** lentos y frágiles; cada uno es un peaje en cada PR, para siempre ·
> **Cómo falla:** fallan por un selector cambiado y la gente empieza a ignorar los rojos ·
> **Decisión:** si un E2E falla, debe significar "el producto está roto" ·
> **Trade-off:** confianza máxima vs coste de mantenimiento máximo ·
> **Relacionado:** flaky tests, datos de prueba `[14]`

---

## Contract testing

El problema que resuelve: el servicio A se mockea a B con lo que *cree* que devuelve B. B cambia. Los tests
de A siguen verdes. Producción se rompe. **Los mocks no se enteran de que el otro lado cambió.**

- **Consumer-driven contracts (Pact):** el consumidor declara qué espera; ese contrato se verifica **contra
  el proveedor real** en el pipeline del proveedor. Si el proveedor rompe algo, su propio CI se pone rojo.
- **Schema-based:** validar contra el OpenAPI/Protobuf compartido en ambos lados.
- **Cuándo importa:** varios servicios y varios equipos. En un monolito no hace falta; el compilador ya lo
  hace.

> **Ficha** · **Cuándo:** varios servicios y varios equipos ·
> **Patrón:** el consumidor declara expectativas y se verifican en el **CI del proveedor** ·
> **Anti-patrón:** mocks del otro servicio que nadie actualiza cuando cambia ·
> **Límites:** verifica forma, no semántica ·
> **Cómo falla:** el proveedor cambia, los tests del consumidor siguen verdes, producción rompe ·
> **Decisión:** en un monolito no hace falta: el compilador ya lo hace ·
> **Trade-off:** infraestructura extra vs detectar roturas antes del despliegue ·
> **Relacionado:** OpenAPI, esquemas de eventos `[03, 08]`

---

## API testing

- **Prueba el contrato, no solo el camino feliz:** códigos de estado, forma del error, validación,
  autenticación **y autorización** (que el usuario A no pueda leer el recurso de B — los tests de IDOR
  deberían ser obligatorios, ver `06-security.md`).
- **Snapshot/golden tests** de respuestas para detectar cambios no intencionados en el contrato.
- **Validación contra el esquema OpenAPI** en los tests: si la respuesta no cumple el spec, falla. Es la
  única forma de que el spec no mienta.
- **Casos límite:** payload vacío, campos extra, tipos incorrectos, unicode, números enormes, arrays
  gigantes, paginación en el borde.

> **Ficha** · **Cuándo:** toda API expuesta ·
> **Patrón:** validar respuestas **contra el esquema OpenAPI** dentro de los tests ·
> **Anti-patrón:** probar solo 200 y olvidar los contratos de error ·
> **Límites:** un snapshot detecta cambios pero no dice si son correctos ·
> **Cómo falla:** el spec se desincroniza y nadie se entera hasta que un cliente se rompe ·
> **Decisión:** los tests de autorización cruzada son obligatorios ·
> **Trade-off:** rigidez del contrato vs libertad para evolucionar ·
> **Relacionado:** error contracts, IDOR `[03, 06]`

---

## Load testing y stress testing

No son lo mismo y confundirlos se nota:

| Tipo | Pregunta que responde |
|---|---|
| **Load** | ¿aguanta la carga esperada con la latencia objetivo? |
| **Stress** | ¿dónde se rompe y **cómo** se rompe? |
| **Soak** (resistencia) | ¿sobrevive 24h? (memory leaks, conexiones sin cerrar, discos que se llenan) |
| **Spike** | ¿sobrevive a un pico repentino? (autoscaling, colas, load shedding) |

**Herramientas:** k6 (JS, muy buena DX), Locust (Python), Gatling, wrk/vegeta para algo rápido.

**Cómo se hace bien:**
- **Define el objetivo antes:** "1.000 RPS con p99 < 300ms y menos de 0,1% de errores". Sin número objetivo,
  la prueba no tiene conclusión.
- **Carga realista:** proporciones de endpoints como en producción, datos con cardinalidad real (una prueba
  que consulta siempre el mismo ID tiene un 100% de aciertos de cache y no mide nada).
- **Calienta primero** (JIT, caches, pools) y mide en estado estacionario.
- **Observa el sistema, no solo el cliente.** El valor está en ver **qué** se satura primero: CPU, pool de
  conexiones, memoria, la DB, un servicio externo.
- **Lo que buscas en stress:** que degrade con gracia (load shedding, 429) en vez de colapsar. Un sistema que
  a 2× la carga devuelve 429 a un 10% está sano; uno que se queda sin memoria y reinicia, no.

> **Ficha** · **Cuándo:** antes de un lanzamiento o un pico previsto ·
> **Patrón:** objetivo numérico previo, carga realista, calentar y medir en estado estacionario ·
> **Anti-patrón:** consultar siempre el mismo ID (100% de aciertos de cache: no mides nada) ·
> **Límites:** el entorno de pruebas rara vez iguala a producción ·
> **Cómo falla:** se mide solo desde el cliente y no se ve **qué recurso** se satura primero ·
> **Decisión:** en stress buscas que **degrade con gracia** (429), no que aguante ·
> **Trade-off:** realismo vs coste de montar el entorno ·
> **Relacionado:** backpressure, capacity planning `[09, 19]`

---

## Mocks, stubs, fakes y fixtures

| Doble | Qué es |
|---|---|
| **Dummy** | relleno que no se usa |
| **Stub** | devuelve respuestas fijas |
| **Spy** | stub que además registra cómo lo llamaron |
| **Mock** | espera unas llamadas concretas y falla si no ocurren |
| **Fake** | implementación real pero simplificada (un repositorio en memoria) |

**Las reglas prácticas:**
- **Mockea las fronteras del sistema** (HTTP externo, pasarela de pago, envío de emails), **no tu propio
  código interno**. Mockear tus clases acopla el test a la estructura y te impide refactorizar.
- **Prefiere fakes a mocks.** Un repositorio en memoria produce tests más legibles y menos frágiles que
  cinco `when(...).thenReturn(...)`.
- **Para HTTP externo:** grabar/reproducir (VCR) o un servidor local (WireMock, `responses`). Y **un test
  de contrato aparte** que verifique periódicamente que el proveedor real sigue comportándose igual.
- **Fixtures:** usa *factories/builders* con valores por defecto sensatos en vez de un JSON gigante
  compartido. `crear_usuario(rol="admin")` se lee; un fixture de 200 líneas que usan 40 tests se convierte
  en un acoplamiento que nadie se atreve a tocar.

> **Ficha** · **Cuándo:** al aislar dependencias en tests ·
> **Patrón:** mockea las **fronteras del sistema**; prefiere fakes a mocks ·
> **Anti-patrón:** mockear tus propias clases internas ·
> **Límites:** un mock nunca se entera de que el otro lado cambió ·
> **Cómo falla:** cinco `when(...).thenReturn(...)` que solo verifican que el test conoce la implementación ·
> **Decisión:** factories con valores por defecto, no un JSON gigante compartido ·
> **Trade-off:** velocidad y aislamiento vs fidelidad ·
> **Relacionado:** contract testing, DI `[05]`

---

## Test databases

- **Testcontainers** es el estándar: un Postgres real y efímero por suite. Elimina toda la clase de bugs
  de "en SQLite pasaba".
- **Nunca uses SQLite para testear si en producción usas Postgres.** Difieren en tipos, transacciones,
  concurrencia y SQL. Los tests pasan y producción falla.
- **Aplica las migraciones reales** en el setup: así pruebas también las migraciones.
- **Paralelismo:** una base de datos o un esquema por worker.

> **Ficha** · **Cuándo:** cualquier test que toque persistencia ·
> **Patrón:** una base efímera por suite, con migraciones reales aplicadas ·
> **Anti-patrón:** una base compartida precargada que nadie sabe cómo se generó ·
> **Límites:** el paralelismo exige una base o un esquema por worker ·
> **Cómo falla:** tests que dependen de datos dejados por otro test ·
> **Decisión:** aplicar migraciones en el setup prueba también las migraciones ·
> **Trade-off:** tiempo de arranque vs fidelidad y aislamiento ·
> **Relacionado:** migraciones, fixtures `[04]`

---

## Property-based testing

En vez de ejemplos, declaras **propiedades que siempre deben cumplirse** y la librería (Hypothesis, fast-check)
genera cientos de casos y **reduce el contraejemplo al mínimo**.

```python
@given(st.lists(st.integers()))
def test_ordenar_es_idempotente(xs):
    assert ordenar(ordenar(xs)) == ordenar(xs)
```

**Propiedades típicas en backend:** ida y vuelta (`parse(serialize(x)) == x`), invariantes (el total nunca
es negativo), idempotencia (aplicar dos veces = aplicar una), y equivalencia con una implementación
ingenua pero obviamente correcta.

**Dónde brilla:** parsers, serialización, cálculos financieros, máquinas de estado. Encuentra los casos
límite que nadie habría escrito a mano (la lista vacía, el cero, el unicode raro, el desbordamiento).

> **Ficha** · **Cuándo:** parsers, serialización, cálculo financiero, máquinas de estado ·
> **Patrón:** invariantes — ida y vuelta, idempotencia, equivalencia con implementación ingenua ·
> **Anti-patrón:** usarlo para lógica con muchos efectos secundarios ·
> **Límites:** genera casos, no garantiza corrección ·
> **Cómo falla:** encuentra un contraejemplo que resulta ser un requisito no documentado ·
> **Decisión:** si el bug sería silencioso y corrompería datos, inviértelo aquí ·
> **Trade-off:** más lento y no determinista vs encuentra lo que nadie habría escrito ·
> **Relacionado:** fundamentos, fuzzing `[01]`

---

## Coverage y la estrategia general

- **La cobertura mide qué se ejecutó, no qué se verificó.** Un test sin asserts da cobertura del 100%.
- Un mínimo (60-80%) evita zonas totalmente a oscuras; perseguir el 100% produce tests basura para getters.
- **Mutation testing** sí mide calidad de verdad: introduce bugs a propósito y comprueba si algún test los
  detecta. Caro, pero revelador sobre módulos críticos.
- **Cobertura de lo que importa > cobertura global.** El módulo de cobros merece 95%; el de formateo de
  fechas, lo que salga.

**Qué hacer cuando aparece un bug:** escribe primero un test que lo reproduzca y falle, luego arréglalo.
Así el test demuestra que el arreglo funciona **y** te protege de la regresión. Es la forma más rentable de
construir una suite: cada test corresponde a un fallo real que ocurrió de verdad.

> **Ficha** · **Cuándo:** al fijar la política de calidad del repo ·
> **Patrón:** cobertura alta donde el fallo es caro; mutation testing en los módulos críticos ·
> **Anti-patrón:** perseguir el 100% — produce tests basura para getters ·
> **Límites:** la cobertura mide lo **ejecutado**, no lo verificado ·
> **Cómo falla:** un test sin asserts da 100% de cobertura ·
> **Decisión:** ante un bug, primero un test que lo reproduzca y falle ·
> **Trade-off:** tiempo de suite vs protección frente a regresiones ·
> **Relacionado:** flaky tests, CI `[14]`

---

## Escenarios de fallo y casos adversariales

Lo que separa una suite que da confianza de una que solo da cobertura: **probar lo que sale mal.**

**Por categoría, lo que hay que tener probado:**

| Categoría | Casos que deben existir |
|---|---|
| **Límites** | vacío, uno, el máximo, el máximo + 1, cero, negativo, nulo |
| **Texto** | unicode, emoji, RTL, cadena de 10.000 caracteres, cadena vacía, solo espacios |
| **Números** | 0, negativos, decimales con muchos dígitos, desbordamiento, divisas sin decimales `[07]` |
| **Tiempo** | cambio de hora, año bisiesto, zonas horarias, fin de mes, fechas futuras |
| **Concurrencia** | dos peticiones simultáneas sobre el mismo recurso `[01]` |
| **Autorización** | el usuario A intentando leer, editar y borrar lo del usuario B |
| **Reintentos** | el mismo request dos veces con la misma clave de idempotencia |
| **Dependencias** | el proveedor devuelve 500, timeout, respuesta malformada, o tarda 30s |
| **Datos** | fila que ya no existe, FK rota, campo nulo que "nunca lo es" |

**Los tests adversariales que deberían ser obligatorios en backend:**

```python
def test_el_usuario_a_no_puede_leer_lo_del_usuario_b(cliente, usuario_a, usuario_b):
    pedido_b = crear_pedido(usuario_b)
    r = cliente.get(f"/v1/pedidos/{pedido_b.id}", headers=auth(usuario_a))
    assert r.status_code == 404            # 404, no 403: no revelamos que existe [06]

def test_el_mismo_pago_con_la_misma_clave_solo_cobra_una_vez(cliente, usuario):
    cabeceras = {**auth(usuario), "Idempotency-Key": "abc-123"}
    r1 = cliente.post("/v1/pagos", json={"pedido_id": "p1"}, headers=cabeceras)
    r2 = cliente.post("/v1/pagos", json={"pedido_id": "p1"}, headers=cabeceras)
    assert r1.json()["id"] == r2.json()["id"]
    assert contar_cargos_en_el_psp() == 1

def test_no_se_puede_escalar_privilegios_por_el_body(cliente, usuario):
    cliente.patch("/v1/usuarios/yo", json={"rol": "admin"}, headers=auth(usuario))
    assert recargar(usuario).rol == "member"     # mass assignment [03]

def test_si_el_proveedor_tarda_demasiado_degradamos(cliente, proveedor_lento):
    r = cliente.get("/v1/producto/1")            # recomendaciones tardan 30s
    assert r.status_code == 200                  # la pagina sigue funcionando
    assert r.json()["recomendaciones"] == []     # degradado, no caido [10]
```

**Fuzzing** para parsers y endpoints que reciben datos externos: genera entradas aleatorias y malformadas
y comprueba que **nunca** provocan un 500 ni un cuelgue. Los 4xx están bien; los 5xx son bugs.

> **Ficha** · **Cuándo:** en todo endpoint público y toda integración ·
> **Patrón:** una tabla de categorías de fallo, y al menos un test por fila ·
> **Anti-patrón:** probar solo el camino feliz en el sandbox del proveedor ·
> **Límites:** no puedes enumerar todos los casos adversariales; el fuzzing cubre lo que no imaginaste ·
> **Cómo falla:** el IDOR y la fuga de campos no producen errores: pasan todos los tests del camino feliz ·
> **Decisión:** si el fallo sería **silencioso**, el test es obligatorio ·
> **Trade-off:** tiempo de suite vs clases enteras de bug detectadas ·
> **Relacionado:** IDOR, idempotencia, degradación `[03, 06, 10]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Qué cobertura de tests debería tener un proyecto?**
La suficiente para desplegar sin miedo, alta en el código crítico. *Señal:* explicas por qué la métrica es
engañosa (ejecutado ≠ verificado) y mencionas mutation testing como forma real de medir calidad.

**Q: ¿Unitarios o de integración en backend?**
Integración para casi todo lo que cruza una frontera (DB, HTTP, colas), unitarios para lógica de negocio
compleja. *Señal:* argumentas que los bugs reales en backend viven en las fronteras y que testcontainers
eliminó la excusa histórica de que los de integración son lentos.

**Q: Tu suite tiene tests que fallan aleatoriamente. ¿Qué haces?**
Tratarlos como bugs de prioridad alta: aislarlos, arreglar la causa (orden, estado compartido, tiempo, red,
concurrencia) y ponerlos en cuarentena mientras tanto. *Señal:* dices que el coste real de un flaky no es el
tiempo, es que **la gente deja de creerse los rojos**, y a partir de ahí la suite ya no protege nada.

**Q: ¿Cómo pruebas que tu integración con Stripe funciona?**
Tests con la librería mockeada para la lógica, más el entorno de test del proveedor para el flujo real, más
tests de tu manejador de webhooks con eventos de ejemplo firmados. *Señal:* mencionas probar la
**idempotencia y los duplicados** del webhook, que es donde están los bugs de verdad (`07-payments.md`).

**Q: ¿Qué es contract testing y cuándo lo necesitas?**
Verificar que las expectativas del consumidor se cumplen contra el proveedor real, en el CI del proveedor.
Lo necesitas con varios servicios y varios equipos. *Señal:* explicas el fallo concreto que evita — mocks
que se quedan desactualizados en silencio — porque es la razón de existir del patrón.

**Trade-off central de esta caja:** *confianza vs velocidad de feedback*. Cuanto más real es el test, más
confianza da y más tarda. El diseño de una buena suite consiste en **poner cada verificación en el nivel más
barato que aún la detecte**, y reservar los niveles caros para los caminos que de verdad pagan las facturas.

---

## Fuentes

- Martin Fowler, [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) y [Test Double](https://martinfowler.com/bliki/TestDouble.html)
- Kent C. Dodds, [The Testing Trophy](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- [Testcontainers](https://testcontainers.com/) · [Hypothesis](https://hypothesis.readthedocs.io/) · [k6](https://k6.io/docs/)
- [Pact — consumer-driven contract testing](https://docs.pact.io/)
