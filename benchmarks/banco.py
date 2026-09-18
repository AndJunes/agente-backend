"""Banco de tareas: ¿la version nueva es mejor HERRAMIENTA, no solo mejor metrica?

Ejecuta las mismas tareas con y sin las mejoras y compara las tres dimensiones:

    BUENO   propiedades verificadas / declaradas
    BARATO  coste y tokens
    BONITO  llamadas y latencia (lo que se espera mirando la pantalla)

Cuesta dinero de verdad: cada tarea es una ejecucion completa.

    python3 banco.py --brazo baseline     # sin plan ni routing
    python3 banco.py --brazo v1.1         # con ambos
    python3 banco.py --comparar
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import statistics
import sys
import tempfile
from pathlib import Path

import rapido
import traza

TAREAS = [
    ("reserva", "API de reservas para una clase con 1 sola plaza. Dos usuarios pueden reservar "
                "a la vez: nunca deben asignarse dos reservas a la misma plaza. Node.js."),
    ("cobro", "Endpoint POST /payments con orderId y amount, Idempotency-Key y sin doble cobro "
              "ante reintentos concurrentes. Node.js."),
    ("stock", "Reservar stock de un producto sin vender de mas cuando llegan pedidos "
              "simultaneos. Node.js."),
    ("rate_limit", "Rate limiter por usuario con token bucket, seguro ante peticiones "
                   "concurrentes. Node.js."),
    ("cola", "Consumidor de una cola que no aplique el mismo mensaje dos veces aunque se "
             "reentregue. Node.js."),
]


def correr(brazo, tareas=TAREAS):
    """Un brazo del experimento, sobre el pipeline de PRODUCCION.

    Antes corria rapido.implementar y armaba el brazo baseline monkeypatcheando
    rapido.cajas_del_plan. Eso media el camino viejo, que ya no es el que usa nadie.
    Ahora los dos brazos pasan por pipeline.ejecutar, que es lo que ejecuta el
    servidor: si el banco no mide el camino real, vuelve el bug que abrio la auditoria.

    baseline = sin acotar por cajas (el plan va con domains vacio)
    v2       = el pipeline completo, con el filtro de metadatos activo
    """
    import agent
    import pipeline
    import plan as P

    # Cada tarea en su propia carpeta. Sin esto las 10 ejecuciones escriben en salida/,
    # que es la carpeta de PRODUCCION: el banco se llevaria por delante la ultima entrega
    # del usuario y ademas dejaria solo la ultima de las diez. Ya paso una vez.
    destino = Path(tempfile.mkdtemp(prefix="banco_"))
    print(f"entregas del banco en {destino}", flush=True)

    for nombre, peticion in tareas:
        print(f"\n{'─' * 70}\n{brazo} · {nombre}\n{'─' * 70}", flush=True)
        agent.PRESUPUESTO.reiniciar()
        plan_ = P.deducir(peticion)
        if brazo == "baseline":
            plan_ = plan_._replace(domains=[], origen="baseline: sin acotar por cajas")
        # La etiqueta lleva prefijo: `traza.VERSION` vale "v1.1" y cualquier consulta
        # normal del usuario quedaba marcada igual que este brazo. Dos cosas distintas con
        # el mismo nombre en el mismo fichero acaban comparandose entre si.
        e = pipeline.ejecutar(peticion, plan_previo=plan_, version=f"banco:{brazo}",
                              carpeta=destino / f"{brazo}_{nombre}")
        estado = e.fila["estado"] if e.fila else "?"
        print(f"  {estado.upper()} · "
              f"{traza.linea(e.fila) if e.fila else 'sin traza'}", flush=True)


def _del_banco(fila, tareas=TAREAS):
    """¿Esta fila es de una tarea del banco, o de otra cosa?

    Hace falta porque `traza.VERSION` vale "v1.1", el mismo nombre que el brazo: cualquier
    consulta normal del usuario queda etiquetada `v1.1` y se colaba en el brazo. Comparar
    demos contra tareas del banco es medir una cosa y llamarla otra — el bug de siempre.
    Por eso el filtro es por la TAREA, que no se puede confundir, y no por la etiqueta.
    """
    return any(fila.get("tarea", "").startswith(p[:60]) for _n, p in tareas)


def comparar(tareas=TAREAS):
    filas = [f for f in traza.leer() + traza.leer(traza.ARCHIVO.parent / "trazas_noche.jsonl")
             if _del_banco(f, tareas) and f.get("coste_usd", 0) > 0
             and str(f.get("version", "")).startswith("banco:")]
    if filas:                     # solo la ultima corrida de cada brazo, no el historico
        ultima = {}
        for f in filas:
            ultima.setdefault(f["version"], []).append(f)
        filas = [f for fs in ultima.values() for f in fs[-len(tareas):]]
    brazos = {}
    for f in filas:
        brazos.setdefault(f["version"], []).append(f)
    if len(brazos) < 2:
        print("Hacen falta los dos brazos. Ejecuta --brazo baseline y --brazo v1.1 primero.")
        return

    def med(fs, campo):
        return statistics.median([f[campo] for f in fs])

    print(f"{'brazo':10} {'n':>3} {'exito':>7} {'verdes':>7} {'$/tarea':>9} "
          f"{'tokens':>9} {'ctx':>7} {'seg':>6} {'valor':>8}")
    for brazo, fs in sorted(brazos.items()):
        verdes = sum(1 for f in fs if f["estado"] == "verde")
        ctx = [f["tokens_contexto"] for f in fs if f.get("tokens_contexto")]
        print(f"{brazo:10} {len(fs):>3} {med(fs,'exito_verificado'):>7.2f} "
              f"{verdes}/{len(fs):<5} {med(fs,'coste_usd'):>9.4f} {med(fs,'tokens'):>9,.0f} "
              f"{statistics.median(ctx) if ctx else 0:>7,.0f} {med(fs,'segundos'):>6.0f} "
              f"{med(fs,'valor'):>8.2f}")

    a, b = sorted(brazos)
    print(f"\n{b} frente a {a}:")
    for campo, etiqueta, mejor_si_sube in [("exito_verificado", "éxito verificado (BUENO)", True),
                                           ("coste_usd", "coste por tarea (BARATO)", False),
                                           ("tokens_contexto", "contexto (BARATO)", False),
                                           ("segundos", "latencia (BONITO)", False)]:
        va = [f.get(campo) for f in brazos[a] if f.get(campo) is not None]
        vb = [f.get(campo) for f in brazos[b] if f.get(campo) is not None]
        if not va or not vb:
            continue
        ma, mb = statistics.median(va), statistics.median(vb)
        cambio = (mb - ma) / ma * 100 if ma else 0
        bien = (cambio > 0) == mejor_si_sube or abs(cambio) < 5
        print(f"  {'✅' if bien else '⚠️ '} {etiqueta:28} {ma:>9.4f} → {mb:<9.4f} ({cambio:+.0f}%)")

    print("\nRegla del plan: una mejora solo cuenta si no degrada seriamente las otras\n"
          "dimensiones. Si el éxito verificado baja, no compensa ahorrar coste.")


if __name__ == "__main__":
    if "--comparar" in sys.argv:
        comparar()
    elif "--brazo" in sys.argv:
        brazo = sys.argv[sys.argv.index("--brazo") + 1]
        n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else len(TAREAS)
        print(f"{n} tareas · brazo {brazo} · esto CUESTA DINERO (~$0.10 por tarea)")
        correr(brazo, TAREAS[:n])
        print(f"\nHecho. Compara con: python3 banco.py --comparar")
    else:
        print(__doc__)
