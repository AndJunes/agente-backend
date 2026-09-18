"""Typed searches over the corpus, exposed to the model as tools.

They are separate on purpose: the model chooses a tool by its description, so each one
says what it is for AND what it is not for.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence

from mirag.core.text import normalize
from mirag.i18n.catalog import MessageCatalog
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus
from mirag.retrieval.ranking import Ranker, filter_by_boxes


class KnowledgeSearch:
    def __init__(self, corpus: KnowledgeCorpus, ranker: Ranker, catalog: MessageCatalog) -> None:
        self._corpus = corpus
        self._ranker = ranker
        self._t = catalog

    def _search(self, index: Sequence[Chunk], query: str, k: int, separator: str,
                boxes: Iterable[str] | None) -> str:
        best = self._ranker.rank(filter_by_boxes(index, boxes), query, k)
        if not best:
            return self._t("search.no_results")
        return separator.join(chunk.text for chunk, _ in best)

    def docs(self, query: str, boxes: Iterable[str] | None = None, k: int = 3) -> str:
        """General search. ``boxes`` narrows it to some areas (less context, less noise)."""
        return self._search(self._corpus.chunks, query, k, "\n\n---\n\n", boxes)

    def tradeoffs(self, topic: str, boxes: Iterable[str] | None = None, k: int = 5) -> str:
        """Only the cards: trade-offs, limits and decisions of each concept."""
        return self._search(self._corpus.cards, topic, k, "\n\n", boxes)

    def failures(self, topic: str, boxes: Iterable[str] | None = None, k: int = 5) -> str:
        """Only what can go wrong: failure sections and the 'how it fails' field."""
        return self._search(self._corpus.failures, topic, k, "\n\n", boxes)

    def anti_patterns(self, topic: str, boxes: Iterable[str] | None = None, k: int = 6) -> str:
        """Only the known mistakes: what NOT to do and what to do instead."""
        return self._search(self._corpus.anti_patterns, topic, k, "\n\n", boxes)

    def related_boxes(self, box: str) -> str:
        """Which boxes this one references and which reference it."""
        graph = self._corpus.box_graph
        needle = normalize(box or "").strip()
        # an empty name is a substring of every box: it used to answer with box 01
        key = next((b for b in graph if needle in normalize(b)), None) if needle else None
        if not key:
            # guessing the box from content returned wrong results; failing with the list
            # lets the model retry with the right name
            return self._t("search.unknown_box", boxes="\n  ".join(sorted(graph)))
        number = int(key.split("·")[0].strip())
        outgoing = graph[key]
        incoming = Counter({b: g[number] for b, g in graph.items() if g.get(number) and b != key})
        names = {int(b.split("·")[0]): b for b in graph}
        out_text = ", ".join(f"{names.get(n, n)} ({v})" for n, v in outgoing.most_common(6))
        in_text = ", ".join(f"{b} ({v})" for b, v in incoming.most_common(6))
        none = self._t("search.none")
        return self._t("search.related", box=key, outgoing=out_text or none, incoming=in_text or none)
