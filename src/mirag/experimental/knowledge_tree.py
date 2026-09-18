"""The Backend → box → subcategory → chunk hierarchy, and routing through it. EXPERIMENTAL.

WHERE EACH LEVEL COMES FROM (nothing is new)
    Backend        a single root, set by hand: the whole corpus is a backend syllabus.
    box            the first line of each ``.md``. 19 of them, written by hand in the corpus.
    subcategory    the syllabus line of each box (``**Covers from the syllabus:**``), read by
                   :class:`~mirag.retrieval.corpus.CorpusParser`. Declared in 19/19 files.
    chunk          the chunk -> subcategory assignment is made by
                   :class:`~mirag.retrieval.metadata.MetadataExtractor` by word matching.
                   NOBODY wrote it: it is derived and it fails.

    This module invents no taxonomy. If a box does not declare a subcategory, it does not
    appear here; if a chunk fits none, it hangs from the box directly and is counted apart in
    :meth:`KnowledgeTree.coverage`. A tree with an honest ``(no subcategory)`` branch is more
    useful than a complete one obtained by padding.

ROUTING, AND ITS MEASURED LIMIT
    :meth:`KnowledgeTree.route` scores boxes against the VOCABULARY of the syllabus
    (subcategory names + the ``subdomain_synonyms`` of the lexicon + the words of the box
    names), not against the ~250 chunks: a precomputed dictionary, O(words of the query).
    That is why it is cheap.

    But cheap is not the same as better. Compared with the obvious baseline - search with
    BM25 and keep the boxes of the best chunks - tree routing gets it right when the query
    uses the syllabus vocabulary and goes SILENT when it does not (it returns no boxes on
    purpose). :meth:`KnowledgeTree.compare_with_bm25` measures that agreement; read it before
    switching this component on in the pipeline.

It works for every locale: the corpus, the metadata, the stop words (``stopwords.tree``) and
the synonyms (``subdomain_synonyms``) all come from the :class:`RetrievalEngine` of the locale.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
from typing import TYPE_CHECKING

from mirag.core.text import normalize
from mirag.i18n.lexicon import Lexicon
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus
from mirag.retrieval.metadata import MetadataExtractor
from mirag.retrieval.ranking import Ranker

if TYPE_CHECKING:
    from mirag.retrieval.engine import RetrievalEngine

ROOT = "Backend"
NO_SUBCATEGORY = "(no subcategory)"
GENERIC_SUBCATEGORY = "concepts"
"""The drawer of the syllabus for whatever fits nowhere else: it routes nothing."""
BOX_NAME_SOURCE = "(box name)"

MIN_NEEDLE = 4
"""A shorter needle matches anything ('rag' inside 'tragedy', 'red' inside 'redis')."""
MIN_TERM = 4
"""The same, from the other side."""
TERM_PUNCTUATION = ".,;:()¿?¡!\"'"

Tree = dict[str, dict[str, dict[str, list[Chunk]]]]
"""``{ROOT: {box: {subcategory: [chunks]}}}``."""


class RoutingOutcome(StrEnum):
    ROUTED = "routed"
    NO_TERMS = "no_terms"
    """The query has no word to route with."""
    NO_MATCH = "no_match"
    """No word of the query is in the syllabus vocabulary."""
    TOO_WEAK = "too_weak"
    """Many boxes tied at a single match: noise, not a signal."""


@dataclass(frozen=True, slots=True)
class TreeRouting:
    """The boxes the TREE proposes for a query, and why.

    An empty ``boxes`` is a legitimate answer: proposing random boxes is worse than proposing
    none, because the metadata filter would believe them.
    """

    boxes: tuple[str, ...]
    outcome: RoutingOutcome
    reason: str
    evidence: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    """box -> ``'term'→`subcategory``` pieces that earned it points."""


@dataclass(frozen=True, slots=True)
class TreeCoverage:
    """How many chunks hang from each level and how many never reach a leaf."""

    root: str
    boxes: int
    subcategories: int
    empty_subcategories: tuple[str, ...]
    """``box/subcategory`` declared by the syllabus that caught no chunk: that is information."""
    chunks: int
    assigned_chunks: int
    """Chunks with at least one subcategory leaf; counted once even if they fall in several."""
    chunks_without_subcategory: int
    chunks_per_box: Mapping[str, int]

    @property
    def balanced(self) -> bool:
        """The check that matters: assigned + without subcategory == every chunk."""
        return self.assigned_chunks + self.chunks_without_subcategory == self.chunks


@dataclass(frozen=True, slots=True)
class BaselineComparison:
    query: str
    tree_boxes: tuple[str, ...]
    bm25_boxes: tuple[str, ...]

    @property
    def agree(self) -> bool:
        return bool(set(self.tree_boxes) & set(self.bm25_boxes))

    @property
    def silent(self) -> bool:
        return not self.tree_boxes


class KnowledgeTree:
    """The syllabus hierarchy of one corpus, its router and its coverage report."""

    def __init__(
        self,
        corpus: KnowledgeCorpus,
        metadata: MetadataExtractor,
        lexicon: Lexicon,
        ranker: Ranker,
    ) -> None:
        self._corpus = corpus
        self._metadata = metadata
        self._ranker = ranker
        self._synonyms = lexicon.mapping("subdomain_synonyms")
        self._stopwords = frozenset(normalize(w) for w in lexicon.words("stopwords.tree"))

    @classmethod
    def from_engine(cls, engine: RetrievalEngine) -> KnowledgeTree:
        return cls(engine.corpus, engine.metadata, engine.lexicon, engine.ranker)

    # ── the tree ─────────────────────────────────────────────────────────────

    @cached_property
    def tree(self) -> Tree:
        """``{ROOT: {box: {subcategory: [chunks]}}}``.

        Declared subcategories that catch no chunk are kept with an empty list instead of
        being deleted: that a branch of the syllabus is empty is information.
        """
        boxes: dict[str, dict[str, list[Chunk]]] = {}
        for chunk in self._corpus.chunks:
            meta = self._metadata.of(chunk)
            branch = boxes.setdefault(
                chunk.box, {sub: [] for sub in self._corpus.syllabus.get(meta.domain, ())}
            )
            for sub in meta.subdomains or (NO_SUBCATEGORY,):
                branch.setdefault(sub, []).append(chunk)
        return {ROOT: dict(sorted(boxes.items()))}

    def path(self, chunk: object) -> list[str]:
        """Where a chunk hangs: ``["Backend", "04 · Databases", "indexing"]``.

        With several subcategories the first one is returned (the rest are in the metadata);
        with none the leaf is ``(no subcategory)``. Odd input (``None``, something that is not
        a chunk) returns only the root instead of raising.
        """
        if not isinstance(chunk, Chunk) or not chunk.box:
            return [ROOT]
        try:
            subs = self._metadata.of(chunk).subdomains
        except (KeyError, TypeError, ValueError):
            subs = ()
        return [ROOT, chunk.box, subs[0] if subs else NO_SUBCATEGORY]

    # ── routing ──────────────────────────────────────────────────────────────

    @cached_property
    def vocabulary(self) -> dict[tuple[str, ...], dict[str, list[str]]]:
        """``{(needle words): {box: [subcategories that contribute it]}}``.

        The needle is the subcategory name (``_`` as a space), its synonyms from the lexicon
        and the words of the box name (``databases``, ``security``). It is stored already
        split into long words: a multi-word needle (``bottleneck`` is one, ``cuello de
        botella`` is three) cannot match a single token of the query. This is the only index
        :meth:`route` looks at: ~90 subcategories, not ~250 chunks.
        """
        vocabulary: dict[tuple[str, ...], dict[str, list[str]]] = {}

        def add(needle: str, box: str, source: str) -> None:
            words = tuple(w for w in normalize(needle).replace("-", " ").split() if len(w) >= MIN_NEEDLE)
            if words:
                vocabulary.setdefault(words, {}).setdefault(box, []).append(source)

        names = self._corpus.box_names
        for number, subs in self._corpus.syllabus.items():
            box = names.get(number, number)
            for sub in subs:
                if sub == GENERIC_SUBCATEGORY:
                    continue
                add(sub.replace("_", " "), box, sub)
                for synonym in self._synonyms.get(sub, ()):
                    add(synonym, box, sub)
            for word in normalize(box.split("·")[-1]).replace("&", " ").split():
                add(word, box, BOX_NAME_SOURCE)
        return vocabulary

    @staticmethod
    def prefix_match(word: str, terms: Sequence[str]) -> str | None:
        """The query term that matches this syllabus word, or ``None``.

        By PREFIX only, both ways: ``indexes`` starts with the needle ``index`` and the query
        ``auth`` is the start of ``authentication``. Allowing a loose substring gave absurd
        false positives - ``ayer`` (yesterday) matched inside ``layered`` and sent "the one
        from yesterday" to System Design.
        """
        for term in terms:
            if term.startswith(word) or word.startswith(term):
                return term
        return None

    def terms(self, query: object) -> list[str]:
        text = normalize(str(query or ""))
        raw = [w.strip(TERM_PUNCTUATION) for w in text.split()]
        return [w for w in dict.fromkeys(raw) if len(w) >= MIN_TERM and w not in self._stopwords]

    def route(self, query: object, k: int = 3) -> TreeRouting:
        """The ``k`` boxes the TREE proposes for the query, and why. Silent when it does not know."""
        terms = self.terms(query)
        if not terms:
            return TreeRouting((), RoutingOutcome.NO_TERMS, "the query has no word to route with")

        points: dict[str, int] = {}
        evidence: dict[str, list[str]] = {}
        for words, boxes in self.vocabulary.items():
            matched = [self.prefix_match(w, terms) for w in words]
            if not all(matched):  # a multi-word needle demands all of its words
                continue
            for box, sources in boxes.items():
                points[box] = points.get(box, 0) + 1
                evidence.setdefault(box, []).append(f"'{matched[0]}'→`{sources[0]}`")

        if not points:
            return TreeRouting(
                (), RoutingOutcome.NO_MATCH,
                f"no word of the query ({', '.join(terms[:4])}) appears in the syllabus: "
                "the tree does not know how to route this",
            )

        ranking = sorted(points.items(), key=lambda item: (-item[1], item[0]))
        # a single match shared by many tied boxes is noise, not a signal
        if ranking[0][1] == 1 and sum(1 for _, p in ranking if p == 1) > k:
            return TreeRouting(
                (), RoutingOutcome.TOO_WEAK,
                f"{len(ranking)} boxes tied at a single match "
                f"({', '.join(box for box, _ in ranking[:3])}...): too weak to route",
            )

        chosen = tuple(box for box, _ in ranking[:k])
        proof = {box: tuple(dict.fromkeys(evidence[box])) for box in chosen}
        detail = "; ".join(f"{box} ({', '.join(proof[box])})" for box in chosen)
        return TreeRouting(chosen, RoutingOutcome.ROUTED, f"syllabus: {detail}", proof)

    # ── reporting ────────────────────────────────────────────────────────────

    def coverage(self) -> TreeCoverage:
        """How many chunks hang from each level and how many never reach a leaf."""
        boxes = self.tree[ROOT]
        assigned: set[tuple[str, str]] = set()
        without: set[tuple[str, str]] = set()
        per_box: dict[str, int] = {}
        empty: list[str] = []
        for box, branches in boxes.items():
            seen: set[tuple[str, str]] = set()
            for sub, chunks in branches.items():
                if not chunks:
                    empty.append(f"{box}/{sub}")
                for chunk in chunks:
                    seen.add(chunk.key)
                    (without if sub == NO_SUBCATEGORY else assigned).add(chunk.key)
            per_box[box] = len(seen)
        without -= assigned  # in case a chunk fell in both branches
        return TreeCoverage(
            root=ROOT,
            boxes=len(boxes),
            subcategories=sum(len(branches) for branches in boxes.values()),
            empty_subcategories=tuple(empty),
            chunks=len(self._corpus.chunks),
            assigned_chunks=len(assigned),
            chunks_without_subcategory=len(without),
            chunks_per_box=per_box,
        )

    def compare_with_bm25(self, queries: Sequence[str], k: int = 3) -> list[BaselineComparison]:
        """Agreement between :meth:`route` and "the boxes of the ``k`` best BM25 chunks".

        Not a quality assert: it is the measurement that decides whether this module earns a
        place. If the tree adds nothing over the baseline, it is surplus.
        """
        rows: list[BaselineComparison] = []
        for query in queries:
            best = self._ranker.rank(self._corpus.chunks, query, k)
            rows.append(BaselineComparison(
                query=query,
                tree_boxes=self.route(query, k=k).boxes,
                bm25_boxes=tuple(dict.fromkeys(chunk.box for chunk, _ in best)),
            ))
        return rows
