"""El arnés de pruebas lo escribe Mirag, no el modelo. Por eso es evidencia.

EL PROBLEMA QUE CIERRA

    Si los tests de integración los escribe el mismo modelo que escribió el código, el
    modelo puede aprobarse a sí mismo: basta con que su "test de CRUD" llame a funciones
    en vez de hacer HTTP, o que imprima `TEST:crud:PASS` al importarse. Los marcadores
    saldrían verdes y nada se habría ejercitado.

    Aquí Mirag inyecta sus propias sondas y **los identificadores llevan un nonce
    generado en Python en cada ejecución**. El modelo no puede adivinar
    `TEST:crud_post_a3f19c2b:PASS`, así que no puede fabricarlo. Lo único que controla es
    si su servidor responde de verdad.

LAS TRES SONDAS

    deps   qué dependencias externas existen EN ESTA máquina. Observado, no supuesto.
    tests  corre los tests del proyecto y emite un marcador por test, con su id.
    crud   arranca el servidor de verdad y le pega por HTTP: POST, GET, GET id, PUT,
           comprobando que el PUT PERSISTE, DELETE, y GET id -> 404.

    Las tres se escriben solo en el directorio temporal de ejecución. Nunca entran en el
    artefacto ni en el ZIP.

EL CONTRATO QUE EL PROYECTO TIENE QUE CUMPLIR

    El entrypoint expone `crear_servidor(puerto=0, bd=":memory:")` que DEVUELVE un
    servidor sin arrancarlo. Nada se ejecuta al importar. Si no se cumple, la sonda lo
    dice con un marcador en FAIL — nunca con un silencio.
"""

import secrets

TIEMPO_SONDA = 20        # < TIMEOUT de skills: hay que morir ANTES y conservar la salida
OPERACIONES = ("crear", "listar", "obtener", "actualizar", "persiste", "borrar", "borrado")


def nonce():
    return secrets.token_hex(4)


def ids_crud(marca):
    return tuple(f"crud_{op}_{marca}" for op in OPERACIONES)


def deps(raices):
    return {"_sonda_deps.py": f'''\
"""Que dependencias externas existen aqui. Lo escribe Mirag."""
import importlib.util as u
for modulo in {sorted(raices)!r}:
    print(f"DEP:{{modulo}}:" + ("INSTALADA" if u.find_spec(modulo) else "AUSENTE"), flush=True)
print("DEP:_sonda:OK", flush=True)
'''}


def tests(comando_modulo, minimo=1):
    """Runner de unittest que emite un marcador por test. Le quita al modelo la
    responsabilidad de imprimirlos, que es la causa numero uno de `sin_evidencia`."""
    return {"_sonda_tests.py": f'''\
"""Corre los tests del proyecto y emite un marcador por cada uno. Lo escribe Mirag."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Marcadores(unittest.TextTestResult):
    def _id(self, t):
        return str(t).split()[0].replace(".", "_")[:60] or "sin_nombre"
    def addSuccess(self, t):
        super().addSuccess(t); print(f"TEST:{{self._id(t)}}:PASS", flush=True)
    def addFailure(self, t, e):
        super().addFailure(t, e); print(f"TEST:{{self._id(t)}}:FAIL", flush=True)
    def addError(self, t, e):
        super().addError(t, e); print(f"TEST:{{self._id(t)}}:FAIL", flush=True)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover("{comando_modulo}", top_level_dir=".")
    r = unittest.TextTestRunner(resultclass=Marcadores, verbosity=0).run(suite)
    corridos = r.testsRun
    if corridos < {minimo}:
        # Un import que falla dentro de un try silencioso deja 0 tests y exit 0.
        # Eso NO es aprobar: es que nadie sabe que se probo.
        print(f"TEST:cobertura_de_tests:FAIL", flush=True)
        print(f"corrieron {{corridos}} tests y se esperaban al menos {minimo}", flush=True)
        sys.exit(1)
    sys.exit(1 if (r.failures or r.errors) else 0)
'''}


def crud(modulo_entrypoint, marca, recurso="/libros", ejemplo=None, cambio=None):
    """La sonda de integración: HTTP real contra el servidor del proyecto."""
    ejemplo = ejemplo or {"titulo": "Rayuela", "autor": "Cortazar"}
    cambio = cambio or {"titulo": "Rayuela (2a ed)", "autor": "Cortazar"}
    campo = next(iter(cambio))
    ids = ids_crud(marca)
    return {"_sonda_crud.py": f'''\
"""CRUD real por HTTP contra el servidor del proyecto. Lo escribe Mirag, no el modelo.

Los identificadores llevan un nonce de esta ejecucion: el modelo no puede fabricarlos.
"""
import json, os, signal, sys, threading, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

IDS = {list(ids)!r}
def marca(i, ok):
    print(f"TEST:{{IDS[i]}}:" + ("PASS" if ok else "FAIL"), flush=True)
def todos_fail(desde=0):
    for i in range(desde, len(IDS)):
        marca(i, False)

def cortar(*_):
    print("la sonda se corto sola antes del limite del ejecutor", flush=True)
    todos_fail()
    os._exit(1)
signal.signal(signal.SIGALRM, cortar)
signal.alarm({TIEMPO_SONDA})

def pedir(base, metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(base + ruta, data=datos, method=metodo,
                                 headers={{"Content-Type": "application/json"}})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            crudo = r.read()
            return r.status, (json.loads(crudo) if crudo else {{}})
    except urllib.error.HTTPError as e:
        crudo = e.read()
        return e.code, (json.loads(crudo) if crudo else {{}})
    except Exception as e:
        print(f"la peticion {{metodo}} {{ruta}} reviento: {{type(e).__name__}}: {{e}}", flush=True)
        return 0, {{}}

srv = None
try:
    from {modulo_entrypoint} import crear_servidor
except Exception as e:
    print(f"no se pudo importar crear_servidor de {modulo_entrypoint}: "
          f"{{type(e).__name__}}: {{e}}", flush=True)
    todos_fail(); sys.exit(1)

try:
    srv = crear_servidor(puerto=0)
    base = f"http://127.0.0.1:{{srv.server_address[1]}}"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
except Exception as e:
    print(f"crear_servidor no arranco: {{type(e).__name__}}: {{e}}", flush=True)
    todos_fail(); sys.exit(1)

try:
    codigo, creado = pedir(base, "POST", "{recurso}", {ejemplo!r})
    ident = creado.get("id") if isinstance(creado, dict) else None
    marca(0, codigo in (200, 201) and ident is not None)
    if ident is None:
        todos_fail(1); sys.exit(1)

    codigo, lista = pedir(base, "GET", "{recurso}")
    marca(1, codigo == 200 and isinstance(lista, list)
          and any(str(x.get("id")) == str(ident) for x in lista))

    codigo, uno = pedir(base, "GET", f"{recurso}/{{ident}}")
    marca(2, codigo == 200 and str(uno.get("id")) == str(ident))

    codigo, _ = pedir(base, "PUT", f"{recurso}/{{ident}}", {cambio!r})
    marca(3, codigo in (200, 204))

    # que el PUT PERSISTA, no que exista un handler de PUT
    codigo, tras = pedir(base, "GET", f"{recurso}/{{ident}}")
    marca(4, codigo == 200 and tras.get({campo!r}) == {cambio[campo]!r})

    codigo, _ = pedir(base, "DELETE", f"{recurso}/{{ident}}")
    marca(5, codigo in (200, 202, 204))

    codigo, _ = pedir(base, "GET", f"{recurso}/{{ident}}")
    marca(6, codigo == 404)
finally:
    signal.alarm(0)
    if srv is not None:
        try:
            srv.shutdown(); srv.server_close()
        except Exception:
            pass
'''}
