"""¿Cuántas veces de diez el modelo produce un proyecto que pasa sus propios tests?

    python3 banco_proyectos.py 10        # con modelo real, si MIRAG_OFFLINE=0
    python3 banco_proyectos.py 3 --seco  # con el guion, para probar el medidor

Cada corrida es independiente y se anota entera: estado, dónde se rompió, cuántos
marcadores, cuántas reparaciones, coste y tiempo. El conteo solo dice cuántas; lo que
sirve para arreglar algo es POR QUE fallaron las otras.
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
from collections import Counter
from pathlib import Path

import agent
import demos

# Este dato no lo lee produccion: vive junto al banco que lo produce.
DESTINO = Path(__file__).resolve().parent / "proyectos.json"


def una(indice, offline):
    # El tope es POR CORRIDA, como en el servidor. `agent.PRESUPUESTO` acumula dentro del
    # proceso, asi que sin esto un banco de diez se queda sin presupuesto a la septima y
    # las tres ultimas salen como EXCEPCION — que fue exactamente lo que paso la primera
    # vez, y contamino la medicion con cuatro corridas que nunca ocurrieron.
    agent.PRESUPUESTO.reiniciar()
    a_coste = agent.PRESUPUESTO.coste
    t0 = time.time()
    fila = {"n": indice, "estado": None, "error": None}
    try:
        e, informe = demos.correr("proyecto", offline=offline)
        cert, proy, art = e.certificado, e.proyecto, e.artefacto
        marcas = dict(cert.marcas) if cert else {}
        # la primera fase que no salio bien: eso es lo que hay que arreglar
        rota = next((f.nombre for f in (cert.fases if cert else ()) if f.estado == "fallo"),
                    None)
        muda = next((f.nombre for f in (cert.fases if cert else ()) if f.estado == "limitado"),
                    None)
        fila.update({
            "estado": cert.estado if cert else "SIN CERTIFICADO",
            "por_que": (cert.por_que if cert else "")[:160],
            "primera_fase_rota": rota, "primera_fase_muda": muda,
            "archivos": proy.totales["archivos"] if proy else 0,
            "lineas": proy.totales["lineas"] if proy else 0,
            "marcas_pasan": sum(1 for v in marcas.values() if v == "PASS"),
            "marcas_total": len(marcas),
            "crud_pasan": sum(1 for k, v in marcas.items()
                              if k.startswith("crud_") and v == "PASS"),
            "reparaciones": len(cert.reparaciones) if cert else 0,
            "integridad": bool(art and art.paquete and art.paquete.ok),
            "zip_bytes": art.paquete.bytes if (art and art.paquete) else 0,
            "descargable": bool(art and art.descargable),
            "cumple_contrato": informe["cumple"],
            "fases": [(f.nombre, f.estado) for f in (cert.fases if cert else ())],
        })
    except Exception as error:                 # una corrida que revienta ES un resultado
        fila["estado"] = "EXCEPCION"
        fila["error"] = f"{type(error).__name__}: {error}"[:200]
    fila["segundos"] = round(time.time() - t0, 1)
    fila["coste"] = round(agent.PRESUPUESTO.coste - a_coste, 4)
    fila["llamadas"] = agent.PRESUPUESTO.llamadas
    return fila


def main(argv):
    veces = int(next((a for a in argv if a.isdigit()), 10))
    offline = "--seco" in argv or agent.OFFLINE
    print(f"{veces} corridas · {'guion' if offline else 'MODELO REAL'}\n")
    filas = []
    for i in range(1, veces + 1):
        fila = una(i, offline)
        filas.append(fila)
        print(f"  {i:>2}/{veces}  {fila['estado']:<12} "
              f"{fila.get('marcas_pasan', 0):>2}/{fila.get('marcas_total', 0):<2} marcas · "
              f"{fila.get('archivos', 0):>2} arch · rep={fila.get('reparaciones', 0)} · "
              f"${fila['coste']:.4f} · {fila['segundos']:>5.0f}s"
              + (f"  [{fila.get('primera_fase_rota') or fila.get('error') or ''}]"
                 if fila['estado'] != "VERIFICADO" else ""), flush=True)

    verificadas = sum(1 for f in filas if f["estado"] == "VERIFICADO")
    print(f"\n{'─' * 70}")
    print(f"  VERIFICADO: {verificadas}/{veces}")
    print(f"  estados: {dict(Counter(f['estado'] for f in filas))}")
    rotas = Counter(f.get("primera_fase_rota") for f in filas if f.get("primera_fase_rota"))
    if rotas:
        print(f"  primera fase que rompe: {dict(rotas)}")
    costes = [f["coste"] for f in filas]
    print(f"  coste: ${sum(costes):.4f} total · ${statistics.mean(costes):.4f} de media")
    print(f"  tiempo: {sum(f['segundos'] for f in filas):.0f}s total · "
          f"{statistics.median([f['segundos'] for f in filas]):.0f}s mediana")
    con_zip = sum(1 for f in filas if f.get("integridad"))
    print(f"  integridad del ZIP: {con_zip}/{veces}")

    DESTINO.parent.mkdir(exist_ok=True)
    DESTINO.write_text(json.dumps({"corridas": filas, "offline": offline,
                                   "cuando": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                  ensure_ascii=False, indent=1))
    print(f"\n  escrito en {DESTINO.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
