"""Cache de respuestas en dos niveles, con caducidad por version.

EL PROBLEMA QUE RESUELVE, Y EL QUE CREA
    Reutilizar una respuesta ya calculada ahorra una llamada al modelo. Tambien es la
    forma mas facil de servir una respuesta FALSA: si el corpus cambio desde que se
    guardo, esa respuesta ya no sale de los documentos que hay ahora. No esta vieja,
    esta MAL. Por eso cada entrada guarda contra que se calculo y una entrada con otra
    version no se devuelve nunca, ni degradada ni con aviso: no se devuelve.

DOS NIVELES, Y SE CUENTAN POR SEPARADO
    exacto   la consulta normalizada (minusculas, sin acentos, sin espacios de mas y
             sin signos de interrogacion) es identica a una guardada. Barato y seguro:
             si las dos cadenas son la misma pregunta, la respuesta vale.
    similar  coseno sobre la señal vectorial local. Es el nivel PELIGROSO y nace
             APAGADO: ver la nota medida al final del modulo.

    Nunca se mezclan en un "hit rate" unico. Un acierto exacto es una certeza y uno
    por similitud es una apuesta; promediarlos esconde justo lo que hay que vigilar.

LA SEÑAL NO ES SEMANTICA
    `vectores.VectorLocalHash` son n-gramas de CARACTERES. Mide cuantos trocitos de
    letra comparten dos textos y nada mas. Medido en este proyecto: 'readiness probe'
    contra su sinonimo 'health check' puntua 0.490, casi lo mismo que dos textos sin
    relacion. Aqui no se usa la palabra 'semantico' ni una vez para describirla.

QUE SE GUARDA
    Un JSON plano. Si el archivo no existe, esta a medias o esta corrupto, la cache
    arranca VACIA y lo dice en `motivo_carga`: una cache que revienta al importar es
    peor que no tener cache.
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
import hashlib
import json
import os
import time
from pathlib import Path
from typing import NamedTuple

import agent
import config
import rag
import vectores

FORMATO = "cache-v1"                  # si cambia la forma del archivo, cambia esto
CAMPOS_VERSION = ("corpus_hash", "embedding_model", "embedding_version", "model_version")
UMBRAL = 0.92                         # minimo para que 'similar' cuente como acierto
MAXIMO = 500
LARGO_HASH = 16                       # sha256 truncado: 16 hex bastan para detectar cambios

# El nivel por similitud nace apagado. No es prudencia generica, es una medicion:
# dos preguntas DISTINTAS ("...al reservar" / "...al cobrar") puntuan 0.94, por encima
# del umbral de 0.92, mientras que dos formas de la MISMA pregunta pueden puntuar 0.87.
# No hay umbral que las separe porque la señal no mira el significado. Ver la nota final.
SIMILAR_POR_DEFECTO = False


class Entrada(NamedTuple):
    clave: str          # sha256 de la consulta normalizada
    consulta: str       # la consulta tal cual entro, para poder mirarla
    valor: object       # lo que se cachea; tiene que ser serializable a JSON para el disco
    version: dict       # contra que se calculo: los cuatro campos de CAMPOS_VERSION
    cuando: float       # time.time() al guardar; es lo que decide el desalojo
    similitud: float = 1.0   # con que parecido entro. Hoy siempre 1.0: solo se guarda
                             # desde la consulta literal, nunca desde una vecina.


def hash_corpus(trozos=None) -> str:
    """sha256 del contenido del corpus, truncado.

    Va sobre los TEXTOS, no sobre las fechas de los archivos ni sobre cuantos trozos
    hay: dos corpus con el mismo numero de trozos y un parrafo cambiado tienen que dar
    hashes distintos, que es exactamente el caso que hace que una respuesta cacheada
    deje de ser cierta.
    """
    h = hashlib.sha256()
    for t in (rag.TROZOS if trozos is None else trozos):
        h.update(t.texto.encode("utf-8"))
        h.update(b"\x00")                      # separador: evita que dos trozos se fundan
    return h.hexdigest()[:LARGO_HASH]


def version_actual() -> dict:
    """Contra que se esta calculando ahora mismo.

    `embedding_model` se llama asi por el contrato que pedia el proyecto, pero con el
    backend local NO es un modelo de embeddings: es la señal lexica de n-gramas. El
    valor lo dice ('local-hash-ngramas') para que nadie lea el campo y asuma otra cosa.
    """
    backend = (config.VECTOR_BACKEND or "local").strip().lower()
    return {
        "corpus_hash": hash_corpus(),
        "embedding_model": (vectores.MODELO_EMBEDDING if backend == "openrouter"
                            else "local-hash-ngramas"),
        "embedding_version": vectores.VERSION_EMBEDDING,
        "model_version": agent.MODEL,
    }


def _clave(consulta) -> str:
    """La misma pregunta escrita de otra manera tiene que dar la misma clave.

    `rag._normalizar` quita mayusculas y acentos, que es lo que hace falta para buscar
    en el corpus, pero deja los signos: '¿que es un indice?' y 'que es un indice' le
    salen distintas y serian dos entradas para la misma pregunta. Aqui se quitan
    ademas los signos de interrogacion y admiracion y la puntuacion final.

    Y NADA mas, a proposito: 'a == b' y 'a = b' siguen siendo consultas distintas,
    porque en una pregunta sobre codigo ese simbolo es justo lo que se pregunta.
    """
    norm = rag._normalizar(str(consulta))
    norm = "".join(" " if c in "¿?¡!" else c for c in norm)   # espacio, para no pegar palabras
    return hashlib.sha256(" ".join(norm.split()).strip(" .,;:").encode("utf-8")
                          ).hexdigest()[:LARGO_HASH]


def _diferencias(vieja, nueva) -> list:
    """Que campos de version no coinciden, con los dos valores, para poder decirlo."""
    fuera = []
    for campo in CAMPOS_VERSION:
        antes, ahora = (vieja or {}).get(campo), (nueva or {}).get(campo)
        if antes != ahora:
            fuera.append(f"{campo} ({antes!r} → {ahora!r})")
    return fuera


class Cache:
    """Dos niveles, una version y un archivo. Nada de esto puede tumbar a quien llama.

    `ruta=None` es cache SOLO EN MEMORIA a proposito: escribir en disco sin que nadie
    lo pida deja archivos por el proyecto. Quien quiera persistencia da una ruta.
    """

    def __init__(self, ruta=None, version=None, umbral=UMBRAL, maximo=MAXIMO, similar=None):
        self.ruta = Path(ruta) if ruta else None
        self.version = dict(version) if version else version_actual()
        self.umbral = float(umbral)
        self.maximo = int(maximo)
        self.similar = SIMILAR_POR_DEFECTO if similar is None else bool(similar)
        self.motivo_carga = ""
        self.motivo_escritura = ""
        self.motivo_invalidacion = ""
        self._entradas = {}            # clave -> Entrada, en orden de insercion
        self._store = None             # la señal vectorial, construida solo si hace falta
        self._claves_indexadas = None  # None = hay que reindexar
        self._cuenta = {"exactos": 0, "similares": 0, "misses": 0, "invalidados": 0,
                        "guardados": 0, "desalojados": 0}
        self._cargar()

    # ── buscar ───────────────────────────────────────────────────────────────

    def buscar(self, consulta):
        """(valor|None, informe). El informe SIEMPRE explica que paso y por que.

        informe = {"resultado": "exacto"|"similar"|"miss"|"invalidado",
                   "similitud": float, "motivo": str, "clave": str}
        """
        clave = _clave(consulta)
        entrada = self._entradas.get(clave)

        if entrada is not None:
            fuera = _diferencias(entrada.version, self.version)
            if fuera:
                # se tira en el acto: una entrada calculada contra otra version no va a
                # volver a servir nunca, y guardarla solo hace que vuelva a salir aqui.
                self._entradas.pop(clave, None)
                self._claves_indexadas = None
                self._cuenta["invalidados"] += 1
                self._volcar()
                return None, {"resultado": "invalidado", "similitud": 1.0, "clave": clave,
                              "motivo": f"habia una respuesta guardada pero cambio "
                                        f"{'; '.join(fuera)}: se calculo contra otra cosa "
                                        f"y seria incorrecta"}
            self._cuenta["exactos"] += 1
            return entrada.valor, {"resultado": "exacto", "similitud": 1.0, "clave": clave,
                                   "motivo": "la consulta normalizada es identica a una "
                                             "guardada"}

        if not self.similar:
            self._cuenta["misses"] += 1
            return None, {"resultado": "miss", "similitud": 0.0, "clave": clave,
                          "motivo": "no hay ninguna consulta identica y el nivel por "
                                    "similitud esta apagado (mide caracteres, no "
                                    "significado: ver cache.SIMILAR_POR_DEFECTO)"}

        vecina, similitud = self._mas_parecida(consulta)
        if vecina is None or similitud < self.umbral:
            self._cuenta["misses"] += 1
            return None, {"resultado": "miss", "similitud": round(similitud, 4), "clave": clave,
                          "motivo": f"la consulta guardada mas parecida puntua "
                                    f"{similitud:.3f} < umbral {self.umbral:.2f}"}

        fuera = _diferencias(vecina.version, self.version)
        if fuera:
            self._entradas.pop(vecina.clave, None)
            self._claves_indexadas = None
            self._cuenta["invalidados"] += 1
            self._volcar()
            return None, {"resultado": "invalidado", "similitud": round(similitud, 4),
                          "clave": clave,
                          "motivo": f"la entrada parecida ({similitud:.3f}) cambio de "
                                    f"version: {'; '.join(fuera)}"}

        self._cuenta["similares"] += 1
        return vecina.valor, {"resultado": "similar", "similitud": round(similitud, 4),
                              "clave": clave,
                              "motivo": f"no habia consulta identica; se sirve la de "
                                        f"{vecina.consulta!r} con parecido LEXICO "
                                        f"{similitud:.3f} ≥ {self.umbral:.2f}. Parecido de "
                                        f"caracteres no es la misma pregunta"}

    # ── guardar, desalojar, invalidar ────────────────────────────────────────

    def guardar(self, consulta, valor) -> None:
        clave = _clave(consulta)
        self._entradas.pop(clave, None)                # reescribir la pone al final
        self._entradas[clave] = Entrada(clave, " ".join(str(consulta).split()), valor,
                                        dict(self.version), time.time(), 1.0)
        self._claves_indexadas = None
        self._cuenta["guardados"] += 1
        self._desalojar()
        self._volcar()

    def _desalojar(self):
        """Por encima de `maximo` se tira la mas VIEJA por fecha de guardado.

        Es FIFO, no LRU: no se cuentan los accesos. Con un limite de cientos de
        entradas la diferencia no compensa llevar contadores que habria que persistir
        y que se desincronizan entre dos procesos.
        """
        while len(self._entradas) > self.maximo:
            vieja = min(self._entradas.values(), key=lambda e: e.cuando)
            self._entradas.pop(vieja.clave, None)
            self._claves_indexadas = None
            self._cuenta["desalojados"] += 1

    def invalidar(self, motivo="") -> int:
        """Tira TODAS las entradas y devuelve cuantas eran.

        Es el boton manual ("acabo de reescribir media caja 04"). Para la caducidad por
        version no hace falta llamarla: buscar() ya no devuelve nada cuya version no
        cuadre, asi que la cache no puede servir algo viejo por olvidar este botón.
        """
        cuantas = len(self._entradas)
        self._entradas.clear()
        self._claves_indexadas = None
        self._store = None
        self.motivo_invalidacion = motivo or "invalidacion manual"
        self._volcar()
        return cuantas

    # ── el nivel por similitud ───────────────────────────────────────────────

    def _mas_parecida(self, consulta):
        """(Entrada|None, similitud). Reindexa solo si la cache cambio."""
        if not self._entradas:
            return None, 0.0
        if self._claves_indexadas is None:
            self._claves_indexadas = list(self._entradas)
            textos = [self._entradas[c].consulta for c in self._claves_indexadas]
            # obtener() respeta el backend configurado y cae al local si el remoto no
            # esta disponible; con agent.OFFLINE puesto no toca la red.
            self._store = vectores.obtener(textos=textos)
        resultados = self._store.buscar(str(consulta), k=1)
        if not resultados:
            return None, 0.0                    # coseno ≤ 0: no comparten nada
        i, puntuacion = resultados[0]
        if i >= len(self._claves_indexadas):
            return None, 0.0
        return self._entradas.get(self._claves_indexadas[i]), float(puntuacion)

    # ── disco ────────────────────────────────────────────────────────────────

    def _cargar(self):
        if self.ruta is None:
            self.motivo_carga = "sin ruta: la cache vive solo en memoria"
            return
        if not self.ruta.exists():
            self.motivo_carga = f"{self.ruta.name} no existe: se empieza vacia"
            return
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
            entradas = datos["entradas"]
            if not isinstance(entradas, list):
                raise ValueError("'entradas' no es una lista")
        except Exception as e:
            # cualquier cosa: JSON roto, bytes que no son texto, un dict sin 'entradas',
            # permisos. Una cache ilegible es una cache vacia, no una excepcion.
            self.motivo_carga = (f"{self.ruta.name} ilegible ({type(e).__name__}): "
                                 f"se empieza vacia")
            return
        recuperadas, rotas = {}, 0
        for cruda in entradas:
            try:
                e = Entrada(str(cruda["clave"]), str(cruda["consulta"]), cruda["valor"],
                            dict(cruda["version"]), float(cruda["cuando"]),
                            float(cruda.get("similitud", 1.0)))
            except Exception:
                rotas += 1                      # una entrada mala no tira las demas
                continue
            recuperadas[e.clave] = e
        self._entradas = recuperadas
        self.motivo_carga = (f"{len(recuperadas)} entradas leidas de {self.ruta.name}"
                             + (f"; {rotas} descartadas por ilegibles" if rotas else ""))
        # OJO: las entradas con otra version se cargan a proposito. No se devuelven
        # nunca, pero conservarlas permite que buscar() diga QUE campo cambio en vez
        # de un 'miss' mudo que parece que la cache nunca guardo nada.

    def _volcar(self):
        """Escribe el archivo entero, atomico, sin propagar fallos.

        tmp + os.replace para que un proceso que muera a medias no deje un JSON
        truncado: o esta el archivo de antes o esta el nuevo, nunca medio.
        """
        if self.ruta is None:
            return
        serializables, descartadas = [], 0
        for e in self._entradas.values():
            fila = {"clave": e.clave, "consulta": e.consulta, "valor": e.valor,
                    "version": e.version, "cuando": e.cuando, "similitud": e.similitud}
            try:
                json.dumps(fila)
            except (TypeError, ValueError):
                descartadas += 1                # valor no serializable: vive en memoria
                continue
            serializables.append(fila)
        payload = {"formato": FORMATO, "version": self.version, "entradas": serializables}
        tmp = self.ruta.with_name(f"{self.ruta.name}.{os.getpid()}.tmp")
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.ruta)
            self.motivo_escritura = (f"{len(serializables)} entradas escritas"
                                     + (f"; {descartadas} no serializables a JSON"
                                        if descartadas else ""))
        except OSError as e:
            self.motivo_escritura = f"no se pudo escribir ({type(e).__name__}: {e})"
            try:
                tmp.unlink()
            except OSError:
                pass

    # ── cuentas ──────────────────────────────────────────────────────────────

    def estadisticas(self) -> dict:
        """Los dos niveles por separado, y ninguna cifra que los mezcle.

        No hay 'tasa_de_acierto' global a proposito: sumar un acierto exacto (seguro)
        con uno por similitud (una apuesta sobre parecido de caracteres) da un numero
        que sube justo cuando el riesgo sube.
        """
        c = self._cuenta
        consultas = c["exactos"] + c["similares"] + c["misses"] + c["invalidados"]
        tasa = lambda n: round(n / consultas, 4) if consultas else 0.0
        return {
            "entradas": len(self._entradas),
            "consultas": consultas,
            "exactos": c["exactos"],
            "similares": c["similares"],
            "misses": c["misses"],
            "invalidados": c["invalidados"],
            "tasa_exacta": tasa(c["exactos"]),
            "tasa_similar": tasa(c["similares"]),
            "guardados": c["guardados"],
            "desalojados": c["desalojados"],
            "umbral": self.umbral,
            "maximo": self.maximo,
            "similar_activado": self.similar,
            "version": dict(self.version),
            "ruta": str(self.ruta) if self.ruta else None,
            "motivo_carga": self.motivo_carga,
        }


# LIMITES CONOCIDOS, para no vender esto como mas de lo que es:
#
#  · EL NIVEL 'SIMILAR' NO SEPARA PREGUNTAS DISTINTAS. Medido con la señal local
#    (n-gramas de caracteres, dim=512):
#        "...race condition al reservar el inventario" vs "...al cobrar el inventario"
#        (preguntas DISTINTAS, respuesta distinta)                    → 0.949
#        "...race condition cuando dos usuarios reservan/cobran..."   → 0.941
#        "idempotencia en pagos" vs "idempotencia en los pagos"
#        (la MISMA pregunta)                                          → 0.873
#        "readiness probe" vs "health check" (la misma, en sinonimos) → 0.493
#    Las distintas puntuan MAS que varias iguales: no hay umbral que las parta, porque
#    lo que se mide son letras compartidas y dos preguntas que solo cambian el verbo
#    comparten casi todas. Por eso SIMILAR_POR_DEFECTO = False. Encenderlo sirve para
#    erratas y plurales sobre consultas muy cortas y controladas, y para nada mas.
#  · El desalojo es FIFO por fecha de guardado, no LRU: una entrada muy usada puede
#    caer antes que una que nadie pidio nunca.
#  · Dos procesos sobre el mismo archivo no se pisan a medias (escritura atomica) pero
#    el ultimo que escribe gana: lo que guardo el otro entre medias se pierde. No hay
#    bloqueo ni fusion. Para un solo proceso sobra; para varios, esto no es la pieza.
#  · `version_actual()` describe el backend CONFIGURADO. Si openrouter estuviera
#    configurado y `vectores.obtener()` cayera al local por un fallo de red, la version
#    no lo reflejaria.
#  · El valor tiene que ser serializable a JSON para persistir. Si no lo es, la entrada
#    se queda en memoria y `motivo_escritura` lo dice: no se guarda a medias.


if __name__ == "__main__":
    import tempfile

    carpeta = Path(tempfile.mkdtemp(prefix="cache-demo-"))
    c = Cache(ruta=carpeta / "cache.json")
    print(f"version actual: {json.dumps(c.version, ensure_ascii=False)}")
    print(f"carga: {c.motivo_carga}\n")

    c.guardar("¿Qué es un índice en Postgres?", "un indice es ...")
    for q in ("que es un indice   en POSTGRES", "¿qué es un índice en postgresql?"):
        valor, info = c.buscar(q)
        print(f"  {info['resultado']:<11} {info['similitud']:.3f}  {q!r}\n        {info['motivo']}")

    viejo = Cache(ruta=carpeta / "cache.json", version={**c.version, "corpus_hash": "otro"})
    _, info = viejo.buscar("¿Qué es un índice en Postgres?")
    print(f"\n  {info['resultado']}: {info['motivo']}")
    print(f"\nestadisticas: {json.dumps(c.estadisticas()['exactos'], ensure_ascii=False)} exactos, "
          f"{c.estadisticas()['similares']} similares, {c.estadisticas()['misses']} misses")
