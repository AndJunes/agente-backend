"""Los tres CRITICOS de la auditoria, con pruebas NEGATIVAS.

Un test que comprueba que algo funciona no sirve aqui: hay que comprobar que algo
NO ocurre. Por eso casi todos estos casos afirman sobre rechazos.

    python3 test_seguridad.py
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
import http.client
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pipeline
import rapido
import skills

AQUI = Path(__file__).parent
casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


# ══ A · el servidor no sirve el directorio ═══════════════════════════════════

_SERVIDOR = {}


def _arrancar():
    """Un servidor de verdad en un puerto libre, para pedirle cosas por HTTP."""
    if _SERVIDOR:
        return _SERVIDOR["puerto"]
    import server
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.2)
    _SERVIDOR.update(puerto=httpd.server_address[1], httpd=httpd)
    return _SERVIDOR["puerto"]


def _get(ruta):
    c = http.client.HTTPConnection("127.0.0.1", _arrancar(), timeout=5)
    c.request("GET", ruta)
    r = c.getresponse()
    cuerpo = r.read()
    c.close()
    return r.status, cuerpo


def el_env_no_se_sirve():
    """El caso que entregaba la OPENROUTER_API_KEY a toda la red local."""
    estado, cuerpo = _get("/.env")
    assert estado == 404, f"GET /.env devolvio {estado}"
    assert b"OPENROUTER" not in cuerpo, "el cuerpo del 404 filtra el contenido"


def los_archivos_internos_no_se_sirven():
    for ruta in ("/trazas.jsonl", "/trazas_noche.jsonl", "/eval_cache.json",
                 "/index.html.bak", "/server.py", "/agent.py", "/.env.example",
                 "/benchmarks/ganancias.json", "/conocimientos/04-databases.md",
                 "/salida/COMO_EJECUTAR.txt"):
        estado, _ = _get(ruta)
        assert estado == 404, f"GET {ruta} devolvio {estado}, deberia ser 404"


def el_traversal_tampoco():
    for ruta in ("/../.env", "/..%2f.env", "/./../.env", "//.env", "/%2e%2e/.env"):
        estado, cuerpo = _get(ruta)
        assert estado != 200 or b"OPENROUTER" not in cuerpo, f"{ruta} filtro algo"


def la_pagina_si_se_sirve():
    for ruta in ("/", "/index.html"):
        estado, cuerpo = _get(ruta)
        assert estado == 200, f"GET {ruta} devolvio {estado}"
        assert b"Mirag" in cuerpo, "no parece index.html"


def escucha_solo_en_localhost():
    import server as _srv
    fuente = Path(_srv.__file__).read_text()
    assert '("127.0.0.1", 8000)' in fuente, "el bind sigue abierto a todas las interfaces"
    assert '("", 8000)' not in fuente


# ══ B · calcular no ejecuta Python ═══════════════════════════════════════════

def la_aritmetica_sigue_funcionando():
    for expresion, esperado in (("2+3", "5"), ("1847 * 293", "541171"),
                                ("(10-4)/3", "2.0"), ("2**10", "1024"),
                                ("-5 + 3.5", "-1.5"), ("7 % 3", "1"), ("10 // 3", "3")):
        assert skills.calcular(expresion) == esperado, f"{expresion} → {skills.calcular(expresion)}"


def ningun_ataque_se_ejecuta():
    ataques = [
        "__import__('os')", "__import__('os').environ",
        "__import__('os').environ['OPENROUTER_API_KEY']",
        "__import__('os').system('echo hola')",
        "open('/etc/passwd').read()", "().__class__.__bases__[0].__subclasses__()",
        "[x for x in range(3)]", "{'a': 1}", "'texto'", "'a'*100",
        "print(1)", "lambda: 1", "globals()", "locals()", "vars()",
        "eval('1+1')", "exec('x=1')", "x", "True", "None",
        "(1).__class__", "1 if True else 2", "[1,2][0]", "f'{1}'",
    ]
    for a in ataques:
        r = skills.calcular(a)
        assert r.startswith(("Rechazado", "No es una expresion")), \
            f"NO SE RECHAZO: calcular({a!r}) → {r[:90]}"


def no_se_cuelga_con_numeros_enormes():
    r = skills.calcular("2**10**9")
    assert "exponente" in r.lower() or "Rechazado" in r, r[:80]


def no_hay_ninguna_llamada_a_eval():
    """Estructural, no textual.

    La primera version de este test buscaba el string 'eval(expresion)' en el fuente
    y fallaba por el docstring que explica que habia ANTES. Buscar texto es el mismo
    tipo de test debil que la auditoria critico: aqui se parsea el AST y se comprueba
    que no existe una llamada a ninguna de las cuatro puertas de ejecucion.
    """
    import ast as _ast
    peligrosas = {"eval", "exec", "compile", "__import__"}
    arbol = _ast.parse(Path(skills.__file__).read_text())
    llamadas = [n.func.id for n in _ast.walk(arbol)
                if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)
                and n.func.id in peligrosas]
    assert not llamadas, f"skills.py sigue llamando a {set(llamadas)}"


# ══ C · guardar sobrevive a lo que el propio proyecto te dice que hagas ══════

def el_ciclo_entregar_ejecutar_entregar():
    """entregar → ejecutar como dice COMO_EJECUTAR.txt → entregar otra vez."""
    entrega = {"archivos": {"m.py": "VALOR = 1",
                            "test_m.py": "import m\nprint('TEST:a:PASS')"},
               "comando_test": "python3 test_m.py", "decisiones": "x"}
    with tempfile.TemporaryDirectory() as tmp:
        rapido.guardar(entrega, carpeta=tmp)
        r = subprocess.run(["/opt/homebrew/bin/python3", "test_m.py"], cwd=tmp,
                           capture_output=True, text=True)
        assert (Path(tmp) / "__pycache__").is_dir(), \
            "el test no creo __pycache__: el caso no se esta reproduciendo"
        rapido.guardar(entrega, carpeta=tmp)          # <- aqui reventaba
        assert not (Path(tmp) / "__pycache__").exists(), "el cleanup dejo el directorio"
        assert (Path(tmp) / "m.py").exists()


def limpia_directorios_anidados():
    with tempfile.TemporaryDirectory() as tmp:
        hondo = Path(tmp) / "a" / "b" / "c"
        hondo.mkdir(parents=True)
        (hondo / "x.txt").write_text("x")
        rapido.guardar({"archivos": {"y.py": "1"}, "comando_test": "python3 y.py",
                        "decisiones": ""}, carpeta=tmp)
        assert not (Path(tmp) / "a").exists()


def la_carpeta_por_defecto_esta_anclada_al_modulo():
    """Relativa al cwd, arrancar desde otro sitio borraba un salida/ ajeno."""
    import inspect
    fuente = inspect.getsource(rapido.guardar)
    assert "Path(__file__).parent" in fuente, "sigue siendo relativa al cwd"


# ══ D · un fallo al guardar no se lleva la respuesta ═════════════════════════

def la_respuesta_sobrevive_a_un_fallo_de_persistencia():
    import dobles
    original = rapido.guardar
    rapido.guardar = lambda *a, **k: (_ for _ in ()).throw(OSError("disco lleno"))
    try:
        with dobles.usar(dobles.CODIGO_CALCULADORA):
            e = pipeline.ejecutar("Crea calculator.py con calculate y tests",
                                  guardar=True, carpeta=tempfile.mkdtemp())
        assert e.entrega, "se perdio la entrega"
        assert skills.veredicto(e.salida)[0] == "verde", "se perdio la verificacion"
        assert [x for x in e.evidencia if x["estado"] == "verificado"], "se perdio la evidencia"
        paso = next((p for p in e.pasos if p.nombre == "persistencia"), None)
        assert paso and paso.estado == "error", "el fallo de guardado no se registro"
        assert "disco lleno" in paso.resumen, paso.resumen
    finally:
        rapido.guardar = original


def encadenar_comandos_no_ejecuta_el_segundo():
    """No basta con que la lista blanca mire el primer token: si el comando fuera a un
    shell, `python3 t.py; rm -rf X` correria el rm igual. Se comprueba con un canario
    en disco, no leyendo el mensaje de error — un rechazo puede llegar por otra via y
    una sonda que busca texto no distingue 'rechazado' de 'ejecutado y fallo'."""
    import skills
    canario = Path(tempfile.mkdtemp()) / "vivo.txt"
    canario.write_text("no me borres")
    for cmd in (f"python3 t.py; rm -rf {canario.parent}",
                f"python3 t.py && rm -rf {canario.parent}",
                f"python3 t.py | tee {canario}"):
        skills.verificar_codigo({"t.py": "print('hola')"}, cmd)
        assert canario.exists() and canario.read_text() == "no me borres", \
            f"el comando encadenado se ejecuto: {cmd!r}"


def el_ejecutor_no_usa_shell():
    """La razon POR LA QUE lo anterior se cumple. Si alguien pone shell=True, esto falla."""
    import ast
    import skills
    fuente = ast.parse(Path(skills.__file__).read_text())
    for n in ast.walk(fuente):
        if isinstance(n, ast.Call) and "run" in ast.dump(n.func):
            for kw in n.keywords:
                assert kw.arg != "shell" or not getattr(kw.value, "value", False), \
                    "subprocess con shell=True: la lista blanca deja de servir"


def el_head_tampoco_sirve_el_directorio():
    """El docstring de do_GET decia "una sola ruta, ni una mas" y era MENTIRA para HEAD.

    do_GET estaba sobreescrito; do_HEAD seguia siendo el de SimpleHTTPRequestHandler,
    que pasa por translate_path() y responde sobre el directorio entero. Medido antes
    del arreglo: `HEAD /.env` -> 200 con Content-Length: 93 y Last-Modified. No filtraba
    el cuerpo, pero si que el archivo existe, cuanto mide y cuando se toco.

    Sobrevivio a toda la auditoria porque los 15 tests de seguridad preguntaban con GET.
    Una prueba que solo usa un metodo solo demuestra ese metodo.
    """
    import http.client
    import threading
    from http.server import ThreadingHTTPServer

    import server
    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=20)
        for ruta in ("/.env", "/trazas.jsonl", "/trazas_noche.jsonl", "/server.py",
                     "/eval_cache.json", "/salida/calculator.py", "/benchmarks/ganancias.json"):
            for metodo in ("GET", "HEAD"):
                c.request(metodo, ruta)
                r = c.getresponse()
                cuerpo = r.read()
                assert r.status == 404, f"{metodo} {ruta} -> {r.status} (filtra que existe)"
                assert not r.getheader("Last-Modified"), f"{metodo} {ruta} filtra la fecha"
                assert b"OPENROUTER" not in cuerpo
        for ruta in ("/", "/index.html"):
            for metodo in ("GET", "HEAD"):
                c.request(metodo, ruta); r = c.getresponse(); r.read()
                assert r.status == 200, f"{metodo} {ruta} -> {r.status}"
    finally:
        srv.shutdown()


def la_lista_blanca_esta_cerrada():
    """Que rutas existen, afirmado por igualdad y no por "ninguna de estas filtra".

    Hasta ahora ningun test decia cuantas rutas hay: `head_y_get_pasan_por_la_misma_lista`
    impide que las listas se dupliquen, pero no que crezcan. Una ruta nueva entraba en
    silencio. Esto la obliga a pasar por aqui.
    """
    import ast

    import server
    assert set(server.Handler.RUTAS) == {"/", "/index.html"}, server.Handler.RUTAS
    assert set(server.Handler.RUTAS_POST) == {"/", "/chat"}, server.Handler.RUTAS_POST
    # Las rutas que `_servir` despacha aparte de la tupla, por su literal.
    fuente = ast.parse(Path(server.__file__).read_text())
    handler = next(n for n in ast.walk(fuente)
                   if isinstance(n, ast.ClassDef) and n.name == "Handler")
    servir = next(n for n in handler.body
                  if isinstance(n, ast.FunctionDef) and n.name == "_servir")
    literales = {n.value for n in ast.walk(servir) if isinstance(n, ast.Constant)
                 and isinstance(n.value, str) and n.value.startswith("/")}
    assert literales == {"/descarga", "/api/blockchain/agent"}, \
        f"hay rutas nuevas sin declarar en este test: {literales}"


def las_carpetas_nuevas_tampoco_se_sirven():
    """La capa blockchain trae un venv, un lock y un pyproject. Ninguno es publico."""
    for ruta in ("/blockchain/config.py", "/blockchain/.venv/pyvenv.cfg",
                 "/blockchain/pyproject.toml", "/blockchain/uv.lock",
                 "/blockchain/wallet/claves.py", "/pyproject.toml", "/uv.lock"):
        estado, cuerpo = _get(ruta)
        assert estado == 404, f"{ruta} devolvio {estado}"
        assert b"STELLAR" not in cuerpo and b"SECRET" not in cuerpo, ruta


def la_ruta_de_blockchain_no_filtra_la_clave():
    """La unica ruta nueva. Con la capa apagada contesta, pero no puede llevar un secreto."""
    import json
    import re
    estado, cuerpo = _get("/api/blockchain/agent")
    assert estado == 200, estado
    d = json.loads(cuerpo)
    assert "disponible" in d, d
    assert not re.search(rb"S[A-Z2-7]{55}", cuerpo), "salio algo con forma de semilla"
    assert b"OPENROUTER" not in cuerpo

def head_y_get_pasan_por_la_misma_lista():
    """Dos listas blancas separadas acaban divergiendo. Tiene que haber UNA."""
    import ast

    import server
    fuente = ast.parse(Path(server.__file__).read_text())
    handler = next(n for n in ast.walk(fuente)
                   if isinstance(n, ast.ClassDef) and n.name == "Handler")
    metodos = {n.name for n in handler.body if isinstance(n, ast.FunctionDef)}
    assert {"do_GET", "do_HEAD", "_servir"} <= metodos, metodos
    # y que ninguno de los dos traiga su propia tupla de rutas
    for nombre in ("do_GET", "do_HEAD"):
        cuerpo = next(n for n in handler.body
                      if isinstance(n, ast.FunctionDef) and n.name == nombre)
        literales = [n for n in ast.walk(cuerpo) if isinstance(n, ast.Constant)
                     and isinstance(n.value, str) and n.value.startswith("/")]
        assert not literales, f"{nombre} tiene su propia lista de rutas: {literales}"


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
