"""Las skills: funciones normales de Python + el schema que ve el modelo.

Las cuatro de conocimiento son busquedas TIPADAS sobre el mismo corpus. Estan
separadas a proposito: el modelo elige por la descripcion, asi que cada una dice
para que sirve Y para que no.
"""

import ast
import operator
import re
import shlex
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import rag

# Solo estos binarios: el modelo elige el comando, asi que nada de shell libre.
# Y solo los que EXISTEN en esta maquina: tener 'pytest' en la lista cuando no esta
# instalado hacia que el modelo propusiera 'pytest -q', no se ejecutara nada, y aun asi
# la tarea se diera por buena. Se comprueba de verdad en vez de suponerlo.
PERMITIDOS = ("node", "python3", "python", "pytest")
INTERPRETES = {c for c in PERMITIDOS if shutil.which(c)}
TIMEOUT = 30


def buscar_en_docs(query: str) -> str:
    return rag.buscar(query)


def buscar_tradeoffs(tema: str) -> str:
    return rag.buscar_tradeoffs(tema)


def buscar_fallos(tema: str) -> str:
    return rag.buscar_fallos(tema)


def buscar_antipatrones(tema: str) -> str:
    return rag.buscar_antipatrones(tema)


def cajas_relacionadas(caja: str) -> str:
    return rag.cajas_relacionadas(caja)


def verificar_codigo(archivos: dict, comando: str) -> str:
    """Escribe los archivos en un directorio temporal y ejecuta el comando.

    Es la unica skill que produce EVIDENCIA en vez de opinion: o los tests pasan o no.
    Aislamiento minimo (allowlist de binarios, timeout, directorio temporal): suficiente
    para un demo local, NO es un sandbox de verdad.
    """
    if not archivos:
        return "NO EJECUTADO: no has pasado ningun archivo."
    try:
        partes = shlex.split(comando)
    except ValueError as e:
        return f"NO EJECUTADO: comando mal formado ({e})"
    if not partes or partes[0] not in INTERPRETES:
        return (f"NO EJECUTADO: solo se permite ejecutar {', '.join(sorted(INTERPRETES))}. "
                f"Pediste: {comando!r}")

    with tempfile.TemporaryDirectory() as carpeta:
        raiz = Path(carpeta).resolve()
        for ruta, contenido in archivos.items():
            destino = (raiz / ruta).resolve()
            if not destino.is_relative_to(raiz):          # nada de ../../etc/passwd
                return f"NO EJECUTADO: ruta no permitida ({ruta!r})"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(contenido)
        try:
            r = subprocess.run(partes, cwd=raiz, capture_output=True, text=True,
                               timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return (f"NO EJECUTADO: TIMEOUT, no termino en {TIMEOUT}s "
                    f"(¿bucle infinito, o espera de red?)")
        except FileNotFoundError:
            return f"NO EJECUTADO: {partes[0]} no esta instalado en esta maquina"

    completa = (r.stdout + r.stderr).strip()
    salida = _recortar_sin_perder_marcas(completa)
    # la cabecera se calcula sobre la salida COMPLETA: si se calculara sobre la
    # recortada, un test que imprime mucho antes de sus marcadores se reportaria
    # SIN EVIDENCIA habiendo pasado de verdad
    return f"{_cabecera(completa, r.returncode)}\n\n{salida or '(sin salida)'}"


MAXIMO_SALIDA = 4000


def _recortar_sin_perder_marcas(salida, maximo=MAXIMO_SALIDA):
    """Recorta la salida sin tirar la evidencia.

    Antes era `salida[-4000:]`, que conserva el final. Un test que imprimia 9.600
    caracteres de ruido DESPUES de sus marcadores perdia los marcadores en el recorte:
    la ejecucion habia pasado y se reportaba SIN EVIDENCIA. Lo que se guardaba dejaba
    de decir la verdad sobre lo que habia ocurrido.

    Ahora se conserva principio y final, y los marcadores se re-adjuntan si el recorte
    se hubiera llevado alguno.
    """
    if len(salida) <= maximo:
        return salida
    mitad = maximo // 2
    recortada = (salida[:mitad] + f"\n\n[... {len(salida) - maximo:,} caracteres recortados ...]\n\n"
                 + salida[-mitad:])
    perdidas = [f"TEST:{i}:{v}" for i, v in MARCA.findall(salida)
                if f"TEST:{i}:{v}" not in recortada]
    if perdidas:
        recortada += ("\n\n[marcadores recuperados del tramo recortado]\n"
                      + "\n".join(dict.fromkeys(perdidas)))
    return recortada


MARCA = re.compile(r"TEST:([^:\s]+):(PASS|FAIL)")


def _cabecera(salida, codigo):
    """La primera linea del resultado: lo UNICO que se sabe de esta ejecucion.

    Antes era 'TESTS EN VERDE' con solo mirar el exit code, y ese string se le pasa
    al modelo tal cual. Un script vacio ('pass') salia con 0 y el modelo leia
    literalmente que los tests estaban en verde — y lo repetia, con razon. No burlaba
    la evidencia: la evidencia le estaba mintiendo.

    Exit 0 demuestra que el comando no se cayo. No demuestra que probara nada.
    """
    marcas = MARCA.findall(salida or "")
    pasan = sum(1 for _, r in marcas if r == "PASS")
    if codigo != 0:
        return f"FALLO (exit {codigo})"
    if marcas and pasan < len(marcas):
        # un test puede imprimir FAIL y salir con 0. Ese test esta roto, y la ejecucion
        # con el: ningun CI lo detectaria y aqui tampoco lo dabamos por fallido.
        return f"FALLO: {len(marcas) - pasan} de {len(marcas)} marcadores fallaron"
    if marcas:
        return f"TESTS EN VERDE · {pasan} de {len(marcas)} marcadores"
    return ("SIN EVIDENCIA: el comando termino sin error pero no imprimio ningun marcador "
            "TEST:<id>:PASS, asi que no se sabe que se probo. NO afirmes que los tests "
            "pasaron: imprime un marcador por cada caso y vuelve a ejecutar.")


def marcas_de(salida):
    """Los marcadores del CUERPO, nunca de la cabecera.

    La cabecera de 'SIN EVIDENCIA' menciona el literal TEST:<id>:PASS para explicar lo
    que falta, y el extractor lo leia como un marcador de verdad: el aviso de que no
    habia evidencia se contaba a si mismo como evidencia.
    """
    cuerpo = (salida or "").split("\n", 1)[1] if "\n" in (salida or "") else ""
    return dict(MARCA.findall(cuerpo))


class Ejecucion(NamedTuple):
    """Lo que se OBSERVO al ejecutar. No una etiqueta: el registro."""
    estado: str            # verde | rojo | sin_evidencia | no_ejecutado
    cabecera: str
    marcas: dict           # test_id -> PASS|FAIL
    pasados: int
    fallados: int
    salida_chars: int
    truncada: bool


def resultado_de(salida):
    """El objeto explicito del ejecutor, para poder persistirlo tal cual."""
    estado, cabecera, marcas = veredicto(salida)
    return Ejecucion(estado=estado, cabecera=cabecera, marcas=marcas,
                     pasados=sum(1 for v in marcas.values() if v == "PASS"),
                     fallados=sum(1 for v in marcas.values() if v == "FAIL"),
                     salida_chars=len(salida or ""),
                     truncada="caracteres recortados" in (salida or ""))


def veredicto(salida):
    """(estado, detalle, marcas) — el unico sitio donde se decide si algo esta verde.

    Estaba re-derivado en ocho sitios con expresiones que no coincidian entre si: en
    pipeline.py un TIMEOUT era 'error' en una linea y 'verde' catorce lineas mas abajo.
    """
    salida = salida or ""
    cabecera = salida.split("\n", 1)[0]
    marcas = marcas_de(salida)
    if cabecera.startswith("NO EJECUTADO"):
        return "no_ejecutado", cabecera, marcas
    if cabecera.startswith("FALLO"):
        return "rojo", cabecera, marcas
    if cabecera.startswith("SIN EVIDENCIA"):
        return "sin_evidencia", cabecera, marcas
    if cabecera.startswith("TESTS EN VERDE"):
        return "verde", cabecera, marcas
    return "sin_evidencia", cabecera or "(sin salida)", marcas


# Solo estos nodos y estos operadores. Todo lo demas se rechaza por defecto:
# una lista blanca no se puede "olvidar" de prohibir algo nuevo, una negra si.
_OPERADORES = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
               ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
               ast.Mod: operator.mod, ast.Pow: operator.pow,
               ast.USub: operator.neg, ast.UAdd: operator.pos}
EXPONENTE_MAXIMO = 1000     # 2**10**9 no es un ataque de codigo, pero cuelga el proceso igual


def _evaluar(nodo):
    """Aritmetica y nada mas. Sin nombres, sin atributos, sin llamadas, sin indices."""
    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, bool) or not isinstance(nodo.value, (int, float)):
            raise ValueError(f"solo numeros: {nodo.value!r}")
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPERADORES:
        izq, der = _evaluar(nodo.left), _evaluar(nodo.right)
        if isinstance(nodo.op, ast.Pow) and (abs(der) > EXPONENTE_MAXIMO
                                             or abs(izq) > EXPONENTE_MAXIMO):
            raise ValueError(f"exponente demasiado grande (maximo {EXPONENTE_MAXIMO})")
        return _OPERADORES[type(nodo.op)](izq, der)
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _OPERADORES:
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.operand))
    raise ValueError(f"no permitido: {type(nodo).__name__}")


def calcular(expresion: str) -> str:
    """Aritmetica sobre una expresion que escribe el MODELO.

    Esto era `eval(expresion)` con un comentario que decia "en produccion nunca uses
    eval". Corre dentro del proceso del servidor, sin subproceso, sin timeout y sin
    aislamiento — al contrario que verificar_codigo, que tiene los tres. Para esta
    funcion, `__import__('os').environ['OPENROUTER_API_KEY']` era una expresion
    aritmetica perfectamente valida.
    """
    try:
        arbol = ast.parse(str(expresion).strip(), mode="eval")
    except SyntaxError as e:
        return f"No es una expresion valida: {e.msg}"
    try:
        return str(_evaluar(arbol.body))
    except ValueError as e:
        return f"Rechazado: {e}. Solo se permite aritmetica con numeros."
    except ZeroDivisionError:
        return "Division por cero."
    except (OverflowError, MemoryError) as e:
        return f"Numero fuera de rango: {type(e).__name__}"


def hora_actual() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# Lo que el agente usa para despachar: nombre -> funcion
SKILLS = {"buscar_en_docs": buscar_en_docs, "buscar_tradeoffs": buscar_tradeoffs,
          "buscar_fallos": buscar_fallos, "buscar_antipatrones": buscar_antipatrones,
          "cajas_relacionadas": cajas_relacionadas, "verificar_codigo": verificar_codigo,
          "calcular": calcular, "hora_actual": hora_actual}


def _tool(nombre, descripcion, arg=None, desc_arg=""):
    params = {"type": "object", "properties": {}}
    if arg:
        params["properties"][arg] = {"type": "string", "description": desc_arg}
        params["required"] = [arg]
    return {"type": "function",
            "function": {"name": nombre, "description": descripcion, "parameters": params}}


# Lo que el modelo recibe en cada llamada. La descripcion ES la señal de enrutamiento.
TOOLS = [
    _tool("buscar_en_docs",
          "Explica un concepto tecnico: que es, como funciona, como se implementa. "
          "Es la busqueda general sobre 19 cajas de backend senior (fundamentos, HTTP, APIs, "
          "bases de datos, arquitectura, seguridad, pagos, sistemas distribuidos, performance, "
          "fiabilidad, testing, observabilidad, cloud, devops, archivos, integraciones, "
          "logica de negocio, IA y system design). "
          "USA ESTA por defecto. No la uses si lo que necesitas es comparar opciones o "
          "anticipar fallos: para eso estan buscar_tradeoffs y buscar_fallos.",
          "query", "Terminos tecnicos a buscar"),

    _tool("buscar_tradeoffs",
          "Devuelve las FICHAS de decision de los conceptos relacionados con un tema: cuando usar "
          "cada cosa, sus limites, el anti-patron y el trade-off que aceptas. "
          "Usala cuando haya que ELEGIR entre alternativas o justificar una decision. "
          "Devuelve criterios de decision condensados, no explicaciones: si lo que hace falta es "
          "entender un concepto, usa buscar_en_docs.",
          "tema", "El tema o la decision a evaluar"),

    _tool("buscar_fallos",
          "Devuelve solo lo que puede SALIR MAL en un tema: modos de fallo conocidos, sintomas y "
          "mitigaciones. Usala para anticipar riesgos, revisar un diseño o depurar un incidente. "
          "No sirve para saber que es algo ni para elegir entre opciones.",
          "tema", "El componente o area cuyos fallos interesan"),

    _tool("cajas_relacionadas",
          "Devuelve el mapa de dependencias entre areas de conocimiento: que otras cajas referencia "
          "una caja y cuales la referencian a ella, con el peso de cada relacion. "
          "Usala para descubrir que areas tocar en un problema que cruza varias. "
          "Devuelve nombres de areas y numeros, NO contenido tecnico.",
          "caja", "Numero (01-19) o nombre en ingles de la caja: Fundamentals, Web & Protocols, APIs, "
          "Databases, Architecture, Security, Payments, Distributed Systems, Performance, Reliability, "
          "Testing, Observability, Cloud & Infrastructure, DevOps, Files & Data, Integrations, "
          "Business Logic, AI Backend, System Design"),

    _tool("buscar_antipatrones",
          "Devuelve los errores CONOCIDOS sobre un tema: que NO hacer y que hacer en su lugar. "
          "Usala al revisar codigo o un diseño, para contrastarlo contra los fallos ya documentados. "
          "No explica conceptos ni compara opciones.",
          "tema", "El componente o patron a contrastar"),

    {"type": "function", "function": {
        "name": "verificar_codigo",
        "description": (
            "EJECUTA codigo de verdad y devuelve su salida real y su exit code. "
            "Es la unica forma de DEMOSTRAR que algo funciona en vez de opinar. "
            "Usala para correr los tests de un codigo que acabas de escribir, sobre todo los de "
            "concurrencia, idempotencia y casos borde. "
            f"Interpretes permitidos EN ESTA MAQUINA: {', '.join(sorted(INTERPRETES)) or '(ninguno)'}. "
            "No uses ningun otro: el comando se rechaza sin ejecutarse y no demuestras nada. "
            "IMPRESCINDIBLE: cada test debe imprimir una linea exacta TEST:<id>:PASS o "
            "TEST:<id>:FAIL. Sin esos marcadores la ejecucion se reporta SIN EVIDENCIA por "
            "mucho que el codigo funcione, porque no hay forma de saber que se probo."),
        "parameters": {"type": "object", "properties": {
            "archivos": {"type": "object",
                         "description": "Mapa ruta -> contenido. Incluye el codigo Y los tests.",
                         "additionalProperties": {"type": "string"}},
            "comando": {"type": "string",
                        "description": f"Como ejecutarlo. Empieza por uno de: "
                                       f"{', '.join(sorted(INTERPRETES))}"}},
            "required": ["archivos", "comando"]}}},

    _tool("calcular",
          "Evalua una expresion matematica, por ejemplo '20 - 8' o '1847 * 293'.",
          "expresion", "Expresion aritmetica"),

    _tool("hora_actual", "Devuelve la fecha y hora actuales."),
]
