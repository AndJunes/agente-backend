"""Per-chunk metadata, and the filter that decides where retrieval looks.

WHAT EXISTS AND WHAT DOES NOT (measured on the corpus, not assumed)

    domain          YES      the box. 19 values.
    subdomain       DERIVED  the syllabus line exists in 19/19 files and declares the
                             vocabulary; the chunk -> subcategory assignment is made here by
                             word matching. Nobody wrote it by hand: check coverage().
    technology      DERIVED  keyword dictionary. The corpus has no 'technology' field.
    language        PARTIAL  from the tags of the code fences; many are untagged.
    artifact_type   DERIVED  from which index the chunk falls in and what it contains.
    difficulty      NONE     0 occurrences in the corpus.
    status          NONE     0 occurrences as a field.
    version         NONE     0 occurrences as a field.

The last three are declared and are ``None`` on purpose: knowing they do not exist is more
useful than filling them with something invented.

THE FILTER SAYS WHEN IT FAILS
    Falling back to the full index silently hides that the filter did not work. Here the
    outcome carries ``fell_back`` and a reason, so the trace and the UI can say "the whole
    corpus was searched because the filter ran out of chunks".
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

from mirag.core.text import normalize
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.lexicon import Lexicon
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus

if TYPE_CHECKING:
    from mirag.retrieval.plan import RetrievalPlan

# A short, hand-written list: every entry was checked against the corpus. This is NOT
# semantic detection, it is word matching. Technology names are language neutral.
TECHNOLOGIES: dict[str, str] = {
    "PostgreSQL": r"postgres|postgresql|psql",
    "MySQL": r"\bmysql\b|mariadb",
    "Redis": r"\bredis\b",
    "MongoDB": r"\bmongo",
    "Kafka": r"\bkafka\b",
    "RabbitMQ": r"rabbitmq|\bamqp\b",
    "Elasticsearch": r"elasticsearch|opensearch",
    "Docker": r"\bdocker\b|dockerfile",
    "Kubernetes": r"kubernetes|\bk8s\b|kubectl",
    "S3": r"\bs3\b|object storage",
    "Stripe": r"\bstripe\b",
    "JWT": r"\bjwt\b|json web token",
    "OAuth": r"oauth|openid",
    "gRPC": r"\bgrpc\b",
    "GraphQL": r"graphql",
    "Terraform": r"terraform",
    "Prometheus": r"prometheus",
    "OpenTelemetry": r"opentelemetry|\botel\b",
    "Nginx": r"\bnginx\b",
    "Python": r"\bpython\b",
    "Node.js": r"node\.js|nodejs|\bnpm\b",
}

ARTIFACT_TYPES = ("concept", "card", "implementation", "table", "failure", "anti_pattern")

# What models (and older plans) call each artifact type, in both languages.
ARTIFACT_TYPE_ALIASES: dict[str, str] = {
    "concept": "concept", "concepto": "concept",
    "card": "card", "ficha": "card",
    "implementation": "implementation", "implementacion": "implementation",
    "table": "table", "tabla": "table",
    "failure": "failure", "fallo": "failure",
    "anti_pattern": "anti_pattern", "anti-pattern": "anti_pattern", "antipatron": "anti_pattern",
}
FILTERABLE_TYPES = frozenset({"card", "failure", "anti_pattern", "concept", "implementation"})


def canonical_artifact_type(raw: str) -> str | None:
    return ARTIFACT_TYPE_ALIASES.get(normalize(str(raw)).strip())


@dataclass(frozen=True, slots=True)
class ChunkMetadata:
    domain: str
    domain_name: str
    subdomains: tuple[str, ...] = ()
    technologies: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    artifact_types: tuple[str, ...] = ()
    # declared on purpose, with no source in the corpus:
    difficulty: str | None = None
    status: str | None = None
    version: str | None = None


class MetadataExtractor:
    """Derives the metadata of every chunk of one corpus. Everything derived, nothing invented."""

    def __init__(self, corpus: KnowledgeCorpus, lexicon: Lexicon) -> None:
        self._corpus = corpus
        self._synonyms = lexicon.mapping("subdomain_synonyms")
        self._card_line = re.compile(rf"^> \*\*{re.escape(corpus.format.card_marker)}\*\*", re.MULTILINE)
        self._anti_label = corpus.format.field("anti_pattern")
        self._of = lru_cache(maxsize=8192)(self._compute)

    def of(self, chunk: Chunk) -> ChunkMetadata:
        return self._of(chunk)

    def _compute(self, chunk: Chunk) -> ChunkMetadata:
        technologies = tuple(n for n, p in TECHNOLOGIES.items() if re.search(p, chunk.text, re.IGNORECASE))
        languages = tuple(dict.fromkeys(re.findall(r"^```([a-z]+)", chunk.text, re.MULTILINE)))
        types = ["concept"]
        if self._card_line.search(chunk.text):
            types.append("card")
        if "```" in chunk.text:
            types.append("implementation")
        if re.search(r"^\|.*\|", chunk.text, re.MULTILINE):
            types.append("table")
        if self._corpus.parser.is_failure_title(chunk.title):
            types.append("failure")
        if self._anti_label in chunk.text:
            types.append("anti_pattern")
        return ChunkMetadata(
            domain=chunk.box_number,
            domain_name=chunk.box_name,
            subdomains=self._subdomains(chunk, self._corpus.syllabus.get(chunk.box_number, ())),
            technologies=technologies,
            languages=languages,
            artifact_types=tuple(types),
        )

    def _subdomains(self, chunk: Chunk, declared: Sequence[str]) -> tuple[str, ...]:
        """Assign the chunk to the declared subcategories of its box that really appear in it."""
        text = normalize(chunk.title + " " + chunk.text[:1200])
        found = []
        for sub in declared:
            needles = (sub.replace("_", " "), *self._synonyms.get(sub, ()))
            if any(normalize(n) in text for n in needles if n):
                found.append(sub)
        # 'concepts' is the generic drawer of the syllabus: it has no word of its own, so it
        # takes what fits nowhere else. It is not a hit, it is the remainder.
        if not found and "concepts" in declared:
            return ("concepts",)
        return tuple(found)

    def coverage(self) -> dict[str, object]:
        """How much of the chunk -> subcategory assignment really works. Reported, not claimed."""
        chunks = self._corpus.chunks
        declared = {s for subs in self._corpus.syllabus.values() for s in subs}
        assigned = {s for c in chunks for s in self.of(c).subdomains}
        return {
            "chunks": len(chunks),
            "with_subdomain": sum(1 for c in chunks if self.of(c).subdomains),
            "with_technology": sum(1 for c in chunks if self.of(c).technologies),
            "with_language": sum(1 for c in chunks if self.of(c).languages),
            "declared_subcategories": len(declared),
            "subcategories_assigned_to_some_chunk": len(assigned),
            "never_assigned": sorted(declared - assigned),
            "without_source_in_corpus": ["difficulty", "status", "version"],
        }


@dataclass(frozen=True, slots=True)
class FilterOutcome:
    chunks: list[Chunk]
    fell_back: bool
    reason: str


class MetadataFilter:
    """Narrows an index by boxes, technologies, artifact types and exclusions."""

    MINIMUM_KEPT = 3

    def __init__(self, extractor: MetadataExtractor, catalog: MessageCatalog) -> None:
        self._extractor = extractor
        self._t = catalog

    def apply(
        self,
        index: Sequence[Chunk],
        plan: RetrievalPlan | None = None,
        boxes: Iterable[str] | None = None,
        technologies: Iterable[str] | None = None,
        types: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
    ) -> FilterOutcome:
        boxes, technologies = list(boxes or ()), list(technologies or ())
        types, exclude = list(types or ()), list(exclude or ())
        if plan is not None:
            boxes = boxes or list(plan.domains)
            technologies = technologies or list(plan.technologies)
            types = types or [t for t in (canonical_artifact_type(x) for x in plan.artifact_types)
                              if t in FILTERABLE_TYPES]
            exclude = exclude or list(plan.exclude)

        if not any((boxes, technologies, types, exclude)):
            return FilterOutcome(list(index), False, self._t("retrieval.filter.none"))

        kept, applied = list(index), []
        if boxes:
            keys = {str(b).split("·")[0].strip().zfill(2) if str(b).strip().isdigit() else normalize(str(b))
                    for b in boxes}
            kept = [c for c in kept
                    if c.box_number in keys or any(k in normalize(c.box) for k in keys if not k.isdigit())]
            applied.append(self._t("retrieval.filter.part.boxes", boxes=",".join(sorted(map(str, boxes)))))
        if exclude:
            out = {str(b).zfill(2) for b in exclude}
            kept = [c for c in kept if c.box_number not in out]
            applied.append(self._t("retrieval.filter.part.excluding", boxes=",".join(sorted(out))))
        if technologies:
            wanted = {t.lower() for t in technologies}
            kept = [c for c in kept if any(x.lower() in wanted for x in self._extractor.of(c).technologies)]
            applied.append(self._t("retrieval.filter.part.technologies", items=",".join(sorted(technologies))))
        if types:
            wanted_types = {t.lower() for t in types}
            kept = [c for c in kept if wanted_types & set(self._extractor.of(c).artifact_types)]
            applied.append(self._t("retrieval.filter.part.types", items=",".join(sorted(types))))

        detail = " · ".join(applied)
        if not kept:
            return FilterOutcome(list(index), True, self._t("retrieval.filter.empty", detail=detail))
        if len(kept) < self.MINIMUM_KEPT:
            return FilterOutcome(
                list(index), True, self._t("retrieval.filter.too_few", detail=detail, kept=len(kept))
            )
        return FilterOutcome(
            kept, False, self._t("retrieval.filter.applied", detail=detail, kept=len(kept), total=len(index))
        )
