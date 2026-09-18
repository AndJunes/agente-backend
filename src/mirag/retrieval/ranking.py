"""Lexical rankers. BM25 is the floor of retrieval and always runs.

In production this would be pgvector + hybrid search + a cross-encoder (see box 18 of the
corpus). The rest of the application does not notice: it only needs ranked chunks.
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Iterable, Sequence
from functools import lru_cache

from mirag.core.text import normalize
from mirag.retrieval.corpus import Chunk

Scored = tuple[Chunk, float]


class Ranker(ABC):
    """Scores chunks against a query and returns the best ``k``, best first."""

    name: str = "ranker"

    @abstractmethod
    def rank(self, chunks: Sequence[Chunk], query: str, k: int) -> list[Scored]: ...


def filter_by_boxes(chunks: Sequence[Chunk], boxes: Iterable[str] | None) -> list[Chunk]:
    """Keep only the chunks of those boxes. Accepts a number or a name (``"04"``, ``"Databases"``).

    If the filter leaves nothing, the whole index is searched: an empty answer is worse.
    """
    wanted = [normalize(str(box)) for box in (boxes or ())]
    if not wanted:
        return list(chunks)
    kept = [c for c in chunks if any(w in normalize(c.box) for w in wanted)]
    return kept or list(chunks)


@lru_cache(maxsize=16_384)
def _tokens(norm: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9_]{3,}", norm))


class Bm25Ranker(Ranker):
    """BM25 over tokens, with one concession: shared prefixes also count (at half weight).

    Real BM25 brings controlled saturation (k1) and length normalisation (b), which the
    older IDF method lacked: a long chunk collected points just for being long. The
    prefix concession keeps the morphology that plain tokens lose ("indice", "indices" and
    "indexacion"; "index", "indexes" and "indexing").
    """

    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75, prefix: int = 5) -> None:
        self.k1 = k1
        self.b = b
        self.prefix = prefix
        self._frequencies = lru_cache(maxsize=16_384)(self._compute_frequencies)

    def _compute_frequencies(self, norm: str) -> Counter[str]:
        counts = Counter(_tokens(norm))
        for token, n in list(counts.items()):
            counts["^" + token[: self.prefix]] += n
        return counts

    def rank(self, chunks: Sequence[Chunk], query: str, k: int) -> list[Scored]:
        terms = [t for t in dict.fromkeys(normalize(query).split()) if len(t) >= 3]
        if not chunks or not terms:
            return []
        freqs = [self._frequencies(c.norm) for c in chunks]
        lengths = [sum(n for tok, n in f.items() if not tok.startswith("^")) for f in freqs]
        mean = (sum(lengths) / len(lengths)) or 1
        total = len(chunks)

        weights: dict[str, float] = {}
        for term in terms:
            key = "^" + term[: self.prefix]
            df = sum(1 for f in freqs if f.get(term) or f.get(key))
            if df:
                weights[term] = math.log(1 + (total - df + 0.5) / (df + 0.5))
        if not weights:
            return []

        scored: list[Scored] = []
        for chunk, f, length in zip(chunks, freqs, lengths, strict=True):
            score = 0.0
            for term, idf in weights.items():
                tf = f.get(term, 0) + 0.5 * f.get("^" + term[: self.prefix], 0)
                if tf:
                    score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * length / mean))
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]


class IdfRanker(Ranker):
    """The original method: IDF x sqrt(tf), counting SUBSTRINGS.

    Counting substrings is a poor but effective stemmer: ``indice`` matches inside
    ``indices`` and ``indexing``. Kept so the benchmarks can compare against it.
    """

    name = "idf"

    def rank(self, chunks: Sequence[Chunk], query: str, k: int) -> list[Scored]:
        if not chunks:
            return []
        weights = {
            word: math.log(len(chunks) / (1 + sum(word in c.norm for c in chunks)))
            for word in set(normalize(query).split())
            if len(word) >= 3
        }
        if not weights:
            return []

        def score(chunk: Chunk) -> float:
            # sqrt = saturation: 10 repetitions are not worth 10 times one
            return sum(math.sqrt(chunk.norm.count(w)) * weight for w, weight in weights.items())

        best = sorted(chunks, key=score, reverse=True)[:k]
        return [(c, score(c)) for c in best if score(c) > 0]
