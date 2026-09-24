"""The test harness is written by Mirag, not by the model. That is why it is evidence.

THE PROBLEM IT CLOSES
    If the integration tests are written by the same model that wrote the code, the model
    can approve itself: its "CRUD test" can call functions instead of doing HTTP, or print
    ``TEST:crud:PASS`` on import. The markers would be green and nothing would have run.

    Here Mirag injects its own probes and **the identifiers carry a nonce generated in
    Python on every run**. The model cannot guess ``TEST:crud_post_a3f19c2b:PASS``, so it
    cannot fabricate it. The only thing it controls is whether its server really answers.

THE THREE PROBES
    deps   which external dependencies exist ON THIS machine. Observed, not assumed.
    tests  runs the project tests and emits one marker per test, with its id.
    crud   starts the real server and hits it over HTTP: POST, GET, GET id, PUT (checking that
           the PUT PERSISTS), DELETE, and GET id -> 404.

    They are written only into the temporary execution folder. They never enter the artifact
    nor the ZIP.

THE CONTRACT THE PROJECT MUST MEET
    The entrypoint exposes ``create_server(port=0, db=":memory:")`` which RETURNS a server
    without starting it. Nothing runs on import. If it is not met, the probe says so with a
    FAIL marker - never with a silence.

The CRUD probe uses a watchdog thread instead of ``signal.SIGALRM``, which does not exist on
Windows.
"""

from __future__ import annotations

import json
import re
import secrets
from collections.abc import Iterable, Mapping
from typing import Any

PROBE_TIMEOUT_S = 20
"""Below the runner timeout: the probe must die FIRST and keep its output."""
OPERATIONS = ("create", "list", "get", "update", "persists", "delete", "deleted")
PROBE_PREFIX = "_probe_"
DEFAULT_RESOURCE = "/books"
DEFAULT_SAMPLE = {"title": "Hopscotch", "author": "Cortazar"}
DEFAULT_CHANGE = {"title": "Hopscotch (2nd ed)", "author": "Cortazar"}
"""Only for a project that really is about books — see :func:`sample_for`."""

NUMBER_HINTS = frozenset({"count", "cantidad", "total", "price", "precio", "amount", "monto",
                          "age", "edad", "year", "ano", "qty", "stock", "number", "numero"})
DATE_HINTS = frozenset({"date", "fecha", "time", "hora", "start", "end", "inicio", "fin",
                        "at", "on", "from", "until", "desde", "hasta"})
BOOLEAN_PREFIXES = ("is_", "has_", "can_", "es_", "tiene_")
BOOLEAN_NAMES = frozenset({"active", "activo", "enabled", "habilitado", "done", "completed"})


def _tokens(name: str) -> list[str]:
    """``start_at`` -> ``['start', 'at']``.

    Split rather than searched: matching ``"at"`` as a substring made `patient_name` and
    `status` both look like dates, because the letters are in there. A field name is a word
    list, so it is read as one."""
    return [t for t in re.split(r"[_\-\s]+|(?<=[a-z])(?=[A-Z])", name) if t]


def sample_for(entity: object, fields: Iterable[object] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """A payload the project under test might plausibly accept, built from its own blueprint.

    The blueprint has always collected ``entity`` and ``fields`` and nothing has ever read
    them. So every project got a book POSTed at it: a booking API received
    ``{"title": "Hopscotch", "author": "Cortazar"}``, its validator answered 400, and all
    seven CRUD markers came out red **by construction** — on a project that was fine.

    The values are guessed from the field names, which is a guess and is allowed to be wrong:
    a wrong payload makes the probe report a failure the project can be fixed for, whereas the
    old behaviour reported a failure nothing could fix.
    """
    names = [str(f).strip() for f in fields or () if str(f).strip()]
    names = [n for n in names if n.lower() not in ("id", "pk", "uuid")]  # the server assigns these
    if not names:
        return dict(DEFAULT_SAMPLE), dict(DEFAULT_CHANGE)

    label = str(entity or "item").strip() or "item"
    sample: dict[str, Any] = {}
    for name in names[:6]:  # enough to be accepted; not so many that one bad guess sinks it
        low = name.lower()
        # Tokenised from the ORIGINAL spelling: lowercasing first destroys the camelCase
        # boundary, and `dueDate` becomes one word that matches nothing.
        words = {t.lower() for t in _tokens(name)}
        if low.startswith(BOOLEAN_PREFIXES) or low in BOOLEAN_NAMES:
            sample[name] = True
        elif words & DATE_HINTS:
            sample[name] = "2026-01-15T10:00:00"
        elif words & NUMBER_HINTS:
            sample[name] = 1
        else:
            # Text is the default on purpose: a string is the value most validators accept,
            # and a wrong guess here costs one field, not the whole request.
            sample[name] = f"{label} de prueba"
    # The changed field must be one the update can actually alter, so never the first if the
    # first looks like a key, and always a string so the comparison after PUT is meaningful.
    changeable = next((n for n in sample if isinstance(sample[n], str)), next(iter(sample)))
    change = {**sample, changeable: f"{sample[changeable]} (v2)" if isinstance(sample[changeable], str) else 2}
    return sample, change
RESOURCE = re.compile(r"\A(/[A-Za-z0-9_-]+)+\Z")


def safe_resource(resource: object) -> str:
    """The REST path the CRUD probe hits, or :data:`DEFAULT_RESOURCE`.

    It comes from the MODEL's spec and ends up inside code Mirag writes and runs. Pasted as
    is, a resource like ``/books", None); mark(0, True) ...`` was valid Python that printed
    this run's nonce markers from inside the probe: the model approving itself, which is the
    one thing the probe exists to prevent. So it is validated here and embedded with ``repr``.
    """
    clean = "/" + str(resource or "").strip().strip("/")
    return clean if RESOURCE.match(clean) else DEFAULT_RESOURCE


def nonce() -> str:
    return secrets.token_hex(4)


def crud_ids(mark: str) -> tuple[str, ...]:
    return tuple(f"crud_{op}_{mark}" for op in OPERATIONS)


def deps_probe(roots: list[str]) -> dict[str, str]:
    return {f"{PROBE_PREFIX}deps.py": f'''\
"""Which external dependencies exist here. Written by Mirag."""
import importlib.util as u
for module in {sorted(roots)!r}:
    print(f"DEP:{{module}}:" + ("INSTALLED" if u.find_spec(module) else "MISSING"), flush=True)
print("DEP:_probe:OK", flush=True)
'''}


def tests_probe(start_dir: str = "tests", minimum: int = 1) -> dict[str, str]:
    """A unittest runner that emits one marker per test. It takes away from the model the
    duty of printing them, which is the number one cause of NO EVIDENCE.

    Two things in here were wrong and both were silent.

    The marker id came from `str(test).split()[0]`, which is the bare METHOD name — so
    `TestRepository.test_eliminar` and `TestService.test_eliminar` produced the same marker
    and one overwrote the other's verdict. Measured on a real project: 65 tests ran and 55
    markers came out. It is `test.id()` now, which is the full dotted path.

    And `discover()` raising — the ordinary `ImportError: Start directory is not importable` —
    left a bare traceback, no markers and exit 1, indistinguishable downstream from thirty-five
    failing assertions. The two have opposite fixes. It says which one it is now.
    """
    return {f"{PROBE_PREFIX}tests.py": f'''\
"""Runs the project tests and emits one marker per test. Written by Mirag."""
import os, sys, traceback, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Markers(unittest.TextTestResult):
    def _id(self, test):
        # The FULL id, not the method name: two classes routinely share a method name, and
        # a shared marker means one test silently overwrites the other's verdict. Kept from
        # the right, because what distinguishes them is the tail.
        full = test.id().replace(".", "_")
        return (full[-80:] if len(full) > 80 else full) or "unnamed"
    def addSuccess(self, test):
        super().addSuccess(test); print(f"TEST:{{self._id(test)}}:PASS", flush=True)
    def addFailure(self, test, err):
        super().addFailure(test, err); print(f"TEST:{{self._id(test)}}:FAIL", flush=True)
    def addError(self, test, err):
        super().addError(test, err); print(f"TEST:{{self._id(test)}}:FAIL", flush=True)

if __name__ == "__main__":
    try:
        suite = unittest.defaultTestLoader.discover({start_dir!r}, top_level_dir=".")
    except Exception:
        # NOT the same event as a failing assertion, and the fix is the opposite one.
        print("TEST:test_discovery:FAIL", flush=True)
        print("PROBE: the tests could not be loaded at all — this is not a failing test, it "
              "is {start_dir}/ not being importable. Check the package markers and the imports.",
              flush=True)
        traceback.print_exc()
        sys.exit(1)
    result = unittest.TextTestRunner(resultclass=Markers, verbosity=0).run(suite)
    if result.testsRun < {minimum}:
        # An import that fails inside a silent try leaves 0 tests and exit 0.
        # That is NOT passing: nobody knows what was tested.
        print("TEST:test_coverage:FAIL", flush=True)
        print(f"PROBE: {{result.testsRun}} tests ran and at least {minimum} were expected",
              flush=True)
        sys.exit(1)
    sys.exit(1 if (result.failures or result.errors) else 0)
'''}


_NODE_TESTS = r'''// Runs the project tests and emits one marker per test. Written by Mirag.
import { run } from "node:test";
import { readdirSync } from "node:fs";
import { basename, extname, join, resolve } from "node:path";

const START = __START__;
const MINIMUM = __MINIMUM__;

function walk(dir) {
  let out = [];
  let entries;
  try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const entry of entries) {
    if (entry.name === "node_modules" || entry.name === ".git") continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out = out.concat(walk(full));
    else if (/\.(c|m)?js$/.test(entry.name)) out.push(resolve(full));
  }
  return out;
}

// The file is part of the id for the same reason the full dotted path is in the Python probe:
// two files routinely share a test name, and a shared marker means one silently overwrites
// the other's verdict.
const seen = new Map();
function marker(data) {
  const file = data.file ? basename(data.file, extname(data.file)) : "";
  const raw = `${file}_${data.name}`.replace(/[^A-Za-z0-9_]+/g, "_").replace(/^_+|_+$/g, "");
  const base = (raw || "unnamed").slice(-80);
  const n = (seen.get(base) ?? 0) + 1;
  seen.set(base, n);
  return n === 1 ? base : `${base}_${n}`;
}

const files = walk(START);
if (files.length === 0) {
  console.log("TEST:test_discovery:FAIL");
  console.log(`PROBE: no .js test file was found under ${START}/ — this is not a failing test, it is nothing to run.`);
  process.exit(1);
}

let ran = 0;
let failed = 0;
const stream = run({ files });
stream.on("test:pass", (data) => {
  if (data.details?.type === "suite") return;
  ran += 1;
  console.log(`TEST:${marker(data)}:PASS`);
});
stream.on("test:fail", (data) => {
  if (data.details?.type === "suite") return;
  ran += 1;
  failed += 1;
  console.log(`TEST:${marker(data)}:FAIL`);
  const error = data.details?.error;
  console.log(`FAIL: ${data.name} (${data.file ?? "?"})`);
  console.log(String(error?.cause?.stack ?? error?.stack ?? error?.message ?? error ?? ""));
});

try {
  for await (const _event of stream) { /* drained: the listeners above do the reporting */ }
} catch (error) {
  console.log("TEST:test_discovery:FAIL");
  console.log("PROBE: the tests could not be loaded at all — this is not a failing test.");
  console.log(String(error?.stack ?? error));
  process.exit(1);
}

if (ran < MINIMUM) {
  // A test file that registers nothing leaves 0 tests and exit 0. That is NOT passing.
  console.log("TEST:test_coverage:FAIL");
  console.log(`PROBE: ${ran} tests ran and at least ${MINIMUM} were expected`);
  process.exit(1);
}
process.exit(failed ? 1 : 0);
'''


def node_tests_probe(start_dir: str = "tests", minimum: int = 1) -> dict[str, str]:
    """The Node.js twin of :func:`tests_probe`: `node:test` run programmatically, one marker per test.

    The model is asked for plain `node:test` files with no dependencies, and this is what turns
    their result into evidence — a test that prints its own `TEST:...:PASS` is a test that can
    approve itself. Suites (`describe`) report as their own events and are skipped: only the
    tests inside them are markers, otherwise a suite with one failing test would count twice.
    """
    source = _NODE_TESTS.replace("__START__", json.dumps(start_dir)).replace("__MINIMUM__", str(int(minimum)))
    return {f"{PROBE_PREFIX}tests.mjs": source}


def crud_probe(
    entrypoint_module: str,
    mark: str,
    resource: str = "/books",
    sample: Mapping[str, Any] | None = None,
    change: Mapping[str, Any] | None = None,
    entrypoint_name: str = "create_server",
) -> dict[str, str]:
    """The integration probe: real HTTP against the project's server.

    Every value that reaches the generated source is embedded with ``repr`` (a literal can
    never become code) and the resource is validated by :func:`safe_resource`.

    ``entrypoint_name`` is the factory the certifier actually FOUND, not the one the contract
    asked for. The language directive pushes the model towards the user's tongue, so a project
    can perfectly well expose ``crear_servidor``; hardcoding the English name here left those
    projects with no CRUD evidence at all and nothing on screen to say why.
    """
    sample = dict(sample or DEFAULT_SAMPLE)
    change = dict(change or DEFAULT_CHANGE)
    field = next(iter(change))
    resource = safe_resource(resource)
    ids = crud_ids(mark)
    return {f"{PROBE_PREFIX}crud.py": f'''\
"""Real CRUD over HTTP against the project's server. Written by Mirag, not by the model.

The identifiers carry a nonce of this run: the model cannot fabricate them.
"""
import importlib, json, os, sys, threading, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

IDS = {list(ids)!r}
ENTRYPOINT = {entrypoint_module!r}
FACTORY = {entrypoint_name!r}
RESOURCE = {resource!r}
def mark(i, ok):
    print(f"TEST:{{IDS[i]}}:" + ("PASS" if ok else "FAIL"), flush=True)
def fail_all(start=0):
    for i in range(start, len(IDS)):
        mark(i, False)

def watchdog():
    print("the probe stopped itself before the runner limit", flush=True)
    fail_all()
    os._exit(1)
timer = threading.Timer({PROBE_TIMEOUT_S}, watchdog)
timer.daemon = True
timer.start()

def call(base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={{"Content-Type": "application/json"}})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else {{}})
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            return error.code, (json.loads(raw) if raw else {{}})
        except ValueError:
            return error.code, {{}}
    except Exception as error:
        print(f"the request {{method}} {{path}} blew up: {{type(error).__name__}}: {{error}}", flush=True)
        return 0, {{}}

server = None
try:
    # importlib and not `from X import`: a module path that is not an identifier ('my-api')
    # must end in FAIL markers, not in a SyntaxError of the probe itself (a silence).
    create_server = getattr(importlib.import_module(ENTRYPOINT), FACTORY)
except Exception as error:
    print(f"could not import {{FACTORY}} from {{ENTRYPOINT}}: {{type(error).__name__}}: {{error}}", flush=True)
    fail_all(); timer.cancel(); sys.exit(1)

try:
    server = create_server(port=0)
    base = f"http://127.0.0.1:{{server.server_address[1]}}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
except Exception as error:
    print(f"{{FACTORY}} did not start: {{type(error).__name__}}: {{error}}", flush=True)
    fail_all(); timer.cancel(); sys.exit(1)

try:
    status, created = call(base, "POST", RESOURCE, {sample!r})
    ident = created.get("id") if isinstance(created, dict) else None
    mark(0, status in (200, 201) and ident is not None)
    if ident is None:
        fail_all(1); timer.cancel(); sys.exit(1)
    item = f"{{RESOURCE}}/{{ident}}"

    status, listing = call(base, "GET", RESOURCE)
    mark(1, status == 200 and isinstance(listing, list)
         and any(str(x.get("id")) == str(ident) for x in listing if isinstance(x, dict)))

    status, one = call(base, "GET", item)
    mark(2, status == 200 and isinstance(one, dict) and str(one.get("id")) == str(ident))

    status, _ = call(base, "PUT", item, {change!r})
    mark(3, status in (200, 204))

    # that the PUT PERSISTS, not that a PUT handler exists
    status, after = call(base, "GET", item)
    mark(4, status == 200 and isinstance(after, dict) and after.get({field!r}) == {change[field]!r})

    status, _ = call(base, "DELETE", item)
    mark(5, status in (200, 202, 204))

    status, _ = call(base, "GET", item)
    mark(6, status == 404)
finally:
    timer.cancel()
    if server is not None:
        try:
            server.shutdown(); server.server_close()
        except Exception:
            pass
'''}
