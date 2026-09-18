"""¿Alcanza lo recuperado para responder, o hay que decir que no se sabe?

EL PROBLEMA QUE RESUELVE
    El retrieval SIEMPRE devuelve algo. Preguntale por Raft y te devuelve
    "CAP, PACELC y consistencia" con buena puntuacion, porque Raft se menciona cuatro
    veces en el corpus. Un sistema que no distingue MENCION de COBERTURA contesta con
    seguridad sobre algo que nunca se documento.

LA SEÑAL QUE LOS SEPARA
    El corpus tiene estructura: cada trozo tiene un TITULO y la mayoria una FICHA (el
    bloque '> **Ficha**' con Cuándo/Patrón/Anti-patrón/...). Un concepto que el corpus
    cubre de verdad aparece en un titulo o en una ficha. Un concepto que solo se
    menciona aparece únicamente en la prosa.

        Kubernetes  -> hay un trozo titulado "Kubernetes"          -> cubierto
        Raft        -> solo aparece suelto dentro de otros trozos  -> mencionado
        WebRTC      -> no aparece en ningun sitio                  -> ausente

    No es perfecto (ver los limites al final del modulo), pero es una señal real del
    corpus, no un umbral inventado sobre puntuaciones que no tienen escala.

QUE SE HACE CON EL VEREDICTO
    Solo decirlo. Este modulo no decide si se contesta: marca el grado y el motivo para
    que el pipeline y la UI puedan decir "esto no esta cubierto" en vez de rellenar.
"""

import re
from functools import lru_cache
from typing import NamedTuple

import rag

# palabras demasiado comunes para juzgar cobertura con ellas
VACIAS = {"como", "que", "para", "por", "con", "los", "las", "del", "una", "uno", "the",
          "and", "for", "with", "cual", "cuales", "donde", "cuando", "hacer", "puedo",
          "quiero", "necesito", "mejor", "usar", "entre", "sobre", "esto", "esta",
          "mi", "un", "de", "en", "es", "se", "y", "o", "a", "al", "lo", "su"}

MINIMO_TERMINO = 4          # por debajo de esto una palabra no distingue nada
DEMASIADO_COMUN = 25        # un termino en mas de N trozos no sirve para juzgar cobertura
RARO_DE_VERDAD = 6          # para decir "solo mencionado" el termino tiene que ser raro
MINIMO_AUSENTE = 6          # una palabra corta que falta ('slot', 'left') no es un agujero
PREFIJO = 4                 # 'reserven' tiene que casar con 'reservar': es la misma palabra

# Terminaciones de verbo y de plural en español. Una palabra que no esta en el corpus y
# acaba asi es lenguaje, no tema: 'amontonan', 'hago', 'evito' no son agujeros de
# cobertura, son como habla la gente. 'webrtc', 'pytorch' o 'raft' no acaban asi.
# Es una regla morfologica a mano y se equivoca a veces; ver los limites del modulo.
COLA_DE_VERBO = ("ando", "endo", "aron", "eron", "amos", "emos", "imos", "aban", "ian",
                 "ara", "iera", "ase", "ese", "an", "en", "as", "es", "ar", "er", "ir",
                 "aba", "o", "a")


class Veredicto(NamedTuple):
    suficiente: bool
    grado: str               # "cubierto" | "mencionado" | "ausente"
    motivo: str
    terminos: dict           # termino -> "titulo" | "ficha" | "prosa" | "ausente"
    señales: dict

    def frase(self):
        """Lo que se le enseña a quien pregunta."""
        if self.grado in ("cubierto", "no evaluado"):
            return ""                 # nadie miro: no hay nada honesto que avisar
        flojos = [t for t, d in self.terminos.items() if d in ("prosa", "ausente")]
        if self.grado == "ausente":
            return (f"El corpus no cubre {', '.join(flojos)}: no aparece en ninguna de las "
                    f"19 cajas. Lo que siga no sale de los documentos.")
        return (f"El corpus MENCIONA {', '.join(flojos)} pero no lo desarrolla: no hay "
                f"ninguna seccion ni ficha sobre eso. Lo recuperado habla de temas "
                f"vecinos, no de lo que preguntas.")


def no_evaluado(motivo):
    """SUFICIENCIA=off. `suficiente=True` no afirma cobertura: afirma que no hay aviso que
    dar, porque nadie miro. Que quede en el motivo y no en un silencio."""
    return Veredicto(True, "no evaluado", motivo, {}, {"evaluado": False})


def _distintivos(consulta):
    """Las palabras de la consulta que de verdad discriminan."""
    palabras = re.findall(r"[a-z0-9]{%d,}" % MINIMO_TERMINO, rag._normalizar(consulta))
    return [p for p in dict.fromkeys(palabras) if p not in VACIAS]


@lru_cache(maxsize=2048)
def _donde_aparece(termino):
    """Donde vive un termino y en cuantos trozos: (sitio, frecuencia).

    Se mira el corpus ENTERO, no solo lo recuperado: la pregunta es si el corpus cubre
    el concepto, no si esta busqueda acerto.

    El prefijo evita el falso negativo del español: 'reserven' no esta literalmente en
    el corpus pero 'reservar' si, y son la misma palabra. Sin esto, cualquier verbo
    conjugado se contaba como un agujero de cobertura.
    """
    corto = termino[:PREFIJO]

    def dentro(texto):
        return termino in texto or corto in texto

    en_titulo = any(dentro(rag._normalizar(t.titulo)) for t in rag.TROZOS)
    frecuencia = sum(1 for t in rag.TROZOS if dentro(t.norm))
    if en_titulo:
        return "titulo", frecuencia
    if any(dentro(f.norm) for f in rag.FICHAS):
        return "ficha", frecuencia
    return ("prosa" if frecuencia else "ausente"), frecuencia


def evaluar(consulta, recuperados=(), plan=None):
    """El veredicto. `recuperados` es [(Trozo, puntuacion)] de la busqueda."""
    terminos = _distintivos(consulta)
    # lo que el plan dice que hace falta si o si pesa igual que lo que pidio el usuario
    if plan is not None:
        for extra in list(plan.technologies or ()) + list(plan.required_knowledge or ()):
            for p in _distintivos(str(extra)):
                if p not in terminos:
                    terminos.append(p)

    if not terminos:
        return Veredicto(True, "cubierto", "la consulta no tiene terminos distintivos que juzgar",
                         {}, {"terminos": 0})

    sitios = {t: _donde_aparece(t) for t in terminos}
    donde = {t: sitio for t, (sitio, _) in sitios.items()}

    # Solo juzgan los terminos RAROS. Uno que sale en media enciclopedia ('servicio',
    # 'implementar') no dice nada sobre si el tema esta cubierto, y promediarlo
    # ahogaba justo al termino que importaba: 'webrtc' se perdia entre 'streaming',
    # 'video' y 'tiempo', que si estan en el corpus.
    juzgan = {t: sitio for t, (sitio, f) in sitios.items() if f <= DEMASIADO_COMUN}
    ignorados = [t for t in terminos if t not in juzgan]

    cubiertos = [t for t, d in juzgan.items() if d in ("titulo", "ficha")]
    # 'solo mencionado' pide que el termino sea RARO: uno que sale en 20 trozos de prosa
    # es vocabulario normal ('diferencia'), no un concepto que el corpus dejo a medias.
    solo_prosa = [t for t, d in juzgan.items()
                  if d == "prosa" and sitios[t][1] <= RARO_DE_VERDAD]
    # y un termino ausente solo cuenta si no es una palabra conjugada del idioma
    # Un termino ausente solo pesa si (a) no es una palabra conjugada del idioma y
    # (b) es largo: 'slot' o 'left' faltan del corpus y no significan nada, mientras que
    # 'webrtc' o 'pytorch' faltando si son el tema entero de la pregunta.
    ausentes = [t for t, d in juzgan.items()
                if d == "ausente" and not t.endswith(COLA_DE_VERBO)
                and len(t) >= MINIMO_AUSENTE]

    puntuaciones = [p for _, p in recuperados]
    señales = {
        "terminos": len(terminos), "juzgan": len(juzgan),
        "ignorados_por_comunes": ignorados,
        "cubiertos": len(cubiertos), "solo_prosa": len(solo_prosa), "ausentes": len(ausentes),
        "mejor_puntuacion": round(puntuaciones[0], 3) if puntuaciones else 0.0,
        "recuperados": len(recuperados),
    }

    if not recuperados:
        return Veredicto(False, "ausente", "la busqueda no devolvio nada", donde, señales)
    # basta UN termino raro sin cubrir para no poder responder: es el que lleva el tema
    if ausentes:
        return Veredicto(False, "ausente",
                         f"{', '.join(ausentes)} no aparece en el corpus", donde, señales)
    if solo_prosa:
        return Veredicto(False, "mencionado",
                         f"{', '.join(solo_prosa)} solo aparece de pasada: ninguna seccion ni "
                         f"ficha lo desarrolla", donde, señales)
    if not juzgan:
        return Veredicto(True, "cubierto",
                         "todos los terminos son comunes en el corpus: no hay nada raro "
                         "que pueda faltar", donde, señales)
    return Veredicto(True, "cubierto",
                     f"los {len(juzgan)} terminos que discriminan tienen seccion o ficha propia",
                     donde, señales)


# LIMITES CONOCIDOS, para no vender esto como mas de lo que es:
#  · Va por palabras: una pregunta que usa sinonimos de algo cubierto puede salir
#    'mencionado' aunque el corpus lo trate. Es un falso negativo, y prefiero ese
#    error al contrario.
#  · Un termino comun que aparezca en cualquier titulo cuenta como cubierto aunque
#    ese titulo no venga a cuento.
#  · No mide si la RESPUESTA es correcta, solo si el corpus tiene material del tema.


if __name__ == "__main__":
    import hibrido
    pruebas = [
        ("cubierto", "que es un indice de postgresql"),
        ("cubierto", "volumenes persistentes en kubernetes"),
        ("cubierto", "como evito que dos usuarios reserven la misma plaza"),
        ("mencionado", "implementar consenso Raft con garantias de linealizabilidad"),
        ("mencionado", "configurar un service mesh con mTLS entre servicios"),
        ("ausente", "streaming de video en tiempo real con WebRTC"),
        ("ausente", "entrenar un modelo de machine learning con pytorch"),
    ]
    aciertos = 0
    for esperado, q in pruebas:
        r = hibrido.recuperar(q, k=5)
        v = evaluar(q, r.trozos)
        ok = v.grado == esperado
        aciertos += ok
        print(f"  {'✅' if ok else '❌'} [{v.grado:<10}] esperado {esperado:<10} {q[:52]}")
        print(f"        {v.motivo}")
        if v.frase():
            print(f"        → {v.frase()[:110]}")
    print(f"\n{aciertos}/{len(pruebas)} " + ("TODO OK" if aciertos == len(pruebas) else "FALLOS"))
