"""Loading the PM corpus, which is shaped nothing like the backend one.

Mirag's corpus is nineteen ``NN-name.md`` files whose knowledge is carried in a ``> **Card**``
blockquote per section. This one is ninety-one documents in domain folders, carrying their
knowledge in YAML frontmatter and a fixed body contract, with citations to a source register.
Pointing mirag's loader at it would parse cleanly and produce three empty indices, which is
the worst possible failure: silent.

So this builds the same ``KnowledgeCorpus`` from a different shape. Everything downstream —
retrieval, ranking, filtering, the tools — sees the object it already knows.

The four indices are mapped onto what this corpus actually has, and the mapping is meant
literally rather than as a convenience:

``knowledge``      every ``##`` section, carrying its title and domain
``anti_patterns``  the **Limitations** sections — "what the sources do not establish" is this
                   corpus's form of "what not to do", and answering a question without it is
                   how an agent sounds more certain than its evidence
``failures``       everything the corpus marks as unsafe: ``⚠``, ``[DISPUTED]``,
                   ``UNVERIFIED``, ``VENDOR PROJECTION``, "do not cite", the ``confidence:
                   low`` documents, and the two reference documents whose whole subject is
                   what to distrust
``cards``          synthesised from frontmatter, never invented: type, evidence, confidence
                   and sources, which is the filter and rerank surface the corpus asks for
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from mirag.i18n.corpus_format import CorpusFormat
from mirag.retrieval.corpus import Chunk, CorpusParser, KnowledgeCorpus

from mirag_pm.frontmatter import Document, parse
from mirag_pm.paths import DOCUMENTS_LOCALE

DOMAIN_FOLDER = re.compile(r"^(\d{2})-(.+)$")

LIMITATION_HEADING = re.compile(
    r"limitation|what (?:the |this )?\w+ (?:does|do) not (?:cover|contain|say|show|establish)"
    r"|must not be used for",
    re.IGNORECASE,
)
"""Any heading that says what the sources do not establish.

Matched on the whole heading, not by prefix, and that was not the first attempt. Prefixing on
"Limitations" reads 65 of the 77 sections and misses every variant that puts a word first —
`## Important limitation of this document`, `## Cross-cutting limitations` — which silently
dropped those documents out of the `anti_patterns` index *and* listed them as having no
limitations at all. Two more live at `###` depth (`Known limitations`), inside a parent
section, so depth is searched too.

The corpus README calls this section "Always present". It is not, and the load report counts
the documents that lack it rather than letting the claim stand."""

CAUTION_MARKERS = ("⚠", "[DISPUTED]", "UNVERIFIED", "VENDOR PROJECTION", "do not cite", "Do not cite")

DISTRUST_DOCUMENTS = ("disputed-information.md", "outdated-information.md")
"""Indexed whole into ``failures``. Their entire subject is what not to assert, and a
half-retrieved warning is worse than none."""

PROSE_META = ("README.md", "TAXONOMY.md", "CONCEPT_GRAPH.md", "CORPUS_AUDIT.md",
              "RESEARCH_BACKLOG.md", "CHANGELOG.md")
"""Meta files that answer questions in prose, so they are retrievable like any document."""

LOOKUP_META = ("INDEX.md", "SOURCES.md", "GLOSSARY.md")
"""Meta files that are tables, not prose: 633 term→document rows, the `[Snnn]`/`[Ennn]`
registers, and the glossary. Chunking a lookup table into fuzzy-retrievable prose makes it
worse at the one thing it is for. They are loaded whole and answered by exact lookup instead
— see ``lookups``. Nothing is dropped; it is read with the right instrument."""

META_BOX = "00 · About this knowledge base"

_SMALL_WORDS = {"and", "or", "of", "the", "for", "to", "vs", "a", "an", "in", "on"}
_UPPERCASE = {"ai", "ux", "it", "pm", "gtm", "eol"}


def box_of(folder: str) -> str:
    """``06-requirements`` -> ``06 · Requirements``.

    The ``NN · Name`` shape is not cosmetic: ``Chunk.box_number`` splits on the ``·`` and the
    graph and search helpers call ``int()`` on what comes out.
    """
    match = DOMAIN_FOLDER.match(folder)
    if not match:
        raise ValueError(f"not a domain folder: {folder!r}")
    number, rest = match.groups()
    words = [
        word.upper() if word in _UPPERCASE
        else word if word in _SMALL_WORDS and index > 0
        else word.capitalize()
        for index, word in enumerate(rest.split("-"))
    ]
    return f"{number} · {' '.join(words)}"


@dataclass(frozen=True, slots=True)
class LoadReport:
    """What the load actually found. Printed by ``doctor``, asserted by CI."""

    directory: Path
    documents: int
    counts: dict[str, int]
    fell_back_from: str | None = None
    without_limitations: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    lookups: tuple[str, ...] = ()
    skipped_sources_sections: int = 0

    def lines(self) -> list[str]:
        out = [f"corpus: {self.directory}"]
        if self.fell_back_from:
            out.append(
                f"  locale {self.fell_back_from!r} has no documents of its own; reading "
                f"{DOCUMENTS_LOCALE!r}. The corpus is written in one language; the answer "
                f"language is chosen by the message catalogue."
            )
        out.append(f"  {self.documents} documents across {len(self.domains)} domains")
        out += [f"  {name:<14} {count:>5}" for name, count in self.counts.items()]
        out.append(f"  lookup tables  {', '.join(self.lookups) or 'none'}")
        out.append(f"  `## Sources` sections skipped: {self.skipped_sources_sections}")
        if self.without_limitations:
            out.append(f"  no Limitations section ({len(self.without_limitations)}):")
            out += [f"      {name}" for name in self.without_limitations]
        return out


@dataclass
class _Indices:
    knowledge: list[Chunk] = field(default_factory=list)
    cards: list[Chunk] = field(default_factory=list)
    failures: list[Chunk] = field(default_factory=list)
    anti_patterns: list[Chunk] = field(default_factory=list)


class PmCorpus:
    """Builds a :class:`KnowledgeCorpus` from the frontmatter-and-domains layout."""

    @classmethod
    def load(cls, directory: Path, fmt: CorpusFormat, locale: str | None = None) -> KnowledgeCorpus:
        corpus, _ = cls.load_with_report(directory, fmt, locale)
        return corpus

    @classmethod
    def load_with_report(
        cls, directory: Path, fmt: CorpusFormat, locale: str | None = None
    ) -> tuple[KnowledgeCorpus, LoadReport]:
        root, fell_back_from = cls._resolve(directory)
        indices = _Indices()
        syllabus: dict[str, tuple[str, ...]] = {}
        without_limitations: list[str] = []
        domains: list[str] = []
        documents = 0
        skipped_sources = 0

        for folder in sorted(p for p in root.iterdir() if p.is_dir() and DOMAIN_FOLDER.match(p.name)):
            box = box_of(folder.name)
            domains.append(box)
            topics: list[str] = []
            for path in sorted(folder.glob("*.md")):
                doc = parse(path.read_text(encoding="utf-8"), source=str(path))
                documents += 1
                topics += list(doc.list("topics")) + list(doc.list("synonyms"))
                skipped_sources += cls._add_document(indices, doc, path, box, fmt)
                if not cls._has_limitations(doc.body):
                    without_limitations.append(f"{folder.name}/{path.name}")
            # The syllabus of a box is what mirag uses to say what an area covers. Here the
            # documents declare their own topics, so it is read rather than inferred.
            syllabus[box.split("·")[0].strip()] = tuple(dict.fromkeys(topics))

        for name in PROSE_META:
            path = root / name
            if path.exists():
                documents += 1
                doc = parse(path.read_text(encoding="utf-8"), source=str(path))
                skipped_sources += cls._add_document(indices, doc, path, META_BOX, fmt)

        if not indices.knowledge:
            raise ValueError(
                f"the corpus at {root} produced no chunks. `Path.glob` returns an empty list "
                f"for a directory that does not exist, so a missing corpus looks exactly like "
                f"an empty one — which is why this is checked rather than assumed."
            )

        corpus = KnowledgeCorpus(
            locale or fmt.locale,
            fmt,
            tuple(indices.knowledge),
            tuple(indices.cards),
            tuple(indices.failures),
            tuple(indices.anti_patterns),
            syllabus,
        )
        report = LoadReport(
            directory=root,
            documents=documents,
            counts={
                "knowledge": len(indices.knowledge),
                "cards": len(indices.cards),
                "failures": len(indices.failures),
                "anti_patterns": len(indices.anti_patterns),
            },
            fell_back_from=fell_back_from,
            without_limitations=tuple(without_limitations),
            domains=tuple(domains),
            lookups=tuple(name for name in LOOKUP_META if (root / name).exists()),
            skipped_sources_sections=skipped_sources,
        )
        return corpus, report

    # ── one document ─────────────────────────────────────────────────────────

    @classmethod
    def _add_document(
        cls, indices: _Indices, doc: Document, path: Path, box: str, fmt: CorpusFormat
    ) -> int:
        """Returns how many ``## Sources`` sections were skipped."""
        name = doc.text("title") or path.stem.replace("-", " ").title()
        skipped = 0
        distrust = path.name in DISTRUST_DOCUMENTS

        card = cls._card(doc, name, box)
        if card:
            indices.cards.append(Chunk.of(card, box, name))

        for section in CorpusParser.sections(doc.body):
            heading = section.split("\n", 1)[0].strip()
            if heading.startswith(fmt.sources_title):
                # Same reasoning as mirag's loader: a bibliography is not knowledge. The
                # citations are not lost — `SOURCES.md` holds the resolvable register.
                skipped += 1
                continue
            # Keyed by document AND section: "Limitations" is a heading in 78 of these
            # documents, and `Chunk.key` is `(box, title)`. Without the document name they
            # would collide inside their own domain.
            title = f"{name} — {heading}"
            body = f"[{box}] {name}\n\n## {section.strip()}"
            indices.knowledge.append(Chunk.of(body, box, title))

            for label, block in cls._limitation_blocks(heading, section):
                indices.anti_patterns.append(
                    Chunk.of(
                        f"[{box}] {name}\n  ✗ {fmt.label('avoid')}: {block.strip()}",
                        box, f"{name} — {label}",
                    )
                )
            if distrust or cls._has_caution(section):
                indices.failures.append(Chunk.of(body, box, title))

        # A `confidence: low` document leads with its own coverage warning; the corpus says to
        # read it as a map of what is missing, not as an answer.
        if doc.text("confidence") == "low":
            indices.failures.append(
                Chunk.of(
                    f"[{box}] {name} — {fmt.label('fails_like')}: confidence: low. "
                    f"{doc.text('evidence_type')}. Read as a map of what is missing.",
                    box, f"{name} — low confidence",
                )
            )
        return skipped

    @staticmethod
    def _card(doc: Document, name: str, box: str) -> str:
        """The card, assembled from frontmatter. Nothing here is written by this loader."""
        if not doc.meta:
            return ""
        parts = [f"[{box}] {name}"]
        for label, key in (("Type", "type"), ("Evidence", "evidence_type"), ("Confidence", "confidence")):
            if value := doc.text(key):
                parts.append(f"{label}: {value}")
        if sources := doc.list("sources"):
            parts.append(f"Sources: {', '.join(sources)}")
        for level, ids in doc.nested("provenance").items():
            # An empty `empirical` list is information: it says nobody has measured this.
            parts.append(f"{level}: {', '.join(ids) if ids else 'nothing'}")
        if topics := doc.list("topics"):
            parts.append(f"Topics: {', '.join(topics)}")
        return " · ".join(parts)

    @staticmethod
    def _limitation_blocks(heading: str, section: str) -> list[tuple[str, str]]:
        """The limitation passages of one section: the whole thing, or its ``###`` parts."""
        if LIMITATION_HEADING.search(heading):
            return [(heading, section)]
        blocks: list[tuple[str, str]] = []
        current: list[str] | None = None
        current_heading = ""
        for line in section.split("\n"):
            if line.startswith("### "):
                if current is not None:
                    blocks.append((current_heading, "\n".join(current)))
                sub = line[4:].strip()
                current, current_heading = ([sub] if LIMITATION_HEADING.search(sub) else None), sub
            elif current is not None:
                current.append(line)
        if current is not None:
            blocks.append((current_heading, "\n".join(current)))
        return blocks

    @staticmethod
    def _has_limitations(body: str) -> bool:
        return any(
            LIMITATION_HEADING.search(line.lstrip("#").strip())
            for line in body.split("\n")
            if line.startswith("#")
        )

    @staticmethod
    def _has_caution(section: str) -> bool:
        return any(marker in section for marker in CAUTION_MARKERS)

    # ── where the documents are ──────────────────────────────────────────────

    @staticmethod
    def _resolve(directory: Path) -> tuple[Path, str | None]:
        """The directory to read, and the locale it stood in for.

        ``I18n.knowledge_dir`` appends the locale, so a Spanish request asks for ``…/es``.
        This corpus is written in English and has no ``es`` tree — deliberately, because
        ninety-one duplicated files would be ninety-one files to edit twice. Falling back
        here, and reporting it, keeps that a stated fact instead of a silent empty corpus.
        """
        if any(DOMAIN_FOLDER.match(p.name) for p in directory.iterdir()) if directory.exists() else False:
            return directory, None
        return directory.parent / DOCUMENTS_LOCALE, directory.name


def lookup_tables(root: Path) -> dict[str, str]:
    """The three tables, whole. Read by the tools that answer by exact match."""
    return {
        name: (root / name).read_text(encoding="utf-8")
        for name in LOOKUP_META
        if (root / name).exists()
    }


def domain_counts(corpus: KnowledgeCorpus) -> Counter[str]:
    return Counter(chunk.box for chunk in corpus.chunks)
