"""La capa Stellar: el candado, la frontera, los secretos y la honestidad del claim.

Todo lo de aquí corre con el intérprete del sistema, **sin `stellar-sdk` instalado y sin
red**. Eso no es una limitación del test: es exactamente la propiedad que se comprueba.
Si algún día esta suite necesitara el venv, la capa habría dejado de estar aislada.

    python3 tests/test_blockchain.py
"""

import sys as _sys
from pathlib import Path as _Path
_RAIZ_REPO = _Path(__file__).resolve().parent.parent
for _d in (_RAIZ_REPO, _RAIZ_REPO / "experimental", _RAIZ_REPO / "benchmarks"):
    _sys.path.insert(0, str(_d))

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import blockchain as B
from blockchain import config as C
from blockchain import dobles, metadata, modelos

RAIZ = _RAIZ_REPO
CAPA = RAIZ / "blockchain"
casos = []


def probar(nombre, fn):
    anterior = os.environ.get("MIRAG_BLOCKCHAIN")
    try:
        fn()
        casos.append((True, nombre, ""))
    except AssertionError as e:
        casos.append((False, nombre, str(e) or "assert"))
    except Exception as e:
        casos.append((False, nombre, f"{type(e).__name__}: {e}"))
    finally:
        os.environ.pop("MIRAG_BLOCKCHAIN", None)
        if anterior is not None:
            os.environ["MIRAG_BLOCKCHAIN"] = anterior


def _py_de_la_capa():
    archivos = sorted(CAPA.rglob("*.py"))
    archivos = [p for p in archivos if ".venv" not in p.parts]
    assert len(archivos) >= 8, f"el escaneo no ve la capa: {len(archivos)} archivos en {CAPA}"
    return archivos


# ══ 1 · el candado ═══════════════════════════════════════════════════════════

def por_defecto_la_capa_esta_apagada():
    """Igual que MIRAG_OFFLINE: no confiamos en acordarnos, lo impedimos."""
    os.environ.pop("MIRAG_BLOCKCHAIN", None)
    assert C.red() == C.APAGADA
    assert not C.disponible()
    assert "off" in C.impedimento()


def mainnet_no_es_alcanzable():
    """Lo mas importante de este archivo: no hay forma de llegar a mainnet por accidente."""
    assert set(C.REDES) == {"testnet"}, f"hay mas redes de las que deberia: {set(C.REDES)}"
    for intento in ("mainnet", "public", "pubnet", "MAINNET", "prod"):
        os.environ["MIRAG_BLOCKCHAIN"] = intento
        try:
            C.impedimento()
        except C.RedDesconocida:
            continue
        raise AssertionError(f"MIRAG_BLOCKCHAIN={intento} no lanzo: cayo a algun defecto")


def una_red_desconocida_lanza_en_vez_de_caer_a_un_defecto():
    os.environ["MIRAG_BLOCKCHAIN"] = "loquesea"
    try:
        C.ajustes()
    except C.RedDesconocida:
        return
    raise AssertionError("ajustes() devolvio algo con una red que no existe")


def la_fachada_no_lanza_nunca():
    """El servidor no puede caerse porque la capa tenga un mal dia."""
    for valor in (None, "off", "testnet", "mainnet", "basura", ""):
        os.environ.pop("MIRAG_BLOCKCHAIN", None)
        if valor is not None:
            os.environ["MIRAG_BLOCKCHAIN"] = valor
        e = B.estado()
        assert isinstance(e, modelos.Estado), f"{valor!r} devolvio {type(e)}"
        if not e.disponible:
            assert e.motivo, f"{valor!r}: apagada y sin decir por que"


def ningun_dato_real_se_simula_solo():
    """Un doble que se enciende solo seria la UI mintiendo."""
    os.environ.pop("MIRAG_BLOCKCHAIN", None)
    e = B.estado()
    assert not e.disponible and e.identidad is None and e.wallet is None


# ══ 2 · la frontera ══════════════════════════════════════════════════════════

def importar_la_capa_no_importa_el_sdk():
    """La propiedad que hace que las 21 suites del core no necesiten el venv."""
    r = subprocess.run([sys.executable, "-c",
                        "import sys, blockchain; print('stellar_sdk' in sys.modules)"],
                       cwd=RAIZ, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
    assert r.stdout.strip() == "False", f"importar blockchain cargo el SDK: {r.stdout!r}"


def el_servidor_arranca_sin_el_sdk():
    """Con el interprete del sistema, que no tiene stellar-sdk instalado."""
    r = subprocess.run([sys.executable, "-c", "import server; print(server.Handler.RUTAS)"],
                       cwd=RAIZ, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
    assert "/index.html" in r.stdout


def solo_client_abre_un_socket():
    """La frase que el docstring de client.py afirma, comprobada.

    La regla es sobre el SOCKET, no sobre el paquete: `wallet/claves.py` importa `Keypair`
    (criptografia pura, no abre nada) y esa excepcion esta declarada aqui.
    """
    RED = ("Server", "SorobanServer", "ContractClient", "urlopen", "requests", "httpx")
    PERMITIDO = {"stellar/client.py"}
    malos = []
    for archivo in _py_de_la_capa():
        rel = archivo.relative_to(CAPA).as_posix()
        if rel in PERMITIDO:
            continue
        texto = archivo.read_text()
        for nombre in RED:
            if re.search(rf"\b{nombre}\b", texto):
                malos.append(f"{rel} nombra {nombre}")
    assert not malos, "hay red fuera de client.py:\n  " + "\n  ".join(malos)


def el_sdk_solo_entra_donde_esta_declarado():
    SDK_PERMITIDO = {"stellar/client.py", "wallet/claves.py"}
    malos = []
    for archivo in _py_de_la_capa():
        rel = archivo.relative_to(CAPA).as_posix()
        if rel in SDK_PERMITIDO:
            continue
        for nodo in ast.walk(ast.parse(archivo.read_text())):
            mods = ([a.name for a in nodo.names] if isinstance(nodo, ast.Import)
                    else [nodo.module] if isinstance(nodo, ast.ImportFrom) and nodo.module
                    else [])
            if any((m or "").split(".")[0] == "stellar_sdk" for m in mods):
                malos.append(rel)
    assert not malos, f"importan stellar_sdk sin estar declarados: {sorted(set(malos))}"


def toda_la_red_pasa_por_el_estrangulamiento():
    """Cada funcion de red de client.py tiene que llamar a `_pedir`."""
    fuente = ast.parse((CAPA / "stellar" / "client.py").read_text())
    publicas = [n for n in fuente.body
                if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
                and n.name not in ("horizon", "soroban", "passphrase", "saldo_xlm")]
    assert len(publicas) >= 4, f"solo {len(publicas)} funciones de red que comprobar"
    for fn in publicas:
        llamadas = {n.func.id for n in ast.walk(fn)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert "_pedir" in llamadas, f"client.{fn.name}() sale a la red sin pasar por _pedir"


# ══ 3 · los secretos ═════════════════════════════════════════════════════════

def la_wallet_no_expone_el_secreto():
    """Por AST y no importando: `wallet.servicio` arrastra el cliente, y este archivo
    corre a proposito en un interprete SIN el SDK. Un test que solo pudiera comprobarlo
    con el venv puesto no comprobaria nada en la suite normal."""
    fuente = ast.parse((CAPA / "wallet" / "servicio.py").read_text())
    definidas = {n.name for n in fuente.body if isinstance(n, ast.FunctionDef)}
    assert definidas, "wallet/servicio.py no define ninguna funcion"
    for prohibido in ("secreto", "secret", "clave_secreta", "private_key", "seed",
                      "pagar", "enviar", "transferir"):
        assert prohibido not in definidas, f"wallet.servicio expone {prohibido}()"
    assert {"wallet", "pagos", "fondear_testnet"} <= definidas, definidas


def solo_un_archivo_devuelve_un_secreto():
    """`claves.generar()` es la unica funcion del repo que devuelve una clave privada."""
    culpables = []
    for archivo in _py_de_la_capa():
        rel = archivo.relative_to(CAPA).as_posix()
        if rel == "wallet/claves.py":
            continue
        if re.search(r"\.secret\b|Keypair\.random", archivo.read_text()):
            culpables.append(rel)
    assert not culpables, f"devuelven o generan secretos fuera de claves.py: {culpables}"


def ningun_modulo_de_produccion_lee_la_clave():
    """La invariante no es "no la nombra" sino "no la LEE".

    `empaquetado.py` tiene que nombrarla: es el que la caza antes de meter un ZIP en manos
    del usuario. Nombrarla para detectarla es lo contrario de usarla. Lo que ningun modulo
    de produccion puede hacer es sacarla del entorno, que es como acabaria en una traza,
    en un log o en el contexto del modelo.
    """
    fuentes = sorted(RAIZ.glob("*.py"))
    assert len(fuentes) >= 25, f"el escaneo no ve produccion: {len(fuentes)} archivos"
    CAZADOR = {"empaquetado.py"}          # declarado: la nombra para detectarla
    malos = []
    for archivo in fuentes:
        texto = archivo.read_text()
        if "STELLAR_SECRET_KEY" not in texto:
            continue
        if archivo.name not in CAZADOR:
            malos.append(f"{archivo.name} la nombra sin estar declarado")
            continue
        for nodo in ast.walk(ast.parse(texto)):
            if isinstance(nodo, ast.Constant) and nodo.value == "STELLAR_SECRET_KEY":
                malos.append(f"{archivo.name} la usa como cadena suelta, no en la regex")
    assert not malos, f"la clave se maneja en produccion: {malos}"
    assert "STELLAR_SECRET_KEY" in (RAIZ / "empaquetado.py").read_text(), \
        "el cazador dejo de conocer la clave: un ZIP con una semilla pasaria"


def lo_que_sale_por_http_no_puede_llevar_una_semilla():
    """El ultimo cortafuegos: `para_la_pagina()` LANZA si detecta algo con esa forma."""
    e = dobles.estado()
    envenenado = e._replace(identidad=e.identidad._replace(uri="S" + "A" * 55))
    try:
        envenenado.para_la_pagina()
    except RuntimeError as err:
        assert "secreta" in str(err)
        return
    raise AssertionError("una semilla salio por HTTP sin que nadie se quejara")


def el_estado_normal_si_sale():
    d = dobles.estado().para_la_pagina()
    assert d["disponible"] and d["identidad"]["verificada"]
    assert not modelos.hay_semilla(json.dumps(d))


def el_empaquetado_caza_una_semilla_de_stellar():
    """Una clave de Stellar en un proyecto entregado tiene que bloquear la descarga."""
    import empaquetado
    fabricada = b"SECRET = 'S" + b"A" * 55 + b"'"
    assert empaquetado.SECRETOS.search(fabricada), \
        "la regex de secretos no reconoce una semilla de Stellar"


# ══ 4 · los modelos y la metadata ════════════════════════════════════════════

def las_direcciones_se_distinguen_por_su_forma():
    assert modelos.es_publica("G" + "A" * 55)
    assert not modelos.es_publica("S" + "A" * 55)
    assert not modelos.es_publica("G" + "A" * 54)
    assert modelos.es_contrato("C" + "A" * 55)
    assert modelos.hay_semilla("algo S" + "B" * 55 + " en medio")


def la_metadata_es_la_forma_del_estandar():
    doc = metadata.documento(wallet="G" + "A" * 55)
    assert doc["type"] == metadata.TIPO
    assert doc["type"].endswith("#registration-v1")
    assert doc["agentWallet"] == "G" + "A" * 55
    assert doc["role"] == "backend" and doc["capabilities"]


def la_metadata_va_y_vuelve():
    u = metadata.uri_del_backend("G" + "A" * 55)
    assert u.startswith("data:application/json;base64,")
    assert metadata.de_uri(u) == metadata.documento(wallet="G" + "A" * 55)
    assert metadata.de_uri("https://ejemplo.com/a.json") is None
    assert metadata.de_uri("data:application/json;base64,!!!") is None


def una_metadata_que_no_cabe_se_rechaza_aqui_y_no_on_chain():
    enorme = dict(metadata.BACKEND, description="x" * metadata.MAXIMO_URI)
    try:
        metadata.a_uri(enorme)
    except ValueError:
        return
    raise AssertionError("una metadata que no cabe en la cadena paso el control local")


# ══ 5 · esta fase no gasta ═══════════════════════════════════════════════════

def no_hay_ninguna_funcion_de_pago_saliente():
    """La capacidad declarada es RECIBIR. Si esto cambia, que se vea."""
    prohibidas = ("def pagar", "def enviar", "def transferir", "def pay", "def send")
    malos = []
    for archivo in _py_de_la_capa():
        texto = archivo.read_text()
        for p in prohibidas:
            if p in texto:
                malos.append(f"{archivo.relative_to(CAPA)} tiene {p}()")
    assert not malos, f"aparecio gasto saliente: {malos}"


def la_documentacion_dice_lo_que_el_codigo_hace():
    doc = (RAIZ / "docs" / "blockchain.md").read_text()
    for frase in ("RECIBIR", "NO IMPLEMENTADO", "MIRAG_BLOCKCHAIN=off"):
        assert frase in doc, f"docs/blockchain.md no dice {frase!r}"
    assert C.REDES[C.TESTNET]["identity_registry"] in doc, \
        "el contrato que usa el codigo no es el que documenta docs/blockchain.md"


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
