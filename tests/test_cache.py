"""La cache de dos niveles: que acierte, y sobre todo que CADUQUE.

Lo que mas importa aqui no es el ahorro, es que una respuesta calculada contra otro
corpus u otro modelo no salga nunca. Y hay una prueba que existe para dejar por escrito
un resultado NEGATIVO medido: el nivel por similitud no separa dos preguntas distintas
que se parecen de letra. Si algun dia esa prueba se pone en rojo es que la señal mejoro
y habra que rehacer la recomendacion, no que el test este mal.

    python3 test_cache.py
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
import json
import shutil
import sys
import tempfile
from pathlib import Path

import cache as C
import rag

casos = []
MEDIDO = {}                     # numeros que se enseñan al final, no se inventan

CARPETA = Path(tempfile.mkdtemp(prefix="test-cache-"))
_contador = [0]

# Version fija para los tests: asi no dependen del corpus real ni de que alguien
# toque agent.MODEL, y el unico cambio de version es el que provoca cada prueba.
BASE = {"corpus_hash": "aaaa1111", "embedding_model": "local-hash-ngramas",
        "embedding_version": "v1", "model_version": "anthropic/claude-haiku-4.5"}

# El par confundible: dos preguntas DISTINTAS que solo cambian un verbo.
RESERVAR = ("en el checkout, ¿cómo evito una race condition al reservar el inventario "
            "con varios workers concurrentes?")
COBRAR = ("en el checkout, ¿cómo evito una race condition al cobrar el inventario "
          "con varios workers concurrentes?")


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _v(**cambios):
    return {**BASE, **cambios}


def _ruta(nombre):
    _contador[0] += 1
    return CARPETA / f"{_contador[0]:02d}-{nombre}.json"


def _similitud(a, b):
    """Lo que puntua la señal local entre dos consultas. Sin umbral de por medio."""
    c = C.Cache(version=_v(), similar=True, umbral=0.0)
    c.guardar(a, "valor")
    return c.buscar(b)[1]["similitud"]


# ── nivel 1: exacto ──────────────────────────────────────────────────────────

def miss_en_cache_vacia():
    valor, info = C.Cache(version=_v()).buscar("que es un indice")
    assert valor is None, valor
    assert info["resultado"] == "miss", info
    assert info["motivo"] and len(info["motivo"]) > 10, info
    assert info["clave"] and info["similitud"] == 0.0, info


def guardar_y_acierto_exacto():
    c = C.Cache(version=_v())
    c.guardar("que es un indice", "un indice es una estructura...")
    valor, info = c.buscar("que es un indice")
    assert valor == "un indice es una estructura...", (valor, info)
    assert info["resultado"] == "exacto" and info["similitud"] == 1.0, info


def la_normalizacion_lleva_a_la_misma_entrada():
    """Acentos, mayusculas, espacios de mas y signos son la misma pregunta, no otra."""
    c = C.Cache(version=_v())
    c.guardar("¿Cómo evito una race condition?", "con un lock...")
    for variante in ("como evito una race condition",
                     "  ¿CÓMO   evito    una RACE condition?  ",
                     "cómo evito una race condition."):
        valor, info = c.buscar(variante)
        assert info["resultado"] == "exacto", (variante, info)
        assert valor == "con un lock...", (variante, valor)
    assert c.estadisticas()["entradas"] == 1, "una pregunta, una entrada"
    # pero solo eso: lo que cambia el sentido sigue siendo otra consulta
    c.guardar("cuando uso a == b", "asi")
    assert c.buscar("cuando uso a = b")[1]["resultado"] == "miss"
    assert C.Cache(version=_v()).buscar("otra cosa")[1]["resultado"] == "miss"


# ── nivel 2: similar (apagado por defecto, y por eso hay que encenderlo aqui) ─

def acierto_por_similitud_sobre_umbral():
    c = C.Cache(version=_v(), umbral=0.90, similar=True)
    c.guardar("que es un indice en postgres", "un indice es ...")
    valor, info = c.buscar("que es un indice en postgresql")
    MEDIDO["variante_lexica"] = info["similitud"]
    assert info["resultado"] == "similar", info
    assert valor == "un indice es ...", valor
    assert info["similitud"] >= 0.90, info
    assert "LEXICO" in info["motivo"], info["motivo"]


def miss_por_similitud_bajo_umbral():
    """Dos formas de decir lo MISMO con otras palabras: la señal no las une."""
    c = C.Cache(version=_v(), umbral=0.92, similar=True)
    c.guardar("readiness probe en kubernetes", "la probe dice si el pod recibe trafico")
    valor, info = c.buscar("health check en kubernetes")
    MEDIDO["sinonimos"] = info["similitud"]
    assert valor is None and info["resultado"] == "miss", info
    assert info["similitud"] < 0.92, info
    assert str(info["similitud"])[:4] in info["motivo"], info["motivo"]


def el_par_confundible_no_lo_separa_el_umbral():
    """RESULTADO NEGATIVO, medido: reservar != cobrar, pero la señal dice que si.

    Con el umbral por defecto (0.92) el nivel 'similar' sirve la respuesta sobre
    RESERVAR a una pregunta sobre COBRAR. No es un umbral mal elegido: mas abajo se
    comprueba que una pregunta REPETIDA con otras palabras puntua MENOS que estas dos
    preguntas distintas, asi que no existe ningun corte que las separe.
    """
    c = C.Cache(version=_v(), umbral=C.UMBRAL, similar=True)
    c.guardar(RESERVAR, "RESPUESTA SOBRE RESERVAR")
    valor, info = c.buscar(COBRAR)
    MEDIDO["par_confundible"] = info["similitud"]
    assert info["resultado"] == "similar" and valor == "RESPUESTA SOBRE RESERVAR", (
        "si esto deja de pasar es que la señal ya separa las dos preguntas: rehacer la "
        f"recomendacion antes de tocar el test → {info}")
    assert info["similitud"] > C.UMBRAL, info

    misma = _similitud("idempotencia en pagos", "idempotencia en los pagos")
    MEDIDO["misma_pregunta_otras_palabras"] = misma
    assert MEDIDO["par_confundible"] > misma, (
        "dos preguntas distintas puntuan mas que la misma pregunta reescrita: "
        f"{MEDIDO['par_confundible']} vs {misma}")

    # y lo que protege de verdad: por defecto el nivel similar esta apagado
    assert C.SIMILAR_POR_DEFECTO is False
    d = C.Cache(version=_v())
    d.guardar(RESERVAR, "RESPUESTA SOBRE RESERVAR")
    valor, info = d.buscar(COBRAR)
    assert valor is None and info["resultado"] == "miss", info


# ── caducidad por version: el motivo entero del modulo ───────────────────────

def invalidacion_si_cambia_corpus_hash():
    ruta = _ruta("corpus")
    C.Cache(ruta=ruta, version=_v()).guardar("que es un indice", "vieja")
    nueva = C.Cache(ruta=ruta, version=_v(corpus_hash="bbbb2222"))
    valor, info = nueva.buscar("que es un indice")
    assert valor is None, "una respuesta calculada contra otro corpus no se devuelve"
    assert info["resultado"] == "invalidado", info
    assert "corpus_hash" in info["motivo"], info["motivo"]
    assert "aaaa1111" in info["motivo"] and "bbbb2222" in info["motivo"], info["motivo"]


def invalidacion_si_cambia_embedding_model():
    ruta = _ruta("modelo-emb")
    C.Cache(ruta=ruta, version=_v()).guardar("que es un indice", "vieja")
    _, info = C.Cache(ruta=ruta,
                      version=_v(embedding_model="openai/text-embedding-3-small")
                      ).buscar("que es un indice")
    assert info["resultado"] == "invalidado", info
    assert "embedding_model" in info["motivo"], info["motivo"]
    assert "corpus_hash" not in info["motivo"], "solo se nombra el campo que cambio"


def invalidacion_si_cambia_embedding_version():
    ruta = _ruta("version-emb")
    C.Cache(ruta=ruta, version=_v()).guardar("que es un indice", "vieja")
    _, info = C.Cache(ruta=ruta, version=_v(embedding_version="v2")).buscar("que es un indice")
    assert info["resultado"] == "invalidado" and "embedding_version" in info["motivo"], info


def invalidacion_si_cambia_model_version():
    ruta = _ruta("modelo")
    C.Cache(ruta=ruta, version=_v()).guardar("que es un indice", "vieja")
    _, info = C.Cache(ruta=ruta, version=_v(model_version="anthropic/claude-opus-4")
                      ).buscar("que es un indice")
    assert info["resultado"] == "invalidado" and "model_version" in info["motivo"], info


def la_entrada_invalidada_no_vuelve_por_similitud():
    """Ni por la puerta de atras: caducada es caducada en los dos niveles."""
    ruta = _ruta("caducada-similar")
    C.Cache(ruta=ruta, version=_v()).guardar("que es un indice en postgres", "vieja")
    c = C.Cache(ruta=ruta, version=_v(corpus_hash="cccc"), umbral=0.90, similar=True)
    valor, info = c.buscar("que es un indice en postgresql")
    assert valor is None, "se sirvio una entrada caducada por el nivel similar"
    assert info["resultado"] == "invalidado" and "corpus_hash" in info["motivo"], info


def invalidar_tira_todo_y_lo_cuenta():
    c = C.Cache(ruta=_ruta("invalidar"), version=_v())
    for i in range(4):
        c.guardar(f"pregunta {i}", i)
    assert c.invalidar("reescribi la caja 04") == 4
    assert c.estadisticas()["entradas"] == 0
    assert c.buscar("pregunta 0")[1]["resultado"] == "miss"
    assert C.Cache(ruta=c.ruta, version=_v()).estadisticas()["entradas"] == 0, \
        "invalidar tiene que llegar al disco, no solo a la memoria"


# ── el archivo ───────────────────────────────────────────────────────────────

def archivo_que_no_existe():
    ruta = _ruta("no-existe")
    assert not ruta.exists()
    c = C.Cache(ruta=ruta, version=_v())
    assert c.estadisticas()["entradas"] == 0
    assert c.buscar("hola")[1]["resultado"] == "miss"
    assert "no existe" in c.motivo_carga, c.motivo_carga


def archivo_corrupto_degrada_a_vacio():
    """Bytes que no son ni texto: la cache arranca vacia y lo dice, no revienta."""
    for nombre, basura in (("bytes", b"\x00\x01\x02not json at all\xff\xfe"),
                           ("json-a-medias", b'{"formato": "cache-v1", "entradas": [{"cla'),
                           ("json-sin-entradas", b'{"hola": 1}'),
                           ("vacio", b"")):
        ruta = _ruta(f"corrupto-{nombre}")
        ruta.write_bytes(basura)
        c = C.Cache(ruta=ruta, version=_v())
        assert c.estadisticas()["entradas"] == 0, (nombre, c.motivo_carga)
        assert c.buscar("hola")[1]["resultado"] == "miss", nombre
        assert "ilegible" in c.motivo_carga, (nombre, c.motivo_carga)
        c.guardar("hola", "mundo")            # y se puede seguir usando
        assert C.Cache(ruta=ruta, version=_v()).buscar("hola")[0] == "mundo", nombre


def una_entrada_rota_no_tira_las_demas():
    ruta = _ruta("entrada-rota")
    c = C.Cache(ruta=ruta, version=_v())
    c.guardar("buena", "valor")
    datos = json.loads(ruta.read_text())
    datos["entradas"].append({"clave": "x"})          # sin consulta, sin version
    ruta.write_text(json.dumps(datos))
    otra = C.Cache(ruta=ruta, version=_v())
    assert otra.buscar("buena")[0] == "valor", otra.motivo_carga
    assert "descartada" in otra.motivo_carga, otra.motivo_carga


def persistencia_entre_instancias():
    ruta = _ruta("persistencia")
    C.Cache(ruta=ruta, version=_v()).guardar("¿Qué es un ÍNDICE?", {"texto": "...", "n": 3})
    valor, info = C.Cache(ruta=ruta, version=_v()).buscar("que es un indice")
    assert info["resultado"] == "exacto", info
    assert valor == {"texto": "...", "n": 3}, valor


def valor_no_serializable_no_rompe_el_archivo():
    ruta = _ruta("no-serializable")
    c = C.Cache(ruta=ruta, version=_v())
    c.guardar("con set", {1, 2, 3})                  # un set no es JSON
    c.guardar("normal", "si cabe")
    assert c.buscar("con set")[0] == {1, 2, 3}, "en memoria tiene que seguir estando"
    json.loads(ruta.read_text())                     # el archivo sigue siendo JSON valido
    otra = C.Cache(ruta=ruta, version=_v())
    assert otra.buscar("normal")[0] == "si cabe"
    assert otra.buscar("con set")[1]["resultado"] == "miss", "no se guarda a medias"


def dos_caches_sobre_el_mismo_archivo_no_lo_corrompen():
    """Ultimo que escribe gana, pero el archivo siempre es legible. Sin bloqueos."""
    ruta = _ruta("concurrencia")
    a = C.Cache(ruta=ruta, version=_v())
    b = C.Cache(ruta=ruta, version=_v())
    for i in range(10):
        a.guardar(f"pregunta a{i}", f"valor a{i}")
        b.guardar(f"pregunta b{i}", f"valor b{i}")
        json.loads(ruta.read_text(encoding="utf-8"))          # nunca a medias
    tercera = C.Cache(ruta=ruta, version=_v())
    assert tercera.buscar("pregunta b9")[0] == "valor b9", tercera.motivo_carga
    assert not list(CARPETA.glob("*.tmp")), "quedaron temporales sin renombrar"
    # y el limite conocido, escrito para que nadie lo descubra en produccion:
    assert tercera.buscar("pregunta a9")[1]["resultado"] == "miss", \
        "si esto acierta es que ahora hay fusion entre procesos: actualizar los LIMITES"


def desalojo_cuando_se_pasa_del_maximo():
    c = C.Cache(ruta=_ruta("desalojo"), version=_v(), maximo=3)
    for i in range(5):
        c.guardar(f"pregunta {i}", i)
    st = c.estadisticas()
    assert st["entradas"] == 3, st
    assert st["desalojados"] == 2, st
    assert c.buscar("pregunta 0")[1]["resultado"] == "miss", "la mas vieja tenia que caer"
    assert c.buscar("pregunta 4")[0] == 4, "la mas nueva tenia que quedarse"


# ── cuentas ──────────────────────────────────────────────────────────────────

def estadisticas_cuentan_exacto_y_similar_por_separado():
    c = C.Cache(version=_v(), umbral=0.90, similar=True)
    c.guardar("que es un indice en postgres", "un indice es ...")
    c.buscar("que es un indice en postgres")          # exacto
    c.buscar("que es un indice en postgresql")        # similar
    c.buscar("como configuro stripe")                 # miss
    st = c.estadisticas()
    assert (st["exactos"], st["similares"], st["misses"]) == (1, 1, 1), st
    assert st["tasa_exacta"] and st["tasa_similar"], st
    assert not any("acierto" in k for k in st), \
        "no puede existir una tasa unica: mezclaria una certeza con una apuesta"
    assert st["similar_activado"] is True and st["umbral"] == 0.90, st


def estadisticas_cuentan_los_invalidados_aparte():
    ruta = _ruta("stats-invalidados")
    C.Cache(ruta=ruta, version=_v()).guardar("que es un indice", "vieja")
    c = C.Cache(ruta=ruta, version=_v(corpus_hash="dddd"))
    c.buscar("que es un indice")
    st = c.estadisticas()
    assert st["invalidados"] == 1 and st["misses"] == 0, st
    assert st["exactos"] == 0, "un invalidado no es un acierto"


# ── la version en si ─────────────────────────────────────────────────────────

def la_version_actual_trae_los_cuatro_campos():
    v = C.version_actual()
    assert set(v) == set(C.CAMPOS_VERSION), v
    assert all(isinstance(x, str) and x for x in v.values()), v
    assert v["corpus_hash"] == C.hash_corpus(), v


def el_corpus_hash_cambia_si_cambia_el_contenido():
    """Un parrafo distinto con el mismo numero de trozos tiene que dar otro hash."""
    uno = [rag.Trozo("texto a", "texto a", "04 · Databases", "t")]
    otro = [rag.Trozo("texto b", "texto a", "04 · Databases", "t")]
    assert C.hash_corpus(uno) != C.hash_corpus(otro)
    assert C.hash_corpus(uno) == C.hash_corpus(uno), "el hash tiene que ser estable"
    assert len(C.hash_corpus(uno)) == C.LARGO_HASH


def el_informe_siempre_explica_que_paso():
    ruta = _ruta("informes")
    C.Cache(ruta=ruta, version=_v()).guardar("que es un indice en postgres", "v")
    c = C.Cache(ruta=ruta, version=_v(), umbral=0.90, similar=True)
    vieja = C.Cache(ruta=ruta, version=_v(model_version="otro"))
    informes = [c.buscar("que es un indice en postgres")[1],
                c.buscar("que es un indice en postgresql")[1],
                c.buscar("nada que ver con esto")[1],
                vieja.buscar("que es un indice en postgres")[1]]
    resultados = [i["resultado"] for i in informes]
    assert resultados == ["exacto", "similar", "miss", "invalidado"], resultados
    for i in informes:
        assert set(i) >= {"resultado", "similitud", "motivo", "clave"}, i
        assert len(i["motivo"]) > 20, i
        assert isinstance(i["similitud"], float), i


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "_")) \
                and getattr(fn, "__module__", "") == "__main__":
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))

    print("\n  medido con la señal local (n-gramas de caracteres, sin semantica):")
    for que, cuanto in MEDIDO.items():
        print(f"    {cuanto:.3f}  {que.replace('_', ' ')}")
    print(f"    umbral por defecto: {C.UMBRAL} · nivel similar por defecto: "
          f"{'ON' if C.SIMILAR_POR_DEFECTO else 'OFF'}")

    shutil.rmtree(CARPETA, ignore_errors=True)
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
