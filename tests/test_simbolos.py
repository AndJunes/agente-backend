"""Los tests del indice de simbolos. Sin pytest, como el resto del proyecto:

    python3 test_simbolos.py

Se prueba contra dos repos distintos a proposito: `pruebas/app/` es un fixture
diminuto y controlado (se pueden afirmar numeros exactos), y `agente_backend/`
—este mismo codigo— es el caso real, sucio y grande. Un indexador que solo
funciona con su propio fixture no sirve para nada.
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

import simbolos

AQUI = Path(__file__).parent
# El fixture viaja CON los tests: es un repo falso, no produccion.
FIXTURE = AQUI / "fixtures" / "repo_ejemplo"
APP = simbolos.indexar(FIXTURE)
# Se indexa la raiz de PRODUCCION, no la del test: lo que se comprueba es que el
# indexador encuentre los simbolos de Mirag (verificar_codigo en skills.py), y desde
# tests/ no hay ningun skills.py que encontrar.
_RAIZ_PROD = Path(simbolos.__file__).resolve().parent
MIRAG = simbolos.indexar(_RAIZ_PROD)

PREGUNTA_JWT = "¿dónde se valida el JWT?"

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:                      # un error inesperado tambien es un fallo
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def uno(simbolos_, nombre, archivo=None):
    """El simbolo con ese nombre exacto. Falla si no hay exactamente uno.

    `archivo` hace falta en el repo de verdad: `indexar` existe en simbolos.py y
    ademas como metodo en vectores.py, y eso es normal, no un error del indice.
    """
    hallados = [s for s in simbolos_ if s.nombre == nombre
                and (archivo is None or s.archivo == archivo)]
    assert len(hallados) == 1, f"{nombre}: esperaba 1 simbolo, hay {len(hallados)}"
    return hallados[0]


def nombres(resultados):
    return [s.nombre for s, _ in resultados]


# ── lo que el indice tiene que saber de cada cosa ────────────────────────────

def encuentra_una_funcion():
    s = uno(APP, "validate_token")
    assert s.tipo == "funcion", s.tipo
    assert s.archivo == "auth.py", s.archivo
    assert s.firma == "validate_token(token: str) -> dict", s.firma
    assert s.doc.startswith("Valida un token JWT"), s.doc
    assert s.padre == "", s.padre
    assert nombres(simbolos.buscar(APP, "validate token", k=3))[0] == "validate_token"


def encuentra_una_clase():
    s = uno(APP, "AuthService")
    assert s.tipo == "clase", s.tipo
    assert s.firma == "class AuthService", s.firma
    assert s.doc.startswith("Emite tokens"), s.doc
    assert nombres(simbolos.buscar(APP, "AuthService", k=3))[0] == "AuthService"
    # y la clase de ruido tambien, para que no parezca que solo sabe de auth
    assert uno(APP, "UserRepository").tipo == "clase"


def encuentra_un_metodo_con_su_padre():
    s = uno(APP, "issue_token")
    assert s.tipo == "metodo", s.tipo
    assert s.padre == "AuthService", f"un metodo sin clase contenedora: {s.padre!r}"
    assert s.firma == "issue_token(self, user_id: str, vigencia: int=VIGENCIA) -> str", s.firma
    # los metodos de la clase de ruido tambien llevan su padre
    assert uno(APP, "find_by_email").padre == "UserRepository"


def encuentra_un_test():
    s = uno(APP, "token_caducado_se_rechaza")
    assert s.tipo == "test", f"deberia ser test por vivir en tests/: {s.tipo}"
    assert s.archivo == "tests/test_auth.py", s.archivo
    # el modulo sigue siendo modulo aunque el archivo sea de tests
    assert uno(APP, "test_auth").tipo == "modulo"


def el_modulo_tambien_es_un_simbolo():
    s = uno(APP, "middleware")
    assert s.tipo == "modulo", s.tipo
    assert s.linea == 1, s.linea
    assert "auth" in s.importa, s.importa


def parte_snake_case_y_camel_case():
    """Sin esto, 'validar' no casa con `validate_token` ni 'jwt' con `verifyJWT`."""
    assert simbolos.palabras("validate_token") == ["validate", "token"]
    assert simbolos.palabras("verifyJWT") == ["verify", "jwt"]
    assert simbolos.palabras("UserRepository") == ["user", "repository"]
    assert simbolos.palabras("SECRET") == ["secret"]


def el_resumen_cuenta_bien():
    r = simbolos.resumen(APP)
    esperado = {"archivos": 4, "modulos": 4, "clases": 3, "funciones": 14,
                "tests": 5, "importados": 9}
    assert r == esperado, f"{r} != {esperado}"
    # y las cuentas cuadran con la lista: nada se queda sin clasificar
    assert r["modulos"] + r["clases"] + r["funciones"] + r["tests"] == len(APP)


# ── la busqueda ──────────────────────────────────────────────────────────────

def la_pregunta_en_espanol_encuentra_el_codigo_en_ingles():
    """El caso de uso: preguntar en español sobre simbolos escritos en ingles."""
    top3 = nombres(simbolos.buscar(APP, PREGUNTA_JWT, k=3))
    for esperado in ("validate_token", "verify_jwt", "auth_middleware"):
        assert esperado in top3, f"{esperado} no esta en el top-3: {top3}"


def _sin_diccionario(fn):
    """Corre algo con SINONIMOS apagado: es la unica forma de saber cuanto aporta."""
    original = simbolos.SINONIMOS
    try:
        simbolos.SINONIMOS = {}
        return fn()
    finally:
        simbolos.SINONIMOS = original


def el_caso_jwt_NO_depende_del_diccionario():
    """Hallazgo incomodo, escrito como test para que no se olvide.

    El top-3 de la pregunta del JWT sale igual con el diccionario apagado. No lo
    resuelve el puente español->ingles, lo resuelven dos cosas mas tontas:
    'valida' y 'validate' son cognados (casan por prefijo de 4 letras) y los
    docstrings del fixture estan en español, asi que `auth_middleware` ya dice
    "Valida el token JWT" en su propia linea de doc.
    O sea: este caso NO demuestra que SINONIMOS sirva. Lo demuestra el de abajo.
    """
    top3 = _sin_diccionario(lambda: nombres(simbolos.buscar(APP, PREGUNTA_JWT, k=3)))
    esperado = ["validate_token", "verify_jwt", "auth_middleware"]
    assert sorted(top3) == sorted(esperado), \
        f"ahora el diccionario SI hace falta para el JWT: sin el sale {top3}"


def el_puente_aporta_donde_no_hay_cognado():
    """'guardar' no se parece a 'save': aqui el diccionario es lo unico que puentea."""
    consulta = "¿dónde se guarda el usuario?"
    guardar = uno(APP, "save")
    con = simbolos.puntuar(guardar, consulta)
    sin = _sin_diccionario(lambda: simbolos.puntuar(guardar, consulta))
    assert con >= 2 * sin, f"el diccionario casi no aporta: {con:.1f} con, {sin:.1f} sin"
    assert nombres(simbolos.buscar(APP, consulta, k=3))[0] == "save"
    assert "UserRepository" in nombres(simbolos.buscar(APP, consulta, k=3))
    assert "UserRepository" not in _sin_diccionario(
        lambda: nombres(simbolos.buscar(APP, consulta, k=3)))


def el_diccionario_sigue_siendo_una_lista_corta():
    """15-25 entradas escritas a mano. Si crece, deja de ser 'una lista a mano'."""
    assert 15 <= len(simbolos.SINONIMOS) <= 25, len(simbolos.SINONIMOS)


def una_consulta_irrelevante_no_arrastra_auth():
    """Una consulta ajena de verdad no devuelve nada.

    Antes la consulta era 'pagos con tarjeta', con el comentario «no toca este repo». Dejo
    de ser cierto el dia que aparecio `blockchain/wallet/servicio.py` con `pagos()` y
    `ultimo_pago()`: el indexador encontraba tres simbolos y el test se ponia rojo. No
    estaba roto el indice, estaba caduco el supuesto. Se separa en dos casos: aqui, una
    consulta que sigue siendo ajena a los dos indices; abajo, la de pagos, que ahora es un
    acierto y no un fallo.
    """
    fuerte = max([p for _, p in simbolos.buscar(APP, PREGUNTA_JWT, k=1)] or [0])
    assert fuerte > 0, "el indice del fixture no puntua nada: no hay con que comparar"
    for indice, etiqueta in ((APP, "fixture"), (MIRAG, "mirag")):
        for consulta in ("streaming de video con webrtc", "recetas de cocina italiana"):
            for s, p in simbolos.buscar(indice, consulta, k=5):
                assert s.archivo not in ("auth.py", "middleware.py"), \
                    f"[{etiqueta}] {s.nombre} sale en {consulta!r} ({p:.1f})"
                assert p < fuerte * 0.25, \
                    f"[{etiqueta}] {s.nombre} puntua {p:.1f} en {consulta!r}"


def una_consulta_de_pagos_encuentra_la_capa_y_no_la_de_auth():
    """El caso que antes era 'irrelevante' y ahora tiene respuesta correcta.

    Comprueba algo mas fuerte que el test viejo: no solo que no salga `auth`, sino que lo
    que sale sea de la capa que de verdad habla de dinero.
    """
    hallados = simbolos.buscar(MIRAG, "pagos con tarjeta", k=5)
    assert hallados, "el indice ya no encuentra la capa de pagos: ¿dejo de indexarse?"
    for s, p in hallados:
        assert "blockchain/" in s.archivo, \
            f"{s.nombre} ({s.archivo}) sale en una consulta de pagos y no es de la capa"
    # Y en el fixture, que no tiene nada de pagos, sigue sin salir auth.
    for s, p in simbolos.buscar(APP, "pagos con tarjeta", k=5):
        assert s.archivo not in ("auth.py", "middleware.py"), s.nombre


def sin_terminos_utiles_no_se_inventa_nada():
    assert simbolos.buscar(APP, "¿y esto como es que se hace?") == []
    assert simbolos.buscar(APP, "") == []


def las_llamadas_dan_la_relacion():
    """auth_middleware -> validate_token es la unica pista de que el middleware
    es parte de la respuesta a '¿donde se valida el JWT?'."""
    medio = uno(APP, "auth_middleware")
    assert "validate_token" in medio.llamadas, medio.llamadas
    assert "verify_jwt" in uno(APP, "validate_token").llamadas
    # y una clase no se atribuye las llamadas de sus metodos
    assert "firmar" not in uno(APP, "AuthService").llamadas, uno(APP, "AuthService").llamadas
    assert "firmar" in uno(APP, "issue_token").llamadas


# ── lo que tiene que aguantar ────────────────────────────────────────────────

def un_archivo_roto_no_rompe_el_indexado():
    """Mientras escribes codigo hay archivos a medias. El indice se hace igual."""
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "bueno.py").write_text("def suma(a, b):\n    return a + b\n")
        (raiz / "roto.py").write_text("def mal(:\n    esto no es python\n")
        (raiz / "vacio.py").write_text("")
        indice = simbolos.indexar(raiz)
        assert any(s.nombre == "suma" for s in indice), "se perdio el archivo bueno"
        assert not any(s.archivo == "roto.py" for s in indice), "el roto colo simbolos"
        assert any(s.nombre == "vacio" for s in indice), "un .py vacio sigue siendo un modulo"


def una_carpeta_vacia_da_una_lista_vacia():
    with tempfile.TemporaryDirectory() as tmp:
        assert simbolos.indexar(tmp) == []
        assert simbolos.resumen([])["archivos"] == 0
    assert simbolos.indexar(_RAIZ_PROD / "no-existe-esta-carpeta") == []


def indexar_mirag_encuentra_simbolos_de_verdad():
    """El caso real: este mismo repo, con sus 25 archivos y su ruido."""
    assert len(MIRAG) > 200, f"solo {len(MIRAG)} simbolos en todo el repo"
    for nombre, archivo in (("verificar_codigo", "skills.py"), ("buscar_en_docs", "skills.py"),
                            ("indexar", "simbolos.py")):
        s = uno(MIRAG, nombre, archivo)
        assert s.firma.startswith(f"{nombre}("), s.firma
    # verificar_codigo si tiene docstring; buscar_en_docs es un delegador de una linea y no
    # lo tiene: el indice no puede exigirlo, solo aprovecharlo cuando esta.
    assert uno(MIRAG, "verificar_codigo", "skills.py").doc.startswith("Escribe los archivos")
    assert uno(MIRAG, "buscar_en_docs", "skills.py").doc == ""
    assert nombres(simbolos.buscar(MIRAG, "verificar codigo", k=1)) == ["verificar_codigo"]
    assert nombres(simbolos.buscar(MIRAG, "buscar en docs", k=1)) == ["buscar_en_docs"]
    r = simbolos.resumen(MIRAG)
    assert r["archivos"] > 20 and r["clases"] > 5 and r["tests"] > 0, r


def el_orden_es_determinista():
    """Dos indexados de lo mismo dan exactamente lo mismo: sin esto, ningun numero vale."""
    assert simbolos.indexar(FIXTURE) == APP
    assert simbolos.buscar(APP, PREGUNTA_JWT, k=5) == simbolos.buscar(APP, PREGUNTA_JWT, k=5)


def la_clasificacion_no_depende_de_donde_este_guardado_el_proyecto():
    """Un proyecto en `~/tests/loquesea/` no puede tener todos sus simbolos marcados como
    test solo por donde vive. Lo destapo mover este fixture a tests/fixtures/: sus 14
    funciones pasaron a contarse como 19 tests sin cambiar una linea de su codigo."""
    import tempfile, shutil
    resumen_real = simbolos.resumen(simbolos.indexar(FIXTURE))
    with tempfile.TemporaryDirectory() as tmp:
        # el mismo arbol, pero colgando de una carpeta llamada "tests"
        destino = Path(tmp) / "tests" / "un_proyecto"
        shutil.copytree(FIXTURE, destino)
        resumen_mudado = simbolos.resumen(simbolos.indexar(destino))
    assert resumen_mudado == resumen_real, \
        f"la clasificacion cambio al mover el proyecto:\n  {resumen_real}\n  {resumen_mudado}"
    assert resumen_real["funciones"] > 0, "no clasifica ninguna funcion"


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if callable(fn) and not nombre.startswith(("probar", "uno", "nombres", "_")) \
                and fn.__module__ == "__main__":
            probar(nombre.replace("_", " "), fn)

    for ok, nombre, error in casos:
        print(f"  {'✅' if ok else '❌'} {nombre}" + (f"  → {error}" if error else ""))
    fallos = sum(1 for ok, _, _ in casos if not ok)
    print(f"\n{len(casos)} casos · {'TODO OK' if not fallos else f'{fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
