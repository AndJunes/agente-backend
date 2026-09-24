"""The agent manager: every `mirag` agent this deployment runs, behind one port.

Not a third agent. It builds the same `Container` each agent would build standalone — `mirag`'s
own for the backend, `mirag_pm.container.build_pm_container` for the PM — and serves them from
one `ThreadingHTTPServer` instead of one process per agent. See `mirag_manager.server` for how a
request finds its container, and `mirag_manager.__main__` for how the set is built.
"""

from __future__ import annotations
