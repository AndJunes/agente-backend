"""What every bench shares: an isolated container, the results folder, rank metrics, output.

ISOLATION
    A bench builds the container exactly as production does (``build_container``), but with
    ``MIRAG_DATA_DIR`` pointing at a temporary folder that is deleted afterwards. The legacy
    task bench once wrote its ten deliveries into the production ``salida/`` folder: it wiped
    the user's last delivery and kept only the last of its own ten. Nothing a bench runs may
    write into the package or the repository, except its own report in ``benchmarks/results/``.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mirag.container import Container, build_container
from mirag.core.settings import Settings, load_dotenv
from mirag.paths import source_checkout_root

BENCHMARKS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BENCHMARKS_DIR / "results"
"""Where the benches leave their reports. The only place in the repository they write to."""


# ── the container ────────────────────────────────────────────────────────────


def benchmark_environment(
    data_dir: Path,
    *,
    offline: bool | None = None,
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """The environment a bench runs with: the caller's (plus ``.env``), redirected to ``data_dir``.

    ``offline``: ``True``/``False`` forces the lock; ``None`` keeps whatever ``MIRAG_OFFLINE``
    says (spending money stays opt-in: the lock is on unless ``MIRAG_OFFLINE=0``).
    """
    env = dict(os.environ) if base is None else dict(base)
    if base is None and (root := source_checkout_root()) is not None:
        load_dotenv(root / ".env", env)  # the API key usually lives there
    env["MIRAG_DATA_DIR"] = str(data_dir)
    if offline is not None:
        env["MIRAG_OFFLINE"] = "1" if offline else "0"
    return env


@contextmanager
def isolated_container(
    *,
    offline: bool | None = None,
    environ: Mapping[str, str] | None = None,
) -> Iterator[Container]:
    """A production container whose data directory is a temporary folder, removed afterwards."""
    with tempfile.TemporaryDirectory(prefix="mirag-bench-", ignore_cleanup_errors=True) as tmp:
        env = benchmark_environment(Path(tmp), offline=offline, base=environ)
        yield build_container(Settings.from_env(env))


def warm_up(container: Container, locale: str) -> None:
    """Load the corpus and fill the ranking caches before anything is timed.

    Without it the first run of a bench pays ~1.5 s of loading that no other run pays, and
    whichever arm runs first looks slower for a cost that is the bench's, not the arm's.
    """
    engine = container.engines.get(locale)
    engine.service.retrieve(engine.catalog.t("demo.canonical.knowledge.question"))


# ── metrics ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RankMetrics:
    """Recall at 1, 3 and k (as hit counts, like the legacy reports) and MRR at depth k.

    Each case contributes the rank of its FIRST acceptable chunk (``None`` = not within k).
    """

    n: int
    hits_at_1: int
    hits_at_3: int
    hits_at_k: int
    k: int
    mrr: float

    @classmethod
    def of(cls, first_positions: Sequence[int | None], k: int) -> RankMetrics:
        found = [p for p in first_positions if p is not None and p <= k]
        n = len(first_positions)
        mrr = round(sum(1.0 / p for p in found) / n, 4) if n else 0.0
        return cls(
            n=n,
            hits_at_1=sum(1 for p in found if p == 1),
            hits_at_3=sum(1 for p in found if p <= 3),
            hits_at_k=len(found),
            k=k,
            mrr=mrr,
        )

    def as_dict(self) -> dict[str, Any]:
        return {"n": self.n, "recall_1": self.hits_at_1, "recall_3": self.hits_at_3,
                "recall_k": self.hits_at_k, "k": self.k, "mrr": self.mrr}

    def row(self, label: str, width: int = 14) -> str:
        """One table row: ``label n R@1 R@3 R@k MRR``."""
        n = self.n
        cells = " ".join(f"{f'{hits}/{n}':>7}" for hits in (self.hits_at_1, self.hits_at_3, self.hits_at_k))
        return f"  {label:<{width}} {n:>3}  {cells} {self.mrr:>6.3f}"

    @staticmethod
    def header(k: int, width: int = 14) -> str:
        return (f"  {'family':<{width}} {'n':>3}  {'R@1':>7} {'R@3':>7} {f'R@{k}':>7} {'MRR':>6}")


def median(values: Sequence[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def percentile(values: Sequence[float], fraction: float) -> float:
    """Nearest-rank percentile, the same rule the legacy benches used for p95."""
    if not values:
        return 0.0
    ordered = sorted(values)
    return float(ordered[min(len(ordered) - 1, int(len(ordered) * fraction))])


# ── output ───────────────────────────────────────────────────────────────────


def utf8_console() -> None:
    """Corpus titles carry accents and the tables use ``·``: a cp1252 console must not crash."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        with suppress(OSError, ValueError):
            reconfigure(encoding="utf-8", errors="replace")


def write_json(path: Path, data: Any, indent: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
