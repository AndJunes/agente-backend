"""La jerarquia Backend → caja → subcategoria → trozo, y el enrutado por ella.

DE DONDE SALE CADA NIVEL (nada es nuevo)
    Backend         raiz unica, puesta a mano: el corpus entero es un temario de backend.
    caja            la primera linea de cada .md. 19, escritas a mano en el corpus.
    subcategoria    la linea '**Cubre del temario:**', via metadatos._temario().
                    88 subcategorias distintas declaradas en 19/19 archivos.
    trozo           el reparto trozo -> subcategoria lo hace metadatos.de(), por
                    coincidencia de palabras. NO lo escribio nadie: es derivado y falla.

    Este modulo no inventa taxonomia. Si una caja no declara una subcategoria, aqui no
    aparece; si un trozo no encaja en ninguna, cuelga de la caja directamente y se
    cuenta aparte en cobertura(). Un arbol con una rama '(sin subcategoría)' honesta es
    mas util que uno completo a base de rellenar.

EL ENRUTADO, Y SU LIMITE MEDIDO
    enrutar() puntua cajas contra el VOCABULARIO del temario (nombres de subcategoria
    + los sinonimos de metadatos), no contra los 247 trozos: es un diccionario
    precalculado, O(palabras de la consulta). Por eso es barato.

    Pero barato no es lo mismo que mejor. Comparado contra el baseline obvio — buscar
    con BM25 y quedarse con las cajas de los mejores trozos — el enrutado por arbol
    acierta cuando la consulta usa el vocabulario del temario y se queda MUDO cuando no
    (devuelve [] a proposito). El __main__ de este modulo mide ese acuerdo sobre
    consultas reales; leelo antes de encender este componente en el pipeline.
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
from functools import lru_cache

import metadatos
import rag

RAIZ = "Backend"
SIN_SUB = "(sin subcategoría)"

# Palabras que no distinguen nada al enrutar. Misma idea que suficiencia.VACIAS, pero
# esta lista solo tiene que proteger un diccionario de 88 terminos.
VACIAS = {"como", "que", "para", "por", "con", "los", "las", "del", "una", "uno",
          "cual", "cuales", "donde", "cuando", "hacer", "puedo", "quiero", "necesito",
          "mejor", "usar", "entre", "sobre", "esto", "esta", "the", "and", "for",
          "with", "mis", "sus", "hay", "son", "ser", "muy", "mas", "menos"}

MINIMO_AGUJA = 4      # una aguja mas corta casa con cualquier cosa ('rag' en 'tragedia')
MINIMO_TERMINO = 4    # idem por el otro lado


@lru_cache(maxsize=1)
def construir() -> dict:
    """El arbol: {RAIZ: {caja: {subcategoria: [trozos]}}}.

    Las subcategorias declaradas que no atrapan ningun trozo se dejan con lista vacia
    en vez de borrarse: que una rama del temario este vacia es informacion.
    """
    arbol = {}
    temario = metadatos._temario()
    for t in rag.TROZOS:
        m = metadatos.de(t)
        rama = arbol.setdefault(t.caja, {s: [] for s in temario.get(m.domain, ())})
        for sub in (m.subdomains or (SIN_SUB,)):
            rama.setdefault(sub, []).append(t)
    return {RAIZ: dict(sorted(arbol.items()))}


def ruta(trozo) -> list:
    """Donde cuelga este trozo: ['Backend', '04 · Databases', 'indexing'].

    Si tiene varias subcategorias se devuelve la primera (las demas estan en
    metadatos.de().subdomains); si no tiene ninguna, la hoja es '(sin subcategoría)'.
    Entrada rara (None, algo que no es un Trozo) devuelve solo la raiz, sin reventar.
    """
    caja = getattr(trozo, "caja", None)
    if not caja:
        return [RAIZ]
    try:
        subs = metadatos.de(trozo).subdomains
    except Exception:
        subs = ()
    return [RAIZ, caja, subs[0] if subs else SIN_SUB]


@lru_cache(maxsize=1)
def _vocabulario():
    """{(palabras de la aguja): {caja: [subcategorias que la aportan]}}.

    La aguja es el nombre de la subcategoria (con '_' como espacio), sus sinonimos de
    metadatos.SINONIMOS y las palabras del nombre de la caja ('databases', 'security').
    Se guarda ya partida en palabras largas: una aguja de varias palabras ('cuello de
    botella') no puede casar con un solo token de la consulta.
    Es el unico indice que mira enrutar(): 88 subcategorias, no 247 trozos.
    """
    vocab = {}

    def apuntar(aguja, caja, fuente):
        palabras = tuple(p for p in rag._normalizar(aguja).replace("-", " ").split()
                         if len(p) >= MINIMO_AGUJA)
        if not palabras:
            return
        vocab.setdefault(palabras, {}).setdefault(caja, []).append(fuente)

    temario = metadatos._temario()
    nombres = {t.caja.split("·")[0].strip(): t.caja for t in rag.TROZOS}
    for numero, subs in temario.items():
        caja = nombres.get(numero, numero)
        for sub in subs:
            if sub == "concepts":           # el cajon del resto: no enruta nada
                continue
            apuntar(sub.replace("_", " "), caja, sub)
            for sinonimo in metadatos.SINONIMOS.get(sub, ()):
                apuntar(sinonimo, caja, sub)
        for palabra in rag._normalizar(caja.split("·")[-1]).replace("&", " ").split():
            apuntar(palabra, caja, "(nombre de la caja)")
    return vocab


def _casa(palabra, terminos):
    """El termino de la consulta que casa con esta palabra del temario, o None.

    Solo por PREFIJO, en los dos sentidos: 'indices' empieza por la aguja 'indice' y la
    consulta 'auth' es el principio de 'authentication'. Permitir la subcadena suelta
    daba falsos positivos absurdos — 'ayer' casaba dentro de 'layered' y mandaba
    "la de ayer" a System Design.
    """
    for termino in terminos:
        if termino.startswith(palabra) or palabra.startswith(termino):
            return termino
    return None


def enrutar(consulta, k=3):
    """Las k cajas que el ARBOL propone para la consulta, y por que.

    Devuelve (cajas, motivo). Si ninguna palabra de la consulta esta en el vocabulario
    del temario devuelve ([], motivo) — callarse es la respuesta correcta: proponer
    cajas al azar es peor que no proponer nada, porque el filtro de metadatos se las
    creeria.
    """
    texto = rag._normalizar(str(consulta or ""))
    terminos = [p.strip(".,;:()¿?¡!\"'") for p in texto.split()]
    terminos = [p for p in dict.fromkeys(terminos)
                if len(p) >= MINIMO_TERMINO and p not in VACIAS]
    if not terminos:
        return [], "la consulta no tiene ninguna palabra con la que enrutar"

    vocab = _vocabulario()
    puntos, pruebas = {}, {}
    for palabras, cajas in vocab.items():
        casan = [_casa(p, terminos) for p in palabras]
        if not all(casan):        # una aguja de varias palabras las exige todas
            continue
        for caja, fuentes in cajas.items():
            puntos[caja] = puntos.get(caja, 0) + 1
            pruebas.setdefault(caja, []).append(f"'{casan[0]}'→`{fuentes[0]}`")

    if not puntos:
        return [], (f"ninguna palabra de la consulta ({', '.join(terminos[:4])}) aparece "
                    f"en el temario: el arbol no sabe enrutar esto")

    orden = sorted(puntos.items(), key=lambda x: (-x[1], x[0]))
    # una sola coincidencia entre muchas cajas empatadas es ruido, no una señal
    if orden[0][1] == 1 and sum(1 for _, p in orden if p == 1) > k:
        return [], (f"{len(orden)} cajas empatadas a una sola coincidencia "
                    f"({', '.join(p[0] for p in orden[:3])}...): demasiado flojo para enrutar")

    cajas = [c for c, _ in orden[:k]]
    detalle = "; ".join(f"{c} ({', '.join(dict.fromkeys(pruebas[c]))})" for c in cajas)
    return cajas, f"temario: {detalle}"


def cobertura() -> dict:
    """Cuantos trozos cuelgan de cada nivel y cuantos no llegan a hoja.

    La comprobacion que importa: asignados + sin_subcategoria == len(rag.TROZOS).
    Un trozo cuenta como asignado una sola vez aunque caiga en varias subcategorias.
    """
    arbol = construir()[RAIZ]
    asignados, sin_sub, por_caja = set(), set(), {}
    ramas_vacias = []
    for caja, ramas in arbol.items():
        vistos = set()
        for sub, trozos in ramas.items():
            if not trozos:
                ramas_vacias.append(f"{caja}/{sub}")
            for t in trozos:
                vistos.add((t.caja, t.titulo))
                (sin_sub if sub == SIN_SUB else asignados).add((t.caja, t.titulo))
        por_caja[caja] = len(vistos)
    sin_sub -= asignados            # por si un trozo cayera en las dos ramas
    return {
        "raiz": RAIZ,
        "cajas": len(arbol),
        "subcategorias": sum(len(r) for r in arbol.values()),
        "subcategorias_sin_ningun_trozo": ramas_vacias,
        "trozos": len(rag.TROZOS),
        "trozos_asignados": len(asignados),
        "trozos_sin_subcategoria": len(sin_sub),
        "trozos_por_caja": por_caja,
    }


# ── el baseline contra el que hay que medir este modulo ──────────────────────
# Consultas reales del dominio. Se comparan las cajas del arbol contra las cajas de
# los mejores trozos segun BM25: si el arbol no aporta nada sobre eso, sobra.
CONSULTAS = [
    "índices en postgres", "cómo cobro con stripe", "reintentos idempotentes en colas",
    "autenticación con JWT", "trazas distribuidas y métricas", "despliegue canary",
    "subida de archivos grandes", "rag con embeddings", "tests de contrato",
    "cuellos de botella de latencia",
]


def comparar_con_bm25(k=3):
    """Acuerdo entre enrutar() y 'las cajas de los k mejores trozos de rag'."""
    filas = []
    for consulta in CONSULTAS:
        cajas, _ = enrutar(consulta, k=k)
        mejores = rag._ranking(rag.TROZOS, consulta, k)
        base = list(dict.fromkeys(t.caja for t, _ in mejores))
        filas.append((consulta, cajas, base, bool(set(cajas) & set(base))))
    return filas


if __name__ == "__main__":
    c = cobertura()
    print(f"{c['raiz']} → {c['cajas']} cajas → {c['subcategorias']} subcategorias → "
          f"{c['trozos']} trozos\n")
    print(f"  trozos con hoja de subcategoria : {c['trozos_asignados']}")
    print(f"  trozos colgando de la caja      : {c['trozos_sin_subcategoria']}")
    print(f"  suma                            : "
          f"{c['trozos_asignados'] + c['trozos_sin_subcategoria']} / {c['trozos']}")
    vacias = c["subcategorias_sin_ningun_trozo"]
    print(f"  ramas del temario sin ningun trozo ({len(vacias)}): "
          f"{', '.join(vacias[:6])}{'...' if len(vacias) > 6 else ''}")

    print("\n  enrutado por arbol vs cajas del BM25:")
    acuerdos = 0
    for consulta, cajas, base, ok in comparar_con_bm25():
        acuerdos += ok
        arbol_txt = ", ".join(c.split("·")[0].strip() for c in cajas) or "— (se calla)"
        base_txt = ", ".join(b.split("·")[0].strip() for b in base)
        print(f"    {'✓' if ok else '·'} {consulta:<34} arbol[{arbol_txt}]  bm25[{base_txt}]")
    print(f"\n  coinciden en {acuerdos}/{len(CONSULTAS)} consultas")
