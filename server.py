"""Servidor minimo para ver el agente en el navegador. Solo libreria estandar."""

import hmac
import json
import os
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import agent
import arquitecto
import estado
import rapido


LENGUAJES = {".js": "javascript", ".py": "python", ".sql": "sql", ".json": "json", ".ts": "typescript"}


def rapido_a_pasos(r):
    """Convierte la salida de rapido.py en los pasos que pinta la pagina."""
    pasos = [{"tipo": "fase", "texto": "1 · Recuperar del corpus  ·  0 llamadas al modelo"}]

    if r.get("plan"):
        pasos += [{"tipo": "fase", "texto": "2 · Razonar y decidir  ·  1 llamada"},
                  {"tipo": "pensamiento", "texto": r["plan"]}]

    entrega = r.get("entrega")
    if not entrega:
        return {"pasos": pasos, "respuesta": f"No hubo entrega: {r.get('error', r.get('estado'))}"}

    carpeta, _error_guardado = _guardar_sin_morir(entrega)
    pasos += [{"tipo": "fase", "texto": "3 · Generar codigo y tests  ·  1 llamada"},
              {"tipo": "skill", "nombre": "entregar_implementacion",
               "args": {"archivos": list(entrega["archivos"]), "comando": entrega.get("comando_test")},
               "resultado": "El código va abajo, en su propia sección.\n\n"
                            + "\n".join(f"- `{ruta}` · {len(c.splitlines())} líneas"
                                         for ruta, c in entrega["archivos"].items())},
              {"tipo": "fase", "texto": "4 · Ejecutar los tests  ·  0 llamadas"},
              {"tipo": "skill", "nombre": "verificar_codigo",
               "args": {"comando": entrega.get("comando_test")}, "resultado": r["salida"]}]
    if r.get("arreglado"):
        pasos.insert(-2, {"tipo": "fase", "texto": "5 · Un arreglo (y solo uno)  ·  1 llamada"})

    icono = {"verde": "✅ tests en verde", "rojo": "❌ siguen fallando",
             "sin_evidencia": "❔ se ejecutó, pero sin evidencia de qué se probó",
             "no_ejecutado": "🚫 no llegó a ejecutarse"}.get(r["estado"], r["estado"])
    partes = [f"## {icono}",
              (f"Código guardado en `{carpeta}/` · ejecútalo con " if carpeta else
               f"⚠️ No se pudo guardar en disco ({_error_guardado}), pero el código y su "
               f"evidencia son válidos. Ejecútalo con ") +
              f"`{entrega.get('comando_test', '?')}`", "", "## Decisiones", entrega.get("decisiones", "")]
    if r.get("evidencia"):
        iconos = {"verificado": "✅ verificado", "refutado": "❌ refutado",
                  "verificado en simulación": "🟡 solo en simulación",
                  "sin verificar": "❔ sin verificar"}
        partes += ["", "## Evidencia",
                   "El estado lo decide la **ejecución**, no lo que diga el modelo.", "",
                   "| Estado | Riesgo | Propiedad demostrada | Test |", "|---|---|---|---|"]
        partes += [f"| {iconos.get(e['estado'], e['estado'])} | {e['riesgo']} | "
                   f"`{e['propiedad']}` | `{e['test_id']}` |" for e in r["evidencia"]]
        if r.get("simulado"):
            partes += ["", f"> ⚠️ **{', '.join(r['simulado'])} se sustituyó por una simulación.** "
                           "Los tests verdes prueban la lógica, **no** las garantías reales "
                           "(constraints `UNIQUE`, aislamiento, `SELECT FOR UPDATE`). "
                           "Por eso esas propiedades figuran como *solo en simulación*."]
        sin = [e for e in r["evidencia"] if e["estado"] == "sin verificar"]
        if sin:
            partes += ["", f"⚠️ **{len(sin)} de {len(r['evidencia'])} propiedades no se llegaron "
                           "a demostrar**: el modelo dijo que las cubriría y su test no apareció "
                           "en la salida."]
    if r.get("sin_cubrir"):
        partes += ["", "## Reconocido como no probado", "El propio agente admite que esto queda fuera:"]
        partes += [f"- {x}" for x in r["sin_cubrir"]]
    return {"pasos": pasos, "respuesta": "\n".join(partes)}


def _paso_json(paso):
    """Un Paso del pipeline, en algo que se pueda serializar y enseñar."""
    detalle = paso.detalle
    if isinstance(detalle, (list, tuple)):
        detalle = [list(x) if isinstance(x, tuple) else x for x in detalle]
    try:
        json.dumps(detalle)
    except (TypeError, ValueError):
        detalle = str(detalle)[:2000]
    return {"nombre": paso.nombre, "estado": paso.estado, "resumen": paso.resumen,
            "ms": round(paso.ms, 1), "fuente": paso.fuente, "detalle": detalle}


def _guardar_sin_morir(entrega):
    """(carpeta, error). Un fallo al persistir no invalida lo que ya se demostro."""
    try:
        return str(rapido.guardar(entrega).resolve()), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _resumen_de_ejecucion(e):
    """Una linea con lo que de verdad paso al ejecutar. Sin repetir el codigo."""
    import skills
    if not e.salida:
        return "> El código se entregó y **no se ejecutó**: no hay evidencia de que funcione."
    r = skills.resultado_de(e.salida)
    intentos = ("Falló, se reparó una vez y se volvió a ejecutar. "
                if getattr(e, "arreglado", False) else "")
    if r.estado == "verde":
        return (f"> {intentos}**{r.cabecera}.** Verde significa *se ejecutó y pasó*, "
                f"no *es correcto*: prueba lo que esos {len(r.marcas)} tests cubren.")
    if r.estado == "rojo":
        return f"> {intentos}**{r.cabecera}.** El código se ejecutó y falló."
    if r.estado == "sin_evidencia":
        return (f"> {intentos}**El comando terminó sin error y no imprimió ni un marcador.** "
                f"Eso no es aprobar: es que nadie sabe qué se probó.")
    return f"> {intentos}**{r.cabecera}**"


def panel_evidencia(e):
    """Las cuatro capas, separadas a proposito. Es el centro del producto.

        MODEL CLAIM    lo que el modelo dijo que iba a cubrir
        OBSERVED       lo que Mirag vio al ejecutar: comando, exit code, marcadores
        VERIFIED       lo declarado que la ejecucion demostro
        NOT VERIFIED   lo declarado que la ejecucion NO demostro, y lo que ni se pudo mirar

    Mezclarlas en una sola tabla fue durante mucho tiempo la forma de que una afirmacion
    del modelo pareciera un hecho. Aqui no se pueden confundir porque no comparten sitio.
    """
    import skills
    ejec = skills.resultado_de(e.salida) if e.salida else None
    ev = list(e.evidencia or [])

    def fila(x):
        return {"riesgo": x.get("riesgo"), "propiedad": x.get("propiedad"),
                "test_id": x.get("test_id"), "estado": x.get("estado")}

    verificadas = [fila(x) for x in ev if x.get("estado") == "verificado"]
    simuladas = [fila(x) for x in ev if x.get("estado") == "verificado en simulación"]
    pendientes = [fila(x) for x in ev if x.get("estado") in ("sin verificar", "refutado")]

    observado = None
    if ejec:
        observado = {"estado": ejec.estado, "cabecera": ejec.cabecera,
                     "marcadores": dict(ejec.marcas), "pasados": ejec.pasados,
                     "fallados": ejec.fallados, "truncada": ejec.truncada}
    elif e.entrega:
        observado = {"estado": "no_ejecutado",
                     "cabecera": "se entregó código y no se llegó a ejecutar"}

    return {
        "claim": [fila(x) for x in ev],
        "observed": observado,
        "verified": verificadas,
        "simulated": simuladas,
        "not_verified": pendientes,
        # lo que el modelo reconocio no cubrir: es una afirmacion suya, va con las suyas
        "sin_cubrir": list((e.entrega or {}).get("sin_cubrir") or []),
    }


def _linea_de_tiempo(e):
    """Una ejecucion, en lenguaje humano. La traza tiene 32 campos; esto tiene ocho filas.

    Las etapas internas del retrieval se pliegan en una sola: quince filas de `bm25:` y
    `rrf:` no cuentan la historia de lo que paso, la esconden.
    """
    import re
    filas, acumulado = [], 0.0
    interna = re.compile(r"^(filtro|bm25|vector|rrf|reranker):")
    retrieval_ms = sum(p.ms for p in e.pasos if interna.match(p.nombre))
    for paso in e.pasos:
        if interna.match(paso.nombre):
            continue
        ms = paso.ms + (retrieval_ms if paso.nombre == "recuperacion" else 0)
        acumulado += ms
        filas.append({"t": round(acumulado / 1000, 2), "ms": round(ms, 1),
                      "etapa": paso.nombre, "estado": paso.estado,
                      "resumen": paso.resumen, "fuente": paso.fuente})
    return filas


def _coste(e, demo=None):
    """Sin falsas precisiones: un doble cuesta 0 y se dice, no se disfraza de $0.0000."""
    if e.simulado_llm:
        # Dos cosas distintas otra vez: una demo tiene guion y responde; sin demo no hubo
        # decision ninguna. Decir "vino de un guion" cuando no hubo guion es inventar.
        return {"simulado": True, "demo": demo, "llamadas": 0,
                "texto": "SIMULADO · $0" if demo else "SIN MODELO · $0"}
    p = agent.PRESUPUESTO
    # Tercer caso, por la misma razon que los dos de arriba: hubo llamadas de verdad y el
    # coste reportado es exactamente 0. Pasa con los modelos gratuitos, porque el
    # proveedor no manda campo `cost` y `PRESUPUESTO.anotar` lo cuenta como 0.0 (agent.py).
    # Escribir "$0.0000" ahi sugiere una medicion de gasto que nadie hizo. Es gratis, y se
    # dice — junto con el modelo, porque "gratis" sin decir de que no informa de nada.
    if p.llamadas and p.coste == 0:
        return {"simulado": False, "gratuito": True, "modelo": agent.MODEL,
                "texto": f"GRATIS · $0 · {agent.MODEL}",
                "llamadas": p.llamadas, "tokens": p.entrada + p.salida}
    return {"simulado": False, "gratuito": False, "texto": f"${p.coste:.4f}",
            "llamadas": p.llamadas, "tokens": p.entrada + p.salida}


def _respuesta_pipeline(e, demo=None):
    """El markdown final: la respuesta, la evidencia y lo que NO se demostro."""
    # el aviso de cobertura ya lo antepone el pipeline: repetirlo aqui lo duplicaba
    partes = [e.respuesta or ""]
    # En una tarea de codigo `e.respuesta` viene vacia y la pagina saltaba directa a la
    # tabla de evidencia: el usuario veia QUE se verifico y nunca POR QUE se hizo asi.
    # Las decisiones son lo que el modelo razono, asi que van etiquetadas como suyas.
    if not (e.respuesta or "").strip() and (e.entrega or {}).get("decisiones"):
        resumen = _resumen_de_ejecucion(e)
        partes = [f"## Qué se hizo\n\n{e.entrega['decisiones'].strip()}"]
        if resumen:
            partes += ["", resumen]
    if e.evidencia:
        iconos = {"verificado": "✅ verificado", "refutado": "❌ refutado",
                  "verificado en simulación": "🟡 solo en simulación",
                  "sin verificar": "❔ sin verificar"}
        partes += ["", "## Evidencia",
                   "El estado lo decide la **ejecución**, no lo que diga el modelo.", "",
                   "| Estado | Riesgo | Propiedad demostrada | Test |", "|---|---|---|---|"]
        partes += [f"| {iconos.get(x['estado'], x['estado'])} | {x['riesgo']} | "
                   f"`{x['propiedad']}` | `{x['test_id']}` |" for x in e.evidencia]
    if getattr(e, "cobertura_antipatrones", None):
        import obligaciones
        partes += ["", obligaciones.tabla_markdown(e.cobertura_antipatrones)]
    if e.simulado_llm:
        # Dos situaciones muy distintas, y confundirlas es la mentira que cerro la Fase 6:
        # una demo preparada SI responde a lo que se pregunto; "sin modelo" no responde nada.
        if demo:
            partes += ["", f"> ⚠️ **SIMULADA · demo `{demo}`** (candado offline). La decisión "
                           "del modelo viene de un guion fijo. Lo que se recuperó, se ejecutó y "
                           "se verificó es real; lo que el modelo *decidió*, no."]
        else:
            partes += ["", "> ⛔ **SIN MODELO** (candado offline) y esta pregunta no es una de "
                           "las demos preparadas. El plan, la recuperación y el contexto de "
                           "arriba son reales; la respuesta no existe y no se inventa."]
    return "\n".join(partes)


PAGINA = Path(__file__).parent / "index.html"


class Handler(SimpleHTTPRequestHandler):
    # GET  -> SOLO index.html, por lista blanca
    # POST -> ejecuta el agente y devuelve {pasos, respuesta}

    RUTAS = ("/", "/index.html")

    def _descargar(self, consulta):
        """El ZIP de un artefacto. **El id no es un path y no puede llegar a serlo.**

        Se valida contra una regex de 24 hex, se busca en un diccionario en memoria, y
        el artefacto trae sus propios bytes. Nada de la peticion se concatena nunca a un
        Path: si alguien escribe algun dia `CARPETA / ident`, vuelve entero el agujero
        que la lista blanca cerro.

        Los bytes salen de memoria, que son EXACTAMENTE los que inspecciono el gate de
        integridad. Leerlos del disco abriria una ventana entre "se comprobo esto" y
        "se entrego lo otro".
        """
        import urllib.parse

        import artefactos
        import proyecto as _P
        if not self._autorizado():
            return
        ident = urllib.parse.parse_qs(consulta).get("id", [""])[0]
        if not artefactos.ID_VALIDO.match(ident or ""):
            self.send_error(400, "id mal formado")      # literal: no se ecoa lo recibido
            return
        art = artefactos.obtener(ident)
        if art is None:
            self.send_error(410, "ese artefacto ya no existe")
            return
        if not art.descargable:
            self.send_error(409, "ARTIFACT INTEGRITY ERROR: el paquete no paso la inspeccion")
            return
        datos = art.paquete.datos
        if _P.sha(datos) != art.paquete.sha256:         # ~1 ms, y cierra el ultimo hueco
            self.send_error(500, "ARTIFACT INTEGRITY ERROR en la entrega")
            return
        nombre = _P.nombre_seguro(art.nombre) + ".zip"
        assert "\r" not in nombre and "\n" not in nombre and '"' not in nombre
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Content-Disposition", f'attachment; filename="{nombre}"')
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Mirag-Sha256", art.paquete.sha256)
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        """Una sola ruta. Ni una mas.

        Antes se heredaba el do_GET de SimpleHTTPRequestHandler, que sirve el
        directorio de trabajo ENTERO: `curl http://<ip>:8000/.env` devolvia la clave
        de OpenRouter con un 200, y lo mismo trazas.jsonl (los prompts del usuario),
        index.html.bak y eval_cache.json. Con el servidor escuchando ademas en
        0.0.0.0, eso era un robo de credenciales desde cualquier red compartida.
        """
        self._servir(cuerpo=True)

    def do_HEAD(self):
        """La misma lista blanca. Y hacia falta decirlo aparte.

        Este docstring decia "una sola ruta, ni una mas" y era MENTIRA para HEAD:
        do_GET estaba sobreescrito pero do_HEAD seguia siendo el de
        SimpleHTTPRequestHandler, que pasa por translate_path() y responde sobre el
        directorio entero. `HEAD /.env` devolvia 200 con Content-Length: 93 y
        Last-Modified. No filtraba el cuerpo, pero si que el archivo existe, cuanto
        mide y cuando se toco — que es justo lo que la lista blanca dejo de decir.

        Sobrevivio a toda la auditoria porque los 15 tests de seguridad preguntaban
        con GET. Una prueba que solo usa un metodo solo demuestra ese metodo.
        """
        self._servir(cuerpo=False)

    def _json(self, objeto, codigo=200):
        """Una respuesta JSON. Mismas cabeceras defensivas que `_descargar`.

        Es el primer emisor de JSON del servidor: hasta ahora solo salian HTML, ZIP y
        SSE. Si falla al serializar, contesta 500 con un literal fijo; nunca se ecoa lo
        que se intento serializar, que es justo por donde se escapa un secreto.
        """
        try:
            datos = json.dumps(objeto, ensure_ascii=False).encode()
        except (TypeError, ValueError):
            datos = b'{"error":"no serializable"}'
            codigo = 500
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        return datos

    def _blockchain(self, cuerpo):
        """El estado de la capa Stellar. **El import es perezoso, y es lo importante.**

        `blockchain/` vive fuera de la cadena de produccion y tiene su propio venv. Si el
        paquete falta, si su dependencia no esta instalada o si la red no contesta, esto
        devuelve `{"disponible": false, "motivo": ...}` y el servidor sigue de pie. Un
        import arriba del archivo ataria el arranque de Mirag a un paquete externo.
        """
        try:
            import blockchain
            estado_cadena = blockchain.estado().para_la_pagina()
        except Exception as e:
            estado_cadena = {"disponible": False, "motivo": f"{type(e).__name__}: {e}",
                             "identidad": None, "wallet": None, "ultimo_pago": None,
                             "enlaces": {}}
        datos = self._json(estado_cadena)
        if cuerpo:
            self.wfile.write(datos)

    def _servir(self, cuerpo):
        ruta, _, consulta = self.path.partition("?")
        if ruta == "/descarga":
            if cuerpo:
                self._descargar(consulta)
            else:
                self.send_error(404, "No encontrado")   # HEAD no descarga
            return
        if ruta == "/api/blockchain/agent":
            self._blockchain(cuerpo)
            return
        if ruta not in self.RUTAS:
            self.send_error(404, "No encontrado")
            return
        try:
            datos = PAGINA.read_bytes()
        except OSError:
            self.send_error(500, "falta index.html")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        if cuerpo:
            self.wfile.write(datos)
    def _emitir(self, evento):
        """Un evento SSE. flush() en cada uno o el navegador no lo ve hasta el final."""
        # se guardan las ejecuciones reales para poder auditarlas al final
        if evento.get("tipo") == "skill" and \
                str(evento.get("nombre", "")).startswith("verificar_codigo"):
            self._salidas.append(evento.get("resultado", ""))
        if evento.get("tipo") == "paso" and evento.get("nombre", "").startswith("verificacion"):
            self._salidas.append(str(evento.get("detalle") or ""))
        self.wfile.write(f"data: {json.dumps(evento, ensure_ascii=False)}\n\n".encode())
        self.wfile.flush()

    RUTAS_POST = ("/", "/chat")

    def _autorizado(self):
        """True si la peticion puede pasar. Si no, ya ha respondido 401 y hay que salir.

        `MIRAG_TOKEN` vacia deja el servidor ABIERTO, que es como ha funcionado siempre en
        local, y el arranque lo dice en voz alta. No se pone un token por defecto a
        proposito: un secreto que viene de fabrica lo conoce todo el mundo y da una
        sensacion de seguridad peor que no tener ninguno.

        Con token, la comprobacion es `hmac.compare_digest` y no `==`: comparar cadenas
        con `==` corta en el primer byte distinto, y ese tiempo distinto es medible. Es
        barato hacerlo bien.

        Esto no es autenticacion de usuarios: es un secreto compartido entre el servidor
        de CodeZard y este. Quien lo tenga, puede pedirlo todo.
        """
        esperado = os.environ.get("MIRAG_TOKEN", "").strip()
        if not esperado:
            return True
        dado = (self.headers.get("X-Mirag-Token") or "").strip()
        if hmac.compare_digest(dado, esperado):
            return True
        # 401 seco: ni se dice que falta la cabecera ni que el valor esta mal, porque esa
        # diferencia le ahorra trabajo a quien prueba.
        self.send_error(401, "No autorizado")
        return False

    def do_POST(self):
        # Hasta ahora do_POST no miraba `self.path`: `POST /descarga` ejecutaba el agente.
        # Con una segunda ruta GET eso pasa de rareza a confusion.
        if self.path.split("?")[0] not in self.RUTAS_POST:
            self.send_error(404, "No encontrado")
            return
        if not self._autorizado():
            return
        # El cuerpo se parsea DENTRO de un try, y esto no es una formalidad. Antes se
        # parseaba aqui fuera y antes del `send_response`: un cuerpo mal formado, o sin
        # la clave "pregunta", reventaba el handler y socketserver cerraba la conexion
        # sin enviar NADA. El cliente veia un fetch abortado en vez de un error. Con un
        # solo cliente —la propia pagina, que siempre manda bien— eso no se notaba; con
        # CodeZard llamando desde otro servidor, se nota el primer dia.
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            peticion = json.loads(self.rfile.read(largo))
            pregunta = peticion["pregunta"]
            if not isinstance(pregunta, str) or not pregunta.strip():
                raise ValueError("'pregunta' tiene que ser un texto no vacio")
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            # El motivo se dice, pero no se ecoa el cuerpo recibido: si alguien manda una
            # clave por error, devolverla amplifica el descuido en vez de contenerlo.
            self.send_error(400, f"Peticion mal formada: {type(e).__name__}")
            return
        agent.PRESUPUESTO.reiniciar()          # el tope es POR peticion (y por hilo)
        modo = peticion.get("modo", "pipeline")
        entregable = None
        self._salidas = []

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        # atajo: si pregunta por el propio Mirag, la respuesta es un dato, no una busqueda
        if (directa := estado.responder(pregunta)):
            self._emitir({"tipo": "fase", "texto": "Atajo · 0 llamadas · 0 búsquedas"})
            self._emitir({"tipo": "fin", "respuesta": directa, "modo": "estado",
                          "gasto": "0 llamadas · 0 tokens · $0.0000"})
            return

        evidencia = linea_tiempo = coste = proyecto_json = None
        try:
            if modo == "pipeline":
                import pipeline
                emitir = lambda paso: self._emitir({"tipo": "paso", **_paso_json(paso)})
                if agent.OFFLINE:
                    # Con el candado puesto la maquina se puede ver funcionar igual: lo
                    # unico que se sustituye es la DECISION del modelo, y la respuesta
                    # lo dice. Sin esto el modo pipeline no seria demostrable sin pagar.
                    import dobles, demos
                    # Solo hay guion para las TRES demos preparadas. Para cualquier otra
                    # pregunta el guion dice que no hay modelo, en vez de contestar con
                    # seguridad a una pregunta distinta (ver demos.py).
                    demo, guion = demos.guion_para(pregunta)
                    # El chip sale de este hecho observado, no de una suposicion de la pagina.
                    self._emitir({"tipo": "paso", "nombre": "candado offline",
                                  "estado": "simulado" if demo else "sinmodelo",
                                  "ms": 0.0, "fuente": "evidencia",
                                  "resumen": (f"demo preparada «{demo}»: la decisión del modelo "
                                              f"viene de un guion fijo"
                                              if demo else
                                              "esta pregunta no es una demo preparada: no habrá "
                                              "respuesta del modelo, y no se inventa"),
                                  "detalle": {"demo": demo, "offline": True,
                                              "demos_disponibles": [d["clave"]
                                                                    for d in demos.catalogo()]}})
                    with dobles.usar(guion):
                        e = pipeline.ejecutar(pregunta, al_avanzar=emitir)
                else:
                    demo = None
                    e = pipeline.ejecutar(pregunta, al_avanzar=emitir)
                respuesta = _respuesta_pipeline(e, demo)
                if e.artefacto is not None:
                    # El proyecto manda sobre `entregable`: son dos cosas distintas y la
                    # pagina pinta una sola. Todo lo que viaja sale del manifiesto y del
                    # certificado, nunca del texto del modelo. Y el artefacto viene de
                    # `e.artefacto`, no de buscarlo: el boton tiene que apuntar a ESTE.
                    proyecto_json = e.artefacto.para_la_pagina()
                evidencia = panel_evidencia(e)
                linea_tiempo = _linea_de_tiempo(e)
                coste = _coste(e, demo)
                if e.entrega:
                    entregable = {"archivos": e.entrega["archivos"],
                                  "comando": e.entrega.get("comando_test"),
                                  "carpeta": _guardar_sin_morir(e.entrega)[0],
                                  "estado": __import__("skills").veredicto(e.salida)[0],
                                  "simulado": rapido.simulado(pregunta, e.entrega["archivos"])}
            elif modo == "arquitecto":
                r = arquitecto.disenar(pregunta, mostrar=False, al_avanzar=self._emitir)
                respuesta = r["fases"][-1]["respuesta"] if r["fases"] else "No hubo fases."
                if r.get("agotado"):
                    respuesta = f"⛔ {r['agotado']}\n\n{respuesta}"
            else:
                # 'simple' y 'rapido' se retiraron: eran dos caminos de produccion mas,
                # cada uno con su propio contexto y su propia evidencia. agent.run sigue
                # existiendo como motor interno (lo usa arquitecto), no como modo.
                respuesta = (f"El modo {modo!r} ya no existe. Los modos son: "
                             f"**pipeline** (produccion) y **arquitecto** (experimental).")
        except agent.PresupuestoAgotado as e:
            respuesta = f"⛔ {e}"
        except Exception as e:                  # lo emitido hasta aqui ya lo tiene el navegador
            respuesta = f"Error: {type(e).__name__}: {e}"

        # rapido y pipeline no pasan por agent.run, asi que se auditan aqui
        import auditoria
        respuesta, veredicto_afirmacion = auditoria.aplicar(respuesta, self._salidas)
        self._emitir({"tipo": "fin", "respuesta": respuesta, "modo": modo,
                      "entregable": entregable, "gasto": str(agent.PRESUPUESTO),
                      "afirmacion": veredicto_afirmacion,
                      # el panel y la linea de tiempo son datos, no markdown: la pagina
                      # los pinta y los tests los comprueban sin parsear HTML
                      "evidencia": evidencia, "linea_tiempo": linea_tiempo, "coste": coste,
                      "proyecto": proyecto_json})


# El bind por defecto es localhost y se queda asi: esto es una herramienta de un solo
# usuario y NO TIENE AUTENTICACION. Quien exporte MIRAG_HOST esta abriendo un servidor sin
# auth —y que ejecuta codigo— a su red; tiene que ser un acto deliberado y visible, no el
# valor por defecto que se hereda sin querer.
#
# El unico caso previsto es el contenedor, donde "0.0.0.0" no es una relajacion sino la
# unica forma de que el puerto publicado alcance al proceso: dentro del contenedor no hay
# mas red que la suya. Lo que aisla ahi no es el bind, es publicar con
# `-p 127.0.0.1:8000:8000` y no exponer el puerto al mundo. Ver docs/DESPLIEGUE.md.
HOST_POR_DEFECTO = "127.0.0.1"
PUERTO_POR_DEFECTO = 8000


def escucha_en():
    """(host, puerto) donde escuchar. Por defecto, solo localhost."""
    host = os.environ.get("MIRAG_HOST", HOST_POR_DEFECTO).strip() or HOST_POR_DEFECTO
    try:
        puerto = int(os.environ.get("MIRAG_PORT", PUERTO_POR_DEFECTO))
    except ValueError:
        puerto = PUERTO_POR_DEFECTO
    return host, puerto


if __name__ == "__main__":
    _host, _puerto = escucha_en()
    print(f"Abre http://localhost:{_puerto}")
    if not os.environ.get("MIRAG_TOKEN", "").strip():
        print("  Sin MIRAG_TOKEN: cualquiera que alcance este puerto puede pedir. Para\n"
              "  que solo entre tu servidor de CodeZard, pon MIRAG_TOKEN y mandalo en\n"
              "  la cabecera X-Mirag-Token.")
    if _host != HOST_POR_DEFECTO:
        print(f"  AVISO: escuchando en {_host}, no solo en localhost. Este servidor no "
              f"tiene autenticacion y ejecuta codigo: no lo expongas a una red abierta.")
    # ThreadingHTTPServer y no HTTPServer: con un solo hilo, una peticion larga
    # (el modo arquitecto son ~10 min) congela la pagina entera.
    ThreadingHTTPServer((_host, _puerto), Handler).serve_forever()
