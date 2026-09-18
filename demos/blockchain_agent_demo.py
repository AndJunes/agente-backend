"""El flujo completo: wallet, fondeo, registro 8004 y verificación contra la cadena.

    uv run --project blockchain python demos/blockchain_agent_demo.py            # leer
    uv run --project blockchain python demos/blockchain_agent_demo.py --crear    # keypair
    uv run --project blockchain python demos/blockchain_agent_demo.py --fondear
    uv run --project blockchain python demos/blockchain_agent_demo.py --registrar
    uv run --project blockchain python demos/blockchain_agent_demo.py --abi      # el spec

Nada de esto se ejecuta solo. Cada paso que escribe en la cadena pide su bandera, con el
operador delante. Sin banderas solo lee y muestra.

Necesita `MIRAG_BLOCKCHAIN=testnet`. Con el candado puesto (el valor por defecto) la demo
dice qué falta y sale sin tocar la red.
"""

import sys as _sys
from pathlib import Path as _Path
_RAIZ = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_RAIZ))

import os
import sys

# El mismo cargador de .env que usa agent.py: el entorno real gana sobre el archivo.
try:
    for _linea in open(_RAIZ / ".env"):
        _c, _, _v = _linea.strip().partition("=")
        if _c:
            os.environ.setdefault(_c, _v)
except OSError:
    pass

import blockchain as B
from blockchain import config, metadata


def linea(c="─"):
    print(c * 74)


def campo(k, v, corto=False):
    v = str(v) if v is not None else "—"
    print(f"  {k:<22} {v[:44] + '…' if corto and len(v) > 44 else v}")


def exigir_red():
    try:
        motivo = config.impedimento()
    except config.RedDesconocida as e:
        print(f"  ✗ {e}")
        sys.exit(1)
    if motivo:
        print(f"  ✗ {motivo}")
        print(f"    Para la demo: MIRAG_BLOCKCHAIN=testnet uv run --project blockchain \\")
        print(f"                  python demos/blockchain_agent_demo.py")
        sys.exit(1)


def mostrar_abi():
    """Lee el spec del contrato DESDE la cadena. Es lo que produjo docs/blockchain.md."""
    exigir_red()
    from stellar_sdk import SorobanServer
    from stellar_sdk.xdr import SCSpecEntryKind, SCSpecType
    a = config.ajustes()

    def txt(x):
        for attr in ("sc_symbol", "sc_string"):
            if hasattr(x, attr):
                x = getattr(x, attr)
        return x.decode() if isinstance(x, bytes) else str(x)

    def tipo(t):
        n = SCSpecType(t.type.value).name.replace("SC_SPEC_TYPE_", "")
        if n == "UDT":
            return txt(t.udt.name)
        if n == "OPTION":
            return f"Option<{tipo(t.option.value_type)}>"
        if n == "VEC":
            return f"Vec<{tipo(t.vec.element_type)}>"
        if n == "RESULT":
            return f"Result<{tipo(t.result.ok_type)},{tipo(t.result.error_type)}>"
        return n

    print(f"\n  ABI leida de {a['identity_registry']}\n")
    spec = SorobanServer(a["rpc"]).get_contract_spec(a["identity_registry"])
    for e in spec:
        if e.kind != SCSpecEntryKind.SC_SPEC_ENTRY_FUNCTION_V0:
            continue
        f = e.function_v0
        args = ", ".join(f"{txt(x.name)}: {tipo(x.type)}" for x in f.inputs)
        print(f"    {txt(f.name)}({args}) -> "
              + (", ".join(tipo(o) for o in f.outputs) or "()"))


def crear():
    from blockchain.wallet import claves
    if claves.hay_secreto():
        print("  ✗ ya hay STELLAR_SECRET_KEY. No la piso: borrala a mano si querés otra.")
        sys.exit(1)
    pub, sec = claves.generar()
    print("\n  Wallet nueva. Copiá estas dos lineas a .env (que NO se versiona):\n")
    print(f"    STELLAR_PUBLIC_KEY={pub}")
    print(f"    STELLAR_SECRET_KEY={sec}")
    print("\n  La secreta no vuelve a poder leerse. Despues: --fondear y --registrar.")


def fondear():
    exigir_red()
    from blockchain.wallet import servicio
    print(f"  fondeando {servicio.direccion()} con Friendbot…")
    h = servicio.fondear_testnet()
    w = servicio.wallet()
    campo("tx", h)
    campo("saldo", f"{w.saldo} XLM")


def registrar():
    exigir_red()
    from blockchain.identity import registro
    from blockchain.wallet import claves, servicio
    if registro.agent_id_configurado() is not None:
        print(f"  ✗ ya hay STELLAR_AGENT_ID={registro.agent_id_configurado()}. "
              f"Borralo de .env si querés registrar otro.")
        sys.exit(1)
    mia = claves.direccion()
    print(f"  registro contiene {registro.total()} agentes")
    print(f"  register_with_uri(caller={mia[:10]}…, agent_uri=<data URI>) firmando…")
    aid, tx1 = registro.registrar()
    campo("agent_id", aid)
    campo("tx", tx1)
    print(f"  set_agent_wallet({aid}, {mia[:10]}…) firmando…")
    tx2 = registro.asociar_wallet(aid)
    campo("tx", tx2)
    print("\n  Copiá esto a .env:\n")
    print(f"    STELLAR_AGENT_ID={aid}")
    print(f"    STELLAR_TX_REGISTRO={tx1}")
    print(f"    STELLAR_TX_WALLET={tx2}")


def mostrar():
    e = B.estado()
    linea("═")
    print("  BACKEND AGENT · Stellar 8004")
    linea("═")
    if not e.disponible:
        print(f"  ✗ {e.motivo}")
        return 1
    w, i, p = e.wallet, e.identidad, e.ultimo_pago
    campo("red", config.red())
    if w:
        campo("wallet", w.direccion)
        campo("saldo", f"{w.saldo} XLM" if w.existe else "la cuenta no existe (sin fondear)")
    linea()
    if not i:
        print("  sin identidad: el agente todavia no esta registrado en el 8004")
        print("  → --registrar")
    else:
        campo("agent id", f"#{i.agent_id}")
        campo("identity registry", i.registro)
        campo("wallet EN LA CADENA", i.wallet_en_cadena or "—")
        campo("tx de registro", i.tx_registro or "—", corto=True)
        campo("tx de wallet", i.tx_wallet or "—", corto=True)
        doc = metadata.de_uri(i.uri)
        campo("metadata", f"{doc['name']} · {', '.join(doc['capabilities'])}" if doc else "—",
              corto=True)
        linea()
        if i.verificada:
            print("  ✓ VERIFICADO ON-CHAIN")
            print(f"    get_agent_wallet({i.agent_id}) devuelve la misma wallet que usa Mirag.")
            print("    No es lo que Mirag dice de si mismo: es lo que responde el contrato.")
        else:
            print("  ✗ SIN VERIFICAR")
            print(f"    {i.motivo}")
    if p:
        linea()
        campo("ultimo pago", f"+{p.cantidad} {p.activo} de {p.de[:10]}…")
        campo("tx", p.hash_tx, corto=True)
    linea()
    for k, v in e.enlaces.items():
        campo(k, v, corto=False)
    linea("═")
    print(f"  capacidad: RECIBIR · pagos salientes: NO IMPLEMENTADO · mainnet: NO ALCANZABLE")
    return 0 if (i and i.verificada) else 1


if __name__ == "__main__":
    if "--abi" in sys.argv:
        mostrar_abi()
    elif "--crear" in sys.argv:
        crear()
    elif "--fondear" in sys.argv:
        fondear()
    elif "--registrar" in sys.argv:
        registrar()
    else:
        sys.exit(mostrar())
