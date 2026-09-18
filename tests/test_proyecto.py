"""El artefacto, sus rutas, y la cadena que lo verifica.

    python3 test_proyecto.py
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
import sys
import tempfile
from pathlib import Path

import dependencias as D
import fixture_proyecto as F
import proyecto as P
import verificacion_proyecto as V

AQUI = Path(__file__).parent
# Las rutas que apuntan a PRODUCCION se derivan de un modulo de produccion, nunca de
# __file__: asi siguen apuntando al sitio correcto viva donde viva este test. Cuando
# colgaban de `AQUI`, mover el test a tests/ los dejaba mirando una carpeta vacia y
# el test pasaba sin comprobar nada.
RAIZ = Path(P.__file__).resolve().parent
casos = []


def probar(nombre, fn):
    try:
        fn(); casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _libros():
    return P.desde_dict(F.ESPEC["nombre"], F.ARCHIVOS)


# ══ Rutas: el unico sitio por donde nace una ruta ═══════════════════════════

ATAQUES = [
    "../../etc/passwd", "/etc/passwd", "app/../../fuera.py", "~/x.py",
    "C:\\Windows\\x.py", "app/../../../root/.ssh/id_rsa", "__pycache__/x.pyc",
    ".env", ".git/config", "app/x.exe", "a/b/c/d/e/f/g/h.py", "", "   ",
    "app/x\x00.py", "app//..//y.py", "node_modules/mal.js",
]


def ninguna_ruta_se_escapa():
    """Si una sola pasa, el modelo puede escribir donde quiera."""
    colados = []
    for ruta in ATAQUES:
        try:
            P.ruta_segura(ruta)
            colados.append(ruta)
        except P.RutaProhibida:
            pass
    assert not colados, f"rutas que deberian estar prohibidas y pasan: {colados}"


def las_rutas_normales_si_pasan():
    for ruta in ("app/main.py", "app/libros/router.py", "tests/test_x.py",
                 "README.md", "requirements.txt", ".env.example", "app/__init__.py"):
        assert P.ruta_segura(ruta) == ruta, ruta


def añadir_un_archivo_con_ruta_mala_revienta():
    p = P.Proyecto("x")
    for ruta in ("../fuera.py", "/etc/passwd", ".env"):
        try:
            p.añadir(ruta, "x = 1")
            raise AssertionError(f"acepto {ruta!r}")
        except P.RutaProhibida:
            pass
    assert not p.listar(), "quedo algo dentro"


def los_topes_muerden():
    p = P.Proyecto("x")
    try:
        p.añadir("grande.py", "x" * (P.MAXIMO_ARCHIVO + 1))
        raise AssertionError("acepto un archivo por encima del tope")
    except P.RutaProhibida:
        pass


def el_nombre_del_proyecto_se_sanea():
    for crudo, limpio in (("Libros API!!", "libros-api"), ("../../etc", "etc"),
                          ('a"b\r\nc', "a-b-c"), ("", "proyecto"), ("Ñandú App", "nandu-app")):
        assert P.nombre_seguro(crudo) == limpio, (crudo, P.nombre_seguro(crudo))


def un_nombre_hostil_no_parte_una_cabecera():
    """Un \\r\\n en Content-Disposition inyecta cabeceras."""
    for crudo in ('x"\r\nSet-Cookie: a=b', "x\nY", 'a"b'):
        limpio = P.nombre_seguro(crudo)
        assert "\r" not in limpio and "\n" not in limpio and '"' not in limpio, limpio


def consultar_una_ruta_imposible_no_revienta():
    """Estricto al escribir, tolerante al leer. Cuando `obtener` lanzaba, una dependencia
    mal declarada por el modelo (`depende_de: ["app/libros/api"]`, sin extension) mataba
    la generacion entera — lo descubrio una corrida con modelo real."""
    p = _libros()
    for imposible in ("app/libros/api", "../fuera", ".env", "", "x" * 300):
        assert p.obtener(imposible) is None, imposible


def añadir_sigue_siendo_estricto():
    """Que leer sea tolerante no puede ablandar la escritura."""
    p = P.Proyecto("x")
    try:
        p.añadir("app/libros/api", "x = 1")
        raise AssertionError("acepto una ruta sin extension")
    except P.RutaProhibida:
        pass


# ══ El artefacto ════════════════════════════════════════════════════════════

def los_directorios_implicitos_aparecen():
    p = _libros()
    arbol = p.arbol()
    assert "app/" in arbol and "tests/" in arbol
    assert "core/" in arbol["app/"] and "libros/" in arbol["app/"]
    assert p.totales["directorios"] == 4, p.totales


def los_planos_son_lo_que_consume_el_ejecutor():
    """`skills.verificar_codigo` ya sabe ejecutar arboles: el puente es un dict."""
    import skills
    p = _libros()
    salida = skills.verificar_codigo(p.planos(), "python3 -c \"import app.main; print('ok')\"")
    assert "ok" in salida, salida[:200]


def sellar_congela_el_arbol():
    """Lo que se verifica tiene que ser lo que se empaqueta."""
    p = _libros().sellar()
    try:
        p.añadir("nuevo.py", "x = 1")
        raise AssertionError("se pudo modificar un proyecto sellado")
    except RuntimeError:
        pass


def materializar_conserva_los_subdirectorios():
    """`rapido.guardar` aplana con Path(ruta).name: por eso un proyecto no pasa por ahi."""
    destino = _libros().materializar(tempfile.mkdtemp())
    assert (destino / "app" / "libros" / "router.py").exists()
    assert (destino / "tests" / "test_libros.py").exists()
    assert len(list(destino.rglob("*.py"))) == 11, list(destino.rglob("*.py"))


def un_proyecto_no_se_escribe_encima_de_mirag():
    p = _libros()
    for destino in (RAIZ, RAIZ / "salida", RAIZ / "benchmarks"):
        try:
            p.materializar(destino)
            raise AssertionError(f"escribio en {destino}")
        except P.DestinoProhibido:
            pass


def el_hash_es_completo_no_truncado():
    """Aqui el hash es la PRUEBA de identidad, no una deteccion de cambios."""
    p = _libros()
    assert all(len(a.sha) == 64 for a in p.listar())


# ══ Imports: roto ≠ ausente ════════════════════════════════════════════════

def un_import_interno_roto_es_un_error():
    p = P.desde_dict("x", {"app/__init__.py": "", "app/main.py": "from app.no_hay import x\n"})
    _i, h = D.analizar(p)
    rotos = [x for x in h if x.clase == "import_interno_roto"]
    assert rotos and rotos[0].gravedad == D.ERROR, h


def un_simbolo_que_no_existe_es_un_error():
    """El manifiesto puede prometer `LibroRepo` y el archivo definir `RepoLibros`."""
    p = P.desde_dict("x", {"app/__init__.py": "", "app/bd.py": "def conectar():\n    ...\n",
                           "app/main.py": "from app.bd import inexistente\n"})
    _i, h = D.analizar(p)
    malos = [x for x in h if x.clase == "simbolo_inexistente"]
    assert malos and malos[0].gravedad == D.ERROR, h


def una_dependencia_ausente_NO_es_un_error():
    """Es la distincion que hace honesto el caso FastAPI."""
    p = P.desde_dict("x", {"app/__init__.py": "",
                           "app/main.py": "from fastapi import FastAPI\n",
                           "requirements.txt": "fastapi\n"})
    _i, h = D.analizar(p)
    ausentes = [x for x in h if x.clase == "dependencia_ausente"]
    assert ausentes, h
    assert all(x.gravedad == D.LIMITE for x in ausentes), \
        "una dependencia que falta se esta tratando como un error del proyecto"
    assert not [x for x in h if x.gravedad == D.ERROR], h


def la_stdlib_no_genera_hallazgos():
    p = P.desde_dict("x", {"app/__init__.py": "",
                           "app/main.py": "import json, sqlite3, threading\n"
                                          "from http.server import ThreadingHTTPServer\n"})
    _i, h = D.analizar(p)
    assert not h, h


def un_getattr_de_modulo_rebaja_la_gravedad():
    """PEP 562: el simbolo puede existir en runtime sin estar en el AST."""
    p = P.desde_dict("x", {"app/__init__.py": "",
                           "app/din.py": "def __getattr__(n):\n    return 1\n",
                           "app/main.py": "from app.din import lo_que_sea\n"})
    _i, h = D.analizar(p)
    assert not [x for x in h if x.clase == "simbolo_inexistente"], h


def el_proyecto_de_la_demo_no_tiene_ni_un_hallazgo_grave():
    _i, h = D.analizar(_libros())
    graves = [x for x in h if x.gravedad == D.ERROR]
    assert not graves, graves


# ══ La cadena y el estado ══════════════════════════════════════════════════

def el_proyecto_de_la_demo_sale_verificado():
    cert = V.certificar(_libros(), comando_test=F.ESPEC["comando_test"])
    assert cert.estado == V.VERIFICADO, f"{cert.estado}: {cert.por_que}"
    assert sum(1 for v in cert.marcas.values() if v == "PASS") >= 16, cert.marcas


def el_crud_se_ejercita_por_HTTP_de_verdad():
    cert = V.certificar(_libros(), comando_test=F.ESPEC["comando_test"])
    crud = {k: v for k, v in cert.marcas.items() if k.startswith("crud_")}
    assert len(crud) == 7, crud
    assert all(v == "PASS" for v in crud.values()), crud


def un_servidor_que_miente_se_caza():
    """El PUT devuelve 200 y no persiste. Un test complaciente no lo veria."""
    roto = dict(F.ARCHIVOS)
    roto["app/libros/repositorio.py"] = roto["app/libros/repositorio.py"].replace(
        'cur = con.execute("UPDATE libros SET titulo = ?, autor = ?, anio = ? WHERE id = ?",\n'
        '                          (datos["titulo"], datos.get("autor", ""), datos.get("anio"),\n'
        '                           libro_id))',
        'cur = con.execute("SELECT 1 FROM libros WHERE id = ?", (libro_id,))')
    cert = V.certificar(P.desde_dict("libros-api", roto))
    assert cert.estado != V.VERIFICADO, "un PUT que no persiste paso como verificado"
    assert cert.marcas.get([k for k in cert.marcas if "persiste" in k][0]) == "FAIL", cert.marcas


def fastapi_jamas_llega_a_verificado():
    p = P.desde_dict("api", {
        "app/__init__.py": "",
        "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "tests/__init__.py": "",
        "tests/test_x.py": "import unittest\nclass T(unittest.TestCase):\n"
                           "    def test_x(self):\n        pass\n",
        "requirements.txt": "fastapi\n"})
    cert = V.certificar(p)
    assert cert.estado == V.VALIDADO, f"{cert.estado}: {cert.por_que}"
    assert "fastapi" in cert.por_que
    assert "no hay evidencia" in cert.por_que


def un_import_roto_deja_el_proyecto_fallido():
    p = P.desde_dict("x", {"app/__init__.py": "", "app/main.py": "from app.no_hay import x\n",
                           "tests/__init__.py": "", "tests/test_x.py": "# t\n"})
    assert V.certificar(p).estado == V.FALLIDO


def una_fase_muda_no_puede_quedar_tapada():
    """Los 9 tests salieron SIN EVIDENCIA y los 7 marcadores del CRUD arrastraron el
    estado a VERIFICADO. Eso paso de verdad y no puede volver a pasar."""
    fases = (V.Fase("estructura", "ok", ""), V.Fase("sintaxis", "ok", ""),
             V.Fase("tests", "limitado", "SIN EVIDENCIA"), V.Fase("crud", "ok", ""))
    estado, por_que = V.derivar_estado(fases, {"crud_a": "PASS"}, (), ("crud_a",))
    assert estado == V.PARCIAL, estado
    assert "no produjo ni un marcador" in por_que


def si_el_comando_del_README_falla_no_es_verificado():
    """Es el comando que va a escribir quien descomprima el ZIP."""
    cert = V.certificar(_libros(), comando_test="python3 no_existe.py")
    assert cert.estado != V.VERIFICADO, cert.estado


def exit_cero_sin_marcadores_no_es_aprobar():
    fases = (V.Fase("estructura", "ok", ""), V.Fase("sintaxis", "ok", ""),
             V.Fase("tests", "limitado", ""))
    estado, por_que = V.derivar_estado(fases, {}, (), ())
    assert estado == V.EJECUTADO and "no es aprobar" in por_que


def si_el_plano_no_trae_tests_mirag_los_pone():
    """Medido sobre 6 corridas reales: en 5 el plano venia sin un solo archivo en tests/,
    aunque la peticion los pedia. La ESTRUCTURA es responsabilidad de Mirag, no del
    modelo; el contenido lo sigue escribiendo el."""
    import generador as G
    sin = [{"ruta": "app/main.py", "tipo": "entrypoint", "grupo": "nucleo",
            "exporta": ["crear_servidor"], "depende_de": []}]
    plano, añadidos = G.completar_plano(sin, {"entidad": "libro"})
    assert "tests/test_libro.py" in añadidos, añadidos
    nueva = next(f for f in plano if f["ruta"] == "tests/test_libro.py")
    assert nueva["grupo"] == "tests" and nueva["depende_de"] == ["app/main.py"]
    assert not G.validar_plano(plano, {"comando_test": "python3 -m unittest"})


def si_el_plano_ya_trae_tests_no_se_toca():
    import generador as G
    con = [{"ruta": "app/main.py", "tipo": "entrypoint", "grupo": "nucleo",
            "exporta": [], "depende_de": []},
           {"ruta": "tests/test_api.py", "tipo": "test", "grupo": "tests",
            "exporta": [], "depende_de": []}]
    plano, añadidos = G.completar_plano(con, {"entidad": "libro"})
    assert añadidos == [] and plano == con


def el_bucle_de_reparacion_esta_conectado():
    """Estuvo escrito y sin cablear, y lo destapo una corrida con modelo real: un import
    interno roto dejaba el proyecto en FALLIDO sin intentar arreglarlo siquiera.

    Se comprueba por COMPORTAMIENTO: se pasa un reparador de mentira y se exige que lo
    llamen. Un grep del fuente no distinguiria "declarado" de "conectado", que es
    exactamente el error que se esta fijando."""
    llamadas = []

    def reparador_falso(proy, errores, salida, intento):
        llamadas.append((len(errores), intento))
        arreglado = P.Proyecto(proy.nombre, proy.espec)
        for a in proy.listar():
            arreglado.añadir(a.ruta, a.texto, tipo=a.tipo)
        arreglado.añadir("app/roto.py", "def existe():\n    return 1\n")
        return arreglado, ("app/roto.py",), "faltaba el modulo"

    p = P.desde_dict("x", {"app/__init__.py": "",
                           "app/main.py": "from app.roto import existe\n",
                           "tests/__init__.py": "", "tests/test_x.py": "# t\n"})
    V.certificar(p, reparador=reparador_falso)
    assert llamadas, "el reparador no se llamo: el bucle no esta conectado"


def el_pipeline_le_pasa_un_reparador_de_verdad():
    """Y que el que se conecta sea el real, no cualquiera."""
    import ast
    import pipeline
    fuente = ast.parse(Path(pipeline.__file__).read_text())
    fn = next(n for n in ast.walk(fuente)
              if isinstance(n, ast.FunctionDef) and n.name == "_ejecutar_proyecto")
    llamada = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
               and any(k.arg == "reparador" for k in n.keywords)]
    assert llamada, "certificar() se llama sin reparador"


def el_estado_solo_se_decide_en_un_sitio():
    """`skills.veredicto` existe porque el verde estaba re-derivado en ocho sitios y un
    TIMEOUT era "error" en una linea y "verde" catorce mas abajo.

    Referirse al estado (un icono, un contrato de test) es legitimo. DECIDIRLO no: eso
    es devolverlo. Asi que se buscan `return` de estos literales fuera de su modulo.
    """
    import ast
    ESTADOS = {"VERIFICADO", "PARCIAL", "VALIDADO", "FALLIDO", "EJECUTADO", "GENERADO"}
    decisiones = []
    fuentes = sorted(RAIZ.glob("*.py"))
    assert len(fuentes) >= 20, \
        f"el escaneo no ve produccion: {len(fuentes)} archivos en {RAIZ}"
    for archivo in fuentes:
        if archivo.name == "verificacion_proyecto.py" or archivo.name.startswith("test_"):
            continue
        for nodo in ast.walk(ast.parse(archivo.read_text())):
            if not isinstance(nodo, ast.Return) or nodo.value is None:
                continue
            devueltos = (nodo.value.elts if isinstance(nodo.value, ast.Tuple)
                         else [nodo.value])
            for d in devueltos:
                if isinstance(d, ast.Constant) and d.value in ESTADOS:
                    decisiones.append(f"{archivo.name}:{d.lineno} devuelve {d.value!r}")
    assert not decisiones, \
        f"el estado se decide fuera de verificacion_proyecto: {decisiones}"


def el_icono_y_el_contrato_pueden_nombrar_el_estado():
    """Lo anterior no puede ser tan estricto que prohiba REFERIRSE al estado: la UI
    necesita un icono por estado y un contrato de demo necesita exigir uno."""
    import demos
    assert demos.CANONICAS["proyecto"]["exige"]["estado_proyecto"] == ("VERIFICADO",)


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
