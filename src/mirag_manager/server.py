"""One port, every agent. The leading path segment (`/pm/...`, `/backend/...`) picks the
container; everything after that is `mirag`'s own request handling, unmodified.

Why this is still two isolated agents and not one merged one: `ApiRequestHandler`'s methods
never construct behaviour from scratch, they read `self.container` — its i18n, its tools, its
operations — and act on whatever that says. Swapping which `Container` `self.container` points
to, per request, based on a path prefix decided BEFORE a single byte of routing happens, is the
entire mechanism. Nothing PM answers can reach the backend's `run_code` tool; nothing routed to
`/backend` is ever handed to a container whose lexicon has `asks_for_code` permanently `False`.
The isolation was always a property of which `Container` answers a request, not of which OS
process runs it — this only changes how a request finds its container.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any, ClassVar

from mirag.api.server import ApiRequestHandler, build_router, startup_notes

if TYPE_CHECKING:
    from mirag.api.router import Router
    from mirag.container import Container

Agents = dict[str, "Container"]


class ManagerRequestHandler(ApiRequestHandler):
    """`ApiRequestHandler`, told to pick its container from the URL instead of holding one for
    the life of the process.

    The query string is carried through by hand rather than via `_split()` (which the parent's
    own `_dispatch` calls again once the prefix is stripped): re-deriving it from the already
    -parsed dict would lose the raw string a route's own regex still has to match against.
    """

    agents: ClassVar[dict[str, tuple[Container, Router]]]

    def log_message(self, format: str, *args: Any) -> None:
        # The parent's own version reads `self.container` unconditionally, which the two
        # manager-level routes below never set: there is no one container to ask about
        # `MIRAG_HTTP_LOG` before an agent has even been chosen. Called directly on
        # `BaseHTTPRequestHandler` rather than via `super()`, which would run straight back
        # into the same unconditional read.
        container = getattr(self, "container", None)
        if container is not None and container.settings.env.get("MIRAG_HTTP_LOG") == "1":
            BaseHTTPRequestHandler.log_message(self, format, *args)

    def _dispatch(self, method: str) -> None:
        path, sep, query = self.path.partition("?")
        head_only = method == "HEAD"
        if path in ("/", "/health"):
            self._json({"status": "ok",
                        "agents": {name: container.health() for name, (container, _r)
                                  in self.agents.items()}}, head_only=head_only)
            return
        prefix, _, rest = path.lstrip("/").partition("/")
        found = self.agents.get(prefix)
        if found is None:
            self._error(404, "unknown_agent",
                        f"this manager serves: {', '.join(sorted(self.agents))}", head_only)
            return
        self.container, self.router = found
        self.path = "/" + rest + (sep + query if sep else "")
        super()._dispatch(method)


class ManagerHTTPServer(ThreadingHTTPServer):
    """Threaded for the same reason `MiragHTTPServer` is: one agent's slow request (a model
    call runs for minutes) must not freeze the others sharing this port."""

    daemon_threads = True


def build_manager_server(agents: Agents, host: str, port: int) -> ManagerHTTPServer:
    routed = {name: (container, build_router(container)) for name, container in agents.items()}
    handler = type("BoundManagerHandler", (ManagerRequestHandler,), {"agents": routed})
    return ManagerHTTPServer((host, port), handler)


def serve(agents: Agents, host: str, port: int) -> None:
    server = build_manager_server(agents, host, port)
    bound_host, bound_port = server.server_address[:2]
    address = bound_host if isinstance(bound_host, str) else bytes(bound_host).decode()
    print(f"Mirag manager listening on http://{address}:{bound_port}")
    for name, container in agents.items():
        print(f"  /{name} -> model={container.settings.model} offline={container.settings.offline}")
        for note in startup_notes(container, address):
            print(f"    [{name}] {note}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
