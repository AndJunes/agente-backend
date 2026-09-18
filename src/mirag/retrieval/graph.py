"""The reference graph, per CHUNK instead of per box.

WHAT CHANGES WITH RESPECT TO THE BOX GRAPH
    The corpus box graph aggregates every `` `[NN]` `` mark into the box of its chunk and
    forgets that it was the "Indexes" section that said it. Here the exact origin is kept.
    Same corpus, same regex, zero format changes: just not throwing away what was there.

WHAT THE CORPUS DOES NOT GIVE, AND IS NOT INVENTED
    The `` `[NN]` `` marks point to BOXES, never to sections. So this graph is chunk -> box:
    to bring concrete chunks of the target box a heuristic is needed, and that choice is
    declared in the path (see :meth:`ChunkGraph.expand`).

THE GRAPH IS VERY DENSE, AND THAT LIMITS HOPS
    At 2 hops almost any box reaches 17-18 of the 19. "Neighbour at 2 hops" therefore narrows
    nothing on its own: what narrows is the order (distance first, weight second) and the
    ``limit``. An unbounded multi-hop here is equivalent to no filter.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from mirag.core.text import normalize
from mirag.i18n.catalog import MessageCatalog
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus


def box_number(box: object) -> str:
    """``'04 · Databases'`` -> ``'04'``. Also accepts a bare number."""
    return str(box).split("·")[0].strip().zfill(2)


@dataclass(frozen=True, slots=True)
class GraphIndex:
    boxes: list[str]
    names: dict[str, str]
    citations: list[tuple[str, ...]]
    """Parallel to ``corpus.chunks``: the boxes each chunk cites."""
    by_box: dict[str, list[int]]
    outgoing: dict[str, Counter[str]]
    incoming: dict[str, Counter[str]]
    chunk_edges: int
    box_edges: int


@dataclass(frozen=True, slots=True)
class ExpansionStep:
    origin_box: str
    chunk: Chunk
    explanation: str


class ChunkGraph:
    """Built once per corpus and reused."""

    def __init__(self, corpus: KnowledgeCorpus, catalog: MessageCatalog) -> None:
        self._corpus = corpus
        self._t = catalog

    @cached_property
    def index(self) -> GraphIndex:
        names: dict[str, str] = {}
        by_box: dict[str, list[int]] = {}
        citations: list[tuple[str, ...]] = []
        outgoing: dict[str, Counter[str]] = {}
        incoming: dict[str, Counter[str]] = {}
        chunk_edges = 0
        for i, chunk in enumerate(self._corpus.chunks):
            n = box_number(chunk.box)
            names[n] = chunk.box
            by_box.setdefault(n, []).append(i)
            refs = [r for r in KnowledgeCorpus.references(chunk.text) if r != n]
            citations.append(tuple(refs))
            chunk_edges += len(refs)
            for target in refs:
                outgoing.setdefault(n, Counter())[target] += 1
                incoming.setdefault(target, Counter())[n] += 1
        return GraphIndex(
            boxes=sorted(by_box), names=names, citations=citations, by_box=by_box,
            outgoing=outgoing, incoming=incoming, chunk_edges=chunk_edges,
            box_edges=sum(len(c) for c in outgoing.values()),
        )

    def resolve(self, box: object) -> str | None:
        """Accepts ``'04'``, ``4``, ``'04 · Databases'`` or ``'databases'``. ``None`` if unknown."""
        g = self.index
        key = box_number(box)
        if key in g.by_box:
            return key
        text = normalize(str(box))
        if len(text) >= 3:
            for n, name in g.names.items():
                if text in normalize(name):
                    return n
        return None

    def neighbours(self, box: object, hops: int = 1) -> dict[str, int]:
        """Bounded BFS over the DIRECTED box graph. ``{box: distance}``, without the origin.

        An unknown box returns ``{}`` instead of raising: the model calls this and often gets
        the name wrong.
        """
        origin = self.resolve(box)
        if origin is None or hops < 1:
            return {}
        outgoing = self.index.outgoing
        distance, queue = {origin: 0}, deque([origin])
        while queue:
            current = queue.popleft()
            if distance[current] >= hops:
                continue
            for target in outgoing.get(current, ()):
                if target not in distance:
                    distance[target] = distance[current] + 1
                    queue.append(target)
        distance.pop(origin, None)
        return distance

    def _candidates(self, origins: Sequence[str], hops: int) -> list[tuple[str, tuple[int, int, str]]]:
        outgoing = self.index.outgoing
        best: dict[str, tuple[int, int, str]] = {}
        for origin in origins:
            for target, dist in self.neighbours(origin, hops).items():
                if target in origins:
                    continue
                weight = outgoing.get(origin, Counter()).get(target, 0)
                previous = best.get(target)
                if previous is None or (dist, -weight) < (previous[0], -previous[1]):
                    best[target] = (dist, weight, origin)
        return sorted(best.items(), key=lambda item: (item[1][0], -item[1][1], item[0]))

    def _shortest_path(self, origin: str, target: str, hops: int) -> list[str]:
        outgoing = self.index.outgoing
        previous: dict[str, str | None] = {origin: None}
        queue = deque([origin])

        def path_to(node: str | None) -> list[str]:
            path = []
            while node is not None:
                path.append(node)
                node = previous.get(node)
            return list(reversed(path))

        while queue:
            current = queue.popleft()
            if current == target:
                break
            if len(path_to(current)) - 1 >= hops:
                continue
            for nxt in outgoing.get(current, ()):
                if nxt not in previous:
                    previous[nxt] = current
                    queue.append(nxt)
        return path_to(target) if target in previous else []

    def expand(self, chunks: Sequence[Chunk], hops: int = 1, limit: int = 8) -> tuple[list[Chunk], list[ExpansionStep]]:
        """Brings chunks from the boxes related to the ones already retrieved.

        THE HEURISTIC PART, SAID OUT LOUD
            The corpus does not say WHICH section of the target box is relevant, only the
            box. So a chunk that cites the origin box back is preferred (a reciprocal link is
            a real relationship) and, if there is none, the first one of the box - and it is
            said. Without a query nothing better can be done without inventing a signal.

        Boxes take turns: with ``limit=8`` and five candidate boxes, all five contribute.
        """
        chunks = list(chunks or ())
        if not chunks or limit < 1:
            return [], []
        g = self.index
        origins = [o for o in dict.fromkeys(box_number(c.box) for c in chunks) if o in g.by_box]
        if not origins:
            return [], []
        already = {c.key for c in chunks}

        queues = []
        for target, (dist, weight, origin) in self._candidates(origins, hops):
            reciprocal: deque[Chunk] = deque()
            rest: deque[Chunk] = deque()
            for i in g.by_box[target]:
                candidate = self._corpus.chunks[i]
                if candidate.key in already:
                    continue
                (reciprocal if origin in g.citations[i] else rest).append(candidate)
            queues.append((origin, target, dist, weight, reciprocal, rest))

        extra: list[Chunk] = []
        steps: list[ExpansionStep] = []
        while queues and len(extra) < limit:
            remaining = []
            for origin, target, dist, weight, reciprocal, rest in queues:
                if len(extra) >= limit:
                    remaining.append((origin, target, dist, weight, reciprocal, rest))
                    continue
                if reciprocal:
                    chunk, how = reciprocal.popleft(), self._t("graph.how.reciprocal")
                elif rest:
                    chunk, how = rest.popleft(), self._t("graph.how.next_in_box")
                else:
                    continue
                route = " → ".join(self._shortest_path(origin, target, hops) or [origin, target])
                weight_text = (self._t("graph.weight", count=weight, origin=origin) if weight
                               else self._t("graph.hops", count=dist))
                steps.append(ExpansionStep(g.names.get(origin, origin), chunk,
                                           f"{route} ({weight_text}) · {chunk.title}: {how}"))
                extra.append(chunk)
                remaining.append((origin, target, dist, weight, reciprocal, rest))
            queues = [q for q in remaining if q[4] or q[5]]
        return extra, steps

    def compare_with_box_graph(self) -> dict[str, Any]:
        """How much information this graph keeps compared to the aggregated box graph."""
        g = self.index
        return {
            "chunk_to_box_nodes": len(self._corpus.chunks),
            "chunk_to_box_edges": g.chunk_edges,
            "box_to_box_nodes": len(self._corpus.box_graph),
            "box_to_box_edges_corpus": sum(len(c) for c in self._corpus.box_graph.values()),
            "box_to_box_edges_own": g.box_edges,
            "chunks_with_references": sum(1 for c in g.citations if c),
            "chunks_without_references": sum(1 for c in g.citations if not c),
        }
