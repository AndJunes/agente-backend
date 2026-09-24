"""``python -m mirag_pm serve`` — the same server, told it is a different agent.

Deliberately thin. It builds the PM container and hands it to mirag's own ``serve``, so the
binding, the startup warnings and the shutdown are one implementation used twice rather than
two that drift. What differs between the two agents is the container, and only the container.
"""

from __future__ import annotations

import sys

from mirag.api.server import serve
from mirag_pm.container import build_pm_container


def main(argv: list[str] | None = None) -> int:
    arguments = argv if argv is not None else sys.argv[1:]
    if arguments and arguments[0] != "serve":
        print(f"usage: python -m mirag_pm serve  (got {arguments[0]!r})", file=sys.stderr)
        return 2

    container = build_pm_container()
    print(f"  operations: {', '.join(sorted(container.operations or {}))}", flush=True)
    serve(container)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
