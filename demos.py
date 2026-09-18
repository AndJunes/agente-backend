"""Que se pueda ver la maquina funcionando sin pagar, sin que invente respuestas.

EL PROBLEMA QUE RESUELVE

    Con el candado offline puesto, el servidor sustituia la decision del modelo por un
    fixture elegido con una regex de tres literales: cualquier pregunta que no dijera
    "calculator" recibia un parrafo fijo y seguro sobre indices de PostgreSQL. Preguntar
    "¿que es Raft?" devolvia esa explicacion de indices con un aviso de "decision simulada".

    El aviso era cierto y aun asi el conjunto mentia: **un fixture que responde con
    seguridad a la pregunta equivocada es exactamente lo que este proyecto existe para no
    hacer.** Peor que no contestar, porque parece una alucinacion del modelo cuando es un
    fixture mal elegido.

COMO QUEDA

    Hay TRES demos preparadas y reconocibles. Si la pregunta es una de ellas, se responde
    con su guion y se marca `SIMULADA`. Si no lo es, NO se inventa: se dice que no hay
    modelo, y el resto del pipeline —plan, recuperacion, contexto, suficiencia— corre y se
    enseña de verdad, que es lo unico que aqui no es simulado.
"""

import os
import re

# Las demos ENCIENDEN la ejecucion a proposito, y hay que decir por que para que nadie se
# confunda: en produccion esta APAGADA (skills.impedimento_de_ejecucion), porque este
# agente entrega el codigo y sus casos de test sin correrlos — de eso se encargara el
# agente de QA. Lo que estas demos ensenan es la maquinaria de verificacion: que cuando
# algo SI se ejecuta, el veredicto sale de lo observado y no de lo que diga el modelo.
# Esa maquinaria sigue entera, apagada, y es la que heredara QA.
#
# Sin esto las cuatro demos saldrian GENERADO / no_ejecutado: honesto, pero no demuestra
# nada, que es justo lo contrario de para lo que existen.
os.environ.setdefault("MIRAG_EJECUCION", "on")

import dobles

# Cada demo: (clave, que demuestra, como se reconoce, guion).
# ORDEN: de lo mas especifico a lo mas general. "crea calculator.py que use un indice" es una
# peticion de codigo, no una pregunta conceptual, y con el orden al reves se llevaria la demo
# equivocada — la misma clase de error que este modulo existe para cerrar, en pequeño.
DEMOS = (
    # La primera, por la regla de este archivo: de lo mas especifico a lo mas general.
    # "crea un proyecto con una calculadora" no puede llevarse el guion de `codigo`.
    ("proyecto",
     "un proyecto multiarchivo generado, ejecutado, empaquetado y re-verificado",
     re.compile(r"api rest|api de libros|libros-api|crud completo|"
                r"proyecto (completo|multiarchivo)|por dominios", re.I),
     lambda: dobles.PROYECTO_LIBROS),
    ("reparacion",
     "el bucle de arreglo: codigo roto, fallo observado, segunda pasada",
     re.compile(r"divisi[oó]n por cero|divide\s*\(|dividir por cero", re.I),
     lambda: dobles.CODIGO_ROTO_LUEGO_ARREGLADO),
    ("codigo",
     "generar codigo, EJECUTARLO y verificarlo con marcadores reales",
     re.compile(r"calculator|calculadora|calculate\s*\(", re.I),
     lambda: dobles.CODIGO_CALCULADORA),
    ("conceptual",
     "retrieval visible: plan, tres indices, contexto y suficiencia, sin codigo",
     re.compile(r"\bíndice|\bindice|\bindex\b|postgres", re.I),
     lambda: dobles.DECISION_SIMPLE),
)

SIN_MODELO = (
    "No hay respuesta del modelo: el candado offline está puesto (`MIRAG_OFFLINE=1`) y esta "
    "pregunta no es una de las tres demos preparadas.\n\n"
    "**Lo que se ve arriba no está simulado**: el plan, la recuperación sobre los tres índices, "
    "el contexto que se habría enviado y el veredicto de suficiencia son reales. Lo único que "
    "falta es la decisión del modelo, y antes de inventarla se prefiere no darla.\n\n"
    "Para una respuesta de verdad: `MIRAG_OFFLINE=0`. Para ver la máquina entera sin pagar, "
    "probá una de las demos."
)


def reconocer(pregunta):
    """(clave, guion) de la demo que corresponde, o (None, None) si no hay ninguna."""
    for clave, _que, patron, guion in DEMOS:
        if patron.search(pregunta or ""):
            return clave, list(guion())
    return None, None


def por_clave(clave):
    """El guion de una demo por su nombre. `None` = el de 'no hay modelo'."""
    if clave is None:
        return [dobles.texto(SIN_MODELO)]
    for c, _q, _p, guion in DEMOS:
        if c == clave:
            return list(guion())
    raise KeyError(f"guion desconocido: {clave!r}")


def guion_para(pregunta):
    """El guion offline para esta pregunta. Nunca una demo que no le toca.

    Devuelve (clave_o_None, guion). Si no hay demo, el guion responde diciendo que no hay
    modelo — no un parrafo de otro tema.
    """
    clave, guion = reconocer(pregunta)
    if clave:
        return clave, guion
    return None, [dobles.texto(SIN_MODELO)]


# Las tres demos canonicas del producto: lo que hay que poder enseñar sin miedo.
# `clave` es la del guion offline; `pregunta` es la que se lanza; `exige` es el contrato.
# `guion` es explicito a proposito: hacer que una demo canonica se re-descubra por regex
# es pedir que te sirva otra. Paso: la pregunta de `construccion` dice "division por cero"
# y se la llevaba el guion de `reparacion`, asi que la pagina anunciaba una demo y corria
# la otra. Un producto no puede equivocarse sobre lo que te esta enseñando.
CANONICAS = {
    "proyecto": {
        "pregunta": ("Creá una API REST de libros con CRUD completo. Arquitectura por "
                     "dominios: separá router, service, repository, schemas y models. "
                     "Agregá tests y dejame el proyecto listo para descargar."),
        "guion": "proyecto",
        "demuestra": ("de una frase a un proyecto de 14 archivos, ejecutado, verificado "
                      "y empaquetado en un ZIP que se puede descomprimir y correr"),
        "exige": {"hay_proyecto": True, "archivos": 10, "estado_proyecto": ("VERIFICADO",),
                  "integridad_ok": True, "crud_verificado": 7, "hay_descarga": True},
    },
    "conocimiento": {
        "pregunta": "¿Qué es un índice de PostgreSQL y cuándo deja de servir?",
        "guion": "conceptual",
        "demuestra": "el corpus contesta: qué se recuperó, qué contexto se armó, qué se respondió",
        "exige": {"hay_respuesta": True, "hay_retrieval": True, "hay_codigo": False,
                  "suficiencia": ("cubierto", "mencionado")},
    },
    "construccion": {
        "pregunta": ("Crea calculator.py con una función calculate(a, b, operation) y sus tests "
                     "con marcadores TEST:<id>:PASS, cubriendo las cuatro operaciones."),
        "guion": "codigo",
        "demuestra": "plan, retrieval, código, EJECUCIÓN, tests y evidencia",
        "exige": {"hay_respuesta": True, "hay_retrieval": True, "hay_codigo": True,
                  "ejecutado": True, "estado": ("verde",), "propiedades_verificadas": 1},
    },
    "abstencion": {
        "pregunta": "¿Cómo implemento consenso Raft con garantías de linealizabilidad?",
        "guion": None,          # justamente: no hay guion, y eso es lo que demuestra
        "demuestra": "que Mirag dice que no sabe en vez de inventar",
        "exige": {"hay_respuesta": True, "hay_retrieval": True, "hay_codigo": False,
                  "suficiencia": ("mencionado", "ausente"), "avisa_cobertura": True},
    },
}


def catalogo():
    return [{"clave": c, "demuestra": q, "ejemplo": e}
            for (c, q, _p, _g), e in zip(DEMOS, EJEMPLOS)]


EJEMPLOS = (
    "Crea una función divide(a, b) en Python que maneje la división por cero, con tests",
    "Crea calculator.py con una función calculate(a, b, operation) y sus tests",
    "¿Qué es un índice de PostgreSQL y cuándo no sirve?",
)


def correr(clave, offline=None, guardar=False):
    """Una demo canonica de punta a punta. Devuelve (Ejecucion, informe del contrato).

    offline=None respeta `agent.OFFLINE`. El informe dice que se exigia, que se observo
    y si cuadran — sin interpretar nada: los datos salen de la Ejecucion real.
    """
    import agent
    import pipeline
    import skills

    if clave not in CANONICAS:
        raise KeyError(f"demo desconocida: {clave!r}. Hay: {', '.join(CANONICAS)}")
    caso = CANONICAS[clave]
    simular = agent.OFFLINE if offline is None else offline

    if simular:
        import dobles
        guion = por_clave(caso["guion"])
        with dobles.usar(guion):
            e = pipeline.ejecutar(caso["pregunta"], guardar=guardar)
    else:
        e = pipeline.ejecutar(caso["pregunta"], guardar=guardar)

    ejec = skills.resultado_de(e.salida) if e.salida else None
    # Se mide lo que VE EL USUARIO, no `e.respuesta`: en una tarea de codigo esa viene
    # vacia y el texto lo arma el servidor. Un contrato que mira el campo interno daria
    # por bueno un producto que no enseña nada.
    import server
    markdown = server._respuesta_pipeline(e, caso["guion"] if simular else None)
    cert = e.certificado
    art = e.artefacto
    observado = {
        "hay_proyecto": e.proyecto is not None,
        "archivos": (e.proyecto.totales["archivos"] if e.proyecto else 0),
        "estado_proyecto": (cert.estado if cert else None),
        "integridad_ok": bool(art and art.paquete and art.paquete.ok),
        "crud_verificado": sum(1 for k, v in (cert.marcas if cert else {}).items()
                               if k.startswith("crud_") and v == "PASS"),
        "hay_descarga": bool(art and art.para_la_pagina()["descarga"]),
        "hay_respuesta": len(markdown.strip()) > 40,
        "hay_retrieval": any(p.nombre == "recuperacion" and p.estado == "ejecutado"
                             for p in e.pasos),
        "hay_codigo": bool(e.entrega),
        "ejecutado": bool(ejec),
        "estado": ejec.estado if ejec else None,
        "suficiencia": e.veredicto.grado if e.veredicto else None,
        "propiedades_verificadas": sum(1 for x in (e.evidencia or [])
                                       if x.get("estado") == "verificado"),
        "avisa_cobertura": bool(e.veredicto and not e.veredicto.suficiente
                                and (e.respuesta or "").startswith(e.veredicto.frase()[:24])),
    }

    fallos = []
    for campo, esperado in caso["exige"].items():
        real = observado.get(campo)
        if isinstance(esperado, tuple):
            ok = real in esperado
        elif isinstance(esperado, bool):
            ok = bool(real) is esperado
        else:
            ok = isinstance(real, int) and real >= esperado
        if not ok:
            fallos.append(f"{campo}: se exigia {esperado!r}, se observo {real!r}")
    return e, {"demo": clave, "pregunta": caso["pregunta"], "simulada": simular,
               "markdown": markdown,
               "observado": observado, "fallos": fallos, "cumple": not fallos}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import agent
        for clave in ([sys.argv[1]] if sys.argv[1] != "todas" else list(CANONICAS)):
            e, informe = correr(clave)
            print(f"\n{'─' * 72}\nDEMO {clave.upper()} · {CANONICAS[clave]['demuestra']}")
            print(f"{'─' * 72}\n  {informe['pregunta'][:70]}\n")
            for k, v in informe["observado"].items():
                print(f"    {k:<26} {v}")
            print(f"\n  {'✅ CUMPLE EL CONTRATO' if informe['cumple'] else '❌ NO CUMPLE'}"
                  f"{'' if informe['cumple'] else ': ' + '; '.join(informe['fallos'])}")
            print(f"  {'SIMULADO · $0' if informe['simulada'] else f'${agent.PRESUPUESTO.coste:.4f}'}"
                  f" · {len(e.pasos)} etapas")
        raise SystemExit

    print("demos preparadas (offline, 0 coste):\n")
    for d in catalogo():
        print(f"  {d['clave']:<12} {d['demuestra']}")
        print(f"  {'':<12} ej: {d['ejemplo']}\n")
    print("cualquier otra pregunta:")
    for q in ("¿que es Raft?", "como funciona el consenso distribuido", "que es un indice"):
        clave, _ = guion_para(q)
        print(f"  {str(clave):<12} {q}")
