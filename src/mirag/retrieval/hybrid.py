"""Hybrid retrieval: BM25 + a vector signal fused with RRF, and an optional reranker.

    metadata filter
        ↓
    BM25  ───┐
             ├── RRF ──→ top N ──→ reranker? ──→ top K
    vector ──┘

WHY RRF AND NOT SUMMING SCORES
    BM25 returns unscaled scores (0..30) and cosine goes from 0 to 1. Summing them needs a
    normalisation, and any normalisation invents an equivalence between two things that
    have none. RRF only looks at the RANK, so nothing has to be calibrated.

WHAT DOES NOT ALWAYS RUN
    The vector signal and the reranker go through the feature gate: if nobody measured that
    they help, they do not run. BM25 is the floor and always runs.

Every stage records how many candidates it produced and how long it took: without that
nobody can answer "why did Mirag retrieve this?" or "where does the time go?".
"""

from __future__ import annotations

import threading
from collections.abc import Sequence
from dataclasses import dataclass, field

from mirag.core.timing import Stopwatch
from mirag.features.flags import FeatureGate
from mirag.i18n.catalog import MessageCatalog
from mirag.retrieval.corpus import Chunk
from mirag.retrieval.metadata import MetadataFilter
from mirag.retrieval.plan import RetrievalPlan
from mirag.retrieval.ranking import Ranker, Scored
from mirag.retrieval.reranker import HeuristicReranker
from mirag.retrieval.vectors import VectorStore, VectorStoreFactory

RRF_K = 60
"""The classic constant: it dampens the first positions."""
CANDIDATES = 20
"""What enters the reranker. Never the whole corpus."""


@dataclass(frozen=True, slots=True)
class StageReport:
    name: str
    candidates: int
    ms: float
    detail: str = ""
    used: bool = True


@dataclass(frozen=True, slots=True)
class HybridResult:
    chunks: list[Scored]
    stages: list[StageReport]
    fallbacks: list[tuple[str, str]] = field(default_factory=list)

    @property
    def ms(self) -> float:
        return round(sum(s.ms for s in self.stages), 2)


def reciprocal_rank_fusion(rankings: Sequence[Sequence[Chunk]], k: int = RRF_K) -> list[Scored]:
    """Each list votes by RANK, not by score."""
    points: dict[tuple[str, str], float] = {}
    seen: dict[tuple[str, str], Chunk] = {}
    for ranking in rankings:
        for position, chunk in enumerate(ranking, 1):
            points[chunk.key] = points.get(chunk.key, 0.0) + 1.0 / (k + position)
            seen[chunk.key] = chunk
    ordered = sorted(points.items(), key=lambda item: item[1], reverse=True)
    return [(seen[key], score) for key, score in ordered]


class VectorIndexCache:
    """Indexing ~250 chunks costs ~170 ms; doing it on EVERY query turned a 0.6 ms signal
    into a 160 ms one and the gate would have rejected it for a cost that was ours, not its
    own. The index is built once per chunk set."""

    def __init__(self, factory: VectorStoreFactory) -> None:
        self._factory = factory
        self._stores: dict[tuple[int, int], VectorStore] = {}
        self._lock = threading.Lock()

    def store_for(self, chunks: Sequence[Chunk]) -> VectorStore:
        key = (len(chunks), hash(tuple(c.key for c in chunks)))
        with self._lock:
            if key not in self._stores:
                self._stores[key] = self._factory.create([c.text for c in chunks])
            return self._stores[key]


class HybridRetriever:
    """The retrieval pipeline over ONE index. Returns everything that happened."""

    def __init__(
        self,
        ranker: Ranker,
        metadata_filter: MetadataFilter,
        reranker: HeuristicReranker,
        vectors: VectorIndexCache,
        gate: FeatureGate,
        catalog: MessageCatalog,
    ) -> None:
        self._ranker = ranker
        self._filter = metadata_filter
        self._reranker = reranker
        self._vectors = vectors
        self._gate = gate
        self._t = catalog

    def retrieve(
        self,
        query: str,
        index: Sequence[Chunk],
        plan: RetrievalPlan | None = None,
        k: int = 5,
        family: str = "general",
        vector: bool | None = None,
        rerank: bool | None = None,
    ) -> HybridResult:
        """``vector`` / ``rerank``: ``None`` = the gate decides; ``True``/``False`` = forced (to measure)."""
        stages: list[StageReport] = []
        fallbacks: list[tuple[str, str]] = []

        # ── 1. metadata filter ──────────────────────────────────────────────
        clock = Stopwatch()
        if self._gate.decide("metadata_routing").enabled and plan is not None:
            outcome = self._filter.apply(index, plan=plan)
            filtered, reason = outcome.chunks, outcome.reason
            if outcome.fell_back:
                fallbacks.append(("metadata_routing", reason))
        else:
            filtered, reason = list(index), self._t("retrieval.filter.no_plan")
        stages.append(StageReport("filter", len(filtered), clock.ms, reason))

        # ── 2. BM25: the floor, always ──────────────────────────────────────
        # HYBRID_RETRIEVAL off = no ranking: the corpus order. The absolute floor against
        # which it is measured whether BM25 adds anything.
        clock.restart()
        if self._gate.decide("hybrid_retrieval").enabled:
            lexical = self._ranker.rank(filtered, query, CANDIDATES)
        else:
            lexical = [(chunk, 0.0) for chunk in filtered[:CANDIDATES]]
        stages.append(StageReport("bm25", len(lexical), clock.ms,
                                  self._t("retrieval.stage.bm25", method=self._ranker.name)))

        # ── 3. vector signal, if measured ───────────────────────────────────
        vector_decision = self._gate.decide("vector_signal", family)
        use_vector = vector_decision.enabled if vector is None else vector
        semantic: list[Scored] = []
        if use_vector:
            clock.restart()
            try:
                store = self._vectors.store_for(filtered)
                semantic = [(filtered[i], score) for i, score in store.search(query, CANDIDATES)]
                detail = self._t("retrieval.stage.vector_backend", backend=store.name)
                if store.fallback:
                    fallbacks.append(("vector", store.fallback))
                    detail += f" ({store.fallback})"
            except Exception as exc:  # an optional signal never takes the search down
                fallbacks.append(("vector", f"{type(exc).__name__}: {exc}"))
                detail = self._t("retrieval.stage.vector_failed", error=type(exc).__name__)
            stages.append(StageReport("vector", len(semantic), clock.ms, detail))
        else:
            stages.append(StageReport("vector", 0, 0.0, vector_decision.explain(self._t), used=False))

        # ── 4. fusion ───────────────────────────────────────────────────────
        clock.restart()
        if semantic:
            fused = reciprocal_rank_fusion([[c for c, _ in lexical], [c for c, _ in semantic]])
            detail = self._t("retrieval.stage.rrf", lexical=len(lexical), vector=len(semantic))
        else:
            fused = lexical
            detail = self._t("retrieval.stage.rrf_single")
        stages.append(StageReport("rrf", len(fused), clock.ms, detail))

        # ── 5. reranker, if measured ────────────────────────────────────────
        rerank_decision = self._gate.decide("reranker", family)
        use_rerank = rerank_decision.enabled if rerank is None else rerank
        if use_rerank and fused:
            clock.restart()
            try:
                final = self._reranker.rerank(query, fused[:CANDIDATES], k)
                detail = self._t("retrieval.stage.reranker", candidates=min(len(fused), CANDIDATES))
            except Exception as exc:
                final = fused[:k]
                detail = self._t("retrieval.stage.reranker_failed", error=type(exc).__name__)
                fallbacks.append(("reranker", str(exc)))
            stages.append(StageReport("reranker", len(final), clock.ms, detail))
        else:
            final = fused[:k]
            stages.append(StageReport("reranker", 0, 0.0, rerank_decision.explain(self._t), used=False))

        return HybridResult(final[:k], stages, fallbacks)
