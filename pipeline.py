"""El pipeline completo, de la pregunta a la evidencia.

    pregunta
       │
       ▼ ProjectState ──→ ¿ya lo sabemos? → responder. 0 llamadas, 0 retrieval.
       ▼ RetrievalPlan
       ▼ routing por metadatos
       ▼ BM25 (+ vector si esta medido) → RRF → reranker si esta medido
       ▼ simbolos    si el plan los pide
       ▼ grafo       si la compuerta lo abre
       ▼ SUFICIENCIA ──→ ¿el corpus cubre esto? si no, se dice.
       ▼ contexto
       ▼ LLM         (esta noche: un doble determinista)
       ▼ skills + verificacion por EJECUCION
       ▼ evidencia
       ▼ traza

NINGUNA ETAPA SE EJECUTA POR COSTUMBRE
    Las opcionales pasan por config.activar(), que lee lo medido en ganancias.json. Una
    etapa que nadie ha medido no corre. Y cuando NO corre, se anota igual con el motivo:
    "Mirag no uso el grafo porque no esta medido" es informacion util, no un hueco.

CADA PASO DICE DE DONDE SALE LO QUE AFIRMA
    fuente='ejecucion' -> lo hizo el ordenador y se puede repetir
    fuente='modelo'    -> lo dijo el modelo (o su doble)
    fuente='corpus'    -> sale de los documentos
"""

import json
import time
from pathlib import Path
from typing import NamedTuple

import agent
import config
import estado
import hibrido
import metadatos as M
import plan as P
import obligaciones
import rag
import rapido
import recuperacion
import suficiencia
import traza
import skills
from skills import SKILLS

MAX_ARREGLOS = 1


class Paso(NamedTuple):
    nombre: str
    estado: str          # ejecutado | omitido | fallback | error
    resumen: str
    ms: float = 0.0
    fuente: str = ""
    detalle: object = None

    def linea(self):
        marca = {"ejecutado": "·", "omitido": "○", "fallback": "△", "error": "✗"}
        return f"  {marca.get(self.estado, '?')} {self.nombre:<22} {self.resumen}"


class Ejecucion(NamedTuple):
    pregunta: str
    pasos: list
    respuesta: str
    veredicto: object = None      # suficiencia.Veredicto
    entrega: dict = None
    evidencia: list = ()
    cobertura_antipatrones: list = ()
    salida: str = ""
    simulado_llm: bool = True     # ¿la decision vino de un doble?
    proyecto: object = None       # ProyectoArtefacto, si la peticion pedia un proyecto
    certificado: object = None    # el resultado de verificacion_proyecto
    artefacto: object = None      # el artefacto registrado: de aqui sale el boton
    fila: dict = None             # la traza escrita

    @property
    def ms(self):
        return round(sum(p.ms for p in self.pasos), 1)

    def imprimir(self):
        print(f"\n{self.pregunta}\n")
        for p in self.pasos:
            print(p.linea())
        print(f"\n  {self.ms} ms · "
              f"{'decision SIMULADA' if self.simulado_llm else 'modelo real'}")


_SIMBOLOS = {}


def _indice_de_simbolos(raiz):
    """Indexar 629 simbolos cuesta ~118 ms y se repetia en CADA peticion.

    Se cachea por (ruta, mtime maximo de los .py): si el codigo cambia, el indice se
    reconstruye solo. Un indice pegado seria peor que uno lento — este agente indexa
    su propio repositorio, que cambia mientras se trabaja.
    """
    import simbolos
    raiz = Path(raiz)
    sello = max((f.stat().st_mtime for f in raiz.rglob("*.py")), default=0)
    clave = (str(raiz), sello)
    if clave not in _SIMBOLOS:
        _SIMBOLOS.clear()                  # solo se guarda la version vigente
        _SIMBOLOS[clave] = simbolos.indexar(raiz)
    return _SIMBOLOS[clave]


def _reloj():
    t = time.perf_counter()
    return lambda: (time.perf_counter() - t) * 1000


def _leer_entrega(mensaje):
    """Lo que el modelo entrego, tolerando que venga cortado o mal formado."""
    llamada = (mensaje.get("tool_calls") or [None])[0]
    if not llamada:
        return None, "el modelo no llamo a entregar_implementacion"
    try:
        datos = json.loads(llamada["function"]["arguments"] or "{}", strict=False)
    except json.JSONDecodeError as e:
        return None, f"los argumentos no son JSON valido ({e})"
    if not isinstance(datos.get("archivos"), dict) or not datos["archivos"]:
        return None, "la entrega no trae archivos"
    return datos, None


def ejecutar(pregunta, k=5, familia="general", al_avanzar=None, guardar=True,
             plan_previo=None, version=None, carpeta=None):
    """Recorre el diagrama entero. Devuelve todo lo que paso, no solo el resultado."""
    arranque = time.time()
    # Para que la traza anote lo que costo ESTA ejecucion y no el acumulado del proceso.
    presupuesto_antes = {"coste": agent.PRESUPUESTO.coste,
                         "llamadas": agent.PRESUPUESTO.llamadas,
                         "tokens": agent.PRESUPUESTO.entrada + agent.PRESUPUESTO.salida}
    pasos = []

    def anota(paso):
        pasos.append(paso)
        if al_avanzar:
            al_avanzar(paso)
        return paso

    # ── 1. ProjectState: lo que ya sabemos no se busca ──────────────────────
    ms = _reloj()
    if (directa := estado.responder(pregunta)):
        anota(Paso("estado del proyecto", "ejecutado",
                   "respondido sin buscar y sin llamar al modelo", ms(), "ejecucion"))
        return Ejecucion(pregunta, pasos, directa, simulado_llm=False)
    anota(Paso("estado del proyecto", "omitido",
               "no es una pregunta sobre el propio Mirag", ms(), "ejecucion"))

    # ── 2. el plan ──────────────────────────────────────────────────────────
    ms = _reloj()
    # plan_previo: lo usa el banco para forzar un brazo sin tocar globales
    # RETRIEVAL_PLAN apagado = sin plan deducido: el brazo baseline de los bancos, y la
    # forma de comprobar que el plan sirve para algo en vez de suponerlo.
    hay_plan, motivo_plan = config.activar("retrieval_plan")
    if plan_previo is not None:
        plan_ = plan_previo
    elif hay_plan:
        plan_ = P.deducir(pregunta)
    else:
        plan_ = P.VACIO
    anota(Paso("plan de busqueda", "ejecutado", plan_.resumen(), ms(), "ejecucion",
               {"origen": plan_.origen, "plan": plan_._asdict()}))

    # ── 3-5. LA recuperacion: una sola, sobre los tres indices ──────────────
    # Esta es la unica que ocurre en una peticion de produccion. Antes habia dos:
    # esta, cuyo resultado se tiraba, y otra dentro de rapido.recuperar() que era la
    # que de verdad llegaba al modelo.
    ms = _reloj()
    r = recuperacion.recuperar(pregunta, plan=plan_, familia=familia)
    for etapa in r.etapas:
        anota(Paso(etapa.nombre,
                   "ejecutado" if etapa.usada else "omitido",
                   (f"{etapa.candidatos} candidatos · {etapa.detalle}" if etapa.usada
                    else etapa.detalle),
                   etapa.ms, "corpus"))
    for etapa, motivo in r.fallbacks:
        anota(Paso(f"{etapa} (fallback)", "fallback", motivo, 0.0, "ejecucion"))
    anota(Paso("recuperacion", "ejecutado", f"{r.resumen()} · {r.metricas['ms']} ms",
               ms(), "corpus", {"ids": r.ids(), "metodos": r.metricas["metodos"]}))
    recuperados = [(tr.trozo, tr.puntuacion) for tr in r.seleccionados]

    # ── 6. simbolos, solo si el plan los pide ───────────────────────────────
    ms = _reloj()
    simbolos_hallados = []
    quiere_simbolos = plan_.needs_symbols and config.activar("symbol_retrieval")[0]
    if quiere_simbolos:
        try:
            import simbolos
            indice = _indice_de_simbolos(rag.CARPETA.parent)
            simbolos_hallados = simbolos.buscar(indice, pregunta, k=5)
            anota(Paso("simbolos", "ejecutado",
                       f"{len(simbolos_hallados)} simbolos de {len(indice)} indexados",
                       ms(), "ejecucion",
                       [(s.nombre, s.archivo, s.linea) for s, _ in simbolos_hallados]))
        except Exception as e:
            anota(Paso("simbolos", "error", f"{type(e).__name__}: {e}", ms(), "ejecucion"))
    else:
        anota(Paso("simbolos", "omitido",
                   "el plan no pide buscar en codigo" if not plan_.needs_symbols
                   else config.activar("symbol_retrieval")[1], ms(), "ejecucion"))

    # ── 7. grafo, solo si esta medido Y el plan lo pide ─────────────────────
    ms = _reloj()
    abre, motivo = config.activar("graph_retrieval", familia)
    if abre and plan_.needs_graph:
        try:
            import grafo
            extra, camino = grafo.expandir([t for t, _ in recuperados], saltos=1)
            recuperados = recuperados + [(t, 0.0) for t in extra]
            anota(Paso("grafo", "ejecutado", f"{len(extra)} trozos por relacion", ms(),
                       "corpus", camino))
        except Exception as e:
            anota(Paso("grafo", "error", f"{type(e).__name__}: {e}", ms(), "corpus"))
    else:
        anota(Paso("grafo", "omitido",
                   motivo if not abre else "el plan no necesita relaciones", ms(), "ejecucion"))

    # ── 8. ¿alcanza esto para responder? ────────────────────────────────────
    ms = _reloj()
    hay_suf, motivo_suf = config.activar("suficiencia")
    veredicto = (suficiencia.evaluar(pregunta, recuperados, plan_) if hay_suf
                 else suficiencia.no_evaluado(motivo_suf))
    anota(Paso("suficiencia", "ejecutado" if veredicto.suficiente else "fallback",
               f"{veredicto.grado}: {veredicto.motivo}", ms(), "corpus",
               veredicto.señales))

    # ── 9. contexto: SE CONSTRUYE DESDE EL RetrievalResult ──────────────────
    ms = _reloj()
    extra = None
    if plan_.needs_code:
        # se exigia evidencia por marcadores que nunca se pedian en este camino
        extra = ("=== COMO SE MIDE LO QUE ENTREGAS ===\n"
                 "Cada test imprime una linea EXACTA TEST:<id>:PASS o TEST:<id>:FAIL, con el "
                 "mismo <id> que pongas en propiedades[].test_id. Una propiedad cuyo test_id "
                 "no aparezca en la salida se marca SIN VERIFICAR, digas lo que digas. "
                 "El test debe salir con exit != 0 si algo falla: imprimir FAIL no es reportarlo.")
    # El aviso de cobertura solo vale para preguntas que se responden CON el corpus: en
    # una tarea de codigo la correccion la decide la ejecucion, no los documentos.
    contexto, medidas = recuperacion.construir_contexto(
        r, peticion=pregunta, simbolos=simbolos_hallados,
        aviso_cobertura=None if veredicto.suficiente else veredicto.frase(),
        instrucciones_extra=extra)
    anota(Paso("contexto", "ejecutado",
               f"~{medidas['tokens_aprox']:,} tokens · {medidas['incluidos']} trozos"
               + (f" · {len(medidas['descartados'])} descartados"
                  if medidas["descartados"] else ""),
               ms(), "corpus", medidas))

    # ── 10. el modelo ───────────────────────────────────────────────────────
    ms = _reloj()
    # ¿la decision la toma un doble o el modelo de verdad? De esto depende que la
    # traza diga SIMULATED o no, asi que no se adivina: se mira quien es agent.llm.
    simulado = type(agent.llm).__name__ == "Doble"

    # ── 10-bis. ¿piden un PROYECTO entero? ──────────────────────────────────
    # Una RAMA, no un pipeline paralelo. Los pasos 1-9 son exactamente los mismos y
    # `recuperacion.py` existe precisamente porque tener dos fuentes de contexto costo
    # el desastre del reranker. Lo unico que cambia es que en vez de pedir un archivo,
    # se pide un plano y luego los archivos por grupos.
    if plan_.needs_project:
        return _ejecutar_proyecto(pregunta, plan_, r, contexto, medidas, veredicto,
                                  pasos, anota, arranque, simulado, guardar, version,
                                  presupuesto_antes)

    try:
        msg = agent.llm([{"role": "system", "content": agent.SYSTEM},
                         {"role": "user", "content": contexto}],
                        tools=[rapido.ENTREGAR] if plan_.needs_code else [])
    except agent.ModoOffline as e:
        anota(Paso("modelo", "error", "candado offline: no se llamo a nadie", ms(), "ejecucion"))
        return Ejecucion(pregunta, pasos, f"[sin modelo] {e}", veredicto,
                         simulado_llm=simulado)
    anota(Paso("modelo", "ejecutado",
               "pidio entregar codigo" if msg.get("tool_calls") else "respondio texto",
               ms(), "modelo"))

    # ── 11. si hay codigo: ejecutar y verificar ─────────────────────────────
    entrega, evidencia, salida, arreglado = None, [], "", False
    cobertura = []
    if msg.get("tool_calls"):
        ms = _reloj()
        entrega, error = _leer_entrega(msg)
        if error:
            anota(Paso("entrega", "error", error, ms(), "modelo"))
        else:
            anota(Paso("entrega", "ejecutado",
                       f"{len(entrega['archivos'])} archivos · "
                       f"{entrega.get('comando_test', '?')}", ms(), "modelo",
                       list(entrega["archivos"])))

            ms = _reloj()
            salida = _verificar(entrega)
            estado_ejec, cabecera, _ = skills.veredicto(salida)
            verde = estado_ejec == "verde"
            # "omitido" y no "error" cuando no se ejecuto: un paso que no corrio no ha
            # fallado. Los cuatro estados de Paso significan cosas distintas y la linea
            # de tiempo de la pagina los pinta distinto; llamar error a una omision es
            # la misma clase de mentira que llamar rojo a lo que nadie miro.
            anota(Paso("verificacion",
                       "ejecutado" if verde else
                       "omitido" if estado_ejec == "no_ejecutado" else "error",
                       salida.splitlines()[0] if salida else "(sin salida)", ms(),
                       "ejecucion", salida[:2000]))

            # `and estado_ejec != "no_ejecutado"`: sin ejecucion no hay nada que arreglar.
            # Sin esta guarda el bucle disparaba SIEMPRE con la ejecucion apagada —
            # `no_ejecutado` no es "verde"— y gastaba una llamada al modelo mandandole
            # como "SALIDA REAL" el texto de que no se ejecuto nada. Una reparacion a
            # ciegas, pagada, de un fallo que nadie ha visto.
            if not verde and estado_ejec != "no_ejecutado" and MAX_ARREGLOS:
                ms = _reloj()
                try:
                    arreglo = agent.llm(
                        [{"role": "system", "content": "Arregla la CAUSA, no el test."},
                         {"role": "user", "content": f"{contexto}\n\nSALIDA REAL:\n{salida[:2000]}"}],
                        tools=[rapido.ENTREGAR])
                    nueva, err = _leer_entrega(arreglo)
                    if not err:
                        entrega = {**entrega, **nueva}
                        arreglado = True        # se registraba siempre como False
                        salida = _verificar(entrega)
                        estado_ejec, cabecera, _ = skills.veredicto(salida)
                        verde = estado_ejec == "verde"
                        anota(Paso("verificacion (tras arreglo)",
                                   "ejecutado" if verde else "error",
                                   salida.splitlines()[0], ms(), "ejecucion", salida[:2000]))
                except Exception as e:
                    anota(Paso("arreglo", "error", f"{type(e).__name__}: {e}", ms(), "modelo"))

            ms = _reloj()
            sustituidas = rapido.simulado(pregunta, entrega.get("archivos"))
            evidencia = rapido._evidencia(entrega.get("propiedades"), salida,
                                          ejecutado=True, sustituidas=sustituidas)
            cuenta = {}
            for e in evidencia:
                cuenta[e["estado"]] = cuenta.get(e["estado"], 0) + 1
            anota(Paso("evidencia", "ejecutado",
                       " · ".join(f"{n} {k_}" for k_, n in cuenta.items()) or "sin propiedades",
                       ms(), "ejecucion", evidencia))

            # El corpus trajo anti-patrones "de cubrimiento OBLIGATORIO" y hasta ahora
            # nadie comprobaba si la entrega los cubria. Se cruza con la evidencia REAL.
            ms = _reloj()
            obligaciones_ = obligaciones.de_retrieval(r)
            cobertura = obligaciones.cobertura(obligaciones_, evidencia)
            cuenta_ob = obligaciones.resumen(cobertura)
            anota(Paso("anti-patrones", "ejecutado" if not cuenta_ob.get("no cubierta")
                       else "advertencia",
                       " · ".join(f"{n} {k_}" for k_, n in cuenta_ob.items())
                       or "el corpus no trajo anti-patrones",
                       ms(), "ejecucion", cobertura))
            if guardar:
                # La persistencia NO puede matar la ejecucion. Antes esto era una
                # llamada suelta: si reventaba (y reventaba, con salida/__pycache__),
                # la excepcion subia hasta server.py y se descartaba la respuesta
                # entera — despues de pagar la llamada y de verificar el codigo.
                ms = _reloj()
                try:
                    destino = rapido.guardar(entrega, carpeta=carpeta)
                    anota(Paso("persistencia", "ejecutado", f"guardado en {destino}",
                               ms(), "ejecucion"))
                except Exception as e:
                    anota(Paso("persistencia", "error",
                               f"no se pudo guardar: {type(e).__name__}: {e}. "
                               f"La respuesta y la evidencia siguen siendo validas.",
                               ms(), "ejecucion"))

    # El aviso se calla SOLO si la ejecucion demostro algo: entonces la correccion no
    # depende del corpus. Que la tarea "parezca" de codigo no basta — "implementar Raft"
    # dispara las mismas palabras que "implementar una calculadora" y no es lo mismo.
    hay_evidencia = bool(salida) and skills.veredicto(salida)[0] == "verde"
    respuesta = msg.get("content") or ""
    if not veredicto.suficiente and not hay_evidencia:
        respuesta = f"{veredicto.frase()}\n\n{respuesta}"

    # ── 12. traza ───────────────────────────────────────────────────────────
    fila = None
    # `guardar` decide si se escriben los ARCHIVOS. El registro es otra cosa: una llamada
    # que costo dinero tiene que quedar anotada aunque no se quisiera nada en disco. Tres
    # ejecuciones reales de las demos salieron sin traza por mezclar las dos cosas, que es
    # el mismo defecto de siempre: paso algo y no lo anoto nadie. Los dobles no ensucian
    # el fichero porque no cuestan nada y no hay nada que contabilizar.
    if guardar or not simulado:
        estado_final = skills.veredicto(salida)[0] if salida else "sin_codigo"
        ejec = skills.resultado_de(salida) if salida else None
        resultado = {
            "estado": estado_final, "evidencia": evidencia,
            "cajas": list(plan_.domains), "tokens_contexto": medidas["tokens_aprox"],
            "simulado": simulado, "arreglado": arreglado,
            "presupuesto_antes": presupuesto_antes,
            # lo que de verdad paso, no una etiqueta
            "plan": {"origen": plan_.origen, "domains": list(plan_.domains),
                     "needs_code": plan_.needs_code, "needs_symbols": plan_.needs_symbols,
                     "needs_graph": plan_.needs_graph, "depth": plan_.depth},
            "filtros": r.filtros,
            "retrieval": {"ids": r.ids(), "candidatos": r.metricas["candidatos"],
                          "metodos": r.metricas["metodos"], "ms": r.metricas["ms"],
                          "por_indice": {k: len(v) for k, v in r.por_indice.items()},
                          "simbolos": len(simbolos_hallados) or None},
            "contexto": {k: v for k, v in medidas.items() if k != "descartados"},
            "verificacion": ejec._asdict() if ejec else None,
            "antipatrones": obligaciones.resumen(cobertura) if cobertura else None,
            "cobertura_antipatrones": cobertura,
            "repair_attempts": 1 if arreglado else 0,
            "final_status": estado_final,
            "fallbacks": [{"etapa": a, "motivo": b} for a, b in r.fallbacks],
            "errores": [{"etapa": p_.nombre, "detalle": p_.resumen}
                        for p_ in pasos if p_.estado == "error"],
            "model": agent.MODEL if not simulado else "doble determinista",
            "model_route": None,          # no hay router activo: null, no inventado
            "tools": [{"tool": "verificar_codigo", "status": estado_final}] if salida else [],
        }
        fila = traza.escribir(pregunta, "pipeline", resultado, time.time() - arranque,
                              version=version or ("v2-offline" if simulado else traza.VERSION),
                              archivo=traza.ARCHIVO.parent / "trazas_noche.jsonl")

    return Ejecucion(pregunta, pasos, respuesta, veredicto, entrega, evidencia,
                     cobertura_antipatrones=cobertura, salida=salida,
                     simulado_llm=simulado, fila=fila)


def _ejecutar_proyecto(pregunta, plan_, r, contexto, medidas, veredicto,
                       pasos, anota, arranque, simulado, guardar, version,
                       presupuesto_antes=None):
    """La rama de proyecto: plano -> grupos -> verificacion -> ZIP -> registro.

    Reutiliza todo lo de arriba (retrieval, contexto, suficiencia) y todo lo de abajo
    (evidencia, traza). Lo nuevo es lo que hay en medio.

    NO llama a `rapido.guardar`: esa aplana las rutas y vacia `salida/` entera, asi que
    `app/libros/router.py` y `tests/test_libros.py` colisionarian despues de borrar lo
    anterior. Un proyecto va a su propio artefacto, con su id.
    """
    import artefactos
    import empaquetado
    import generador
    import verificacion_proyecto as VP

    ms = _reloj()
    try:
        proy, espec, pasos_gen = generador.generar(pregunta, contexto)
    except agent.ModoOffline as e:
        anota(Paso("generacion", "error", "candado offline: no se llamo a nadie",
                   ms(), "ejecucion"))
        return Ejecucion(pregunta, pasos, f"[sin modelo] {e}", veredicto,
                         simulado_llm=simulado)
    for nombre, estado, resumen, detalle in pasos_gen:
        anota(Paso(nombre, estado, resumen, 0.0, "modelo", detalle))
    if proy is None:
        anota(Paso("proyecto", "error", "no se pudo armar un proyecto", ms(), "ejecucion"))
        return Ejecucion(pregunta, pasos, "No se pudo generar el proyecto.", veredicto,
                         simulado_llm=simulado)
    anota(Paso("proyecto", "ejecutado",
               f"{proy.totales['archivos']} archivos · {proy.totales['directorios']} "
               f"directorios · {proy.totales['lineas']} lineas", ms(), "modelo",
               {"arbol": proy.rutas(), "totales": proy.totales}))

    proy.sellar()          # a partir de aqui no cambia: lo que se verifica es lo que se empaqueta
    # El reparador SI se conecta. Estuvo escrito y sin cablear, y una corrida real lo
    # destapo: un `from libros_api import crear_servidor` contra un __init__.py que no lo
    # reexporta dejaba el proyecto en FALLIDO sin intentar arreglarlo siquiera.
    cert = VP.certificar(proy, comando_test=(espec or {}).get("comando_test"),
                         reparador=generador.reparador(contexto),
                         al_avanzar=lambda f: anota(Paso(
                             f.nombre, {"ok": "ejecutado", "fallo": "error",
                                        "limitado": "fallback"}.get(f.estado, "omitido"),
                             f.detalle, f.ms, "ejecucion")))

    ms = _reloj()
    paquete = empaquetado.sellar(proy, cert, version=version or traza.VERSION)
    anota(Paso("empaquetado", "ejecutado" if paquete.ok else "error",
               (f"{paquete.nombre} · {paquete.bytes:,} bytes · "
                f"{len(paquete.inspeccion.comprobaciones)} comprobaciones de integridad"
                if paquete.ok else f"ERROR DE INTEGRIDAD: {paquete.inspeccion.motivo[:90]}"),
               ms(), "ejecucion",
               {"comprobaciones": [list(c) for c in paquete.inspeccion.comprobaciones]}))

    # El artefacto se registra SIEMPRE: sin el no hay nada que descargar, y los bytes
    # del ZIP ya existen en memoria. `guardar` solo decide si ademas se escribe en disco.
    artefacto = None
    ms = _reloj()
    try:
        artefacto = artefactos.guardar(proy, cert, paquete, en_disco=bool(guardar),
                                       simulado=simulado)
        anota(Paso("artefacto", "ejecutado",
                   f"listo para descargar · {artefacto.id}"
                   + (" · copia en disco" if guardar else " · solo en memoria"),
                   ms(), "ejecucion"))
    except Exception as e:
        anota(Paso("artefacto", "error",
                   f"no se pudo registrar: {type(e).__name__}: {e}", ms(), "ejecucion"))
    respuesta = _respuesta_de_proyecto(proy, cert, paquete, espec)
    fila = None
    if guardar or not simulado:
        resultado = {
            "estado": cert.estado, "evidencia": list(cert.evidencia),
            "cajas": list(plan_.domains), "tokens_contexto": medidas["tokens_aprox"],
            "simulado": simulado, "arreglado": bool(cert.reparaciones),
            "presupuesto_antes": presupuesto_antes,
            "plan": {"origen": plan_.origen, "domains": list(plan_.domains),
                     "needs_code": plan_.needs_code, "needs_project": True,
                     "needs_symbols": plan_.needs_symbols,
                     "needs_graph": plan_.needs_graph, "depth": plan_.depth},
            "filtros": r.filtros,
            "retrieval": {"ids": r.ids(), "candidatos": r.metricas["candidatos"],
                          "metodos": r.metricas["metodos"], "ms": r.metricas["ms"],
                          "por_indice": {k: len(v) for k, v in r.por_indice.items()},
                          "simbolos": None},
            "contexto": {k: v for k, v in medidas.items() if k != "descartados"},
            "verificacion": {"estado": cert.estado, "cabecera": cert.por_que,
                             "marcas": dict(cert.marcas)},
            "antipatrones": None, "cobertura_antipatrones": [],
            "repair_attempts": len(cert.reparaciones),
            "final_status": cert.estado,
            "fallbacks": [{"etapa": a, "motivo": b} for a, b in r.fallbacks],
            "errores": [{"etapa": p_.nombre, "detalle": p_.resumen}
                        for p_ in pasos if p_.estado == "error"],
            "model": agent.MODEL if not simulado else "doble determinista",
            "model_route": None,
            "tools": [{"tool": "generar_proyecto", "status": cert.estado}],
            "proyecto": {"archivos": proy.totales["archivos"],
                         "bytes": proy.totales["bytes"],
                         "estado": cert.estado,
                         "zip_bytes": paquete.bytes,
                         "integridad": paquete.ok,
                         "artefacto": artefacto.id if artefacto else None},
        }
        fila = traza.escribir(pregunta, "proyecto", resultado, time.time() - arranque,
                              version=version or ("v2-offline" if simulado else traza.VERSION),
                              archivo=traza.ARCHIVO.parent / "trazas_noche.jsonl")

    return Ejecucion(pregunta, pasos, respuesta, veredicto, entrega=None,
                     evidencia=cert.evidencia, simulado_llm=simulado, fila=fila,
                     proyecto=proy, certificado=cert, artefacto=artefacto)


def _respuesta_de_proyecto(proy, cert, paquete, espec):
    """El markdown. El estado sale del certificado, nunca del texto del modelo."""
    espec = espec or {}
    t = proy.totales
    partes = [f"## {proy.nombre}", ""]
    if espec.get("arquitectura"):
        partes.append(f"{espec.get('lenguaje','')} · {espec.get('framework','')} · "
                      f"{espec.get('base_datos','')} · {espec['arquitectura']}".strip(" ·"))
        partes.append("")
    partes += [f"**{t['archivos']} archivos** en {t['directorios']} directorios, "
               f"{t['lineas']} líneas.", ""]
    if espec.get("supuestos"):
        partes += ["Lo que se decidió sin que se dijera:", ""]
        partes += [f"- {s}" for s in espec["supuestos"]] + [""]

    pasan = sum(1 for v in cert.marcas.values() if v == "PASS")
    icono = {"VERIFICADO": "✅", "PARCIAL": "❔", "VALIDADO": "○",
             "FALLIDO": "❌"}.get(cert.estado, "○")
    partes += [f"### {icono} {cert.estado}", "", cert.por_que, ""]
    if cert.marcas:
        partes += [f"`{pasan}` de `{len(cert.marcas)}` marcadores en PASS. "
                   f"Verde significa *se ejecutó y pasó*, no *es correcto*.", ""]
    partes += ["| Fase | Estado | Qué pasó |", "|---|---|---|"]
    iconos = {"ok": "✅", "fallo": "❌", "limitado": "❔", "omitido": "—"}
    partes += [f"| {f.nombre} | {iconos.get(f.estado, f.estado)} | {f.detalle} |"
               for f in cert.fases]
    if not paquete.ok:
        partes += ["", f"> ⛔ **ERROR DE INTEGRIDAD** — {paquete.inspeccion.motivo}",
                   "> El ZIP no se entrega: no se puede demostrar que sea lo que se verificó."]
    return "\n".join(partes)


def _verificar(entrega):
    if (error := rapido._comprobar_sintaxis(entrega["archivos"])):
        return f"FALLO {error}"
    return SKILLS["verificar_codigo"](entrega["archivos"], entrega.get("comando_test", ""))


if __name__ == "__main__":
    import dobles
    with dobles.usar(dobles.DECISION_SIMPLE):
        ejecutar("que es un indice de postgresql", guardar=False).imprimir()
