"""El agente: una llamada HTTP a OpenRouter y un bucle. Eso es todo."""

import json
import os
import threading
import urllib.request
from pathlib import Path
from skills import SKILLS, TOOLS

try:  # carga la clave del archivo .env
    for linea in open(Path(__file__).parent / ".env"):
        clave, _, valor = linea.strip().partition("=")
        if clave:
            os.environ.setdefault(clave, valor)
except OSError:
    # sin .env el proyecto tiene que seguir importandose: los tests corren offline,
    # en una maquina limpia y sin claves. Solo falla quien intente llamar de verdad.
    pass

# El defecto NO cambia: quien no diga nada sigue con el modelo de siempre. Pedir el modo
# gratis es un acto explicito, y por eso vive en una variable.
#   MIRAG_MODELO=openrouter/free  → el router de modelos gratuitos de OpenRouter, que
#   reparte entre los que hay y filtra por las capacidades de la peticion, tool calling
#   incluido (Mirag lo necesita para sus skills). Mismo endpoint y misma clave.
# Lo que cuesta: 20 peticiones por minuto y 50 al dia (1.000 si alguna vez compraste
# 10 $ de credito), y el catalogo de modelos gratuitos rota sin avisar.
MODEL = os.environ.get("MIRAG_MODELO", "anthropic/claude-haiku-4.5").strip() \
        or "anthropic/claude-haiku-4.5"
LIMITE_USD = float(os.environ.get("LIMITE_USD", "0"))   # tope por ejecucion; 0 = sin tope
# Configurable por la misma razon, y solo por esa: todos los proveedores que interesan
# (OpenRouter, NVIDIA, Groq, Gemini) hablan el mismo dialecto de chat/completions, asi que
# cambiar de uno a otro es cambiar esta URL y el modelo. Nada mas del transporte cambia.
URL = os.environ.get("MIRAG_LLM_URL", "https://openrouter.ai/api/v1/chat/completions").strip() \
      or "https://openrouter.ai/api/v1/chat/completions"

# El candado: por defecto NO se llama a nadie. No confiamos en acordarnos de no gastar,
# lo impedimos en el unico sitio del proyecto que abre un socket. Para gastar de verdad:
# MIRAG_OFFLINE=0 python3 server.py
OFFLINE = os.environ.get("MIRAG_OFFLINE", "1") != "0"
SYSTEM = ("Eres un tutor de backend. Consulta los documentos antes de responder cosas tecnicas y di de que "
          "documento sacas cada cosa. Si no esta en los documentos, dilo. Usa la calculadora para cuentas. "
          "Responde breve. "
          "Cuando ejecutes tests, cada caso debe imprimir una linea exacta TEST:<id>:PASS o TEST:<id>:FAIL. Es lo unico que se lee para saber que quedo demostrado. NO afirmes que un test paso si no ves su marcador en la salida real: un exit 0 solo demuestra que el comando no se cayo, no que probara nada.")


class PresupuestoAgotado(RuntimeError):
    """Se corta ANTES de gastar mas, no despues de la factura."""


class ModoOffline(RuntimeError):
    """Alguien intento llamar al modelo con el candado puesto.

    Falla ruidosamente a proposito: es preferible un test en rojo a una factura.
    """


class Presupuesto:
    """Cuenta lo gastado de verdad: OpenRouter devuelve el coste de cada llamada."""

    def __init__(self, limite_usd):
        self.limite = limite_usd
        self.coste = 0.0
        self.entrada = self.salida = self.llamadas = 0

    def anotar(self, respuesta):
        u = respuesta.get("usage") or {}
        self.llamadas += 1
        self.entrada += u.get("prompt_tokens", 0)
        self.salida += u.get("completion_tokens", 0)
        self.coste += u.get("cost", 0.0)

    def comprobar(self):
        if self.limite <= 0:                    # 0 = sin tope, solo contabilidad
            return
        if self.coste >= self.limite:
            raise PresupuestoAgotado(
                f"Tope alcanzado: ${self.coste:.4f} de ${self.limite:.2f} en {self.llamadas} "
                f"llamadas. Sube LIMITE_USD si quieres seguir.")

    def reiniciar(self):
        self.__init__(self.limite)

    def __str__(self):
        tope = "sin tope" if self.limite <= 0 or self.limite >= 1e6 else f"de ${self.limite:.2f}"
        return (f"{self.llamadas} llamadas · {self.entrada + self.salida:,} tokens · "
                f"${self.coste:.4f} {tope}")


class _PorHilo(threading.local):
    """Cada peticion tiene su propio contador.

    Con ThreadingHTTPServer dos peticiones a la vez compartian el mismo objeto y
    se reseteaban el contador entre ellas: el gasto salia mal y el tope tambien.
    """

    def __init__(self):
        self.actual = Presupuesto(LIMITE_USD)


_HILO = _PorHilo()


class _Proxy:
    """Para que el resto del codigo siga escribiendo agent.PRESUPUESTO."""

    def __getattr__(self, nombre):
        return getattr(_HILO.actual, nombre)

    def __setattr__(self, nombre, valor):
        # sin esto, 'agent.PRESUPUESTO.limite = 0.5' se escribia en el proxy y el
        # presupuesto de verdad no se enteraba: un no-op silencioso justo en la pieza
        # que existe para cortar el gasto
        setattr(_HILO.actual, nombre, valor)

    def __str__(self):
        return str(_HILO.actual)


PRESUPUESTO = _Proxy()


def llm(messages, tools=None):
    """Una sola llamada al modelo. Le mandamos la conversacion + las tools disponibles.

    Las tools van como ARGUMENTO, no como global: con el servidor multihilo, cambiar
    agent.TOOLS desde una peticion se lo colaba a las demas.
    """
    if OFFLINE:                        # el candado, antes que nada
        raise ModoOffline(
            "MIRAG_OFFLINE esta puesto: no se llama a OpenRouter. Para probar sin gastar usa "
            "los dobles de dobles.py; para gastar de verdad, MIRAG_OFFLINE=0.")
    PRESUPUESTO.comprobar()            # cortar ANTES de gastar, no despues
    cuerpo = {"model": MODEL, "messages": messages, "max_tokens": 12000,
              "usage": {"include": True}}                      # pide el coste real
    # None = las de siempre · una lista = esas · [] = NINGUNA, y entonces no se manda
    # la clave. Sin este caso, una pregunta conceptual recibia las 8 skills y el modelo
    # se ponia a llamarlas en un pipeline que no las iba a ejecutar.
    herramientas = TOOLS if tools is None else tools
    if herramientas:
        cuerpo["tools"] = herramientas
    body = json.dumps(cuerpo).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
        "Content-Type": "application/json",
    })
    respuesta = json.loads(urllib.request.urlopen(req, timeout=60).read())
    PRESUPUESTO.anotar(respuesta)
    return respuesta["choices"][0]["message"]


RECIENTES = 2          # cuantos resultados de tool se mandan enteros
UMBRAL = 40_000        # a partir de cuantos caracteres empieza a recortar


def _recortar(messages):
    """Los trozos del corpus se reenvian en CADA vuelta y el coste crece al cuadrado.

    Los ultimos RECIENTES resultados van enteros; los anteriores, resumidos: el modelo
    ya razono sobre ellos y solo necesita recordar que los consulto.
    """
    if sum(len(m.get("content") or "") for m in messages) < UMBRAL:
        return messages
    indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    a_recortar = set(indices[:-RECIENTES] if len(indices) > RECIENTES else [])
    return [{**m, "content": f"[recortado: {len(m['content'])} caracteres ya consultados]"}
            if i in a_recortar else m
            for i, m in enumerate(messages)]


def run(pregunta, max_vueltas=5, system=None, al_avanzar=None):
    # 'messages' ES la memoria del agente: todo lo que pasa se acumula aqui.
    messages = [{"role": "system", "content": system or SYSTEM}, {"role": "user", "content": pregunta}]
    pasos = []  # solo para poder enseniar el flujo por pantalla

    for _ in range(max_vueltas):
        try:
            msg = llm(_recortar(messages))
        except PresupuestoAgotado:
            raise                                    # esta si sube: la maneja quien llama
        except Exception as e:                       # red, JSON del proveedor, lo que sea
            return {"pasos": pasos, "respuesta": f"Se corto la ejecucion: {type(e).__name__}: {e}"}
        messages.append(msg)

        if not msg.get("tool_calls"):
            # Unico punto donde conviven la prosa final y el registro de ejecuciones.
            # Sin esto, el modelo podia leer una salida sin marcadores y escribir "los 3
            # tests pasaron", y esa frase llegaba al usuario sin que nada la contradijera.
            return {"pasos": pasos,
                    "respuesta": _auditar(msg.get("content"), pasos)}   # respuesta final

        if msg.get("content"):  # a veces "piensa en voz alta" antes de usar una skill
            paso = {"tipo": "pensamiento", "texto": msg["content"]}
            pasos.append(paso)
            if al_avanzar:
                al_avanzar(paso)

        for call in msg["tool_calls"]:
            nombre = call["function"]["name"]
            # el modelo puede mandar argumentos mal, incompletos o JSON cortado:
            # el error se le DEVUELVE como resultado para que reintente, no se propaga
            try:
                # strict=False: los saltos de linea literales dentro de las cadenas
                # son invalidos en JSON estricto y el modelo los manda constantemente
                args = json.loads(call["function"]["arguments"] or "{}", strict=False)
                if nombre not in SKILLS:
                    # sin la lista, el modelo repite la misma llamada imposible y
                    # se gasta otra vuelta para nada
                    raise LookupError(
                        f"la skill {nombre!r} NO existe. Las unicas disponibles son: "
                        f"{', '.join(sorted(SKILLS))}. Usa una de esas o responde sin tools.")
                resultado = SKILLS[nombre](**args)
            except json.JSONDecodeError as e:
                args, resultado = {}, f"ERROR: los argumentos no son JSON valido ({e}). Reintenta."
            except TypeError as e:
                resultado = f"ERROR: argumentos incorrectos para {nombre}: {e}. Mira el schema y reintenta."
            except Exception as e:
                resultado = f"ERROR ejecutando {nombre}: {type(e).__name__}: {e}"
            paso = {"tipo": "skill", "nombre": nombre, "args": args, "resultado": resultado}
            pasos.append(paso)
            if al_avanzar:
                al_avanzar(paso)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": resultado})
        # ...y volvemos a llamar al modelo, ahora con los resultados dentro.

    return {"pasos": pasos,
            "respuesta": _auditar("Me quede sin vueltas.", pasos)}


def _auditar(respuesta, pasos):
    """El aviso se antepone; el texto del modelo se conserva entero debajo."""
    import auditoria                      # tardio: auditoria importa skills, y skills a mi no
    texto, _ = auditoria.aplicar(respuesta or "", auditoria.salidas_de_pasos(pasos))
    return texto


if __name__ == "__main__":
    print("Escribe una pregunta (Ctrl+C para salir)")
    while True:
        r = run(input("\n> "))
        for p in r["pasos"]:
            if p["tipo"] == "skill":
                resumen = ' '.join(p['resultado'].split())[:100]
                print(f'  [tool] {p["nombre"]}({p["args"]}) -> {resumen}...')
            else:
                print(f'  [pensó] {" ".join(p["texto"].split())[:100]}...')
        print(r["respuesta"])
        print(f"  [gasto] {PRESUPUESTO}")
