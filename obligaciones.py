"""Los anti-patrones recuperados son una obligación. Aquí se comprueba si se cumplió.

EL HUECO QUE CIERRA ESTE MODULO

    `rapido.py` afirma desde hace tiempo: "Los anti-patrones recuperados son de
    cubrimiento OBLIGATORIO". La sección del prompt se titula "(cubrir con un test CADA
    UNO)". Y **nadie lo comprobaba**: `_evidencia` cruza los `test_id` que declaró el
    MODELO contra los marcadores, nunca contra los anti-patrones que se recuperaron. Un
    modelo podía recibir seis anti-patrones, declarar una propiedad y salir con
    "1 verificado" limpio.

    Es el mismo defecto que el reranker medido sobre un ranking descartado: algo se
    afirmaba y nada lo observaba.

LO QUE ESTE MODULO SI HACE Y LO QUE NO

    SI: convierte cada anti-patrón recuperado en una obligación con identidad, y dice si
        la entrega la cubre, no la cubre, o si ni siquiera es comprobable.

    NO: no juzga si el código es correcto, no llama al modelo, y NO da por cubierta una
        obligación por parecido vago. Ante la duda: `no verificable`. Un falso "cubierta"
        sería exactamente el tipo de mentira que el resto del proyecto existe para evitar.

LO QUE NO SE PUEDE AFIRMAR TODAVIA (medido el 2026-09-15)

    Que los anti-patrones recuperados **apliquen** a la tarea. BM25 devuelve k resultados por
    consulta haya o no relación, y los scores no separan lo relevante de lo que no:

        "Implementa reservar(conn, plaza_id, usuario)... dos usuarios no pueden quedarse
         con la misma plaza"  →  top-1 = "Diseñar una capa de integración" con score 10.6
        "API de reservas: dos usuarios..."
                              →  "Transacciones y ACID", genuinamente relevante, score 4.7

    Un corte por score mataría el bueno y dejaría el malo. Así que aquí NO se pone umbral y la
    tabla NO afirma relevancia: dice qué trajo el corpus y qué demostró la ejecución. La versión
    anterior escribía "el corpus los trajo porque aplican a esta tarea" — una afirmación fuerte
    sin nada detrás, o sea el mismo defecto que este módulo existe para cerrar.

COMO DECIDE, Y POR QUE ASI
    Sin llamar a nadie: cruza los términos distintivos del anti-patrón contra el texto de
    las propiedades que el modelo declaró, y después mira si esa propiedad quedó
    VERIFICADA por un marcador real. O sea que hacen falta las dos cosas: que el modelo
    dijera que lo cubría Y que la ejecución lo demostrara.
"""

import re
from typing import NamedTuple

import rag

VACIAS = {"que", "una", "uno", "por", "para", "con", "los", "las", "del", "cada", "esta",
          "este", "sin", "mas", "muy", "todo", "toda", "cuando", "donde", "como", "pero",
          "sus", "ser", "hay", "the", "and", "for", "you", "your", "not", "debe", "deberia",
          "siempre", "nunca", "solo", "hacer", "tener", "dar", "aun", "asi"}
MINIMO_TERMINO = 5
MINIMO_COMUNES = 2        # cuantos terminos tienen que coincidir para considerarlo tratado


class Obligacion(NamedTuple):
    id: str               # "07 · Idempotencia en pagos"
    caja: str
    titulo: str
    evitar: str           # el ✗ NO
    hacer: str            # el ✓ SI
    terminos: tuple       # lo distintivo, para poder cruzarlo

    def resumen(self):
        return f"{self.id} — evitar: {self.evitar[:70]}"


def _terminos(*textos):
    palabras = []
    for t in textos:
        palabras += re.findall(r"[a-z0-9]{%d,}" % MINIMO_TERMINO, rag._normalizar(t or ""))
    return tuple(p for p in dict.fromkeys(palabras) if p not in VACIAS)


def de_retrieval(resultado):
    """Las obligaciones que salen de los anti-patrones REALMENTE recuperados."""
    salida = []
    for tr in resultado.antipatrones:
        texto = tr.trozo.texto
        evitar = (re.search(r"✗ NO:\s*(.+)", texto) or [None, ""])[1].strip()
        hacer = (re.search(r"✓ SÍ:\s*(.+)", texto) or [None, ""])[1].strip()
        if not evitar:
            continue                      # sin un "no hagas esto" no hay obligación que medir
        caja = tr.trozo.caja.split("·")[0].strip()
        salida.append(Obligacion(
            id=f"{caja} · {tr.trozo.titulo}", caja=caja, titulo=tr.trozo.titulo,
            evitar=evitar, hacer=hacer, terminos=_terminos(evitar, hacer, tr.trozo.titulo)))
    return salida


def cobertura(obligaciones, evidencia):
    """¿La entrega cubrió cada obligación? Devuelve una fila por obligación.

    estado:
      cubierta       el modelo declaró una propiedad que trata el anti-patrón Y la
                     ejecución la demostró con un marcador real
      declarada      el modelo dijo que la cubría y la ejecución NO lo demostró
      no cubierta    ninguna propiedad declarada trata este anti-patrón
      no verificable el anti-patrón no tiene términos suficientes para poder cruzarlo
    """
    filas = []
    for ob in obligaciones:
        if len(ob.terminos) < MINIMO_COMUNES:
            filas.append({"obligacion": ob.id, "estado": "no verificable",
                          "por_que": "el anti-patron no tiene terminos distintivos suficientes",
                          "evitar": ob.evitar, "propiedad": None})
            continue

        mejor, mejor_comunes = None, 0
        for prop in evidencia or []:
            texto = f"{prop.get('riesgo', '')} {prop.get('propiedad', '')}"
            comunes = len(set(ob.terminos) & set(_terminos(texto)))
            if comunes > mejor_comunes:
                mejor, mejor_comunes = prop, comunes

        if mejor_comunes < MINIMO_COMUNES:
            filas.append({"obligacion": ob.id, "estado": "no cubierta",
                          "por_que": "ninguna propiedad declarada trata este anti-patron",
                          "evitar": ob.evitar, "propiedad": None})
        elif mejor.get("estado") == "verificado":
            filas.append({"obligacion": ob.id, "estado": "cubierta",
                          "por_que": f"propiedad demostrada por el test {mejor.get('test_id')!r}",
                          "evitar": ob.evitar, "propiedad": mejor.get("propiedad")})
        else:
            filas.append({"obligacion": ob.id, "estado": "declarada",
                          "por_que": f"el modelo la declaro pero la ejecucion la dejo en "
                                     f"{mejor.get('estado')!r}",
                          "evitar": ob.evitar, "propiedad": mejor.get("propiedad")})
    return filas


def resumen(filas):
    cuenta = {}
    for f in filas:
        cuenta[f["estado"]] = cuenta.get(f["estado"], 0) + 1
    return cuenta


def tabla_markdown(filas):
    if not filas:
        return ""
    # RELATED / RECOVERED en vez de "cubierta / no cubierta": el estado describe la
    # relacion con la ENTREGA, no que el anti-patron aplique. Decir "no cubierta" sobre
    # algo que quiza ni venia a cuento sonaba a reproche y era una afirmacion de mas.
    iconos = {"cubierta": "✅ VERIFIED · demostrado por la ejecución",
              "declarada": "❔ NOT VERIFIED · el modelo lo trató, nada lo demostró",
              "no cubierta": "○ RECOVERED · recuperado, sin relación con la entrega",
              "no verificable": "— RECOVERED · no se puede cruzar"}
    lineas = ["## Anti-patrones que el corpus trajo para esta consulta", "",
              "El buscador devuelve un número fijo de anti-patrones por consulta, **relevantes o "
              "no** — no hay medición que diga cuáles aplican de verdad aquí. Así que esto es un "
              "registro, no un veredicto: el estado sale de cruzar lo que el modelo declaró con "
              "lo que la **ejecución** demostró.", "",
              "| Estado | Anti-patrón | Qué había que evitar |", "|---|---|---|"]
    lineas += [f"| {iconos.get(f['estado'], f['estado'])} | `{f['obligacion']}` | {f['evitar']} |"
               for f in filas]
    sin = [f for f in filas if f["estado"] in ("no cubierta", "declarada")]
    if sin:
        lineas += ["", f"**{len(sin)} de {len(filas)} sin demostrar.** No significa que el "
                       "código esté mal ni que faltara cubrirlos: significa exactamente que la "
                       "ejecución no aportó evidencia sobre ellos, y en varios casos que el "
                       "anti-patrón probablemente no venía a cuento."]
    return "\n".join(lineas)


if __name__ == "__main__":
    import plan as P
    import recuperacion
    q = "API de reservas: dos usuarios no pueden quedarse con la misma plaza"
    r = recuperacion.recuperar(q, plan=P.deducir(q))
    obs = de_retrieval(r)
    print(f"{len(obs)} obligaciones recuperadas para:\n  {q}\n")
    for o in obs:
        print(f"  {o.resumen()}")
    # una evidencia de mentira para ver los cuatro estados
    falsa = [{"riesgo": "dos usuarios reservan la misma plaza a la vez",
              "propiedad": "exitosos == 1", "test_id": "carrera", "estado": "verificado"},
             {"riesgo": "el pago se captura al autorizar", "propiedad": "captura != autorizacion",
              "test_id": "captura", "estado": "sin verificar"}]
    print(f"\ncruzando con una evidencia de ejemplo:")
    for f in cobertura(obs, falsa):
        print(f"  {f['estado']:<16} {f['obligacion'][:44]:<44} {f['por_que'][:46]}")
    print(f"\n  {resumen(cobertura(obs, falsa))}")
