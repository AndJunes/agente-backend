"""The labelled retrieval sets: loading, validation and cross-locale label alignment.

WHY THERE IS A "HARD" SET
    The original set scored 31/31 in recall@3: it was saturated. Against a ceiling nothing
    can be shown to improve, so any number over the easy set is unfalsifiable. The hard set
    adds families where lexical retrieval really suffers: paraphrase with no shared
    vocabulary, mixed English/Spanish, typos and multi-hop questions.

GRANULARITY
    The easy set was labelled by BOX. That forgives a real miss: retrieving the wrong section
    of the right box counts as a hit. The hard set is labelled by CHUNK (``"04 · Indexes"``),
    which is what is really sent to the model. Both forms coexist: ``"04"`` accepts any chunk
    of box 04. Every chunk label was checked by hand against the corpus: the cited section
    really answers the question.

TWO LANGUAGES, ONE SET
    The English corpus has exactly the same ``##`` sections, in the same order, as the Spanish
    one in every box. So the English chunk labels are not translated by hand: the i-th section
    of box NN in Spanish IS the i-th section in English (:func:`align_titles`).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mirag.retrieval.corpus import Chunk, KnowledgeCorpus

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"
RETRIEVAL_FILE = "retrieval.json"

EASY = "easy"
HARD_FAMILIES: tuple[str, ...] = ("paraphrase", "mixed", "typos", "multi_hop")
FAMILIES: tuple[str, ...] = (EASY, *HARD_FAMILIES)
UNCOVERED_GRADES: tuple[str, ...] = ("mentioned", "absent")
SEPARATOR = "·"
_BOX = re.compile(r"\A\d{2}\Z")


class DatasetError(ValueError):
    """A dataset file that does not follow the schema, or labels that do not exist."""


# ── labels ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Label:
    """``"04"`` (any chunk of box 04) or ``"04 · Indexes"`` (that chunk only)."""

    box: str
    title: str = ""

    @classmethod
    def parse(cls, text: object) -> Label:
        if not isinstance(text, str):
            raise DatasetError(f"a label must be a string, got {text!r}")
        box, separator, title = text.partition(SEPARATOR)
        box, title = box.strip(), title.strip()
        if not _BOX.match(box):
            raise DatasetError(f"a label starts with a two-digit box number: {text!r}")
        if separator and not title:
            raise DatasetError(f"a chunk label needs a title after '{SEPARATOR}': {text!r}")
        return cls(box, title)

    @property
    def is_chunk(self) -> bool:
        return bool(self.title)

    def matches(self, chunk: Chunk) -> bool:
        return chunk.box_number == self.box and (not self.title or chunk.title == self.title)

    def __str__(self) -> str:
        return f"{self.box} {SEPARATOR} {self.title}" if self.title else self.box


# ── cases ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RetrievalCase:
    family: str
    query: str
    expected: tuple[Label, ...]

    def accepts(self, chunk: Chunk) -> bool:
        """Is this chunk a valid answer?"""
        return any(label.matches(chunk) for label in self.expected)

    def hit_positions(self, chunks: Iterable[Chunk]) -> tuple[int, ...]:
        """Where a valid answer appears in the ranking (1 = first)."""
        return tuple(i for i, chunk in enumerate(chunks, 1) if self.accepts(chunk))

    def as_dict(self) -> dict[str, Any]:
        return {"family": self.family, "query": self.query, "expected": [str(label) for label in self.expected]}


@dataclass(frozen=True, slots=True)
class UncoveredCase:
    """A question the corpus does NOT answer. Not part of recall: there is no right chunk.

    It is there for the sufficiency stage. The grade matters: ``mentioned`` is the hard case,
    because retrieval DOES return something with a good score and it looks like an answer.
    """

    grade: str
    query: str

    def as_dict(self) -> dict[str, Any]:
        return {"grade": self.grade, "query": self.query}


@dataclass(frozen=True, slots=True)
class RetrievalDataset:
    locale: str
    cases: tuple[RetrievalCase, ...]
    uncovered: tuple[UncoveredCase, ...] = ()
    description: str = ""
    source: Path | None = field(default=None, compare=False)

    # ── loading ──────────────────────────────────────────────────────────────

    @classmethod
    def path_for(cls, locale: str, directory: Path = DATASETS_DIR) -> Path:
        return directory / locale / RETRIEVAL_FILE

    @classmethod
    def load(cls, locale: str, directory: Path = DATASETS_DIR) -> RetrievalDataset:
        path = cls.path_for(locale, directory)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise DatasetError(f"no retrieval dataset for locale {locale!r}: {path}") from exc
        except ValueError as exc:
            raise DatasetError(f"{path} is not valid JSON: {exc}") from exc
        dataset = cls.from_dict(data, source=path)
        if dataset.locale != locale:
            raise DatasetError(f"{path} declares locale {dataset.locale!r}, expected {locale!r}")
        return dataset

    @classmethod
    def from_dict(cls, data: object, source: Path | None = None) -> RetrievalDataset:
        where = str(source or "dataset")
        if not isinstance(data, dict):
            raise DatasetError(f"{where}: the top level must be an object")
        locale = data.get("locale")
        if not isinstance(locale, str) or not locale:
            raise DatasetError(f"{where}: 'locale' is required")
        raw_cases = data.get("cases")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise DatasetError(f"{where}: 'cases' must be a non-empty list")
        cases = tuple(cls._case(item, f"{where} case {i}") for i, item in enumerate(raw_cases, 1))
        raw_uncovered = data.get("uncovered", [])
        if not isinstance(raw_uncovered, list):
            raise DatasetError(f"{where}: 'uncovered' must be a list")
        uncovered = tuple(cls._uncovered(item, f"{where} uncovered {i}") for i, item in enumerate(raw_uncovered, 1))
        return cls(locale, cases, uncovered, str(data.get("description", "")), source)

    @staticmethod
    def _case(item: object, where: str) -> RetrievalCase:
        if not isinstance(item, dict) or set(item) != {"family", "query", "expected"}:
            raise DatasetError(f"{where}: needs exactly the keys family, query, expected")
        family, query, expected = item["family"], item["query"], item["expected"]
        if family not in FAMILIES:
            raise DatasetError(f"{where}: unknown family {family!r}; known: {', '.join(FAMILIES)}")
        if not isinstance(query, str) or not query.strip():
            raise DatasetError(f"{where}: 'query' must be a non-empty string")
        if not isinstance(expected, list) or not expected:
            raise DatasetError(f"{where}: 'expected' must be a non-empty list of labels")
        return RetrievalCase(family, query, tuple(Label.parse(label) for label in expected))

    @staticmethod
    def _uncovered(item: object, where: str) -> UncoveredCase:
        if not isinstance(item, dict) or set(item) != {"grade", "query"}:
            raise DatasetError(f"{where}: needs exactly the keys grade, query")
        grade, query = item["grade"], item["query"]
        if grade not in UNCOVERED_GRADES:
            raise DatasetError(f"{where}: unknown grade {grade!r}; known: {', '.join(UNCOVERED_GRADES)}")
        if not isinstance(query, str) or not query.strip():
            raise DatasetError(f"{where}: 'query' must be a non-empty string")
        return UncoveredCase(grade, query)

    # ── views ────────────────────────────────────────────────────────────────

    @property
    def families(self) -> tuple[str, ...]:
        """The families present, in the canonical order."""
        present = {case.family for case in self.cases}
        return tuple(f for f in FAMILIES if f in present)

    def of_family(self, family: str) -> tuple[RetrievalCase, ...]:
        return tuple(case for case in self.cases if case.family == family)

    @property
    def easy(self) -> tuple[RetrievalCase, ...]:
        return self.of_family(EASY)

    @property
    def hard(self) -> tuple[RetrievalCase, ...]:
        return tuple(case for case in self.cases if case.family != EASY)

    def subset(self, per_family: int) -> RetrievalDataset:
        """The first ``per_family`` cases of each family (and of the uncovered set): quick runs."""
        kept = [case for family in self.families for case in self.of_family(family)[:per_family]]
        return RetrievalDataset(self.locale, tuple(kept), self.uncovered[:per_family], self.description, self.source)

    # ── validation ───────────────────────────────────────────────────────────

    def problems(self, corpus: KnowledgeCorpus) -> list[str]:
        """Every label that does not exist in ``corpus``. Empty list = the dataset is sound."""
        titles = {(chunk.box_number, chunk.title) for chunk in corpus.chunks}
        found: list[str] = []
        for case in self.cases:
            for label in case.expected:
                if not corpus.has_box(label.box):
                    found.append(f"[{case.family}] {case.query!r}: box {label.box} does not exist")
                elif label.is_chunk and (label.box, label.title) not in titles:
                    found.append(f"[{case.family}] {case.query!r}: no chunk {str(label)!r} in the {corpus.locale} corpus")
        return found

    def as_dict(self) -> dict[str, Any]:
        return {"locale": self.locale, "description": self.description,
                "cases": [case.as_dict() for case in self.cases],
                "uncovered": [case.as_dict() for case in self.uncovered]}


def dump_dataset(data: Mapping[str, Any]) -> str:
    """The on-disk format: one case per line, so a diff shows exactly which case changed."""

    def line(item: Mapping[str, Any]) -> str:
        return json.dumps(item, ensure_ascii=False)

    parts = ["{",
             f'  "locale": {json.dumps(data["locale"])},',
             f'  "description": {json.dumps(data.get("description", ""), ensure_ascii=False)},',
             '  "cases": [']
    cases = list(data["cases"])
    parts += [f"    {line(case)}{',' if i < len(cases) else ''}" for i, case in enumerate(cases, 1)]
    parts.append("  ],")
    parts.append('  "uncovered": [')
    uncovered = list(data.get("uncovered", []))
    parts += [f"    {line(case)}{',' if i < len(uncovered) else ''}" for i, case in enumerate(uncovered, 1)]
    parts += ["  ]", "}"]
    return "\n".join(parts) + "\n"


# ── cross-locale alignment ───────────────────────────────────────────────────


def titles_by_box(corpus: KnowledgeCorpus) -> dict[str, list[str]]:
    """Box number -> chunk titles in corpus order."""
    boxes: dict[str, list[str]] = {}
    for chunk in corpus.chunks:
        boxes.setdefault(chunk.box_number, []).append(chunk.title)
    return boxes


def align_titles(source: KnowledgeCorpus, target: KnowledgeCorpus) -> dict[tuple[str, str], str]:
    """``(box, source title) -> target title``, by position inside each box.

    Refuses to guess: if a box does not have the same number of sections in both corpora the
    position means nothing, and a wrong label is worse than no label.
    """
    source_boxes, target_boxes = titles_by_box(source), titles_by_box(target)
    if set(source_boxes) != set(target_boxes):
        raise DatasetError(f"the {source.locale} and {target.locale} corpora do not have the same boxes")
    mapping: dict[tuple[str, str], str] = {}
    for box, titles in source_boxes.items():
        counterpart = target_boxes[box]
        if len(titles) != len(counterpart):
            raise DatasetError(f"box {box}: {len(titles)} sections in {source.locale}, "
                               f"{len(counterpart)} in {target.locale}; the corpora are out of step")
        mapping.update({(box, title): other for title, other in zip(titles, counterpart, strict=True)})
    return mapping


def translate_labels(labels: Sequence[Label], mapping: Mapping[tuple[str, str], str]) -> tuple[Label, ...]:
    """Box labels stay; chunk labels point at the same section in the other language."""
    translated: list[Label] = []
    for label in labels:
        if not label.is_chunk:
            translated.append(label)
            continue
        key = (label.box, label.title)
        if key not in mapping:
            raise DatasetError(f"cannot align {str(label)!r}: no such chunk in the source corpus")
        translated.append(Label(label.box, mapping[key]))
    return tuple(translated)


def aligned_expectations(
    source: RetrievalDataset, target: RetrievalDataset, mapping: Mapping[tuple[str, str], str]
) -> list[tuple[Label, ...]]:
    """The expected labels the target dataset MUST have, case by case, from the source one.

    Both datasets hold the same questions in two languages: same number of cases, same
    families, same order. Only the query text differs.
    """
    if len(source.cases) != len(target.cases):
        raise DatasetError(f"{len(source.cases)} cases in {source.locale}, {len(target.cases)} in {target.locale}")
    aligned: list[tuple[Label, ...]] = []
    for i, (mine, theirs) in enumerate(zip(source.cases, target.cases, strict=True), 1):
        if mine.family != theirs.family:
            raise DatasetError(f"case {i}: family {mine.family!r} in {source.locale}, "
                               f"{theirs.family!r} in {target.locale}")
        aligned.append(translate_labels(mine.expected, mapping))
    return aligned
