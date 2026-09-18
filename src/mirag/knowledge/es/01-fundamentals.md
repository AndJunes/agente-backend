# 01 · Fundamentals

> La base que se asume que ya tienes. Nadie te pregunta esto directamente en una entrevista senior,
> pero todo lo demás se derrumba si no lo dominas: te delatas al explicar por qué una query es lenta
> o por qué tu servicio se cae con 200 usuarios concurrentes.

**Cubre del temario:** `concepts` · `patterns` · `implementations` · `constraints` · `failure_modes`
· `tradeoffs` · `tests`

---

## Complejidad algorítmica

La notación Big-O describe **cómo crece** el coste cuando crece la entrada, no cuánto tarda. `O(n)` con
constante enorme puede ser más lento que `O(n²)` para n pequeño. En backend real, la constante y el
acceso a memoria mandan más de lo que la carrera te hizo creer.

| Notación | Nombre | Ejemplo típico en backend |
|---|---|---|
| O(1) | constante | lookup en hash map, acceso a Redis por key |
| O(log n) | logarítmica | búsqueda en índice B-tree, binary search |
| O(n) | lineal | recorrer una lista, full table scan |
| O(n log n) | linearítmica | sort, merge de listas ordenadas |
| O(n²) | cuadrática | doble bucle anidado, el clásico N+1 mal resuelto |
| O(2ⁿ) | exponencial | fuerza bruta sobre subconjuntos |

**Amortizado vs peor caso.** Un `append` a un array dinámico es O(1) amortizado, pero el resize puntual
es O(n). Si tienes un SLA de latencia p99, **el peor caso *es* tu latencia**.

**Complejidad espacial.** Cargar 2 millones de filas en memoria para "solo sumarlas" es el bug de
producción más común que existe. Streaming > cargar todo.

```python
# O(n) en tiempo y O(n) en MEMORIA: 2M de filas en RAM -> OOMKilled
total = sum(fila.importe for fila in cursor.fetchall())

# O(n) en tiempo y O(1) en memoria: el cursor va trayendo lotes
total = 0
for fila in cursor:              # server-side cursor
    total += fila.importe
```

> **Ficha** · **Cuándo:** al elegir estructura o algoritmo sobre colecciones que crecen ·
> **Patrón:** medir el orden de crecimiento antes de optimizar la constante ·
> **Anti-patrón:** optimizar un bucle O(n²) sobre 50 elementos que contiene 50 queries dentro ·
> **Límites:** Big-O ignora constantes y jerarquía de memoria; con n pequeño puede mentir ·
> **Cómo falla:** OOM por complejidad espacial, y p99 disparado por el peor caso amortizado ·
> **Decisión:** si el coste dominante es I/O, ataca el I/O, no el bucle ·
> **Trade-off:** tiempo vs memoria — casi toda aceleración se paga en RAM ·
> **Relacionado:** N+1 queries, query optimization `[04, 09]`

---

## Los números de latencia que hay que tener memorizados

```
referencia a L1 cache        ~1 ns
referencia a RAM             ~100 ns
leer 1 MB secuencial de RAM  ~10 µs
SSD random read              ~100 µs        (1.000× más lento que RAM)
round-trip en el mismo DC    ~500 µs
leer 1 MB de SSD             ~1 ms
round-trip intercontinental  ~150 ms
```

La conclusión práctica: **una llamada de red cuesta lo mismo que decenas de miles de operaciones en
memoria.** Por eso batching y caching ganan siempre, y por eso mover trabajo "a otro servicio" nunca
es gratis.

> **Ficha** · **Cuándo:** al estimar capacidad o decidir si algo se cachea `[19]` ·
> **Patrón:** convertir N llamadas en una (batching) antes que optimizar el cálculo ·
> **Anti-patrón:** microoptimizar CPU mientras haces un round trip por elemento ·
> **Límites:** la latencia no se arregla con más ancho de banda, solo estando más cerca ·
> **Cómo falla:** un servicio "rápido" con 200 llamadas internas encadenadas es lento sin que ninguna
> pieza parezca culpable · **Decisión:** si cruza la red, batch; si cruza el continente, cachea en el borde ·
> **Trade-off:** batching mejora throughput y empeora la latencia del elemento individual ·
> **Relacionado:** tail latency, CDN, capacity planning `[09, 13, 19]`

---

## Estructuras de datos

No se trata de implementar un red-black tree, sino de elegir la estructura correcta y saber qué pagas.

| Estructura | Búsqueda | Inserción | Cuándo la usas en backend |
|---|---|---|---|
| Array / slice | O(n) | O(1) al final | listas ordenadas, iteración, cache-friendly |
| Hash map | O(1) media | O(1) media | índices en memoria, dedup, counters |
| B-tree | O(log n) | O(log n) | **índices de base de datos** (disco: pocos niveles, mucho fanout) |
| LSM-tree | O(log n) | muy rápida | Cassandra, RocksDB: optimizado para escritura |
| Heap | O(1) el min | O(log n) | priority queues, schedulers, top-K |
| Trie | O(k) | O(k) | autocomplete, routing de URLs, prefijos |
| Bloom filter | O(k) probabilista | O(k) | "¿seguro que NO está?" antes de ir a disco |
| Skip list | O(log n) | O(log n) | Redis sorted sets |

**Las tres que separan a un senior:**

- **B-tree vs LSM-tree.** El B-tree actualiza en sitio (bueno para lecturas y updates, escribe amplificado
  por página). El LSM-tree escribe secuencialmente en niveles y compacta después (escrituras brutales,
  lecturas más caras). Postgres/MySQL = B-tree. Cassandra/RocksDB = LSM. **Si te preguntan "¿por qué
  Cassandra escribe tan rápido?", la respuesta es LSM + append-only.**
- **Bloom filter.** Puede dar falsos positivos pero **nunca falsos negativos**. Se usa para evitar I/O:
  "¿este key podría estar en este SSTable?" Si dice que no, te ahorras el disco.
- **Consistent hashing ring.** Repartir keys entre N nodos de forma que añadir un nodo solo mueva 1/N de
  los datos. Base de sharding y de caches distribuidos. **Cae muchísimo en system design.**

```python
# Consistent hashing en 12 lineas: el anillo es una lista ordenada de (hash, nodo)
import bisect, hashlib

class Anillo:
    def __init__(self, nodos, replicas=150):        # replicas = virtual nodes
        self.anillo = sorted(
            (self._h(f"{n}:{i}"), n) for n in nodos for i in range(replicas))

    def _h(self, clave):
        return int(hashlib.md5(clave.encode()).hexdigest(), 16)

    def nodo_de(self, clave):
        i = bisect.bisect(self.anillo, (self._h(clave),))
        return self.anillo[i % len(self.anillo)][1]   # el siguiente en el anillo
```

> **Ficha** · **Cuándo:** al diseñar índices, caches o repartir datos entre nodos ·
> **Patrón:** virtual nodes para que el reparto sea uniforme con pocos nodos físicos ·
> **Anti-patrón:** `hash(key) % N` para repartir: añadir un nodo remapea **todo** ·
> **Límites:** el bloom filter no permite borrar; el hash map degrada a O(n) con colisiones ·
> **Cómo falla:** hotspots cuando la clave de reparto no es uniforme (un tenant enorme) ·
> **Decisión:** LSM si el cuello es escritura, B-tree si es lectura y update ·
> **Trade-off:** memoria vs velocidad de acceso, y escritura vs lectura (LSM vs B-tree) ·
> **Relacionado:** índices, sharding, caching `[04, 09]`

---

## Concurrencia vs paralelismo

No son lo mismo y confundirlos en una entrevista es una bandera roja.

- **Concurrencia** = gestionar varias tareas *en progreso* a la vez (pueden intercalarse en un solo core).
  Es un modelo de *estructura* del programa.
- **Paralelismo** = ejecutar varias cosas *simultáneamente* en varios cores. Es un modelo de *ejecución*.

> "Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at
> once." — Rob Pike

Un servidor Node.js es **concurrente pero no paralelo** (un solo hilo de JS). Maneja 10.000 conexiones
porque casi todo el tiempo está esperando I/O, no calculando.

**Los tres modelos que vas a encontrar:**

1. **Thread por request** (Java tradicional, Rails, PHP-FPM). Cada request ocupa un OS thread. Simple de
   razonar; cada thread cuesta ~1 MB de stack y el context switch es caro. Techo: miles, no cientos de miles.
2. **Event loop / async I/O** (Node, asyncio, nginx). Un hilo, una cola de eventos. Escala a decenas de
   miles de conexiones con poca RAM. **Precio: si bloqueas el loop, matas todo el servidor.**
3. **Green threads / corrutinas** (Go, Java 21+ virtual threads, Erlang). El runtime multiplexa millones de
   "hilos" ligeros sobre pocos OS threads. Escribes código secuencial y obtienes escalado de event loop.
   **Es el modelo que ha ganado.**

> **Ficha** · **Cuándo:** al elegir stack y al dimensionar workers ·
> **Patrón:** I/O-bound → concurrencia; CPU-bound → paralelismo real (procesos) ·
> **Anti-patrón:** "añadir threads" para acelerar un cálculo en Python (GIL) ·
> **Límites:** el event loop es un solo core; thread-per-request tiene techo de memoria ·
> **Cómo falla:** un `bcrypt` o un `json.loads` de 50 MB dentro del event loop congela **todas** las conexiones ·
> **Decisión:** si tu carga es esperar a la DB y a APIs (el 95% del backend), concurrencia basta ·
> **Trade-off:** simplicidad de razonamiento (threads) vs escala con poca RAM (event loop) ·
> **Relacionado:** async/await, connection pools, backpressure `[09]`

---

## Patrones de concurrencia

Los cuatro que aparecen una y otra vez en backend, y que se implementan igual en cualquier lenguaje.

**1. Worker pool** — N trabajadores consumen de una cola. Es **el patrón por defecto** para limitar
concurrencia: procesas rápido sin abrir 10.000 conexiones a la vez.

```python
import asyncio

async def worker_pool(tareas, trabajo, n=10):
    cola = asyncio.Queue()
    for t in tareas:
        cola.put_nowait(t)

    async def worker():
        while not cola.empty():
            await trabajo(await cola.get())

    await asyncio.gather(*[worker() for _ in range(n)])   # exactamente n en vuelo
```

**2. Producer-consumer con cola acotada** — el productor se bloquea si la cola está llena. Es
**backpressure** implementado en tres líneas: `asyncio.Queue(maxsize=100)`.

**3. Fan-out / fan-in** — lanzas N tareas independientes en paralelo y esperas a todas.

```python
usuario, pedidos, saldo = await asyncio.gather(
    get_usuario(uid), get_pedidos(uid), get_saldo(uid))   # 100ms en vez de 300ms
```

**4. Pipeline** — etapas encadenadas por colas, cada una con su propia concurrencia. Permite que la etapa
lenta tenga más workers que la rápida.

> **Ficha** · **Cuándo:** siempre que proceses una colección contra recursos externos ·
> **Patrón:** concurrencia **acotada** (semáforo o pool), nunca ilimitada ·
> **Anti-patrón:** `gather` sobre 10.000 items: abres 10.000 conexiones y tumbas la DB ·
> **Límites:** el paralelismo útil lo marca el recurso más lento, no el número de workers ·
> **Cómo falla:** sin cola acotada, un productor rápido llena la memoria hasta el OOM ·
> **Decisión:** worker pool si las tareas son homogéneas; pipeline si tienen etapas de coste distinto ·
> **Trade-off:** más workers = más throughput hasta saturar, y después menos (contención) ·
> **Relacionado:** backpressure, connection pooling, colas `[08, 09]`

---

## Async / await

Azúcar sintáctico sobre "registra una continuación y devuelve el control".

```python
# Esto NO es concurrente: await secuencial = esperar uno detrás de otro
a = await fetch_usuario()      # 100ms
b = await fetch_pedidos()      # 100ms  -> total 200ms

# Esto SÍ: lanzas las dos y esperas juntas
a, b = await asyncio.gather(fetch_usuario(), fetch_pedidos())   # total 100ms

# Y esto es lo correcto cuando son muchas: acotado con semáforo
sem = asyncio.Semaphore(10)
async def limitado(coro):
    async with sem:
        return await coro
resultados = await asyncio.gather(*(limitado(fetch(i)) for i in ids))
```

**Los cuatro errores que se ven en producción:**

1. **Bloquear el event loop** con trabajo síncrono pesado. Solución: `run_in_executor` / `worker_threads`.
2. **Función color / async contagioso.** Una función async solo se llama desde async; mezclar produce
   wrappers feos y bugs sutiles.
3. **Fire-and-forget sin referencia.** Si no guardas la task, el GC puede matarla a mitad y la excepción
   se pierde en silencio.
4. **Sin límite de concurrencia** (ver arriba).

> **Ficha** · **Cuándo:** todo backend I/O-bound moderno ·
> **Patrón:** `gather` para independientes + semáforo para acotar ·
> **Anti-patrón:** `time.sleep()`, `requests.get()` o un hash bcrypt dentro de una corrutina ·
> **Límites:** no acelera CPU; un solo hilo sigue siendo un solo core ·
> **Cómo falla:** una tarea bloqueante hace que **todas** las peticiones sufran, no solo la suya ·
> **Decisión:** trabajo CPU-intensivo → executor o proceso aparte; nunca en el loop ·
> **Trade-off:** rendimiento vs complejidad de depuración (los stack traces async son peores) ·
> **Relacionado:** patrones de concurrencia, GIL, backpressure `[09]`

---

## Threads vs processes

| | Thread | Process |
|---|---|---|
| Memoria | compartida | aislada |
| Coste de crear | bajo (~µs) | alto (~ms) |
| Comunicación | variables compartidas (necesita locks) | IPC, pipes, sockets (serializar) |
| Un crash | mata todo el proceso | aislado |
| Paralelismo real en Python | **no** (GIL) | sí |

**El GIL de Python** permite solo un bytecode a la vez por proceso. Threads en Python sirven para
I/O-bound (el GIL se libera durante el I/O), **nunca** para CPU-bound. (Python 3.13+ tiene un build
experimental sin GIL — *free-threading* — que en 2026 aún no es el default de producción.)

**Modelo típico de producción:** N procesos (uno por core) × un event loop dentro de cada uno. Es
literalmente lo que hace `gunicorn -k uvicorn.workers.UvicornWorker -w 4`.

> **Ficha** · **Cuándo:** al dimensionar el servidor de aplicación ·
> **Patrón:** procesos = `núcleos disponibles`; dentro, async o threads según el lenguaje ·
> **Anti-patrón:** 32 workers en un contenedor con 1 CPU: solo añades context switching ·
> **Límites:** cada proceso duplica la memoria base de la app; cada thread cuesta su stack ·
> **Cómo falla:** memoria compartida sin lock → race condition; procesos de más → OOMKilled ·
> **Decisión:** CPU-bound en Python → `multiprocessing`; I/O-bound → async ·
> **Trade-off:** aislamiento (procesos) vs coste de comunicación y memoria ·
> **Relacionado:** contenedores y límites de recursos `[13]`

---

## Memory management

- **Stack:** rápido, LIFO, se libera solo. Tamaño limitado (de ahí el stack overflow por recursión).
- **Heap:** dinámico, lo gestiona el allocator o el GC. Fragmentación y coste de asignación viven aquí.

**Garbage collection** te ahorra bugs de memoria y te cobra en **pausas**. Los GC modernos (G1, ZGC, el
generacional de Go) buscan pausas sub-milisegundo, pero bajo presión de memoria el p99 de tu API se
dispara. **Si tu latencia tiene picos periódicos inexplicables, sospecha del GC.**

**Memory leaks con GC** son referencias que no sueltas: caches sin límite ni TTL, listeners que nunca se
desregistran, closures que capturan objetos gigantes, conexiones sin cerrar.

> **Ficha** · **Cuándo:** al depurar consumo creciente o picos de latencia periódicos ·
> **Patrón:** todo cache en memoria lleva **tamaño máximo y TTL** ·
> **Anti-patrón:** un `dict` global que acumula por request "para acelerar" ·
> **Límites:** el contenedor tiene un límite duro; superarlo es muerte inmediata, no degradación ·
> **Cómo falla:** OOMKilled y reinicio en bucle; o GC thrashing (la app "vive" pero no avanza) ·
> **Decisión:** si el tamaño de lo que procesas no está acotado, streaming obligatorio ·
> **Trade-off:** cachear en memoria es lo más rápido y lo que peor escala horizontalmente ·
> **Relacionado:** caching, límites de contenedor, backpressure `[09, 13]`

---

## Error handling

La diferencia entre junior y senior está casi entera aquí.

| Tipo | Ejemplo | Qué haces |
|---|---|---|
| Esperado / de negocio | saldo insuficiente, email duplicado | 4xx con contrato claro, **no** loguear como error |
| Transitorio | timeout de red, 503 del proveedor | **retry con backoff** |
| Permanente | payload inválido, 401 | fallar rápido, no reintentar |
| Programación | null pointer, índice fuera de rango | loguear con stack, alertar, arreglar |
| Catastrófico | DB caída, disco lleno | circuit breaker, degradar, alertar |

```python
class ErrorDeNegocio(Exception):      # -> 4xx, esperado, no alerta
    codigo = "generico"

class SaldoInsuficiente(ErrorDeNegocio):
    codigo = "saldo_insuficiente"

class ErrorTransitorio(Exception):    # -> reintentable
    pass

try:
    cobrar(pedido)
except SaldoInsuficiente:
    raise                                            # sube tal cual, el borde lo traduce a 409
except TimeoutError as e:
    raise ErrorTransitorio(f"timeout cobrando el pedido {pedido.id}") from e   # contexto + causa
```

**Principios:** falla rápido en desarrollo, degrada con gracia en producción · **nunca `catch` vacío**
(el log silencioso es el peor bug: el sistema miente sobre su estado) · envuelve añadiendo contexto,
no tragues · la idempotencia y los errores van juntos: si reintentas, el error transitorio no debe
duplicar el efecto.

> **Ficha** · **Cuándo:** en cada frontera del sistema ·
> **Patrón:** jerarquía de excepciones que distingue negocio / transitorio / programación ·
> **Anti-patrón:** `except Exception: pass`, y devolver 200 con `{"error": ...}` dentro ·
> **Límites:** no puedes distinguir un timeout "no llegó" de "llegó y no vi la respuesta" ·
> **Cómo falla:** reintentar un error permanente multiplica la carga sin arreglar nada ·
> **Decisión:** ¿es reintentable? Solo si es transitorio **y** la operación es idempotente ·
> **Trade-off:** errores como valores (explícito, verboso) vs excepciones (limpio, fácil de ignorar) ·
> **Relacionado:** retries, idempotencia, error contracts `[03, 08, 10]`

---

## Networking básico

El detalle está en `[02]`. Lo mínimo para no quedar en evidencia:

- **El modelo mental:** DNS resuelve nombre → IP · TCP establece conexión · TLS negocia cifrado ·
  HTTP transporta el mensaje.
- **TCP vs UDP:** TCP garantiza orden y entrega (con coste de handshake y retransmisión); UDP no
  garantiza nada. HTTP/3 corre sobre QUIC, que es UDP con fiabilidad encima.
- **Sockets y file descriptors:** cada conexión abierta es un FD. El límite `ulimit -n` es la causa real
  de muchísimos "too many open files" bajo carga.
- **Latencia vs throughput:** no puedes arreglar la latencia con más ancho de banda — solo estando más
  cerca (CDN) o hablando menos (batching).

> **Ficha** · **Cuándo:** al depurar cualquier fallo que cruce la red ·
> **Patrón:** conexiones persistentes y pooling en vez de abrir una por operación ·
> **Anti-patrón:** abrir una conexión nueva a la DB en cada request ·
> **Límites:** file descriptors, puertos efímeros (~28.000), y `TIME_WAIT` de 60s ·
> **Cómo falla:** "too many open files" o "cannot assign requested address" bajo carga ·
> **Decisión:** si abres y cierras mucho, pool; si el destino está lejos, cachea en el borde ·
> **Trade-off:** conexiones persistentes ahorran handshakes y consumen FDs ociosos ·
> **Relacionado:** connection pooling, TCP handshake `[02, 04, 09]`

---

## Paradigmas y patrones

**Paradigmas:** OOP (encapsulación, polimorfismo; peligroso cuando la herencia crece — **composición
sobre herencia**) · funcional (funciones puras e inmutabilidad: gana en concurrencia porque no hay estado
compartido) · procedural (a veces una función que transforma datos es todo lo que necesitas).

**Patrones que usas a diario** (el catálogo en `[05]`): Repository · Factory · Strategy · Adapter ·
Decorator/middleware · Observer/pub-sub · Singleton (el más abusado: un global disfrazado que arruina
los tests).

**El anti-patrón que más caro sale:** *premature abstraction*. Tres capas de interfaces con una sola
implementación cada una no es arquitectura limpia, es deuda. **La regla de tres:** abstrae cuando
aparezca el tercer caso, no el primero.

> **Ficha** · **Cuándo:** al estructurar código que va a cambiar ·
> **Patrón:** composición sobre herencia; inmutabilidad por defecto ·
> **Anti-patrón:** abstraer con un solo caso de uso; jerarquías de herencia de 6 niveles ·
> **Límites:** cada abstracción cuesta un salto mental al leer el código ·
> **Cómo falla:** el código "flexible" que nadie entiende acaba reescrito ·
> **Decisión:** ¿hay tres casos reales? Entonces abstrae ·
> **Trade-off:** flexibilidad futura vs legibilidad hoy ·
> **Relacionado:** SOLID, design patterns, DI `[05]`

---

## Cómo se prueba todo esto

Los fundamentos tienen una estrategia de prueba propia, distinta de la de una API (`[11]`).

**Algoritmos y estructuras → property-based testing.** En vez de ejemplos, declaras invariantes y la
librería genera cientos de casos y reduce el contraejemplo al mínimo.

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_ordenar_es_idempotente(xs):
    assert ordenar(ordenar(xs)) == ordenar(xs)

@given(st.text())
def test_serializar_ida_y_vuelta(s):
    assert deserializar(serializar(s)) == s      # encuentra el unicode raro que no pensaste
```

**Concurrencia → determinismo forzado.** Las race conditions no se reproducen con un test normal.
Lo que funciona: inyectar el reloj y la aleatoriedad (nunca `now()` ni `random()` directos), ejecutar
la operación N veces en paralelo y afirmar sobre el **estado final**, y usar detectores del lenguaje
(`-race` en Go, ThreadSanitizer).

```python
def test_no_se_vende_stock_de_mas():
    with ThreadPoolExecutor(max_workers=50) as ex:
        resultados = list(ex.map(lambda _: comprar(producto_id=1), range(50)))
    assert sum(resultados) == 10          # solo 10 unidades habia
    assert stock(1) == 0                  # y nunca negativo
```

**Rendimiento → benchmark con umbral en CI**, no "parece rápido". **Memoria → soak test**: ejecuta una
hora y comprueba que la memoria no crece de forma monótona.

> **Ficha** · **Cuándo:** en código con invariantes fuertes o concurrencia ·
> **Patrón:** property-based para lógica pura; ejecución paralela + aserción sobre estado final para concurrencia ·
> **Anti-patrón:** un `sleep(0.1)` para "sincronizar" el test — es flaky garantizado ·
> **Límites:** que el test pase no prueba ausencia de race conditions, solo que no apareció ·
> **Cómo falla:** tests que pasan en local y fallan en CI (otra máquina, otro número de cores) ·
> **Decisión:** si el bug sería silencioso y corrompería datos, invierte en property-based ·
> **Trade-off:** los tests de concurrencia son lentos y no deterministas: sepáralos de la suite rápida ·
> **Relacionado:** property-based testing, flaky tests, load testing `[11]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Diferencia entre concurrencia y paralelismo?**
Concurrencia es estructura (varias tareas en progreso, intercaladas); paralelismo es ejecución simultánea
en varios cores. *Señal:* pones el ejemplo de Node — concurrente con un solo hilo — y explicas que la
concurrencia es lo que te salva en workloads I/O-bound, que es el 95% del backend.

**Q: Tu API tiene picos de latencia en el p99 cada pocos minutos. ¿Por dónde empiezas?**
GC pauses, expiración de cache sincronizada, un cron que compite por recursos, pool agotado, o CPU
throttling del contenedor. *Señal:* mencionas que miras p99 y no la media, y que el primer paso es
correlacionar el pico con métricas de GC, de pool y de throttling.

**Q: ¿Por qué no usar threads en Python para acelerar un cálculo pesado?**
El GIL. Para CPU-bound necesitas procesos. *Señal:* sabes que para I/O-bound los threads sí sirven porque
el GIL se libera durante el I/O, y mencionas el free-threading build como la dirección futura.

**Q: ¿Cómo evitas un deadlock?**
Orden global de adquisición de locks, timeouts, transacciones cortas y reducir el scope del lock.
*Señal:* mencionas que en la práctica los que te muerden son los de la base de datos, que Postgres los
detecta y mata una víctima, y que **tu código debe reintentar esa transacción**.

**Q: ¿Cómo pruebas que no hay una race condition en tu contador?**
Ejecutas N operaciones en paralelo y afirmas sobre el estado final, con detector de races si el lenguaje
lo tiene. *Señal:* reconoces que un test verde no demuestra ausencia de races, y que la solución robusta
es de diseño (operación atómica en la DB) y no de testing.

**Trade-off central de esta caja:** *simplicidad vs control*. Un event loop escala más con menos RAM pero
te obliga a no bloquear nunca; thread-per-request es trivial de depurar pero tiene techo. Go y Java 21
intentan darte los dos. Elegir mal aquí condiciona toda la arquitectura del servicio.

---

## Fuentes

- Rob Pike, *Concurrency is not Parallelism* — la distinción canónica.
- Jeff Dean, *Latency Numbers Every Programmer Should Know* — origen de la tabla de latencias.
- Python docs: [GIL](https://docs.python.org/3/glossary.html#term-global-interpreter-lock) ·
  [PEP 703 free-threading](https://peps.python.org/pep-0703/)
- [Hypothesis](https://hypothesis.readthedocs.io/) — property-based testing en Python.
