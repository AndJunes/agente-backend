"""The knowledge corpus: how the boxes are split into chunks, in both languages.

The English and Spanish corpora are translations of each other, so their STRUCTURE must be
identical: same boxes, same sections per box, same cards, same failure and anti-pattern
entries and the same cross references. A difference means one translation lost (or grew) a
section, and retrieval would then answer differently depending on the language.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from mirag.i18n.corpus_format import CorpusFormat
from mirag.i18n.registry import I18n
from mirag.retrieval.corpus import Chunk, CorpusParser, KnowledgeCorpus
from mirag.retrieval.engine import RetrievalEngine

LOCALES = ("en", "es")


def fenced_headings(content: str) -> list[str]:
    """The ``## `` lines that live INSIDE a code fence (the test oracle, not the parser)."""
    inside, found = False, []
    for line in content.split("\n"):
        if line.lstrip().startswith("```"):
            inside = not inside
        elif inside and line.startswith("## "):
            found.append(line[3:].strip())
    return found


# ── the real corpus: both languages, same structure ──────────────────────────

def test_both_corpora_have_the_same_boxes(engine_en: RetrievalEngine, engine_es: RetrievalEngine) -> None:
    assert engine_en.corpus.boxes == engine_es.corpus.boxes
    assert len(engine_en.corpus.boxes) == 19


def test_both_corpora_have_the_same_number_of_sections_per_box(
    engine_en: RetrievalEngine, engine_es: RetrievalEngine
) -> None:
    per_box = {c.locale: Counter(chunk.box for chunk in c.chunks)
               for c in (engine_en.corpus, engine_es.corpus)}
    assert per_box["en"] == per_box["es"]


def test_both_corpora_have_the_same_cards_failures_and_anti_patterns(
    engine_en: RetrievalEngine, engine_es: RetrievalEngine
) -> None:
    en, es = engine_en.corpus.stats(), engine_es.corpus.stats()
    for key in ("boxes", "chunks", "cards", "failures", "anti_patterns"):
        assert en[key] == es[key], key
    # pinned: a change here is a change of the corpus, and must be made on purpose
    assert (en["chunks"], en["cards"]) == (247, 228)
    for index in ("cards", "failures", "anti_patterns"):
        boxes_en = Counter(c.box for c in engine_en.corpus.index(index))
        boxes_es = Counter(c.box for c in engine_es.corpus.index(index))
        assert boxes_en == boxes_es, index


def test_both_corpora_have_identical_cross_references(
    engine_en: RetrievalEngine, engine_es: RetrievalEngine
) -> None:
    refs_en = [(c.box, KnowledgeCorpus.references(c.text)) for c in engine_en.corpus.chunks]
    refs_es = [(c.box, KnowledgeCorpus.references(c.text)) for c in engine_es.corpus.chunks]
    assert refs_en == refs_es
    assert engine_en.corpus.box_graph == engine_es.corpus.box_graph


def test_both_corpora_declare_the_same_syllabus(engine_en: RetrievalEngine, engine_es: RetrievalEngine) -> None:
    assert engine_en.corpus.syllabus == engine_es.corpus.syllabus
    assert all(engine_en.corpus.syllabus[n] for n in engine_en.corpus.box_names), "a box declares nothing"


def test_every_chunk_carries_its_box_and_has_content(engine: RetrievalEngine) -> None:
    for chunk in engine.corpus.chunks:
        assert chunk.text.startswith(f"[{chunk.box}]")
        assert chunk.title and chunk.text.strip()
        assert chunk.box_number.isdigit() and len(chunk.box_number) == 2
        assert chunk.norm == chunk.norm.lower()


def test_code_fences_never_create_phantom_sections(engine: RetrievalEngine, i18n: I18n) -> None:
    """The ADR template of box 19 has ``## Status``/``## Context``... inside a fenced block.
    Splitting on every ``\\n## `` turned them into five phantom chunks."""
    directory = i18n.knowledge_dir(engine.locale)
    phantoms_checked = 0
    for path in sorted(directory.glob("[0-9]*.md")):
        fenced = set(fenced_headings(path.read_text(encoding="utf-8")))
        box_titles = {c.title for c in engine.corpus.chunks if path.name.startswith(c.box_number)}
        assert not fenced & box_titles, f"{path.name}: {sorted(fenced & box_titles)}"
        phantoms_checked += len(fenced)
    assert phantoms_checked >= 5, "no fenced headings left: this test no longer proves anything"


def test_the_adr_card_of_box_19_is_attached_to_its_real_section(engine: RetrievalEngine) -> None:
    corpus = engine.corpus
    adr_cards = [c for c in corpus.cards if c.box_number == "19" and "ADR" in c.title]
    assert len(adr_cards) == 1, [c.title for c in corpus.cards if c.box_number == "19"]
    section = next(c for c in corpus.chunks if c.key == adr_cards[0].key)
    assert f"> **{corpus.format.card_marker}**" in section.text
    assert len([c for c in corpus.chunks if c.box_number == "19"]) == 11


def test_sources_sections_are_not_chunks(engine: RetrievalEngine, i18n: I18n) -> None:
    title = engine.corpus.format.sources_title
    files = sorted(i18n.knowledge_dir(engine.locale).glob("[0-9]*.md"))
    with_sources = [p for p in files if f"\n## {title}" in p.read_text(encoding="utf-8")]
    assert len(with_sources) == len(files), "the corpus lost its bibliography: the check is empty"
    assert not [c.title for c in engine.corpus.chunks if c.title.startswith(title)]


def test_the_typed_indices_come_from_the_cards(engine: RetrievalEngine) -> None:
    corpus, fmt = engine.corpus, engine.corpus.format
    assert all(fmt.card_marker in c.text for c in corpus.cards)
    assert all(f"✗ {fmt.label('avoid')}:" in c.text and f"✓ {fmt.label('prefer')}:" in c.text
               for c in corpus.anti_patterns)
    whole_sections = [c for c in corpus.failures if corpus.parser.is_failure_title(c.title)
                      and c.text.startswith(f"[{c.box}]\n\n## ")]
    assert whole_sections, "no whole failure section reached the failures index"
    assert any(fmt.label("fails_like") in c.text for c in corpus.failures)


def test_index_names_and_box_lookups(engine: RetrievalEngine) -> None:
    corpus = engine.corpus
    assert corpus.index("knowledge") is corpus.chunks
    assert corpus.index("cards") is corpus.cards
    assert corpus.index("failures") is corpus.failures
    assert corpus.index("anti_patterns") is corpus.anti_patterns
    assert corpus.box_names["04"] == "04 · Databases"
    assert corpus.has_box("19") and not corpus.has_box("99")
    with pytest.raises(KeyError):
        corpus.index("nonexistent")


def test_the_content_hash_identifies_the_text(engine_en: RetrievalEngine, engine_es: RetrievalEngine) -> None:
    assert engine_en.corpus.content_hash != engine_es.corpus.content_hash
    assert len(engine_en.corpus.content_hash) == 16


def test_references_are_read_in_order_and_without_repeats() -> None:
    assert KnowledgeCorpus.references("see `[04, 09]` and `[9]` and `[04]`") == ["04", "09"]
    assert KnowledgeCorpus.references("nothing here [04] (not backticked)") == []
    assert KnowledgeCorpus.references("") == []


def test_chunk_identity_is_its_position_not_its_text() -> None:
    a = Chunk.of("[04 · Databases]\n\n## Indexes\n\nsome text", "04 · Databases", "Indexes")
    b = Chunk.of("completely different text", "04 · Databases", "Indexes")
    assert a.key == b.key == ("04 · Databases", "Indexes")
    assert (a.box_number, a.box_name) == ("04", "Databases")
    assert Chunk.of("Índice", "x", "y").norm == "indice"


# ── a synthetic corpus written with each locale's markers ────────────────────

def _box(fmt: CorpusFormat, number: str, name: str, cites: str = "`[02, 03]`") -> str:
    card = "\n".join([
        f"> **{fmt.card_marker}** · **{fmt.field('when')}:** always ·",
        f"> **{fmt.field('pattern')}:** do the right thing ·",
        f"> **{fmt.field('anti_pattern')}:** do the wrong thing ·",
        f"> **{fmt.field('how_it_fails')}:** it breaks at night ·",
        f"> **{fmt.field('related')}:** neighbours {cites}",
    ])
    return (
        f"# {number} · {name}\n\n"
        f"**{fmt.syllabus_marker}:** `concepts` · `indexing`\n\n---\n\n"
        "## First section\n\nSome body text.\n\n"
        "```markdown\n# A template\n\n## Not a section\nstill the template\n```\n\n"
        f"{card}\n\n---\n\n"
        f"## {fmt.failure_title_prefixes[0]}: a thing\n\nHow it goes wrong.\n\n"
        f"## {fmt.sources_title}\n\n- a book\n"
    )


def _corpus(tmp_path: Path, fmt: CorpusFormat, newline: str = "\n") -> KnowledgeCorpus:
    directory = tmp_path / f"{fmt.locale}-{len(newline)}"
    directory.mkdir()
    for number, name in (("01", "First"), ("02", "Second")):
        content = _box(fmt, number, name).replace("\n", newline)
        (directory / f"{number}-{name.lower()}.md").write_bytes(content.encode("utf-8"))
    (directory / "README.md").write_text("# not a box\n\n## Ignored\n", encoding="utf-8")
    return KnowledgeCorpus.load(directory, fmt)


@pytest.mark.parametrize("locale", LOCALES)
def test_a_synthetic_box_is_split_with_the_markers_of_its_language(
    tmp_path: Path, i18n: I18n, locale: str
) -> None:
    fmt = i18n.corpus_format(locale)
    corpus = _corpus(tmp_path, fmt)
    failure_title = f"{fmt.failure_title_prefixes[0]}: a thing"
    assert corpus.locale == locale
    assert [c.title for c in corpus.chunks] == ["First section", failure_title] * 2
    assert [c.title for c in corpus.cards] == ["First section"] * 2
    assert "## Not a section" in corpus.chunks[0].text, "the fence stays inside its real section"
    assert len(corpus.anti_patterns) == 2
    assert "do the wrong thing" in corpus.anti_patterns[0].text
    assert "do the right thing" in corpus.anti_patterns[0].text
    # the 'how it fails' field of the card + the whole failure section, per box
    assert len(corpus.failures) == 4
    assert corpus.syllabus == {"01": ("concepts", "indexing"), "02": ("concepts", "indexing")}
    assert corpus.box_graph["01 · First"] == Counter({2: 1, 3: 1})


@pytest.mark.parametrize("locale", LOCALES)
def test_crlf_files_parse_exactly_like_lf_files(tmp_path: Path, i18n: I18n, locale: str) -> None:
    fmt = i18n.corpus_format(locale)
    lf, crlf = _corpus(tmp_path, fmt), _corpus(tmp_path, fmt, "\r\n")
    assert [c.text for c in crlf.chunks] == [c.text for c in lf.chunks]
    assert [c.text for c in crlf.cards] == [c.text for c in lf.cards]
    assert crlf.content_hash == lf.content_hash
    assert not any("\r" in c.text for c in crlf.chunks)


@pytest.mark.parametrize("locale", LOCALES)
def test_card_fields_are_read_by_their_localised_label(i18n: I18n, locale: str) -> None:
    fmt = i18n.corpus_format(locale)
    parser = CorpusParser(fmt)
    section = _box(fmt, "01", "First").split("## First section", 1)[1]
    card = parser.card_of(section)
    assert card.startswith(f"**{fmt.card_marker}**")
    assert parser.card_field(card, "how_it_fails") == "it breaks at night"
    assert parser.card_field(card, "anti_pattern") == "do the wrong thing"
    assert parser.card_field(card, "pattern") == "do the right thing"
    assert parser.card_field(card, "decision") == ""
    assert parser.card_of("no card here\n> just a quote") == ""


def test_sections_ignore_text_before_the_first_title() -> None:
    assert CorpusParser.sections("# Box\n\nintro\n\n## A\nx\n## B\ny") == ["A\nx", "B\ny"]
    assert CorpusParser.sections("no titles at all") == []
