"""Los vectores: determinismo, ranking, cache de ingesta y el candado de red.

Todo sin red y sin claves. El backend remoto se prueba sustituyendo
`vectores._URLOPEN`, asi que ni un socket sale de aqui: si alguno de estos casos
llegase a llamar de verdad, seria un bug del candado, que es justo lo que miden
los dos ultimos.

    python3 test_vectores.py
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
# La raiz (produccion) y las dos carpetas cuyos modulos se importan por nombre desnudo:
# `test_cache` importa `cache` (experimental/) y `test_plan` importa `eval` (benchmarks/).
for _d in (_RAIZ_REPO, _RAIZ_REPO / "experimental", _RAIZ_REPO / "benchmarks"):
    _sys.path.insert(0, str(_d))
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import zlib
from pathlib import Path

import agent
import rag
import vectores
from vectores import VectorLocalHash, VectorOpenRouter, obtener

AQUI = Path(__file__).parent
# La raiz de PRODUCCION, derivada de un modulo suyo: inmune a donde viva el test.
_RAIZ_PROD = Path(rag.__file__).resolve().parent
casos = []
notas = []          # lo que hay que reportar aunque el caso pase


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:                      # un error inesperado tambien es un fallo
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


# ── corpus de juguete, para que el ranking sea comprobable a mano ────────────

CORPUS = [
    "Postgres guarda los indices en un B-tree y el planificador usa estadisticas.",   # 0
    "La paleta de colores calida y la tipografia del rediseño de la marca.",          # 1
    "Recetas de cocina italiana: masa madre, tomate San Marzano y albahaca.",         # 2
]


def _local(textos=CORPUS, **kw):
    v = VectorLocalHash(**kw)
    v.indexar(textos)
    return v


# ── el backend local ─────────────────────────────────────────────────────────

def mismo_texto_mismo_vector():
    a, b = VectorLocalHash(), VectorLocalHash()
    assert a.vector(CORPUS[0]) == b.vector(CORPUS[0]), "dos instancias dan vectores distintos"


def el_hash_de_python_si_cambia_entre_procesos():
    """Premisa del caso siguiente: si `hash()` no variase, no probaria nada."""
    vistos = {_subproceso("print(hash('postgres'))", semilla) for semilla in ("1", "424242")}
    assert len(vistos) > 1, (
        "PYTHONHASHSEED no esta cambiando nada en esta maquina: el caso de "
        "determinismo entre procesos no demuestra lo que dice demostrar")


def determinismo_entre_procesos():
    """El motivo de usar crc32 y no hash(): el vector no puede depender de la semilla."""
    aqui = json.dumps(VectorLocalHash().vector(CORPUS[0]))
    codigo = f"import json, vectores; print(json.dumps(vectores.VectorLocalHash().vector({CORPUS[0]!r})))"
    for semilla in ("0", "1", "424242"):
        fuera = _subproceso(codigo, semilla)
        assert fuera == aqui, f"con PYTHONHASHSEED={semilla} el vector cambia"


def _subproceso(codigo, semilla):
    r = subprocess.run([sys.executable, "-c", codigo], cwd=_RAIZ_PROD, capture_output=True,
                       text=True, env={**os.environ, "PYTHONHASHSEED": semilla})
    assert r.returncode == 0, f"el subproceso fallo: {r.stderr[-300:]}"
    return r.stdout.strip()


def coseno_consigo_mismo_es_uno():
    v = _local()
    [(idx, score)] = v.buscar(CORPUS[0], k=1)
    assert idx == 0, f"un texto no se recupera a si mismo: salio {idx}"
    assert abs(score - 1.0) < 1e-9, f"coseno consigo mismo = {score}, deberia ser 1.0"


def ranking_sensato():
    """El documento que contiene la consulta tiene que ir por delante del que no."""
    v = _local()
    resultados = v.buscar("indices en postgres", k=3)
    assert resultados, "no devolvio nada"
    assert resultados[0][0] == 0, f"gano el documento {resultados[0][0]}, no el de postgres"


def scores_en_rango_y_ordenados():
    v = _local([t.texto for t in rag.TROZOS])
    resultados = v.buscar("transacciones y locks", k=10)
    assert resultados, "el corpus real no devolvio nada"
    scores = [s for _, s in resultados]
    assert all(0.0 <= s <= 1.0 for s in scores), f"score fuera de [0,1]: {scores}"
    assert scores == sorted(scores, reverse=True), f"no viene ordenado: {scores}"


def corpus_vacio():
    v = VectorLocalHash()
    v.indexar([])
    assert v.buscar("lo que sea", k=5) == [], "un corpus vacio tiene que devolver []"


def consulta_vacia():
    v = _local()
    for consulta in ("", "   ", "\n\t"):
        assert v.buscar(consulta, k=5) == [], f"la consulta {consulta!r} devolvio algo"


def consulta_que_no_aparece():
    """NO devuelve [], y merece decirse en voz alta en vez de ajustar el assert.

    El hashing trick mete todos los n-gramas en 512 dimensiones, asi que una
    consulta corta y un trozo largo SIEMPRE colisionan en alguna y el score nunca
    baja a cero del todo. El caso comprueba lo unico que de verdad importa: que
    ese suelo quede muy por debajo de una coincidencia real, para que el ORDEN
    siga siendo correcto aunque el numero no sea interpretable.
    """
    v = _local()
    ruido = dict(v.buscar("zzqqxw wvkkjj yyjxq", k=3)).get(0, 0.0)
    real = dict(v.buscar("indices en postgres", k=3)).get(0, 0.0)
    notas.append(f"suelo de ruido por colision (dim=512): {ruido:.3f} frente a {real:.3f} "
                 f"de una coincidencia real ({real / max(ruido, 1e-9):.1f}x de margen)")
    assert ruido < real / 3, (
        f"una consulta sin nada en comun puntua {ruido:.3f} y una real {real:.3f}: "
        f"sin margen, el ranking deja de distinguir")


def mas_dimensiones_hunden_el_ruido():
    """La comprobacion de que el suelo es colision y no un bug del coseno."""
    suelos = {}
    for dim in (512, 1024, 8192):
        v = _local(dim=dim)
        suelos[dim] = dict(v.buscar("zzqqxw wvkkjj yyjxq", k=3)).get(0, 0.0)
    notas.append("suelo por dimension: " + " · ".join(f"{d}→{s:.4f}" for d, s in suelos.items()))
    assert suelos[8192] < suelos[512], f"mas dimensiones no bajan el ruido: {suelos}"


def tolerancia_a_erratas():
    """La razon de ser del backend: 'postgress' no es una palabra del corpus."""
    v = _local()
    resultados = v.buscar("postgress", k=3)
    assert resultados, "la errata no recupero nada"
    assert resultados[0][0] == 0, (
        f"'postgress' no recupero el documento de postgres: gano el {resultados[0][0]}")
    notas.append(f"errata 'postgress' → doc de postgres con score {resultados[0][1]:.3f}")


def tolerancia_a_erratas_en_el_corpus_real():
    """Lo mismo pero con los 247 trozos de verdad, que es donde suele romperse."""
    trozos = [t.texto for t in rag.TROZOS]
    v = _local(trozos)
    bien = [i for i, _ in v.buscar("postgres", k=5)]
    errata = [i for i, _ in v.buscar("postgress", k=5)]
    comunes = len(set(bien) & set(errata))
    notas.append(f"corpus real: 'postgres' vs 'postgress' comparten {comunes}/5 del top-5 "
                 f"({', '.join(rag.TROZOS[i].titulo for i, _ in v.buscar('postgress', k=3))})")
    assert comunes >= 3, (
        f"la errata solo conserva {comunes}/5 del top-5 en el corpus real: la tolerancia "
        f"a erratas NO esta funcionando sobre documentos largos")


def mezcla_espanol_ingles():
    """Formas parecidas en los dos idiomas, que es lo que hay en el corpus."""
    v = _local(["El cache invalida las entradas por TTL.",
                "La paleta de colores calida del rediseño."])
    resultados = v.buscar("caching", k=2)
    assert resultados and resultados[0][0] == 0, f"'caching' no encontro 'cache': {resultados}"


def no_entiende_semantica():
    """El limite se documenta, asi que se comprueba como caso.

    No vale mirar quien gana el ranking: con dos documentos, el sinonimo 'gana'
    por puro ruido de colision. Lo que demuestra que no hay semantica es el SCORE:
    el sinonimo se queda al nivel del suelo mientras la frase literal dispara.
    """
    v = _local(["El readiness probe del pod decide si entra en el balanceador.",
                "Recetas de cocina italiana con tomate y albahaca."])
    literal = dict(v.buscar("readiness probe", k=2)).get(0, 0.0)
    sinonimo = dict(v.buscar("health check", k=2)).get(0, 0.0)
    notas.append(f"sin semantica: 'readiness probe' puntua {literal:.3f} y su sinonimo "
                 f"'health check' {sinonimo:.3f} — ruido, no comprension")
    assert sinonimo < literal / 5, (
        f"'health check' puntua {sinonimo:.3f} contra el doc de 'readiness probe': "
        f"si eso fuese una señal real, el modulo estaria mintiendo al decir que no hay semantica")


# ── dobles de red: nada de esto abre un socket ───────────────────────────────

class _Respuesta:
    """Lo minimo que usa el codigo de urlopen: un .read() con bytes."""

    def __init__(self, cuerpo):
        self._cuerpo = cuerpo

    def read(self):
        return self._cuerpo


def _embedding(texto, dim=8):
    """Vector falso pero DETERMINISTA: el mismo texto da el mismo vector."""
    h = zlib.crc32(texto.encode())
    return [float((h >> (b * 3)) % 17 - 8) for b in range(dim)]


def _guion_valido(textos):
    return _Respuesta(json.dumps({
        "data": [{"index": i, "embedding": _embedding(t)} for i, t in enumerate(textos)]
    }).encode())


def _guion_http_429(textos):
    raise urllib.error.HTTPError(vectores.URL_EMBEDDINGS, 429, "Too Many Requests", {}, None)


def _guion_timeout(textos):
    raise TimeoutError("the read operation timed out")


def _guion_json_roto(textos):
    return _Respuesta(b'{"data": [{"index": 0, "embed')


def _guion_faltan_vectores(textos):
    """Devuelve uno menos: el fallo silencioso que desalinearia indices con textos."""
    return _Respuesta(json.dumps({
        "data": [{"index": i, "embedding": _embedding(t)} for i, t in enumerate(textos[:-1])]
    }).encode())


@contextlib.contextmanager
def _mockeado(guion, abierto=True):
    """Sustituye urlopen, la carpeta de cache, el candado y la clave. Y lo devuelve todo.

    La carpeta se sustituye tambien a proposito: ningun caso puede escribir en el
    embeddings/ del proyecto.
    """
    with tempfile.TemporaryDirectory() as tmp:
        antes = (vectores._URLOPEN, vectores.CARPETA_CACHE, agent.OFFLINE,
                 os.environ.get("OPENROUTER_API_KEY"))
        llamadas = []

        def falso_urlopen(req, timeout=None):
            llamadas.append(json.loads(req.data)["input"])
            return guion(llamadas[-1])

        falso_urlopen.llamadas = llamadas
        falso_urlopen.carpeta = Path(tmp)
        vectores._URLOPEN = falso_urlopen
        vectores.CARPETA_CACHE = Path(tmp)
        agent.OFFLINE = not abierto
        os.environ["OPENROUTER_API_KEY"] = "sk-de-mentira-nunca-sale-de-este-proceso"
        try:
            yield falso_urlopen
        finally:
            vectores._URLOPEN, vectores.CARPETA_CACHE, agent.OFFLINE = antes[:3]
            if antes[3] is None:
                os.environ.pop("OPENROUTER_API_KEY", None)
            else:
                os.environ["OPENROUTER_API_KEY"] = antes[3]


# ── la cache de ingesta ──────────────────────────────────────────────────────

def cache_miss_escribe():
    with _mockeado(_guion_valido) as red:
        v = VectorOpenRouter()
        v.indexar(CORPUS)
        assert v.listo, f"no indexo: {v.motivo}"
        assert len(red.llamadas) == 1, f"un corpus de 3 deberia ser 1 lote, fueron {len(red.llamadas)}"
        ruta = v.ruta_cache(v.corpus_hash(CORPUS))
        assert ruta.exists(), f"no escribio la cache en {ruta}"
        datos = json.loads(ruta.read_text())
        assert len(datos["vectores"]) == 3, datos.keys()
        assert datos["modelo"] == v.modelo and datos["version"] == vectores.VERSION_EMBEDDING


def cache_hit_sin_llamadas():
    with _mockeado(_guion_valido) as red:
        VectorOpenRouter().indexar(CORPUS)
        antes = len(red.llamadas)
        otro = VectorOpenRouter()
        otro.indexar(CORPUS)
        assert otro.listo, f"con cache en disco deberia quedar listo: {otro.motivo}"
        assert otro.llamadas == 0, f"la cache no evito las llamadas: {otro.llamadas}"
        assert len(red.llamadas) == antes, "toco la red teniendo cache"


def cache_invalida_al_cambiar_el_corpus():
    with _mockeado(_guion_valido) as red:
        VectorOpenRouter().indexar(CORPUS)
        otro = VectorOpenRouter()
        otro.indexar(CORPUS[:2] + ["Un trozo nuevo que antes no estaba en el corpus."])
        assert otro.llamadas == 1, "un corpus distinto tiene que re-ingerir"
        assert len(red.llamadas) == 2


def cache_invalida_al_cambiar_de_modelo():
    with _mockeado(_guion_valido) as red:
        VectorOpenRouter().indexar(CORPUS)
        otro = VectorOpenRouter(modelo="openai/text-embedding-3-large")
        otro.indexar(CORPUS)
        assert otro.llamadas == 1, "otro modelo no puede reutilizar los vectores del anterior"
        assert len(red.llamadas) == 2


def cache_invalida_al_cambiar_la_version():
    with _mockeado(_guion_valido) as red:
        v = VectorOpenRouter()
        v.indexar(CORPUS)
        ruta = v.ruta_cache(v.corpus_hash(CORPUS))
        datos = json.loads(ruta.read_text())
        datos["version"] = "version-de-antes"
        ruta.write_text(json.dumps(datos))
        otro = VectorOpenRouter()
        otro.indexar(CORPUS)
        assert otro.llamadas == 1, "cambiar VERSION_EMBEDDING tiene que invalidar la cache"


# ── el backend remoto: una respuesta buena y cuatro fallos ───────────────────

def openrouter_respuesta_valida():
    with _mockeado(_guion_valido) as red:
        store = obtener("openrouter", textos=CORPUS)
        assert store.nombre == "openrouter", f"cayo al local sin motivo: {store.fallback}"
        assert store.fallback is None, store.fallback
        assert len(red.llamadas) == 1, red.llamadas
        resultados = store.buscar(CORPUS[0], k=3)
        assert resultados and resultados[0][0] == 0, f"no se recupero a si mismo: {resultados}"
        assert all(0.0 <= s <= 1.0 for _, s in resultados), resultados


def _cae_al_local(guion, trozo_del_motivo):
    with _mockeado(guion) as red:
        store = obtener("openrouter", textos=CORPUS)
        assert store.nombre == "local", "no degrado al backend local"
        assert store.fallback, "degrado pero sin explicar por que: la traza se queda muda"
        assert trozo_del_motivo in store.fallback, f"el motivo no lo explica: {store.fallback!r}"
        assert store.listo, "el local tiene que venir ya indexado y utilizable"
        assert store.buscar("postgres", k=1), "el plan B no busca"
        assert len(red.llamadas) >= 1, "ni siquiera llego a intentarlo"


def openrouter_httperror_cae_al_local():
    _cae_al_local(_guion_http_429, "HTTPError")


def openrouter_timeout_cae_al_local():
    _cae_al_local(_guion_timeout, "TimeoutError")


def openrouter_json_invalido_cae_al_local():
    _cae_al_local(_guion_json_roto, "JSONDecodeError")


def openrouter_vectores_de_menos_cae_al_local():
    _cae_al_local(_guion_faltan_vectores, "2 vectores para 3 textos")


# ── el candado ───────────────────────────────────────────────────────────────

def el_candado_esta_puesto_por_defecto():
    assert agent.OFFLINE, "sin MIRAG_OFFLINE=0 el candado tiene que estar puesto"


def con_el_candado_no_se_llama_ni_una_vez():
    with _mockeado(_guion_valido, abierto=False) as red:
        v = VectorOpenRouter()
        assert not v.disponible, "se declara disponible con el candado puesto"
        v.indexar(CORPUS)
        v.buscar("postgres", k=3)
        store = obtener("openrouter", textos=CORPUS)
        assert red.llamadas == [], f"abrio {len(red.llamadas)} llamadas con el candado puesto"
        assert v.llamadas == 0, v.llamadas
        assert store.nombre == "local", store.nombre
        assert "MIRAG_OFFLINE" in (store.fallback or ""), store.fallback


def sin_clave_tampoco_se_llama():
    with _mockeado(_guion_valido) as red:
        os.environ.pop("OPENROUTER_API_KEY", None)
        store = obtener("openrouter", textos=CORPUS)
        assert red.llamadas == [], "llamo sin clave"
        assert store.nombre == "local" and "OPENROUTER_API_KEY" in (store.fallback or ""), \
            store.fallback


def obtener_por_defecto_es_local():
    store = obtener()
    assert store.nombre == "local", f"el defecto tiene que ser local, salio {store.nombre}"
    assert store.fallback is None, "pedir el defecto no es una degradacion"


def obtener_backend_desconocido_no_revienta():
    assert obtener("colbert-de-mentira").nombre == "local"


def el_unico_sitio_que_abre_socket_lleva_candado():
    """Defensa en profundidad: una ruta nueva que llame a _pedir sin pasar por indexar
    o buscar generaria factura en silencio. Se prueba haciendo estallar el urlopen."""
    import os
    anterior_url, anterior_off = vectores._URLOPEN, agent.OFFLINE
    def prohibido(*a, **k):
        raise AssertionError("se abrio un socket con el candado puesto")
    vectores._URLOPEN = prohibido
    agent.OFFLINE = True
    os.environ["OPENROUTER_API_KEY"] = "falsa-para-la-prueba"
    try:
        v = vectores.VectorOpenRouter()
        for fn, nombre in ((lambda: v._pedir(["x"]), "_pedir"),
                           (lambda: v.indexar(["x", "y"]), "indexar"),
                           (lambda: v.buscar("x", 3), "buscar")):
            try:
                fn()
            except AssertionError:
                raise AssertionError(f"{nombre} llego a la red con MIRAG_OFFLINE puesto")
            except Exception:
                pass          # parar con un error propio es exactamente lo correcto
    finally:
        vectores._URLOPEN, agent.OFFLINE = anterior_url, anterior_off
        os.environ.pop("OPENROUTER_API_KEY", None)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "_")) and fn.__module__ == "__main__":
            probar(nombre.replace("_", " "), fn)

    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))

    # la medicion va en el output, no en un assert: un numero que cambia de maquina
    # a maquina no es un caso de test, es un dato que hay que mirar
    trozos = [t.texto for t in rag.TROZOS]
    t0 = time.perf_counter()
    medido = VectorLocalHash()
    medido.indexar(trozos)
    ingesta = time.perf_counter() - t0
    t0 = time.perf_counter()
    medido.buscar("indices en postgres", k=5)
    consulta = time.perf_counter() - t0

    print(f"\n  · indexar {len(trozos)} trozos ({sum(map(len, trozos)) // len(trozos)} car. "
          f"de media): {ingesta * 1000:.0f} ms")
    print(f"  · una consulta sobre los {len(trozos)}: {consulta * 1000:.2f} ms")
    for n in notas:
        print(f"  · {n}")

    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
