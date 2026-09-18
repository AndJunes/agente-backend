"""The markers of a knowledge corpus written in a given language.

The corpus parser never hard-codes ``Ficha`` or ``Card``: it asks the format of the
corpus it is reading. Adding a language is adding a folder, not editing the parser.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CorpusFormat:
    locale: str
    card_marker: str
    """The bold word that opens a card blockquote: ``> **Card** · ...``."""
    fields: dict[str, str]
    """Logical field -> label in the corpus (``how_it_fails`` -> ``How it fails``)."""
    failure_title_prefixes: tuple[str, ...]
    """``##`` titles that start with one of these are whole failure sections."""
    sources_title: str
    syllabus_marker: str
    labels: dict[str, str]
    """Labels used when Mirag renders derived chunks (``fails like this``, ``AVOID``...)."""

    @classmethod
    def from_file(cls, locale: str, path: Path) -> CorpusFormat:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            locale=locale,
            card_marker=data["card_marker"],
            fields=dict(data["fields"]),
            failure_title_prefixes=tuple(data["failure_title_prefixes"]),
            sources_title=data["sources_title"],
            syllabus_marker=data["syllabus_marker"],
            labels=dict(data["labels"]),
        )

    def field(self, name: str) -> str:
        return self.fields[name]

    def label(self, name: str) -> str:
        return self.labels[name]
