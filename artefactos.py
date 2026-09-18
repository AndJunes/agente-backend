"""Dónde viven los proyectos generados y cómo se identifican sin exponer el disco.

POR QUE UN REGISTRO Y NO UNA CARPETA

    `salida/` no sirve para esto, y no por gusto: `rapido.guardar` la **vacía entera** en
    cada petición (`shutil.rmtree` por cada entrada) y aplana las rutas. Con un
    `ThreadingHTTPServer`, dos peticiones a la vez ya se pisan ahí hoy. Un botón de
    descarga apuntando a `salida/` entregaría el proyecto de la otra pestaña — que es
    literalmente el modo de fallo que este módulo existe para impedir.

LA PROPIEDAD QUE NO SE PUEDE RELAJAR

    El id **nunca se concatena a un Path**. Se valida contra una regex de 24 hex, se
    busca en un diccionario en memoria, y el artefacto trae su propia carpeta ya
    construida. Si alguien escribe algún día `CARPETA / ident`, vuelve entero el agujero
    que la lista blanca de `do_GET` cerró.

LOS BYTES SE SIRVEN DE MEMORIA

    `Paquete.datos` es la fuente de la descarga. El `.zip` en disco es una copia de
    conveniencia que nadie lee para servir. Así no hay ventana entre "el gate inspeccionó
    estos bytes" y "el servidor escribió estos otros".
"""

import re
import secrets
import shutil
import threading
import time
from pathlib import Path
from typing import NamedTuple

CARPETA = Path(__file__).resolve().parent / "artefactos"
ID_VALIDO = re.compile(r"\A[0-9a-f]{24}\Z")
# Tope del texto que viaja en el JSON. Por encima se entregan las rutas y se dice que
# hay que bajar el ZIP: un proyecto generado normal ronda las decenas de KB, asi que esto
# solo se toca cuando algo ha ido mal.
TOPE_TEXTO = 2 * 1024 * 1024
TTL = 3600                    # segundos que vive un artefacto
MAXIMOS = 20                  # cuántos se guardan a la vez
LIMITE_MEMORIA = 64 * 1024 * 1024

_REGISTRO = {}
_CERROJO = threading.Lock()


class Artefacto(NamedTuple):
    id: str
    nombre: str
    creado: float
    carpeta: Path
    proyecto: object
    certificado: object
    paquete: object
    simulado: bool = False       # ¿la decision del modelo vino de un guion?

    @property
    def descargable(self):
        return self.paquete is not None and self.paquete.ok

    @property
    def estado(self):
        return self.certificado.estado if self.certificado is not None else "GENERADO"

    def _archivos(self, man):
        """Las huellas del manifiesto, y ademas el TEXTO de cada archivo.

        El texto viaja aqui porque quien consume esto ya no es solo la pagina propia:
        CodeZard tiene que PINTAR el codigo. Hasta ahora solo iban rutas y hashes, y el
        contenido vivia unicamente dentro del ZIP — o sea que para enseñar un archivo
        habia que bajarse el ZIP y descomprimirlo en el servidor de enfrente.

        Dos guardas, y ninguna sobra:

        1. `TOPE_TEXTO` en total. Pasado el tope se entregan las rutas SIN texto y se dice
           por que. Mandar una respuesta de decenas de MB en silencio no es una entrega:
           es un fallo que aparece mas tarde y en otro sitio.

        2. La misma regex que `empaquetado.SECRETOS`. Esa ya impedia que un secreto
           viajara dentro de un ZIP (empaquetado.py:234 tumba la inspeccion y el artefacto
           deja de ser descargable), pero `para_la_pagina()` se emite IGUAL aunque el ZIP
           no sea descargable. Sin esta guarda, meter el texto aqui habria abierto por la
           API justo la puerta que el ZIP tenia cerrada. Si un archivo generado trae algo
           con forma de clave, sale su ruta y no su contenido.
        """
        import empaquetado                      # aqui para no darle la vuelta al grafo
        planos = self.proyecto.planos()
        huellas = [{"ruta": h.ruta, "bytes": h.bytes, "lineas": h.lineas,
                    "sha256": h.sha256} for h in (man.archivos if man else ())]
        total = sum(h["bytes"] for h in huellas)
        if total > TOPE_TEXTO:
            for h in huellas:
                h["texto"] = None
                h["sin_texto"] = (f"el proyecto ocupa {total} bytes y el tope de la API son "
                                  f"{TOPE_TEXTO}: descarga el ZIP")
            return huellas
        for h in huellas:
            texto = planos.get(h["ruta"])
            if texto is None:
                h["texto"], h["sin_texto"] = None, "no esta en los planos del proyecto"
            elif empaquetado.SECRETOS.search(texto.encode("utf-8", "replace")):
                h["texto"], h["sin_texto"] = None, "contiene algo con forma de credencial"
            else:
                h["texto"] = texto
        return huellas

    def para_la_pagina(self):
        """Lo que viaja al navegador. Sin una sola ruta del filesystem."""
        man = self.paquete.manifiesto if self.paquete else None
        insp = self.paquete.inspeccion if self.paquete else None
        cert = self.certificado
        return {
            "id": self.id,
            "nombre": self.nombre,
            "estado": self.estado,
            "simulado": self.simulado,
            "por_que": cert.por_que if cert else "",
            "archivos": self._archivos(man),
            "totales": self.proyecto.totales,
            "verificacion": (man.verificacion if man else {}),
            "fases": [{"nombre": f.nombre, "estado": f.estado, "detalle": f.detalle}
                      for f in (cert.fases if cert else ())],
            "zip": ({"nombre": self.paquete.nombre, "bytes": self.paquete.bytes,
                     "sha256": self.paquete.sha256} if self.paquete else None),
            "integridad": ({"ok": insp.ok, "motivo": insp.motivo,
                            "comprobaciones": [list(c) for c in insp.comprobaciones]}
                           if insp else {"ok": False, "motivo": "no se empaquetó",
                                         "comprobaciones": []}),
            # La página NUNCA compone esta URL: la usa tal cual o no pinta botón.
            "descarga": (f"/descarga?id={self.id}" if self.descargable else None),
        }


def reservar(nombre):
    """(id, carpeta). `mkdir` sin `exist_ok`: si colisionara, revienta en vez de pisar."""
    for _ in range(5):
        ident = secrets.token_hex(12)
        carpeta = CARPETA / ident
        try:
            carpeta.mkdir(parents=True)
            return ident, carpeta
        except FileExistsError:
            continue
    raise RuntimeError("no se pudo reservar un id libre")


def registrar(artefacto):
    """Lo guarda y caduca los viejos. Un artefacto registrado ya no se muta."""
    with _CERROJO:
        _REGISTRO[artefacto.id] = artefacto
    _caducar()
    return artefacto.id


def obtener(ident):
    """El artefacto, o None. El id no toca el disco: se busca en el índice."""
    if not isinstance(ident, str) or not ID_VALIDO.match(ident):
        return None
    with _CERROJO:
        art = _REGISTRO.get(ident)
    if art is None:
        return None
    if time.time() - art.creado > TTL:
        olvidar(ident)
        return None
    return art


def olvidar(ident):
    with _CERROJO:
        art = _REGISTRO.pop(ident, None)
    if art is not None:
        _borrar(art)
    return art is not None


def _borrar(art):
    # Solo se borra lo que este módulo creó. Nada de barrer la carpeta entera: eso es
    # exactamente lo que hace `rapido.guardar` y lo que se lleva por delante lo ajeno.
    if art.carpeta.parent == CARPETA and art.carpeta.name == art.id and art.carpeta.exists():
        shutil.rmtree(art.carpeta, ignore_errors=True)


def _caducar(ahora=None):
    ahora = time.time() if ahora is None else ahora
    with _CERROJO:
        vivos = sorted(_REGISTRO.values(), key=lambda a: a.creado)
        fuera = [a for a in vivos if ahora - a.creado > TTL]
        resto = [a for a in vivos if a not in fuera]
        while len(resto) > MAXIMOS:
            fuera.append(resto.pop(0))
        memoria = sum(a.paquete.bytes for a in resto if a.paquete)
        while memoria > LIMITE_MEMORIA and len(resto) > 1:
            viejo = resto.pop(0)
            memoria -= viejo.paquete.bytes if viejo.paquete else 0
            fuera.append(viejo)
        for a in fuera:
            _REGISTRO.pop(a.id, None)
    for a in fuera:
        _borrar(a)
    return [a.id for a in fuera]


def guardar(proyecto, certificado, paquete, en_disco=True, simulado=False):
    """Registra el artefacto y lo devuelve listo para enseñar y descargar.

    `en_disco=False` no toca el sistema de archivos: el artefacto vive solo en memoria y
    **se puede descargar igual**, porque los bytes que se sirven salen de `paquete.datos`
    y no del disco. La copia en disco es de conveniencia (mirarla a mano, el CLI), no la
    fuente. Los tests usan `en_disco=False` y no dejan nada detrás.
    """
    ident = secrets.token_hex(12)
    carpeta = CARPETA / ident
    if en_disco:
        ident, carpeta = reservar(proyecto.nombre)
        proyecto.materializar(carpeta / "proyecto")
        if paquete is not None and paquete.datos:
            (carpeta / paquete.nombre).write_bytes(paquete.datos)
            (carpeta / "MIRAG_ARTIFACT.json").write_bytes(paquete.manifiesto.a_bytes())
    art = Artefacto(ident, proyecto.nombre, time.time(), carpeta,
                    proyecto, certificado, paquete, simulado)
    registrar(art)
    return art


def barrer_huerfanos(edad=24 * 3600, ahora=None):
    """Carpetas que quedaron en disco sin nadie que las conozca.

    El registro vive en MEMORIA y muere con el proceso, asi que `_caducar` nunca llega a
    las carpetas de ejecuciones anteriores: se acumulan para siempre. Medido: 33 carpetas
    tras una sesion de desarrollo. Esto corre al importar el modulo y solo toca lo que
    tiene forma de artefacto (un id de 24 hex) y mas de `edad` segundos.
    """
    ahora = time.time() if ahora is None else ahora
    borradas = []
    if not CARPETA.exists():
        return borradas
    with _CERROJO:
        conocidos = set(_REGISTRO)
    for carpeta in CARPETA.iterdir():
        if not carpeta.is_dir() or not ID_VALIDO.match(carpeta.name):
            continue                       # no tiene forma de artefacto: no se toca
        if carpeta.name in conocidos:
            continue                       # vivo en este proceso
        try:
            if ahora - carpeta.stat().st_mtime > edad:
                shutil.rmtree(carpeta, ignore_errors=True)
                borradas.append(carpeta.name)
        except OSError:
            pass
    return borradas


def vivos():
    with _CERROJO:
        return tuple(_REGISTRO)


# Al importar: se barre lo de sesiones anteriores. Sin esto la carpeta crece sin techo.
barrer_huerfanos()


if __name__ == "__main__":
    import empaquetado as E
    import proyecto as P
    a = P.desde_dict("proyecto-a", {"app/__init__.py": "", "app/main.py": "A = 1\n",
                                    "tests/test_a.py": "# a\n"})
    b = P.desde_dict("proyecto-b", {"app/__init__.py": "", "app/main.py": "B = 2\n",
                                    "tests/test_b.py": "# b\n"})
    ra = guardar(a, None, E.sellar(a))
    rb = guardar(b, None, E.sellar(b))
    print(f"  A: {ra.id}  descargable={ra.descargable}  {ra.paquete.bytes} bytes")
    print(f"  B: {rb.id}  descargable={rb.descargable}  {rb.paquete.bytes} bytes")
    print(f"  ids distintos: {ra.id != rb.id} · carpetas distintas: {ra.carpeta != rb.carpeta}")
    print(f"  A sigue intacta tras registrar B: {obtener(ra.id) is not None}")
    print(f"  bytes distintos: {ra.paquete.datos != rb.paquete.datos}")
    print(f"  url de A: {ra.para_la_pagina()['descarga']}")
    print(f"  un id inventado: {obtener('0'*24)}")
    print(f"  un id con ../: {obtener('../../etc/passwd')}")
    for ident in (ra.id, rb.id):
        olvidar(ident)
    print(f"  tras olvidar: vivos={vivos()} · carpetas borradas="
          f"{not (CARPETA / ra.id).exists() and not (CARPETA / rb.id).exists()}")
