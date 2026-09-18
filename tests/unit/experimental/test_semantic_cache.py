"""The two-level answer cache: that it hits, and above all that it EXPIRES.

What matters most here is not the saving, it is that an answer computed against another
corpus or another model never comes out. And one test exists to pin down a measured NEGATIVE
result: the similarity level does not separate two different questions that look alike
letter by letter. If that test ever turns red, the signal improved and the recommendation
must be redone - the test is not wrong.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from mirag.experimental.semantic_cache import (
    DEFAULT_THRESHOLD,
    HASH_LENGTH,
    LOCAL_SIGNAL_NAME,
    SIMILAR_LEVEL_DEFAULT,
    AnswerCache,
    CacheOutcome,
    CacheStats,
    CacheVersion,
    LoadStatus,
    cache_key,
    corpus_hash,
)
from mirag.retrieval.corpus import Chunk
from mirag.retrieval.engine import RetrievalEngine, RetrievalEngineFactory

# A fixed version: tests do not depend on the real corpus nor on the configured model, and
# the only version change is the one each test provokes.
BASE = CacheVersion(
    corpus_hash="aaaa1111",
    embedding_model=LOCAL_SIGNAL_NAME,
    embedding_version="v1",
    model_version="anthropic/claude-haiku-4.5",
)

# Language data per locale. The cache itself has no language, but the measured behaviour of
# the lexical signal must hold for the queries of both.
LEXICAL_VARIANT = {
    "en": ("what is an index in postgres", "what is an index in postgresql"),
    "es": ("que es un indice en postgres", "que es un indice en postgresql"),
}
SYNONYMS = {
    "en": ("readiness probe in kubernetes", "health check in kubernetes"),
    "es": ("readiness probe en kubernetes", "health check en kubernetes"),
}
# The confusable pair: two DIFFERENT questions that only change one verb...
CONFUSABLE = {
    "en": ("in the checkout, how do I avoid a race condition when reserving the inventory "
           "with several concurrent workers?",
           "in the checkout, how do I avoid a race condition when charging the inventory "
           "with several concurrent workers?"),
    "es": ("en el checkout, ¿cómo evito una race condition al reservar el inventario "
           "con varios workers concurrentes?",
           "en el checkout, ¿cómo evito una race condition al cobrar el inventario "
           "con varios workers concurrentes?"),
}
# ...and the SAME question with one more word.
SAME_REWORDED = {
    "en": ("idempotency in payments", "idempotency in the payments"),
    "es": ("idempotencia en pagos", "idempotencia en los pagos"),
}
LOCALES = ("en", "es")


def version(**changes: str) -> CacheVersion:
    return replace(BASE, **changes)


@pytest.fixture
def cache_file(tmp_path: Path) -> Path:
    return tmp_path / "cache.json"


class TickingClock:
    """A deterministic clock: every reading is one second after the previous one."""

    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        self.now += 1.0
        return self.now


def similarity(a: str, b: str) -> float:
    """What the local signal scores between two queries, with no threshold in between."""
    cache = AnswerCache(BASE, similar_enabled=True, threshold=0.0)
    cache.store(a, "value")
    return cache.lookup(b).similarity


# ── level 1: exact ───────────────────────────────────────────────────────────


def test_miss_on_an_empty_cache_explains_itself() -> None:
    result = AnswerCache(BASE).lookup("what is an index")
    assert result.value is None
    assert result.outcome is CacheOutcome.MISS
    assert not result.hit
    assert len(result.reason) > 10
    assert result.key and result.similarity == 0.0


def test_store_then_exact_hit() -> None:
    cache = AnswerCache(BASE)
    cache.store("what is an index", "an index is a structure...")
    result = cache.lookup("what is an index")
    assert result.value == "an index is a structure..."
    assert result.outcome is CacheOutcome.EXACT and result.similarity == 1.0
    assert result.hit


@pytest.mark.parametrize(
    ("stored", "variants"),
    [
        ("How do I avoid a Race Condition?",
         ("how do i avoid a race condition", "  HOW do I   avoid a RACE condition?  ",
          "how do I avoid a race condition.")),
        ("¿Cómo evito una race condition?",
         ("como evito una race condition", "  ¿CÓMO   evito    una RACE condition?  ",
          "cómo evito una race condition.")),
    ],
    ids=LOCALES,
)
def test_normalisation_leads_to_the_same_entry(stored: str, variants: tuple[str, ...]) -> None:
    """Accents, case, extra spaces and question marks are the same question, not another."""
    cache = AnswerCache(BASE)
    cache.store(stored, "with a lock...")
    for variant in variants:
        result = cache.lookup(variant)
        assert result.outcome is CacheOutcome.EXACT, (variant, result)
        assert result.value == "with a lock...", variant
    assert cache.stats().entries == 1, "one question, one entry"


def test_normalisation_stops_where_the_meaning_changes() -> None:
    cache = AnswerCache(BASE)
    cache.store("when do I use a == b", "like this")
    assert cache.lookup("when do I use a = b").outcome is CacheOutcome.MISS
    assert cache_key("a == b") != cache_key("a = b")
    assert AnswerCache(BASE).lookup("something else").outcome is CacheOutcome.MISS


# ── level 2: similar (off by default, hence switched on here) ────────────────


@pytest.mark.parametrize("locale", LOCALES)
def test_similarity_hit_above_the_threshold_says_it_is_lexical(locale: str) -> None:
    stored, asked = LEXICAL_VARIANT[locale]
    cache = AnswerCache(BASE, threshold=0.90, similar_enabled=True)
    cache.store(stored, "an index is ...")
    result = cache.lookup(asked)
    assert result.outcome is CacheOutcome.SIMILAR, result
    assert result.value == "an index is ..."
    assert result.similarity >= 0.90
    assert "LEXICAL" in result.reason


@pytest.mark.parametrize("locale", LOCALES)
def test_synonyms_miss_because_the_signal_is_not_semantic(locale: str) -> None:
    """Two ways of saying the SAME thing with other words: the signal does not join them."""
    stored, asked = SYNONYMS[locale]
    cache = AnswerCache(BASE, threshold=0.92, similar_enabled=True)
    cache.store(stored, "the probe says whether the pod receives traffic")
    result = cache.lookup(asked)
    assert result.value is None and result.outcome is CacheOutcome.MISS, result
    assert result.similarity < 0.92
    assert str(result.similarity)[:4] in result.reason


@pytest.mark.parametrize("locale", LOCALES)
def test_the_confusable_pair_cannot_be_split_by_the_threshold(locale: str) -> None:
    """NEGATIVE RESULT, measured: reserving != charging, but the signal says they are equal.

    With the default threshold the 'similar' level serves the answer about RESERVING to a
    question about CHARGING. It is not a badly chosen threshold: a REPEATED question with
    other words scores LOWER than these two different questions, so no cut separates them.
    """
    reserve, charge = CONFUSABLE[locale]
    cache = AnswerCache(BASE, threshold=DEFAULT_THRESHOLD, similar_enabled=True)
    cache.store(reserve, "ANSWER ABOUT RESERVING")
    result = cache.lookup(charge)
    assert result.outcome is CacheOutcome.SIMILAR and result.value == "ANSWER ABOUT RESERVING", (
        "if this stops passing the signal now separates both questions: redo the "
        f"recommendation before touching the test -> {result}")
    assert result.similarity > DEFAULT_THRESHOLD

    same = similarity(*SAME_REWORDED[locale])
    assert result.similarity > same, (
        f"two different questions score more than the same question reworded: "
        f"{result.similarity} vs {same}")

    # and what really protects: by default the similar level is off
    assert SIMILAR_LEVEL_DEFAULT is False
    default = AnswerCache(BASE)
    default.store(reserve, "ANSWER ABOUT RESERVING")
    result = default.lookup(charge)
    assert result.value is None and result.outcome is CacheOutcome.MISS


# ── expiry by version: the whole point of the module ─────────────────────────


@pytest.mark.parametrize(
    ("field", "new_value"),
    [
        ("corpus_hash", "bbbb2222"),
        ("embedding_model", "openai/text-embedding-3-small"),
        ("embedding_version", "v2"),
        ("model_version", "anthropic/claude-opus-4"),
    ],
)
def test_a_changed_version_field_invalidates_and_names_only_that_field(
    cache_file: Path, field: str, new_value: str
) -> None:
    AnswerCache(BASE, cache_file).store("what is an index", "old")
    result = AnswerCache(version(**{field: new_value}), cache_file).lookup("what is an index")
    assert result.value is None, "an answer computed against another version is never returned"
    assert result.outcome is CacheOutcome.INVALIDATED
    assert field in result.reason
    assert repr(getattr(BASE, field)) in result.reason and repr(new_value) in result.reason
    others = [name for name in CacheVersion.field_names() if name != field]
    assert not any(name in result.reason for name in others), "only the changed field is named"


def test_an_invalidated_entry_does_not_come_back_through_similarity(cache_file: Path) -> None:
    """Not through the back door either: expired is expired on both levels."""
    AnswerCache(BASE, cache_file).store("what is an index in postgres", "old")
    cache = AnswerCache(version(corpus_hash="cccc"), cache_file, threshold=0.90, similar_enabled=True)
    result = cache.lookup("what is an index in postgresql")
    assert result.value is None, "an expired entry was served by the similar level"
    assert result.outcome is CacheOutcome.INVALIDATED and "corpus_hash" in result.reason
    assert cache.stats().entries == 0, "the expired neighbour is dropped on the spot"


def test_invalidate_drops_everything_and_reaches_the_disk(cache_file: Path) -> None:
    cache = AnswerCache(BASE, cache_file)
    for i in range(4):
        cache.store(f"question {i}", i)
    assert cache.invalidate("I rewrote box 04") == 4
    assert cache.invalidation_reason == "I rewrote box 04"
    assert cache.stats().entries == 0
    assert cache.lookup("question 0").outcome is CacheOutcome.MISS
    assert AnswerCache(BASE, cache_file).stats().entries == 0, "invalidate must reach the disk"


# ── the file ─────────────────────────────────────────────────────────────────


def test_without_a_path_nothing_is_written(tmp_path: Path) -> None:
    cache = AnswerCache(BASE)
    cache.store("question", "value")
    assert cache.load_status is LoadStatus.MEMORY_ONLY
    assert not list(tmp_path.iterdir())


def test_a_missing_file_starts_empty(cache_file: Path) -> None:
    assert not cache_file.exists()
    cache = AnswerCache(BASE, cache_file)
    assert cache.stats().entries == 0
    assert cache.lookup("hello").outcome is CacheOutcome.MISS
    assert cache.load_status is LoadStatus.MISSING
    assert "does not exist" in cache.load_reason


@pytest.mark.parametrize(
    "garbage",
    [
        b"\x00\x01\x02not json at all\xff\xfe",
        b'{"format": "cache-v1", "entries": [{"ke',
        b'{"hello": 1}',
        b'{"entries": "not a list"}',
        b"[1, 2, 3]",
        b"",
    ],
    ids=["bytes", "half-json", "json-without-entries", "entries-not-a-list", "json-list", "empty"],
)
def test_a_corrupt_file_degrades_to_empty_and_stays_usable(cache_file: Path, garbage: bytes) -> None:
    """Bytes that are not even text: the cache starts empty and says so, it does not blow up."""
    cache_file.write_bytes(garbage)
    cache = AnswerCache(BASE, cache_file)
    assert cache.stats().entries == 0, cache.load_reason
    assert cache.lookup("hello").outcome is CacheOutcome.MISS
    assert cache.load_status is LoadStatus.UNREADABLE
    assert "unreadable" in cache.load_reason
    cache.store("hello", "world")  # and it can still be used
    assert AnswerCache(BASE, cache_file).lookup("hello").value == "world"


def test_one_broken_entry_does_not_take_the_others_down(cache_file: Path) -> None:
    AnswerCache(BASE, cache_file).store("good", "value")
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    data["entries"] += [{"key": "x"}, 42, {"key": "y", "query": "q", "value": 1, "version": "v1", "saved_at": 1}]
    cache_file.write_text(json.dumps(data), encoding="utf-8")
    other = AnswerCache(BASE, cache_file)
    assert other.lookup("good").value == "value", other.load_reason
    assert other.discarded_on_load == 3
    assert "discarded" in other.load_reason


def test_entries_persist_between_instances(cache_file: Path) -> None:
    AnswerCache(BASE, cache_file).store("What is an INDEX?", {"text": "...", "n": 3})
    result = AnswerCache(BASE, cache_file).lookup("what is an index")
    assert result.outcome is CacheOutcome.EXACT
    assert result.value == {"text": "...", "n": 3}


def test_a_non_serialisable_value_stays_in_memory_and_keeps_the_file_valid(cache_file: Path) -> None:
    cache = AnswerCache(BASE, cache_file)
    cache.store("with a set", {1, 2, 3})  # a set is not JSON
    cache.store("normal", "it fits")
    assert cache.lookup("with a set").value == {1, 2, 3}, "it must still be there in memory"
    assert "not JSON serialisable" in cache.write_reason
    json.loads(cache_file.read_text(encoding="utf-8"))  # the file is still valid JSON
    other = AnswerCache(BASE, cache_file)
    assert other.lookup("normal").value == "it fits"
    assert other.lookup("with a set").outcome is CacheOutcome.MISS, "nothing is stored halfway"


def test_two_caches_on_the_same_file_never_corrupt_it(tmp_path: Path, cache_file: Path) -> None:
    """The last writer wins, but the file is always readable. No locking."""
    first = AnswerCache(BASE, cache_file)
    second = AnswerCache(BASE, cache_file)
    for i in range(10):
        first.store(f"question a{i}", f"value a{i}")
        second.store(f"question b{i}", f"value b{i}")
        json.loads(cache_file.read_text(encoding="utf-8"))  # never half written
    third = AnswerCache(BASE, cache_file)
    assert third.lookup("question b9").value == "value b9", third.load_reason
    assert not list(tmp_path.glob("*.tmp")), "temporary files were left behind"
    # and the known limit, written down so nobody discovers it in production:
    assert third.lookup("question a9").outcome is CacheOutcome.MISS, (
        "if this hits there is now merging between processes: update the KNOWN LIMITS")


def test_eviction_drops_the_oldest_above_the_maximum(cache_file: Path) -> None:
    cache = AnswerCache(BASE, cache_file, max_entries=3, clock=TickingClock())
    for i in range(5):
        cache.store(f"question {i}", i)
    stats = cache.stats()
    assert stats.entries == 3
    assert stats.evicted == 2
    assert cache.lookup("question 0").outcome is CacheOutcome.MISS, "the oldest had to go"
    assert cache.lookup("question 4").value == 4, "the newest had to stay"


def test_eviction_keeps_insertion_order_when_the_clock_does_not_tick() -> None:
    """A coarse clock (Windows ticks every ~15 ms) must still evict the oldest."""
    cache = AnswerCache(BASE, max_entries=2, clock=lambda: 5.0)
    for i in range(3):
        cache.store(f"question {i}", i)
    assert cache.lookup("question 0").outcome is CacheOutcome.MISS
    assert cache.lookup("question 2").value == 2


# ── accounting ───────────────────────────────────────────────────────────────


def test_stats_count_exact_and_similar_separately() -> None:
    cache = AnswerCache(BASE, threshold=0.90, similar_enabled=True)
    cache.store("what is an index in postgres", "an index is ...")
    cache.lookup("what is an index in postgres")  # exact
    cache.lookup("what is an index in postgresql")  # similar
    cache.lookup("how do I configure stripe")  # miss
    stats = cache.stats()
    assert (stats.exact, stats.similar, stats.misses) == (1, 1, 1)
    assert stats.lookups == 3
    assert stats.exact_rate and stats.similar_rate
    names = set(CacheStats.__dataclass_fields__) | set(stats.as_dict())
    assert not any("hit" in name for name in names), (
        "a single hit rate cannot exist: it would mix a certainty with a bet")
    assert stats.similar_enabled is True and stats.threshold == 0.90


def test_stats_count_invalidations_apart(cache_file: Path) -> None:
    AnswerCache(BASE, cache_file).store("what is an index", "old")
    cache = AnswerCache(version(corpus_hash="dddd"), cache_file)
    cache.lookup("what is an index")
    stats = cache.stats()
    assert stats.invalidated == 1 and stats.misses == 0
    assert stats.exact == 0, "an invalidation is not a hit"


def test_the_report_always_explains_what_happened(cache_file: Path) -> None:
    AnswerCache(BASE, cache_file).store("what is an index in postgres", "v")
    cache = AnswerCache(BASE, cache_file, threshold=0.90, similar_enabled=True)
    stale = AnswerCache(version(model_version="another"), cache_file)
    results = [
        cache.lookup("what is an index in postgres"),
        cache.lookup("what is an index in postgresql"),
        cache.lookup("nothing to do with this"),
        stale.lookup("what is an index in postgres"),
    ]
    assert [r.outcome for r in results] == [
        CacheOutcome.EXACT, CacheOutcome.SIMILAR, CacheOutcome.MISS, CacheOutcome.INVALIDATED]
    for result in results:
        assert result.key and len(result.reason) > 20
        assert isinstance(result.similarity, float)


# ── the version itself ───────────────────────────────────────────────────────


def test_the_current_version_carries_the_four_fields(engine: RetrievalEngine) -> None:
    current = CacheVersion.describe(engine.corpus.chunks, "anthropic/claude-haiku-4.5")
    assert set(current.as_dict()) == set(CacheVersion.field_names()) == {
        "corpus_hash", "embedding_model", "embedding_version", "model_version"}
    assert all(isinstance(v, str) and v for v in current.as_dict().values())
    assert current.corpus_hash == corpus_hash(engine.corpus.chunks)
    assert current.embedding_model == LOCAL_SIGNAL_NAME, "the local backend is not an embeddings model"


def test_an_answer_from_one_locale_corpus_is_never_served_for_the_other(
    engines: RetrievalEngineFactory, cache_file: Path
) -> None:
    """The corpora of both locales differ in content, so their versions differ too."""
    spanish = CacheVersion.describe(engines.get("es").corpus.chunks, "some/model")
    english = CacheVersion.describe(engines.get("en").corpus.chunks, "some/model")
    assert spanish.corpus_hash != english.corpus_hash
    AnswerCache(spanish, cache_file).store("what is an index", "respuesta")
    result = AnswerCache(english, cache_file).lookup("what is an index")
    assert result.outcome is CacheOutcome.INVALIDATED and "corpus_hash" in result.reason


def test_the_openrouter_backend_is_named_in_the_version() -> None:
    chunks = [Chunk.of("text", "04 · Databases", "t")]
    assert CacheVersion.describe(chunks, "m", "openrouter").embedding_model != LOCAL_SIGNAL_NAME
    assert CacheVersion.describe(chunks, "m", "local") != CacheVersion.describe(chunks, "m", "openrouter")


def test_the_corpus_hash_changes_when_the_content_changes() -> None:
    """A different paragraph with the same number of chunks must give another hash."""
    one = [Chunk.of("text a", "04 · Databases", "t")]
    other = [Chunk.of("text b", "04 · Databases", "t")]
    assert corpus_hash(one) != corpus_hash(other)
    assert corpus_hash(one) == corpus_hash(one), "the hash must be stable"
    assert len(corpus_hash(one)) == HASH_LENGTH
    # the separator keeps two adjacent chunks from merging into the same bytes
    split_a = [Chunk.of("a\nb", "04 · Databases", "t"), Chunk.of("c", "04 · Databases", "u")]
    split_b = [Chunk.of("a", "04 · Databases", "t"), Chunk.of("b\nc", "04 · Databases", "u")]
    assert corpus_hash(split_a) != corpus_hash(split_b)
