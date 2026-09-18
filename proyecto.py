"""Un proyecto entero como UN objeto: el artefacto del que sale todo lo demás.

POR QUE EXISTE

    Mirag sabía entregar archivos sueltos. `rapido.guardar` los escribe en `salida/`, y
    para hacerlo **aplana las rutas** (`destino / Path(ruta).name`) y **vacía la carpeta
    entera** antes. Con un proyecto eso es fatal: `app/libros/router.py` y
    `tests/test_libros.py` colisionarían en dos archivos llamados igual, después de
    haber borrado lo anterior. Así que un proyecto NO pasa por ahí.

    El artefacto es la fuente única: el workspace donde se ejecuta, el manifiesto que se
    enseña y el ZIP que se descarga salen todos de él. Si cada uno se construyera por su
    lado, volvería el defecto que costó dos fases cerrar — medir una cosa y servir otra.

LO QUE GARANTIZA Y LO QUE NO

    SI: que ninguna ruta escape del proyecto, que el árbol sea inmutable una vez sellado,
        y que los hashes se calculen UNA vez sobre los bytes exactos.

    NO: no juzga si el código es bueno, no lo ejecuta y no decide si está verificado.
        Eso es de `verificacion_proyecto.py`, y el veredicto lo sigue dando la ejecución.
"""

import hashlib
import re
import unicodedata
from pathlib import Path, PurePosixPath
from typing import NamedTuple

AQUI = Path(__file__).resolve().parent
# El unico subarbol de Mirag donde un proyecto generado puede aterrizar. Cada artefacto
# tiene ahi su carpeta con un id opaco; nadie mas escribe en ella.
AREA_ARTEFACTOS = AQUI / "artefactos"

# Topes. No son estética: un modelo que se va de madre no puede llenar el disco ni
# generar un ZIP que nadie pueda abrir.
MAXIMO_ARCHIVOS = 40
MAXIMA_PROFUNDIDAD = 6
MAXIMO_RUTA = 120
MAXIMO_ARCHIVO = 60 * 1024
MAXIMO_TOTAL = 400 * 1024

# Lista BLANCA de segmentos, no negra: se acepta lo conocido y se rechaza el resto.
# Es el mismo criterio que `skills._OPERADORES` usa para la calculadora, y por la misma
# razon: enumerar lo prohibido siempre deja algo fuera.
SEGMENTO = re.compile(r"\A[A-Za-z0-9_][A-Za-z0-9._-]{0,63}\Z")
OCULTOS_PERMITIDOS = {".gitignore", ".env.example", ".dockerignore", ".editorconfig"}
PROHIBIDOS = {"__pycache__", ".git", ".env", "node_modules", ".venv", "venv", ".DS_Store"}
EXTENSIONES = {".py", ".js", ".ts", ".json", ".md", ".txt", ".sql", ".yml", ".yaml",
               ".toml", ".cfg", ".ini", ".html", ".css", ".example", ".gitignore"}


class RutaProhibida(ValueError):
    """Una ruta que no puede existir dentro de un proyecto."""


class DestinoProhibido(ValueError):
    """Un intento de materializar el proyecto encima de Mirag."""


def ruta_segura(ruta):
    """La ruta normalizada, o `RutaProhibida`. **El único sitio donde nace una ruta.**

    Nada que venga del modelo llega al disco sin pasar por aquí. Rechaza rutas absolutas,
    `..`, `~`, NUL, unidades de Windows, segmentos vacíos y los nombres que nunca deben
    entrar en un proyecto generado (`__pycache__`, `.git`, `.env`).
    """
    if not isinstance(ruta, str) or not ruta.strip():
        raise RutaProhibida(f"ruta vacia o no es texto: {ruta!r}")
    cruda = ruta.strip().replace("\\", "/")
    if "\x00" in cruda:
        raise RutaProhibida("la ruta lleva un NUL")
    if cruda.startswith("/") or cruda.startswith("~") or re.match(r"\A[A-Za-z]:", cruda):
        raise RutaProhibida(f"ruta absoluta: {ruta!r}")
    if len(cruda) > MAXIMO_RUTA:
        raise RutaProhibida(f"ruta de {len(cruda)} caracteres, el tope son {MAXIMO_RUTA}")

    partes = [p for p in PurePosixPath(cruda).parts]
    if not partes:
        raise RutaProhibida(f"ruta sin segmentos: {ruta!r}")
    if len(partes) > MAXIMA_PROFUNDIDAD:
        raise RutaProhibida(f"{len(partes)} niveles, el tope son {MAXIMA_PROFUNDIDAD}")
    for parte in partes:
        if parte in ("..", ".", ""):
            raise RutaProhibida(f"segmento no permitido {parte!r} en {ruta!r}")
        if parte in PROHIBIDOS:
            raise RutaProhibida(f"{parte!r} nunca entra en un proyecto generado")
        if parte.startswith(".") and parte not in OCULTOS_PERMITIDOS:
            raise RutaProhibida(f"archivo oculto no permitido: {parte!r}")
        if parte not in OCULTOS_PERMITIDOS and not SEGMENTO.match(parte):
            raise RutaProhibida(f"segmento con caracteres no permitidos: {parte!r}")
    if PurePosixPath(partes[-1]).suffix.lower() not in EXTENSIONES \
            and partes[-1] not in OCULTOS_PERMITIDOS:
        raise RutaProhibida(f"extension no permitida en {partes[-1]!r}")
    return "/".join(partes)


def nombre_seguro(nombre):
    """Un nombre de proyecto usable como carpeta y como nombre de archivo.

    Se sanea aquí y se vuelve a comprobar antes de escribirlo en una cabecera HTTP: un
    `\\r\\n` en el nombre partiría `Content-Disposition` en dos.
    """
    limpio = unicodedata.normalize("NFKD", str(nombre or "")).encode("ascii", "ignore").decode()
    limpio = re.sub(r"[^A-Za-z0-9._-]+", "-", limpio).strip("-._").lower()
    limpio = re.sub(r"-{2,}", "-", limpio)[:48]
    return limpio or "proyecto"


def sha(datos):
    """sha256 COMPLETO de unos bytes.

    Sin truncar, al contrario que `cache.py`, y la diferencia importa: allí el hash
    DETECTA cambios y 16 hex sobran; aquí el hash es la PRUEBA de que el ZIP que se
    descarga es el que se verificó. Truncar convertiría una prueba en una heurística.
    """
    return hashlib.sha256(datos).hexdigest()


class Archivo(NamedTuple):
    ruta: str
    datos: bytes
    tipo: str = "codigo"        # codigo | test | entrypoint | config | doc
    proposito: str = ""
    exporta: tuple = ()
    depende_de: tuple = ()
    grupo: str = ""

    @property
    def sha(self):
        return sha(self.datos)

    @property
    def bytes(self):
        return len(self.datos)

    @property
    def lineas(self):
        return self.datos.count(b"\n") + (0 if self.datos.endswith(b"\n") else 1)

    @property
    def texto(self):
        return self.datos.decode("utf-8", "replace")

    @property
    def modulo(self):
        """"app/libros/repo.py" -> "app.libros.repo". Vacío si no es Python."""
        if not self.ruta.endswith(".py"):
            return ""
        return self.ruta[:-3].replace("/", ".")


class Proyecto:
    """El artefacto. Mutable mientras se genera; se sella antes de verificar."""

    def __init__(self, nombre, espec=None):
        self.nombre = nombre_seguro(nombre)
        self.espec = espec
        self._archivos = {}          # ruta -> Archivo, en orden de inserción
        self._sellado = False

    # ── construcción ────────────────────────────────────────────────────────

    def añadir(self, ruta, contenido, **ficha):
        """Añade o reemplaza un archivo. La ruta pasa por `ruta_segura` siempre."""
        if self._sellado:
            raise RuntimeError("el proyecto esta sellado: una reparacion crea uno nuevo")
        limpia = ruta_segura(ruta)
        datos = contenido.encode("utf-8") if isinstance(contenido, str) else bytes(contenido)
        if len(datos) > MAXIMO_ARCHIVO:
            raise RutaProhibida(f"{limpia}: {len(datos)} bytes, el tope son {MAXIMO_ARCHIVO}")
        nuevo = dict(self._archivos)
        nuevo[limpia] = Archivo(limpia, datos, **ficha)
        if len(nuevo) > MAXIMO_ARCHIVOS:
            raise RutaProhibida(f"{len(nuevo)} archivos, el tope son {MAXIMO_ARCHIVOS}")
        total = sum(a.bytes for a in nuevo.values())
        if total > MAXIMO_TOTAL:
            raise RutaProhibida(f"{total} bytes en total, el tope son {MAXIMO_TOTAL}")
        self._archivos = nuevo
        return nuevo[limpia]

    def sellar(self):
        """A partir de aquí el árbol no cambia. Lo que se verifique será lo que se empaquete."""
        self._sellado = True
        return self

    # ── consulta ────────────────────────────────────────────────────────────

    def obtener(self, ruta):
        """El archivo, o None. **Consultar nunca lanza.**

        Estricto al escribir, tolerante al leer: una ruta que no puede existir es
        simplemente una ruta que no esta. Cuando esto lanzaba, una dependencia mal
        declarada por el modelo (`depende_de: ["app/libros/api"]`, sin extension)
        reventaba la generacion entera en vez de ser un hueco en el contrato.
        """
        try:
            return self._archivos.get(ruta_segura(ruta))
        except RutaProhibida:
            return None

    def listar(self, tipo=None):
        return tuple(a for a in sorted(self._archivos.values(), key=lambda x: x.ruta)
                     if tipo is None or a.tipo == tipo)

    def rutas(self):
        return tuple(sorted(self._archivos))

    def planos(self):
        """`{ruta: texto}`, que es EXACTAMENTE lo que consume `skills.verificar_codigo`.

        Ese ya valida con `is_relative_to` y crea subdirectorios con `mkdir(parents=True)`,
        o sea que sabe ejecutar árboles desde antes de que existiera este módulo. Por eso
        el puente es un dict y no un formato nuevo.
        """
        return {a.ruta: a.texto for a in self.listar()}

    def arbol(self):
        """Los directorios implícitos, derivados de las rutas. Para enseñarlo."""
        nodos = {}
        for ruta in self.rutas():
            actual = nodos
            partes = ruta.split("/")
            for parte in partes[:-1]:
                actual = actual.setdefault(parte + "/", {})
            actual[partes[-1]] = None
        return nodos

    @property
    def totales(self):
        archivos = self.listar()
        directorios = {"/".join(a.ruta.split("/")[:-1]) for a in archivos} - {""}
        return {"archivos": len(archivos), "directorios": len(directorios),
                "lineas": sum(a.lineas for a in archivos),
                "bytes": sum(a.bytes for a in archivos)}

    # ── salida a disco ──────────────────────────────────────────────────────

    def materializar(self, destino):
        """Escribe el árbol. Nunca encima de Mirag ni de `salida/`.

        Se permiten exactamente dos sitios: cualquier ruta FUERA del directorio de Mirag
        (un temporal, por ejemplo) y el área de artefactos, que es un subárbol dedicado
        donde cada proyecto tiene su propia carpeta con un id opaco. Todo lo demás se
        rechaza: un proyecto generado no puede escribir sobre los módulos del agente ni
        sobre `salida/`, que además se vacía entera en cada petición.
        """
        destino = Path(destino).resolve()
        dentro_de_mirag = destino == AQUI or AQUI in destino.parents
        if dentro_de_mirag and not destino.is_relative_to(AREA_ARTEFACTOS):
            raise DestinoProhibido(f"un proyecto no se escribe dentro de Mirag: {destino}")
        destino.mkdir(parents=True, exist_ok=True)
        for archivo in self.listar():
            ruta = (destino / archivo.ruta).resolve()
            if not ruta.is_relative_to(destino):      # el segundo cinturón, como en skills.py
                raise RutaProhibida(f"escapa del destino: {archivo.ruta}")
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(archivo.datos)           # bytes, nunca write_text:
        return destino                                # write_text traduce saltos de línea


def desde_dict(nombre, archivos, espec=None):
    """Atajo: `{ruta: contenido}` -> Proyecto. Lo que devuelve el modelo."""
    p = Proyecto(nombre, espec)
    for ruta, contenido in archivos.items():
        p.añadir(ruta, contenido)
    return p


if __name__ == "__main__":
    p = desde_dict("Libros API!!", {
        "app/__init__.py": "", "app/main.py": "print('hola')\n",
        "app/libros/repositorio.py": "def listar(): ...\n",
        "tests/test_libros.py": "# test\n", "README.md": "# Libros\n"})
    print(f"nombre saneado: {p.nombre}")
    print(f"totales: {p.totales}")
    print("\narbol:")

    def pintar(nodo, nivel=1):
        for clave, hijo in nodo.items():
            print("  " * nivel + clave)
            if hijo:
                pintar(hijo, nivel + 1)
    pintar(p.arbol())
    print("\nrutas que NO pueden existir:")
    for mala in ("../../etc/passwd", "/etc/passwd", "app/../../fuera.py", "~/x.py",
                 "__pycache__/x.pyc", ".env", "app/x.exe", "a/b/c/d/e/f/g/h.py"):
        try:
            ruta_segura(mala)
            print(f"  !! PASO: {mala}")
        except RutaProhibida as e:
            print(f"  rechazada  {mala:<24} {e}")
