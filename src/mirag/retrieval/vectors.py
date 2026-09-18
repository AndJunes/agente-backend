"""Retrieval vectors behind one interface with two backends.

The default (:class:`LocalHashVectorStore`) is NOT embeddings: it is a LEXICAL signal of
characters. It hashes character n-grams and compares with cosine, so it measures "how many
little pieces of letters do these two texts share?" and nothing else. That adds three real
things to the word-based ranker: tolerance to typos (``postgress`` still lands near
``postgres``), partial word overlap (``index``/``indexes``/``indexing``) and mixed
Spanish-English when both forms look alike (``latencia``/``latency``).

It does NOT add semantics, which is exactly what people assume when they read "vector":
it does not join ``health check`` with ``readiness probe``. For that you need the other
backend, which calls a real embeddings model: born off (money, latency and a key), behind
the offline lock, and with an ingestion cache.
"""

from __future__ import annotations

import json
import math
import urllib.request
import zlib
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from mirag.core.text import normalize, short_hash

EMBEDDING_VERSION = "v1"
"""Change it when the way vectors are built or stored changes: it invalidates the cache."""
EMBEDDING_MODEL = "openai/text-embedding-3-small"
EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
BATCH = 64

Hit = tuple[int, float]


def cosine_top_k(query: dict[int, float], vectors: Sequence[Sequence[float]], k: int) -> list[Hit]:
    """Cosine = dot product, because everything arrives normalised to norm 1.

    The query is sparse (``{index: weight}``) and the documents dense: each document costs
    the ~30 dimensions the query touches, not all of them.
    """
    if not query or not vectors:
        return []
    pairs = []
    for i, doc in enumerate(vectors):
        score = sum(weight * doc[j] for j, weight in query.items() if j < len(doc))
        if score > 0:  # signed hashing yields negatives: that means "nothing in common"
            pairs.append((i, min(1.0, score)))
    pairs.sort(key=lambda p: (-p[1], p[0]))  # the index breaks ties: reproducible
    return pairs[:k]


class VectorStore(ABC):
    """The common interface. The only thing the rest of the project may rely on."""

    name = "base"

    def __init__(self) -> None:
        self.texts: list[str] = []
        self.reason = ""
        """Why it could not be used, if it could not."""
        self.fallback: str | None = None
        """Set by the factory when this store is plan B."""

    @property
    def available(self) -> bool:
        return True

    @property
    @abstractmethod
    def ready(self) -> bool:
        """There are usable vectors. Indexing may fail without raising."""

    @abstractmethod
    def index(self, texts: Sequence[str]) -> None: ...

    @abstractmethod
    def search(self, query: str, k: int = 5) -> list[Hit]: ...


class LocalHashVectorStore(VectorStore):
    """Local lexical signal: hashed character n-grams + cosine. No network, free.

    The hash is ``zlib.crc32``, not Python's ``hash()``, which is randomised per process by
    PYTHONHASHSEED: vectors would change between runs and a green test would turn red.

    NOISE FLOOR, measured: with dim=512 a query with NOTHING in common scores ~0.10 instead
    of 0, while a real match scores ~0.49. The ranking holds (4.8x margin); reading the score
    as a probability does not. What the ranker consumes is the ORDER, not the number.
    """

    name = "local"

    def __init__(self, dim: int = 512, n: int = 3) -> None:
        super().__init__()
        self.dim = dim
        self.n = n
        self._vectors: list[list[float]] = []

    @property
    def ready(self) -> bool:
        return bool(self._vectors)

    def _ngrams(self, text: str) -> list[str]:
        padded = " " + " ".join(normalize(text).split()) + " "
        if len(padded) <= 2:
            return []
        return [padded[i : i + self.n] for i in range(len(padded) - self.n + 1)]

    def _weights(self, text: str) -> dict[int, float]:
        """``{dimension: weight}`` normalised to norm 1, with the signed hashing trick.

        Without the sign, colliding n-grams always reinforce each other and the whole corpus
        ends up looking like everything; with it, collisions cancel out on average.
        """
        vector: dict[int, float] = {}
        for gram in self._ngrams(text):
            h = zlib.crc32(gram.encode())
            i = h % self.dim
            vector[i] = vector.get(i, 0.0) + (1.0 if h & 0x80000000 else -1.0)
        norm = math.sqrt(sum(x * x for x in vector.values()))
        if not norm:
            return {}
        return {i: x / norm for i, x in vector.items() if x}

    def vector(self, text: str) -> list[float]:
        dense = [0.0] * self.dim
        for i, x in self._weights(text).items():
            dense[i] = x
        return dense

    def index(self, texts: Sequence[str]) -> None:
        self.texts = list(texts)
        self._vectors = [self.vector(t) for t in self.texts]

    def search(self, query: str, k: int = 5) -> list[Hit]:
        return cosine_top_k(self._weights(query), self._vectors, k)


Opener = Callable[..., Any]


class OpenRouterVectorStore(VectorStore):
    """Real embeddings through OpenRouter. Optional, off by default and fault tolerant.

    Two non-negotiable rules: the lock first (offline or without a key, not even a socket),
    and nothing propagates - network, provider or JSON failures are recorded in ``reason``
    and the factory falls back to the local store. Degraded retrieval is a nuisance;
    broken retrieval is an outage.
    """

    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        offline: bool,
        cache_dir: Path,
        model: str = EMBEDDING_MODEL,
        timeout_s: float = 30.0,
        opener: Opener | None = None,
    ) -> None:
        super().__init__()
        self._api_key = api_key
        self._offline = offline
        self.cache_dir = cache_dir
        self.model = model
        self.timeout_s = timeout_s
        self.calls = 0
        self._open = opener or urllib.request.urlopen
        self._vectors: list[list[float]] = []

    @property
    def ready(self) -> bool:
        return bool(self._vectors)

    def impediment(self) -> str:
        """Why the provider can NOT be called right now, or ``""``."""
        if self._offline:
            return "MIRAG_OFFLINE is on: OpenRouter is not called"
        if not self._api_key:
            return "OPENROUTER_API_KEY is not set"
        return ""

    @property
    def available(self) -> bool:
        return not self.impediment()

    @staticmethod
    def corpus_hash(texts: Sequence[str]) -> str:
        return short_hash("\n".join(texts))

    def cache_path(self, corpus_hash: str) -> Path:
        return self.cache_dir / corpus_hash / (self.model.replace("/", "_") + ".json")

    def _read_cache(self, corpus_hash: str) -> list[list[float]] | None:
        try:
            data = json.loads(self.cache_path(corpus_hash).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None  # valid JSON of another shape is a miss too, not an AttributeError
        if (
            data.get("version") != EMBEDDING_VERSION
            or data.get("model") != self.model
            or data.get("corpus_hash") != corpus_hash
        ):
            return None
        vectors = data.get("vectors")
        if not isinstance(vectors, list) or len(vectors) != len(self.texts):
            return None
        return vectors

    def _write_cache(self, corpus_hash: str, vectors: list[list[float]]) -> None:
        path = self.cache_path(corpus_hash)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"version": EMBEDDING_VERSION, "model": self.model,
                            "corpus_hash": corpus_hash, "vectors": vectors}),
                encoding="utf-8",
            )
        except OSError as exc:
            self.reason = f"could not write the cache: {exc}"

    def _request(self, texts: Sequence[str]) -> list[list[float]]:
        """Raw vectors. It carries the lock too: this is the ONLY socket of the module."""
        if impediment := self.impediment():
            raise RuntimeError(impediment)
        out: list[list[float]] = []
        for start in range(0, len(texts), BATCH):
            batch = list(texts[start : start + BATCH])
            request = urllib.request.Request(
                EMBEDDINGS_URL,
                data=json.dumps({"model": self.model, "input": batch}).encode("utf-8"),
                headers={"Authorization": "Bearer " + self._api_key, "Content-Type": "application/json"},
            )
            self.calls += 1
            with self._open(request, timeout=self.timeout_s) as response:
                payload = json.loads(response.read())
            data = payload.get("data")
            if not isinstance(data, list) or len(data) != len(batch):
                # a short batch is never padded with zeros: indices would drift from texts
                raise ValueError(f"the provider returned {len(data or [])} vectors for {len(batch)} texts")
            for item in sorted(data, key=lambda d: d.get("index", 0)):
                vector = item.get("embedding")
                if not isinstance(vector, list) or not vector:
                    raise ValueError("an entry of 'data' has no 'embedding'")
                out.append([float(x) for x in vector])
        return out

    @staticmethod
    def _normalised(vector: Sequence[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector] if norm else list(vector)

    def index(self, texts: Sequence[str]) -> None:
        self.texts = list(texts)
        self._vectors = []
        self.reason = ""
        if not self.texts:
            return
        corpus_hash = self.corpus_hash(self.texts)
        if (cached := self._read_cache(corpus_hash)) is not None:
            self._vectors = [self._normalised(v) for v in cached]
            return  # cache: zero calls, zero cost
        if impediment := self.impediment():
            self.reason = impediment
            return
        try:
            raw = self._request(self.texts)
        except Exception as exc:  # deliberately broad: none of these is worth an outage
            self.reason = f"{type(exc).__name__}: {exc}"
            return
        self._vectors = [self._normalised(v) for v in raw]
        self._write_cache(corpus_hash, raw)

    def search(self, query: str, k: int = 5) -> list[Hit]:
        """There IS one call per query here. The cache only covers ingestion."""
        if not self._vectors or not query.strip():
            return []
        if impediment := self.impediment():
            self.reason = impediment
            return []
        try:
            vector = self._normalised(self._request([query])[0])
        except Exception as exc:
            self.reason = f"{type(exc).__name__}: {exc}"
            return []
        return cosine_top_k(dict(enumerate(vector)), self._vectors, k)


class VectorStoreFactory:
    """Returns the store that applies. Ask for openrouter and it cannot be used: local.

    The fallback reason goes into ``.fallback`` instead of a log: the trace must be able to
    say "openrouter was not used because X", the same way the feature gate explains itself.
    """

    def __init__(self, backend: str, api_key: str = "", offline: bool = True, cache_dir: Path | None = None) -> None:
        self.backend = (backend or "local").strip().lower()
        self._api_key = api_key
        self._offline = offline
        self._cache_dir = cache_dir or Path(".")

    def create(self, texts: Sequence[str] | None = None) -> VectorStore:
        if self.backend != "openrouter":
            local = LocalHashVectorStore()
            if texts is not None:
                local.index(texts)
            return local
        remote = OpenRouterVectorStore(self._api_key, self._offline, self._cache_dir)
        reason = remote.impediment()
        if not reason:
            if texts is None:
                return remote
            remote.index(texts)
            if remote.ready:
                return remote
            reason = remote.reason or "the vectors could not be obtained"
        local = LocalHashVectorStore()
        local.fallback = f"openrouter discarded: {reason}"
        if texts is not None:
            local.index(texts)
        return local
