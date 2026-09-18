"""Lo que Mirag sabe de si mismo, sin preguntarselo al RAG ni al modelo.

Preguntas como "¿que modelo usas?" o "¿cuantas cajas hay?" no necesitan busqueda
ni LLM: la respuesta es un dato del proyecto. Este atajo las contesta en
milisegundos y con coste cero.

Si la pregunta NO encaja, devuelve None y el flujo normal sigue como siempre:
un atajo que adivina es peor que no tener atajo.
"""

import re
import unicodedata
from pathlib import Path

import agent
import rag
import skills

AQUI = Path(__file__).parent


def _modos_reales():
    """Lee del dispatch del servidor cuales existen, en vez de repetirlos aqui."""
    try:
        fuente = (AQUI / "server.py").read_text()
    except OSError:
        return {"pipeline": "produccion"}
    modos = {}
    if 'modo == "pipeline"' in fuente:
        modos["pipeline"] = ("PRODUCCION · plan, recuperacion de 3 indices, contexto, "
                             "generacion, verificacion y evidencia · 1-2 llamadas")
    if 'modo == "arquitecto"' in fuente:
        modos["arquitecto"] = ("EXPERIMENTAL · 9 fases de diseño encadenadas. Sus fases NO "
                               "tienen el mismo nivel de verificacion que pipeline · ~10 min")
    return modos


def _simbolos():
    """Estado real del indice de codigo del propio proyecto."""
    try:
        import simbolos
        idx = simbolos.indexar(AQUI)
        r = simbolos.resumen(idx)
        lenguajes = sorted({p.suffix for p in AQUI.rglob("*")
                            if p.is_file() and p.suffix in (".py", ".html", ".md", ".json")})
        return {**r, "lenguajes": lenguajes,
                "entrypoints": sorted(p.name for p in AQUI.glob("*.py")
                                      if "__main__" in p.read_text())}
    except Exception as e:
        return {"estado": "NOT AVAILABLE", "motivo": f"{type(e).__name__}: {e}"}


def _estado():
    cajas = sorted({t.caja for t in rag.TROZOS})
    return {
        "proyecto": "Mirag",
        "modelo": agent.MODEL,
        # los modos se anunciaban a mano y quedaron obsoletos dos veces (faltaba
        # 'pipeline', y despues sobraban 'simple' y 'rapido' ya retirados)
        "modos": _modos_reales(),
        "skills": sorted(skills.SKILLS),
        "simbolos": _simbolos(),
        "corpus": {"cajas": len(cajas), "trozos": len(rag.TROZOS),
                   "fichas": len(rag.FICHAS), "antipatrones": len(rag.ANTIPATRONES),
                   "caracteres": sum(len(t.texto) for t in rag.TROZOS)},
        "cajas": cajas,
        "archivos": sorted(p.name for p in AQUI.glob("*.py")),
        # Era "cero dependencias externas" a secas, y dejo de ser cierto el dia que
        # aparecio blockchain/. La frase que ve el usuario tiene que decir donde vale.
        "restricciones": ["el nucleo no tiene dependencias externas; la capa blockchain/ "
                          "declara stellar-sdk",
                          "el codigo se verifica ejecutandolo, no leyendolo",
                          "coste visible en cada respuesta"],
        "salida": str(AQUI / "salida"),
    }


ESTADO = _estado()


def _norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# patron -> (titulo, como sacar la respuesta). Deliberadamente pocos y explicitos:
# cada uno resuelve una pregunta que de verdad se hace, no un caso hipotetico.
ATAJOS = [
    (r"\b(que|cual|cuál)\b.*\bmodelo\b", "Modelo",
     lambda e: f"`{e['modelo']}`, via OpenRouter. Se cambia con la constante MODEL de agent.py."),
    (r"\bmodos?\b.*\b(tiene|hay|son|existen|de mirag|del agente)\b"
     r"|\b(que|cuales|cuantos)\b.*\bmodos?\b"
     r"|\bdiferencia\b.*\b(simple|rapido|pipeline|arquitecto)\b", "Modos",
     lambda e: "\n".join(f"- **{k}** — {v}" for k, v in e["modos"].items())),
    (r"\b(que|cuales|cuantas)\b.*\b(skills?|herramientas?|tools?)\b"
     r"|\b(skills?|herramientas?|tools?)\b.*\b(tiene|tienes|hay|dispone|disponibles|del agente|de mirag)\b",
     "Skills disponibles",
     lambda e: "\n".join(f"- `{s}`" for s in e["skills"])),
    (r"\bcuant[oa]s?\b.*\b(cajas?|trozos?|chunks?|documentos?)\b|\btamañ?o\b.*corpus",
     "Tamaño del corpus",
     lambda e: (f"{e['corpus']['cajas']} cajas · {e['corpus']['trozos']} trozos recuperables · "
                f"{e['corpus']['fichas']} fichas · {e['corpus']['antipatrones']} anti-patrones\n\n"
                f"~{e['corpus']['caracteres'] // 4:,} tokens en total.")),
    (r"\b(que|cuales)\b.*\bcajas\b|\btemas?\b.*\bcubre\b"
     r"|\b(que|cuales|cuantas)\b.*\bareas?\b.*\b(cubre|hay|tiene|corpus)\b",
     "Las 19 cajas", lambda e: "\n".join(f"- {c}" for c in e["cajas"])),
    (r"\bdonde\b.*\b(guarda|queda|deja|escribe|guardan)\b.*\b(codigo|salida|archivos?)\b"
     r"|\bcarpeta\b.*\bsalida\b",
     "Dónde queda el código", lambda e: f"En `{e['salida']}/`, con un `COMO_EJECUTAR.txt`."),
    # Antes esto volcaba los 49 nombres de archivo en 52 lineas. Un desarrollador que
    # pregunta "de que se compone esto" no quiere un `ls`: quiere saber por donde entrar.
    (r"\barchivos?\b.*\bproyecto\b|\bestructura\b.*\bproyecto\b|\bde que\b.*\bcompone\b",
     "De qué se compone", lambda e: _mapa(e)),
]


CAMINO = [
    ("server.py", "el servidor y la página; una sola ruta, solo loopback"),
    ("pipeline.py", "**el camino de producción**: plan → retrieval → contexto → modelo → verificación"),
    ("recuperacion.py", "fuente única de retrieval y de contexto"),
    ("skills.py", "ejecuta el código y decide el veredicto; nadie más lo decide"),
    ("obligaciones.py", "cruza los anti-patrones recuperados con la evidencia"),
    ("config.py", "los interruptores y la compuerta de medición"),
    ("demos.py", "las tres demos canónicas"),
]


def _mapa(e):
    """Por dónde entrar, no un `ls`."""
    s = e.get("simbolos") or {}
    lineas = ["**Por dónde entrar**", ""]
    lineas += [f"- `{a}` — {q}" for a, q in CAMINO if a in e["archivos"]]
    if s.get("modulos"):
        lineas += ["", f"**El resto**: {len(e['archivos'])} módulos en total · "
                       f"{s.get('clases', '?')} clases · {s.get('funciones', '?')} funciones · "
                       f"{s.get('tests', '?')} tests."]
    lineas += ["", "El núcleo es solo biblioteca estándar: 0 dependencias externas. "
                   "La capa `blockchain/`, que está fuera de esa cadena y tiene su propio "
                   "entorno, declara `stellar-sdk`."]
    return "\n".join(lineas)


# Si la peticion es una ORDEN DE TRABAJO, el atajo no se mete. ProjectState contesta
# preguntas SOBRE Mirag, no acepta encargos. Sin esta guarda, un prompt que pedia generar
# codigo y verificarlo se comia el atajo entero — por la palabra "salida", que en
# castellano tecnico significa "output" — y devolvia 0 llamadas y ningun trabajo hecho.
# Y como estado.responder() corre ANTES de elegir modo, se llevaba por delante los cuatro.
VERBOS_DE_TRABAJO = re.compile(
    r"\b(crea|crear|cre[ao]s|construye|construir|implementa|implementar|escribe|escribir|"
    r"genera|generar|programa|programar|desarrolla|desarrollar|ejecuta|ejecutar|corre|correr|"
    r"prueba|probar|testea|testear|verifica|verificar|comprueba|comprobar|arregla|arreglar|"
    r"corrige|corregir|refactoriza|refactorizar|optimiza|optimizar|migra|migrar|"
    r"a[ñn]ade|agrega|agregar|dame el codigo|hazme|haz una|haz un)\b")


def es_orden_de_trabajo(pregunta: str) -> bool:
    return bool(VERBOS_DE_TRABAJO.search(_norm(pregunta)))


def responder(pregunta: str):
    """La respuesta si la pregunta es sobre el propio Mirag; None si no lo es."""
    p = _norm(pregunta)
    if es_orden_de_trabajo(p):
        return None                      # hay trabajo que hacer: no es una pregunta de estado
    for patron, titulo, formatear in ATAJOS:
        if re.search(patron, p):
            return f"## {titulo}\n\n{formatear(ESTADO)}\n\n*(del estado del proyecto: sin búsqueda ni llamada al modelo)*"
    return None


if __name__ == "__main__":
    PRUEBAS = [
        # deben acertar
        ("que modelo usas?", True), ("cuales son los modos?", True),
        ("que skills tienes?", True), ("cuantas cajas hay?", True),
        ("que areas cubre el corpus?", True), ("donde guarda el codigo?", True),
        ("de que archivos se compone el proyecto?", True),
        # NO deben acertar: son preguntas tecnicas, van al RAG
        ("que es el outbox pattern?", False), ("como evito el doble cobro?", False),
        ("diferencia entre inner join y left join", False),
        ("genera un endpoint de pagos", False), ("que es un circuit breaker", False),
        # ORDENES DE TRABAJO que contienen las palabras golosas. Todas secuestraban el
        # atajo: la de 'salida' es literalmente la que te devolvio 0 llamadas.
        ("Crea una funcion divide(a,b) y si no obtienes los marcadores desde la salida "
         "real responde EVIDENCIA INSUFICIENTE", False),
        ("escribe tests para mi API usando las herramientas que necesites", False),
        ("separa las areas de responsabilidad del modulo", False),
        ("ejecuta el codigo en modo debug y enseñame la salida", False),
        ("genera los archivos del proyecto base", False),
        ("implementa un rate limiter y prueba la concurrencia", False),
    ]
    fallos = 0
    for pregunta, deberia in PRUEBAS:
        r = responder(pregunta)
        ok = (r is not None) == deberia
        fallos += not ok
        print(f"  {'✅' if ok else '❌'} {'atajo ' if r else 'al RAG'} · {pregunta}")
        if r and ok:
            print(f"      {' '.join(r.split())[:88]}")
    print(f"\n{'TODO OK' if not fallos else f'{fallos} FALLOS'} · "
          f"{sum(1 for p, d in PRUEBAS if d)} preguntas resueltas con 0 llamadas")
