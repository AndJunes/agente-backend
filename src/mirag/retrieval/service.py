"""THE single source of retrieval. Production and the benchmarks both consume it.

WHY IT EXISTS
    There used to be two stacks: the pipeline ran the hybrid retriever and then threw its
    result away, while the model's context was rebuilt elsewhere with three loose searches.
    The benchmark measured the first and the model received the second. It was proved with
    the SHA of the context: identical with the reranker on and off, because the reranker
    improved a ranking nobody read.

TWO INVARIANTS THAT MUST NOT BREAK
    1. Every retrieval metric that decides whether to enable a capability is measured on
       the SAME pipeline that feeds the model.
    2. benchmark(query, config) and production(query, config) go through this service and
       obtain the same chunks. A test compares the data, not the shape.

THE THREE INDICES STAY SEPARATE
    They are not mixed: each one has different semantics in the prompt and the model reads
    them differently. All three go through the same ranking.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from mirag.core.timing import Stopwatch
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus
from mirag.retrieval.hybrid import HybridRetriever, StageReport
from mirag.retrieval.plan import RetrievalPlan


@dataclass(frozen=True, slots=True)
class IndexSpec:
    name: str
    """Logical name, used in ids and traces."""
    source: str
    """Which index of the corpus it reads."""
    k: int
    separator: str


# The k values are the ones the original context used (3, 6, 5): kept so as not to change
# two things at once.
INDICES: tuple[IndexSpec, ...] = (
    IndexSpec("knowledge", "knowledge", 3, "\n\n---\n\n"),
    IndexSpec("anti_patterns", "anti_patterns", 6, "\n\n"),
    IndexSpec("failures", "failures", 5, "\n\n"),
)


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A chunk and where it came from. Provenance is half its value."""

    chunk: Chunk
    index: str
    score: float
    rank: int
    """1 = the best of its index."""
    methods: tuple[str, ...]

    @property
    def id(self) -> str:
        """Stable identity, to trace a chunk all the way to the prompt."""
        return f"{self.index}:{self.chunk.box_number}:{self.chunk.title}"


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    query: str
    plan: RetrievalPlan | None
    by_index: dict[str, list[RetrievedChunk]]
    stages: list[StageReport]
    fallbacks: list[tuple[str, str]]
    filters: str
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def selected(self) -> list[RetrievedChunk]:
        return [rc for spec in INDICES for rc in self.by_index.get(spec.name, ())]

    @property
    def anti_patterns(self) -> list[RetrievedChunk]:
        """Exposed on its own on purpose: the corpus says anti-patterns MUST be covered, and
        the evidence phase needs their identity and provenance to check it. It does NOT
        pretend they are already covered."""
        return list(self.by_index.get("anti_patterns", ()))

    def ids(self) -> list[str]:
        return [rc.id for rc in self.selected]

    def summary(self) -> str:
        return " · ".join(f"{spec.name}:{len(self.by_index.get(spec.name, ()))}" for spec in INDICES)


class RetrievalService:
    """Retrieves from the three indices with the same ranking and keeps the provenance."""

    def __init__(self, corpus: KnowledgeCorpus, retriever: HybridRetriever) -> None:
        self._corpus = corpus
        self._retriever = retriever

    def retrieve(
        self,
        query: str,
        plan: RetrievalPlan | None = None,
        family: str = "general",
        vector: bool | None = None,
        rerank: bool | None = None,
        per_index_limit: Mapping[str, int] | None = None,
    ) -> RetrievalResult:
        clock = Stopwatch()
        by_index: dict[str, list[RetrievedChunk]] = {}
        stages: list[StageReport] = []
        fallbacks: list[tuple[str, str]] = []
        filters: list[str] = []

        for spec in INDICES:
            k = (per_index_limit or {}).get(spec.name, spec.k)
            result = self._retriever.retrieve(
                query, self._corpus.index(spec.source), plan=plan, k=k,
                family=family, vector=vector, rerank=rerank,
            )
            methods = tuple(stage.name for stage in result.stages if stage.used)
            by_index[spec.name] = [
                RetrievedChunk(chunk, spec.name, round(score, 4), rank, methods)
                for rank, (chunk, score) in enumerate(result.chunks, 1)
            ]
            # stage names are per index: three calls produced three identical 'bm25' steps
            # and any lookup by name kept only the first one
            stages += [StageReport(f"{s.name}:{spec.name}", s.candidates, s.ms, s.detail, s.used)
                       for s in result.stages]
            fallbacks += [(f"{stage}:{spec.name}", reason) for stage, reason in result.fallbacks]
            filters += [s.detail for s in result.stages if s.name == "filter"]

        metrics = {
            "ms": round(clock.ms, 2),
            "candidates": {name: len(items) for name, items in by_index.items()},
            "total_selected": sum(len(items) for items in by_index.values()),
            "methods": sorted({m for items in by_index.values() for rc in items for m in rc.methods}),
        }
        return RetrievalResult(query, plan, by_index, stages, fallbacks, " | ".join(filters), metrics)
