"""El 'RAG': busca en los documentos de conocimientos/.

Trocea cada .md por sus titulos '## ' y puntua los trozos por las palabras de la
pregunta, pesando cada palabra por lo rara que es (IDF).

Ademas del buscador general hay tres busquedas TIPADAS que aprovechan la estructura
del corpus: las fichas de cada concepto y las referencias [NN] entre cajas.

En produccion esto seria pgvector + busqueda hibrida + reranker (ver
conocimientos/18-ai-backend.md). El agente no se entera: solo le importa
que estas funciones devuelvan texto.
"""

import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

CARPETA = Path(__file__).parent / "conocimientos"
TITULOS_DE_FALLO = ("Cómo falla", "Escenarios de fallo", "Inconsistencias de negocio")


class Trozo(NamedTuple):
    texto: str       # lo que se le devuelve al modelo
    norm: str        # el mismo texto normalizado, para buscar
    caja: str        # "04 · Databases"
    titulo: str      # "Índices"


def _normalizar(texto):
    """minusculas y sin acentos, para que 'cuántos días' case con 'dias'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _ficha_de(seccion):
    """Extrae el bloque '> **Ficha** ...' de una seccion, si lo tiene."""
    lineas, dentro = [], False
    for linea in seccion.split("\n"):
        if linea.startswith("> **Ficha**"):
            dentro = True
        if dentro:
            if not linea.startswith(">"):
                break
            lineas.append(linea.lstrip("> "))
    return " ".join(lineas)


def _campo(ficha, nombre):
    """Saca un campo concreto de la ficha, p.ej. 'Cómo falla'."""
    m = re.search(rf"\*\*{nombre}:\*\*(.+?)(?: · \*\*|$)", ficha)
    return m.group(1).strip() if m else ""


def _secciones(contenido):
    """Parte el documento por los '## ', RESPETANDO los bloques de codigo.

    Partir por la cadena "\\n## " a secas convierte cualquier '##' que viva dentro de
    un bloque ``` en una seccion del documento. La plantilla de ADR de la caja 19
    generaba asi cinco trozos fantasma ('Estado', 'Contexto', 'Decision'...) y le
    robaba la ficha a la seccion de verdad.
    """
    secciones, actual, en_bloque = [], None, False
    for linea in contenido.split("\n"):
        if linea.lstrip().startswith("```"):
            en_bloque = not en_bloque
        if not en_bloque and linea.startswith("## "):
            if actual is not None:
                secciones.append("\n".join(actual))
            actual = [linea[3:]]                                 # el titulo, ya sin '## '
        elif actual is not None:
            actual.append(linea)
    if actual is not None:
        secciones.append("\n".join(actual))
    return secciones


def _cargar():
    trozos, fichas, fallos, antipatrones = [], [], [], []
    for archivo in sorted(CARPETA.glob("[0-9]*.md")):
        contenido = archivo.read_text()
        caja = contenido.split("\n", 1)[0].lstrip("# ")          # "04 · Databases"
        for seccion in _secciones(contenido):                    # un trozo por titulo '##'
            titulo = seccion.split("\n", 1)[0].strip()
            if titulo.startswith("Fuentes"):                     # bibliografia: no es conocimiento
                continue

            def trozo(texto):
                return Trozo(texto, _normalizar(texto), caja, titulo)

            trozos.append(trozo(f"[{caja}]\n\n## {seccion.strip()}"))

            if ficha := _ficha_de(seccion):
                fichas.append(trozo(f"[{caja}] {titulo} — {ficha}"))
                if falla := _campo(ficha, "Cómo falla"):
                    fallos.append(trozo(f"[{caja}] {titulo} — falla así: {falla}"))
                if anti := _campo(ficha, "Anti-patrón"):
                    patron = _campo(ficha, "Patrón")
                    antipatrones.append(trozo(
                        f"[{caja}] {titulo}\n  ✗ NO: {anti}\n  ✓ SÍ: {patron or '(ver la caja)'}"))
            if titulo.startswith(TITULOS_DE_FALLO):               # secciones enteras de fallos
                fallos.append(trozo(f"[{caja}]\n\n## {seccion.strip()}"))
    return trozos, fichas, fallos, antipatrones


TROZOS, FICHAS, FALLOS, ANTIPATRONES = _cargar()   # se cargan una vez, al importar


def _grafo():
    """Quien referencia a quien, leyendo las marcas `[NN]` del texto."""
    g = {}
    for t in TROZOS:
        refs = Counter()
        for grupo in re.findall(r"`\[([0-9,\s]+)\]`", t.texto):
            refs.update(int(n) for n in grupo.split(",") if n.strip())
        g.setdefault(t.caja, Counter()).update(refs)
    return g


GRAFO = _grafo()


def _peso(palabra, indice):
    """IDF: 'como' sale en casi todos los trozos y no distingue nada;
    'outbox' sale en dos y lo distingue todo."""
    return math.log(len(indice) / (1 + sum(palabra in t.norm for t in indice)))


def _filtrar(indice, cajas):
    """Deja solo los trozos de esas cajas. Acepta nombre o numero ('04', 'Databases')."""
    if not cajas:
        return indice
    claves = [_normalizar(str(c)) for c in cajas]
    filtrado = [t for t in indice if any(c in _normalizar(t.caja) for c in claves)]
    return filtrado or indice          # si el filtro no deja nada, mejor buscar en todo


def _ranking_idf(indice, query, k, cajas=None):
    """El metodo original: IDF x sqrt(tf), contando SUBCADENAS.

    Contar subcadenas hace de stemmer pobre pero efectivo en español: 'indice'
    casa dentro de 'indices' y de 'indexing'. Se conserva porque el BM25 por
    tokens, que es lo correcto de manual, pierde justamente eso.
    """
    indice = _filtrar(indice, cajas)
    pesos = {p: _peso(p, indice) for p in set(_normalizar(query).split()) if len(p) >= 3}
    if not pesos:
        return []
    # sqrt = saturacion: 10 repeticiones no valen 10 veces mas que una (como hace BM25)
    def puntuar(t):
        return sum(math.sqrt(t.norm.count(p)) * peso for p, peso in pesos.items())

    mejores = sorted(indice, key=puntuar, reverse=True)[:k]
    return [(t, puntuar(t)) for t in mejores if puntuar(t) > 0]


# BM25 de verdad: saturacion controlada (k1) y normalizacion por longitud (b), que
# es lo que le faltaba al metodo anterior — un trozo largo acumulaba puntos solo por
# ser largo.
K1, B = 1.5, 0.75
PREFIJO = 5          # tokens que comparten este prefijo cuentan como el mismo


@lru_cache(maxsize=8192)
def _tokens(norm):
    return tuple(re.findall(r"[a-z0-9_]{3,}", norm))


@lru_cache(maxsize=8192)
def _frecuencias(norm):
    cuenta = Counter(_tokens(norm))
    # ademas por prefijo, para no perder la morfologia del español:
    # 'indice', 'indices' e 'indexacion' comparten 'indic'/'index' parcialmente
    for token, n in list(cuenta.items()):
        cuenta["^" + token[:PREFIJO]] += n
    return cuenta


def _ranking_bm25(indice, query, k, cajas=None):
    """BM25 sobre tokens, con una concesion: los prefijos tambien cuentan."""
    indice = _filtrar(indice, cajas)
    terminos = [p for p in dict.fromkeys(_normalizar(query).split()) if len(p) >= 3]
    if not indice or not terminos:
        return []

    frecuencias = [_frecuencias(t.norm) for t in indice]
    longitudes = [sum(n for tok, n in f.items() if not tok.startswith("^"))
                  for f in frecuencias]
    media = (sum(longitudes) / len(longitudes)) or 1
    n = len(indice)

    pesos = {}
    for termino in terminos:
        clave = "^" + termino[:PREFIJO]
        df = sum(1 for f in frecuencias if f.get(termino) or f.get(clave))
        if df:
            pesos[termino] = math.log(1 + (n - df + 0.5) / (df + 0.5))
    if not pesos:
        return []

    puntuaciones = []
    for trozo, f, dl in zip(indice, frecuencias, longitudes):
        total = 0.0
        for termino, idf in pesos.items():
            # el prefijo vale la mitad: es una coincidencia mas floja que el token entero
            tf = f.get(termino, 0) + 0.5 * f.get("^" + termino[:PREFIJO], 0)
            if tf:
                total += idf * (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * dl / media))
        if total > 0:
            puntuaciones.append((trozo, total))
    puntuaciones.sort(key=lambda x: x[1], reverse=True)
    return puntuaciones[:k]


# Cual se usa. Se cambia para medir: el benchmark decide, no la costumbre.
METODO = "bm25"


def _ranking(indice, query, k, cajas=None):
    """Los k trozos mejor puntuados, con su puntuacion."""
    if METODO == "idf":
        return _ranking_idf(indice, query, k, cajas)
    return _ranking_bm25(indice, query, k, cajas)


def _buscar_en(indice, query, k, separador="\n\n---\n\n", cajas=None):
    mejores = _ranking(indice, query, k, cajas)
    if not mejores:
        return "Sin resultados."
    return separador.join(t.texto for t, _ in mejores)


def buscar(query: str, cajas=None, k=3) -> str:
    """Busqueda general. `cajas` acota a unas areas concretas (menos contexto, menos ruido)."""
    return _buscar_en(TROZOS, query, k=k, cajas=cajas)


def buscar_tradeoffs(tema: str, cajas=None, k=5) -> str:
    """Solo las fichas: trade-offs, limites y decisiones de cada concepto."""
    return _buscar_en(FICHAS, tema, k=k, separador="\n\n", cajas=cajas)


def buscar_fallos(tema: str, cajas=None, k=5) -> str:
    """Solo lo que puede salir mal: secciones de fallos y el campo 'Cómo falla'."""
    return _buscar_en(FALLOS, tema, k=k, separador="\n\n", cajas=cajas)


def buscar_antipatrones(tema: str, cajas=None, k=6) -> str:
    """Solo los errores conocidos: que NO hacer y que hacer en su lugar.
    Sirve para revisar codigo contra los fallos que el corpus ya documenta."""
    return _buscar_en(ANTIPATRONES, tema, k=k, separador="\n\n", cajas=cajas)


def cajas_relacionadas(caja: str) -> str:
    """Que cajas referencia esta y cuales la referencian a ella."""
    clave = next((c for c in GRAFO if _normalizar(caja) in _normalizar(c)), None)
    if not clave:
        # adivinar la caja por contenido devolvia resultados erroneos ("pagos" -> Architecture,
        # porque la palabra sale de pasada por todo el corpus). Mejor fallar informando:
        # el modelo reintenta con el nombre correcto.
        return ("No existe esa caja. Usa el nombre o el numero de una de estas:\n  "
                + "\n  ".join(sorted(GRAFO)))
    numero = int(clave.split("·")[0].strip())
    salen = GRAFO[clave]
    entran = Counter({c: g[numero] for c, g in GRAFO.items() if g.get(numero) and c != clave})
    nombre = {int(c.split("·")[0]): c for c in GRAFO}
    fmt = lambda cnt: ", ".join(f"{nombre.get(n, n)} ({v})" for n, v in cnt.most_common(6))
    return (f"[{clave}]\n"
            f"referencia a: {fmt(salen) or 'ninguna'}\n"
            f"la referencian: {', '.join(f'{c} ({v})' for c, v in entran.most_common(6)) or 'ninguna'}")
