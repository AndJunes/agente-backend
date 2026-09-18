"""The lexical rankers: BM25 (production floor) and the original IDF method (benchmarks)."""

from __future__ import annotations

import pytest

from mirag.retrieval.corpus import Chunk
from mirag.retrieval.engine import RetrievalEngine, RetrievalEngineFactory
from mirag.retrieval.ranking import Bm25Ranker, IdfRanker, filter_by_boxes


def chunk(text: str, box: str = "04 · Databases", title: str | None = None) -> Chunk:
    return Chunk.of(text, box, title or text[:24])


TOY = [
    chunk("postgres indexing strategies with a btree"),                       # 0
    chunk("colour palette and typography of the rebrand", "05 · Architecture"),  # 1
    chunk("italian recipes: sourdough, tomato and basil", "07 · Payments"),     # 2
]


# ── BM25 ─────────────────────────────────────────────────────────────────────

def test_bm25_concedes_shared_prefixes() -> None:
    """'indexes' is not a token of the chunk; 'indexing' shares its 5-letter prefix."""
    ranked = Bm25Ranker().rank(TOY, "indexes", k=3)
    assert [c for c, _ in ranked] == [TOY[0]]
    assert Bm25Ranker(prefix=8).rank(TOY, "indexes", k=3) == [], "without the concession it is lost"


def test_bm25_prefers_the_exact_token_over_the_prefix() -> None:
    exact = chunk("indexes everywhere in this text", title="exact")
    ranked = Bm25Ranker().rank([TOY[0], exact], "indexes", k=2)
    assert [c.title for c, _ in ranked] == ["exact", TOY[0].title]
    assert ranked[0][1] > ranked[1][1]


def test_bm25_normalises_length_so_long_chunks_do_not_win_by_length() -> None:
    short = chunk("replication lag", title="short")
    long = chunk("replication lag " + "filler words about nothing " * 60, title="long")
    ranked = Bm25Ranker().rank([long, short], "replication lag", k=2)
    assert ranked[0][0].title == "short"


def test_bm25_ignores_short_terms_and_empty_inputs() -> None:
    ranker = Bm25Ranker()
    assert ranker.rank(TOY, "", k=3) == []
    assert ranker.rank(TOY, "a to of", k=3) == []
    assert ranker.rank([], "postgres", k=3) == []
    assert ranker.rank(TOY, "zzqqxw", k=3) == []


def test_bm25_respects_k_and_orders_by_score() -> None:
    chunks = [chunk(f"cache {'cache ' * i} entry {i}", title=str(i)) for i in range(6)]
    ranked = Bm25Ranker().rank(chunks, "cache", k=4)
    assert len(ranked) == 4
    scores = [s for _, s in ranked]
    assert scores == sorted(scores, reverse=True)


def test_bm25_is_accent_and_case_insensitive() -> None:
    ranked = Bm25Ranker().rank([chunk("Índices y consultas")], "INDICES", k=1)
    assert ranked and ranked[0][1] > 0


@pytest.mark.parametrize(
    ("locale", "query", "box", "title_start"),
    [
        ("en", "outbox pattern", "08", "Outbox pattern"),
        ("es", "outbox pattern", "08", "Outbox pattern"),
        ("en", "persistent volumes in kubernetes", "13", "Kubernetes"),
        ("es", "volumenes persistentes en kubernetes", "13", "Kubernetes"),
    ],
)
def test_bm25_finds_the_section_on_the_real_corpus(
    engines: RetrievalEngineFactory, locale: str, query: str, box: str, title_start: str
) -> None:
    engine = engines.get(locale)
    best, _ = engine.ranker.rank(engine.corpus.chunks, query, k=1)[0]
    assert best.box_number == box and best.title.startswith(title_start), best.title


# ── IDF (the original method, kept for comparison) ───────────────────────────

def test_idf_counts_substrings_as_a_poor_stemmer() -> None:
    # log(N / (1 + df)): with a single other chunk the weight would be log(1) = 0
    ranked = IdfRanker().rank([chunk("los indices de postgres"), *TOY], "indice", k=4)
    assert [c.text for c, _ in ranked] == ["los indices de postgres"]


def test_idf_drops_zero_scores_and_handles_empty_inputs() -> None:
    ranker = IdfRanker()
    assert ranker.rank([], "postgres", k=3) == []
    assert ranker.rank(TOY, "to", k=3) == []
    assert all(score > 0 for _, score in ranker.rank(TOY, "postgres btree", k=3))
    assert ranker.name == "idf" and Bm25Ranker.name == "bm25"


def test_both_rankers_agree_on_an_easy_query(engine: RetrievalEngine) -> None:
    bm25 = engine.ranker.rank(engine.corpus.chunks, "outbox pattern", k=1)[0][0]
    idf = IdfRanker().rank(engine.corpus.chunks, "outbox pattern", k=1)[0][0]
    assert bm25.key == idf.key


# ── the box pre-filter of the typed searches ─────────────────────────────────

def test_filter_by_boxes_accepts_numbers_and_names_and_never_empties() -> None:
    assert filter_by_boxes(TOY, ["04"]) == [TOY[0]]
    assert filter_by_boxes(TOY, ["payments"]) == [TOY[2]]
    assert filter_by_boxes(TOY, ["04", "Architecture"]) == [TOY[0], TOY[1]]
    assert filter_by_boxes(TOY, None) == TOY
    assert filter_by_boxes(TOY, []) == TOY
    assert filter_by_boxes(TOY, ["99"]) == TOY, "an empty filter searches everything instead"
