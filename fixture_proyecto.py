"""El proyecto de la demo canónica, en texto. Stdlib puro, y se ejecuta de verdad.

No es una captura de pantalla: `dobles.PROYECTO_LIBROS` lo entrega por grupos como lo
haría el modelo, la verificación lo ejecuta, y la sonda de CRUD le pega por HTTP real.
Si este código dejara de funcionar, la demo canónica se pondría roja — que es justo lo
que tiene que pasar.
"""

BD = '''\
"""Conexion y esquema. Lo unico que sabe de sqlite3."""

import sqlite3
import threading

ESCRITURA = threading.Lock()


def conectar(ruta=":memory:"):
    """Una conexion compartida entre hilos: el servidor atiende cada peticion en uno."""
    con = sqlite3.connect(ruta, check_same_thread=False)
    con.row_factory = sqlite3.Row
    crear_esquema(con)
    return con


def crear_esquema(con):
    con.execute("""CREATE TABLE IF NOT EXISTS libros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autor TEXT NOT NULL DEFAULT '',
        anio INTEGER)""")
    con.commit()
    return con
'''

MODELOS = '''\
"""La forma de un libro y sus reglas. Sin sqlite3 y sin HTTP."""

CAMPOS = ("titulo", "autor", "anio")


def validar(datos):
    """[] si el libro es valido, o la lista de problemas. La validacion va aqui, no
    dispersa por los handlers: asi un titulo vacio se rechaza igual venga de donde venga."""
    problemas = []
    if not isinstance(datos, dict):
        return ["el cuerpo no es un objeto"]
    titulo = (datos.get("titulo") or "").strip()
    if not titulo:
        problemas.append("titulo es obligatorio")
    if len(titulo) > 300:
        problemas.append("titulo demasiado largo")
    anio = datos.get("anio")
    if anio is not None and not isinstance(anio, int):
        problemas.append("anio tiene que ser un numero entero")
    return problemas


def como_dict(fila):
    return {"id": fila["id"], "titulo": fila["titulo"],
            "autor": fila["autor"], "anio": fila["anio"]}
'''

REPOSITORIO = '''\
"""Acceso a datos. Aqui viven las sentencias SQL y nada mas."""

from app.core.bd import ESCRITURA
from app.libros.modelos import como_dict


def crear(con, datos):
    with ESCRITURA:
        cur = con.execute("INSERT INTO libros (titulo, autor, anio) VALUES (?, ?, ?)",
                          (datos["titulo"], datos.get("autor", ""), datos.get("anio")))
        con.commit()
    return obtener(con, cur.lastrowid)


def listar(con):
    return [como_dict(f) for f in con.execute(
        "SELECT id, titulo, autor, anio FROM libros ORDER BY id").fetchall()]


def obtener(con, libro_id):
    fila = con.execute("SELECT id, titulo, autor, anio FROM libros WHERE id = ?",
                       (libro_id,)).fetchone()
    return como_dict(fila) if fila else None


def actualizar(con, libro_id, datos):
    with ESCRITURA:
        cur = con.execute("UPDATE libros SET titulo = ?, autor = ?, anio = ? WHERE id = ?",
                          (datos["titulo"], datos.get("autor", ""), datos.get("anio"),
                           libro_id))
        con.commit()
    return obtener(con, libro_id) if cur.rowcount else None


def borrar(con, libro_id):
    with ESCRITURA:
        cur = con.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
        con.commit()
    return cur.rowcount > 0
'''

SERVICIO = '''\
"""Las reglas de negocio. Traduce entre "lo que se pide" y "lo que hay en la base".

Devuelve `(codigo_http, cuerpo)` para que el router no tenga que decidir nada.
"""

from app.libros import repositorio
from app.libros.modelos import validar


def alta(con, datos):
    problemas = validar(datos)
    if problemas:
        return 400, {"error": "datos invalidos", "detalles": problemas}
    return 201, repositorio.crear(con, datos)


def listado(con):
    return 200, repositorio.listar(con)


def detalle(con, libro_id):
    libro = repositorio.obtener(con, libro_id)
    return (200, libro) if libro else (404, {"error": "ese libro no existe"})


def edicion(con, libro_id, datos):
    problemas = validar(datos)
    if problemas:
        return 400, {"error": "datos invalidos", "detalles": problemas}
    libro = repositorio.actualizar(con, libro_id, datos)
    return (200, libro) if libro else (404, {"error": "ese libro no existe"})


def baja(con, libro_id):
    if repositorio.borrar(con, libro_id):
        return 204, None
    return 404, {"error": "ese libro no existe"}
'''

ROUTER = '''\
"""Traduce HTTP a llamadas al servicio. No sabe SQL y no decide codigos de estado."""

import re

from app.libros import servicio

COLECCION = re.compile(r"\\A/libros/?\\Z")
ELEMENTO = re.compile(r"\\A/libros/(\\d+)/?\\Z")


def resolver(metodo, ruta):
    """(funcion, id) o (None, None) si esa combinacion no existe."""
    if COLECCION.match(ruta):
        if metodo == "GET":
            return servicio.listado, None
        if metodo == "POST":
            return servicio.alta, None
        return None, None
    hallado = ELEMENTO.match(ruta)
    if not hallado:
        return None, None
    libro_id = int(hallado.group(1))
    return {"GET": servicio.detalle, "PUT": servicio.edicion,
            "PATCH": servicio.edicion, "DELETE": servicio.baja}.get(metodo), libro_id


def despachar(con, metodo, ruta, cuerpo):
    funcion, libro_id = resolver(metodo, ruta)
    if funcion is None:
        return 404, {"error": "esa ruta no existe"}
    if libro_id is None:
        return funcion(con) if metodo == "GET" else funcion(con, cuerpo)
    if metodo in ("PUT", "PATCH"):
        return funcion(con, libro_id, cuerpo)
    return funcion(con, libro_id)
'''

MAIN = '''\
"""El servidor. `crear_servidor` lo DEVUELVE sin arrancarlo: quien lo arranca decide."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.core.bd import conectar
from app.libros.router import despachar


class Handler(BaseHTTPRequestHandler):
    conexion = None

    def log_message(self, *_):
        pass                      # sin ruido en la salida: los tests leen marcadores

    def _responder(self, codigo, cuerpo):
        datos = b"" if cuerpo is None else json.dumps(cuerpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        if datos:
            self.wfile.write(datos)

    def _cuerpo(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if not largo:
            return {}
        try:
            return json.loads(self.rfile.read(largo))
        except ValueError:
            return None

    def _atender(self, metodo):
        cuerpo = self._cuerpo() if metodo in ("POST", "PUT", "PATCH") else {}
        if cuerpo is None:
            return self._responder(400, {"error": "el cuerpo no es JSON valido"})
        codigo, respuesta = despachar(self.conexion, metodo, self.path, cuerpo)
        self._responder(codigo, respuesta)

    def do_GET(self):
        self._atender("GET")

    def do_POST(self):
        self._atender("POST")

    def do_PUT(self):
        self._atender("PUT")

    def do_PATCH(self):
        self._atender("PATCH")

    def do_DELETE(self):
        self._atender("DELETE")


def crear_servidor(puerto=0, bd=":memory:"):
    """Devuelve el servidor listo. Puerto 0 = el sistema elige uno libre."""
    Handler.conexion = conectar(bd)
    return ThreadingHTTPServer(("127.0.0.1", puerto), Handler)


if __name__ == "__main__":
    servidor = crear_servidor(8080)
    print(f"escuchando en http://127.0.0.1:{servidor.server_address[1]}")
    servidor.serve_forever()
'''

TESTS = '''\
"""CRUD completo contra el servidor de verdad, por HTTP. Solo unittest y urllib."""

import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import crear_servidor


class ApiDeLibros(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.servidor = crear_servidor()
        cls.base = f"http://127.0.0.1:{cls.servidor.server_address[1]}"
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def pedir(self, metodo, ruta, cuerpo=None):
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
        peticion = urllib.request.Request(
            self.base + ruta, data=datos, method=metodo,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(peticion, timeout=5) as respuesta:
                crudo = respuesta.read()
                return respuesta.status, (json.loads(crudo) if crudo else None)
        except urllib.error.HTTPError as error:
            crudo = error.read()
            return error.code, (json.loads(crudo) if crudo else None)

    def alta(self, titulo="Rayuela", autor="Cortazar", anio=1963):
        codigo, libro = self.pedir("POST", "/libros",
                                   {"titulo": titulo, "autor": autor, "anio": anio})
        self.assertEqual(codigo, 201)
        return libro

    def test_crea_y_devuelve_el_libro_con_id(self):
        libro = self.alta()
        self.assertIsInstance(libro["id"], int)
        self.assertEqual(libro["titulo"], "Rayuela")

    def test_lista_incluye_lo_creado(self):
        libro = self.alta("Pedro Paramo", "Rulfo", 1955)
        codigo, lista = self.pedir("GET", "/libros")
        self.assertEqual(codigo, 200)
        self.assertIn(libro["id"], [x["id"] for x in lista])

    def test_obtiene_uno_por_id(self):
        libro = self.alta("Ficciones", "Borges", 1944)
        codigo, uno = self.pedir("GET", f"/libros/{libro['id']}")
        self.assertEqual(codigo, 200)
        self.assertEqual(uno["autor"], "Borges")

    def test_actualizar_persiste_de_verdad(self):
        libro = self.alta("Primera", "Alguien", 2000)
        self.pedir("PUT", f"/libros/{libro['id']}",
                   {"titulo": "Corregida", "autor": "Alguien", "anio": 2001})
        codigo, tras = self.pedir("GET", f"/libros/{libro['id']}")
        self.assertEqual(codigo, 200)
        self.assertEqual(tras["titulo"], "Corregida")
        self.assertEqual(tras["anio"], 2001)

    def test_borrar_lo_quita_de_verdad(self):
        libro = self.alta("Efimero", "Nadie", 1999)
        codigo, _ = self.pedir("DELETE", f"/libros/{libro['id']}")
        self.assertIn(codigo, (200, 204))
        codigo, _ = self.pedir("GET", f"/libros/{libro['id']}")
        self.assertEqual(codigo, 404)

    def test_rechaza_un_libro_sin_titulo(self):
        codigo, error = self.pedir("POST", "/libros", {"autor": "Sin titulo"})
        self.assertEqual(codigo, 400)
        self.assertIn("titulo es obligatorio", error["detalles"])

    def test_rechaza_un_anio_que_no_es_numero(self):
        codigo, _ = self.pedir("POST", "/libros", {"titulo": "X", "anio": "mil"})
        self.assertEqual(codigo, 400)

    def test_un_libro_inexistente_da_404(self):
        codigo, _ = self.pedir("GET", "/libros/999999")
        self.assertEqual(codigo, 404)

    def test_una_ruta_desconocida_da_404(self):
        codigo, _ = self.pedir("GET", "/revistas")
        self.assertEqual(codigo, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

README = '''\
# libros-api

API REST de libros con CRUD completo. **Sin dependencias**: solo biblioteca estandar de
Python (`http.server`, `sqlite3`, `unittest`).

## Arquitectura

Por dominios, con las capas separadas:

```
app/
  core/bd.py            conexion y esquema; lo unico que sabe de sqlite3
  libros/modelos.py     la forma de un libro y sus reglas
  libros/repositorio.py el SQL, y nada mas
  libros/servicio.py    las reglas de negocio; devuelve (codigo, cuerpo)
  libros/router.py      traduce HTTP a llamadas al servicio
  main.py               el servidor
tests/test_libros.py    CRUD completo por HTTP real
```

Cada capa solo conoce a la de debajo: el router no sabe SQL y el repositorio no sabe HTTP.

## Arrancar

```bash
python3 -m app.main
```

Escucha en `http://127.0.0.1:8080`. Con `bd=":memory:"` (por defecto) los datos se pierden
al parar; pasa una ruta a `crear_servidor` para guardarlos en un archivo.

## Los tests

```bash
python3 -m unittest discover -s tests -t .
```

Levantan el servidor en un puerto libre y le piden por HTTP de verdad: no hay mocks.

## Endpoints

| metodo | ruta | que hace |
|---|---|---|
| `POST` | `/libros` | crea uno. 400 si falta el titulo |
| `GET` | `/libros` | lista todos |
| `GET` | `/libros/{id}` | uno. 404 si no existe |
| `PUT` | `/libros/{id}` | lo reemplaza. 404 si no existe |
| `DELETE` | `/libros/{id}` | lo borra. 204, o 404 si no existe |

## Ejemplo

```bash
curl -X POST http://127.0.0.1:8080/libros \\
  -H 'Content-Type: application/json' \\
  -d '{"titulo":"Rayuela","autor":"Cortazar","anio":1963}'
```
'''

REQUIREMENTS = '''\
# Sin dependencias externas: este proyecto solo usa la biblioteca estandar.
# Se deja el archivo para que anadir una sea obvio cuando haga falta.
'''

ENV = '''\
PUERTO=8080
BD=libros.db
'''

ARCHIVOS = {
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/core/bd.py": BD,
    "app/libros/__init__.py": "",
    "app/libros/modelos.py": MODELOS,
    "app/libros/repositorio.py": REPOSITORIO,
    "app/libros/servicio.py": SERVICIO,
    "app/libros/router.py": ROUTER,
    "app/main.py": MAIN,
    "tests/__init__.py": "",
    "tests/test_libros.py": TESTS,
    "README.md": README,
    "requirements.txt": REQUIREMENTS,
    ".env.example": ENV,
}

GRUPOS = {
    "nucleo": ["app/__init__.py", "app/core/__init__.py", "app/core/bd.py", "app/main.py"],
    "dominio": ["app/libros/__init__.py", "app/libros/modelos.py",
                "app/libros/repositorio.py", "app/libros/servicio.py",
                "app/libros/router.py"],
    "tests": ["tests/__init__.py", "tests/test_libros.py"],
    "docs": ["README.md", "requirements.txt", ".env.example"],
}

PLANO = [
    {"ruta": "app/__init__.py", "tipo": "codigo", "proposito": "paquete raiz",
     "exporta": [], "depende_de": [], "grupo": "nucleo"},
    {"ruta": "app/core/__init__.py", "tipo": "codigo", "proposito": "paquete core",
     "exporta": [], "depende_de": [], "grupo": "nucleo"},
    {"ruta": "app/core/bd.py", "tipo": "codigo", "proposito": "conexion y esquema",
     "exporta": ["conectar", "crear_esquema", "ESCRITURA"], "depende_de": [], "grupo": "nucleo"},
    {"ruta": "app/main.py", "tipo": "entrypoint", "proposito": "el servidor HTTP",
     "exporta": ["crear_servidor", "Handler"],
     "depende_de": ["app/core/bd.py", "app/libros/router.py"], "grupo": "nucleo"},
    {"ruta": "app/libros/__init__.py", "tipo": "codigo", "proposito": "paquete del dominio",
     "exporta": [], "depende_de": [], "grupo": "dominio"},
    {"ruta": "app/libros/modelos.py", "tipo": "codigo", "proposito": "forma y validacion",
     "exporta": ["CAMPOS", "validar", "como_dict"], "depende_de": [], "grupo": "dominio"},
    {"ruta": "app/libros/repositorio.py", "tipo": "codigo", "proposito": "el SQL",
     "exporta": ["crear", "listar", "obtener", "actualizar", "borrar"],
     "depende_de": ["app/core/bd.py", "app/libros/modelos.py"], "grupo": "dominio"},
    {"ruta": "app/libros/servicio.py", "tipo": "codigo", "proposito": "reglas de negocio",
     "exporta": ["alta", "listado", "detalle", "edicion", "baja"],
     "depende_de": ["app/libros/repositorio.py", "app/libros/modelos.py"], "grupo": "dominio"},
    {"ruta": "app/libros/router.py", "tipo": "codigo", "proposito": "HTTP -> servicio",
     "exporta": ["resolver", "despachar"], "depende_de": ["app/libros/servicio.py"],
     "grupo": "dominio"},
    {"ruta": "tests/__init__.py", "tipo": "test", "proposito": "paquete de tests",
     "exporta": [], "depende_de": [], "grupo": "tests"},
    {"ruta": "tests/test_libros.py", "tipo": "test", "proposito": "CRUD por HTTP real",
     "exporta": [], "depende_de": ["app/main.py"], "grupo": "tests"},
    {"ruta": "README.md", "tipo": "doc", "proposito": "como usarlo",
     "exporta": [], "depende_de": [], "grupo": "docs"},
    {"ruta": "requirements.txt", "tipo": "config", "proposito": "dependencias",
     "exporta": [], "depende_de": [], "grupo": "docs"},
    {"ruta": ".env.example", "tipo": "config", "proposito": "variables de entorno",
     "exporta": [], "depende_de": [], "grupo": "docs"},
]

ESPEC = {
    "nombre": "libros-api", "lenguaje": "python", "framework": "stdlib",
    "base_datos": "sqlite", "arquitectura": "por dominios, en capas",
    "entidad": "libro", "recurso": "/libros",
    "campos": ["titulo", "autor", "anio"], "dependencias": [],
    "comando_test": "python3 -m unittest discover -s tests -t .",
    "supuestos": [
        "no se pidio framework, asi que se usa http.server: el proyecto corre sin instalar nada",
        "la base va en memoria por defecto para que los tests no dejen archivos",
    ],
    "archivos": PLANO,
}
