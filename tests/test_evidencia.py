"""Que lo guardado diga la verdad sobre lo que ocurrio.

El defecto sistemico de este proyecto ha sido siempre el mismo: algo se afirma y nada
lo observa. El reranker medido sobre un ranking descartado, `arreglado` registrado sobre
un campo que nadie escribia, los tests sobre la carpeta de produccion, los marcadores
perdidos en el truncado. Estos tests existen para que eso se pueda detectar.

    python3 test_evidencia.py
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
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import agent
import dobles
import obligaciones
import pipeline
import plan as P
import rapido
import recuperacion
import skills
import traza

AQUI = Path(__file__).parent
# La raiz de PRODUCCION, derivada de un modulo suyo: inmune a donde viva el test.
_RAIZ_PROD = Path(rapido.__file__).resolve().parent
# Las rutas que apuntan a PRODUCCION se derivan de un modulo de produccion, nunca de
# __file__: asi siguen apuntando al sitio correcto viva donde viva este test. Cuando
# colgaban de `AQUI`, mover el test a tests/ los dejaba mirando una carpeta vacia y
# el test pasaba sin comprobar nada.
RAIZ = Path(rapido.__file__).resolve().parent
TRAZAS = traza.ARCHIVO.parent / "trazas_noche.jsonl"
# La ejecucion real esta APAGADA por defecto (skills.impedimento_de_ejecucion): en
# produccion este agente entrega el codigo y sus casos de test sin correrlos, y de eso se
# encarga el agente de QA. Estos casos existen para demostrar que cuando SI se ejecuta, la
# maquina no miente sobre lo que vio — asi que la encienden a proposito.
# La bandera se lee en cada llamada, no al importar, justo para permitir esto.
os.environ.setdefault("MIRAG_EJECUCION", "on")

casos = []


def probar(nombre, fn):
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))


def _correr(pregunta, guion, guardar=True):
    antes = len(traza.leer(TRAZAS))
    with dobles.usar(list(guion)) as doble:
        e = pipeline.ejecutar(pregunta, guardar=guardar, carpeta=tempfile.mkdtemp())
    filas = traza.leer(TRAZAS)
    return e, doble, (filas[-1] if len(filas) > antes else None)


# ══ El truncado no puede borrar evidencia ═══════════════════════════════════

def el_marcador_sobrevive_al_truncado_por_delante():
    """Imprimir 9.600 chars DESPUES del marcador lo borraba: verde pasaba a sin_evidencia."""
    codigo = "\n".join(["print('TEST:temprano:PASS')"]
                       + [f"print('ruido {i} ' + 'y'*60)" for i in range(120)])
    salida = skills.verificar_codigo({"t.py": codigo}, "python3 t.py")
    estado, _, marcas = skills.veredicto(salida)
    assert marcas == {"temprano": "PASS"}, f"se perdio el marcador: {marcas}"
    assert estado == "verde", estado


def el_marcador_sobrevive_al_truncado_por_detras():
    codigo = "\n".join([f"print('ruido {i} ' + 'x'*60)" for i in range(120)]
                       + ["print('TEST:tardio:PASS')"])
    salida = skills.verificar_codigo({"t.py": codigo}, "python3 t.py")
    assert skills.veredicto(salida)[2] == {"tardio": "PASS"}


def un_fail_enterrado_no_desaparece():
    """Lo peor posible: un FAIL que se pierde convierte un fallo en un verde."""
    codigo = "\n".join(["print('TEST:a:PASS')"]
                       + [f"print('ruido {i} ' + 'q'*60)" for i in range(60)]
                       + ["print('TEST:malo:FAIL')"]
                       + [f"print('ruido {i} ' + 'r'*60)" for i in range(60)])
    salida = skills.verificar_codigo({"t.py": codigo}, "python3 t.py")
    estado, _, marcas = skills.veredicto(salida)
    assert marcas.get("malo") == "FAIL", f"se perdio el FAIL: {marcas}"
    assert estado == "rojo", estado


def la_salida_recortada_lo_dice():
    codigo = "\n".join([f"print('x'*200)" for _ in range(60)])
    salida = skills.verificar_codigo({"t.py": codigo}, "python3 t.py")
    r = skills.resultado_de(salida)
    assert r.truncada, "se recorto sin avisarlo"
    assert "recortados" in salida


# ══ Reparacion: ejecutado == registrado ═════════════════════════════════════

def la_reparacion_se_registra():
    """Se hacian 2 llamadas (generacion + arreglo) y la traza decia arreglado=false."""
    e, doble, fila = _correr("Crea calculator.py con division por cero",
                             dobles.CODIGO_ROTO_LUEGO_ARREGLADO)
    assert fila, "no se escribio traza"
    assert fila["arreglado"] is True, "la reparacion ocurrio y no se registro"
    assert fila["repair_attempts"] == 1, fila["repair_attempts"]
    assert doble.llamadas == 2, f"llamadas reales: {doble.llamadas}"
    assert fila["final_status"] == "verde", fila["final_status"]


def sin_reparacion_se_registra_cero():
    e, doble, fila = _correr("Crea calculator.py con calculate y tests",
                             dobles.CODIGO_CALCULADORA)
    assert fila["arreglado"] is False
    assert fila["repair_attempts"] == 0
    assert doble.llamadas == 1, doble.llamadas


def el_registro_no_sale_del_texto_del_modelo():
    """Si el modelo DICE que arreglo algo pero no hubo segunda llamada, repair=0."""
    guion = [dobles.tool("entregar_implementacion",
                         {"archivos": {"calculator.py": dobles.CALCULADORA,
                                       "test_calculator.py": dobles.TEST_CALCULADORA},
                          "comando_test": "python3 test_calculator.py",
                          "decisiones": "Arreglé el bug de división por cero, ya está reparado.",
                          "propiedades": [], "sin_cubrir": []})]
    e, doble, fila = _correr("Crea calculator.py", guion)
    assert fila["repair_attempts"] == 0, "el texto del modelo no puede fijar repair_attempts"


# ══ Los tests no tocan la carpeta del usuario ═══════════════════════════════

def la_suite_no_pisa_la_entrega_del_usuario():
    """Producir entrega → guardar → correr tests → la entrega sigue ahí."""
    salida_real = RAIZ / "salida"
    marca = salida_real / "MARCA_DE_PRUEBA.txt"
    salida_real.mkdir(exist_ok=True)
    marca.write_text("entrega del usuario")
    try:
        for archivo in ("test_full_pipeline.py", "test_seguridad.py"):
            # El returncode SI se comprueba: sin esto, un subproceso que ni arranca
            # dejaba pasar el canario como si la suite se hubiera ejecutado.
            r = subprocess.run([sys.executable, str(AQUI / archivo)], cwd=_RAIZ_PROD,
                               capture_output=True, text=True, timeout=600)
            assert r.returncode == 0, \
                f"{archivo} no se ejecuto: {(r.stderr or r.stdout)[-300:]}"
        assert marca.exists(), f"{archivo} borro la entrega del usuario de salida/"
        assert marca.read_text() == "entrega del usuario"
    finally:
        marca.unlink(missing_ok=True)


# ══ Anti-patrones: se cierra el hueco, sin fingir ═══════════════════════════

def los_antipatrones_se_cruzan_con_la_evidencia():
    q = "API de reservas: dos usuarios no pueden quedarse con la misma plaza"
    obs = obligaciones.de_retrieval(recuperacion.recuperar(q, plan=P.deducir(q)))
    assert obs, "no se extrajo ninguna obligacion de los anti-patrones"
    assert all(o.evitar for o in obs), "hay obligaciones sin un 'que evitar'"


def sin_evidencia_no_se_da_por_cubierto():
    """Ante la duda, NO cubierta. Un falso 'cubierta' seria la mentira de siempre."""
    q = "API de reservas concurrentes"
    obs = obligaciones.de_retrieval(recuperacion.recuperar(q, plan=P.deducir(q)))
    filas = obligaciones.cobertura(obs, [])
    assert filas, "no devolvio filas"
    assert all(f["estado"] != "cubierta" for f in filas), \
        "dio algo por cubierto sin una sola propiedad demostrada"


def una_propiedad_declarada_no_basta():
    """Declarada != demostrada. Tiene que quedar en 'declarada', no en 'cubierta'."""
    ob = obligaciones.Obligacion("04 · x", "04", "x",
                                 "llamar a una API externa dentro de una transaccion abierta",
                                 "sacar la llamada fuera",
                                 obligaciones._terminos("llamar a una API externa dentro de "
                                                        "una transaccion abierta"))
    declarada = [{"riesgo": "llamar a una API externa dentro de una transaccion abierta",
                  "propiedad": "ninguna transaccion contiene llamadas externas",
                  "test_id": "t", "estado": "sin verificar"}]
    assert obligaciones.cobertura([ob], declarada)[0]["estado"] == "declarada"
    demostrada = [{**declarada[0], "estado": "verificado"}]
    assert obligaciones.cobertura([ob], demostrada)[0]["estado"] == "cubierta"


def el_pipeline_registra_la_cobertura():
    e, _, fila = _correr("Crea calculator.py con calculate y tests", dobles.CODIGO_CALCULADORA)
    paso = next((p for p in e.pasos if p.nombre == "anti-patrones"), None)
    assert paso, "el pipeline no comprueba los anti-patrones"
    assert fila["antipatrones"], "la cobertura no se persiste"


def la_tabla_no_afirma_que_los_antipatrones_apliquen():
    """Medido: BM25 devuelve k anti-patrones haya o no relacion. La tabla no puede fingir que si."""
    filas = [{"obligacion": "x", "estado": "no cubierta", "evitar": "y", "propiedad": None}]
    md = obligaciones.tabla_markdown(filas)
    assert "porque aplican a esta tarea" not in md, "vuelve a afirmar relevancia sin medirla"
    assert "relevantes o" in md, "no advierte que el corpus trae relleno"


def el_corpus_trae_antipatrones_aunque_no_vengan_a_cuento():
    """El hecho observado que justifica lo anterior: una consulta ajena recibe 6 igual."""
    q = "como se dibuja un diagrama de secuencia"
    ap = recuperacion.recuperar(q, plan=P.deducir(q)).por_indice["antipatrones"]
    assert len(ap) == 6, f"cambio el k de antipatrones: {len(ap)}"
    codigo = "Implementa reservar(conn, plaza_id, usuario) con sus tests. Dos usuarios no " \
             "pueden quedarse con la misma plaza."
    puntos = [t.puntuacion for t in recuperacion.recuperar(
        codigo, plan=P.deducir(codigo)).por_indice["antipatrones"]]
    assert max(puntos) > 4.7, \
        "si esto deja de cumplirse, un umbral por score ya seria separable y habria que medirlo"


# ══ Trazabilidad de punta a punta ═══════════════════════════════════════════

def un_chunk_se_rastrea_hasta_la_traza():
    """query → retrieval → contexto → prompt → traza. El mismo chunk en los cuatro."""
    capturado = {}

    class Espia(dobles.Doble):
        def __call__(self, m, tools=None):
            capturado.setdefault("ctx", m[-1]["content"])
            return super().__call__(m, tools)

    q = "como evito un race condition al reservar una plaza en postgres"
    with dobles.usar(Espia(list(dobles.DECISION_SIMPLE))):
        e = pipeline.ejecutar(q, guardar=True, carpeta=tempfile.mkdtemp())
    r = recuperacion.recuperar(q, plan=P.deducir(q))
    chunk = r.seleccionados[0]

    assert chunk.id in r.ids(), "1. no esta en el RetrievalResult"
    paso = next(p for p in e.pasos if p.nombre == "recuperacion")
    assert chunk.id in paso.detalle["ids"], "2. no esta en el paso de recuperacion"
    assert chunk.trozo.titulo in capturado["ctx"], "3. no esta en el prompt del modelo"
    fila = traza.leer(TRAZAS)[-1]
    assert chunk.id in fila["retrieval"]["ids"], "4. no esta en la traza persistida"


def una_llamada_que_cuesta_dinero_siempre_se_anota():
    """`guardar=False` pedia no escribir ARCHIVOS y ademas silenciaba el registro: tres
    demos con modelo real salieron sin traza. Lo que se paga, se anota."""
    import inspect
    fuente = inspect.getsource(pipeline.ejecutar)
    assert "if guardar or not simulado:" in fuente, \
        "el registro vuelve a depender de si se querian archivos en disco"
    # y de comportamiento: con un doble (gratis) no se ensucia el fichero
    antes = len(traza.leer(TRAZAS))
    with dobles.usar(dobles.DECISION_SIMPLE):
        pipeline.ejecutar("que es un indice", guardar=False)
    assert len(traza.leer(TRAZAS)) == antes, "un doble gratis ensucia la traza"


def la_traza_anota_lo_que_costo_ESTA_ejecucion():
    """`agent.PRESUPUESTO` acumula por PROCESO y el servidor lo reinicia por peticion,
    pero un script que ejecuta varias seguidas no. Cada fila anotaba el total corrido
    —0.153, 0.309, 0.465...— asi que sumar la columna contaba la primera seis veces.
    Lo destapo un banco de diez corridas, cuyo coste salio inflado en 2,3 dolares."""
    import agent
    antes = len(traza.leer(TRAZAS))
    for _ in range(3):
        with dobles.usar(list(dobles.CODIGO_CALCULADORA)):
            pipeline.ejecutar("Crea calculator.py con calculate y tests",
                              guardar=True, carpeta=tempfile.mkdtemp())
    filas = traza.leer(TRAZAS)[antes:]
    assert len(filas) == 3, len(filas)
    llamadas = [f["llamadas"] for f in filas]
    assert llamadas == [1, 1, 1], f"la traza acumula en vez de anotar el delta: {llamadas}"
    assert agent.PRESUPUESTO.llamadas >= 3, "el presupuesto del proceso si tiene que acumular"


def la_traza_tiene_los_campos_importantes():
    _, _, fila = _correr("Crea calculator.py con calculate y tests", dobles.CODIGO_CALCULADORA)
    for campo in ("plan", "filtros", "retrieval", "contexto", "verificacion",
                  "antipatrones", "repair_attempts", "final_status", "model",
                  "fallbacks", "errores", "tools"):
        assert campo in fila, f"falta {campo} en la traza"
    assert fila["retrieval"]["ids"], "el retrieval persistido esta vacio"
    assert fila["contexto"]["tokens_aprox"] > 0


def la_traza_guarda_el_texto_no_solo_el_conteo():
    """Auditar una corrida real exigia rebuscar en tempdirs porque solo se guardaba el conteo."""
    _, _, fila = _correr("Crea calculator.py con calculate y tests", dobles.CODIGO_CALCULADORA)
    det = fila["propiedades_detalle"]
    assert det, "no se guarda el texto de las propiedades"
    assert det[0]["test_id"] and det[0]["propiedad"], det[0]
    assert sum(fila["propiedades"].values()) >= len(det) > 0
    assert fila["antipatrones_detalle"], "el resumen dice cuantas, no cuales"
    assert all(f["por_que"] for f in fila["antipatrones_detalle"])


def lo_que_no_aplica_es_null_no_inventado():
    _, _, fila = _correr("que es un indice", dobles.DECISION_SIMPLE)
    assert fila["model_route"] is None, "hay un router inventado"
    assert fila["verificacion"] is None, "hay verificacion sin ejecucion"


def la_traza_distingue_simulado_de_real():
    _, _, fila = _correr("que es un indice", dobles.DECISION_SIMPLE)
    assert fila["decision_simulada"] is True
    assert fila["coste_usd"] == 0
    assert fila["model"] == "doble determinista", fila["model"]


# ══ SSE y traza dicen lo mismo ══════════════════════════════════════════════

def los_eventos_y_la_traza_coinciden():
    eventos = []
    with dobles.usar(list(dobles.CODIGO_CALCULADORA)):
        e = pipeline.ejecutar("Crea calculator.py con tests", guardar=True,
                              carpeta=tempfile.mkdtemp(), al_avanzar=eventos.append)
    fila = traza.leer(TRAZAS)[-1]
    por_nombre = {p.nombre: p for p in eventos}
    assert por_nombre["verificacion"].estado == "ejecutado"
    assert fila["final_status"] == "verde", "la UI vio verde y la traza dice otra cosa"
    assert por_nombre["recuperacion"].detalle["ids"] == fila["retrieval"]["ids"], \
        "el retrieval que vio la UI no es el que se persistio"


# ══ Claim del modelo != observacion del sistema ════════════════════════════

def afirmar_sin_marcadores_no_es_verificado():
    guion = [dobles.tool("verificar_codigo",
                         {"archivos": {"t.py": "print('todos los tests pasaron')"},
                          "comando": "python3 t.py"}),
             dobles.texto("TEST_X pasó. Los 3 tests pasaron correctamente.")]
    with dobles.usar(guion):
        r = agent.run("construye algo y ejecutalo")
    assert "NO RESPALDADA" in r["respuesta"], "una afirmacion sin marcadores paso por buena"


def una_propiedad_sin_marcador_queda_sin_verificar():
    ev = rapido._evidencia([{"riesgo": "x", "propiedad": "y", "test_id": "inexistente"}],
                           "TESTS EN VERDE · 1 de 1 marcadores\n\nTEST:otro:PASS",
                           ejecutado=True)
    assert ev[0]["estado"] == "sin verificar", ev


# ══ Fronteras de error ══════════════════════════════════════════════════════

def un_fallo_de_persistencia_no_borra_la_respuesta():
    original = rapido.guardar
    rapido.guardar = lambda *a, **k: (_ for _ in ()).throw(OSError("disco lleno"))
    try:
        with dobles.usar(dobles.CODIGO_CALCULADORA):
            e = pipeline.ejecutar("Crea calculator.py con tests", guardar=True)
        assert e.entrega and e.evidencia, "se perdio el trabajo"
        paso = next(p for p in e.pasos if p.nombre == "persistencia")
        assert paso.estado == "error" and "disco lleno" in paso.resumen
        fila = traza.leer(TRAZAS)[-1]
        assert any(x["etapa"] == "persistencia" for x in fila["errores"]), \
            "el error de persistencia no quedo en la traza"
    finally:
        rapido.guardar = original


def los_errores_quedan_separados_por_etapa():
    with dobles.usar(dobles.JSON_ROTO):
        e = pipeline.ejecutar("Crea algo", guardar=True, carpeta=tempfile.mkdtemp())
    fila = traza.leer(TRAZAS)[-1]
    etapas = {x["etapa"] for x in fila["errores"]}
    assert "entrega" in etapas, f"el error de entrega no se registro: {fila['errores']}"


# ══ ProjectState real ═══════════════════════════════════════════════════════

def el_estado_refleja_los_modos_reales():
    import estado
    assert set(estado.ESTADO["modos"]) == {"pipeline", "arquitecto"}, estado.ESTADO["modos"]
    assert "EXPERIMENTAL" in estado.ESTADO["modos"]["arquitecto"]


def el_estado_deriva_del_repositorio():
    import estado
    s = estado.ESTADO["simbolos"]
    assert s.get("funciones", 0) > 100, s
    assert "recuperacion.py" in estado.ESTADO["archivos"]
    assert s.get("entrypoints"), "no detecta ningun entrypoint"


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
