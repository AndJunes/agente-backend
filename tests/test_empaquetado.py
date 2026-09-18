"""El ZIP, el gate de integridad, el registro y la descarga.

La pregunta que contesta esta suite es una sola: **¿lo que se descarga es lo que se
verificó?** Todo lo demás es instrumental.

    python3 test_empaquetado.py
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
# La raiz (produccion) y las dos carpetas cuyos modulos se importan por nombre desnudo:
# `test_cache` importa `cache` (experimental/) y `test_plan` importa `eval` (benchmarks/).
for _d in (_RAIZ_REPO, _RAIZ_REPO / "experimental", _RAIZ_REPO / "benchmarks"):
    _sys.path.insert(0, str(_d))
import hashlib
import http.client
import io
import json
import subprocess
import sys
import tempfile
import threading
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path

import artefactos as A
import empaquetado as E
import fixture_proyecto as F
import proyecto as P
import server

AQUI = Path(__file__).parent
casos = []


def probar(nombre, fn):
    try:
        fn(); casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _libros(nombre="libros-api"):
    return P.desde_dict(nombre, F.ARCHIVOS)


def _rehacer(datos, cambiar):
    origen = zipfile.ZipFile(io.BytesIO(datos))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        cambiar(origen, z)
    return buf.getvalue()


def _copiar(o, z, saltar=None):
    for n in o.namelist():
        if saltar and saltar in n:
            continue
        z.writestr(n, o.read(n))


# ══ La forma del ZIP ════════════════════════════════════════════════════════

def el_zip_se_abre_con_una_sola_raiz():
    """`books-api.zip` -> `books-api/`, nunca `tmp/uuid/books-api/`."""
    paq = E.sellar(_libros())
    with zipfile.ZipFile(io.BytesIO(paq.datos)) as z:
        raices = {n.split("/")[0] for n in z.namelist()}
    assert raices == {"libros-api"}, raices


def ninguna_ruta_del_zip_lleva_rastro_del_filesystem():
    paq = E.sellar(_libros())
    with zipfile.ZipFile(io.BytesIO(paq.datos)) as z:
        nombres = z.namelist()
    assert not [n for n in nombres if "tmp" in n or "Users" in n or "artefactos" in n], nombres


def los_subdirectorios_sobreviven():
    paq = E.sellar(_libros())
    with zipfile.ZipFile(io.BytesIO(paq.datos)) as z:
        assert "libros-api/app/libros/router.py" in z.namelist()
        assert "libros-api/tests/test_libros.py" in z.namelist()


def el_zip_es_determinista_en_este_interprete():
    p = _libros()
    man = E.manifiesto_de(p)
    assert E.construir(p, man) == E.construir(p, man)


def el_conjunto_nombre_crc_tamano_es_estable():
    """La propiedad fuerte: aguanta otra version de zlib, al contrario que los bytes."""
    p = _libros()
    man = E.manifiesto_de(p)
    def firma(datos):
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            return {(i.filename, i.CRC, i.file_size) for i in z.infolist()}
    assert firma(E.construir(p, man)) == firma(E.construir(p, man))


def el_manifiesto_va_dentro_y_no_lleva_secretos():
    paq = E.sellar(_libros())
    with zipfile.ZipFile(io.BytesIO(paq.datos)) as z:
        crudo = z.read(f"{paq.manifiesto.proyecto}/{E.MANIFIESTO}")
    man = json.loads(crudo)
    assert man["proyecto"] == "libros-api" and man["archivos"]
    assert not E.SECRETOS.search(crudo)
    assert "Users" not in crudo.decode() and "tmp" not in crudo.decode()


def el_env_example_si_entra_y_el_env_no():
    """El `$` del patron separa uno de otro, y es facil relajarlo por descuido."""
    assert E.es_prohibido(".env") if hasattr(E, "es_prohibido") else True
    assert any(p.search(".env") for p in E.PROHIBIDOS)
    assert not any(p.search(".env.example") for p in E.PROHIBIDOS)


# ══ El gate: solo vale si CAZA ═════════════════════════════════════════════

def un_contenido_cambiado_no_pasa():
    """El caso central: el ZIP deja de ser el proyecto que se verifico."""
    paq = E.sellar(_libros())
    tocado = _rehacer(paq.datos, lambda o, z: [
        z.writestr(n, b"# MANIPULADO\n" if n.endswith("main.py") else o.read(n))
        for n in o.namelist()])
    r = E.inspeccionar(tocado, paq.manifiesto)
    assert not r.ok and "hashes" in r.motivo, r.motivo


def un_archivo_de_mas_no_pasa():
    paq = E.sellar(_libros())
    tocado = _rehacer(paq.datos, lambda o, z: (_copiar(o, z),
                                               z.writestr("libros-api/colado.py", b"x")))
    assert not E.inspeccionar(tocado, paq.manifiesto).ok


def un_archivo_de_menos_no_pasa():
    paq = E.sellar(_libros())
    tocado = _rehacer(paq.datos, lambda o, z: _copiar(o, z, saltar="README.md"))
    assert not E.inspeccionar(tocado, paq.manifiesto).ok


def un_env_colado_no_pasa():
    paq = E.sellar(_libros())
    tocado = _rehacer(paq.datos, lambda o, z: (
        _copiar(o, z), z.writestr("libros-api/.env", b"OPENROUTER_API_KEY=sk-or-v1-secreto")))
    assert not E.inspeccionar(tocado, paq.manifiesto).ok


def un_pycache_colado_no_pasa():
    paq = E.sellar(_libros())
    tocado = _rehacer(paq.datos, lambda o, z: (
        _copiar(o, z), z.writestr("libros-api/app/__pycache__/main.pyc", b"\x00")))
    assert not E.inspeccionar(tocado, paq.manifiesto).ok


def una_ruta_que_se_escapa_no_pasa():
    paq = E.sellar(_libros())
    tocado = _rehacer(paq.datos, lambda o, z: (
        _copiar(o, z), z.writestr("libros-api/../fuera.py", b"x")))
    assert not E.inspeccionar(tocado, paq.manifiesto).ok


def un_zip_truncado_no_pasa():
    paq = E.sellar(_libros())
    assert not E.inspeccionar(paq.datos[:len(paq.datos) // 2], paq.manifiesto).ok


def un_byte_cambiado_rompe_el_crc():
    paq = E.sellar(_libros())
    malo = bytearray(paq.datos); malo[len(malo) // 2] ^= 0xFF
    assert not E.inspeccionar(bytes(malo), paq.manifiesto).ok


def un_secreto_en_el_contenido_no_pasa():
    """Criterio INDEPENDIENTE del filtro de construccion: si fuera el mismo, un solo bug
    pasaria las dos puertas."""
    p = P.desde_dict("x", {"app/__init__.py": "",
                           "app/config.py": 'CLAVE = "sk-or-v1-esto-es-un-secreto"\n',
                           "tests/test_x.py": "# t\n"})
    assert not E.sellar(p).ok


def el_zip_intacto_si_pasa():
    paq = E.sellar(_libros())
    assert paq.ok, paq.inspeccion.motivo
    assert len(paq.inspeccion.comprobaciones) >= 12


def un_fallo_de_integridad_no_lanza():
    """No puede llevarse por delante una respuesta que ya costo dinero y verificacion."""
    p = P.desde_dict("x", {"app/x.py": 'K = "sk-or-v1-secreto"\n'})
    paq = E.sellar(p)
    assert isinstance(paq, E.Paquete) and not paq.ok


# ══ El registro ════════════════════════════════════════════════════════════

def dos_proyectos_no_se_pisan():
    a = A.guardar(_libros("proyecto-a"), None, E.sellar(_libros("proyecto-a")), en_disco=False)
    b = A.guardar(_libros("proyecto-b"), None, E.sellar(_libros("proyecto-b")), en_disco=False)
    try:
        assert a.id != b.id
        assert a.paquete.datos != b.paquete.datos
        assert A.obtener(a.id).nombre == "proyecto-a"
        assert A.obtener(b.id).nombre == "proyecto-b"
    finally:
        A.olvidar(a.id); A.olvidar(b.id)


def registrar_uno_nuevo_no_borra_los_anteriores():
    """Es lo que hace `rapido.guardar` con `salida/`, y por eso no se usa aqui."""
    a = A.guardar(_libros("a"), None, E.sellar(_libros("a")), en_disco=False)
    for i in range(3):
        A.guardar(_libros(f"otro{i}"), None, E.sellar(_libros(f"otro{i}")), en_disco=False)
    assert A.obtener(a.id) is not None, "registrar otros borro el primero"
    for ident in list(A.vivos()):
        A.olvidar(ident)


def un_id_invalido_no_devuelve_nada():
    for malo in ("../../etc/passwd", "", "x" * 24, "ABCDEF" * 4, "0" * 23, None, 7):
        assert A.obtener(malo) is None, malo


def el_id_no_se_deriva_del_nombre():
    a = A.guardar(_libros("mismo"), None, E.sellar(_libros("mismo")), en_disco=False)
    b = A.guardar(_libros("mismo"), None, E.sellar(_libros("mismo")), en_disco=False)
    try:
        assert a.id != b.id and A.ID_VALIDO.match(a.id)
    finally:
        A.olvidar(a.id); A.olvidar(b.id)


def veinte_hilos_registrando_no_pierden_ninguno():
    ids, barrera = [], threading.Barrier(20)
    def registrar(i):
        barrera.wait()
        p = _libros(f"p{i}")
        ids.append(A.guardar(p, None, E.sellar(p), en_disco=False).id)
    hilos = [threading.Thread(target=registrar, args=(i,)) for i in range(20)]
    [h.start() for h in hilos]; [h.join() for h in hilos]
    try:
        assert len(set(ids)) == 20, f"{len(set(ids))} ids unicos de 20"
    finally:
        for ident in ids:
            A.olvidar(ident)


def las_carpetas_huerfanas_se_barren():
    """El registro vive en memoria y muere con el proceso, asi que las carpetas de
    ejecuciones anteriores no las limpiaba nadie. Medido: 33 tras una sesion."""
    import os
    import time
    viejo = A.CARPETA / ("b" * 24)
    viejo.mkdir(parents=True, exist_ok=True)
    (viejo / "x.txt").write_text("x")
    os.utime(viejo, (time.time() - 48 * 3600,) * 2)
    try:
        assert (A.CARPETA / ("b" * 24)).name in A.barrer_huerfanos()
        assert not viejo.exists()
    finally:
        if viejo.exists():
            import shutil as _sh
            _sh.rmtree(viejo, ignore_errors=True)


def el_barrido_no_toca_lo_que_no_es_suyo():
    """Barrer con `iterdir()` a lo bruto es lo que hace `rapido.guardar` con salida/."""
    import os
    import time
    ajeno = A.CARPETA / "carpeta-de-otro"
    ajeno.mkdir(parents=True, exist_ok=True)
    os.utime(ajeno, (time.time() - 48 * 3600,) * 2)
    try:
        A.barrer_huerfanos()
        assert ajeno.exists(), "borro una carpeta que no tiene forma de artefacto"
    finally:
        ajeno.rmdir()


def el_barrido_respeta_los_vivos_de_este_proceso():
    art = A.guardar(_libros("vivo"), None, E.sellar(_libros("vivo")), en_disco=True)
    try:
        A.barrer_huerfanos(edad=0)          # todo es "viejo" y aun asi sobrevive
        assert art.carpeta.exists(), "borro un artefacto vivo"
        assert A.obtener(art.id) is not None
    finally:
        A.olvidar(art.id)


# ══ La descarga, contra el servidor real ═══════════════════════════════════

def _servidor():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _generar(srv, pregunta):
    c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=300)
    c.request("POST", "/", json.dumps({"pregunta": pregunta, "modo": "pipeline"}),
              {"Content-Type": "application/json"})
    eventos = [json.loads(l[6:]) for l in c.getresponse().read().decode().splitlines()
               if l.startswith("data: ")]
    return next(e for e in eventos if e.get("tipo") == "fin")


def _bajar(srv, url):
    c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=120)
    c.request("GET", url)
    r = c.getresponse()
    return r.status, r.read(), dict(r.getheaders())


def lo_que_se_descarga_es_lo_que_se_verifico():
    """EL test del producto. Todo lo demas existe para que este pueda pasar."""
    import demos
    srv = _servidor()
    try:
        fin = _generar(srv, demos.CANONICAS["proyecto"]["pregunta"])
        p = fin["proyecto"]
        assert p and p["descarga"], fin.get("respuesta", "")[:200]
        codigo, datos, cab = _bajar(srv, p["descarga"])
        assert codigo == 200, codigo
        assert cab["X-Mirag-Sha256"] == hashlib.sha256(datos).hexdigest()
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            del_zip = {n.split("/", 1)[1]: hashlib.sha256(z.read(n)).hexdigest()
                       for n in z.namelist() if not n.endswith(E.MANIFIESTO)}
        de_la_ui = {a["ruta"]: a["sha256"] for a in p["archivos"]}
        assert de_la_ui == del_zip, "el arbol que se enseño no es el ZIP que se descargo"
    finally:
        srv.shutdown()


def el_zip_descargado_se_descomprime_y_sus_tests_pasan():
    """La promesa entera: descomprimir y ejecutar, sin editar nada."""
    import demos
    srv = _servidor()
    try:
        p = _generar(srv, demos.CANONICAS["proyecto"]["pregunta"])["proyecto"]
        _codigo, datos, _c = _bajar(srv, p["descarga"])
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(io.BytesIO(datos)) as z:
                z.extractall(tmp)
            raiz = Path(tmp) / p["nombre"]
            r = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                               cwd=raiz, capture_output=True, text=True, timeout=120)
            assert r.returncode == 0, r.stderr[-400:]
            assert "OK" in r.stderr, r.stderr[-200:]
    finally:
        srv.shutdown()


def generar_b_no_estropea_la_descarga_de_a():
    """A, luego B, luego descargar A. Y despues B. Los dos intactos."""
    import demos
    srv = _servidor()
    try:
        a = _generar(srv, demos.CANONICAS["proyecto"]["pregunta"])["proyecto"]
        b = _generar(srv, demos.CANONICAS["proyecto"]["pregunta"])["proyecto"]
        assert a["id"] != b["id"]
        ca, da, _ = _bajar(srv, a["descarga"])
        cb, db, _ = _bajar(srv, b["descarga"])
        assert ca == 200 and cb == 200
        assert hashlib.sha256(da).hexdigest() == a["zip"]["sha256"], "A cambio al generar B"
        assert hashlib.sha256(db).hexdigest() == b["zip"]["sha256"]
    finally:
        srv.shutdown()


def las_descargas_concurrentes_no_se_cruzan():
    """La generacion va en serie porque `dobles.usar` sustituye un global; lo que aqui
    se demuestra es que la ENTREGA concurrente no mezcla dos proyectos."""
    import demos
    srv = _servidor()
    try:
        a = _generar(srv, demos.CANONICAS["proyecto"]["pregunta"])["proyecto"]
        b = _generar(srv, demos.CANONICAS["proyecto"]["pregunta"])["proyecto"]
        recibido = {}
        def bajar(clave, p):
            recibido[clave] = _bajar(srv, p["descarga"])[1]
        hilos = [threading.Thread(target=bajar, args=("a", a)),
                 threading.Thread(target=bajar, args=("b", b))]
        [h.start() for h in hilos]; [h.join() for h in hilos]
        assert hashlib.sha256(recibido["a"]).hexdigest() == a["zip"]["sha256"]
        assert hashlib.sha256(recibido["b"]).hexdigest() == b["zip"]["sha256"]
    finally:
        srv.shutdown()


def un_id_desconocido_da_410_y_uno_malo_400():
    srv = _servidor()
    try:
        assert _bajar(srv, "/descarga?id=" + "0" * 24)[0] == 410
        for malo in ("", "../../etc/passwd", "x", "0" * 100):
            codigo, cuerpo, _ = _bajar(srv, f"/descarga?id={malo}")
            assert codigo == 400, (malo, codigo)
            assert b"OPENROUTER" not in cuerpo
    finally:
        srv.shutdown()


def la_carpeta_de_artefactos_no_se_sirve():
    srv = _servidor()
    try:
        for ruta in ("/artefactos/", "/artefactos/x/proyecto/app/main.py",
                     "/artefactos/x/libros-api.zip"):
            assert _bajar(srv, ruta)[0] == 404, ruta
    finally:
        srv.shutdown()


def la_demo_no_deja_pycache_ni_toca_salida():
    import demos
    import rapido
    salida = Path(rapido.__file__).resolve().parent / "salida"
    antes = sorted(p.name for p in salida.iterdir()) if salida.exists() else []
    demos.correr("proyecto")
    ahora = sorted(p.name for p in salida.iterdir()) if salida.exists() else []
    assert antes == ahora, "la demo de proyecto escribio en salida/"
    paq = E.sellar(_libros())
    with zipfile.ZipFile(io.BytesIO(paq.datos)) as z:
        assert not [n for n in z.namelist() if "__pycache__" in n or n.endswith(".pyc")]


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and getattr(fn, "__module__", "") == "__main__" \
                and not nombre.startswith(("probar", "_")):
            probar(nombre.replace("_", " "), fn)
    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
