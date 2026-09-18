"""Dobles determinsticos del LLM: el orquestador no nota la diferencia, y no se paga.

QUE ES Y QUE NO ES
    Desde fuera, un Doble se comporta como agent.llm: recibe messages y devuelve un
    message con content o con tool_calls. Todo lo que hay ALREDEDOR del modelo corre de
    verdad — el retrieval, las skills, la ejecucion de tests, la verificacion, la traza.

    Lo unico simulado es la DECISION del modelo. Por eso lo que se prueba con esto se
    marca SIMULATED y no VERIFIED LOCALLY: demuestra que la maquina funciona cuando el
    modelo contesta lo esperado, no que el modelo vaya a contestar eso.

COSTE
    Un doble no gasta. Anota coste 0.0 y marca la traza como simulada. No se inventa un
    coste "equivalente": cero llamadas son cero dolares, y asi hay que reportarlo.

USO
    with dobles.usar(dobles.PLAN_VALIDO + dobles.CODIGO_CALCULADORA):
        r = rapido.implementar("...")     # sin tocar la red
"""

import contextlib
import json

import agent

CONTADOR = {"llamadas": 0}          # para poder afirmar "no se llamo ni una vez"


# ── construir mensajes con la forma que devuelve OpenRouter ──────────────────

def texto(contenido):
    """Una respuesta normal, sin tools."""
    return {"role": "assistant", "content": contenido}


def tool(nombre, argumentos, contenido=None, id_="call_1"):
    """Una respuesta que pide ejecutar una skill."""
    return {"role": "assistant", "content": contenido,
            "tool_calls": [{"id": id_, "type": "function",
                            "function": {"name": nombre,
                                         "arguments": json.dumps(argumentos, ensure_ascii=False)}}]}


def tool_crudo(nombre, argumentos_crudos, id_="call_1"):
    """Una tool con los argumentos TAL CUAL, para simular JSON roto."""
    return {"role": "assistant", "content": None,
            "tool_calls": [{"id": id_, "type": "function",
                            "function": {"name": nombre, "arguments": argumentos_crudos}}]}


# ── guiones listos ───────────────────────────────────────────────────────────

PLAN_VALIDO = [texto('Voy a mirar bases de datos y sistemas distribuidos.\n'
                     '{"goal":"evitar doble reserva","domains":["04","08"],'
                     '"technologies":["PostgreSQL"],"needs_code":true,"depth":"deep"}')]

PLAN_INCOMPLETO = [texto('{"goal":"algo","domains":["04","08"],"technologies":["Postg')]

PLAN_INVALIDO = [texto("No he entendido la pregunta, lo siento.")]

PLAN_FORMATO_VIEJO = [texto("He razonado sobre el problema.\n\n**CAJAS: 03, 07**")]

DECISION_SIMPLE = [texto("Un indice de PostgreSQL es una estructura que acelera las "
                         "busquedas a cambio de encarecer las escrituras.")]

# Codigo real y ejecutable: lo importante es que la VERIFICACION corra de verdad.
CALCULADORA = '''\
"""Calculadora minima."""


class ErrorDeCalculo(ValueError):
    pass


def calculate(a, b, operation):
    if operation not in ("add", "subtract", "multiply", "divide"):
        raise ErrorDeCalculo(f"operacion no soportada: {operation}")
    if operation == "divide" and b == 0:
        raise ErrorDeCalculo("division por cero")
    return {"add": a + b, "subtract": a - b,
            "multiply": a * b, "divide": a / b if b else None}[operation]
'''

TEST_CALCULADORA = '''\
from calculator import calculate, ErrorDeCalculo

fallos = 0


def comprobar(id_, condicion):
    global fallos
    print(f"TEST:{id_}:{'PASS' if condicion else 'FAIL'}")
    if not condicion:
        fallos += 1


comprobar("suma", calculate(2, 3, "add") == 5)
comprobar("resta", calculate(5, 3, "subtract") == 2)
comprobar("multiplica", calculate(4, 3, "multiply") == 12)
comprobar("divide", calculate(6, 3, "divide") == 2)

try:
    calculate(1, 0, "divide")
    comprobar("division_por_cero", False)
except ErrorDeCalculo:
    comprobar("division_por_cero", True)

try:
    calculate(1, 2, "potencia")
    comprobar("operacion_invalida", False)
except ErrorDeCalculo:
    comprobar("operacion_invalida", True)

print(f"=== RESUMEN === {6 - fallos} PASADOS, {fallos} FALLIDOS")
raise SystemExit(1 if fallos else 0)
'''

# el mismo codigo pero roto: para probar el camino del arreglo
CALCULADORA_ROTA = CALCULADORA.replace(
    'if operation == "divide" and b == 0:\n        raise ErrorDeCalculo("division por cero")',
    'pass')

_ENTREGA = {
    "archivos": {"calculator.py": CALCULADORA, "test_calculator.py": TEST_CALCULADORA},
    "comando_test": "python3 test_calculator.py",
    "decisiones": "Excepcion propia en vez de dejar salir ZeroDivisionError, para no "
                  "filtrar trazas internas al cliente (caja 03).",
    "propiedades": [
        {"riesgo": "division por cero revienta sin control",
         "propiedad": "calculate(1,0,'divide') lanza ErrorDeCalculo",
         "test_id": "division_por_cero"},
        {"riesgo": "una operacion desconocida devuelve algo en vez de fallar",
         "propiedad": "calculate(1,2,'potencia') lanza ErrorDeCalculo",
         "test_id": "operacion_invalida"},
        {"riesgo": "las cuatro operaciones basicas calculan mal",
         "propiedad": "add/subtract/multiply/divide dan el resultado correcto",
         "test_id": "suma"},
    ],
    "sin_cubrir": ["Numeros muy grandes y precision de punto flotante",
                   "Entradas que no sean numeros"],
}

CODIGO_CALCULADORA = [tool("entregar_implementacion", _ENTREGA)]

CODIGO_ROTO_LUEGO_ARREGLADO = [
    tool("entregar_implementacion",
         {**_ENTREGA, "archivos": {"calculator.py": CALCULADORA_ROTA,
                                   "test_calculator.py": TEST_CALCULADORA}}),
    tool("entregar_implementacion", _ENTREGA),      # el arreglo
]

# ── un PROYECTO entero, por grupos, como lo entregaria el modelo ────────────
# El codigo vive en fixture_proyecto.py y SE EJECUTA DE VERDAD: la demo canonica lo
# verifica ejecutando sus tests y pegandole al servidor por HTTP. Si dejara de
# funcionar, la demo se pondria roja, que es justo lo que tiene que pasar.
def _grupo(claves):
    import fixture_proyecto as F
    return tool("entregar_grupo",
                {"archivos": {r: F.ARCHIVOS[r] for r in claves}, "notas": ""})


def _proyecto_libros():
    import fixture_proyecto as F
    return ([tool("especificar_proyecto", F.ESPEC)]
            + [_grupo(F.GRUPOS[g]) for g in ("nucleo", "dominio", "tests", "docs")])


class _Perezoso(list):
    """El guion se arma al usarlo: asi `dobles` no importa `fixture_proyecto` al cargar."""

    def __iter__(self):
        return iter(_proyecto_libros())

    def __len__(self):
        return 5


PROYECTO_LIBROS = _Perezoso()


JSON_ROTO = [tool_crudo("entregar_implementacion", '{"archivos": {"a.py": "print(1)"'),
             tool("entregar_implementacion", _ENTREGA)]

SKILL_QUE_NO_EXISTE = [tool("skill_inventada", {"x": 1}),
                       texto("Vale, no existe. Respondo sin tools.")]

BUSCA_Y_RESPONDE = [tool("buscar_en_docs", {"query": "outbox pattern"}),
                    texto("El outbox pattern resuelve la doble escritura.")]


# ── el doble ─────────────────────────────────────────────────────────────────

class Doble:
    """Se comporta como agent.llm. Va devolviendo el guion, en orden."""

    def __init__(self, guion, coste=0.0, fallar_en=None, excepcion=None):
        self.guion = list(guion)
        self.coste = coste
        self.fallar_en = fallar_en          # numero de llamada que debe reventar
        self.excepcion = excepcion or RuntimeError("el modelo fallo")
        self.llamadas = 0
        self.recibido = []                  # lo que se le mando, para poder afirmar sobre ello

    def __call__(self, messages, tools=None):
        self.llamadas += 1
        CONTADOR["llamadas"] += 1
        self.recibido.append({"messages": messages, "tools": tools})
        if self.fallar_en == self.llamadas:
            raise self.excepcion
        agent.PRESUPUESTO.comprobar()       # el tope se respeta igual que con el modelo real
        agent.PRESUPUESTO.anotar({"usage": {"prompt_tokens": 0, "completion_tokens": 0,
                                            "cost": self.coste}})
        if not self.guion:
            return texto("(el guion se quedo sin respuestas)")
        return self.guion.pop(0)


@contextlib.contextmanager
def usar(guion, **kwargs):
    """Sustituye agent.llm por un doble mientras dure el bloque."""
    doble = guion if isinstance(guion, Doble) else Doble(guion, **kwargs)
    original = agent.llm
    agent.llm = doble
    try:
        yield doble
    finally:
        agent.llm = original


if __name__ == "__main__":
    import skills
    print("el codigo de los fixtures se ejecuta de VERDAD:\n")
    salida = skills.verificar_codigo(_ENTREGA["archivos"], _ENTREGA["comando_test"])
    print("  bueno →", salida.splitlines()[0])
    roto = skills.verificar_codigo(
        {"calculator.py": CALCULADORA_ROTA, "test_calculator.py": TEST_CALCULADORA},
        "python3 test_calculator.py")
    print("  roto  →", roto.splitlines()[0])
    print(f"\n  marcas en la salida buena: "
          f"{[l for l in salida.splitlines() if l.startswith('TEST:')]}")
