"""Prueba la orquestacion del pipeline SIN llamar al modelo (coste cero).

Sustituye agent.llm por un doble que devuelve respuestas guionizadas, pero deja que
las skills se ejecuten de VERDAD: verificar_codigo corre Node en local y su exit code
es real. Asi se comprueba la fontaneria — despacho de tools, paso de contexto,
disparo del bucle de correccion y su tope — que es justo lo que no se puede verificar
leyendo el codigo.

    python3 prueba_bucle.py
"""

import sys as _sys
from pathlib import Path as _Path
# Este archivo vive en una subcarpeta y produccion sigue en la raiz. Sin esto, ejecutarlo
# directamente (`python3 tests/test_x.py`) pone la subcarpeta en sys.path[0] y no la raiz,
# asi que `import pipeline` no encontraria nada. Mismo patron que usan las sondas.
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ_REPO))
import json
import agent
import arquitecto

# ── el codigo con el bug real: comprueba, cede el event loop, y guarda demasiado tarde ──
BUGGY = """
const store = new Map();
let cobros = 0;
async function cobrarEnProveedor() {
  await new Promise(r => setTimeout(r, 20));      // latencia de red
  cobros++; return { txnId: "txn_" + cobros };
}
async function crearPago(key, orderId, amount) {
  const existente = store.get(key);               // 1) COMPRUEBA
  if (existente) return existente.response;
  const txn = await cobrarEnProveedor();          // 2) COBRA  <- cede el loop
  const response = { orderId, amount, transactionId: txn.txnId };
  store.set(key, { response });                   // 3) GUARDA (tarde)
  return response;
}
"""

# ── el mismo codigo con la reserva ANTES de cobrar (single-flight) ──
ARREGLADO = """
const store = new Map();
let cobros = 0;
async function cobrarEnProveedor() {
  await new Promise(r => setTimeout(r, 20));
  cobros++; return { txnId: "txn_" + cobros };
}
async function crearPago(key, orderId, amount) {
  const existente = store.get(key);
  if (existente) return existente.promesa;        // el segundo espera al primero
  const promesa = (async () => {
    const txn = await cobrarEnProveedor();
    return { orderId, amount, transactionId: txn.txnId };
  })();
  store.set(key, { promesa });                    // RESERVA antes de ceder el loop
  return promesa;
}
"""

TEST = """
(async () => {
  const [a, b] = await Promise.all([
    crearPago("abc", "order_1", 5000),
    crearPago("abc", "order_1", 5000),
  ]);
  console.log("cobros al proveedor:", cobros);
  if (cobros !== 1) {
    console.log("TEST:idempotencia:FAIL");        // el marcador es lo que se lee como evidencia
    console.error(`FAIL: se cobro ${cobros} veces con la misma clave`);
    process.exit(1);                              // exit != 0: asi SI lo detecta el bucle
  }
  console.log("TEST:idempotencia:PASS");
})();
"""

# Imprime el marcador FAIL pero sale con 0. Antes se colaba como "TESTS EN VERDE" y
# hacia falta la red de seguridad de arquitecto.py; ahora el propio ejecutor lo caza.
TEST_ROTO = TEST.replace("process.exit(1);", "// (test roto: imprime FAIL y sale con 0)")


def _texto(t):
    return {"role": "assistant", "content": t}


def _tool(codigo, test):
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": "1", "function": {"name": "verificar_codigo", "arguments": json.dumps(
            {"archivos": {"t.js": codigo + test}, "comando": "node t.js"})}}]}


def guion(escenario):
    """Las respuestas que daria el modelo, en orden. Fases 1-7 no usan tools."""
    pasos = [_texto(f"(fase {i} simulada)") for i in range(1, 8)]
    test8 = TEST_ROTO if escenario == "test_roto" else TEST
    if escenario == "nunca_arregla":
        # el "arreglo" sigue teniendo el bug: el bucle debe rendirse al llegar al tope
        pasos += [_tool(BUGGY, TEST), _texto("## Evidencia\nSOSPECHA 1: Estado: DEMOSTRADA")]
        for _ in range(6):
            pasos += [_tool(BUGGY, TEST), _texto("## Que cambie\n(no lo arreglo)")]
            pasos += [_tool(BUGGY, TEST), _texto("## Evidencia\nSOSPECHA 1: Estado: DEMOSTRADA")]
        return pasos
    if escenario == "ya_verde":
        pasos += [_tool(ARREGLADO, TEST), _texto("## Evidencia\nTodas DESCARTADAS.")]
        return pasos
    # fase 8: ejecuta el codigo con el bug -> debe fallar
    pasos += [_tool(BUGGY, test8), _texto("## Evidencia\nSOSPECHA 1: Estado: DEMOSTRADA")]
    # fase 9 (corregir) + fase 8 otra vez
    pasos += [_tool(ARREGLADO, TEST), _texto("## Que cambie\nReserva antes de cobrar.")]
    pasos += [_tool(ARREGLADO, TEST), _texto("## Evidencia\nTodas DESCARTADAS.")]
    # por si el bucle diera mas vueltas de las esperadas
    pasos += [_texto("(no deberia llegar aqui)")] * 20
    return pasos


def probar(escenario, esperado_corrigio, esperado_pendiente=False,
           limite=None, coste_por_llamada=0.0, esperado_agotado=False):
    cola = guion(escenario)

    def llm_falso(messages, **kw):
        agent.PRESUPUESTO.comprobar()          # mismo control que el llm real
        respuesta = cola.pop(0)
        agent.PRESUPUESTO.anotar({"usage": {"prompt_tokens": 1000, "completion_tokens": 300,
                                            "cost": coste_por_llamada}})
        return respuesta

    original, agent.llm = agent.llm, llm_falso
    agent.PRESUPUESTO = agent.Presupuesto(limite if limite is not None else 1e9)
    try:
        r = arquitecto.disenar("problema de prueba", mostrar=False)
    finally:
        agent.llm = original

    nombres = [f["fase"] for f in r["fases"]]
    corrigio = any("Corregir" in n for n in nombres)
    ejecuciones = [p["resultado"].splitlines()[0] for f in r["fases"] for p in f["pasos"]
                   if p["tipo"] == "skill" and p["nombre"] == "verificar_codigo"]

    quedo_pendiente = r["pendiente"] is not None
    ok = (corrigio == esperado_corrigio and quedo_pendiente == esperado_pendiente
          and (r["agotado"] is not None) == esperado_agotado)
    print(f"\n{'✅' if ok else '❌'} escenario {escenario!r}")
    print(f"   fases ejecutadas: {len(nombres)} · {'corrigio' if corrigio else 'no corrigio'}"
          f" (esperado: {'corregir' if esperado_corrigio else 'no corregir'})")
    print(f"   ejecuciones reales de node: {ejecuciones}")
    print(f"   pendiente al acabar: {r['pendiente']}")
    print(f"   gasto: {r['gasto']}" + (f"  ⛔ {r['agotado']}" if r["agotado"] else ""))
    return ok


if __name__ == "__main__":
    print("Pipeline con LLM simulado · las skills se ejecutan de verdad\n" + "─" * 66)
    resultados = [
        probar("falla", esperado_corrigio=True),    # test rojo -> debe corregir
        probar("ya_verde", esperado_corrigio=False),  # todo bien -> no debe corregir
        probar("test_roto", esperado_corrigio=True),  # imprime FAIL pero sale 0 -> red de seguridad
        probar("nunca_arregla", esperado_corrigio=True, esperado_pendiente=True),  # tope del bucle
        # tope de GASTO: con 0,02 $ por llamada y limite de 0,10 $ debe cortar a mitad.
        # OJO: 'pendiente' es False porque nada quedo DEMOSTRADAMENTE roto; simplemente
        # no llego a verificar. 'agotado' y 'pendiente' son estados distintos.
        probar("falla", esperado_corrigio=False, esperado_pendiente=False,
               limite=0.10, coste_por_llamada=0.02, esperado_agotado=True),
    ]
    print("\n" + "─" * 66)
    print("TODO OK" if all(resultados) else "HAY FALLOS")
