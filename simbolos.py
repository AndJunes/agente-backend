"""El indice de simbolos: que hay en un repo de Python y donde.

El RAG de rag.py busca en prosa (.md troceado por titulos). Esto busca en CODIGO,
y el codigo tiene estructura que la prosa no tiene: una funcion tiene nombre, firma,
docstring, archivo, clase contenedora y a quien llama. Se lee con `ast`, que es el
parser del propio Python, asi que no hay que adivinar nada con expresiones regulares.

Todo es determinista y local: cero dependencias, cero red, cero modelo. La misma
regla que el resto del proyecto (ver el candado de agent.py).

    python3 -c "import simbolos; s=simbolos.indexar('.'); print(simbolos.resumen(s))"
"""

import ast
import re
import unicodedata
from pathlib import Path
from typing import NamedTuple

# Carpetas que nunca son codigo del proyecto: indexarlas solo mete ruido y tarda.
IGNORADAS = {"__pycache__", ".git", ".venv", "venv", "node_modules", "site-packages",
             ".mypy_cache", ".pytest_cache", "build", "dist"}

# Palabras que no distinguen nada: salen en cualquier pregunta. Sin esto, "donde" y
# "como" puntuan archivos al azar. Es la version pobre del IDF que usa rag.py, pero
# aqui el indice es pequeño y las preguntas cortas, asi que una lista basta.
VACIAS = {"donde", "como", "cual", "cuales", "que", "quien", "cuando", "por", "para",
          "con", "sin", "del", "las", "los", "una", "unos", "unas", "esta", "este",
          "esto", "hace", "hacer", "estan", "son", "the", "and", "for", "with", "does",
          "where", "what", "how", "which", "was", "are", "use", "using"}

# El puente español -> ingles. ES UNA LISTA A MANO, no semantica: 23 entradas escritas
# por una persona. No "entiende" nada, no generaliza, y lo que no este aqui no se traduce.
# Existe porque el caso real del proyecto es preguntar en español sobre codigo escrito en
# ingles ("¿donde se valida el JWT?" -> validate_token), y la alternativa seria un modelo
# de embeddings: red, coste y una dependencia, por un problema que se resuelve con un dict.
# Si crece mucho, deja de ser honesto: entonces toca medir si un modelo compensa (config.py).
SINONIMOS = {
    "validar": ["validate", "verify", "check", "valid"],
    "verificar": ["verify", "validate", "check"],
    "comprobar": ["check", "verify", "assert"],
    "autenticar": ["auth", "authenticate", "login", "credential"],
    "autorizar": ["authorize", "permission", "grant", "allow"],
    "token": ["token", "jwt", "bearer"],
    "jwt": ["jwt", "token"],
    "sesion": ["session", "login", "cookie"],
    "contrasena": ["password", "secret", "credential"],
    "secreto": ["secret", "key", "token"],
    "firma": ["sign", "signature", "hmac"],
    "cifrar": ["encrypt", "hash", "cipher"],
    "usuario": ["user", "account", "profile"],
    "permiso": ["permission", "role", "scope"],
    "ruta": ["route", "path", "endpoint", "url"],
    "peticion": ["request", "req"],
    "respuesta": ["response", "reply"],
    "guardar": ["save", "store", "persist", "write"],
    "borrar": ["delete", "remove", "drop"],
    "buscar": ["search", "find", "query", "lookup"],
    "crear": ["create", "add", "new", "insert"],
    "actualizar": ["update", "modify", "patch"],
    "prueba": ["test", "assert", "check"],
}

# Cuanto vale cada señal, de mas fiable a menos: el nombre es lo que el autor eligio
# para el simbolo, el docstring es lo que escribio de paso, el archivo es casi geografia.
# (directo, por sinonimo). Los sinonimos pesan menos porque son una traduccion adivinada.
EXACTO = 100.0                  # la consulta ES el nombre del simbolo
W_NOMBRE = (10.0, 6.0)          # palabra del nombre partido
W_LLAMADAS = (4.0, 2.5)         # a quien llama: "donde se valida" incluye quien lo invoca
W_TEXTO = (3.0, 2.0)            # firma o primera linea del docstring
W_ARCHIVO = (1.5, 1.0)          # nombre del archivo
PESO_TEST = 0.5                 # un test menciona lo que prueba, pero no es donde se hace


class Simbolo(NamedTuple):
    nombre: str          # "validate_token"
    tipo: str            # "funcion" | "metodo" | "clase" | "modulo" | "test"
    archivo: str         # ruta relativa a la raiz indexada
    linea: int
    firma: str           # "validate_token(token: str) -> dict"
    doc: str             # primera linea del docstring, o ""
    padre: str           # clase contenedora, o ""
    llamadas: list       # nombres que este simbolo invoca (para relaciones)
    importa: list        # modulos que importa el archivo


# ── indexar ──────────────────────────────────────────────────────────────────

def _primera_linea(nodo):
    doc = ast.get_docstring(nodo) or ""
    return doc.strip().split("\n")[0].strip()


def _firma(nodo):
    """Reconstruye la firma desde el AST, con anotaciones y defaults incluidos."""
    args = ast.unparse(nodo.args)
    retorno = f" -> {ast.unparse(nodo.returns)}" if nodo.returns else ""
    return f"{nodo.name}({args}){retorno}"


def _firma_clase(nodo):
    bases = [ast.unparse(b) for b in nodo.bases] + [ast.unparse(k) for k in nodo.keywords]
    return f"class {nodo.name}({', '.join(bases)})" if bases else f"class {nodo.name}"


DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _llamadas(nodo, entrar_en_defs=True):
    """A quien invoca este nodo, en orden y sin repetir.

    De `self.repo.save(x)` se queda con "save": el nombre del metodo es lo que se busca,
    el receptor cambia segun donde estes. `entrar_en_defs=False` evita que una clase se
    atribuya las llamadas de todos sus metodos.
    """
    vistos, hijos = [], list(ast.iter_child_nodes(nodo))
    while hijos:
        h = hijos.pop(0)
        if isinstance(h, (*DEFS, ast.ClassDef)) and not entrar_en_defs:
            continue
        if isinstance(h, ast.Call):
            f = h.func
            nombre = f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)
            if nombre and nombre not in vistos:
                vistos.append(nombre)
        hijos.extend(ast.iter_child_nodes(h))
    return vistos


def _importa(arbol):
    """Los modulos que toca el archivo. Solo el primer tramo: 'os.path' -> 'os'."""
    mods = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            mods += [a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.append(n.module.split(".")[0])
    return sorted(set(mods))


def _es_archivo_de_test(ruta: Path):
    """Convencion, no magia: test_algo.py, algo_test.py, o cualquier cosa bajo tests/.

    Se marca el ARCHIVO, no el nombre de cada funcion: en este proyecto los tests se
    llaman `candado_muerde`, no `test_candado_muerde` (ver tests/test_cimientos.py).

    La ruta que se mira es la RELATIVA a la raiz indexada, no la absoluta: si no, un
    proyecto guardado en `~/tests/loquesea/` tendria todos sus simbolos marcados como
    test solo por donde esta en el disco. Lo destapo mover un fixture a `tests/fixtures/`:
    sus 14 funciones pasaron a contarse como tests sin cambiar una linea de su codigo.
    """
    ruta = Path(ruta)
    return (ruta.stem.startswith("test_") or ruta.stem.endswith("_test")
            or any(p in ("test", "tests") for p in ruta.parts[:-1]))


def _simbolos_de(ruta: Path, rel: str, arbol):
    importa = _importa(arbol)
    es_test = _es_archivo_de_test(rel)      # relativa a la raiz, no absoluta

    def simbolo(nombre, tipo, linea, firma, doc, padre, llamadas):
        return Simbolo(nombre, tipo, rel, linea, firma, doc, padre, llamadas, importa)

    salida = [simbolo(ruta.stem, "modulo", 1, "", _primera_linea(arbol), "",
                      _llamadas(arbol, entrar_en_defs=False))]

    for nodo in arbol.body:
        if isinstance(nodo, DEFS):
            salida.append(simbolo(nodo.name, "test" if es_test else "funcion", nodo.lineno,
                                  _firma(nodo), _primera_linea(nodo), "", _llamadas(nodo)))
        elif isinstance(nodo, ast.ClassDef):
            salida.append(simbolo(nodo.name, "clase", nodo.lineno, _firma_clase(nodo),
                                  _primera_linea(nodo), "",
                                  _llamadas(nodo, entrar_en_defs=False)))
            for hijo in nodo.body:      # solo un nivel: las funciones anidadas son detalle interno
                if isinstance(hijo, DEFS):
                    salida.append(simbolo(hijo.name, "test" if es_test else "metodo",
                                          hijo.lineno, _firma(hijo), _primera_linea(hijo),
                                          nodo.name, _llamadas(hijo)))
    return salida


def indexar(raiz) -> list:
    """Todos los simbolos de los .py bajo `raiz`, en orden de archivo.

    Tolerante a proposito: un archivo con la sintaxis rota (o codificado raro) se salta
    y el resto del indice se construye igual. Un indexador que revienta con un archivo a
    medio escribir es inutil justo cuando mas falta hace, que es mientras escribes codigo.
    """
    raiz = Path(raiz)
    if not raiz.is_dir():
        return []
    salida = []
    for ruta in sorted(raiz.rglob("*.py")):
        if IGNORADAS & set(ruta.parts):
            continue
        try:
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        except (SyntaxError, ValueError, UnicodeDecodeError, OSError, RecursionError):
            continue
        salida += _simbolos_de(ruta, ruta.relative_to(raiz).as_posix(), arbol)
    return salida


# ── buscar ───────────────────────────────────────────────────────────────────

def _normalizar(texto):
    """minusculas, sin acentos y sin puntuacion: '¿JWT?' y 'jwt' son lo mismo."""
    texto = unicodedata.normalize("NFD", str(texto).lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


# snake_case, camelCase, SCREAMING y siglas pegadas: "verifyJWT" -> ["verify", "jwt"]
_PARTES = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z0-9]+")


def palabras(nombre) -> list:
    """Parte un identificador en palabras. Es lo que hace comparable `validate_token`
    con 'validar' y `verifyJWT` con 'jwt'."""
    return [p.lower() for p in _PARTES.findall(str(nombre))]


def _coincide(a, b):
    """Iguales, o uno prefijo del otro con 4 letras minimo.

    Stemmer de pobre, pero es el que hace falta: 'token'/'tokens',
    'valida'/'validacion' y 'auth'/'authenticate' son la misma palabra para esto.
    """
    corta, larga = sorted((a, b), key=len)
    return corta == larga or (len(corta) >= 4 and larga.startswith(corta))


def _terminos(consulta):
    """(directos, por sinonimo). Los sinonimos que ya cubre un termino directo se
    descartan: 'valida' ya casa con 'validate' por prefijo, no hay que contarlo dos veces."""
    # >= 3 letras: "de", "se", "el" y companyia no distinguen nada y ademas casan con
    # identificadores reales ("de", "id"), que es como se cuela ruido en el top-k.
    directos = [p for p in _normalizar(consulta).split() if len(p) >= 3 and p not in VACIAS]
    expandidos = set()
    for p in directos:
        for clave, valores in SINONIMOS.items():
            if _coincide(p, clave):
                expandidos.update(valores)
    expandidos = {e for e in expandidos if not any(_coincide(e, d) for d in directos)}
    return directos, sorted(expandidos)


def _puntos(objetivo, directos, expandidos, pesos):
    """Cuenta una vez por termino de la consulta, no por palabra del objetivo:
    si no, un nombre largo gana solo por repetir."""
    if not objetivo:
        return 0.0
    directo, sinonimo = pesos
    p = sum(directo for t in directos if any(_coincide(t, o) for o in objetivo))
    return p + sum(sinonimo for e in expandidos if any(_coincide(e, o) for o in objetivo))


def puntuar(simbolo, consulta) -> float:
    """La puntuacion de un simbolo para una consulta. Determinista y explicable:
    nombre > palabras del nombre > a quien llama > firma/doc > archivo."""
    directos, expandidos = _terminos(consulta)
    if not directos:
        return 0.0
    q = _normalizar(consulta)
    if q == _normalizar(simbolo.nombre) or q.replace(" ", "") == _normalizar(simbolo.nombre).replace(" ", ""):
        return EXACTO

    nombre = palabras(simbolo.nombre)
    llamadas = [w for c in simbolo.llamadas for w in palabras(c)]
    texto = palabras(simbolo.firma) + _normalizar(simbolo.doc).split()
    archivo = palabras(simbolo.archivo.replace("/", " ").removesuffix(".py"))

    total = (_puntos(nombre, directos, expandidos, W_NOMBRE)
             + _puntos(llamadas, directos, expandidos, W_LLAMADAS)
             + _puntos(texto, directos, expandidos, W_TEXTO)
             + _puntos(archivo, directos, expandidos, W_ARCHIVO))
    return total * (PESO_TEST if simbolo.tipo == "test" else 1.0)


def buscar(simbolos, consulta, k=5) -> list:
    """Los k simbolos que mejor responden a la consulta, con su puntuacion.

    Los que puntuan 0 NO se devuelven: si nada casa, la respuesta correcta es la lista
    vacia. Rellenar el top-k con lo menos malo es como se cuelan respuestas inventadas.
    """
    puntuados = [(s, puntuar(s, consulta)) for s in simbolos]
    # desempate estable (archivo, linea) para que dos ejecuciones den lo mismo
    puntuados.sort(key=lambda par: (-par[1], par[0].archivo, par[0].linea))
    return [(s, p) for s, p in puntuados[:k] if p > 0]


def resumen(simbolos) -> dict:
    """Las cifras que dicen de un vistazo si el indice tiene sentido.

    Sirve de canario: si `archivos` o `tests` caen de golpe, algo dejo de parsearse.
    """
    tipos = [s.tipo for s in simbolos]
    return {"archivos": len({s.archivo for s in simbolos}),
            "modulos": tipos.count("modulo"),
            "clases": tipos.count("clase"),
            "funciones": tipos.count("funcion") + tipos.count("metodo"),
            "tests": tipos.count("test"),
            "importados": len({m for s in simbolos for m in s.importa})}
