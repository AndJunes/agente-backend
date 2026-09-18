"""The syllabus tree: do its numbers add up, and does route() stay silent when it does not know?

Staying silent matters more than being right: the metadata filter believes what it is told.
Every test runs on both locales - the corpus, the stop words and the synonyms are per locale.
"""

from __future__ import annotations

import pytest

from mirag.experimental.knowledge_tree import (
    NO_SUBCATEGORY,
    ROOT,
    KnowledgeTree,
    RoutingOutcome,
)
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus
from mirag.retrieval.engine import RetrievalEngine
from mirag.retrieval.metadata import MetadataExtractor

INDEX_QUERY = {"en": "indexes in postgres", "es": "índices en postgres"}
INDEX_TITLE = {"en": "Indexes", "es": "Índices"}
IRRELEVANT = {
    "en": ("how do I cook a valencian paella", "xyzzy qwerty", "", "the one from yesterday"),
    "es": ("cómo hago una paella valenciana", "xyzzy qwerty", "", "la de ayer"),
}
ONLY_STOPWORDS = {"en": "what about this", "es": "como para esto"}
MULTI_BOX_QUERY = {"en": "latency bottlenecks and caching", "es": "cuellos de botella de latencia y caching"}
# Real queries of the domain: the tree's boxes against the boxes of the best BM25 chunks.
BASELINE_PROBES = {
    "en": ("indexes in postgres", "how do I charge with stripe", "idempotent retries in queues",
           "authentication with JWT", "distributed traces and metrics", "canary deployment",
           "uploading large files", "rag with embeddings", "contract tests", "latency bottlenecks"),
    "es": ("índices en postgres", "cómo cobro con stripe", "reintentos idempotentes en colas",
           "autenticación con JWT", "trazas distribuidas y métricas", "despliegue canary",
           "subida de archivos grandes", "rag con embeddings", "tests de contrato",
           "cuellos de botella de latencia"),
}
BOXES = 19


@pytest.fixture
def tree(engine: RetrievalEngine) -> KnowledgeTree:
    return KnowledgeTree.from_engine(engine)


def chunk(engine: RetrievalEngine, title: str, box: str) -> Chunk:
    return next(c for c in engine.corpus.chunks if c.title == title and c.box_number == box)


# ── the tree ─────────────────────────────────────────────────────────────────


def test_path_of_a_real_chunk(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    assert tree.path(chunk(engine, INDEX_TITLE[engine.locale], "04")) == [ROOT, "04 · Databases", "indexing"]
    path = tree.path(chunk(engine, "Kubernetes", "13"))
    assert path[:2] == [ROOT, "13 · Cloud & Infrastructure"] and len(path) == 3


def test_path_of_odd_input_is_only_the_root(tree: KnowledgeTree) -> None:
    for odd in (None, "04 · Databases", 0, object()):
        assert tree.path(odd) == [ROOT]


def test_every_leaf_hangs_from_a_valid_box(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    boxes = set(engine.corpus.boxes)
    for box, branches in tree.tree[ROOT].items():
        assert box in boxes
        declared = engine.corpus.syllabus[box.split("·")[0].strip()]
        for sub, chunks in branches.items():
            assert sub in declared or sub == NO_SUBCATEGORY, (box, sub)
            for c in chunks:
                assert c.box == box, f"{c.title} hangs from {box} but belongs to {c.box}"


def test_the_root_is_unique(tree: KnowledgeTree) -> None:
    assert list(tree.tree) == [ROOT]
    assert len(tree.tree[ROOT]) == BOXES


def test_coverage_adds_up(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    coverage = tree.coverage()
    assert coverage.chunks == len(engine.corpus.chunks) > 0
    assert coverage.balanced, coverage
    assert coverage.assigned_chunks + coverage.chunks_without_subcategory == coverage.chunks
    assert sum(coverage.chunks_per_box.values()) == coverage.chunks
    assert coverage.boxes == BOXES
    assert all("/" in branch for branch in coverage.empty_subcategories)


def test_an_empty_corpus_does_not_blow_up(engine: RetrievalEngine) -> None:
    """The module cannot assume ~250 chunks."""
    empty = KnowledgeCorpus(engine.locale, engine.corpus.format, (), (), (), (), {})
    tree = KnowledgeTree(empty, MetadataExtractor(empty, engine.lexicon), engine.lexicon, engine.ranker)
    assert tree.tree == {ROOT: {}}
    assert tree.route(INDEX_QUERY[engine.locale]).boxes == ()
    coverage = tree.coverage()
    assert coverage.chunks == 0 and coverage.boxes == 0 and coverage.balanced
    assert tree.compare_with_bm25(BASELINE_PROBES[engine.locale][:2])[0].bm25_boxes == ()


# ── routing ──────────────────────────────────────────────────────────────────


def test_indexes_in_postgres_routes_to_box_04(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    routing = tree.route(INDEX_QUERY[engine.locale])
    assert routing.outcome is RoutingOutcome.ROUTED
    assert routing.boxes and routing.boxes[0].startswith("04"), routing
    assert "indexing" in routing.reason
    assert any("indexing" in proof for proof in routing.evidence[routing.boxes[0]])


def test_something_irrelevant_proposes_no_garbage(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    for query in IRRELEVANT[engine.locale]:
        routing = tree.route(query)
        assert routing.boxes == (), f"{query!r} -> {routing.boxes} ({routing.reason})"
        assert routing.outcome is not RoutingOutcome.ROUTED
        assert len(routing.reason) > 10


def test_the_stop_words_come_from_the_lexicon(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    assert tree.terms(ONLY_STOPWORDS[engine.locale]) == []
    assert tree.route(ONLY_STOPWORDS[engine.locale]).outcome is RoutingOutcome.NO_TERMS


def test_matching_is_by_prefix_never_by_loose_substring(tree: KnowledgeTree) -> None:
    """'ayer' used to match inside 'layered' and sent "the one from yesterday" to System Design."""
    assert tree.prefix_match("layered", ["ayer"]) is None
    assert tree.prefix_match("index", ["indexes"]) == "indexes"
    assert tree.prefix_match("authentication", ["auth"]) == "auth"


@pytest.mark.parametrize("query", [None, 0, "   ", "a b c", "¿?"])
def test_odd_queries_do_not_blow_up(tree: KnowledgeTree, query: object) -> None:
    routing = tree.route(query)
    assert isinstance(routing.boxes, tuple) and isinstance(routing.reason, str)


def test_route_respects_k(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    assert len(tree.route(MULTI_BOX_QUERY[engine.locale], k=3).boxes) == 3
    assert len(tree.route(MULTI_BOX_QUERY[engine.locale], k=2).boxes) == 2


def test_routing_is_compared_with_the_bm25_baseline(engine: RetrievalEngine, tree: KnowledgeTree) -> None:
    """Not a quality assert: it is the measurement that decides whether this module earns a place."""
    probes = BASELINE_PROBES[engine.locale]
    rows = tree.compare_with_bm25(probes)
    assert [row.query for row in rows] == list(probes), "without queries there is no measurement"
    boxes = set(engine.corpus.boxes)
    for row in rows:
        assert set(row.tree_boxes) <= boxes and set(row.bm25_boxes) <= boxes
        assert row.agree == bool(set(row.tree_boxes) & set(row.bm25_boxes))
        assert row.silent == (not row.tree_boxes)
