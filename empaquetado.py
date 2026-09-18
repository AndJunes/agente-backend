"""El ZIP y la prueba de que es el mismo proyecto que se verificó.

LA CADENA QUE HAY QUE PODER DEMOSTRAR

    artefacto -> workspace -> verificación -> manifiesto -> ZIP -> reapertura -> descarga

    Entre cada par de estados tiene que haber identidad comprobable, o vuelve el defecto
    que ha recorrido este proyecto entero en todas sus formas: lo que ocurre ≠ lo que se
    registra ≠ lo que ve el usuario. Aquí sería: el ZIP que se descarga ≠ el proyecto que
    se verificó ≠ el árbol que se enseñó.

DOS CRITERIOS DISTINTOS, A PROPOSITO

    El constructor mete por LISTA BLANCA: solo entra lo que está en el manifiesto, así
    que `.env`, `__pycache__` o las trazas de Mirag no pueden colarse por construcción,
    no por acordarse de excluirlas.

    El inspector rechaza por LISTA NEGRA de patrones y por contenido. Si el inspector
    reutilizara el filtro del constructor, un solo bug pasaría las dos puertas y el test
    saldría verde. Son dos criterios independientes por diseño.

SOBRE EL DETERMINISMO, SIN PROMETER DE MAS

    Mismo árbol y mismo intérprete dan los mismos bytes. Entre versiones de zlib eso no
    está garantizado, así que lo que se afirma —y lo que se prueba— es la propiedad
    fuerte: el conjunto de (nombre, CRC-32, tamaño) es siempre el mismo. Decir
    "reproducible byte a byte en cualquier máquina" sería una afirmación sin respaldo.
"""

import io
import json
import re
import time
import zipfile
from typing import NamedTuple

import proyecto as P

FECHA_FIJA = (1980, 1, 1, 0, 0, 0)     # sin mtimes: son ruido no determinista
MAXIMO_ZIP = 8 * 1024 * 1024
MANIFIESTO = "MIRAG_ARTIFACT.json"

# Lo que jamás puede aparecer dentro del ZIP. Son PATRONES sobre cada entrada.
PROHIBIDOS = (
    re.compile(r"(^|/)\.env$"),                    # .env.example no casa: el $ va tras 'env'
    re.compile(r"(^|/)__pycache__(/|$)"),
    re.compile(r"\.py[co]$"),
    re.compile(r"(^|/)trazas.*\.jsonl$"),
    re.compile(r"(^|/)eval_cache\.json$"),
    re.compile(r"(^|/)\.git(/|$)"),
    re.compile(r"(^|/)\.DS_Store$"),
    re.compile(r"(^|/)(node_modules|\.venv|venv)(/|$)"),
    re.compile(r"\.(key|pem|p12|keystore)$"),
    re.compile(r"(^|/)(id_rsa|\.npmrc|\.netrc|\.pypirc)$"),
    re.compile(r"(^|/)_sonda_\w+\.py$"),           # el arnés de Mirag no es del usuario
)
SECRETOS = re.compile(
    rb"OPENROUTER_API_KEY|sk-or-v1-|sk-ant-|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY"
    # Una semilla de Stellar: 'S' + 55 base32. Es la clave con la que se firma, y la
    # unica forma de cazarla es por su forma: no lleva prefijo ni nombre de variable.
    # Puede dar algun falso positivo; el coste de uno es una alarma, el del falso
    # negativo es publicar una clave privada dentro de un ZIP que el usuario descarga.
    rb"|STELLAR_SECRET_KEY|\bS[A-Z2-7]{55}\b")


class Huella(NamedTuple):
    ruta: str
    sha256: str
    bytes: int
    lineas: int


class Manifiesto(NamedTuple):
    proyecto: str
    generado_en: str
    version: str
    estado: str
    verificacion: dict
    archivos: tuple

    def rutas(self):
        return tuple(h.ruta for h in self.archivos)

    def por_ruta(self):
        return {h.ruta: h for h in self.archivos}

    def a_bytes(self):
        cuerpo = {"proyecto": self.proyecto, "generado_en": self.generado_en,
                  "mirag": self.version, "estado": self.estado,
                  "verificacion": self.verificacion,
                  "archivos": [{"ruta": h.ruta, "sha256": h.sha256,
                                "bytes": h.bytes, "lineas": h.lineas}
                               for h in self.archivos]}
        return (json.dumps(cuerpo, ensure_ascii=False, sort_keys=True, indent=2)
                .encode("utf-8") + b"\n")


class Inspeccion(NamedTuple):
    ok: bool
    comprobaciones: tuple      # ((nombre, ok, detalle), ...)
    motivo: str

    def fallidas(self):
        return tuple(c for c in self.comprobaciones if not c[1])


class Paquete(NamedTuple):
    nombre: str
    datos: bytes
    sha256: str
    manifiesto: Manifiesto
    inspeccion: Inspeccion

    @property
    def ok(self):
        return self.inspeccion.ok

    @property
    def bytes(self):
        return len(self.datos)


def manifiesto_de(proy, certificado=None, version="mirag"):
    """El manifiesto se calcula DESPUES de verificar: representa lo que se comprobó."""
    cert = certificado
    verificacion = {}
    if cert is not None:
        verificacion = {"estado": cert.estado, "por_que": cert.por_que,
                        "marcadores": dict(cert.marcas),
                        "pasan": sum(1 for v in cert.marcas.values() if v == "PASS"),
                        "fallan": sum(1 for v in cert.marcas.values() if v == "FAIL")}
    return Manifiesto(
        proyecto=proy.nombre,
        generado_en=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        version=version,
        estado=(cert.estado if cert is not None else "GENERADO"),
        verificacion=verificacion,
        archivos=tuple(Huella(a.ruta, a.sha, a.bytes, a.lineas) for a in proy.listar()))


def construir(proy, manifiesto):
    """Los bytes del ZIP. Lista blanca: solo entra lo que el manifiesto declara."""
    raiz = manifiesto.proyecto
    permitidas = set(manifiesto.rutas())
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for archivo in proy.listar():
            if archivo.ruta not in permitidas:
                continue                       # no está en el manifiesto: no entra
            info = zipfile.ZipInfo(f"{raiz}/{archivo.ruta}", date_time=FECHA_FIJA)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3             # unix fijo: si no, difiere por SO
            info.external_attr = 0o644 << 16
            z.writestr(info, archivo.datos)
        info = zipfile.ZipInfo(f"{raiz}/{MANIFIESTO}", date_time=FECHA_FIJA)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o644 << 16
        z.writestr(info, manifiesto.a_bytes())
    return buf.getvalue()


def inspeccionar(datos, manifiesto):
    """Se REABRE el ZIP y se comprueba que es lo que el manifiesto dice. Nunca lanza."""
    pruebas = []

    def comprobar(nombre, ok, detalle=""):
        pruebas.append((nombre, bool(ok), detalle))
        return bool(ok)

    if not comprobar("cabe en el tope", len(datos) <= MAXIMO_ZIP,
                     f"{len(datos)} bytes"):
        return Inspeccion(False, tuple(pruebas), "el ZIP supera el tope de tamaño")
    try:
        z = zipfile.ZipFile(io.BytesIO(datos))
        nombres = z.namelist()
    except Exception as e:
        comprobar("se reabre", False, f"{type(e).__name__}: {e}")
        return Inspeccion(False, tuple(pruebas), "el ZIP no se puede reabrir")
    comprobar("se reabre", True, f"{len(nombres)} entradas")

    try:
        malo = z.testzip()
    except Exception as e:
        malo = f"{type(e).__name__}"
    if not comprobar("los CRC cuadran", malo is None, str(malo or "")):
        return Inspeccion(False, tuple(pruebas), f"CRC corrupto en {malo}")

    raiz = manifiesto.proyecto
    fuera = [n for n in nombres if not n.startswith(f"{raiz}/")]
    comprobar("todo cuelga de una raiz unica", not fuera, ", ".join(fuera[:3]))

    peligrosas = [n for n in nombres
                  if n.startswith("/") or ".." in n.split("/") or "\\" in n]
    comprobar("ninguna ruta se escapa", not peligrosas, ", ".join(peligrosas[:3]))

    enlaces = [i.filename for i in z.infolist()
               if (i.external_attr >> 16) & 0o170000 == 0o120000]
    comprobar("ningun symlink", not enlaces, ", ".join(enlaces[:3]))

    relativas = [n[len(raiz) + 1:] for n in nombres if n.startswith(f"{raiz}/")]
    vetadas = [(n, p.pattern) for n in relativas for p in PROHIBIDOS if p.search(n)]
    comprobar("nada de basura de Mirag ni secretos por nombre", not vetadas,
              "; ".join(f"{n} ({p})" for n, p in vetadas[:3]))

    declaradas = set(manifiesto.rutas())
    presentes = set(relativas) - {MANIFIESTO}
    faltan, sobran = sorted(declaradas - presentes), sorted(presentes - declaradas)
    comprobar("no falta ningun archivo del manifiesto", not faltan, ", ".join(faltan[:3]))
    comprobar("no sobra ningun archivo", not sobran, ", ".join(sobran[:3]))

    # el re-hash: se extrae de verdad, como hará el usuario
    distintos, con_secreto = [], []
    esperado = manifiesto.por_ruta()
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        try:
            z.extractall(tmp)
        except Exception as e:
            comprobar("se puede extraer", False, f"{type(e).__name__}: {e}")
            return Inspeccion(False, tuple(pruebas), "el ZIP no se puede extraer")
        comprobar("se puede extraer", True, "")
        for ruta, huella in esperado.items():
            fichero = Path(tmp) / raiz / ruta
            if not fichero.exists():
                distintos.append((ruta, "no se extrajo"))
                continue
            crudo = fichero.read_bytes()
            if P.sha(crudo) != huella.sha256:
                distintos.append((ruta, "hash distinto"))
            elif len(crudo) != huella.bytes:
                distintos.append((ruta, "tamaño distinto"))
            if SECRETOS.search(crudo):
                con_secreto.append(ruta)
        embebido = Path(tmp) / raiz / MANIFIESTO
        igual = embebido.exists() and embebido.read_bytes() == manifiesto.a_bytes()

    comprobar("los hashes del ZIP == los del artefacto", not distintos,
              "; ".join(f"{r}: {p}" for r, p in distintos[:3]))
    comprobar("ningun secreto en el contenido", not con_secreto, ", ".join(con_secreto[:3]))
    comprobar("el manifiesto embebido coincide", igual, "")

    fallidas = [c for c in pruebas if not c[1]]
    motivo = "" if not fallidas else "; ".join(f"{c[0]}: {c[2]}" or c[0] for c in fallidas)
    return Inspeccion(not fallidas, tuple(pruebas), motivo)


def sellar(proy, certificado=None, version="mirag"):
    """Construye e inspecciona. **Nunca lanza**: un fallo de integridad no puede llevarse
    por delante una respuesta que ya costó dinero y verificación."""
    manifiesto = manifiesto_de(proy, certificado, version)
    try:
        datos = construir(proy, manifiesto)
    except Exception as e:
        vacio = Inspeccion(False, (("se construye", False, f"{type(e).__name__}: {e}"),),
                           f"no se pudo construir el ZIP: {e}")
        return Paquete(f"{proy.nombre}.zip", b"", "", manifiesto, vacio)
    return Paquete(f"{proy.nombre}.zip", datos, P.sha(datos), manifiesto,
                   inspeccionar(datos, manifiesto))


if __name__ == "__main__":
    p = P.desde_dict("libros-api", {
        "app/__init__.py": "", "app/main.py": "def crear_servidor(puerto=0):\n    ...\n",
        "tests/test_api.py": "# tests\n", "README.md": "# Libros API\n",
        ".env.example": "PUERTO=8080\n"})
    paq = sellar(p)
    print(f"  {paq.nombre} · {paq.bytes} bytes · sha {paq.sha256[:16]}")
    print(f"  integridad: {'OK' if paq.ok else 'ERROR — ' + paq.inspeccion.motivo}\n")
    for nombre, ok, detalle in paq.inspeccion.comprobaciones:
        print(f"    {'✅' if ok else '❌'} {nombre}" + (f"  ({detalle})" if detalle else ""))
    b = construir(p, paq.manifiesto)
    print(f"\n  determinista en este interprete: {b == paq.datos}")
    import zipfile as _z, io as _io
    with _z.ZipFile(_io.BytesIO(paq.datos)) as z:
        print(f"  se abre como: {sorted({n.split('/')[0] for n in z.namelist()})}")
        print(f"  entradas: {z.namelist()}")
