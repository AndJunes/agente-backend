"""Fase 3: decidir con evidencia qué señales de retrieval merecen quedar encendidas.

Todo se mide sobre `recuperacion.recuperar()`, que es la MISMA función que usa
producción. Ninguna cifra de aquí viene de una implementación paralela — ese fue
exactamente el bug que abrió la auditoría.

    python3 calibracion.py            # mide y enseña
    python3 calibracion.py --escribir # ademas actualiza benchmarks/ganancias.json

0 llamadas al modelo. 0 coste.
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import json
import statistics
import sys
import time
from pathlib import Path

import config
import eval as E
import plan as P
import rag
import recuperacion

# ganancias.json lo LEE produccion (config.activar). Anclar el que escribe al que lee
# es lo unico que garantiza que no se separen: si config cambia, esto cambia con el.
DESTINO = config.GANANCIAS.parent
PROFUNDIDAD = 10


def casos():
    return ([("facil", p, a) for p, a in E.FACILES]
            + [(fam, p, a) for fam, p, a in E.DUROS])


def _posicion(trozos, aceptables):
    for i, tr in enumerate(trozos, 1):
        if E.acierta(tr.trozo, aceptables):
            return i
    return None


def _metricas(posiciones):
    n = len(posiciones) or 1
    return {"n": len(posiciones),
            "recall_1": sum(1 for p in posiciones if p == 1),
            "recall_3": sum(1 for p in posiciones if p and p <= 3),
            "mrr": round(sum(1 / p for p in posiciones if p) / n, 4)}


def medir(nombre, vector=False, reranker=False):
    """Un brazo. Mismo set, mismas queries, misma función que producción."""
    por_familia, latencias, ctx, candidatos = {}, [], [], {}
    ids_por_query = {}
    for familia, pregunta, aceptables in casos():
        t0 = time.perf_counter()
        plan_ = P.deducir(pregunta)
        r = recuperacion.recuperar(pregunta, plan=plan_, familia=familia,
                                   vector=vector, reranker=reranker,
                                   limite_por_indice={"conocimiento": PROFUNDIDAD})
        latencias.append((time.perf_counter() - t0) * 1000)
        por_familia.setdefault(familia, []).append(
            _posicion(r.por_indice["conocimiento"], aceptables))
        _, medidas = recuperacion.construir_contexto(r, peticion=pregunta)
        ctx.append(medidas["chars"])
        for k, v in r.metricas["candidatos"].items():
            candidatos[k] = candidatos.get(k, 0) + v
        ids_por_query[pregunta] = r.ids()

    todas = [p for ps in por_familia.values() for p in ps]
    duras = [p for f, ps in por_familia.items() if f != "facil" for p in ps]
    return {"nombre": nombre, "config": {"vector": vector, "reranker": reranker},
            "familias": {f: _metricas(ps) for f, ps in por_familia.items()},
            "total": _metricas(todas), "duro": _metricas(duras),
            "ms_mediana": round(statistics.median(latencias), 2),
            "ms_p95": round(sorted(latencias)[int(len(latencias) * .95)], 2),
            "contexto_mediana": int(statistics.median(ctx)),
            "candidatos": candidatos, "_ids": ids_por_query}


def aporte_de_los_indices():
    """Cuánto aporta cada índice: candidatos únicos y cuántos llegan al contexto."""
    unicos, solapes, en_contexto = {}, 0, 0
    total = 0
    for _familia, pregunta, _a in casos():
        r = recuperacion.recuperar(pregunta, plan=P.deducir(pregunta))
        claves = {}
        for tr in r.seleccionados:
            k = (tr.trozo.caja, tr.trozo.titulo)
            claves.setdefault(k, []).append(tr.indice)
            unicos[tr.indice] = unicos.get(tr.indice, set())
            unicos[tr.indice].add(k)
        solapes += sum(1 for v in claves.values() if len(v) > 1)
        total += len(r.seleccionados)
        _, m = recuperacion.construir_contexto(r, peticion=pregunta)
        en_contexto += m["incluidos"]
    return {"trozos_distintos_por_indice": {k: len(v) for k, v in unicos.items()},
            "recuperados_totales": total, "solapes": solapes,
            "llegan_al_contexto": en_contexto,
            "porcentaje_descartado_por_dedup": round(100 * (total - en_contexto) / total, 1)}


def rrf_sin_segunda_señal():
    """¿RRF hace algo con una sola señal? Debería ser un passthrough."""
    q = "como evito un race condition al reservar una plaza"
    r = recuperacion.recuperar(q, plan=P.deducir(q), vector=False)
    etapas = {e.nombre: e for e in r.etapas}
    detalle = etapas["rrf:conocimiento"].detalle
    bm25 = etapas["bm25:conocimiento"].candidatos
    rrf = etapas["rrf:conocimiento"].candidatos
    return {"detalle": detalle, "candidatos_bm25": bm25, "candidatos_rrf": rrf,
            "es_passthrough": bm25 == rrf and "solo bm25" in detalle}


def solape_vector_bm25():
    """¿El vector trae candidatos que BM25 no trae, o repite los mismos?"""
    nuevos, compartidos, consultas = 0, 0, 0
    for _f, pregunta, _a in casos()[:20]:
        plan_ = P.deducir(pregunta)
        solo_bm25 = recuperacion.recuperar(pregunta, plan=plan_, vector=False)
        con_vector = recuperacion.recuperar(pregunta, plan=plan_, vector=True)
        a = {t.id for t in solo_bm25.seleccionados}
        b = {t.id for t in con_vector.seleccionados}
        nuevos += len(b - a)
        compartidos += len(a & b)
        consultas += 1
    return {"consultas": consultas, "candidatos_nuevos_del_vector": nuevos,
            "compartidos": compartidos,
            "porcentaje_nuevo": round(100 * nuevos / max(nuevos + compartidos, 1), 1)}


def coste_normalizado(medida, base):
    """ms extra a escala de MRR: un segundo de latencia = 1.0 de MRR."""
    return round(max(0.0, medida["ms_mediana"] - base["ms_mediana"]) / 1000.0, 4)


def main():
    print("calibrando sobre el pipeline REAL · 0 llamadas al modelo · 0 coste\n")
    base = medir("baseline · BM25 + 3 indices")
    brazos = [base,
              medir("+ reranker", reranker=True),
              medir("+ vector", vector=True),
              medir("+ vector + reranker", vector=True, reranker=True)]

    print(f"{'brazo':<30} {'R@1':>8} {'R@3':>8} {'MRR':>7} {'MRRduro':>8} "
          f"{'ms':>7} {'ctx':>7} {'ΔMRRduro':>9}")
    print("─" * 92)
    for a in brazos:
        t, d = a["total"], a["duro"]
        delta = d["mrr"] - base["duro"]["mrr"]
        print(f"{a['nombre']:<30} {t['recall_1']:>4}/{t['n']:<3} {t['recall_3']:>4}/{t['n']:<3} "
              f"{t['mrr']:>7.3f} {d['mrr']:>8.3f} {a['ms_mediana']:>7.2f} "
              f"{a['contexto_mediana']:>7,} {'' if a is base else f'{delta:+.3f}':>9}")

    print("\npor familia (MRR del set duro):")
    fams = [f for f in base["familias"] if f != "facil"]
    print(f"  {'brazo':<30} " + " ".join(f"{f:>11}" for f in fams))
    for a in brazos:
        print(f"  {a['nombre']:<30} " + " ".join(f"{a['familias'][f]['mrr']:>11.3f}" for f in fams))

    indices = aporte_de_los_indices()
    print(f"\naporte de los tres indices (49 consultas):")
    for k, v in indices["trozos_distintos_por_indice"].items():
        print(f"  {k:<14} {v} trozos distintos")
    print(f"  {indices['recuperados_totales']} recuperados → {indices['llegan_al_contexto']} "
          f"al contexto ({indices['porcentaje_descartado_por_dedup']}% se descarta por duplicado)")

    rrf = rrf_sin_segunda_señal()
    print(f"\nRRF con una sola señal: {rrf['candidatos_bm25']} → {rrf['candidatos_rrf']} "
          f"candidatos · passthrough = {rrf['es_passthrough']}")

    vec = solape_vector_bm25()
    print(f"vector vs BM25 (20 consultas): {vec['candidatos_nuevos_del_vector']} candidatos nuevos, "
          f"{vec['compartidos']} compartidos ({vec['porcentaje_nuevo']}% nuevo)")

    # ── la politica ─────────────────────────────────────────────────────────
    ganancias = {}
    for etapa, medida in (("reranker", brazos[1]), ("vector_signal", brazos[2])):
        entrada = {}
        for familia in base["familias"]:
            d = medida["familias"][familia]["mrr"] - base["familias"][familia]["mrr"]
            entrada[familia] = {"delta_mrr": round(d, 4),
                                "coste_normalizado": coste_normalizado(medida, base),
                                "medido": time.strftime("%Y-%m-%d"),
                                "sobre": "pipeline real (fase 3)",
                                "base": base["familias"][familia]["mrr"]}
        entrada["general"] = {"delta_mrr": round(medida["duro"]["mrr"] - base["duro"]["mrr"], 4),
                              "coste_normalizado": coste_normalizado(medida, base),
                              "medido": time.strftime("%Y-%m-%d"),
                              "sobre": "pipeline real (fase 3)",
                              "base": base["duro"]["mrr"]}
        ganancias[etapa] = entrada

    print("\nlo que decide la compuerta con estos numeros:")
    for etapa in ganancias:
        for familia in ("general", "parafrasis", "mixto", "erratas", "multisalto"):
            si, motivo = config.activar(etapa, familia, ganancias=ganancias)
            print(f"  {'ON ' if si else 'off'} {etapa:<14} {familia:<12} {motivo}")

    if "--escribir" in sys.argv:
        DESTINO.mkdir(exist_ok=True)
        (DESTINO / "ganancias.json").write_text(json.dumps(ganancias, ensure_ascii=False, indent=1))
        limpio = [{k: v for k, v in a.items() if not k.startswith("_")} for a in brazos]
        (DESTINO / "calibracion_fase3.json").write_text(json.dumps(
            {"brazos": limpio, "indices": indices, "rrf": rrf, "vector": vec},
            ensure_ascii=False, indent=1))
        print("\nescrito en benchmarks/ganancias.json y calibracion_fase3.json")
    else:
        print("\n(nada escrito: --escribir para actualizar la politica)")
    return brazos


if __name__ == "__main__":
    main()
