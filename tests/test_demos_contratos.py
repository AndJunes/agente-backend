"""Las tres demos son el contrato del producto, no una captura de pantalla.

`331 tests, 0 rojas` no es el final de la verificacion: el banco a nivel agente descubrio
un `needs_code` roto que la suite entera no cubria. Por eso las tres demos que se enseñan
se comprueban aqui de punta a punta — respuesta, estado, evidencia, traza y codigo — y
cuando el contrato es de UI se levanta el servidor DE VERDAD en vez de leer el HTML.

    python3 test_demos_contratos.py
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
import json
import shutil
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import demos
import server

AQUI = Path(__file__).parent
import server as _srv
# `index.html` es de PRODUCCION: se ancla al modulo que lo sirve, no a esta carpeta.
# Colgado de `AQUI` dejaba de encontrarse en cuanto el test cambiaba de sitio.
_PAGINA = Path(_srv.__file__).resolve().parent / "index.html"
casos = []


def probar(nombre, fn):
    try:
        fn(); casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _por_http(pregunta, modo="pipeline"):
    """El servidor real en un puerto libre. Devuelve los eventos SSE."""
    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=300)
        c.request("POST", "/", json.dumps({"pregunta": pregunta, "modo": modo}),
                  {"Content-Type": "application/json"})
        cuerpo = c.getresponse().read().decode()
    finally:
        srv.shutdown()
    return [json.loads(l[6:]) for l in cuerpo.splitlines() if l.startswith("data: ")]


def _fin(eventos):
    return next(e for e in eventos if e.get("tipo") == "fin")


# ══ Los tres contratos ══════════════════════════════════════════════════════

def demo_conocimiento_cumple():
    _e, inf = demos.correr("conocimiento")
    assert inf["cumple"], inf["fallos"]
    assert not inf["observado"]["hay_codigo"], "una pregunta conceptual no entrega codigo"


def demo_construccion_cumple():
    _e, inf = demos.correr("construccion")
    assert inf["cumple"], inf["fallos"]
    o = inf["observado"]
    assert o["ejecutado"] and o["estado"] == "verde", o
    assert o["propiedades_verificadas"] >= 1, "verde sin una sola propiedad demostrada"


def demo_abstencion_cumple():
    _e, inf = demos.correr("abstencion")
    assert inf["cumple"], inf["fallos"]
    assert inf["observado"]["suficiencia"] in ("mencionado", "ausente")
    assert not inf["observado"]["hay_codigo"]


def la_abstencion_avisa_antes_de_responder():
    """Lo primero que se lee tiene que ser el aviso, no la respuesta."""
    _e, inf = demos.correr("abstencion")
    cabeza = inf["markdown"].strip()[:200].lower()
    assert "corpus" in cabeza, f"el aviso no va primero: {cabeza[:90]!r}"


def la_demo_de_codigo_explica_que_hizo():
    """Sin esto la pagina saltaba de la pregunta a la tabla de evidencia: se veia QUE se
    verifico y nunca POR QUE se hizo asi."""
    _e, inf = demos.correr("construccion")
    md = inf["markdown"]
    assert "## Qué se hizo" in md, "no explica las decisiones"
    assert md.index("## Qué se hizo") < md.index("## Evidencia"), "el porqué va despues"


def el_verde_nunca_se_presenta_como_correcto():
    _e, inf = demos.correr("construccion")
    assert "no *es correcto*" in inf["markdown"]


def cada_demo_corre_el_guion_que_anuncia():
    """La pregunta de `construccion` decia "division por cero" y el reconocedor por regex
    se la llevaba al guion de `reparacion`: la pagina anunciaba una demo y corria la otra.
    Un producto no puede equivocarse sobre lo que te esta enseñando."""
    for clave, caso in demos.CANONICAS.items():
        porRegex = demos.reconocer(caso["pregunta"])[0]
        assert porRegex == caso["guion"], \
            f"{clave} declara el guion {caso['guion']!r} y por texto le tocaria {porRegex!r}"


def la_demo_de_abstencion_no_tiene_guion_a_proposito():
    assert demos.CANONICAS["abstencion"]["guion"] is None
    guion = demos.por_clave(None)
    assert len(guion) == 1, "el 'sin modelo' no puede ser un guion con varias respuestas"


def el_codigo_se_presenta_segun_lo_observado_no_segun_una_etiqueta():
    """La pagina decia "nadie ha comprobado este codigo" con 6 marcadores en verde: el
    veredicto salia de un evento `verificar_codigo` que el pipeline NO emite."""
    fin = _fin(_por_http(demos.CANONICAS["construccion"]["pregunta"]))
    assert fin["evidencia"]["observed"]["estado"] == "verde"
    html = _PAGINA.read_text()
    assert "DEL_EJECUTOR" in html, "seccionCodigo no lee lo observado"
    i = html.index("function seccionCodigo")
    assert "observado ? (DEL_EJECUTOR" in html[i:i + 1400], \
        "lo observado no manda sobre el evento de skill"


# ══ La demo de proyecto ═════════════════════════════════════════════════════

def demo_proyecto_cumple():
    e, inf = demos.correr("proyecto")
    assert inf["cumple"], inf["fallos"]
    o = inf["observado"]
    assert o["archivos"] >= 10 and o["estado_proyecto"] == "VERIFICADO", o
    assert o["crud_verificado"] == 7, o


def un_verificado_con_guion_se_marca_como_simulado():
    """Las 21 corridas VERIFICADO del desarrollo salieron del guion; con modelo real esta
    tarea acaba en PARCIAL. La ejecucion, los tests y el ZIP son reales en los dos casos,
    pero quien escribio el codigo no, y decir solo "verificado" dejaria creer que el
    modelo lo consiguio."""
    e, _inf = demos.correr("proyecto")
    datos = e.artefacto.para_la_pagina()
    assert datos["estado"] == "VERIFICADO"
    assert datos["simulado"] is True, "un VERIFICADO de guion no se marca como simulado"
    html = _PAGINA.read_text()
    i = html.index("function seccionProyecto")
    bloque = html[i:i + 3000]
    assert "p.simulado" in bloque, "la tarjeta no distingue el guion del modelo"
    assert "no el modelo" in bloque


def el_arbol_que_se_pinta_sale_del_manifiesto():
    """Nunca reconstruido: si el manifiesto trae 14 rutas se pintan 14."""
    fin = _fin(_por_http(demos.CANONICAS["proyecto"]["pregunta"]))
    p = fin["proyecto"]
    del_manifiesto = {a["ruta"] for a in p["archivos"]}
    assert len(del_manifiesto) == p["totales"]["archivos"], (len(del_manifiesto), p["totales"])
    assert "app/libros/router.py" in del_manifiesto


def la_pagina_no_pinta_catorce_tarjetas():
    """Mismo patron que el retrieval: los grupos se acumulan y se pintan juntos."""
    html = _PAGINA.read_text()
    assert "ETAPAS_PROYECTO" in html and "resumirGeneracion" in html
    assert "etapasProyecto.push(ev)" in html, "los grupos no se acumulan"
    eventos = _por_http(demos.CANONICAS["proyecto"]["pregunta"])
    grupos = [e for e in eventos if str(e.get("nombre", "")).startswith("generacion:")]
    assert len(grupos) >= 3, "sin los eventos por grupo no se puede agrupar nada"


def el_boton_apunta_al_artefacto_validado():
    """Nunca al ultimo archivo generado, ni a salida/, ni a una carpeta compuesta."""
    fin = _fin(_por_http(demos.CANONICAS["proyecto"]["pregunta"]))
    p = fin["proyecto"]
    assert p["descarga"] == f"/descarga?id={p['id']}", p["descarga"]
    html = _PAGINA.read_text()
    i = html.index("function seccionProyecto")
    bloque = html[i:i + 3000]
    assert "p.descarga" in bloque, "la pagina compone la URL en vez de usar la del backend"
    assert "salida/" not in bloque and "descargarTodo" not in bloque


def sin_integridad_no_hay_boton():
    """Un ZIP que no se puede demostrar no se entrega, y la pagina no lo ofrece."""
    import artefactos
    import empaquetado
    import proyecto as _P
    malo = _P.desde_dict("x", {"app/__init__.py": "",
                               "app/c.py": 'K = "sk-or-v1-secreto"\n',
                               "tests/t.py": "# t\n"})
    art = artefactos.guardar(malo, None, empaquetado.sellar(malo), en_disco=False)
    try:
        datos = art.para_la_pagina()
        assert datos["descarga"] is None, "ofrece descargar algo que no paso el gate"
        assert not datos["integridad"]["ok"]
    finally:
        artefactos.olvidar(art.id)


def la_pagina_no_dice_verificado_sin_evidencia():
    """Se ejecuta `seccionProyecto` de verdad en node, con tres fixtures."""
    import re
    import subprocess
    if not shutil.which("node"):
        return
    js = re.search(r"<script>(.*)</script>", _PAGINA.read_text(), re.S).group(1)
    base = {"id": "a" * 24, "nombre": "x", "totales": {"archivos": 3, "directorios": 1, "lineas": 9},
            "archivos": [{"ruta": "a.py", "bytes": 3, "lineas": 1, "sha256": "f" * 64}],
            "verificacion": {"pasan": 3, "fallan": 0}, "por_que": "x",
            "zip": {"nombre": "x.zip", "bytes": 10, "sha256": "e" * 64}}
    fixtures = {
        "verificado": {**base, "estado": "VERIFICADO", "descarga": "/descarga?id=" + "a" * 24,
                       "integridad": {"ok": True, "motivo": "", "comprobaciones": [["x", True, ""]]}},
        "parcial": {**base, "estado": "PARCIAL", "descarga": "/descarga?id=" + "a" * 24,
                    "integridad": {"ok": True, "motivo": "", "comprobaciones": [["x", True, ""]]}},
        "roto": {**base, "estado": "VERIFICADO", "descarga": None,
                 "integridad": {"ok": False, "motivo": "hashes distintos",
                                "comprobaciones": [["x", False, "y"]]}},
    }
    preludio = ("globalThis.document={getElementById:()=>({}),querySelector:()=>null,"
                "querySelectorAll:()=>[],addEventListener:()=>{}};\n"
                "globalThis.window={};globalThis.setInterval=()=>0;\n")
    guion = (preludio + js + "\n" +
             "const F=" + json.dumps(fixtures) + ";\n" +
             "console.log(JSON.stringify(Object.fromEntries("
             "Object.entries(F).map(([k,v])=>[k, seccionProyecto(v)]))));")
    tmp = AQUI / ".proyecto_check.js"
    tmp.write_text(guion)
    try:
        r = subprocess.run(["node", tmp.name], cwd=AQUI, capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 0, r.stderr[-400:]
        salida = json.loads(r.stdout)
    finally:
        tmp.unlink(missing_ok=True)
    assert "Proyecto listo para descargar" in salida["verificado"]
    assert "descargar" in salida["verificado"]
    assert "Proyecto listo" not in salida["parcial"], "dice listo con estado PARCIAL"
    assert "verificación no está completa" in salida["parcial"]
    assert "ARTIFACT INTEGRITY ERROR" in salida["roto"]
    assert "<a class=\"descargar\"" not in salida["roto"], "ofrece boton sin integridad"


# ══ El panel de evidencia: cuatro capas, sin mezclarse ══════════════════════

def el_panel_separa_claim_de_verificado():
    e, _ = demos.correr("construccion")
    p = server.panel_evidencia(e)
    assert p["claim"], "no recoge lo que declaro el modelo"
    assert p["observed"] and p["observed"]["marcadores"], "no recoge lo observado"
    assert p["verified"], "no recoge lo demostrado"
    assert all(x["estado"] == "verificado" for x in p["verified"])
    assert all(x["estado"] in ("sin verificar", "refutado") for x in p["not_verified"])


def sin_ejecucion_no_hay_nada_observado():
    e, _ = demos.correr("conocimiento")
    p = server.panel_evidencia(e)
    assert p["observed"] is None, "hay 'observado' sin haber ejecutado nada"
    assert not p["verified"], "algo figura verificado sin ejecucion"


def lo_verificado_es_subconjunto_de_lo_declarado():
    """Nada puede quedar VERIFIED sin que el modelo lo declarara primero."""
    e, _ = demos.correr("construccion")
    p = server.panel_evidencia(e)
    declarados = {(x["riesgo"], x["test_id"]) for x in p["claim"]}
    for x in p["verified"] + p["not_verified"]:
        assert (x["riesgo"], x["test_id"]) in declarados, f"aparece sin declararse: {x}"


# ══ La traza legible ════════════════════════════════════════════════════════

def la_linea_de_tiempo_pliega_el_retrieval():
    """Quince filas de internals no cuentan la historia: la esconden."""
    e, _ = demos.correr("construccion")
    filas = server._linea_de_tiempo(e)
    nombres = [f["etapa"] for f in filas]
    assert not any(n.startswith(("bm25:", "rrf:", "filtro:")) for n in nombres), nombres
    assert "recuperacion" in nombres
    assert len(filas) < len(e.pasos), "no plego nada"
    assert len(filas) <= 14, f"demasiadas filas para leerlas: {len(filas)}"


def la_linea_de_tiempo_no_pierde_tiempo():
    """El tiempo del retrieval se suma a su fila, no se evapora al plegar."""
    e, _ = demos.correr("construccion")
    filas = server._linea_de_tiempo(e)
    total_pasos = sum(p.ms for p in e.pasos)
    total_filas = sum(f["ms"] for f in filas)
    assert abs(total_pasos - total_filas) < 1.0, (total_pasos, total_filas)


def la_traza_conserva_todas_las_etapas():
    """Plegar es de la VISTA. Lo que se persiste sigue entero."""
    e, _ = demos.correr("construccion")
    assert any(p.nombre.startswith("bm25:") for p in e.pasos), "se perdieron las etapas reales"


# ══ El coste no finge ═══════════════════════════════════════════════════════

def un_doble_no_cuesta_cero_coma_cero_cero_cero_cero():
    e, _ = demos.correr("conocimiento")
    c = server._coste(e, "conceptual")
    assert c["simulado"] is True and c["texto"] == "SIMULADO · $0", c
    assert "0.0000" not in c["texto"], "un doble disfrazado de coste real"


# ══ Contra el servidor real ═════════════════════════════════════════════════

def el_servidor_emite_el_panel_y_la_traza():
    fin = _fin(_por_http(demos.CANONICAS["construccion"]["pregunta"]))
    assert fin["evidencia"]["verified"], "el panel llega vacio"
    assert fin["linea_tiempo"], "la traza no llega"
    assert fin["coste"]["simulado"] is True
    assert fin["entregable"]["estado"] == "verde"


def el_servidor_no_manda_quince_etapas_de_retrieval_como_pasos_visibles():
    """Siguen emitiendose —son ciertas— pero la pagina las agrupa: se comprueba que
    llegan para poder agruparlas, y que el cierre con el resumen tambien llega."""
    eventos = _por_http(demos.CANONICAS["conocimiento"]["pregunta"])
    pasos = [e for e in eventos if e.get("tipo") == "paso"]
    internas = [p for p in pasos if p["nombre"].startswith(("bm25:", "rrf:", "filtro:"))]
    assert len(internas) >= 6, "sin las etapas no se puede explicar el retrieval"
    cierre = [p for p in pasos if p["nombre"] == "recuperacion"]
    assert cierre and cierre[0]["detalle"]["ids"], "falta el cierre con los ids"


def la_abstencion_sobrevive_al_servidor():
    fin = _fin(_por_http(demos.CANONICAS["abstencion"]["pregunta"]))
    assert "corpus" in fin["respuesta"][:220].lower(), fin["respuesta"][:120]
    assert not fin["entregable"], "invento codigo para algo que no sabe"


def una_pregunta_fuera_de_las_demos_no_inventa():
    fin = _fin(_por_http("¿Qué es el teorema CAP aplicado a Cassandra?"))
    assert "SIN MODELO" in fin["respuesta"], fin["respuesta"][:160]


# ══ Una demo no contamina la siguiente ══════════════════════════════════════

def dos_pasadas_dan_el_mismo_resultado():
    """Si la segunda vez cambia algo, lo que se enseña no es reproducible."""
    for clave in demos.CANONICAS:
        _a, ia = demos.correr(clave)
        _b, ib = demos.correr(clave)
        assert ia["observado"] == ib["observado"], \
            f"{clave} no es reproducible:\n  {ia['observado']}\n  {ib['observado']}"


def una_demo_no_contamina_a_la_otra():
    """La de codigo entrega archivos; la conceptual no puede heredarlos."""
    demos.correr("construccion")
    _e, inf = demos.correr("conocimiento")
    assert not inf["observado"]["hay_codigo"], "arrastro la entrega de la demo anterior"
    assert not inf["observado"]["ejecutado"]


def las_demos_no_escriben_en_la_carpeta_de_produccion():
    import rapido
    salida = Path(rapido.__file__).resolve().parent / "salida"
    salida.mkdir(exist_ok=True)
    marca = salida / "CANARIO_DEMOS.txt"
    marca.write_text("entrega del usuario")
    antes = sorted(p.name for p in salida.iterdir())
    try:
        for clave in demos.CANONICAS:
            demos.correr(clave)                 # guardar=False por defecto
        assert marca.read_text() == "entrega del usuario", "una demo piso la entrega"
        assert sorted(p.name for p in salida.iterdir()) == antes, "una demo escribio en salida/"
    finally:
        marca.unlink(missing_ok=True)


# ══ El perfil de operacion ══════════════════════════════════════════════════

def hay_exactamente_dos_modos_y_uno_es_experimental():
    html = _PAGINA.read_text()
    import re
    assert set(re.findall(r'name="modo" value="(\w+)"', html)) == {"pipeline", "arquitecto"}
    i = html.index('value="arquitecto"')
    assert "experimental" in html[i:i + 400].lower()


def la_pagina_se_puede_leer_en_un_movil():
    """Sin el meta viewport, un movil renderiza a 980px y lo enseña en miniatura: el panel
    de evidencia sale ilegible aunque su grid colapse bien. Comprobado en 375x812."""
    html = _PAGINA.read_text()
    assert 'name="viewport"' in html, "falta el meta viewport"
    assert "width=device-width" in html, "el viewport no sigue al dispositivo"
    assert "@media (max-width: 560px)" in html, "el panel no colapsa en estrecho"
    i = html.index("@media (max-width: 560px)")
    assert "grid-template-columns: 1fr" in html[i:i + 400], \
        "las cuatro capas siguen en varias columnas en un movil"


def lo_ancho_se_desplaza_solo_ello_no_la_pagina():
    """Una tabla o un bloque de codigo anchos no pueden hacer scrollear la pagina entera."""
    html = _PAGINA.read_text()
    assert ".md table, table.tl { display: block; overflow-x: auto; max-width: 100%; }" in html


def el_javascript_de_la_pagina_es_valido():
    """La pagina es producto: un error de sintaxis la deja en blanco y nadie se entera."""
    if not shutil.which("node"):
        return                                  # sin node no se puede comprobar, no se finge
    import re
    js = re.search(r"<script>(.*)</script>", _PAGINA.read_text(), re.S).group(1)
    tmp = Path(AQUI / ".ui_check.js")
    tmp.write_text(js)
    try:
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
        assert r.returncode == 0, f"la pagina no parsea: {r.stderr[-300:]}"
    finally:
        tmp.unlink(missing_ok=True)


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
