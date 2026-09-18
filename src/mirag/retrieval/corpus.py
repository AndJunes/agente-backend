"""The knowledge corpus: markdown boxes split into retrievable chunks.

Each ``NN-name.md`` file is a *box*; each ``##`` section inside it is a *knowledge item*
and one retrievable chunk. Besides the general index there are three typed indices that
exploit the structure of the corpus:

* ``cards``          - only the card of each concept (when, limits, trade-off...).
* ``failures``       - the "how it fails" field of each card, plus whole failure sections.
* ``anti_patterns``  - what NOT to do and what to do instead.

The markers (``Card``/``Ficha``, field labels, failure titles) come from the
:class:`~mirag.i18n.corpus_format.CorpusFormat` of the corpus language: the parser has no
language of its own.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from mirag.core.text import normalize, short_hash
from mirag.i18n.corpus_format import CorpusFormat

REFERENCE = re.compile(r"`\[([0-9,\s]+)\]`")
"""Cross references between boxes: `` `[04, 09]` ``. The same regex for every consumer."""


@dataclass(frozen=True, slots=True)
class Chunk:
    """One retrievable unit."""

    text: str
    """What is sent to the model."""
    norm: str
    """The same text, normalised, for searching."""
    box: str
    """``"04 · Databases"``."""
    title: str
    """``"Indexes"``."""

    @property
    def box_number(self) -> str:
        return self.box.split("·")[0].strip()

    @property
    def box_name(self) -> str:
        return self.box.partition("·")[2].strip()

    @property
    def key(self) -> tuple[str, str]:
        """Identity by position in the corpus, never by text."""
        return (self.box, self.title)

    @classmethod
    def of(cls, text: str, box: str, title: str) -> Chunk:
        return cls(text=text, norm=normalize(text), box=box, title=title)


class CorpusParser:
    """Splits box documents into sections and reads their cards."""

    def __init__(self, fmt: CorpusFormat) -> None:
        self.fmt = fmt
        self._card_opening = f"> **{fmt.card_marker}**"

    @staticmethod
    def sections(content: str) -> list[str]:
        """Split by ``## `` titles, RESPECTING code fences.

        Splitting on ``"\\n## "`` alone turns any ``##`` inside a fenced block into a section
        of the document: the ADR template of box 19 used to produce five phantom chunks
        ("Status", "Context", "Decision"...) and stole the card of the real section.
        """
        sections: list[str] = []
        current: list[str] | None = None
        in_fence = False
        for line in content.split("\n"):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
            if not in_fence and line.startswith("## "):
                if current is not None:
                    sections.append("\n".join(current))
                current = [line[3:]]
            elif current is not None:
                current.append(line)
        if current is not None:
            sections.append("\n".join(current))
        return sections

    def card_of(self, section: str) -> str:
        """The ``> **Card** ...`` blockquote of a section, flattened to one line."""
        lines: list[str] = []
        inside = False
        for line in section.split("\n"):
            if line.startswith(self._card_opening):
                inside = True
            if inside:
                if not line.startswith(">"):
                    break
                lines.append(line.lstrip("> "))
        return " ".join(lines)

    def card_field(self, card: str, field: str) -> str:
        """One field of a card, e.g. ``card_field(card, "how_it_fails")``."""
        label = re.escape(self.fmt.field(field))
        match = re.search(rf"\*\*{label}:\*\*(.+?)(?: · \*\*|$)", card)
        return match.group(1).strip() if match else ""

    def is_failure_title(self, title: str) -> bool:
        return title.startswith(self.fmt.failure_title_prefixes)

    def syllabus_of(self, content: str) -> tuple[str, ...]:
        """The subcategories a box DECLARES to cover (``**Covers from the syllabus:**``)."""
        marker = re.escape(self.fmt.syllabus_marker)
        match = re.search(rf"\*\*{marker}:\*\*(.+)$", content, re.MULTILINE)
        if not match:
            return ()
        # the declaration may wrap onto the following line
        tail = content[match.start():].split("\n\n", 1)[0]
        return tuple(dict.fromkeys(re.findall(r"`([a-z_]+)`", tail)))


class KnowledgeCorpus:
    """The corpus of one locale, loaded once: four indices, the syllabus and the box graph."""

    def __init__(
        self,
        locale: str,
        fmt: CorpusFormat,
        chunks: tuple[Chunk, ...],
        cards: tuple[Chunk, ...],
        failures: tuple[Chunk, ...],
        anti_patterns: tuple[Chunk, ...],
        syllabus: dict[str, tuple[str, ...]],
    ) -> None:
        self.locale = locale
        self.format = fmt
        self.parser = CorpusParser(fmt)
        self.chunks = chunks
        self.cards = cards
        self.failures = failures
        self.anti_patterns = anti_patterns
        self.syllabus = syllabus
        self.box_graph = self._build_box_graph()

    # ── loading ──────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, directory: Path, fmt: CorpusFormat, locale: str | None = None) -> KnowledgeCorpus:
        parser = CorpusParser(fmt)
        chunks: list[Chunk] = []
        cards: list[Chunk] = []
        failures: list[Chunk] = []
        anti_patterns: list[Chunk] = []
        syllabus: dict[str, tuple[str, ...]] = {}
        fails_like = fmt.label("fails_like")
        avoid, prefer, see_box = fmt.label("avoid"), fmt.label("prefer"), fmt.label("see_box")

        for path in sorted(directory.glob("[0-9]*.md")):
            content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
            box = content.split("\n", 1)[0].lstrip("# ").strip()  # "04 · Databases"
            syllabus[box.split("·")[0].strip()] = parser.syllabus_of(content)
            for section in parser.sections(content):
                title = section.split("\n", 1)[0].strip()
                if title.startswith(fmt.sources_title):  # bibliography is not knowledge
                    continue
                chunks.append(Chunk.of(f"[{box}]\n\n## {section.strip()}", box, title))
                card = parser.card_of(section)
                if card:
                    cards.append(Chunk.of(f"[{box}] {title} — {card}", box, title))
                    if fails := parser.card_field(card, "how_it_fails"):
                        failures.append(Chunk.of(f"[{box}] {title} — {fails_like}: {fails}", box, title))
                    if anti := parser.card_field(card, "anti_pattern"):
                        pattern = parser.card_field(card, "pattern") or see_box
                        anti_patterns.append(
                            Chunk.of(f"[{box}] {title}\n  ✗ {avoid}: {anti}\n  ✓ {prefer}: {pattern}", box, title)
                        )
                if parser.is_failure_title(title):  # whole failure sections
                    failures.append(Chunk.of(f"[{box}]\n\n## {section.strip()}", box, title))
        return cls(
            locale or fmt.locale,
            fmt,
            tuple(chunks),
            tuple(cards),
            tuple(failures),
            tuple(anti_patterns),
            syllabus,
        )

    # ── queries ──────────────────────────────────────────────────────────────

    def index(self, name: str) -> tuple[Chunk, ...]:
        """``knowledge`` | ``cards`` | ``failures`` | ``anti_patterns``."""
        return {
            "knowledge": self.chunks,
            "cards": self.cards,
            "failures": self.failures,
            "anti_patterns": self.anti_patterns,
        }[name]

    @property
    def boxes(self) -> list[str]:
        return sorted({chunk.box for chunk in self.chunks})

    @property
    def box_names(self) -> dict[str, str]:
        """``"04"`` -> ``"04 · Databases"``."""
        return {chunk.box_number: chunk.box for chunk in self.chunks}

    def has_box(self, number: str) -> bool:
        return any(chunk.box_number == number for chunk in self.chunks)

    @property
    def content_hash(self) -> str:
        """Identity by CONTENT: if a paragraph changes, the hash changes."""
        return short_hash("\n".join(chunk.text for chunk in self.chunks))

    def stats(self) -> dict[str, int]:
        return {
            "boxes": len(self.boxes),
            "chunks": len(self.chunks),
            "cards": len(self.cards),
            "anti_patterns": len(self.anti_patterns),
            "failures": len(self.failures),
            "characters": sum(len(chunk.text) for chunk in self.chunks),
        }

    @staticmethod
    def references(text: str) -> list[str]:
        """The boxes a text cites, as two-digit numbers, in order and without repeats."""
        found: list[str] = []
        for group in REFERENCE.findall(text or ""):
            found += [n.strip().zfill(2) for n in group.split(",") if n.strip()]
        return list(dict.fromkeys(found))

    def _build_box_graph(self) -> dict[str, Counter[int]]:
        """Who references whom, box to box, reading the `` `[NN]` `` marks of the text."""
        graph: dict[str, Counter[int]] = {}
        for chunk in self.chunks:
            refs: Counter[int] = Counter()
            for group in REFERENCE.findall(chunk.text):
                refs.update(int(n) for n in group.split(",") if n.strip())
            graph.setdefault(chunk.box, Counter()).update(refs)
        return graph
