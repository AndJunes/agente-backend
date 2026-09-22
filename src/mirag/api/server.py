"""The HTTP server. Standard library only; loopback by default."""

from __future__ import annotations

import hmac
import json
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any, ClassVar

from mirag import __version__
from mirag.api.router import Router
from mirag.core.errors import MiragError, ModelUnreachableError, RateLimitedError
from mirag.api.schemas import MAX_BODY_BYTES, ChatRequest, ValidationError
from mirag.core.text import sha256_hex
from mirag.projects.artifacts import VALID_ID
from mirag.projects.model import safe_name

if TYPE_CHECKING:
    from mirag.container import Container

API = "/api/v1"
TOKEN_HEADER = "X-Mirag-Token"
PROTECTED_ROUTES = frozenset({"chat", "download", "operation"})
"""What costs money or hands out generated code. The page, health and the rest stay open.

`operation` is in here from the moment the route exists, not after someone notices. This is a
frozenset of route NAMES and the check is membership, so a route registered without its name
added is a route with no token on a network whose whole defence is that token."""
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


class ApiRequestHandler(BaseHTTPRequestHandler):
    """Routes requests to the container's use cases. One instance per request."""

    container: ClassVar[Container]
    router: ClassVar[Router]
    server_version = f"Mirag/{__version__}"
    protocol_version = "HTTP/1.1"

    # ── plumbing ─────────────────────────────────────────────────────────────

    def log_message(self, format: str, *args: Any) -> None:
        if self.container.settings.env.get("MIRAG_HTTP_LOG") == "1":
            super().log_message(format, *args)

    def _split(self) -> tuple[str, dict[str, list[str]]]:
        path, _, query = self.path.partition("?")
        return path, urllib.parse.parse_qs(query)

    _answered = False
    """Whether anything has already gone out on this connection.

    The catch-all in `_dispatch` needs it: a handler that failed AFTER sending its headers —
    a stream that died half way — must not have a second response written on top of the
    first, which would leave the caller parsing two bodies glued together."""

    def _send(self, status: int, body: bytes, content_type: str, head_only: bool = False,
              extra: dict[str, str] | None = None) -> None:
        self._answered = True
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in {**SECURITY_HEADERS, **(extra or {})}.items():
            self.send_header(key, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _json(self, payload: Any, status: int = 200, head_only: bool = False) -> None:
        """If serialisation fails, a fixed literal is sent: what failed to serialise is never
        echoed, because that is exactly how a secret leaks."""
        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError):
            body, status = b'{"error":{"code":"not_serializable","message":"not serializable"}}', 500
        self._send(status, body, "application/json; charset=utf-8", head_only)

    def _error(self, status: int, code: str, message: str, head_only: bool = False) -> None:
        self._json({"error": {"code": code, "message": message}}, status, head_only)

    def _authorized(self) -> bool:
        """The shared secret between CodeZard's server and this one. It is not user
        authentication: whoever holds it can ask for everything.

        ``compare_digest`` and not ``==``: ``==`` stops at the first different byte, and that
        timing difference is measurable. Doing it right is cheap.
        """
        expected = self.container.settings.api_token
        if not expected:
            return True
        given = (self.headers.get(TOKEN_HEADER) or "").strip()
        return hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))

    def _dispatch(self, method: str) -> None:
        path, query = self._split()
        head_only = method == "HEAD"
        lookup = self.router.match("GET" if head_only else method, path)
        if lookup is None:
            allowed = self.router.allowed_methods(path)
            if allowed:
                self._error(405, "method_not_allowed", f"allowed: {', '.join(allowed)}", head_only)
            else:
                self._error(404, "not_found", "not found", head_only)
            return
        route, params = lookup
        if route.name in PROTECTED_ROUTES and not self._authorized():
            # A bare 401: it does not say whether the header is missing or wrong, because that
            # difference saves work to whoever is probing.
            self.close_connection = True  # the body was never read: do not reuse the connection
            self._error(401, "unauthorized", "unauthorized", head_only)
            return
        if head_only and route.name == "download":
            self._error(404, "not_found", "HEAD does not download", head_only=True)
            return
        try:
            route.handler(self, query=query, head_only=head_only, **params)
        except Exception as exc:  # noqa: BLE001 — the last line before the socket is dropped
            # Anything a handler did not expect used to leave here uncaught, and `socketserver`
            # answers that by CLOSING THE CONNECTION with nothing on it. Through the gateway
            # that arrives as "Service 'pm' is unreachable" after a minute of waiting — a
            # sentence about the wrong machine. Measured: a TLS failure reaching OpenRouter
            # took down the whole request and said the agent was down.
            #
            # The detail is the exception's type and message, never its traceback: it is the
            # difference between debugging in one minute and reading a stack the caller
            # cannot see. Nothing here is user input echoed back.
            self.log_error("unhandled %s in %s: %s", type(exc).__name__, route.name, exc)
            traceback.print_exc()
            if not getattr(self, "_answered", False):
                self._error(500, "internal_error", f"{type(exc).__name__}: {exc}", head_only)

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_HEAD(self) -> None:
        """The same allow-list as GET. It had to be said apart: HEAD used to fall back to the
        directory listing handler and disclose that ``.env`` existed, its size and mtime."""
        self._dispatch("HEAD")

    def do_POST(self) -> None:
        self._dispatch("POST")

    # ── handlers ─────────────────────────────────────────────────────────────

    def page(self, query: dict[str, list[str]], head_only: bool) -> None:
        try:
            body = self.container.page_path.read_bytes()
        except OSError:
            self._error(500, "page_missing", "the web page is missing", head_only)
            return
        self._send(200, body, "text/html; charset=utf-8", head_only)

    def health(self, query: dict[str, list[str]], head_only: bool) -> None:
        self._json(self.container.health(), head_only=head_only)

    def locales(self, query: dict[str, list[str]], head_only: bool) -> None:
        i18n = self.container.i18n
        self._json({"default": i18n.resolve(None, self.headers.get("Accept-Language")),
                    "supported": list(i18n.supported)}, head_only=head_only)

    def ui_strings(self, query: dict[str, list[str]], head_only: bool, locale: str) -> None:
        i18n = self.container.i18n
        if locale not in i18n.supported:
            self._error(404, "unknown_locale", f"supported: {', '.join(i18n.supported)}", head_only)
            return
        self._json({"locale": locale, "messages": i18n.ui_messages(locale)}, head_only=head_only)

    def demos(self, query: dict[str, list[str]], head_only: bool) -> None:
        requested = (query.get("locale") or [""])[0] or None
        locale = self.container.i18n.resolve(requested, self.headers.get("Accept-Language"))
        self._json({"locale": locale, "offline": self.container.settings.offline,
                    "demos": self.container.demos(locale).listing()}, head_only=head_only)

    def download(self, query: dict[str, list[str]], head_only: bool, artifact_id: str) -> None:
        """The ZIP of an artifact. **The id is not a path and can never become one.**

        Validated against a 24-hex regex and looked up in memory; the bytes served are EXACTLY
        the ones the integrity gate inspected (reading them from disk would open a window
        between "this was checked" and "that was delivered").
        """
        if not VALID_ID.match(artifact_id or ""):
            self._error(400, "malformed_id", "malformed artifact id")  # literal: the input is not echoed
            return
        artifact = self.container.artifacts.get(artifact_id)
        if artifact is None:
            self._error(410, "gone", "that artifact no longer exists")
            return
        if not artifact.downloadable or artifact.package is None:
            self._error(409, "integrity_error", "ARTIFACT INTEGRITY ERROR: the package did not pass inspection")
            return
        data = artifact.package.data
        if sha256_hex(data) != artifact.package.sha256:  # ~1 ms, and it closes the last gap
            self._error(500, "integrity_error", "ARTIFACT INTEGRITY ERROR at delivery")
            return
        filename = safe_name(artifact.name) + ".zip"
        if any(c in filename for c in '\r\n"'):
            self._error(500, "bad_name", "unsafe file name")
            return
        self._send(200, data, "application/zip", extra={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Mirag-Sha256": artifact.package.sha256,
        })

    def blockchain(self, query: dict[str, list[str]], head_only: bool) -> None:
        """The Stellar layer status. **The import is lazy, and that is the point**: if the
        optional dependency is missing or the network does not answer, this returns
        ``{"available": false, "reason": ...}`` and the server stays up."""
        self._json(self.container.blockchain_status(), head_only=head_only)

    def operation(self, query: dict[str, list[str]], head_only: bool, operation: str) -> None:
        """One of this agent's named operations: JSON in, JSON out, no stream.

        Not a mode of `/chat`: `ChatRequest` is `question`, `mode`, `locale` and deliberately
        strict, with nowhere to carry a questionnaire's answers or the plan being revised.
        """
        run = (self.container.operations or {}).get(operation)
        if run is None:
            self._error(404, "unknown_operation",
                        f"this agent serves: {', '.join(sorted(self.container.operations or {}))}", head_only)
            return
        payload = self._read_json(head_only)
        if payload is None:
            return
        locale = self.container.i18n.resolve(
            payload.get("locale") if isinstance(payload.get("locale"), str) else None,
            self.headers.get("Accept-Language"))
        try:
            self._json(run(payload, locale), head_only=head_only)
        except ValueError as exc:
            self._error(400, "invalid_request", str(exc), head_only)
        except (ModelUnreachableError, RateLimitedError) as exc:
            # 503 and not 502: the provider is the one that is unavailable, and the caller may
            # usefully try again. It used to be neither — these are not RuntimeErrors, so they
            # escaped this handler entirely and the connection was dropped with no body.
            self._error(503, "model_unavailable", str(exc), head_only)
        except (RuntimeError, MiragError) as exc:
            # 502: the operation is well-formed and the model behind it did not deliver.
            self._error(502, "upstream_failed", str(exc), head_only)

    def _read_json(self, head_only: bool) -> dict[str, Any] | None:
        """The request body as an object, or ``None`` after answering with the error."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY_BYTES:
            self._error(413 if length > MAX_BODY_BYTES else 400, "bad_length",
                        f"Content-Length must be between 1 and {MAX_BODY_BYTES}", head_only)
            return None
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._error(400, "invalid_json", "the body must be a JSON object", head_only)
            return None
        if not isinstance(payload, dict):
            self._error(400, "invalid_json", "the body must be a JSON object", head_only)
            return None
        return payload

    def chat(self, query: dict[str, list[str]], head_only: bool) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY_BYTES:
            self._error(413 if length > MAX_BODY_BYTES else 400, "bad_length",
                        f"Content-Length must be between 1 and {MAX_BODY_BYTES}")
            return
        try:
            request = ChatRequest.parse(self.rfile.read(length))
        except ValidationError as exc:
            self._error(400, exc.code, str(exc))
            return

        self._answered = True  # from here on the catch-all must not write a second response
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        for key, value in SECURITY_HEADERS.items():
            self.send_header(key, value)
        self.end_headers()
        self.close_connection = True
        gone = False

        def emit(event: dict[str, Any]) -> None:
            """One SSE event. flush() on each one or the browser sees nothing until the end."""
            nonlocal gone
            if gone:
                return
            try:
                payload = json.dumps(event, ensure_ascii=False, default=str)
                self.wfile.write(f"data: {payload}\n\n".encode())
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                gone = True

        self.container.chat.handle(request, emit, self.headers.get("Accept-Language"))


def build_router(container: Container | None = None) -> Router:
    router = Router()
    h = ApiRequestHandler
    router.add("GET", "/", h.page, "page")
    router.add("GET", "/index.html", h.page, "page")
    router.add("GET", f"{API}/health", h.health, "health")
    router.add("GET", f"{API}/locales", h.locales, "locales")
    router.add("GET", f"{API}/i18n/{{locale}}", h.ui_strings, "i18n")
    router.add("GET", f"{API}/demos", h.demos, "demos")
    router.add("GET", f"{API}/artifacts/{{artifact_id}}/download", h.download, "download")
    router.add("GET", f"{API}/blockchain/agent", h.blockchain, "blockchain")
    router.add("POST", f"{API}/chat", h.chat, "chat")
    # Registered only when this container has operations, so a process that cannot serve them
    # does not advertise them. The backend answers 404 here, which is the truth.
    if container is not None and container.operations:
        router.add("POST", f"{API}/{{operation}}", h.operation, "operation")
    return router


class MiragHTTPServer(ThreadingHTTPServer):
    """Threaded: with a single thread, one long request (the architect mode takes minutes)
    freezes the whole page."""

    daemon_threads = True


def build_server(container: Container, host: str | None = None, port: int | None = None) -> MiragHTTPServer:
    handler = type("BoundApiRequestHandler", (ApiRequestHandler,),
                   {"container": container, "router": build_router(container)})
    # Loopback by default and never "": "" is 0.0.0.0, every interface. The one planned
    # exception is a container, where 0.0.0.0 is the only way a published port reaches the
    # process; what isolates it there is publishing against 127.0.0.1 (docs/*/deployment.md).
    return MiragHTTPServer((host or container.settings.host, container.settings.port if port is None else port), handler)


LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def startup_notes(container: Container, host: str) -> list[str]:
    """What an operator must know before trusting this server. A warning that lies is worse
    than none - people learn to ignore it - so each one says only what is true now."""
    settings = container.settings
    notes = []
    if not settings.api_token:
        notes.append(f"No MIRAG_TOKEN: anybody who reaches this port can ask. Set MIRAG_TOKEN and "
                     f"send it in the {TOKEN_HEADER} header.")
    if not settings.execution:
        notes.append("Execution is off: code and tests are delivered WITHOUT running them and the "
                      "verdict is 'not executed'. Switch it on with MIRAG_EXECUTION=on.")
    if host not in LOOPBACK:
        notes.append(f"WARNING: listening on {host}, not only on loopback, "
                     f"{'with' if settings.api_token else 'WITHOUT'} a token. Publish it only against "
                     "127.0.0.1 on the host, or behind something that authenticates.")
    return notes


def serve(container: Container) -> None:
    server = build_server(container)
    host, port = server.server_address[:2]
    address = host if isinstance(host, str) else bytes(host).decode()
    print(f"Mirag {__version__} listening on http://{address}:{port}  (offline={container.settings.offline})")
    for note in startup_notes(container, address):
        print(f"  {note}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
