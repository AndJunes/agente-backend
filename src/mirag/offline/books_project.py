'''The project of the canonical demo, as text. Pure stdlib, and it really runs.

It is not a screenshot: the scripted model delivers it group by group as the real model
would, certification runs it, and the CRUD probe hits it over real HTTP. If this code stopped
working, the canonical demo would turn red - which is exactly what has to happen.
'''

DB = '''\
"""Connection and schema. The only module that knows about sqlite3."""

import sqlite3
import threading

WRITE_LOCK = threading.Lock()


def connect(path=":memory:"):
    """One connection shared across threads: the server serves each request in one."""
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    create_schema(connection)
    return connection


def create_schema(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL DEFAULT '',
        year INTEGER)""")
    connection.commit()
    return connection
'''

MODELS = '''\
"""The shape of a book and its rules. Without sqlite3 and without HTTP."""

FIELDS = ("title", "author", "year")


def validate(data):
    """[] if the book is valid, or the list of problems. Validation lives here, not scattered
    across handlers: an empty title is rejected the same way wherever it comes from."""
    problems = []
    if not isinstance(data, dict):
        return ["the body is not an object"]
    title = (data.get("title") or "").strip()
    if not title:
        problems.append("title is required")
    if len(title) > 300:
        problems.append("title is too long")
    year = data.get("year")
    if year is not None and not isinstance(year, int):
        problems.append("year must be an integer")
    return problems


def as_dict(row):
    return {"id": row["id"], "title": row["title"], "author": row["author"], "year": row["year"]}
'''

REPOSITORY = '''\
"""Data access. SQL lives here and nothing else."""

from app.core.db import WRITE_LOCK
from app.books.models import as_dict


def create(connection, data):
    with WRITE_LOCK:
        cursor = connection.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
                                    (data["title"], data.get("author", ""), data.get("year")))
        connection.commit()
    return get(connection, cursor.lastrowid)


def list_all(connection):
    return [as_dict(row) for row in connection.execute(
        "SELECT id, title, author, year FROM books ORDER BY id").fetchall()]


def get(connection, book_id):
    row = connection.execute("SELECT id, title, author, year FROM books WHERE id = ?",
                             (book_id,)).fetchone()
    return as_dict(row) if row else None


def update(connection, book_id, data):
    with WRITE_LOCK:
        cursor = connection.execute("UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?",
                                    (data["title"], data.get("author", ""), data.get("year"), book_id))
        connection.commit()
    return get(connection, book_id) if cursor.rowcount else None


def delete(connection, book_id):
    with WRITE_LOCK:
        cursor = connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
        connection.commit()
    return cursor.rowcount > 0
'''

SERVICE = '''\
"""Business rules. Translates between "what is asked" and "what is in the database".

It returns `(http_status, body)` so the router does not have to decide anything.
"""

from app.books import repository
from app.books.models import validate


def create(connection, data):
    problems = validate(data)
    if problems:
        return 400, {"error": "invalid data", "details": problems}
    return 201, repository.create(connection, data)


def list_books(connection):
    return 200, repository.list_all(connection)


def detail(connection, book_id):
    book = repository.get(connection, book_id)
    return (200, book) if book else (404, {"error": "that book does not exist"})


def edit(connection, book_id, data):
    problems = validate(data)
    if problems:
        return 400, {"error": "invalid data", "details": problems}
    book = repository.update(connection, book_id, data)
    return (200, book) if book else (404, {"error": "that book does not exist"})


def remove(connection, book_id):
    if repository.delete(connection, book_id):
        return 204, None
    return 404, {"error": "that book does not exist"}
'''

ROUTER = '''\
"""Translates HTTP into service calls. It knows no SQL and decides no status codes."""

import re

from app.books import service

COLLECTION = re.compile(r"\\A/books/?\\Z")
ITEM = re.compile(r"\\A/books/(\\d+)/?\\Z")


def resolve(method, path):
    """(function, id) or (None, None) when that combination does not exist."""
    if COLLECTION.match(path):
        if method == "GET":
            return service.list_books, None
        if method == "POST":
            return service.create, None
        return None, None
    found = ITEM.match(path)
    if not found:
        return None, None
    book_id = int(found.group(1))
    return {"GET": service.detail, "PUT": service.edit,
            "PATCH": service.edit, "DELETE": service.remove}.get(method), book_id


def dispatch(connection, method, path, body):
    function, book_id = resolve(method, path)
    if function is None:
        return 404, {"error": "that route does not exist"}
    if book_id is None:
        return function(connection) if method == "GET" else function(connection, body)
    if method in ("PUT", "PATCH"):
        return function(connection, book_id, body)
    return function(connection, book_id)
'''

MAIN = '''\
"""The server. `create_server` RETURNS it without starting it: whoever starts it decides."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.core.db import connect
from app.books.router import dispatch


class Handler(BaseHTTPRequestHandler):
    database = None  # not 'connection': BaseHTTPRequestHandler already uses that name for the socket

    def log_message(self, *_):
        pass  # no noise in the output: the tests read markers

    def _respond(self, status, body):
        data = b"" if body is None else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except ValueError:
            return None

    def _serve(self, method):
        body = self._body() if method in ("POST", "PUT", "PATCH") else {}
        if body is None:
            return self._respond(400, {"error": "the body is not valid JSON"})
        status, answer = dispatch(self.database, method, self.path, body)
        self._respond(status, answer)

    def do_GET(self):
        self._serve("GET")

    def do_POST(self):
        self._serve("POST")

    def do_PUT(self):
        self._serve("PUT")

    def do_PATCH(self):
        self._serve("PATCH")

    def do_DELETE(self):
        self._serve("DELETE")


def create_server(port=0, db=":memory:"):
    """Returns the server ready. Port 0 = the system picks a free one."""
    Handler.database = connect(db)
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    server = create_server(8080)
    print(f"listening on http://127.0.0.1:{server.server_address[1]}")
    server.serve_forever()
'''

TESTS = '''\
"""Full CRUD against the real server, over HTTP. Only unittest and urllib."""

import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import create_server


class BooksApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = create_server()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method,
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                raw = response.read()
                return response.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as error:
            raw = error.read()
            return error.code, (json.loads(raw) if raw else None)

    def create(self, title="Hopscotch", author="Cortazar", year=1963):
        status, book = self.call("POST", "/books", {"title": title, "author": author, "year": year})
        self.assertEqual(status, 201)
        return book

    def test_creates_and_returns_the_book_with_id(self):
        book = self.create()
        self.assertIsInstance(book["id"], int)
        self.assertEqual(book["title"], "Hopscotch")

    def test_list_includes_what_was_created(self):
        book = self.create("Pedro Paramo", "Rulfo", 1955)
        status, listing = self.call("GET", "/books")
        self.assertEqual(status, 200)
        self.assertIn(book["id"], [x["id"] for x in listing])

    def test_gets_one_by_id(self):
        book = self.create("Ficciones", "Borges", 1944)
        status, one = self.call("GET", f"/books/{book['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(one["author"], "Borges")

    def test_update_really_persists(self):
        book = self.create("First", "Someone", 2000)
        self.call("PUT", f"/books/{book['id']}", {"title": "Corrected", "author": "Someone", "year": 2001})
        status, after = self.call("GET", f"/books/{book['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(after["title"], "Corrected")
        self.assertEqual(after["year"], 2001)

    def test_delete_really_removes_it(self):
        book = self.create("Ephemeral", "Nobody", 1999)
        status, _ = self.call("DELETE", f"/books/{book['id']}")
        self.assertIn(status, (200, 204))
        status, _ = self.call("GET", f"/books/{book['id']}")
        self.assertEqual(status, 404)

    def test_rejects_a_book_without_title(self):
        status, error = self.call("POST", "/books", {"author": "No title"})
        self.assertEqual(status, 400)
        self.assertIn("title is required", error["details"])

    def test_rejects_a_year_that_is_not_a_number(self):
        status, _ = self.call("POST", "/books", {"title": "X", "year": "one thousand"})
        self.assertEqual(status, 400)

    def test_a_missing_book_is_404(self):
        status, _ = self.call("GET", "/books/999999")
        self.assertEqual(status, 404)

    def test_an_unknown_route_is_404(self):
        status, _ = self.call("GET", "/magazines")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

README = '''\
# books-api

REST API of books with full CRUD. **No dependencies**: only the Python standard library
(`http.server`, `sqlite3`, `unittest`).

## Architecture

By domain, with separate layers:

```
app/
  core/db.py              connection and schema; the only module that knows sqlite3
  books/models.py         the shape of a book and its rules
  books/repository.py     the SQL, and nothing else
  books/service.py        business rules; returns (status, body)
  books/router.py         translates HTTP into service calls
  main.py                 the server
tests/test_books.py       full CRUD over real HTTP
```

Each layer only knows the one below: the router knows no SQL and the repository knows no HTTP.

## Run

```bash
python3 -m app.main
```

It listens on `http://127.0.0.1:8080`. With `db=":memory:"` (the default) data is lost on
stop; pass a path to `create_server` to keep it in a file.

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

They start the server on a free port and call it over real HTTP: there are no mocks.

## Endpoints

| method | path | what it does |
|---|---|---|
| `POST` | `/books` | creates one. 400 if the title is missing |
| `GET` | `/books` | lists them all |
| `GET` | `/books/{id}` | one. 404 if it does not exist |
| `PUT` | `/books/{id}` | replaces it. 404 if it does not exist |
| `DELETE` | `/books/{id}` | deletes it. 204, or 404 if it does not exist |

## Example

```bash
curl -X POST http://127.0.0.1:8080/books \\
  -H 'Content-Type: application/json' \\
  -d '{"title":"Hopscotch","author":"Cortazar","year":1963}'
```
'''

REQUIREMENTS = '''\
# No external dependencies: this project only uses the standard library.
# The file is kept so that adding one is obvious when it is needed.
'''

ENV = '''\
PORT=8080
DB=books.db
'''

FILES = {
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/core/db.py": DB,
    "app/books/__init__.py": "",
    "app/books/models.py": MODELS,
    "app/books/repository.py": REPOSITORY,
    "app/books/service.py": SERVICE,
    "app/books/router.py": ROUTER,
    "app/main.py": MAIN,
    "tests/__init__.py": "",
    "tests/test_books.py": TESTS,
    "README.md": README,
    "requirements.txt": REQUIREMENTS,
    ".env.example": ENV,
}

GROUPS = {
    "core": ["app/__init__.py", "app/core/__init__.py", "app/core/db.py", "app/main.py"],
    "domain": ["app/books/__init__.py", "app/books/models.py", "app/books/repository.py",
               "app/books/service.py", "app/books/router.py"],
    "tests": ["tests/__init__.py", "tests/test_books.py"],
    "docs": ["README.md", "requirements.txt", ".env.example"],
}

PLAN = [
    {"path": "app/__init__.py", "kind": "code", "purpose": "root package", "exports": [], "depends_on": [], "group": "core"},
    {"path": "app/core/__init__.py", "kind": "code", "purpose": "core package", "exports": [], "depends_on": [], "group": "core"},
    {"path": "app/core/db.py", "kind": "code", "purpose": "connection and schema",
     "exports": ["connect", "create_schema", "WRITE_LOCK"], "depends_on": [], "group": "core"},
    {"path": "app/main.py", "kind": "entrypoint", "purpose": "the HTTP server", "exports": ["create_server", "Handler"],
     "depends_on": ["app/core/db.py", "app/books/router.py"], "group": "core"},
    {"path": "app/books/__init__.py", "kind": "code", "purpose": "domain package", "exports": [], "depends_on": [],
     "group": "domain"},
    {"path": "app/books/models.py", "kind": "code", "purpose": "shape and validation",
     "exports": ["FIELDS", "validate", "as_dict"], "depends_on": [], "group": "domain"},
    {"path": "app/books/repository.py", "kind": "code", "purpose": "the SQL",
     "exports": ["create", "list_all", "get", "update", "delete"],
     "depends_on": ["app/core/db.py", "app/books/models.py"], "group": "domain"},
    {"path": "app/books/service.py", "kind": "code", "purpose": "business rules",
     "exports": ["create", "list_books", "detail", "edit", "remove"],
     "depends_on": ["app/books/repository.py", "app/books/models.py"], "group": "domain"},
    {"path": "app/books/router.py", "kind": "code", "purpose": "HTTP -> service", "exports": ["resolve", "dispatch"],
     "depends_on": ["app/books/service.py"], "group": "domain"},
    {"path": "tests/__init__.py", "kind": "test", "purpose": "tests package", "exports": [], "depends_on": [], "group": "tests"},
    {"path": "tests/test_books.py", "kind": "test", "purpose": "CRUD over real HTTP", "exports": [],
     "depends_on": ["app/main.py"], "group": "tests"},
    {"path": "README.md", "kind": "doc", "purpose": "how to use it", "exports": [], "depends_on": [], "group": "docs"},
    {"path": "requirements.txt", "kind": "config", "purpose": "dependencies", "exports": [], "depends_on": [], "group": "docs"},
    {"path": ".env.example", "kind": "config", "purpose": "environment variables", "exports": [], "depends_on": [],
     "group": "docs"},
]

SPEC = {
    "name": "books-api", "language": "python", "framework": "stdlib", "database": "sqlite",
    "architecture": "by domain, layered", "entity": "book", "resource": "/books",
    "fields": ["title", "author", "year"], "dependencies": [],
    "test_command": "python3 -m unittest discover -s tests -t .",
    "assumptions": [
        "no framework was requested, so http.server is used: the project runs without installing anything",
        "the database lives in memory by default so tests leave no files behind",
    ],
    "files": PLAN,
}
