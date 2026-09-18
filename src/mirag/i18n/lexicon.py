"""Language-specific heuristics, loaded from ``locales/<locale>/lexicon.json``.

Mirag decides several things without calling a model: whether a request asks for code or
for a whole project, whether a term is a topic or just inflected language, whether the
model claims that tests passed. Those decisions depend on the language of the text, so
the patterns and word lists are data per locale, not code.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import Any


class Lexicon:
    """Compiled patterns and word lists for one locale."""

    def __init__(self, locale: str, data: Mapping[str, Any]) -> None:
        self.locale = locale
        self._data = data
        self._compiled: dict[str, re.Pattern[str]] = {}

    @classmethod
    def from_file(cls, locale: str, path: Path) -> Lexicon:
        return cls(locale, json.loads(path.read_text(encoding="utf-8")))

    def pattern(self, dotted: str) -> re.Pattern[str]:
        """A case-insensitive compiled regex, e.g. ``lexicon.pattern("intent.code_verbs")``."""
        if dotted not in self._compiled:
            source = self._lookup(dotted)
            if not isinstance(source, str):
                raise KeyError(f"lexicon[{self.locale}] has no pattern {dotted!r}")
            self._compiled[dotted] = re.compile(source, re.IGNORECASE)
        return self._compiled[dotted]

    def words(self, dotted: str) -> frozenset[str]:
        value = self._lookup(dotted)
        return frozenset(value or ())

    def sequence(self, dotted: str) -> tuple[str, ...]:
        value = self._lookup(dotted)
        return tuple(value or ())

    def mapping(self, dotted: str) -> dict[str, tuple[str, ...]]:
        value = self._lookup(dotted) or {}
        return {key: tuple(items) for key, items in value.items()}

    def patterns(self, dotted: str) -> dict[str, re.Pattern[str]]:
        """Every pattern of a section, compiled, keeping the file order."""
        section = self._lookup(dotted) or {}
        return {name: self.pattern(f"{dotted}.{name}") for name in section}

    @cached_property
    def inflection_suffixes(self) -> tuple[str, ...]:
        return self.sequence("inflection_suffixes")

    def _lookup(self, dotted: str) -> Any:
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, Mapping) or part not in node:
                return None
            node = node[part]
        return node
