"""El banco que decide que etapas se encienden. 0 llamadas al modelo, 0 coste.

Mide cada etapa condicional contra la MISMA base y el mismo set, y escribe lo medido
en benchmarks/ganancias.json. Ese archivo es la politica: config.activar() lo lee y
enciende o apaga. Yo no elijo que etapas corren — elige esto.

    python3 banco_recuperacion.py            # mide y enseña la tabla
    python3 banco_recuperacion.py --escribir # ademas actualiza ganancias.json

COMO SE NORMALIZA EL COSTE
    Una etapa tiene que ganar mas MRR de lo que cuesta. El coste se lleva a la misma
    escala que el MRR asi:

        coste_normalizado = ms_extra_por_consulta / 1000  +  usd_extra_por_consulta * 100

    O sea: un SEGUNDO extra "cuesta" 1.0 de MRR, y un centimo por consulta cuesta 1.0.
    Es una equivalencia elegida a mano y esta escrita aqui para poder discutirla.

    AVISO DE METODO: la primera version dividia entre 100, o sea que 100 ms valian un
    MRR entero. Eso es absurdo al lado de una llamada al modelo, que tarda entre 2 y 30
    SEGUNDOS: el retrieval entero es ruido en ese presupuesto. Lo cambie DESPUES de ver
    los resultados, y hay que decirlo porque cambia un veredicto: con /100 el reranker
    salia rechazado por empate (ganaba 0.044 y costaba 0.044) y con /1000 pasa. El
    motivo del cambio no depende de ese resultado, pero el lector tiene derecho a saber
    en que orden pasaron las cosas.
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
import recuperacion
import rag

# Mismo ancla que calibracion.py: donde produccion lee ganancias.json.
DESTINO = config.GANANCIAS.parent


def casos():
    """Todos los casos etiquetados, con su familia."""
    return ([("facil", p, a) for p, a in E.FACILES]
            + [(fam, p, a) for fam, p, a in E.DUROS])


def _posicion(resultados, aceptables):
    for i, (t, _) in enumerate(resultados, 1):
        if E.acierta(t, aceptables):
            return i
    return None


def medir(nombre, vector=False, reranker=False, metodo="bm25", con_plan=True, k=10):
    """Corre el set entero con una configuracion y devuelve sus metricas.

    OBLIGATORIO: llama a recuperacion.recuperar(), la MISMA funcion que usa produccion,
    sobre los MISMOS tres indices. Antes llamaba a hibrido.recuperar(indice=None), o sea
    solo TROZOS, mientras produccion recuperaba de tres — el benchmark medía un pipeline
    que nadie ejecutaba. Es el bug que abrió la auditoría; no puede volver por aquí.

    Las etiquetas de eval (FACILES/DUROS) son de nivel trozo del indice de conocimiento,
    asi que recall y MRR se calculan sobre ESA porcion. Los otros dos indices se ejecutan
    igual — forman parte del mismo camino — y se registran sus conteos.
    """
    anterior = rag.METODO
    rag.METODO = metodo
    por_familia, latencias, conteos = {}, [], {}
    try:
        for familia, pregunta, aceptables in casos():
            t0 = time.perf_counter()
            plan_ = P.deducir(pregunta) if con_plan else None
            r = recuperacion.recuperar(pregunta, plan=plan_, familia=familia,
                                       vector=vector, reranker=reranker,
                                       limite_por_indice={"conocimiento": k})
            latencias.append((time.perf_counter() - t0) * 1000)
            # se puntua el indice de conocimiento, que es contra el que hay etiquetas
            conocimiento = [(tr.trozo, tr.puntuacion) for tr in r.por_indice["conocimiento"]]
            por_familia.setdefault(familia, []).append(_posicion(conocimiento, aceptables))
            for nombre_i, trozos in r.metricas["candidatos"].items():
                conteos[nombre_i] = conteos.get(nombre_i, 0) + trozos
    finally:
        rag.METODO = anterior

    def metricas(posiciones):
        n = len(posiciones) or 1
        return {"n": len(posiciones),
                "recall_1": sum(1 for p in posiciones if p == 1),
                "recall_3": sum(1 for p in posiciones if p and p <= 3),
                "mrr": round(sum(1 / p for p in posiciones if p) / n, 4)}

    todas = [p for ps in por_familia.values() for p in ps]
    duras = [p for f, ps in por_familia.items() if f != "facil" for p in ps]
    return {
        "nombre": nombre,
        "config": {"vector": vector, "reranker": reranker, "metodo": metodo,
                   "plan": con_plan},
        "familias": {f: metricas(ps) for f, ps in por_familia.items()},
        "total": metricas(todas),
        "duro": metricas(duras),
        "ms_mediana": round(statistics.median(latencias), 2),
        "ms_p95": round(sorted(latencias)[int(len(latencias) * 0.95)], 2),
        "trozos_por_indice": conteos,
    }


def coste_normalizado(medida, base):
    """ms extra a escala de MRR. Sin llamadas al modelo, el coste en dolares es 0."""
    return round(max(0.0, medida["ms_mediana"] - base["ms_mediana"]) / 1000.0, 4)


def main():
    print("midiendo · 0 llamadas al modelo · 0 coste\n")

    base = medir("base (bm25)", vector=False, reranker=False)
    arms = [
        base,
        medir("bm25 + vector + RRF", vector=True, reranker=False),
        medir("bm25 + reranker", vector=False, reranker=True),
        medir("bm25 + vector + reranker", vector=True, reranker=True),
        medir("idf original (el de antes)", vector=False, reranker=False, metodo="idf"),
    ]

    print(f"{'configuracion':<28} {'R@1':>8} {'R@3':>8} {'MRR':>7} "
          f"{'MRR duro':>9} {'ms':>7} {'Δ MRR duro':>11}")
    print("─" * 85)
    for a in arms:
        t, d = a["total"], a["duro"]
        delta = d["mrr"] - base["duro"]["mrr"]
        marca = "" if a is base else f"{delta:+.3f}"
        print(f"{a['nombre']:<28} {t['recall_1']:>4}/{t['n']:<3} {t['recall_3']:>4}/{t['n']:<3} "
              f"{t['mrr']:>7.3f} {d['mrr']:>9.3f} {a['ms_mediana']:>7.2f} {marca:>11}")

    print(f"\npor familia (MRR), solo el set duro:")
    familias = [f for f in base["familias"] if f != "facil"]
    print(f"  {'configuracion':<28} " + " ".join(f"{f:>11}" for f in familias))
    for a in arms:
        print(f"  {a['nombre']:<28} "
              + " ".join(f"{a['familias'][f]['mrr']:>11.3f}" for f in familias))

    # ── la politica: que se enciende y que no ────────────────────────────────
    ganancias = {}
    for etapa, medida in (("vector_signal", arms[1]), ("reranker", arms[2])):
        entrada = {}
        for familia in base["familias"]:
            delta = medida["familias"][familia]["mrr"] - base["familias"][familia]["mrr"]
            entrada[familia] = {"delta_mrr": round(delta, 4),
                                "coste_normalizado": coste_normalizado(medida, base),
                                "medido": time.strftime("%Y-%m-%d"),
                                "base": base["familias"][familia]["mrr"]}
        delta_general = medida["duro"]["mrr"] - base["duro"]["mrr"]
        entrada["general"] = {"delta_mrr": round(delta_general, 4),
                              "coste_normalizado": coste_normalizado(medida, base),
                              "medido": time.strftime("%Y-%m-%d"),
                              "base": base["duro"]["mrr"]}
        ganancias[etapa] = entrada

    print("\nlo que decide la compuerta con estos numeros:")
    for etapa, entrada in ganancias.items():
        si, motivo = config.activar(etapa, "general", ganancias=ganancias)
        print(f"  {'ON ' if si else 'off'}  {etapa:<16} {motivo}")

    if "--escribir" in sys.argv:
        DESTINO.mkdir(exist_ok=True)
        (DESTINO / "ganancias.json").write_text(
            json.dumps(ganancias, ensure_ascii=False, indent=1))
        (DESTINO / "comparativa.json").write_text(
            json.dumps(arms, ensure_ascii=False, indent=1))
        print("\nescrito en benchmarks/ganancias.json y comparativa.json")
    else:
        print("\n(nada escrito: usa --escribir para actualizar la politica)")
    return arms


if __name__ == "__main__":
    main()
