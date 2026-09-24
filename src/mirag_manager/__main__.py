"""``python -m mirag_manager serve`` — every agent this deployment runs, behind one port.

Deliberately thin, the same shape as `mirag_pm.__main__`: it builds each agent's container
exactly as that agent would build it standalone and hands the set to `mirag_manager.server.serve`.
Adding an agent here is adding one line, not one more process to start and one more port to
remember.
"""

from __future__ import annotations

import sys
from dataclasses import replace

USAGE = "usage: python -m mirag_manager serve  (got %r)"


def _model_override(base, env_var: str):
    """``base``, with its model swapped for ``env_var`` when that is set.

    Both agents read the same process environment now — there is one `.env`, not one per
    agent — so the per-agent model choice that used to be two different containers' worth of
    `MIRAG_MODEL` has to come from two different variable names instead. Unset, an agent gets
    the shared `MIRAG_MODEL`, which is exactly what running it alone would have given it.
    """
    override = (base.env.get(env_var) or "").strip()
    return replace(base, model=override) if override else base


def build_agents():
    from mirag.container import build_container
    from mirag.core.settings import Settings
    from mirag_pm.container import build_pm_container

    base = Settings.from_env()
    return base, {
        "backend": build_container(_model_override(base, "MIRAG_BACKEND_MODEL")),
        "pm": build_pm_container(_model_override(base, "MIRAG_PM_MODEL")),
    }


def main(argv: list[str] | None = None) -> int:
    arguments = argv if argv is not None else sys.argv[1:]
    if arguments and arguments[0] != "serve":
        print(USAGE % arguments[0], file=sys.stderr)
        return 2

    from mirag_manager.server import serve

    base, agents = build_agents()
    for name, container in agents.items():
        ops = ", ".join(sorted(container.operations or {})) or "chat"
        print(f"  {name}: {ops}", flush=True)
    serve(agents, base.host, base.port)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
