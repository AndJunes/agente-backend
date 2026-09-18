"""Mirag's measurement benches.

Scripts, not a library. Run them from the repository root as modules::

    python -m benchmarks.retrieval_eval --locale en
    python -m benchmarks.calibrate_stages --locale es
    python -m benchmarks.project_bench 3 --dry
    python -m benchmarks.task_bench --dry

Every bench measures the SAME code production runs (``RetrievalService.retrieve`` and
``QuestionPipeline.run``), built by the same composition root. A benchmark that measures a
parallel implementation is how the original audit started: the numbers were right about a
pipeline nobody executed.

See ``benchmarks/README.md`` for what each one measures and what it costs.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _ensure_source_on_path() -> None:
    """Let ``python -m benchmarks.X`` work from a source checkout without installing Mirag.

    The package lives under ``src/`` (src layout). When it is installed (``pip install -e .``)
    or ``PYTHONPATH`` already points at it, nothing is touched.
    """
    if importlib.util.find_spec("mirag") is not None:
        return
    source = Path(__file__).resolve().parent.parent / "src"
    if (source / "mirag").is_dir():
        sys.path.insert(0, str(source))


_ensure_source_on_path()
