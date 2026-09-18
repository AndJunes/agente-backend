"""Una linea por ejecucion en trazas.jsonl, para poder comparar versiones.

No mide nada nuevo: junta lo que ya se cuenta por separado — el coste real de
`agent.PRESUPUESTO` y las propiedades de `rapido._evidencia` — y lo deja en
disco con la version, para responder a "¿el cambio de ayer mejoro algo?".
"""

import json
import time
from pathlib import Path

import agent

ARCHIVO = Path(__file__).parent / "trazas.jsonl"
VERSION = "v1.1"


ESTADOS = ("verificado", "verificado en simulación", "refutado", "sin verificar")


def resumen(evidencia):
    """Cuenta por estado, mas DOS fracciones que no hay que confundir.

    'verificado en simulación' era una cuarta clave sorpresa que se caia del numerador:
    una tarea con 10 propiedades demostradas contra una simulacion daba exito 0.0,
    exactamente igual que una tarea donde no se demostro nada. Son cosas distintas.

    Asi que se mantienen separadas: exito_verificado sigue contando SOLO lo demostrado
    de verdad (no se infla), y la simulacion se reporta aparte en vez de desaparecer.
    """
    cuenta = {e: 0 for e in ESTADOS}
    for e in evidencia or []:
        estado = e.get("estado") or "sin verificar"
        cuenta[estado] = cuenta.get(estado, 0) + 1
    total = sum(cuenta.values())
    if not total:
        return cuenta, 0.0, 0.0
    return (cuenta,
            cuenta["verificado"] / total,
            cuenta["verificado en simulación"] / total)


def escribir(tarea, modo, resultado, segundos, version=VERSION, archivo=ARCHIVO):
    cuenta, exito, en_simulacion = resumen(resultado.get("evidencia"))
    p = agent.PRESUPUESTO
    # Lo que costo ESTA ejecucion, no lo que lleva gastado el proceso. `PRESUPUESTO`
    # acumula, y el servidor lo reinicia por peticion — pero un script que ejecuta varias
    # seguidas no, asi que cada fila anotaba el total corrido: 0.153, 0.309, 0.465...
    # Sumar esa columna cuenta la primera corrida seis veces. Lo destapo un banco de diez.
    antes = resultado.get("presupuesto_antes") or {}
    coste = p.coste - antes.get("coste", 0.0)
    llamadas = p.llamadas - antes.get("llamadas", 0)
    tokens = (p.entrada + p.salida) - antes.get("tokens", 0)
    fila = {
        "cuando": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "version": version,
        "tarea": tarea[:120],
        "modo": modo,
        "estado": resultado.get("estado"),
        "llamadas": llamadas,
        # Sin esto, una noche entera de dobles se lee como 65 llamadas al modelo por
        # $0.00, que parece un error de contabilidad en vez de lo que es: simulacion.
        "decision_simulada": bool(resultado.get("simulado")),
        "tokens": tokens,
        "coste_usd": round(coste, 5),
        "segundos": round(segundos, 1),
        "tokens_contexto": resultado.get("tokens_contexto"),
        "cajas": resultado.get("cajas") or [],
        "arreglado": bool(resultado.get("arreglado")),
        "propiedades": cuenta,
        # El conteo solo no deja auditar nada: para saber POR QUE una propiedad quedo sin
        # verificar hace falta el texto que declaro el modelo y el test_id que prometio. Sin
        # esto, reconstruir una corrida real obligaba a rebuscar en carpetas temporales.
        "propiedades_detalle": [
            {"riesgo": (e.get("riesgo") or "")[:200],
             "propiedad": (e.get("propiedad") or "")[:200],
             "test_id": e.get("test_id"), "estado": e.get("estado")}
            for e in (resultado.get("evidencia") or [])[:20]],
        # igual con los anti-patrones: el resumen dice "6 no cubierta" y no cual ni por que
        "antipatrones_detalle": [
            {"obligacion": f.get("obligacion"), "estado": f.get("estado"),
             "por_que": f.get("por_que")}
            for f in (resultado.get("cobertura_antipatrones") or [])[:20]],
        # ── observabilidad: por que Mirag eligio ESTE contexto ───────────────
        # Antes esto solo existia en memoria y se emitia por SSE; una traza vieja no
        # podia contestar "¿por que recupero esto?". Lo que no se persiste, no ocurrio.
        "plan": resultado.get("plan"),
        "filtros": resultado.get("filtros"),
        "retrieval": resultado.get("retrieval"),
        "contexto": resultado.get("contexto"),
        "verificacion": resultado.get("verificacion"),
        "antipatrones": resultado.get("antipatrones"),
        "repair_attempts": resultado.get("repair_attempts", 0),
        "final_status": resultado.get("final_status"),
        "fallbacks": resultado.get("fallbacks") or [],
        "errores": resultado.get("errores") or [],
        # Un proyecto entero no cabe en la traza, pero lo que lo identifica si: cuantos
        # archivos, que estado, y el id del artefacto que se descargo. Sin esto, una
        # traza vieja no puede contestar "¿que se le entrego al usuario?".
        "proyecto": resultado.get("proyecto"),
        "model": resultado.get("model"),
        "model_route": resultado.get("model_route"),
        "tools": resultado.get("tools") or [],
        "exito_verificado": round(exito, 3),
        # aparte a proposito: demostrado contra una simulacion NO es demostrado
        "exito_en_simulacion": round(en_simulacion, 3),
        # la metrica del plan: lo demostrado por cada dolar-segundo
        "valor": round(exito / max(coste * segundos, 1e-9), 4),
    }
    with open(archivo, "a") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    return fila


def linea(fila):
    """El cierre legible que se enseña al final de cada tarea."""
    p = fila["propiedades"]
    m, s = divmod(int(fila["segundos"]), 60)
    partes = [f"{p['verificado']} verificadas"]
    if p.get("verificado en simulación"):
        partes.append(f"{p['verificado en simulación']} solo en simulación")
    if p["refutado"]:
        partes.append(f"{p['refutado']} refutadas")
    if p["sin verificar"]:
        partes.append(f"{p['sin verificar']} sin verificar")
    return (f"{' · '.join(partes)} · {fila['llamadas']} llamadas · "
            f"${fila['coste_usd']:.4f} · {m}m {s:02d}s")


def leer(archivo=ARCHIVO):
    if not archivo.exists():
        return []
    return [json.loads(l) for l in archivo.read_text().splitlines() if l.strip()]


if __name__ == "__main__":
    filas = leer()
    if not filas:
        print("Todavia no hay trazas. Se escriben al ejecutar rapido.py o el modo rapido de la web.")
        raise SystemExit
    print(f"{'cuando':20} {'ver':5} {'est':6} {'llam':>4} {'tokens':>8} {'$':>8} {'seg':>5} "
          f"{'exito':>6} {'valor':>7}")
    for f in filas[-20:]:
        print(f"{f['cuando']:20} {f['version']:5} {str(f['estado']):6} {f['llamadas']:>4} "
              f"{f['tokens']:>8,} {f['coste_usd']:>8.4f} {f['segundos']:>5.0f} "
              f"{f['exito_verificado']:>6.2f} {f['valor']:>7.2f}")
