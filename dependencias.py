"""Un import roto no es lo mismo que una dependencia que falta. Aquí se separan.

POR QUE IMPORTA TANTO

    Si se confunden, pasan las dos cosas malas a la vez: un proyecto FastAPI perfectamente
    escrito parece roto, y el bucle de reparación se pone a "arreglar" imports que estaban
    bien. Y al revés, un `from app.libros.repo import LibroRepo` contra un archivo que
    define `RepoLibros` se colaría como "ya se arreglará al instalar algo".

        import interno que no resuelve  -> ERROR del proyecto. Se repara.
        dependencia externa ausente     -> LIMITE de esta máquina. NO es un error.
                                           Pone un techo al estado, no lo hunde.

    Todo con `ast` y biblioteca estándar. Cero llamadas al modelo, cero coste.

UN DETALLE QUE COSTO DESCUBRIR

    `shutil.which("python3")` —el intérprete con el que Mirag EJECUTA el código— no es
    necesariamente el que corre los tests. En esta máquina son dos instalaciones distintas
    y una tiene `pydantic` y la otra no. Así que la presencia de una dependencia **se
    observa en el intérprete real**, no en el proceso actual. Medirlo en el sitio
    equivocado es, otra vez, medir una cosa y servir otra.
"""

import ast
import subprocess
import sys
from typing import NamedTuple

import skills

# gravedad: lo unico que mira el estado global
ERROR = "error"           # el proyecto esta mal
LIMITE = "limite"         # esta maquina no puede comprobarlo; el proyecto puede estar bien
AVISO = "aviso"           # conviene saberlo, no bloquea


class Importacion(NamedTuple):
    archivo: str
    linea: int
    modulo: str
    nombres: tuple
    nivel: int
    clase: str            # interno | estandar | externo


class Hallazgo(NamedTuple):
    clase: str
    gravedad: str
    archivo: str
    linea: int
    detalle: str


def exportados(texto):
    """Lo que un módulo define de verdad, leído del AST. No lo que promete el manifiesto."""
    try:
        arbol = ast.parse(texto)
    except SyntaxError:
        return frozenset()
    nombres = set()
    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nombres.add(nodo.name)
        elif isinstance(nodo, ast.Assign):
            nombres |= {d.id for d in nodo.targets if isinstance(d, ast.Name)}
        elif isinstance(nodo, ast.AnnAssign) and isinstance(nodo.target, ast.Name):
            nombres.add(nodo.target.id)
    return frozenset(nombres)


def tiene_getattr_de_modulo(texto):
    """PEP 562: un `__getattr__` a nivel de módulo puede crear símbolos en runtime.

    Con eso, "el símbolo no está en el AST" deja de ser prueba de que no exista.
    """
    try:
        arbol = ast.parse(texto)
    except SyntaxError:
        return False
    return any(isinstance(n, ast.FunctionDef) and n.name == "__getattr__" for n in arbol.body)


def modulos_de(proyecto):
    """`{"app.libros.repo": "app/libros/repo.py"}`, más los paquetes intermedios."""
    mapa, paquetes = {}, set()
    for archivo in proyecto.listar():
        if not archivo.modulo:
            continue
        mapa[archivo.modulo] = archivo.ruta
        partes = archivo.modulo.split(".")
        if partes[-1] == "__init__":
            mapa[".".join(partes[:-1])] = archivo.ruta
            partes = partes[:-1]
        for i in range(1, len(partes)):
            paquetes.add(".".join(partes[:i]))
    for p in paquetes:
        mapa.setdefault(p, "")          # paquete implícito, sin __init__.py propio
    return mapa


def importaciones(proyecto):
    """Todos los imports del proyecto, clasificados. También los de dentro de funciones."""
    mapa = modulos_de(proyecto)
    salida = []
    for archivo in proyecto.listar():
        if not archivo.ruta.endswith(".py"):
            continue
        try:
            arbol = ast.parse(archivo.texto)
        except SyntaxError:
            continue                    # la sintaxis la juzga otra fase, no esta
        paquete = ".".join(archivo.modulo.split(".")[:-1])
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    salida.append(_clasificar(archivo, nodo.lineno, alias.name, (), 0, mapa))
            elif isinstance(nodo, ast.ImportFrom):
                modulo = nodo.module or ""
                if nodo.level:          # relativo: se resuelve contra su paquete
                    base = paquete.split(".")[:len(paquete.split(".")) - (nodo.level - 1)]
                    modulo = ".".join([p for p in base if p] + ([modulo] if modulo else []))
                nombres = tuple(a.name for a in nodo.names)
                salida.append(_clasificar(archivo, nodo.lineno, modulo, nombres,
                                          nodo.level, mapa))
    return tuple(salida)


def _clasificar(archivo, linea, modulo, nombres, nivel, mapa):
    raiz = modulo.split(".")[0] if modulo else ""
    if modulo in mapa or (raiz and raiz in mapa):
        clase = "interno"
    elif raiz in sys.stdlib_module_names:
        clase = "estandar"
    else:
        clase = "externo"
    return Importacion(archivo.ruta, linea, modulo, nombres, nivel, clase)


def instaladas(raices, interprete=None):
    """¿Están instaladas, EN EL INTERPRETE QUE USA MIRAG? Se observa, no se supone.

    Se pregunta en un subproceso con el mismo binario que `skills.verificar_codigo`
    ejecutará, porque puede no ser el que corre este proceso.
    """
    raices = sorted({r for r in raices if r})
    if not raices:
        return {}
    binario = interprete or ("python3" if "python3" in skills.INTERPRETES else sys.executable)
    guion = ("import importlib.util as u\n"
             f"for m in {raices!r}:\n"
             "    print(m, u.find_spec(m) is not None, flush=True)\n")
    try:
        r = subprocess.run([binario, "-c", guion], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return {r_: None for r_ in raices}          # no se pudo observar: None, no False
    vistos = {}
    for linea in r.stdout.splitlines():
        partes = linea.split()
        if len(partes) == 2:
            vistos[partes[0]] = partes[1] == "True"
    return {r_: vistos.get(r_) for r_ in raices}


def declaradas(proyecto):
    """Las dependencias que el propio proyecto dice necesitar."""
    archivo = proyecto.obtener("requirements.txt")
    if not archivo:
        return frozenset()
    nombres = set()
    for linea in archivo.texto.splitlines():
        limpia = linea.split("#")[0].strip()
        if limpia and not limpia.startswith("-"):
            nombres.add(limpia.split("[")[0].split("=")[0].split(">")[0]
                        .split("<")[0].split("~")[0].strip().lower().replace("-", "_"))
    return frozenset(nombres)


def analizar(proyecto, interprete=None):
    """(importaciones, hallazgos). Los hallazgos llevan la gravedad que decide el estado."""
    imports = importaciones(proyecto)
    mapa = modulos_de(proyecto)
    por_ruta = {a.ruta: a for a in proyecto.listar()}
    hallazgos = []

    externas = {i.modulo.split(".")[0] for i in imports if i.clase == "externo"}
    presentes = instaladas(externas, interprete)
    declarado = declaradas(proyecto)

    for imp in imports:
        if imp.clase == "interno":
            destino = mapa.get(imp.modulo)
            if destino is None:
                hallazgos.append(Hallazgo(
                    "import_interno_roto", ERROR, imp.archivo, imp.linea,
                    f"importa {imp.modulo!r} y ese modulo no existe en el proyecto"))
                continue
            if imp.nombres and destino:
                fuente = por_ruta.get(destino)
                if fuente and not tiene_getattr_de_modulo(fuente.texto):
                    tiene = exportados(fuente.texto)
                    faltan = [n for n in imp.nombres
                              if n != "*" and n not in tiene and n not in mapa
                              and f"{imp.modulo}.{n}" not in mapa]
                    if faltan:
                        hallazgos.append(Hallazgo(
                            "simbolo_inexistente", ERROR, imp.archivo, imp.linea,
                            f"{destino} no define {', '.join(faltan)}"))
        elif imp.clase == "externo":
            raiz = imp.modulo.split(".")[0]
            if presentes.get(raiz) is False:
                hallazgos.append(Hallazgo(
                    "dependencia_ausente", LIMITE, imp.archivo, imp.linea,
                    f"{raiz!r} no esta instalado en esta maquina. El codigo puede estar "
                    f"bien; aqui no hay forma de comprobarlo."))
            if raiz.lower().replace("-", "_") not in declarado:
                hallazgos.append(Hallazgo(
                    "dependencia_no_declarada", AVISO, imp.archivo, imp.linea,
                    f"usa {raiz!r} y no aparece en requirements.txt"))
    # dedup conservando el orden
    vistos, unicos = set(), []
    for h in hallazgos:
        clave = (h.clase, h.archivo, h.detalle)
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(h)
    return imports, tuple(unicos)


def peor(hallazgos):
    if any(h.gravedad == ERROR for h in hallazgos):
        return ERROR
    if any(h.gravedad == LIMITE for h in hallazgos):
        return LIMITE
    return AVISO if hallazgos else ""


if __name__ == "__main__":
    import proyecto as P
    p = P.desde_dict("demo", {
        "app/__init__.py": "",
        "app/bd.py": "import sqlite3\ndef conectar(ruta):\n    return sqlite3.connect(ruta)\n",
        "app/main.py": ("import json\n"
                        "from app.bd import conectar\n"
                        "from app.bd import inexistente\n"
                        "from app.no_existe import algo\n"
                        "from fastapi import FastAPI\n"
                        "import pydantic\n"),
        "requirements.txt": "fastapi\n"})
    imports, hallazgos = analizar(p)
    print(f"{len(imports)} imports · interprete observado: "
          f"{'python3' if 'python3' in skills.INTERPRETES else 'este proceso'}\n")
    for i in imports:
        print(f"  {i.clase:<9} {i.modulo:<22} {i.archivo}:{i.linea}")
    print(f"\n{len(hallazgos)} hallazgos:")
    for h in hallazgos:
        print(f"  [{h.gravedad:<6}] {h.clase:<24} {h.detalle}")
    print(f"\n  gravedad mayor: {peor(hallazgos)!r}")
