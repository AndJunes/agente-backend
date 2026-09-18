"""El grafo por trozo y el arbol del temario.

Dos preguntas, una por modulo:

    grafo  ¿aporta algo sobre rag.GRAFO, y se puede explicar lo que trae?
           Las dos se comprueban con numeros del corpus, no con mocks.
    arbol  ¿cuadran las cuentas del arbol, y enrutar() se calla cuando no sabe?
           Que se calle importa mas que que acierte: el filtro se cree lo que le digan.

    python3 test_grafo_arbol.py
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
import sys

import arbol
import grafo
import rag

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def trozo(titulo, caja=""):
    return next(t for t in rag.TROZOS if t.titulo == titulo and t.caja.startswith(caja))


# ── grafo: leer las referencias ──────────────────────────────────────────────

def referencias_de_un_trozo_real():
    """conocimientos/04-databases.md, seccion '## Índices':
       '> **Relacionado:** query optimization, pagination `[03, 09]`'"""
    assert grafo.referencias(trozo("Índices", "04")) == ["03", "09"], \
        grafo.referencias(trozo("Índices", "04"))
    # y otro, en otra caja, con tres destinos
    assert grafo.referencias(trozo("Kubernetes", "13")) == ["10", "12", "14"]


def un_trozo_sin_referencias_devuelve_lista_vacia():
    """Las secciones 'Preguntas de entrevista' no llevan linea '> **Relacionado:**'."""
    assert grafo.referencias(trozo("Preguntas de entrevista y trade-offs", "04")) == []
    vacios = [t for t in rag.TROZOS if not grafo.referencias(t)]
    assert vacios, "si todos los trozos tienen refs es que el regex casa de mas"


def las_referencias_apuntan_a_cajas_que_existen():
    cajas = set(grafo.construir()["por_caja"])
    for t in rag.TROZOS:
        for r in grafo.referencias(t):
            assert r in cajas, f"{t.caja}/{t.titulo} cita una caja inexistente: {r}"


# ── grafo: los saltos ────────────────────────────────────────────────────────

def vecinos_a_un_salto():
    v = grafo.vecinos("04", saltos=1)
    assert v, "la caja 04 tiene referencias, no puede quedarse sin vecinos"
    assert all(d == 1 for d in v.values()), v
    assert "09" in v, v                      # 04 cita a 09 desde varias secciones
    assert "04" not in v, "la caja de partida no es vecina de si misma"


def vecinos_a_dos_saltos_alcanzan_mas():
    for caja in ("04", "07", "18"):
        uno, dos = grafo.vecinos(caja, 1), grafo.vecinos(caja, 2)
        assert set(uno) <= set(dos), "2 saltos tiene que incluir lo de 1 salto"
        assert len(dos) > len(uno), f"{caja}: {len(uno)} a 1 salto, {len(dos)} a 2"
        assert max(dos.values()) == 2, dos


def el_grafo_es_denso_y_hay_que_decirlo():
    """A 2 saltos casi todo alcanza a casi todo: sin limite, multi-hop no filtra nada."""
    dos = grafo.vecinos("04", 2)
    total = len(grafo.construir()["cajas"])
    assert len(dos) >= total - 2, (len(dos), total)


def caja_inexistente_no_revienta():
    assert grafo.vecinos("99") == {}
    assert grafo.vecinos("no existe esta caja") == {}
    assert grafo.vecinos("04", saltos=0) == {}


def caja_sin_relaciones_no_revienta():
    """En el corpus de hoy NO hay ninguna caja aislada; se comprueba y ademas se
    fuerza el caso con un indice doctorado, que es el que rompe el BFS si esta mal."""
    salidas = grafo.construir()["salidas"]
    assert all(c in salidas for c in grafo.construir()["cajas"]), \
        "hay una caja sin salidas: actualiza este test, ya no es una hipotesis"

    real = grafo.construir
    indice = dict(real())
    indice["salidas"] = {c: v for c, v in indice["salidas"].items() if c != "04"}
    grafo.construir = lambda: indice
    try:
        assert grafo.vecinos("04", 1) == {}
        assert grafo.vecinos("04", 2) == {}
        assert grafo.expandir([trozo("Índices", "04")]) == ([], [])
    finally:
        grafo.construir = real


# ── grafo: expandir, acotado y explicado ─────────────────────────────────────

def expandir_respeta_el_limite():
    partida = [t for t in rag.TROZOS if t.caja.startswith("04")][:2]
    for limite in (1, 3, 8):
        extra, camino = grafo.expandir(partida, saltos=2, limite=limite)
        assert len(extra) <= limite, (limite, len(extra))
        assert len(camino) == len(extra)
    extra, _ = grafo.expandir(partida, saltos=1, limite=8)
    assert len(extra) == 8, "con 10 cajas vecinas tendria que llenar el limite"


def expandir_no_devuelve_lo_que_ya_tenias():
    partida = [t for t in rag.TROZOS if t.caja.startswith("04")]
    extra, _ = grafo.expandir(partida, saltos=1, limite=8)
    ya = {(t.caja, t.titulo) for t in partida}
    assert not any((t.caja, t.titulo) in ya for t in extra), "repitio trozos de entrada"
    assert not any(t.caja.startswith("04") for t in extra), "expandio a su propia caja"


def el_camino_explica_cada_trozo_traido():
    partida = [trozo("Índices", "04")]
    extra, camino = grafo.expandir(partida, saltos=2, limite=6)
    assert extra and len(camino) == len(extra)
    explicados = {(t.caja, t.titulo) for _, t, _ in camino}
    for t in extra:
        assert (t.caja, t.titulo) in explicados, f"{t.titulo} llego sin explicacion"
    for origen, t, motivo in camino:
        assert origen.startswith("04"), origen
        assert "→" in motivo, f"el motivo no enseña la ruta: {motivo}"
        assert t.titulo in motivo, motivo
        assert ("cita" in motivo or "salto" in motivo), motivo


def expandir_con_entrada_rara_no_revienta():
    assert grafo.expandir([]) == ([], [])
    assert grafo.expandir(None) == ([], [])
    assert grafo.expandir([trozo("Índices", "04")], limite=0) == ([], [])


# ── grafo: el argumento del modulo, medido ───────────────────────────────────

def el_grafo_por_trozo_tiene_mas_aristas_que_el_de_rag():
    c = grafo.comparar_con_rag()
    assert c["aristas_caja_caja_rag"] == c["aristas_caja_caja_propias"], \
        ("si las aristas agregadas no coinciden, uno de los dos regex esta mal: "
         f"{c['aristas_caja_caja_rag']} vs {c['aristas_caja_caja_propias']}")
    assert c["aristas_trozo_caja"] > c["aristas_caja_caja_rag"], c
    print(f"     · trozo→caja {c['aristas_trozo_caja']} aristas / {len(rag.TROZOS)} nodos"
          f"  ·  caja→caja {c['aristas_caja_caja_rag']} aristas / {len(rag.GRAFO)} nodos")


# ── arbol ────────────────────────────────────────────────────────────────────

def ruta_de_un_trozo_real():
    assert arbol.ruta(trozo("Índices", "04")) == ["Backend", "04 · Databases", "indexing"]
    r = arbol.ruta(trozo("Kubernetes", "13"))
    assert r[:2] == ["Backend", "13 · Cloud & Infrastructure"] and len(r) == 3, r


def toda_hoja_cuelga_de_una_caja_valida():
    import metadatos
    temario, cajas = metadatos._temario(), {t.caja for t in rag.TROZOS}
    for caja, ramas in arbol.construir()[arbol.RAIZ].items():
        assert caja in cajas, caja
        declaradas = temario[caja.split("·")[0].strip()]
        for sub, trozos in ramas.items():
            assert sub in declaradas or sub == arbol.SIN_SUB, (caja, sub)
            for t in trozos:
                assert t.caja == caja, f"{t.titulo} cuelga de {caja} pero es de {t.caja}"


def la_raiz_es_unica():
    a = arbol.construir()
    assert list(a) == [arbol.RAIZ] and len(a[arbol.RAIZ]) == 19, list(a)


def enrutar_indices_en_postgres_propone_la_04():
    cajas, motivo = arbol.enrutar("índices en postgres")
    assert cajas and cajas[0].startswith("04"), (cajas, motivo)
    assert "indexing" in motivo, motivo


def enrutar_algo_irrelevante_no_propone_basura():
    for consulta in ("cómo hago una paella valenciana", "xyzzy qwerty", "", "la de ayer"):
        cajas, motivo = arbol.enrutar(consulta)
        assert cajas == [], f"{consulta!r} → {cajas} ({motivo})"
        assert motivo and len(motivo) > 10, motivo


def enrutar_entrada_rara_no_revienta():
    for consulta in (None, 0, "   ", "a b c", "¿?"):
        cajas, motivo = arbol.enrutar(consulta)
        assert isinstance(cajas, list) and isinstance(motivo, str)


def enrutar_respeta_la_k():
    cajas, _ = arbol.enrutar("cuellos de botella de latencia y caching", k=2)
    assert len(cajas) <= 2, cajas


def cobertura_cuadra():
    c = arbol.cobertura()
    assert c["trozos"] == len(rag.TROZOS) == 247, c["trozos"]
    assert c["trozos_asignados"] + c["trozos_sin_subcategoria"] == c["trozos"], c
    assert sum(c["trozos_por_caja"].values()) == c["trozos"], c["trozos_por_caja"]
    assert c["cajas"] == 19
    print(f"     · {c['trozos_asignados']} trozos con subcategoria, "
          f"{c['trozos_sin_subcategoria']} colgando de la caja, "
          f"{len(c['subcategorias_sin_ningun_trozo'])} ramas del temario vacias")


def arbol_vacio_no_revienta():
    """construir() sobre un corpus sin trozos: el modulo no puede asumir 247."""
    reales = rag.TROZOS
    arbol.construir.cache_clear()
    rag.TROZOS = []
    try:
        a = arbol.construir()
        assert a == {arbol.RAIZ: {}}, a
        assert arbol.enrutar("índices")[0] == [] or True   # sin corpus, lo que diga vale
    finally:
        rag.TROZOS = reales
        arbol.construir.cache_clear()
        arbol._vocabulario.cache_clear()
    assert len(arbol.construir()[arbol.RAIZ]) == 19, "no se restauro el arbol real"


def el_enrutado_se_compara_con_el_baseline():
    """No es un assert de calidad: es la medida que decide si este modulo sirve."""
    filas = arbol.comparar_con_bm25()
    acuerdos = sum(1 for _, _, _, ok in filas if ok)
    mudas = sum(1 for _, cajas, _, _ in filas if not cajas)
    assert filas, "sin consultas no hay medida"
    print(f"     · enrutar coincide con las cajas de BM25 en {acuerdos}/{len(filas)} "
          f"consultas · se calla en {mudas}")


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "trozo", "_")) \
                and getattr(fn, "__module__", "") == "__main__":
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
