"""A minimal explicit router. Routes are an ALLOW-list: what is not declared is a 404.

The previous server inherited ``SimpleHTTPRequestHandler.do_GET``, which serves the whole
working directory: ``GET /.env`` returned the OpenRouter key with a 200, and ``HEAD`` kept
answering about the whole directory even after GET was locked down. Here no request path is
ever joined to a filesystem path.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

Handler = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class Route:
    method: str
    pattern: re.Pattern[str]
    handler: Handler
    name: str


@dataclass
class Router:
    routes: list[Route] = field(default_factory=list)

    def add(self, method: str, path: str, handler: Handler, name: str = "") -> None:
        """``path`` may contain ``{param}`` segments: they match ``[A-Za-z0-9_-]+`` only."""
        parts = re.split(r"\{(\w+)\}", path)
        regex = "^" + "".join(
            re.escape(part) if i % 2 == 0 else f"(?P<{part}>[A-Za-z0-9_-]+)" for i, part in enumerate(parts)
        ) + "$"
        self.routes.append(Route(method.upper(), re.compile(regex), handler, name or path))

    def match(self, method: str, path: str) -> tuple[Route, dict[str, str]] | None:
        for route in self.routes:
            if route.method != method.upper():
                continue
            if found := route.pattern.match(path):
                return route, found.groupdict()
        return None

    def allowed_methods(self, path: str) -> list[str]:
        return sorted({r.method for r in self.routes if r.pattern.match(path)})
