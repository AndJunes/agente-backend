"""Los vectores del retrieval, detras de una interfaz con dos backends.

El de por defecto (`VectorLocalHash`) NO son embeddings: es una señal LEXICA, de
caracteres. Hashea n-gramas de caracteres y compara con coseno, asi que mide
"¿cuantos trocitos de letra comparten estos dos textos?" y nada mas. Eso aporta
tres cosas reales al buscador por palabras de `rag.py`:

  · tolerancia a erratas ('postgress' sigue cayendo cerca de 'postgres'),
  · solape parcial de palabras (indice / indices / indexacion / indexing),
  · mezcla español-ingles cuando las dos formas se parecen (latencia / latency).

Y NO aporta semantica, que es justo lo que la gente asume al ver la palabra
"vector": esto no une 'health check' con 'readiness probe', ni 'caida' con
'outage', porque no comparten caracteres. Si hace falta eso, hace falta el otro
backend. Por eso en todo el modulo no aparece la palabra embedding para hablar
del local: no lo es, y llamarlo asi haria que alguien confiara en algo que no hace.

El backend remoto (`VectorOpenRouter`) si pide embeddings de verdad, pero nace
apagado: cuesta dinero, latencia y una clave. Esta escrito para mañana, con el
candado de `agent.OFFLINE` delante y cache de ingesta, para que encenderlo sea
cambiar una variable y no reescribir el retrieval.

    MIRAG_VECTOR_BACKEND=openrouter MIRAG_OFFLINE=0 python3 vectores.py
"""

import hashlib
import json
import math
import os
import urllib.error
import urllib.request
import zlib
from pathlib import Path

import agent
import config
import rag

CARPETA_CACHE = Path(__file__).parent / "embeddings"

# Si cambia como se construyen o se guardan los vectores, cambia esto: invalida
# toda la cache de golpe. Es mas barato re-ingerir que servir vectores viejos
# mezclados con nuevos y no enterarse.
VERSION_EMBEDDING = "v1"

MODELO_EMBEDDING = "openai/text-embedding-3-small"
URL_EMBEDDINGS = "https://openrouter.ai/api/v1/embeddings"
LOTE = 64                 # el endpoint acepta arrays: una llamada por cada 64 textos
TIMEOUT = 30

# Indireccion a proposito. Los tests sustituyen ESTE nombre para probar los fallos
# de red (HTTPError, timeout, JSON roto) sin abrir un socket y sin parchear el
# urllib global, que se lo colaria a agent.py y a cualquier otro modulo.
_URLOPEN = urllib.request.urlopen


class VectorStore:
    """La interfaz comun. Lo unico que el resto del proyecto puede dar por hecho."""

    nombre = "base"

    def __init__(self):
        self.textos = []
        self.motivo = ""        # por que no se pudo usar, si no se pudo
        self.fallback = None    # puesto por obtener() cuando este store es el plan B

    @property
    def disponible(self) -> bool:
        return True

    @property
    def listo(self) -> bool:
        """Hay vectores utilizables. Indexar puede fallar sin lanzar nada."""
        return bool(self._vectores)

    def indexar(self, textos: list) -> None:
        raise NotImplementedError

    def buscar(self, consulta: str, k: int = 5) -> list:
        raise NotImplementedError


def _coseno(consulta, vectores, k):
    """Coseno = producto punto, porque todo entra ya normalizado a norma 1.

    La consulta viene dispersa ({indice: peso}) y los documentos densos: asi cada
    documento cuesta las ~30 dimensiones que la consulta toca, no las 512.
    """
    if not consulta or not vectores:
        return []
    pares = []
    for i, doc in enumerate(vectores):
        s = sum(peso * doc[j] for j, peso in consulta.items() if j < len(doc))
        if s > 0:               # el hashing con signo produce negativos: eso es "nada que ver"
            pares.append((i, min(1.0, s)))
    pares.sort(key=lambda p: (-p[1], p[0]))   # el indice desempata, para que sea reproducible
    return pares[:k]


class VectorLocalHash(VectorStore):
    """Señal lexica local: n-gramas de caracteres hasheados + coseno. Sin red y gratis.

    Insisto porque la clase se va a usar donde uno espera embeddings: esto NO
    entiende lo que dice el texto. Dos frases que significan lo mismo con palabras
    distintas puntuan cero. Lo que si hace es aguantar erratas, plurales, sufijos y
    el espanglish del corpus, que es la parte que al buscador por palabras se le escapa.

    El hash es `zlib.crc32`, no el `hash()` de Python: `hash()` esta aleatorizado
    por PYTHONHASHSEED y devolveria vectores distintos en cada proceso. Eso
    romperia cualquier cache en disco y haria que un test verde hoy fuese rojo
    mañana sin tocar una linea.

    SUELO DE RUIDO, medido y no teorico: con dim=512 una consulta corta toca unas
    20 dimensiones y un trozo del corpus toca casi las 512, asi que siempre
    colisionan y una consulta SIN NADA en comun puntua ~0.10 en vez de 0. Una
    coincidencia de verdad puntua ~0.49, o sea que el margen es de 4.8x y el
    ranking aguanta; lo que no aguanta es leer el score como probabilidad. Un
    0.10 aqui no significa "un 10% parecido", significa "nada". Subir dim lo
    hunde (0.025 con 1024, 0.0 con 8192) a cambio de memoria y de tiempo de
    consulta; 512 se queda por defecto porque el ranking ya es correcto y lo que
    consume el buscador es el ORDEN, no el numero.
    """

    nombre = "local"

    def __init__(self, dim=512, n=3):
        super().__init__()
        self.dim = dim
        self.n = n
        self._vectores = []

    def _ngramas(self, texto):
        """n-gramas de caracteres del texto normalizado (minusculas, sin acentos).

        Se colapsan los espacios y se rodea de un espacio para que el principio y el
        final de cada palabra sean tambien un n-grama: es lo que hace que 'postgres'
        y 'postgress' compartan casi todos sus trozos.
        """
        t = " " + " ".join(rag._normalizar(texto).split()) + " "
        if len(t) <= 2:                     # solo el relleno: no habia texto
            return []
        return [t[i:i + self.n] for i in range(len(t) - self.n + 1)]

    def _pesos(self, texto):
        """{dimension: peso} ya normalizado a norma 1.

        Hashing trick con signo: el bit alto del crc32 decide si el n-grama suma o
        resta. Sin signo, dos n-gramas que colisionan siempre se refuerzan y todo el
        corpus acaba pareciendose a todo; con signo las colisiones se cancelan de
        media y el ruido deja de inflar los scores.
        """
        v = {}
        for g in self._ngramas(texto):
            h = zlib.crc32(g.encode())
            i = h % self.dim
            v[i] = v.get(i, 0.0) + (1.0 if h & 0x80000000 else -1.0)
        norma = math.sqrt(sum(x * x for x in v.values()))
        if not norma:
            return {}
        return {i: x / norma for i, x in v.items() if x}

    def vector(self, texto: str) -> list:
        """El vector denso. Publico porque es lo unico inspeccionable de este backend."""
        pesos = self._pesos(texto)
        denso = [0.0] * self.dim
        for i, x in pesos.items():
            denso[i] = x
        return denso

    def indexar(self, textos: list) -> None:
        self.textos = list(textos)
        self._vectores = [self.vector(t) for t in self.textos]

    def buscar(self, consulta: str, k: int = 5) -> list:
        return _coseno(self._pesos(consulta), self._vectores, k)


class VectorOpenRouter(VectorStore):
    """Embeddings de verdad via OpenRouter. Opcional, apagado y tolerante a fallos.

    Dos reglas que no se negocian:

      · el candado primero: con `agent.OFFLINE` puesto (o sin clave) no se intenta
        nada, ni un socket. Un test no puede generar factura por despiste.
      · nada de aqui se propaga: si la red, el proveedor o el JSON fallan, se anota
        el motivo y `obtener()` se queda con el backend local. El retrieval
        degradado es una molestia; el retrieval caido es una caida.
    """

    nombre = "openrouter"

    def __init__(self, modelo=MODELO_EMBEDDING, carpeta=None, timeout=TIMEOUT):
        super().__init__()
        self.modelo = modelo
        self.carpeta = Path(carpeta) if carpeta else CARPETA_CACHE
        self.timeout = timeout
        self.llamadas = 0          # para poder demostrar que la cache no llamo
        self._vectores = []

    # ── el candado ───────────────────────────────────────────────────────────

    def _impedimento(self):
        """Motivo por el que NO se puede llamar ahora mismo, o '' si se puede.

        Se calcula cada vez y no en el __init__: entre importar el modulo y usarlo
        pueden cambiar tanto el candado como la clave (los tests hacen justo eso).
        """
        if agent.OFFLINE:
            return "MIRAG_OFFLINE esta puesto: no se llama a OpenRouter"
        if not os.environ.get("OPENROUTER_API_KEY"):
            return "no hay OPENROUTER_API_KEY"
        return ""

    @property
    def disponible(self) -> bool:
        return not self._impedimento()

    # ── la cache de ingesta ──────────────────────────────────────────────────

    @staticmethod
    def corpus_hash(textos) -> str:
        """Identidad del corpus por CONTENIDO: si cambia un trozo, cambia la ruta."""
        crudo = "\n".join(textos).encode()
        return hashlib.sha256(crudo).hexdigest()[:16]

    def ruta_cache(self, corpus_hash) -> Path:
        # el modelo lleva '/' y no puede ser un nombre de archivo
        return self.carpeta / corpus_hash / (self.modelo.replace("/", "_") + ".json")

    def _leer_cache(self, corpus_hash):
        """Los vectores guardados, o None si no valen. Tres motivos para no valer."""
        try:
            datos = json.loads(self.ruta_cache(corpus_hash).read_text())
        except (OSError, ValueError):
            return None
        if (datos.get("version") != VERSION_EMBEDDING       # cambio como los calculamos
                or datos.get("modelo") != self.modelo        # cambio el modelo
                or datos.get("corpus_hash") != corpus_hash): # cambio el corpus
            return None
        vectores = datos.get("vectores")
        if not isinstance(vectores, list) or len(vectores) != len(self.textos):
            return None
        return vectores

    def _escribir_cache(self, corpus_hash, vectores):
        ruta = self.ruta_cache(corpus_hash)
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps({
                "version": VERSION_EMBEDDING,
                "modelo": self.modelo,
                "corpus_hash": corpus_hash,
                "vectores": vectores,
            }))
        except OSError as e:
            # no poder guardar es caro (se re-ingiere), pero no es un fallo de busqueda
            self.motivo = f"no se pudo escribir la cache: {e}"

    # ── la llamada ───────────────────────────────────────────────────────────

    def _pedir(self, textos):
        """Los vectores crudos de esos textos. Lanza si algo no cuadra: lo caza indexar().

        Lleva el candado aunque `indexar` y `buscar` ya lo comprueben: este es el UNICO
        sitio del modulo donde se abre un socket, y una ruta nueva que llame aqui sin
        pasar por los otros dos generaria factura en silencio.
        """
        if impedimento := self._impedimento():
            raise RuntimeError(impedimento)
        salida = []
        for inicio in range(0, len(textos), LOTE):
            lote = textos[inicio:inicio + LOTE]
            body = json.dumps({"model": self.modelo, "input": lote}).encode()
            req = urllib.request.Request(URL_EMBEDDINGS, data=body, headers={
                "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
                "Content-Type": "application/json",
            })
            self.llamadas += 1
            respuesta = json.loads(_URLOPEN(req, timeout=self.timeout).read())
            datos = respuesta.get("data")
            if not isinstance(datos, list) or len(datos) != len(lote):
                # un lote corto no se rellena con ceros: eso desalinearia los indices
                # con los textos y el buscador devolveria el documento equivocado
                raise ValueError(
                    f"el proveedor devolvio {len(datos or [])} vectores para {len(lote)} textos")
            for d in sorted(datos, key=lambda d: d.get("index", 0)):
                vector = d.get("embedding")
                if not isinstance(vector, list) or not vector:
                    raise ValueError("una entrada de 'data' viene sin 'embedding'")
                salida.append([float(x) for x in vector])
        return salida

    @staticmethod
    def _normalizado(vector):
        norma = math.sqrt(sum(x * x for x in vector))
        return [x / norma for x in vector] if norma else list(vector)

    def indexar(self, textos: list) -> None:
        self.textos = list(textos)
        self._vectores = []
        self.motivo = ""
        if not self.textos:
            return
        ch = self.corpus_hash(self.textos)
        if (cache := self._leer_cache(ch)) is not None:
            self._vectores = [self._normalizado(v) for v in cache]
            return                                  # cache: cero llamadas, cero coste
        if impedimento := self._impedimento():
            self.motivo = impedimento
            return
        try:
            crudos = self._pedir(self.textos)
        except Exception as e:
            # a proposito tan ancho: red, HTTP, JSON, formato del proveedor y hasta un
            # bug de parseo. Ninguno de esos vale una caida del retrieval.
            self.motivo = f"{type(e).__name__}: {e}"
            return
        self._vectores = [self._normalizado(v) for v in crudos]
        self._escribir_cache(ch, crudos)

    def buscar(self, consulta: str, k: int = 5) -> list:
        """Ojo: aqui SI hay una llamada por consulta. La cache solo cubre la ingesta."""
        if not self._vectores or not consulta.strip():
            return []
        if impedimento := self._impedimento():
            self.motivo = impedimento
            return []
        try:
            vector = self._normalizado(self._pedir([consulta])[0])
        except Exception as e:
            self.motivo = f"{type(e).__name__}: {e}"
            return []
        return _coseno(dict(enumerate(vector)), self._vectores, k)


def obtener(backend: str = None, textos: list = None) -> VectorStore:
    """El store que toca. Si pides openrouter y no se puede, te doy el local.

    `textos` es opcional y no estaba en el plan, pero sin el la promesa "si falla,
    cae al local" es mentira: un fallo de OpenRouter no se ve al construir el
    objeto, se ve al ingerir. Pasando el corpus aqui la degradacion ocurre en un
    solo sitio y quien llama recibe un store YA indexado y utilizable.

    El motivo de la caida va en `.fallback` en vez de en un log: la traza tiene que
    poder decir "no se uso openrouter porque X", igual que hace config.activar().
    """
    nombre = (backend or config.VECTOR_BACKEND or "local").strip().lower()
    if nombre != "openrouter":
        local = VectorLocalHash()
        if textos is not None:
            local.indexar(textos)
        return local

    remoto = VectorOpenRouter()
    motivo = remoto._impedimento()
    if not motivo:
        if textos is None:
            return remoto                       # sin corpus no hay nada que intentar todavia
        remoto.indexar(textos)
        if remoto.listo:
            return remoto
        motivo = remoto.motivo or "no se pudieron obtener los vectores"

    local = VectorLocalHash()
    local.fallback = f"openrouter descartado: {motivo}"
    if textos is not None:
        local.indexar(textos)
    return local


if __name__ == "__main__":
    import time

    textos = [t.texto for t in rag.TROZOS]
    store = obtener(textos=textos)
    print(f"backend: {store.nombre}" + (f"  ({store.fallback})" if store.fallback else ""))

    t0 = time.perf_counter()
    local = VectorLocalHash()
    local.indexar(textos)
    ingesta = time.perf_counter() - t0

    t0 = time.perf_counter()
    resultados = local.buscar("indices en postgres", k=5)
    consulta = time.perf_counter() - t0

    print(f"indexar {len(textos)} trozos: {ingesta * 1000:.0f} ms · "
          f"una consulta: {consulta * 1000:.1f} ms\n")
    for i, score in resultados:
        print(f"  {score:.3f}  [{rag.TROZOS[i].caja}] {rag.TROZOS[i].titulo}")
