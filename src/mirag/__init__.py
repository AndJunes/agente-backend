"""Mirag: a backend engineering agent that proves what it delivers.

Given a problem, Mirag retrieves what it knows from a curated corpus, proposes a solution,
executes it, and shows exactly which parts of the answer are backed by evidence and which
are only claims made by the model.

The public entry points are:

* :func:`mirag.container.build_container` - the composition root that wires every service.
* :mod:`mirag.api.server` - the HTTP server (``python -m mirag serve``).
* :mod:`mirag.cli` - the command line interface.
"""

__all__ = ["__version__"]

__version__ = "2.0.0"
