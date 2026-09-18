"""Contrasta lo que el modelo AFIRMA con lo que la ejecucion DEMUESTRA.

POR QUE HACE FALTA AUNQUE EL EJECUTOR YA NO MIENTA

    Arreglar skills.verificar_codigo quita la causa principal: ya no le decimos
    "TESTS EN VERDE" a un script vacio. Pero sigue habiendo un hueco, porque el modelo
    puede afirmar lo que quiera en su prosa final, y esa prosa no la revisaba nadie:

        ejecucion real  →  SIN EVIDENCIA (0 marcadores)
        respuesta final →  "Perfecto. Los 3 test cases pasaron realmente."

    Las dos frases conviven en la misma pantalla sin contradecirse. Esto las contradice.

QUE HACE Y QUE NO HACE
    NO reescribe ni recorta la respuesta del modelo: la deja intacta, porque el codigo
    puede estar perfectamente bien y lo unico que falta sea el formato del marcador.
    Lo que hace es ANTEPONER un aviso para que nadie lea la afirmacion sin el contexto.

    Tampoco juzga si el codigo es correcto. Juzga si la AFIRMACION tiene respaldo.
"""

import re

import skills

# Como suena una afirmacion de exito. Lista a mano y deliberadamente corta: cuantas mas
# formas se metan, mas falsos positivos, y un aviso que salta cuando no toca ensucia las
# respuestas buenas y acaba ignorandose.
AFIRMA_EXITO = re.compile(
    r"\b(pasaron|pasar on|paso correctamente|pasan todos|todos los tests? pasa|"
    r"tests? en verde|funcionan? correctamente|esta verificado|quedo verificado|"
    r"verificado con exito|los \d+ (tests?|casos)|✓|✅)", re.I)

# Frases que ya reconocen el limite: si el modelo YA avisa, no hace falta avisarle encima.
YA_AVISA = re.compile(
    r"\b(evidencia insuficiente|sin evidencia|no (pude|puedo) (ejecutar|verificar)|"
    r"no se ejecut|no est[aá] verificado|no puedo afirmar|sin verificar)\b", re.I)


def marcas_de(salidas):
    """Todos los marcadores TEST:<id>:PASS|FAIL de todas las ejecuciones."""
    marcas = {}
    for salida in salidas or ():
        marcas.update(skills.marcas_de(salida))
    return marcas


def auditar(respuesta, salidas=(), propiedades_declaradas=None):
    """(aviso | None, estado). `salidas` son los resultados de verificar_codigo.

    estado: "respaldada" | "sin_respaldo" | "refutada" | "no_ejecutado" | "sin_afirmacion"
    """
    texto = respuesta or ""
    salidas = [s for s in (salidas or ()) if s]
    marcas = marcas_de(salidas)
    pasan = [k for k, v in marcas.items() if v == "PASS"]
    fallan = [k for k, v in marcas.items() if v == "FAIL"]
    estados = [skills.veredicto(s)[0] for s in salidas]

    afirma = bool(AFIRMA_EXITO.search(texto))

    # 1. el modelo afirma que algo fallido paso
    if afirma and fallan:
        return (_aviso("AFIRMACIÓN CONTRADICHA POR LA EVIDENCIA",
                       f"El modelo afirma que los tests pasaron, pero la ejecución "
                       f"marcó **{len(fallan)} como FAIL**: "
                       f"{', '.join('`%s`' % f for f in sorted(fallan))}."),
                "refutada")

    # 2. afirma, pero nada llego a ejecutarse
    if afirma and estados and all(e == "no_ejecutado" for e in estados):
        cabecera = skills.veredicto(salidas[-1])[1]
        return (_aviso("AFIRMACIÓN NO RESPALDADA POR EVIDENCIA",
                       f"El modelo afirma que los tests pasaron, pero **el comando no "
                       f"llegó a ejecutarse**: {cabecera}"),
                "no_ejecutado")

    # 3. afirma y no hay ni un marcador que lo respalde — el caso del script vacio
    if afirma and not pasan and not YA_AVISA.search(texto):
        detalle = ("la ejecución no produjo ningún marcador verificable para esos tests"
                   if salidas else "no se ejecutó nada: no hay ninguna ejecución que respaldarlo")
        return (_aviso("AFIRMACIÓN NO RESPALDADA POR EVIDENCIA",
                       f"El modelo afirma que los tests pasaron, pero {detalle}. "
                       f"Un `exit 0` demuestra que el comando no se cayó, no que probara nada. "
                       f"Para que cuente, cada test debe imprimir `TEST:<id>:PASS`."),
                "sin_respaldo")

    # 4. declaro propiedades y ninguna aparecio en la salida
    declaradas = [p for p in (propiedades_declaradas or ()) if isinstance(p, dict)]
    ids = [str(p.get("test_id", "")).strip() for p in declaradas]
    if ids and not any(i in marcas for i in ids if i):
        return (_aviso("NINGUNA PROPIEDAD DEMOSTRADA",
                       f"El modelo declaró **{len(ids)} propiedades** a demostrar y "
                       f"ninguno de sus `test_id` apareció en la salida de ejecución."),
                "sin_respaldo")

    if afirma and pasan:
        return None, "respaldada"
    return None, "sin_afirmacion"


def _aviso(titulo, cuerpo):
    return f"> ⚠️ **{titulo}**\n>\n> {cuerpo}"


def aplicar(respuesta, salidas=(), propiedades_declaradas=None):
    """La respuesta con el aviso delante si hace falta. El texto original no se toca."""
    aviso, estado = auditar(respuesta, salidas, propiedades_declaradas)
    if not aviso:
        return respuesta, estado
    return f"{aviso}\n\n{respuesta or ''}", estado


def salidas_de_pasos(pasos):
    """Saca los resultados de verificar_codigo de los pasos de agent.run."""
    return [p.get("resultado", "") for p in (pasos or [])
            if p.get("tipo") == "skill" and str(p.get("nombre", "")).startswith("verificar_codigo")]


if __name__ == "__main__":
    import sys
    casos = [
        ("afirma sin marcadores", "Perfecto. Los 3 test cases pasaron realmente.",
         ["SIN EVIDENCIA: ...\n\n(sin salida)"], "sin_respaldo"),
        ("afirma con marcadores", "Los tests pasaron.",
         ["TESTS EN VERDE · 2 de 2 marcadores\n\nTEST:a:PASS\nTEST:b:PASS"], "respaldada"),
        ("afirma con un FAIL", "Todos los tests pasaron correctamente.",
         ["FALLO: 1 de 2 marcadores fallaron\n\nTEST:a:PASS\nTEST:b:FAIL"], "refutada"),
        ("afirma y no se ejecuto", "Los 3 tests pasaron.",
         ["NO EJECUTADO: bash no esta permitido"], "no_ejecutado"),
        ("no afirma nada", "Aqui tienes el codigo.", ["SIN EVIDENCIA: ..."], "sin_afirmacion"),
        ("ya avisa el solo", "EVIDENCIA INSUFICIENTE: los tests no pasaron por marcadores.",
         ["SIN EVIDENCIA: ..."], "sin_afirmacion"),
    ]
    fallos = 0
    for nombre, texto, salidas, esperado in casos:
        aviso, estado = auditar(texto, salidas)
        ok = estado == esperado
        fallos += not ok
        print(f"  {'✅' if ok else '❌'} {nombre:<26} → {estado}"
              + ("" if ok else f"  (esperaba {esperado})"))
        if aviso:
            print(f"        {aviso.splitlines()[0]}")
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
