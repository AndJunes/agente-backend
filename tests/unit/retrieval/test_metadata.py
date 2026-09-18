"""Derived metadata and the filter that SAYS when it could not filter.

What matters most is not that the filter hits, but that it reports what it did: the old
filter fell back to the whole corpus in silence and nobody ever found out.
"""

from __future__ import annotations

from mirag.retrieval.corpus import Chunk
from mirag.retrieval.engine import RetrievalEngine
from mirag.retrieval.metadata import (
    ARTIFACT_TYPES,
    TECHNOLOGIES,
    MetadataFilter,
    canonical_artifact_type,
)
from mirag.retrieval.plan import RetrievalPlan

INDEX_TITLE = {"en": "Indexes", "es": "Índices"}


def section(engine: RetrievalEngine, box: str, title: str) -> Chunk:
    return next(c for c in engine.corpus.chunks if c.box_number == box and c.title == title)


def parts(engine: RetrievalEngine, **applied: str) -> str:
    t = engine.catalog
    labels = {"boxes": ("retrieval.filter.part.boxes", "boxes"),
              "technologies": ("retrieval.filter.part.technologies", "items"),
              "types": ("retrieval.filter.part.types", "items")}
    return " · ".join(t(labels[k][0], **{labels[k][1]: v}) for k, v in applied.items())


# ── what is derived ──────────────────────────────────────────────────────────

def test_the_domain_is_the_box(engine: RetrievalEngine) -> None:
    meta = engine.metadata.of(section(engine, "04", INDEX_TITLE[engine.locale]))
    assert (meta.domain, meta.domain_name) == ("04", "Databases")


def test_subdomains_come_from_the_declared_syllabus(engine: RetrievalEngine) -> None:
    meta = engine.metadata.of(section(engine, "04", INDEX_TITLE[engine.locale]))
    assert "indexing" in meta.subdomains
    declared = engine.corpus.syllabus["04"]
    assert set(meta.subdomains) <= set(declared), "a subcategory the box does not declare"
    for chunk in engine.corpus.chunks:
        assert set(engine.metadata.of(chunk).subdomains) <= set(engine.corpus.syllabus[chunk.box_number])


def test_technologies_are_found_by_word(engine: RetrievalEngine) -> None:
    assert "PostgreSQL" in engine.metadata.of(section(engine, "04", INDEX_TITLE[engine.locale])).technologies
    assert "Kubernetes" in engine.metadata.of(section(engine, "13", "Kubernetes")).technologies
    assert all(t in TECHNOLOGIES for c in engine.corpus.chunks for t in engine.metadata.of(c).technologies)


def test_languages_come_from_the_code_fences(engine: RetrievalEngine) -> None:
    with_language = [c for c in engine.corpus.chunks if engine.metadata.of(c).languages]
    assert with_language, "no chunk has a language: the ``` parsing is broken"
    assert all(lang.isalpha() for c in with_language for lang in engine.metadata.of(c).languages)


def test_artifact_types(engine: RetrievalEngine) -> None:
    types = engine.metadata.of(section(engine, "04", INDEX_TITLE[engine.locale])).artifact_types
    assert {"concept", "card"} <= set(types)
    assert set(types) <= set(ARTIFACT_TYPES)
    failure = next(c for c in engine.corpus.chunks if engine.corpus.parser.is_failure_title(c.title))
    assert "failure" in engine.metadata.of(failure).artifact_types


def test_what_does_not_exist_is_none(engine: RetrievalEngine) -> None:
    """Declared, without a source: an explicit None beats an invented value."""
    for chunk in engine.corpus.chunks:
        meta = engine.metadata.of(chunk)
        assert (meta.difficulty, meta.status, meta.version) == (None, None, None)
        assert meta.domain.isdigit() and len(meta.domain) == 2


def test_coverage_is_honest(engine: RetrievalEngine) -> None:
    coverage = engine.metadata.coverage()
    assert coverage["with_subdomain"] <= coverage["chunks"] == len(engine.corpus.chunks)
    assert coverage["subcategories_assigned_to_some_chunk"] <= coverage["declared_subcategories"]
    assert coverage["without_source_in_corpus"] == ["difficulty", "status", "version"]
    assert isinstance(coverage["never_assigned"], list)


def test_metadata_is_the_same_in_both_languages(engine_en: RetrievalEngine, engine_es: RetrievalEngine) -> None:
    """Technologies and types are language neutral; the corpora are translations."""
    for en, es in zip(engine_en.corpus.chunks, engine_es.corpus.chunks, strict=True):
        a, b = engine_en.metadata.of(en), engine_es.metadata.of(es)
        assert (a.domain, a.artifact_types, a.languages) == (b.domain, b.artifact_types, b.languages), en.title


def test_artifact_type_aliases_are_understood_in_both_languages() -> None:
    assert canonical_artifact_type("ficha") == canonical_artifact_type("Card") == "card"
    assert canonical_artifact_type("antipatrón") == canonical_artifact_type("anti-pattern") == "anti_pattern"
    assert canonical_artifact_type("Implementación") == "implementation"
    assert canonical_artifact_type("nonsense") is None


# ── the filter ───────────────────────────────────────────────────────────────

def test_no_filter_touches_nothing(engine: RetrievalEngine) -> None:
    outcome = engine.metadata_filter.apply(engine.corpus.chunks)
    assert outcome.chunks == list(engine.corpus.chunks) and not outcome.fell_back
    assert outcome.reason == engine.catalog.t("retrieval.filter.none")


def test_filter_by_one_box(engine: RetrievalEngine) -> None:
    index = engine.corpus.chunks
    outcome = engine.metadata_filter.apply(index, boxes=["04"])
    assert not outcome.fell_back
    assert outcome.chunks and all(c.box_number == "04" for c in outcome.chunks)
    assert len(outcome.chunks) < len(index)
    assert outcome.reason == engine.catalog.t("retrieval.filter.applied", detail=parts(engine, boxes="04"),
                                              kept=len(outcome.chunks), total=len(index))


def test_filter_by_several_boxes_by_name_and_with_exclusions(engine: RetrievalEngine) -> None:
    apply = engine.metadata_filter.apply
    index = engine.corpus.chunks
    assert {c.box_number for c in apply(index, boxes=["04", "08"]).chunks} == {"04", "08"}
    assert {c.box_number for c in apply(index, boxes=["Databases"]).chunks} == {"04"}
    assert {c.box_number for c in apply(index, boxes=["04", "08"], exclude=["08"]).chunks} == {"04"}


def test_filter_by_technology_and_type(engine: RetrievalEngine) -> None:
    apply, meta = engine.metadata_filter.apply, engine.metadata
    k8s = apply(engine.corpus.chunks, technologies=["Kubernetes"])
    assert not k8s.fell_back and all("Kubernetes" in meta.of(c).technologies for c in k8s.chunks)
    failures = apply(engine.corpus.chunks, types=["failure"])
    assert not failures.fell_back and all("failure" in meta.of(c).artifact_types for c in failures.chunks)


def test_a_filter_that_leaves_nothing_says_so_and_keeps_searching(engine: RetrievalEngine) -> None:
    index = engine.corpus.chunks
    outcome = engine.metadata_filter.apply(index, technologies=["CobolInTheCloud"])
    assert outcome.fell_back is True
    assert outcome.chunks == list(index), "keep searching, do not return nothing"
    assert outcome.reason == engine.catalog.t(
        "retrieval.filter.empty", detail=parts(engine, technologies="CobolInTheCloud"))


def test_a_filter_that_leaves_too_few_says_so(engine: RetrievalEngine) -> None:
    """Two chunks are not a corpus: better to search everything and say it."""
    index = engine.corpus.chunks
    outcome = engine.metadata_filter.apply(index, boxes=["04"], types=["failure"])
    assert outcome.fell_back is True and outcome.chunks == list(index)
    assert MetadataFilter.MINIMUM_KEPT > 1, "one kept chunk must count as too few"
    assert outcome.reason == engine.catalog.t(
        "retrieval.filter.too_few", detail=parts(engine, boxes="04", types="failure"), kept=1)


def test_an_unknown_box_or_an_empty_index_does_not_blow_up(engine: RetrievalEngine) -> None:
    unknown = engine.metadata_filter.apply(engine.corpus.chunks, boxes=["99"])
    assert unknown.fell_back and len(unknown.chunks) == len(engine.corpus.chunks)
    empty = engine.metadata_filter.apply([], boxes=["04"])
    assert empty.chunks == [] and isinstance(empty.reason, str)


def test_the_reason_can_always_be_shown(engine: RetrievalEngine) -> None:
    for kwargs in ({}, {"boxes": ["04"]}, {"technologies": ["NoSuchThing"]}, {"types": ["card"]},
                   {"boxes": ["99"]}, {"exclude": ["04"]}):
        reason = engine.metadata_filter.apply(engine.corpus.chunks, **kwargs).reason
        assert len(reason) > 10 and "{" not in reason, (kwargs, reason)


def test_the_filter_reads_the_plan(engine: RetrievalEngine) -> None:
    plan = engine.plan_parser.parse('{"domains":["04","08"],"needs_code":false}', "concurrent bookings")
    outcome = engine.metadata_filter.apply(engine.corpus.chunks, plan=plan)
    assert not outcome.fell_back
    assert {c.box_number for c in outcome.chunks} == {"04", "08"}


def test_plan_artifact_types_are_canonicalised_and_unknown_ones_dropped(engine: RetrievalEngine) -> None:
    plan = RetrievalPlan(domains=("04",), artifact_types=("ficha", "failure", "bogus"))
    outcome = engine.metadata_filter.apply(engine.corpus.chunks, plan=plan)
    assert not outcome.fell_back
    assert all({"card", "failure"} & set(engine.metadata.of(c).artifact_types) for c in outcome.chunks)
    assert outcome.reason == engine.catalog.t(
        "retrieval.filter.applied", detail=parts(engine, boxes="04", types="card,failure"),
        kept=len(outcome.chunks), total=len(engine.corpus.chunks))


def test_explicit_arguments_win_over_the_plan(engine: RetrievalEngine) -> None:
    plan = RetrievalPlan(domains=("08",))
    outcome = engine.metadata_filter.apply(engine.corpus.chunks, plan=plan, boxes=["04"])
    assert {c.box_number for c in outcome.chunks} == {"04"}
