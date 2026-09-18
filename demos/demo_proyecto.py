"""La demo de generación de proyectos, de punta a punta y con números.

    python3 demo_proyecto.py              # offline determinista, $0
    python3 demo_proyecto.py --online     # con modelo real
    python3 demo_proyecto.py --romper zip # fuerza un fallo de integridad, para verlo

Hace lo mismo que hace el servidor, sin navegador: ejecuta la petición, genera el
proyecto, lo verifica ejecutándolo, lo empaqueta, **reabre el ZIP**, lo descomprime en un
temporal y corre sus tests ahí — que es exactamente lo que hará quien lo descargue.
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
import io
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import agent
import demos


def _linea(titulo):
    print(f"\n{'─' * 74}\n{titulo}\n{'─' * 74}")


def main(argv):
    online = "--online" in argv
    romper = (argv[argv.index("--romper") + 1] if "--romper" in argv else None)
    caso = demos.CANONICAS["proyecto"]

    _linea("PETICION")
    print(f"  {caso['pregunta']}")

    t0 = time.time()
    e, informe = demos.correr("proyecto", offline=not online)
    segundos = time.time() - t0
    proy, cert, art = e.proyecto, e.certificado, e.artefacto
    if proy is None:
        print("\n  no se genero ningun proyecto")
        return 1

    _linea("ARQUITECTURA")
    for ruta in proy.rutas():
        archivo = proy.obtener(ruta)
        print(f"  {ruta:<34} {archivo.lineas:>4} lineas  {archivo.sha[:12]}")

    _linea("VERIFICACION")
    iconos = {"ok": "✅", "fallo": "❌", "limitado": "❔", "omitido": "—"}
    for fase in cert.fases:
        print(f"  {iconos.get(fase.estado, '?')} {fase.nombre:<22} {fase.detalle[:56]}")
    pasan = sum(1 for v in cert.marcas.values() if v == "PASS")
    print(f"\n  {cert.estado} · {pasan}/{len(cert.marcas)} marcadores")
    print(f"  {cert.por_que}")
    if cert.reparaciones:
        print(f"  reparaciones: {len(cert.reparaciones)}")

    paquete = art.paquete if art else None
    if paquete is None:
        print("\n  no se empaqueto nada")
        return 1

    datos = paquete.datos
    if romper:
        datos = _romper(datos, romper)
        import empaquetado
        inspeccion = empaquetado.inspeccionar(datos, paquete.manifiesto)
        _linea(f"INTEGRIDAD (forzando el fallo '{romper}')")
        for nombre, ok, detalle in inspeccion.comprobaciones:
            print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  {detalle[:46]}" if detalle else ""))
        print(f"\n  ⛔ {inspeccion.motivo[:120]}")
        print("  No hay descarga: no se puede demostrar que el ZIP sea lo que se verifico.")
        return 0

    _linea("EMPAQUETADO")
    print(f"  {paquete.nombre} · {paquete.bytes:,} bytes · sha256 {paquete.sha256[:16]}")
    for nombre, ok, detalle in paquete.inspeccion.comprobaciones:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  ({detalle[:40]})" if detalle else ""))

    _linea("Y AHORA COMO EL USUARIO: descomprimir y ejecutar")
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            z.extractall(tmp)
            entradas = len(z.namelist())
        raiz = Path(tmp) / proy.nombre
        comando = (proy.espec or {}).get("comando_test") or \
            "python3 -m unittest discover -s tests -t ."
        print(f"  descomprimido: {entradas} entradas en {raiz.name}/")
        print(f"  $ {comando}")
        # shlex, no split(): el modelo puede devolver `-p "test_*.py"` y las comillas
        # partirian el comando por la mitad. Y si el binario no existe, se dice: no se
        # deja reventar el informe entero.
        import shlex
        try:
            r = subprocess.run(shlex.split(comando), cwd=raiz, capture_output=True,
                               text=True, timeout=180)
            codigo_salida = r.returncode
            cola = [l for l in r.stderr.splitlines()
                    if "Ran" in l or l.strip() in ("OK", "FAILED")]
            print(f"  exit={codigo_salida} · {' · '.join(cola)}")
            if codigo_salida != 0:
                print("  " + r.stderr[-500:].replace("\n", "\n  "))
        except (OSError, ValueError) as error:
            codigo_salida = 1
            print(f"  el comando no se pudo ejecutar: {type(error).__name__}: {error}")

    _linea("RESUMEN")
    print(f"  proyecto      {proy.nombre} · {proy.totales['archivos']} archivos · "
          f"{proy.totales['lineas']} lineas")
    print(f"  estado        {cert.estado}")
    print(f"  marcadores    {pasan}/{len(cert.marcas)}")
    print(f"  zip           {paquete.bytes:,} bytes · {paquete.sha256[:24]}")
    print(f"  integridad    {len(paquete.inspeccion.comprobaciones)} comprobaciones, "
          f"{'todas OK' if paquete.ok else 'FALLIDA'}")
    print(f"  tiempo        {segundos:.1f}s")
    print(f"  coste         {'$%.4f' % agent.PRESUPUESTO.coste if online else 'SIMULADO · $0'}")
    print(f"  contrato      {'CUMPLE' if informe['cumple'] else 'NO CUMPLE: ' + '; '.join(informe['fallos'])}")
    return 0 if (informe["cumple"] and codigo_salida == 0) else 1


def _romper(datos, modo):
    """Manipula el ZIP para poder VER el camino de fallo. Un camino que nunca se ha
    visto en pantalla es un camino que no existe."""
    origen = zipfile.ZipFile(io.BytesIO(datos))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre in origen.namelist():
            crudo = origen.read(nombre)
            if modo == "hash" and nombre.endswith("main.py"):
                crudo = b"# MANIPULADO\n" + crudo
            z.writestr(nombre, crudo)
        if modo == "entrada":
            z.writestr(f"{origen.namelist()[0].split('/')[0]}/colado.py", b"x = 1\n")
    salida = buf.getvalue()
    return salida[:len(salida) // 2] if modo == "zip" else salida


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
