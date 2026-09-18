"""Recuperacion hibrida: BM25 + señal vectorial, fusionadas con RRF, y rerank opcional.

    filtro de metadatos
        ↓
    BM25  ───┐
             ├── RRF ──→ top N ──→ reranker? ──→ top K
    vector ──┘

POR QUE RRF Y NO SUMAR PUNTUACIONES
    BM25 devuelve puntuaciones sin escala (0..30) y el coseno va de 0 a 1. Sumarlos
    exige normalizar, y cualquier normalizacion inventa una equivalencia entre dos
    cosas que no la tienen. RRF solo mira el PUESTO, asi que no hay que calibrar nada.

QUE NO SE EJECUTA SIEMPRE
    El vector y el reranker pasan por config.activar(): si nadie ha medido que
    aporten, no se ejecutan. El BM25 si es el suelo, siempre corre.

Todas las etapas anotan cuantos candidatos produjeron y cuanto tardaron: sin eso no
se puede contestar "¿por que Mirag recupero esto?" ni "¿donde se va el tiempo?".
"""

import re
import time
from typing import NamedTuple

import config
import metadatos as M
import rag

RRF_K = 60           # constante clasica: amortigua los primeros puestos
CANDIDATOS_N = 20    # lo que entra al reranker. Nunca el corpus entero.


class Etapa(NamedTuple):
    nombre: str
    candidatos: int
    ms: float
    detalle: str = ""
    usada: bool = True


class Resultado(NamedTuple):
    trozos: list          # [(Trozo, puntuacion_final)]
    etapas: list          # [Etapa] — para la traza y para la UI
    fallbacks: list       # [(etapa, motivo)]

    @property
    def ms(self):
        return round(sum(e.ms for e in self.etapas), 2)

    def resumen(self):
        return " → ".join(f"{e.nombre}:{e.candidatos}" for e in self.etapas if e.usada)


def _rrf(listas, k=RRF_K):
    """Reciprocal Rank Fusion: cada lista vota por el PUESTO, no por la puntuacion."""
    puntos, vistos = {}, {}
    for lista in listas:
        for puesto, trozo in enumerate(lista, 1):
            clave = (trozo.caja, trozo.titulo)
            puntos[clave] = puntos.get(clave, 0.0) + 1.0 / (k + puesto)
            vistos[clave] = trozo
    orden = sorted(puntos.items(), key=lambda x: x[1], reverse=True)
    return [(vistos[c], p) for c, p in orden]


# ── reranker heuristico local ────────────────────────────────────────────────
# No es un cross-encoder. Es una heuristica explicita y barata: cuantos terminos de
# la consulta aparecen, si aparecen juntos, y si el trozo tiene ficha. Se llama
# heuristico en todos los sitios a proposito.

def _rerank_local(consulta, candidatos, k):
    terminos = [t for t in dict.fromkeys(rag._normalizar(consulta).split()) if len(t) >= 3]
    if not terminos:
        return candidatos[:k]

    def puntuar(par):
        trozo, base = par
        norm = trozo.norm
        presentes = [t for t in terminos if t in norm]
        cobertura = len(presentes) / len(terminos)

        # proximidad: si dos terminos salen a menos de 120 caracteres, el trozo habla
        # del tema y no los menciona de pasada en dos sitios distintos
        posiciones = sorted(norm.find(t) for t in presentes if norm.find(t) >= 0)
        juntos = any(b - a < 120 for a, b in zip(posiciones, posiciones[1:]))

        titulo = rag._normalizar(trozo.titulo)
        en_titulo = sum(1 for t in terminos if t in titulo) / len(terminos)
        tiene_ficha = "ficha" in M.de(trozo).artifact_types

        return (cobertura * 3.0 + en_titulo * 2.0
                + (0.5 if juntos else 0.0) + (0.2 if tiene_ficha else 0.0)
                + base * 0.1)                 # el puesto previo sigue contando un poco

    return sorted(candidatos, key=puntuar, reverse=True)[:k]


# Indexar 247 trozos cuesta ~170 ms; hacerlo en CADA consulta convertia una señal de
# 0.6 ms en una de 160 ms y la compuerta la habria rechazado por un coste que era mio,
# no suyo. El indice se construye una vez por conjunto de trozos.
_TIENDAS = {}


def _tienda_para(trozos):
    import vectores
    clave = (len(trozos), hash(tuple((t.caja, t.titulo) for t in trozos)))
    if clave not in _TIENDAS:
        tienda = vectores.obtener()
        tienda.indexar([t.texto for t in trozos])
        _TIENDAS[clave] = tienda
    return _TIENDAS[clave]


def recuperar(consulta, indice=None, plan=None, k=5, familia="general",
              vector=None, reranker=None):
    """El pipeline de recuperacion. Devuelve Resultado con todo lo que paso.

    vector/reranker: None = decide config.activar(); True/False = forzar (para medir).
    """
    indice = rag.TROZOS if indice is None else indice
    etapas, fallbacks = [], []

    # ── 1. filtro de metadatos ──────────────────────────────────────────────
    t0 = time.perf_counter()
    if config.activar("metadata_routing")[0] and (plan is not None):
        filtrado, hubo_fallback, motivo = M.filtrar(indice, plan=plan)
        if hubo_fallback:
            fallbacks.append(("metadata_routing", motivo))
    else:
        filtrado, motivo = list(indice), "sin plan: no se acota"
    etapas.append(Etapa("filtro", len(filtrado), (time.perf_counter() - t0) * 1000, motivo))

    # ── 2. BM25: el suelo, siempre ──────────────────────────────────────────
    t0 = time.perf_counter()
    # HYBRID_RETRIEVAL apagado = sin ranking: se devuelve el orden del corpus. Es el
    # suelo absoluto contra el que se mide si BM25 aporta algo.
    if config.activar("hybrid_retrieval")[0]:
        bm25 = rag._ranking(filtrado, consulta, CANDIDATOS_N)
    else:
        bm25 = [(tr, 0.0) for tr in filtrado[:CANDIDATOS_N]]
    etapas.append(Etapa("bm25", len(bm25), (time.perf_counter() - t0) * 1000,
                        f"metodo {rag.METODO}"))

    # ── 3. señal vectorial, si esta medida ──────────────────────────────────
    usar_vector = config.activar("vector_signal", familia)[0] if vector is None else vector
    vec = []
    if usar_vector:
        t0 = time.perf_counter()
        try:
            tienda = _tienda_para(filtrado)
            vec = [(filtrado[i], s) for i, s in tienda.buscar(consulta, CANDIDATOS_N)]
            detalle = f"backend {tienda.nombre}"
            if getattr(tienda, "fallback", None):
                fallbacks.append(("vector", tienda.fallback))
                detalle += f" (fallback: {tienda.fallback})"
        except Exception as e:                  # una señal opcional no tumba la busqueda
            fallbacks.append(("vector", f"{type(e).__name__}: {e}"))
            detalle = f"fallo, se sigue con BM25: {type(e).__name__}"
        etapas.append(Etapa("vector", len(vec), (time.perf_counter() - t0) * 1000, detalle))
    else:
        etapas.append(Etapa("vector", 0, 0.0,
                            config.activar("vector_signal", familia)[1], usada=False))

    # ── 4. fusion ───────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    if vec:
        fusionados = _rrf([[t for t, _ in bm25], [t for t, _ in vec]])
        detalle = f"RRF de bm25({len(bm25)}) + vector({len(vec)})"
    else:
        fusionados = bm25
        detalle = "solo bm25: no hay segunda señal que fusionar"
    etapas.append(Etapa("rrf", len(fusionados), (time.perf_counter() - t0) * 1000, detalle))

    # ── 5. reranker, si esta medido ─────────────────────────────────────────
    usar_rerank = config.activar("reranker", familia)[0] if reranker is None else reranker
    if usar_rerank and fusionados:
        t0 = time.perf_counter()
        try:
            finales = _rerank_local(consulta, fusionados[:CANDIDATOS_N], k)
            detalle = f"heuristico local sobre {min(len(fusionados), CANDIDATOS_N)} candidatos"
        except Exception as e:
            finales, detalle = fusionados[:k], f"fallo, se deja el orden de RRF: {type(e).__name__}"
            fallbacks.append(("reranker", str(e)))
        etapas.append(Etapa("reranker", len(finales), (time.perf_counter() - t0) * 1000, detalle))
    else:
        finales = fusionados[:k]
        etapas.append(Etapa("reranker", 0, 0.0,
                            config.activar("reranker", familia)[1], usada=False))

    return Resultado(finales[:k], etapas, fallbacks)


if __name__ == "__main__":
    for q in ("que es un indice de postgresql",
              "como evito que dos usuarios reserven la misma plaza a la vez"):
        r = recuperar(q)
        print(f"\n{q}\n  {r.resumen()}  ·  {r.ms} ms")
        for t, p in r.trozos[:3]:
            print(f"    {p:6.2f}  {t.caja.split('·')[0].strip()} · {t.titulo[:50]}")
        for etapa in r.etapas:
            if not etapa.usada:
                print(f"    (omitida: {etapa.nombre} — {etapa.detalle})")
