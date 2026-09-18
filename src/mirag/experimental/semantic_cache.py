"""A two-level answer cache that expires by version. EXPERIMENTAL: off the production path.

THE PROBLEM IT SOLVES, AND THE ONE IT CREATES
    Reusing an answer already computed saves a model call. It is also the easiest way to
    serve a FALSE answer: if the corpus changed since it was stored, that answer no longer
    comes from the documents that exist now. It is not stale, it is WRONG. So every entry
    records what it was computed against, and an entry with another version is never served
    - not degraded, not with a warning: not served.

TWO LEVELS, COUNTED SEPARATELY
    exact    the normalised query (lower case, no accents, no extra spaces, no question or
             exclamation marks) is identical to a stored one. Cheap and safe: if both strings
             are the same question, the answer holds.
    similar  cosine over the local lexical signal. It is the DANGEROUS level and it is born
             OFF: see the measured note at the end of this module.

    They are never merged into a single "hit rate". An exact hit is a certainty and a
    similarity hit is a bet; averaging them hides precisely what has to be watched.

THE SIGNAL IS NOT SEMANTIC
    The module is named after its feature switch (``semantic_cache``), but the similarity
    level uses :class:`~mirag.retrieval.vectors.LocalHashVectorStore`: hashed CHARACTER
    n-grams. It measures how many little pieces of letters two texts share, nothing else.
    Measured: ``readiness probe`` against its synonym ``health check`` scores 0.493, about
    the same as two unrelated texts. Nowhere else in this module is it called "semantic".

WHAT IS STORED
    A flat JSON file. If the file is missing, half written or corrupt, the cache starts EMPTY
    and says so in ``load_reason``: a cache that blows up on start is worse than no cache.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields
from enum import StrEnum
from pathlib import Path
from typing import Any

from mirag.core.text import normalize, short_hash
from mirag.retrieval.vectors import (
    EMBEDDING_MODEL,
    EMBEDDING_VERSION,
    LocalHashVectorStore,
    VectorStore,
)

FILE_FORMAT = "cache-v1"
"""If the shape of the file changes, change this."""
DEFAULT_THRESHOLD = 0.92
"""Minimum similarity for the 'similar' level to count as a hit."""
DEFAULT_MAX_ENTRIES = 500
HASH_LENGTH = 16
"""Truncated sha256: 16 hex characters are enough to detect changes (not for integrity)."""
LOCAL_SIGNAL_NAME = "local-hash-ngrams"
"""What ``embedding_model`` says with the local backend: it is NOT an embeddings model."""

SIMILAR_LEVEL_DEFAULT = False
"""The similarity level is born off. Not generic caution, a measurement: two DIFFERENT
questions ("... when reserving" / "... when charging") score 0.949 (es) / 0.926 (en), above the
0.92 threshold, while two phrasings of the SAME question score 0.873 (es) / 0.883 (en). No
threshold separates them because the signal does not look at meaning. See the note at the end."""

_QUESTION_MARKS = "¿?¡!"
_TRAILING_PUNCTUATION = " .,;:"


def corpus_hash(chunks: Iterable[Any]) -> str:
    """Truncated sha256 of the CONTENT of the corpus (anything with a ``.text``).

    It hashes the texts, not file dates nor how many chunks there are: two corpora with the
    same number of chunks and one changed paragraph must give different hashes, which is
    exactly the case that makes a cached answer stop being true. The NUL separator keeps two
    adjacent chunks from merging (``"a\\nb" + "c"`` vs ``"a" + "b\\nc"``).
    """
    return short_hash("".join(chunk.text + "\x00" for chunk in chunks), HASH_LENGTH)


def cache_key(query: object) -> str:
    """The same question written another way must give the same key.

    :func:`~mirag.core.text.normalize` removes case and accents, which is what searching the
    corpus needs, but it keeps punctuation: ``¿qué es un índice?`` and ``que es un indice``
    would be two entries for one question. Here question/exclamation marks and trailing
    punctuation are removed as well.

    And NOTHING else, on purpose: ``a == b`` and ``a = b`` remain different queries, because
    in a question about code that symbol is exactly what is being asked.
    """
    norm = normalize(str(query))
    norm = "".join(" " if c in _QUESTION_MARKS else c for c in norm)  # a space: never glue words
    return short_hash(" ".join(norm.split()).strip(_TRAILING_PUNCTUATION), HASH_LENGTH)


# ── version ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CacheVersion:
    """What an answer was computed against. Any difference means the answer is not served."""

    corpus_hash: str
    embedding_model: str
    embedding_version: str
    model_version: str

    @classmethod
    def describe(cls, chunks: Iterable[Any], model: str, vector_backend: str = "local") -> CacheVersion:
        """The version of the answers computed right now.

        ``embedding_model`` keeps the name of the original contract, but with the local
        backend it is NOT an embeddings model: it is the lexical n-gram signal, and the value
        says so (``local-hash-ngrams``) so nobody reads the field and assumes otherwise.
        """
        backend = (vector_backend or "local").strip().lower()
        return cls(
            corpus_hash=corpus_hash(chunks),
            embedding_model=EMBEDDING_MODEL if backend == "openrouter" else LOCAL_SIGNAL_NAME,
            embedding_version=EMBEDDING_VERSION,
            model_version=model,
        )

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(f.name for f in fields(cls))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> CacheVersion:
        """Tolerant on purpose: a missing field becomes ``""`` and therefore never matches."""
        if not isinstance(data, Mapping):
            raise TypeError(f"a version must be a mapping, not {type(data).__name__}")
        return cls(**{name: str(data.get(name) or "") for name in cls.field_names()})

    def as_dict(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in self.field_names()}

    def differences(self, other: CacheVersion) -> list[str]:
        """Which fields do not match, with both values, so it can be said."""
        return [
            f"{name} ({getattr(self, name)!r} → {getattr(other, name)!r})"
            for name in self.field_names()
            if getattr(self, name) != getattr(other, name)
        ]


# ── value objects ────────────────────────────────────────────────────────────


class CacheOutcome(StrEnum):
    EXACT = "exact"
    SIMILAR = "similar"
    MISS = "miss"
    INVALIDATED = "invalidated"


class LoadStatus(StrEnum):
    MEMORY_ONLY = "memory_only"
    """No path: the cache lives only in memory."""
    MISSING = "missing"
    UNREADABLE = "unreadable"
    LOADED = "loaded"


@dataclass(frozen=True, slots=True)
class CacheEntry:
    key: str
    """Truncated sha256 of the normalised query."""
    query: str
    """The query as it arrived (whitespace collapsed), so it can be inspected."""
    value: Any
    """What is cached; it must be JSON serialisable to reach the disk."""
    version: CacheVersion
    saved_at: float
    """Clock reading when stored: it is what decides eviction."""
    similarity: float = 1.0
    """How similar it was when it came in. Always 1.0 today: only the literal query is
    stored, never a neighbour."""

    def to_json(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "query": self.query,
            "value": self.value,
            "version": self.version.as_dict(),
            "saved_at": self.saved_at,
            "similarity": self.similarity,
        }

    @classmethod
    def from_json(cls, raw: Mapping[str, Any]) -> CacheEntry:
        """Raises ``KeyError``/``TypeError``/``ValueError`` on a broken entry."""
        return cls(
            key=str(raw["key"]),
            query=str(raw["query"]),
            value=raw["value"],
            version=CacheVersion.from_mapping(raw["version"]),
            saved_at=float(raw["saved_at"]),
            similarity=float(raw.get("similarity", 1.0)),
        )


@dataclass(frozen=True, slots=True)
class CacheLookup:
    """What a lookup returned, and ALWAYS why."""

    value: Any
    outcome: CacheOutcome
    similarity: float
    reason: str
    key: str

    @property
    def hit(self) -> bool:
        return self.outcome in (CacheOutcome.EXACT, CacheOutcome.SIMILAR)


@dataclass(frozen=True, slots=True)
class CacheStats:
    """Both levels separately, and no figure that mixes them.

    There is deliberately no global hit rate: adding an exact hit (safe) to a similarity hit
    (a bet on shared characters) yields a number that rises exactly when the risk rises.
    """

    entries: int
    exact: int
    similar: int
    misses: int
    invalidated: int
    stored: int
    evicted: int
    threshold: float
    max_entries: int
    similar_enabled: bool
    version: CacheVersion
    path: str | None
    load_reason: str

    @property
    def lookups(self) -> int:
        return self.exact + self.similar + self.misses + self.invalidated

    def _rate(self, count: int) -> float:
        return round(count / self.lookups, 4) if self.lookups else 0.0

    @property
    def exact_rate(self) -> float:
        return self._rate(self.exact)

    @property
    def similar_rate(self) -> float:
        return self._rate(self.similar)

    def as_dict(self) -> dict[str, Any]:
        return {
            "entries": self.entries,
            "lookups": self.lookups,
            "exact": self.exact,
            "similar": self.similar,
            "misses": self.misses,
            "invalidated": self.invalidated,
            "exact_rate": self.exact_rate,
            "similar_rate": self.similar_rate,
            "stored": self.stored,
            "evicted": self.evicted,
            "threshold": self.threshold,
            "max_entries": self.max_entries,
            "similar_enabled": self.similar_enabled,
            "version": self.version.as_dict(),
            "path": self.path,
            "load_reason": self.load_reason,
        }


@dataclass(slots=True)
class _Counters:
    exact: int = 0
    similar: int = 0
    misses: int = 0
    invalidated: int = 0
    stored: int = 0
    evicted: int = 0


# ── the cache ────────────────────────────────────────────────────────────────


class AnswerCache:
    """Two levels, one version and one file. None of it can take the caller down.

    ``path=None`` is an IN-MEMORY cache on purpose: writing to disk without anyone asking
    leaves files around the project. Whoever wants persistence passes a path.
    """

    def __init__(
        self,
        version: CacheVersion,
        path: Path | None = None,
        threshold: float = DEFAULT_THRESHOLD,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        similar_enabled: bool = SIMILAR_LEVEL_DEFAULT,
        clock: Callable[[], float] = time.time,
        store_factory: Callable[[], VectorStore] = LocalHashVectorStore,
    ) -> None:
        self.version = version
        self.path = Path(path) if path else None
        self.threshold = float(threshold)
        self.max_entries = int(max_entries)
        self.similar_enabled = bool(similar_enabled)
        self._clock = clock
        self._store_factory = store_factory
        self.load_status = LoadStatus.MEMORY_ONLY
        self.load_reason = ""
        self.discarded_on_load = 0
        self.write_reason = ""
        self.invalidation_reason = ""
        self._entries: dict[str, CacheEntry] = {}  # key -> entry, in insertion order
        self._store: VectorStore | None = None  # the similarity signal, built only when needed
        self._indexed_keys: list[str] | None = None  # None = must reindex
        self._counters = _Counters()
        self._load()

    # ── lookup ───────────────────────────────────────────────────────────────

    def lookup(self, query: object) -> CacheLookup:
        key = cache_key(query)
        entry = self._entries.get(key)

        if entry is not None:
            if changed := entry.version.differences(self.version):
                # Dropped on the spot: an entry computed against another version will never
                # be served again, and keeping it only makes it come back here.
                self._drop(key)
                return CacheLookup(
                    None, CacheOutcome.INVALIDATED, 1.0,
                    f"there was a stored answer but {'; '.join(changed)} changed: it was computed "
                    "against something else and would be wrong",
                    key,
                )
            self._counters.exact += 1
            return CacheLookup(entry.value, CacheOutcome.EXACT, 1.0,
                               "the normalised query is identical to a stored one", key)

        if not self.similar_enabled:
            self._counters.misses += 1
            return CacheLookup(
                None, CacheOutcome.MISS, 0.0,
                "no identical query is stored and the similarity level is off (it measures "
                "characters, not meaning: see SIMILAR_LEVEL_DEFAULT)",
                key,
            )

        neighbour, similarity = self._most_similar(query)
        if neighbour is None or similarity < self.threshold:
            self._counters.misses += 1
            return CacheLookup(
                None, CacheOutcome.MISS, round(similarity, 4),
                f"the most similar stored query scores {similarity:.3f} < threshold {self.threshold:.2f}",
                key,
            )

        if changed := neighbour.version.differences(self.version):
            # not through the back door either: expired is expired on both levels
            self._drop(neighbour.key)
            return CacheLookup(
                None, CacheOutcome.INVALIDATED, round(similarity, 4),
                f"the similar entry ({similarity:.3f}) has another version: {'; '.join(changed)}",
                key,
            )

        self._counters.similar += 1
        return CacheLookup(
            neighbour.value, CacheOutcome.SIMILAR, round(similarity, 4),
            f"no identical query; serving the answer to {neighbour.query!r} with LEXICAL "
            f"similarity {similarity:.3f} ≥ {self.threshold:.2f}. Shared characters are not the "
            "same question",
            key,
        )

    # ── store, evict, invalidate ─────────────────────────────────────────────

    def store(self, query: object, value: Any) -> None:
        key = cache_key(query)
        self._entries.pop(key, None)  # rewriting moves it to the end
        self._entries[key] = CacheEntry(key, " ".join(str(query).split()), value, self.version, self._clock())
        self._indexed_keys = None
        self._counters.stored += 1
        self._evict()
        self._persist()

    def _evict(self) -> None:
        """Above ``max_entries`` the OLDEST by storage time goes.

        FIFO, not LRU: accesses are not counted. With a limit of hundreds of entries the
        difference does not pay for counters that would have to be persisted and that drift
        apart between two processes. ``min`` keeps the first on ties, which is the insertion
        order: a coarse clock (Windows ticks every ~15 ms) still evicts the oldest.
        """
        while len(self._entries) > self.max_entries:
            oldest = min(self._entries.values(), key=lambda e: e.saved_at)
            self._entries.pop(oldest.key, None)
            self._indexed_keys = None
            self._counters.evicted += 1

    def invalidate(self, reason: str = "") -> int:
        """Drop EVERY entry and return how many there were.

        This is the manual button ("I just rewrote half of box 04"). Version expiry does not
        need it: :meth:`lookup` never returns anything whose version does not match, so the
        cache cannot serve something stale because somebody forgot this button.
        """
        count = len(self._entries)
        self._entries.clear()
        self._indexed_keys = None
        self._store = None
        self.invalidation_reason = reason or "manual invalidation"
        self._persist()
        return count

    def _drop(self, key: str) -> None:
        self._entries.pop(key, None)
        self._indexed_keys = None
        self._counters.invalidated += 1
        self._persist()

    # ── the similarity level ─────────────────────────────────────────────────

    def _most_similar(self, query: object) -> tuple[CacheEntry | None, float]:
        """The closest stored entry and its similarity. Reindexes only if the cache changed."""
        if not self._entries:
            return None, 0.0
        if self._indexed_keys is None or self._store is None:
            self._indexed_keys = list(self._entries)
            self._store = self._store_factory()
            self._store.index([self._entries[k].query for k in self._indexed_keys])
        hits = self._store.search(str(query), k=1)
        if not hits:
            return None, 0.0  # cosine <= 0: nothing in common
        index, score = hits[0]
        if index >= len(self._indexed_keys):
            return None, 0.0
        return self._entries.get(self._indexed_keys[index]), float(score)

    # ── disk ─────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self.path is None:
            self.load_status = LoadStatus.MEMORY_ONLY
            self.load_reason = "no path: the cache lives only in memory"
            return
        if not self.path.exists():
            self.load_status = LoadStatus.MISSING
            self.load_reason = f"{self.path.name} does not exist: starting empty"
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            raw_entries = data["entries"]
            if not isinstance(raw_entries, list):
                raise ValueError("'entries' is not a list")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # Anything: broken JSON, bytes that are not text, a dict without 'entries',
            # permissions. An unreadable cache is an empty cache, not an exception.
            self.load_status = LoadStatus.UNREADABLE
            self.load_reason = f"{self.path.name} is unreadable ({type(exc).__name__}): starting empty"
            return
        recovered: dict[str, CacheEntry] = {}
        broken = 0
        for raw in raw_entries:
            try:
                entry = CacheEntry.from_json(raw)
            except (KeyError, TypeError, ValueError):
                broken += 1  # one bad entry does not take the others down
                continue
            recovered[entry.key] = entry
        # NOTE: entries with another version are loaded on purpose. They are never served,
        # but keeping them lets lookup() say WHICH field changed instead of a mute 'miss'
        # that looks as if the cache never stored anything.
        self._entries = recovered
        self.discarded_on_load = broken
        self.load_status = LoadStatus.LOADED
        self.load_reason = f"{len(recovered)} entries read from {self.path.name}" + (
            f"; {broken} discarded as unreadable" if broken else ""
        )

    def _persist(self) -> None:
        """Write the whole file, atomically, without propagating failures.

        tmp + ``os.replace`` so that a process dying halfway never leaves a truncated JSON:
        either the previous file or the new one is there, never half of one.
        """
        if self.path is None:
            return
        rows: list[dict[str, Any]] = []
        skipped = 0
        for entry in self._entries.values():
            row = entry.to_json()
            try:
                json.dumps(row)
            except (TypeError, ValueError):
                skipped += 1  # not JSON serialisable: it lives in memory only
                continue
            rows.append(row)
        payload = {"format": FILE_FORMAT, "version": self.version.as_dict(), "entries": rows}
        tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.path)
            self.write_reason = f"{len(rows)} entries written" + (
                f"; {skipped} not JSON serialisable" if skipped else ""
            )
        except OSError as exc:
            self.write_reason = f"could not write ({type(exc).__name__}: {exc})"
            with contextlib.suppress(OSError):
                tmp.unlink()

    # ── accounting ───────────────────────────────────────────────────────────

    def stats(self) -> CacheStats:
        c = self._counters
        return CacheStats(
            entries=len(self._entries),
            exact=c.exact,
            similar=c.similar,
            misses=c.misses,
            invalidated=c.invalidated,
            stored=c.stored,
            evicted=c.evicted,
            threshold=self.threshold,
            max_entries=self.max_entries,
            similar_enabled=self.similar_enabled,
            version=self.version,
            path=str(self.path) if self.path else None,
            load_reason=self.load_reason,
        )


# KNOWN LIMITS, so this is not sold as more than it is:
#
#  · THE 'SIMILAR' LEVEL DOES NOT SEPARATE DIFFERENT QUESTIONS. Measured with the local
#    signal (character n-grams, dim=512):
#        es "...race condition al reservar el inventario" vs "...al cobrar el inventario"
#        (DIFFERENT questions, different answers)                          → 0.949
#        en "...when reserving the inventory" vs "...when charging the inventory" → 0.926
#        es "idempotencia en pagos" vs "idempotencia en los pagos" (SAME)   → 0.873
#        en "idempotency in payments" vs "idempotency in the payments"      → 0.883
#        "readiness probe" vs "health check" (the same, in synonyms)        → 0.493
#    Different questions score HIGHER than several identical ones: no threshold splits
#    them, because what is measured is shared letters and two questions that only change
#    the verb share almost all of them. Hence SIMILAR_LEVEL_DEFAULT = False. Switching it on
#    is useful for typos and plurals over very short, controlled queries, and nothing else.
#  · Eviction is FIFO by storage time, not LRU: a heavily used entry can go before one
#    nobody ever asked for.
#  · Two processes on the same file do not corrupt it (atomic write) but the last writer
#    wins: what the other stored in between is lost. No locking, no merging. Fine for one
#    process; for several, this is not the piece.
#  · CacheVersion.describe() describes the CONFIGURED backend. If openrouter were configured
#    and the vector factory fell back to local because of a network failure, the version
#    would not reflect it.
#  · The value must be JSON serialisable to persist. If it is not, the entry stays in
#    memory and ``write_reason`` says so: nothing is stored halfway.
