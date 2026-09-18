"""De una petición a un proyecto entero, en pocas llamadas y sin JSON gigantes.

LA ESTRATEGIA

    1 llamada   especificar + plano   qué se construye y qué archivo hace qué
    2-4         por grupos            núcleo · dominio · tests+docs
    0-2         reparación selectiva  solo los archivos implicados

    Ni un JSON gigante con todo el proyecto (se corta por max_tokens y no hay forma de
    saber qué falta), ni una llamada por archivo (14 llamadas por proyecto).

COMO SE SOSTIENE LA CONSISTENCIA ENTRE LLAMADAS

    Cada grupo recibe el CONTRATO: qué exporta cada archivo ya generado y qué está aún
    pendiente. Y para las dependencias directas del grupo, además, su código real. El
    prompt no crece con el proyecto porque no viaja todo, solo lo que hace falta.

    Y después se comprueba con AST. Declarar no es cumplir: `dependencias.analizar` lee
    los imports de verdad y los cruza con los símbolos que los archivos definen de verdad.
    Es el mismo principio que `skills.veredicto`: manda lo observado.
"""

import json

import agent
import dependencias
import proyecto as P

MAX_LLAMADAS = 7

# El contrato que Mirag impone y el modelo no negocia. Es lo que hace verificable el CRUD.
def _interpretes():
    """Los que existen EN ESTA maquina. Observado con shutil.which, no supuesto: el
    modelo escribio `python -m unittest` y aqui solo hay `python3`."""
    import skills
    return ", ".join(sorted(skills.INTERPRETES)) or "python3"


CONTRATO_HTTP = """\
REGLAS OBLIGATORIAS DEL PROYECTO (las pone Mirag, no son negociables):
- El entrypoint expone `crear_servidor(puerto=0, bd=":memory:")` que DEVUELVE un
  ThreadingHTTPServer ya construido y SIN arrancarlo. Quien lo arranca es quien llama.
- NADA se ejecuta al importar un modulo. El arranque va bajo `if __name__ == "__main__":`.
- `sqlite3.connect(..., check_same_thread=False)` y un `threading.Lock` en las escrituras.
- Cada paquete lleva su `__init__.py`.
- Los tests van en `tests/` y usan `unittest`. OBLIGATORIO: el plano tiene que incluir
  al menos un archivo en `tests/`. Sin tests no hay nada que verificar y el proyecto se
  entrega como FALLIDO.
- El `comando_test` tiene que empezar por uno de los interpretes que EXISTEN en esta
  maquina: {interpretes}. No uses `python` ni `pytest`: aqui no estan.
- Solo biblioteca estandar, salvo que la peticion pida explicitamente otra cosa.
- Las rutas de archivo son relativas, sin `..`, con extension conocida."""

def contrato_base():
    return CONTRATO_HTTP.format(interpretes=_interpretes())


ESPECIFICAR = {"type": "function", "function": {
    "name": "especificar_proyecto",
    "description": "Define QUE se va a construir y con que archivos, sin escribir codigo.",
    "parameters": {"type": "object", "properties": {
        "nombre": {"type": "string", "description": "en minusculas y guiones, ej: libros-api"},
        "lenguaje": {"type": "string"},
        "framework": {"type": "string", "description": "'stdlib' si no hace falta ninguno"},
        "base_datos": {"type": "string"},
        "arquitectura": {"type": "string"},
        "entidad": {"type": "string", "description": "la entidad principal, ej: libro"},
        "recurso": {"type": "string", "description": "la ruta REST, ej: /libros"},
        "campos": {"type": "array", "items": {"type": "string"},
                   "description": "los campos de la entidad"},
        "dependencias": {"type": "array", "items": {"type": "string"},
                         "description": "solo las que de verdad hagan falta. Vacio si stdlib."},
        "comando_test": {"type": "string",
                         "description": "empieza por python3 o node. Nunca `python` ni `pytest`."},
        "supuestos": {"type": "array", "items": {"type": "string"},
                      "description": "lo que decidiste sin que te lo dijeran, y por que"},
        "archivos": {"type": "array", "description": "el plano: un archivo por entrada, SIN contenido",
            "items": {"type": "object", "properties": {
                "ruta": {"type": "string"},
                "tipo": {"type": "string", "enum": ["codigo", "test", "entrypoint", "config", "doc"]},
                "proposito": {"type": "string"},
                "exporta": {"type": "array", "items": {"type": "string"},
                            "description": "funciones y clases que otros van a importar"},
                "depende_de": {"type": "array", "items": {"type": "string"},
                               "description": "rutas de este mismo proyecto"},
                "grupo": {"type": "string", "enum": ["nucleo", "dominio", "tests", "docs"]}},
                "required": ["ruta", "tipo", "proposito", "exporta", "depende_de", "grupo"]}}},
        "required": ["nombre", "lenguaje", "framework", "base_datos", "arquitectura",
                     "entidad", "recurso", "campos", "dependencias", "comando_test",
                     "supuestos", "archivos"]}}}

ENTREGAR_GRUPO = {"type": "function", "function": {
    "name": "entregar_grupo",
    "description": "El contenido completo de los archivos de UN grupo del plano.",
    "parameters": {"type": "object", "properties": {
        "archivos": {"type": "object", "additionalProperties": {"type": "string"},
                     "description": "ruta -> contenido completo del archivo"},
        "notas": {"type": "string", "description": "decisiones de este grupo"}},
        "required": ["archivos"]}}}

REPARAR = {"type": "function", "function": {
    "name": "reparar_archivos",
    "description": "Devuelve SOLO los archivos que cambias. No reescribas el proyecto entero.",
    "parameters": {"type": "object", "properties": {
        "archivos": {"type": "object", "additionalProperties": {"type": "string"}},
        "causa": {"type": "string", "description": "que estaba mal, en una frase"}},
        "required": ["archivos", "causa"]}}}

GRUPOS = ("nucleo", "dominio", "tests", "docs")


def _argumentos(mensaje, diagnostico=None):
    """Los argumentos del tool-call, o None. `diagnostico` recoge POR QUE no salieron.

    "0 archivos" es un silencio: no distingue "el modelo contesto en prosa" de "el JSON
    venia cortado a la mitad por max_tokens". Y son dos problemas distintos con dos
    arreglos distintos.
    """
    apuntar = diagnostico.append if diagnostico is not None else (lambda _x: None)
    llamadas = mensaje.get("tool_calls") or []
    if not llamadas:
        texto = (mensaje.get("content") or "").strip()
        apuntar(f"el modelo no llamo a la herramienta; contesto "
                f"{len(texto)} caracteres de texto: {texto[:120]!r}")
        return None
    crudo = llamadas[0].get("function", {}).get("arguments", "")
    try:
        return json.loads(crudo, strict=False)
    except (ValueError, KeyError, TypeError) as e:
        apuntar(f"el JSON del tool-call no se pudo leer ({type(e).__name__}: {e}). "
                f"{len(crudo)} caracteres, acaba en {crudo[-60:]!r}")
        return None


def contrato(plano, proy, grupo):
    """Qué exporta cada archivo: lo ya generado, y lo que aún no existe.

    Solo se adjunta el CODIGO de las dependencias directas del grupo. El prompt no crece
    con el proyecto.
    """
    lineas = ["INTERFACES DEL PROYECTO. Solo puedes importar lo que aparece aqui o la",
              "biblioteca estandar. Un import que no este aqui se detecta con AST y la",
              "entrega se rechaza.", ""]
    del_grupo = [f for f in plano if f.get("grupo") == grupo]
    necesarios = {r for f in del_grupo for r in (f.get("depende_de") or [])}
    for ficha in plano:
        ruta = ficha.get("ruta", "")
        hecho = proy.obtener(ruta) is not None
        exporta = ", ".join(ficha.get("exporta") or []) or "(nada que importar)"
        estado = "YA GENERADO" if hecho else "PENDIENTE — no lo importes todavia"
        lineas.append(f"  {ruta:<34} exporta: {exporta}   [{estado}]")
    cuerpos = []
    for ruta in sorted(necesarios):
        archivo = proy.obtener(ruta) if ruta else None
        if archivo:
            cuerpos.append(f"\n--- {ruta} (tu grupo lo importa, aqui va su codigo real)\n"
                           f"{archivo.texto}")
    return "\n".join(lineas) + ("\n" + "\n".join(cuerpos) if cuerpos else "")


def generar(peticion, contexto, al_avanzar=None, llm=None):
    """(proyecto, espec, pasos). Consume `MAX_LLAMADAS` como mucho."""
    llamar = llm or agent.llm
    pasos = []

    def anota(nombre, estado, resumen, detalle=None):
        pasos.append((nombre, estado, resumen, detalle))
        if al_avanzar:
            al_avanzar(nombre, estado, resumen, detalle)

    sistema = (f"{contexto}\n\n{contrato_base()}\n\n"
               "Primero define el proyecto y su plano de archivos. Sin escribir codigo.")
    msg = llamar([{"role": "system", "content": sistema},
                  {"role": "user", "content": peticion}], tools=[ESPECIFICAR])
    espec = _argumentos(msg)
    if not espec or not isinstance(espec.get("archivos"), list) or not espec["archivos"]:
        anota("especificacion", "error", "el modelo no devolvio un plano utilizable")
        return None, espec, pasos

    plano = [f for f in espec["archivos"] if isinstance(f, dict) and f.get("ruta")]
    # La ESTRUCTURA la decide Mirag, no el modelo. Medido sobre 6 corridas reales: en 5
    # el plano venia sin un solo archivo en tests/, aunque la peticion los pedia y el
    # contrato los marca como obligatorios. Generar trece archivos y suspenderlos despues
    # por "no hay tests" es caro y ademas es culpa nuestra: si sabemos que faltan, se
    # ponen. El contenido lo sigue escribiendo el modelo, en su grupo.
    plano, añadidos = completar_plano(plano, espec)
    if añadidos:
        anota("plano", "fallback",
              f"el plano no traia tests: se añadieron {len(añadidos)} archivos",
              {"añadidos": añadidos})
    problemas = validar_plano(plano, espec)
    if problemas:
        # Se dice AQUI, no despues de generar once archivos y fallar por estructura.
        anota("plano", "error", "; ".join(problemas), {"problemas": problemas})
    anota("especificacion", "ejecutado",
          f"{espec.get('nombre','proyecto')} · {espec.get('framework','?')} · "
          f"{len(plano)} archivos planeados",
          {"espec": {k: v for k, v in espec.items() if k != "archivos"},
           "plano": [f.get("ruta") for f in plano]})

    proy = P.Proyecto(espec.get("nombre") or "proyecto", espec)
    usados = 1
    for grupo in GRUPOS:
        del_grupo = [f for f in plano if f.get("grupo") == grupo]
        if not del_grupo:
            continue
        if usados >= MAX_LLAMADAS:
            anota(f"generacion:{grupo}", "omitido",
                  f"tope de {MAX_LLAMADAS} llamadas alcanzado: este grupo no se genero")
            continue
        pedido = "\n".join(f"  {f['ruta']} — {f.get('proposito','')}" for f in del_grupo)
        msg = llamar([
            {"role": "system", "content": f"{contrato_base()}\n\n{contrato(plano, proy, grupo)}"},
            {"role": "user", "content": f"Escribe el contenido COMPLETO de estos archivos "
                                        f"del grupo '{grupo}':\n{pedido}"}],
            tools=[ENTREGAR_GRUPO])
        usados += 1
        motivos = []
        datos = _argumentos(msg, motivos) or {}
        archivos = datos.get("archivos") if isinstance(datos.get("archivos"), dict) else {}
        if not archivos and not motivos:
            motivos.append(f"el tool-call no traia archivos: claves {sorted(datos)}")
        puestos, rechazados = [], []
        for ruta, contenido in archivos.items():
            try:
                proy.añadir(ruta, contenido, tipo=_tipo_de(ruta, plano), grupo=grupo)
                puestos.append(ruta)
            except P.RutaProhibida as e:
                rechazados.append(f"{ruta}: {e}")
        anota(f"generacion:{grupo}", "ejecutado" if puestos else "error",
              (f"{len(puestos)} archivos"
               + (f" · {len(rechazados)} rechazados" if rechazados else "")
               + (f" · {motivos[0][:90]}" if not puestos and motivos else "")),
              {"archivos": puestos, "rechazados": rechazados, "motivos": motivos,
               "pedidos": [f["ruta"] for f in del_grupo]})

    return (proy if proy.listar() else None), espec, pasos


def completar_plano(plano, espec):
    """(plano, añadidos). Pone lo que la estructura exige y el modelo se dejo.

    Solo la ENTRADA del manifiesto: la ruta, su proposito y de que depende. El contenido
    lo escribe el modelo cuando le toque el grupo `tests`, igual que el resto.
    """
    rutas = {f.get("ruta", "") for f in plano}
    if any(r.startswith("tests/") and r.endswith(".py") for r in rutas):
        return plano, []

    entidad = (espec or {}).get("entidad") or "api"
    entrypoint = next((f["ruta"] for f in plano if f.get("tipo") == "entrypoint"), "")
    if not entrypoint:
        entrypoint = next((f["ruta"] for f in plano
                           if f.get("ruta", "").endswith("main.py")), "")
    añadidos = []
    for ruta, proposito in (
            ("tests/__init__.py", "paquete de tests"),
            (f"tests/test_{entidad}.py",
             f"CRUD completo de {entidad} por HTTP real, con unittest")):
        if ruta in rutas:
            continue
        plano = plano + [{"ruta": ruta, "tipo": "test", "proposito": proposito,
                          "exporta": [], "grupo": "tests",
                          "depende_de": [entrypoint] if entrypoint and ruta.endswith(
                              f"test_{entidad}.py") else []}]
        añadidos.append(ruta)
    return plano, añadidos


def validar_plano(plano, espec):
    """Lo que tiene que traer un plano para que lo demas signifique algo."""
    import skills
    problemas = []
    rutas = [f.get("ruta", "") for f in plano]
    if not any(r.startswith("tests/") for r in rutas):
        problemas.append("el plano no incluye ningun archivo en tests/: sin tests no hay "
                         "nada que verificar")
    if not any(f.get("tipo") == "entrypoint" for f in plano):
        problemas.append("el plano no marca ningun entrypoint")
    comando = (espec or {}).get("comando_test") or ""
    primero = comando.split()[0] if comando.split() else ""
    if primero and primero not in skills.INTERPRETES:
        problemas.append(f"el comando de test empieza por {primero!r} y aqui solo hay "
                         f"{', '.join(sorted(skills.INTERPRETES))}")
    return problemas


def _tipo_de(ruta, plano):
    for ficha in plano:
        if ficha.get("ruta") == ruta:
            return ficha.get("tipo") or "codigo"
    return "test" if ruta.startswith("tests/") else "codigo"


def reparador(contexto, llm=None):
    """Devuelve una función `(proyecto, errores, salida, intento) -> (nuevo, cambiados, causa)`.

    Solo se le pasan los archivos implicados: no se regenera el proyecto entero porque
    falle `libros/repositorio.py`.
    """
    llamar = llm or agent.llm

    def reparar(proy, errores, salida, intento):
        implicados = sorted({h.archivo for h in errores} |
                            _archivos_del_fallo(proy, salida))
        if not implicados:
            implicados = [a.ruta for a in proy.listar() if a.ruta.endswith(".py")][:4]
        cuerpo = "\n\n".join(f"--- {r}\n{proy.obtener(r).texto}"
                             for r in implicados if proy.obtener(r))
        diagnostico = "\n".join(f"  {h.archivo}:{h.linea} {h.detalle}" for h in errores)
        msg = llamar([
            {"role": "system", "content": f"{contrato_base()}\n\nArregla la CAUSA, no el sintoma. "
                                          f"Devuelve SOLO los archivos que cambies."},
            {"role": "user", "content":
                f"Intento {intento}. Esto esta mal:\n{diagnostico or '(ver la salida)'}\n\n"
                f"Salida de la ejecucion:\n{(salida or '')[:3000]}\n\n"
                f"Archivos implicados:\n{cuerpo}"}],
            tools=[REPARAR])
        datos = _argumentos(msg) or {}
        nuevos = datos.get("archivos") if isinstance(datos.get("archivos"), dict) else {}
        if not nuevos:
            return proy, (), datos.get("causa", "el modelo no devolvio ningun archivo")
        copia = P.Proyecto(proy.nombre, proy.espec)
        for archivo in proy.listar():
            copia.añadir(archivo.ruta, archivo.texto, tipo=archivo.tipo, grupo=archivo.grupo)
        cambiados = []
        for ruta, contenido in nuevos.items():
            try:
                copia.añadir(ruta, contenido)
                cambiados.append(ruta)
            except P.RutaProhibida:
                pass
        return copia, tuple(cambiados), datos.get("causa", "")

    return reparar


def _archivos_del_fallo(proy, salida):
    """Los archivos que aparecen nombrados en una traza de error."""
    if not salida:
        return set()
    return {a.ruta for a in proy.listar() if a.ruta in salida}
