"""El RetrievalPlan: que hay que buscar, donde, y que etapas hacen falta.

DOS IDEAS QUE SOSTIENEN ESTE MODULO

1. No cuesta una llamada. El plan sale de la llamada que rapido.py ya hace para
   razonar. Pedirle al modelo una llamada aparte solo para planificar la busqueda
   romperia el techo de 2-3 llamadas de todo el camino barato.

2. No se depende del formato del modelo. Un plan que solo funciona si el modelo
   escribe exactamente el JSON que le pedimos es un plan que se cae el martes. Aqui
   se aceptan siete formas distintas (ver leer()) y, si ninguna cuela, hay un plan
   determinista sacado de la propia peticion: peor, pero siempre existe.

El plan tampoco DECIDE que etapas se ejecutan. Dice que haria falta (needs_graph,
needs_symbols); quien decide es config.activar(), que mira lo que esta medido.
"""

import json
import re
from typing import NamedTuple

import rag

PROFUNDIDADES = ("shallow", "normal", "deep")

# señales para deducir el plan sin modelo: deterministas y a la vista
# ── ¿me estan pidiendo codigo? ──────────────────────────────────────────────
# La version anterior era una sola lista de palabras y fallaba por los dos lados: acertaba
# 5 de 11 peticiones reales de codigo y se disparaba en 5 de 49 preguntas conceptuales.
# "Rate limiter por usuario con token bucket, seguro ante peticiones concurrentes. Node.js."
# no lleva verbo imperativo, asi que el usuario recibia prosa donde pedia codigo; y
# "necesito rate limiting en mi endpoint", que es una consulta, disparaba por "endpoint".
#
# Lo que separa de verdad no es el vocabulario tecnico (lo comparten las dos) sino la FORMA:
# una peticion de codigo nombra un artefacto o un runtime y NO empieza preguntando.
# Medido sobre 11 peticiones reales y las 49 consultas de eval: 11/11 y 1 falso positivo.
FIRMA = re.compile(r"\w+\.(py|js|ts|sql|json)\b|\w+\s*\([^)]*\)")
# El imperativo rioplatense lleva la tilde en la ultima silaba y NO casaba con nada:
# "Creá una API REST" daba needs_code=False y "Crea una API REST" daba True — la unica
# diferencia era el acento. Lo mismo con agregá, separá, implementá, armá, sumá, pasame.
# El usuario escribe asi, asi que la mitad de sus peticiones de codigo recibian prosa.
VERBO_CODIGO = re.compile(
    r"\b(implement[aá]|implementar|escrib[eií]|cre[aá]|crear|constru[yií]|construir|"
    r"program[aá]|desarroll[aáe]|refactoriz[aá]|codific[aá]|gener[aá]|arm[aá]|hac[eé]|"
    r"agreg[aá]|añad[eií]|sum[aá]|separ[aá]|prepar[aá]|mont[aá]|"
    r"dame (el|la) (codigo|código|implementacion|implementación)|hazme|haceme|pasame)\b",
    re.I)
ARTEFACTO = re.compile(r"\b(funcion|función|function|clase|class|script|modulo|módulo)\b", re.I)
RUNTIME = re.compile(r"\b(node\.?js|python|typescript|javascript|golang|java|ruby|rust|"
                     r"\.net|c\+\+)\b", re.I)
# postgres y redis NO estan aqui a proposito: son almacenes sobre los que se PREGUNTA tanto
# como se programa, y meterlos devolvia "tipos de indices en postgres" como peticion de codigo.
# El "¿" inicial hacia que el ancla no pegara: "¿que es una funcion pura?" salia como
# peticion de codigo por la palabra "funcion". Se saltan los signos de apertura.
PREGUNTA = re.compile(r'''^[\s¿¡"'(]*(como|cómo|qu[eé]|cu[aá]l|cu[aá]ndo|por qu[eé]|'''
                      r'''d[oó]nde|qui[eé]n|necesito|conviene|vale la pena)\b''', re.I)


# ── ¿me piden un PROYECTO, no un archivo? ───────────────────────────────────
# La diferencia no es el tamaño: es que hay ESTRUCTURA. Un proyecto nombra capas que
# tienen que convivir, o pide explicitamente el andamiaje (carpetas, README, ZIP).
# Se mide contra tres conjuntos, como `pide_codigo`: peticiones de proyecto, peticiones
# de un archivo suelto (banco.TAREAS) y las 49 consultas conceptuales de eval.
ANDAMIAJE = re.compile(r"\b(proyecto|scaffold\w*|andamiaje|boilerplate|monorepo|"
                       r"estructura de (carpetas|directorios|archivos)|"
                       r"[aá]rbol de (archivos|carpetas)|listo para descargar|"
                       r"descargable|\.zip\b|en un zip)\b", re.I)
CAPAS = re.compile(r"\b(router|routers|service|services|servicio[s]?|repository|repositorio[s]?|"
                   r"controller[s]?|controlador(es)?|schema[s]?|esquema[s]?|model[eo]?[s]?|"
                   r"dominio[s]?|capa[s]?|middleware|entrypoint)\b", re.I)
COMPUESTO = re.compile(r"\b(api rest|rest api|api completa|crud|backend|micro[- ]?servicio|"
                       r"aplicaci[oó]n|webapp|cli completa|bot de \w+)\b", re.I)
ACOMPAÑA = re.compile(r"\b(readme|requirements\.txt|package\.json|dockerfile|pyproject|"
                      r"\.env|tests?\b|pruebas)\b", re.I)
MINIMO_CAPAS = 2


def pide_proyecto(peticion):
    """¿Piden un proyecto entero, con su estructura? Por forma, como `pide_codigo`.

    Invariante que fija un test: `pide_proyecto(q)` implica `pide_codigo(q)`. Si se
    contradijeran, el pipeline tomaria la rama de proyecto sin pedir codigo, o al reves.
    """
    peticion = peticion or ""
    if PREGUNTA.search(peticion):
        return False                   # "¿que es un CRUD?" no es un encargo
    if ANDAMIAJE.search(peticion):
        return True                    # lo piden por su nombre
    capas = {m.group(0).lower() for m in CAPAS.finditer(peticion)}
    if len(capas) >= MINIMO_CAPAS:
        return True                    # nombran piezas que tienen que convivir
    return bool(COMPUESTO.search(peticion)) and bool(capas or ACOMPAÑA.search(peticion))


def pide_codigo(peticion):
    """¿Esta peticion pide que se escriba codigo? Por forma, no por vocabulario."""
    peticion = peticion or ""
    if FIRMA.search(peticion):
        return True                    # un `calculator.py` o un `f(a, b)` no es una pregunta
    if PREGUNTA.search(peticion):
        return False                   # empieza preguntando: es una consulta
    return bool(VERBO_CODIGO.search(peticion) or ARTEFACTO.search(peticion)
                or RUNTIME.search(peticion))
PISTAS_SIMBOLOS = re.compile(
    r"\b(donde|dónde|en que archivo|en qué archivo|que archivo|busca en el codigo|"
    r"quien llama|quién llama|definid[oa]|se valida|se usa|modulo|módulo)\b", re.I)
PISTAS_GRAFO = re.compile(
    r"\b(y (ademas|además|tambien|también)|relacion|relación|depende|impacto|"
    r"como afecta|cómo afecta|entre .+ y |combinar|integrar)\b", re.I)
PISTAS_PROFUNDO = re.compile(
    r"\b(diseña|diseñar|arquitectura|compara|comparar|trade-?off|evalua|evaluar|"
    r"por que|por qué|justifica)\b", re.I)


class PlanRecuperacion(NamedTuple):
    goal: str = ""
    domains: list = ()            # cajas: ["04", "08"]
    technologies: list = ()
    required_knowledge: list = ()
    artifact_types: list = ()     # ficha / fallo / antipatron / concepto
    exclude: list = ()
    depth: str = "normal"
    needs_code: bool = False
    needs_graph: bool = False
    needs_symbols: bool = False
    # Default al final del NamedTuple a proposito: nada de lo que construya un plan por
    # posicion se rompe, y las 18 suites siguen pasando sin tocarse.
    needs_project: bool = False   # ¿piden un proyecto entero, no un archivo?
    origen: str = "?"             # de donde salio: para la traza y la UI

    def resumen(self):
        """Una linea para la UI: que va a buscar y donde."""
        partes = []
        if self.domains:
            partes.append("cajas " + ", ".join(self.domains))
        if self.technologies:
            partes.append("tecnologias: " + ", ".join(self.technologies))
        if self.required_knowledge:
            partes.append(str(len(self.required_knowledge)) + " conceptos")
        extras = [n for n, v in (("proyecto", self.needs_project),
                                 ("codigo", self.needs_code), ("grafo", self.needs_graph),
                                 ("simbolos", self.needs_symbols)) if v]
        if extras:
            partes.append("necesita " + "+".join(extras))
        return " · ".join(partes) or "sin acotar"


def _lista(valor, limite=12):
    """Lo que venga -> lista de strings limpia. El modelo manda de todo."""
    if valor is None:
        return []
    if isinstance(valor, str):
        valor = re.split(r"[,;\n]", valor)
    elif isinstance(valor, dict):
        valor = list(valor.values())
    elif not isinstance(valor, (list, tuple, set)):
        valor = [valor]
    salida = []
    for x in valor:
        s = (x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)).strip(" \t\"'*·-")
        if s and s.lower() not in ("none", "null", "n/a", "-"):
            salida.append(s)
    return salida[:limite]


def _booleano(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "si", "sí", "yes", "1")
    return bool(valor)


def _cajas(valores):
    """Normaliza a numeros de caja de dos digitos, tolerando nombres."""
    nombres = {t.caja.split("·")[1].strip().lower(): t.caja.split("·")[0].strip()
               for t in rag.TROZOS}
    salida = []
    for v in _lista(valores):
        if (m := re.search(r"\b(\d{1,2})\b", str(v))):
            n = m.group(1).zfill(2)
            if any(t.caja.startswith(n) for t in rag.TROZOS):
                salida.append(n)
                continue
        clave = str(v).strip().lower()
        for nombre, numero in nombres.items():
            if clave and (clave in nombre or nombre in clave):
                salida.append(numero)
                break
    return list(dict.fromkeys(salida))[:6]


def _json_suelto(texto):
    """Saca el primer objeto JSON de un texto que puede traerlo envuelto en prosa.

    Recorta por llaves equilibradas en vez de por regex: el modelo mete objetos
    anidados y un `\\{.*\\}` codicioso o perezoso se equivoca en los dos sentidos.
    """
    inicio = texto.find("{")
    while inicio != -1:
        nivel, en_cadena, escapado = 0, False, False
        for i in range(inicio, len(texto)):
            c = texto[i]
            if escapado:
                escapado = False
                continue
            if c == "\\":
                escapado = True
            elif c == '"':
                en_cadena = not en_cadena
            elif not en_cadena:
                if c == "{":
                    nivel += 1
                elif c == "}":
                    nivel -= 1
                    if nivel == 0:
                        try:
                            return json.loads(texto[inicio:i + 1], strict=False)
                        except json.JSONDecodeError:
                            break
        inicio = texto.find("{", inicio + 1)
    return None


def _reparar(texto):
    """Ultimo intento con un JSON cortado: max_tokens corta a mitad de objeto.

    Se cierran comillas y llaves pendientes y se tira lo que quedo a medias. No
    siempre sale, pero rescata la mayoria de los cortes por longitud.
    """
    inicio = texto.find("{")
    if inicio == -1:
        return None
    t = texto[inicio:]

    # Se recorre anotando el ultimo punto SANO: una coma o un cierre fuera de cadena,
    # junto con los corchetes que quedaban abiertos ahi. Cortar por ese punto y cerrar
    # esa pila da siempre un JSON valido, aunque el corte cayera dentro de un array
    # anidado ('"technologies":[' a medias, que es lo que pasa de verdad).
    pila, en_cadena, escapado, sanos = [], False, False, []
    for i, c in enumerate(t):
        if escapado:
            escapado = False
        elif c == "\\":
            escapado = True
        elif c == '"':
            en_cadena = not en_cadena
        elif not en_cadena:
            if c in "{[":
                pila.append("}" if c == "{" else "]")
            elif c in "}]":
                if pila:
                    pila.pop()
                sanos.append((i + 1, tuple(pila)))
            elif c == ",":
                sanos.append((i, tuple(pila)))

    for corte, abiertos in reversed(sanos):
        intento = t[:corte] + "".join(reversed(abiertos))
        try:
            return json.loads(intento, strict=False)
        except json.JSONDecodeError:
            continue
    return None


# El plan que no acota nada: MIRAG_RETRIEVAL_PLAN=off y el brazo baseline de los bancos.
# Tiene origen propio para que la traza no diga "deducido" sobre un plan que nadie dedujo.
VACIO = PlanRecuperacion(origen="sin plan (RETRIEVAL_PLAN=off)")


def deducir(peticion, k=4):
    """El plan determinista: sin modelo, sin formato que parsear, siempre disponible.

    Las cajas salen de donde vinieron los mejores trozos de una busqueda directa.
    Es peor que un plan razonado, pero no depende de nadie: es el suelo.
    """
    vistas = dict.fromkeys(t.caja.split("·")[0].strip()
                           for t, _ in rag._ranking(rag.TROZOS, peticion, k * 2))
    return PlanRecuperacion(
        goal=peticion.strip()[:200],
        domains=list(vistas)[:k],
        technologies=[],
        required_knowledge=[p for p in re.findall(r"\w{4,}", peticion.lower())][:8],
        artifact_types=[],
        exclude=[],
        depth="deep" if PISTAS_PROFUNDO.search(peticion) else "normal",
        needs_code=pide_codigo(peticion),
        needs_project=pide_proyecto(peticion),
        needs_graph=bool(PISTAS_GRAFO.search(peticion)),
        needs_symbols=bool(PISTAS_SIMBOLOS.search(peticion)),
        origen="deducido de la peticion (0 llamadas)")


def leer(respuesta, peticion="", k=4):
    """Convierte lo que sea que haya dicho el modelo en un plan utilizable.

    Formas que se aceptan, por orden de intento:
      1. un dict ya parseado          5. JSON cortado a medias (se repara)
      2. JSON valido en texto         6. el formato viejo "CAJAS: 03, 07"
      3. JSON envuelto en prosa       7. nada / basura -> plan deducido
      4. JSON en un bloque ```json
    Nunca lanza: si no entiende nada, devuelve el plan determinista.
    """
    suelo = deducir(peticion or "", k) if peticion else PlanRecuperacion(origen="vacio")
    if respuesta is None:
        return suelo._replace(origen="sin respuesta del modelo → plan deducido")

    crudo, origen = None, ""
    if isinstance(respuesta, dict):
        crudo, origen = respuesta, "dict del modelo"
    else:
        texto = str(respuesta)
        if (m := re.search(r"```(?:json)?\s*(.+?)```", texto, re.S)):
            texto_json = m.group(1)
            origen_bloque = "bloque ```json"
        else:
            texto_json, origen_bloque = texto, "JSON en el texto"
        try:
            crudo, origen = json.loads(texto_json, strict=False), origen_bloque
        except (json.JSONDecodeError, ValueError):
            if (crudo := _json_suelto(texto)) is not None:
                origen = "JSON rodeado de prosa"
            elif (crudo := _reparar(texto)) is not None:
                origen = "JSON cortado, reparado"

    if not isinstance(crudo, dict):
        # el formato viejo: una linea "CAJAS: 03, 07" suelta en la prosa
        if isinstance(respuesta, str) and (m := re.search(r"CAJAS\s*:?\**(.*)$",
                                                          respuesta, re.I | re.M)):
            nums = re.findall(r"\b(\d{1,2})\b", m.group(1))
            if nums:
                return suelo._replace(domains=[n.zfill(2) for n in dict.fromkeys(nums)][:k],
                                      origen="formato viejo CAJAS:")
        return suelo._replace(origen=f"no se entendio la respuesta → {suelo.origen}")

    # un dict que no trae NINGUN campo conocido no es un plan
    conocidos = set(PlanRecuperacion._fields)
    if not (set(crudo) & conocidos):
        return suelo._replace(origen=f"JSON sin campos de plan → {suelo.origen}")

    depth = str(crudo.get("depth", "normal")).strip().lower()
    dominios = _cajas(crudo.get("domains") or crudo.get("cajas"))
    return PlanRecuperacion(
        goal=str(crudo.get("goal") or peticion or "").strip()[:200],
        domains=dominios or suelo.domains,      # un plan sin cajas no acota nada: usa el suelo
        technologies=_lista(crudo.get("technologies")),
        required_knowledge=_lista(crudo.get("required_knowledge")),
        artifact_types=_lista(crudo.get("artifact_types")),
        exclude=_cajas(crudo.get("exclude")),
        depth=depth if depth in PROFUNDIDADES else "normal",
        needs_code=_booleano(crudo.get("needs_code", suelo.needs_code)),
        needs_graph=_booleano(crudo.get("needs_graph", suelo.needs_graph)),
        needs_symbols=_booleano(crudo.get("needs_symbols", suelo.needs_symbols)),
        origen=origen + ("" if dominios else " (sin cajas: se usan las deducidas)"))


# El schema que se le pide al modelo. Va como tool en la llamada que YA se hace.
HERRAMIENTA = {"type": "function", "function": {
    "name": "plan_de_busqueda",
    "description": "Antes de responder, di QUE hay que buscar y donde. Una sola vez.",
    "parameters": {"type": "object", "properties": {
        "goal": {"type": "string", "description": "que hay que resolver, en una linea"},
        "domains": {"type": "array", "items": {"type": "string"},
                    "description": "numeros de caja (01-19) donde mirar"},
        "technologies": {"type": "array", "items": {"type": "string"}},
        "required_knowledge": {"type": "array", "items": {"type": "string"},
                               "description": "conceptos que hacen falta si o si"},
        "artifact_types": {"type": "array", "items": {"type": "string"},
                           "description": "concepto | ficha | fallo | antipatron"},
        "exclude": {"type": "array", "items": {"type": "string"}},
        "depth": {"type": "string", "enum": list(PROFUNDIDADES)},
        "needs_code": {"type": "boolean"},
        "needs_graph": {"type": "boolean",
                        "description": "true solo si hace falta relacionar varias areas"},
        "needs_symbols": {"type": "boolean",
                          "description": "true solo si hay que buscar en codigo existente"}},
        "required": ["goal", "domains"]}}}
