"""The local heuristic reranker.

It is NOT a cross-encoder. It is an explicit, cheap heuristic: how many query terms appear,
whether they appear together, whether they appear in the title, and whether the chunk has
a card. It is called "heuristic" everywhere on purpose.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise

from mirag.core.text import normalize
from mirag.retrieval.metadata import MetadataExtractor
from mirag.retrieval.ranking import Scored

PROXIMITY_CHARS = 120
"""Two terms closer than this: the chunk talks about the topic, not about it in passing."""


class HeuristicReranker:
    name = "reranker"

    def __init__(self, metadata: MetadataExtractor) -> None:
        self._metadata = metadata

    def rerank(self, query: str, candidates: Sequence[Scored], k: int) -> list[Scored]:
        terms = [t for t in dict.fromkeys(normalize(query).split()) if len(t) >= 3]
        if not terms:
            return list(candidates[:k])

        def score(pair: Scored) -> float:
            chunk, base = pair
            present = [t for t in terms if t in chunk.norm]
            coverage = len(present) / len(terms)
            positions = sorted(p for p in (chunk.norm.find(t) for t in present) if p >= 0)
            together = any(b - a < PROXIMITY_CHARS for a, b in pairwise(positions))
            title = normalize(chunk.title)
            in_title = sum(1 for t in terms if t in title) / len(terms)
            has_card = "card" in self._metadata.of(chunk).artifact_types
            return (coverage * 3.0 + in_title * 2.0 + (0.5 if together else 0.0)
                    + (0.2 if has_card else 0.0) + base * 0.1)  # the previous rank still counts a bit

        return sorted(candidates, key=score, reverse=True)[:k]
