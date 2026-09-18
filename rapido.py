"""Camino barato: 2 llamadas al LLM en el caso bueno, 3 en el peor.

El pipeline de arquitecto.py son ~40 llamadas. Aqui la idea es otra: el LLM decide
QUE hay que demostrar, y el ordenador demuestra si ocurre. Todo lo mecanico
(recuperar, comprobar sintaxis, ejecutar tests) cuesta 0 llamadas.

    recuperar        0 LLM   busqueda directa con la peticion del usuario
    razonar+decidir  1 LLM
    codigo+tests     1 LLM   en la MISMA llamada, con salida estructurada
    verificar        0 LLM   sintaxis + ejecutar de verdad
    arreglar         1 LLM   UNA sola oportunidad
    verificar        0 LLM

Los anti-patrones recuperados son de cubrimiento OBLIGATORIO: no dependemos de que
al modelo se le ocurra probar concurrencia, se lo exige el corpus.
"""

import codecs
import json
import re
import shutil
import sys
from pathlib import Path

import time

import agent
import rag
import skills
import traza
from skills import SKILLS

MAX_LLAMADAS = 3
MAX_ARREGLOS = 1

ENTREGAR = {"type": "function", "function": {
    "name": "entregar_implementacion",
    "description": "Entrega el codigo y sus tests. Llamala UNA vez, con todo dentro.",
    "parameters": {"type": "object", "properties": {
        "archivos": {"type": "object", "additionalProperties": {"type": "string"},
                     "description": "ruta -> contenido. El codigo Y los tests, ejecutables."},
        "comando_test": {"type": "string",
                         "description": "Como correr los tests. Empieza por uno de: "
                                        + ", ".join(sorted(skills.INTERPRETES))},
        "decisiones": {"type": "string", "description": "que decidiste y por que, citando las cajas"},
        "propiedades": {"type": "array",
            "description": "Que se va a DEMOSTRAR. Una entrada por riesgo, con la propiedad "
                           "falsable y el id del test que la prueba.",
            "items": {"type": "object", "properties": {
                "riesgo": {"type": "string", "description": "que puede salir mal"},
                "propiedad": {"type": "string",
                              "description": "afirmacion comprobable, p.ej. 'exitosos <= 1'"},
                "test_id": {"type": "string",
                            "description": "id exacto que el test imprime en TEST:<id>:PASS"}}}},
        "sin_cubrir": {"type": "array", "items": {"type": "string"},
                       "description": "riesgos que NO pudiste probar. Se honesto: esto se publica."}},
        "required": ["archivos", "comando_test", "decisiones", "propiedades", "sin_cubrir"]}}}


def _una_llamada(prompt, system, tools):
    """Una vuelta sin bucle de agente: el modelo responde o llama a UNA tool."""
    return agent.llm([{"role": "system", "content": system},
                      {"role": "user", "content": prompt}], tools=tools)


def _comprobar_sintaxis(archivos):
    """Gratis, y se come la mitad de los fallos antes de ejecutar nada."""
    for ruta in archivos:
        if ruta.endswith(".js"):
            r = SKILLS["verificar_codigo"](archivos, f"node --check {ruta}")
            if skills.veredicto(r)[0] in ("rojo", "no_ejecutado"):
                return f"sintaxis de {ruta}: {r}"
        elif ruta.endswith(".py"):
            r = SKILLS["verificar_codigo"](archivos, f"python3 -m py_compile {ruta}")
            if skills.veredicto(r)[0] in ("rojo", "no_ejecutado"):
                return f"sintaxis de {ruta}: {r}"
    return None


def _como_lista(valor):
    """Devuelve una lista, venga como venga.

    Formas que han llegado de verdad: lista de dicts, lista de strings, un string
    con JSON dentro, un string suelto y None. Los structured outputs ACOTAN la
    salida, no la garantizan (ver conocimientos/18-ai-backend.md).
    """
    if valor is None:
        return []
    if isinstance(valor, str):
        # strict=False: el modelo mete saltos de linea LITERALES dentro de las cadenas.
        # El segundo intento des-escapa: a veces llega DOBLEMENTE escapado ("[\\n {\\"a\\"...").
        def _desescapar(x):
            # unicode_escape lee los bytes como Latin-1 y rompe el UTF-8 ("acción" ->
            # "acciÃ³n"). El viaje de ida y vuelta lo conserva.
            return x.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")

        for preparar in (lambda x: x, _desescapar):
            try:
                return _como_lista(json.loads(preparar(valor), strict=False))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        return [valor]
    if isinstance(valor, dict):
        return [valor]
    return list(valor)


def _lista_de_textos(valor):
    return [x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
            for x in _como_lista(valor)]


# tecnologia -> como se reconoce en el codigo que de verdad la usa
TECNOLOGIAS = {
    "PostgreSQL": (r"postgres|postgresql", r"require\(['\"]pg|from ['\"]pg|import pg\b|psycopg"),
    "MySQL": (r"\bmysql\b", r"mysql2?|require\(['\"]mysql"),
    "Redis": (r"\bredis\b", r"require\(['\"]redis|from redis|ioredis"),
    "MongoDB": (r"\bmongo", r"mongodb|mongoose"),
    "Kafka": (r"\bkafka\b", r"kafkajs|from kafka"),
    "S3": (r"\bs3\b", r"aws-sdk|boto3|@aws-sdk"),
}
# Express o FastAPI no deciden si el codigo es correcto: la invariante vive en la
# base de datos o en la cola. Sustituir el framework HTTP no degrada la evidencia.


def simulado(peticion, archivos):
    """Tecnologias que la peticion pide y el codigo EJECUTADO no usa de verdad.

    El modelo tiende a sustituir Postgres por un Map cuando no puede ejecutarlo, y
    despues presenta los tests verdes como si probaran Postgres. Esto lo detecta el
    ejecutor leyendo el codigo, no preguntandoselo al modelo.
    """
    codigo = "\n".join((archivos or {}).values())
    faltan = []
    for nombre, (en_peticion, en_codigo) in TECNOLOGIAS.items():
        if re.search(en_peticion, peticion, re.I) and not re.search(en_codigo, codigo, re.I):
            faltan.append(nombre)
    return faltan


def _evidencia(propiedades, salida, ejecutado, sustituidas=()):
    """Cruza lo que el modelo DIJO que probaria con lo que la ejecucion demuestra.

    El estado no lo decide el modelo: se lee de la salida real. Si el test_id no
    aparece, la propiedad queda SIN VERIFICAR aunque el modelo jure que la cubrio.
    """
    marcas = skills.marcas_de(salida)      # del cuerpo: la cabecera no es evidencia
    lista = _como_lista(propiedades)
    if not lista and ejecutado:
        # Declarar CERO propiedades era el camino mas silencioso: _evidencia devolvia []
        # y entonces la tabla de evidencia se omitia entera, dejando un "tests en verde"
        # sin un solo aviso. Declarar cinco y no probarlas gritaba; no declarar ninguna, no.
        return [{"riesgo": "el modelo no declaro ninguna propiedad que demostrar",
                 "propiedad": "(no declaro ninguna)", "test_id": "(ninguno)",
                 "ejecutado": False, "sustituido": list(sustituidas),
                 "estado": "sin verificar"}]
    filas = []
    for p in lista:
        if not isinstance(p, dict):
            p = {"riesgo": str(p)}
        tid = str(p.get("test_id", "")).strip()
        marca = marcas.get(tid)
        estado = {"PASS": "verificado", "FAIL": "refutado"}.get(marca, "sin verificar")
        # un test verde contra un Map NO prueba nada sobre PostgreSQL
        if estado == "verificado" and sustituidas:
            estado = "verificado en simulación"
        filas.append({
            "riesgo": str(p.get("riesgo", "?")),
            "propiedad": str(p.get("propiedad", "(no la declaro)")),
            "test_id": tid or "(sin id)",
            "ejecutado": bool(ejecutado and marca),
            "sustituido": list(sustituidas),
            "estado": estado})
    return filas


def guardar(entrega, carpeta=None):
    """El codigo se ejecuta en un temporal y se perderia. Aqui queda en disco.

    Dos cosas que estaban mal y rompian el producto:

    1. `viejo.unlink()` no borra directorios. Ejecutar el codigo entregado —que es
       literalmente lo que dice COMO_EJECUTAR.txt— crea salida/__pycache__, y desde
       ese momento TODA tarea de codigo posterior moria con PermissionError, despues
       de haber pagado la llamada y verificado el codigo.
    2. la carpeta era relativa al cwd, no al modulo: arrancar el servidor desde otro
       directorio creaba y vaciaba un salida/ ajeno.
    """
    destino = Path(carpeta) if carpeta else Path(__file__).parent / "salida"
    if destino.exists():
        for viejo in destino.iterdir():        # no mezclar con la ejecucion anterior
            shutil.rmtree(viejo) if viejo.is_dir() else viejo.unlink()
    destino.mkdir(exist_ok=True)
    for ruta, contenido in entrega["archivos"].items():
        archivo = destino / Path(ruta).name          # sin rutas raras del modelo
        archivo.write_text(contenido)
    (destino / "COMO_EJECUTAR.txt").write_text(
        f"{entrega.get('comando_test', '?')}\n\n{entrega.get('decisiones', '')}\n")
    return destino


def cajas_del_plan(plan, peticion=None, k=4):
    """Que cajas acotan la busqueda.

    Dos fuentes, y la segunda es la que de verdad aguanta: la linea `CAJAS:` que
    pedimos al modelo (que escribe como le parece: en negrita, con punto final...)
    y, si no la pone, las cajas de donde salieron los mejores trozos de la primera
    recuperacion. Esa segunda no depende del formato de nadie.
    """
    if plan and (m := re.search(r"CAJAS\s*:?\**(.*)$", plan, re.I | re.M)):
        nums = re.findall(r"\b(\d{1,2})\b", m.group(1))   # la linea entera, y de ahi los numeros
        if nums:
            return [n.zfill(2) for n in dict.fromkeys(nums)][:k]
    if peticion:
        # de donde vino lo mejor que encontramos: 0 llamadas, 0 formato que parsear
        vistas = dict.fromkeys(t.caja.split("·")[0].strip()
                               for t, _ in rag._ranking(rag.TROZOS, peticion, k * 2))
        return list(vistas)[:k]
    return []


def recuperar(peticion, cajas=None):
    """Conocimiento + anti-patrones + fallos. Con `cajas`, acotado a esas areas."""
    return {"conocimiento": rag.buscar(peticion, cajas),
            "antipatrones": rag.buscar_antipatrones(peticion, cajas),
            "fallos": rag.buscar_fallos(peticion, cajas)}


def _contexto(peticion, partes):
    return (f"PETICION DEL USUARIO:\n{peticion}\n\n"
            f"=== CONOCIMIENTO RECUPERADO ===\n{partes['conocimiento']}\n\n"
            f"=== ANTI-PATRONES (cubrir con un test CADA UNO) ===\n{partes['antipatrones']}\n\n"
            f"=== MODOS DE FALLO CONOCIDOS ===\n{partes['fallos']}")


def implementar(peticion, mostrar=True, al_avanzar=None, version=traza.VERSION):
    arranque = time.time()

    def log(*a):
        if mostrar:
            print(*a, flush=True)

    def aviso(tipo, **campos):
        if al_avanzar:
            al_avanzar({"tipo": tipo, **campos})

    # ── 1. RECUPERAR AMPLIO · 0 llamadas ─────────────────────────────────────
    partes = recuperar(peticion)
    base = _contexto(peticion, partes)
    tokens_amplio = len(base) // 4
    log(f"[0 LLM] recuperado de las 19 cajas: ~{tokens_amplio:,} tokens, "
        f"{partes['antipatrones'].count('✗ NO:')} anti-patrones")
    aviso("fase", texto=f"1 · Recuperar del corpus · 0 llamadas · "
                        f"{partes['antipatrones'].count('✗ NO:')} anti-patrones a cubrir")

    # ── 2. RAZONAR Y DECIDIR · 1 llamada ─────────────────────────────────────
    log("\n[LLM 1/3] razonar y decidir")
    aviso("fase", texto="2 · Razonar y decidir · 1 llamada")
    plan = _una_llamada(base + """

--- TAREA ---
Antes de escribir codigo, decide. Se breve: listas, no prosa.

## Requisitos      funcionales y no funcionales, incluidos los que asumes
## Decisiones      cada una atada a un requisito, citando la caja
## Que hay que demostrar
   Por CADA anti-patron de arriba que aplique, la afirmacion verificable que habra que probar.
   Formato: "riesgo -> test que lo detectaria". Si un anti-patron no aplica, dilo y por que.
   La concurrencia es obligatoria si hay estado compartido: un test secuencial NO vale.

Termina con UNA linea exacta con las 2-4 cajas que de verdad hacen falta, por numero:

CAJAS: 03, 07, 08

No escribas codigo todavia.""",
        "Eres un arquitecto de backend senior. Consulta solo el conocimiento dado.", [])["content"]
    log(plan)
    aviso("pensamiento", texto=plan)

    # ── 2b. RE-RECUPERAR CON EL PLAN · 0 llamadas ────────────────────────────
    # el plan salio de la llamada anterior, asi que acotar no cuesta ninguna mas
    cajas = cajas_del_plan(plan, peticion)
    if cajas:
        base = _contexto(peticion, recuperar(peticion, cajas))
        ahorro = 100 - (len(base) // 4) * 100 // max(tokens_amplio, 1)
        nombres = sorted({t.caja for t in rag.TROZOS
                          if any(c in t.caja for c in cajas)})
        log(f"[0 LLM] acotado a {len(cajas)} cajas: ~{len(base)//4:,} tokens ({ahorro}% menos)")
        aviso("fase", texto=f"2b · Acotado a {', '.join(nombres)} · "
                            f"0 llamadas · {ahorro}% menos contexto")

    # ── 3. CODIGO + TESTS · 1 llamada ────────────────────────────────────────
    log("\n[LLM 2/3] generar codigo y tests (misma llamada)")
    aviso("fase", texto="3 · Generar código y tests · 1 llamada")
    msg = _una_llamada(f"{base}\n\n=== TU PLAN ===\n{plan}\n\n"
        """--- TAREA ---
Escribe el codigo Y los tests, y entregalo llamando a entregar_implementacion.

Los tests deben poder EJECUTARSE aqui mismo: solo la libreria estandar. Nada de `require`
de paquetes (express, uuid, pg...) NI EN EL CODIGO QUE PRUEBAN.

Si el usuario pide un framework (Express, FastAPI...), SEPARA en dos archivos:
  - logica.js   la logica de negocio en funciones puras, sin imports externos  <- lo que se prueba
  - api.js      el endpoint del framework, que solo llama a logica.js          <- NO se ejecuta aqui
y que comando_test ejecute unicamente el archivo de tests, que importa logica.js.
Esa separacion no es un apaño para el test: es lo que dice la caja 05 sobre testabilidad.

Simula la persistencia en memoria, pero manteniendo la ESTRUCTURA real del codigo: si comprueba y
luego guarda, el test debe poder pillar la ventana entre ambos.
Si la dependencia externa es asincrona en la realidad, simulala asincrona o el test no prueba nada.
EL TEST DEBE SALIR CON EXIT != 0 SI FALLA (process.exit(1) / assert). Imprimir FAIL no es reportarlo.

Cada test imprime ademas una linea EXACTA `TEST:<id>:PASS` o `TEST:<id>:FAIL`, con el mismo <id>
que pusiste en propiedades[].test_id. Es lo que se lee para saber que quedo demostrado: una
propiedad cuyo test_id no aparezca en la salida se marca SIN VERIFICAR, digas lo que digas.

NO SOBREVENDAS en `decisiones`. Si el estado vive en memoria del proceso, no escribas "ACID",
"transaccional", "durable" ni "rollback": no hay commit, ni durabilidad, ni una operacion externa
que pueda fallar a medias. Di lo que SI es: "seccion critica serializada dentro de un proceso".
Lo que no puedas demostrar va en sin_cubrir.

Un test por cada linea de "Que hay que demostrar". Lo que no puedas probar va en sin_cubrir.

SI SUSTITUYES UNA TECNOLOGIA POR UNA SIMULACION (un Map en vez de PostgreSQL, un mutex en vez
de una transaccion), la propiedad NO queda demostrada para esa tecnologia: pon en sin_cubrir
que las garantias reales (constraints UNIQUE, aislamiento, SELECT FOR UPDATE) siguen sin probar.
Y comprueba que las constraints que escribes expresen la invariante: `UNIQUE(slot_id, user_id)`
permite que DOS usuarios distintos reserven el mismo slot.

TAMAÑO, y es un limite duro: SOLO el camino critico y sus tests. Nada de endpoints extra
(GET /x, /admin), ni comentarios decorativos, ni banners de ==== , ni README, ni arranque de
servidor. Menos de 120 lineas por archivo. Si no cabe, recorta funcionalidad accesoria, nunca
los tests: una entrega que no cabe llega cortada y no sirve para nada.""",
        "Eres un backend senior. Entregas codigo ejecutable y tests que fallan cuando deben.",
        [ENTREGAR])

    def leer_entrega(mensaje):
        """El modelo puede agotar max_tokens a mitad del JSON y entregarlo cortado."""
        llamada = (mensaje.get("tool_calls") or [None])[0]
        if not llamada:
            return None, "el modelo no llamo a entregar_implementacion"
        crudo = llamada["function"]["arguments"]
        try:
            return json.loads(crudo, strict=False), None
        except json.JSONDecodeError as e:
            return None, (f"entrega cortada a {len(crudo)} caracteres ({e}). "
                          f"Suele ser max_tokens: pide una implementacion mas pequeña.")

    entrega, error = leer_entrega(msg)
    if error:
        log(f"  ⚠ {error}")
        r = {"estado": "sin_entrega", "error": error, "plan": plan,
             "gasto": str(agent.PRESUPUESTO), "cajas": cajas, "tokens_contexto": len(base) // 4}
        r["traza"] = traza.escribir(peticion, "rapido", r, time.time() - arranque, version)
        return r
    log(f"  archivos: {list(entrega['archivos'])} · comando: {entrega.get('comando_test')}")
    aviso("skill", nombre="entregar_implementacion",
          args={"archivos": list(entrega["archivos"]), "comando": entrega.get("comando_test")},
          resultado="\n\n".join(f"**{ruta}**\n\n```\n{codigo}\n```"
                                 for ruta, codigo in entrega["archivos"].items()))

    # ── 4. VERIFICAR · 0 llamadas ────────────────────────────────────────────
    def verificar(archivos, comando):
        if (error := _comprobar_sintaxis(archivos)):
            return f"FALLO {error}"
        return SKILLS["verificar_codigo"](archivos, comando)

    log("\n[0 LLM] sintaxis + ejecutar tests")
    aviso("fase", texto="4 · Ejecutar los tests de verdad · 0 llamadas")
    salida = verificar(entrega["archivos"], entrega["comando_test"])
    log(salida[:1500])
    aviso("skill", nombre="verificar_codigo",
          args={"comando": entrega.get("comando_test")}, resultado=salida)

    # ── 5. ARREGLAR UNA VEZ · 1 llamada ──────────────────────────────────────
    arreglado = False
    if skills.veredicto(salida)[0] != "verde":
        log("\n[LLM 3/3] un intento de arreglo (y solo uno)")
        aviso("fase", texto="5 · Un arreglo, y solo uno · 1 llamada")
        msg = _una_llamada(
            f"{base}\n\n=== CODIGO ===\n{json.dumps(entrega['archivos'])[:6000]}\n\n"
            f"=== SALIDA REAL DE LOS TESTS ===\n{salida[:3000]}\n\n"
            "--- TAREA ---\nArregla la CAUSA del fallo, no el test. Entrega otra vez con "
            "entregar_implementacion, con los MISMOS tests. Cada test sigue teniendo que "
            "imprimir TEST:<id>:PASS o TEST:<id>:FAIL: sin marcadores no hay evidencia.",
            "Eres un backend senior arreglando tu propio codigo.", [ENTREGAR])
        nueva, error = leer_entrega(msg)
        if error:
            log(f"  ⚠ el arreglo no llego entero: {error}")
        else:
            entrega = {**entrega, **nueva}      # el arreglo puede omitir campos: fusionar
            salida = verificar(entrega["archivos"], entrega["comando_test"])
            arreglado = True
            log(salida[:1500])
            aviso("skill", nombre="verificar_codigo (tras el arreglo)",
                  args={"comando": entrega.get("comando_test")}, resultado=salida)

    verde = skills.veredicto(salida)[0] == "verde"
    r = {"estado": "verde" if verde else "rojo", "plan": plan, "entrega": entrega,
            "cajas": cajas, "tokens_contexto": len(base) // 4,
            "salida": salida, "arreglado": arreglado,
            "sin_cubrir": _lista_de_textos(entrega.get("sin_cubrir")),
            "simulado": simulado(peticion, entrega.get("archivos")),
            "evidencia": _evidencia(entrega.get("propiedades"), salida, ejecutado=True,
                                    sustituidas=simulado(peticion, entrega.get("archivos"))),
            "gasto": str(agent.PRESUPUESTO)}
    r["traza"] = traza.escribir(peticion, "rapido", r, time.time() - arranque, version)
    aviso("gasto", texto=traza.linea(r["traza"]))
    return r


if __name__ == "__main__":
    peticion = " ".join(sys.argv[1:]) or input("Que hay que implementar?\n> ")
    r = implementar(peticion)
    print(f"\n{'═' * 70}")
    if r.get("entrega"):
        destino = guardar(r["entrega"])
        print(f"CODIGO EN: {destino.resolve()}/  "
              f"({', '.join(sorted(p.name for p in destino.iterdir()))})")
    print(f"ESTADO: {r['estado'].upper()}" + ("  (tras un arreglo)" if r.get("arreglado") else ""))
    for e in r.get("evidencia", []):
        icono = {"verificado": "✅", "refutado": "❌"}.get(e["estado"], "❔")
        print(f"  {icono} {e['estado'].upper():13} {e['riesgo']}")
        print(f"       propiedad: {e['propiedad']}  ·  test: {e['test_id']}")
    for s in r.get("sin_cubrir", []):
        print(f"  ⚠ SIN EVIDENCIA: {s}")
    print(f"GASTO: {r['gasto']}")
    if r.get("traza"):
        print(f"RESUMEN: {traza.linea(r['traza'])}")
