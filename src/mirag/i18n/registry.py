"""The locale registry: which languages exist and where their resources live."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.corpus_format import CorpusFormat
from mirag.i18n.lexicon import Lexicon
from mirag.paths import KNOWLEDGE_DIR, LOCALES_DIR

SUPPORTED_LOCALES: tuple[str, ...] = ("en", "es")
FALLBACK_LOCALE = "en"


def parse_accept_language(header: str | None, supported: tuple[str, ...] = SUPPORTED_LOCALES) -> str | None:
    """The best supported locale in an ``Accept-Language`` header, or ``None``.

    ``"es-AR,es;q=0.9,en;q=0.8"`` -> ``"es"``.
    """
    if not header:
        return None
    ranked: list[tuple[float, int, str]] = []
    for position, part in enumerate(header.split(",")):
        piece = part.strip()
        if not piece:
            continue
        tag, _, params = piece.partition(";")
        quality = 1.0
        if params.strip().startswith("q="):
            try:
                quality = float(params.strip()[2:])
            except ValueError:
                quality = 0.0
        ranked.append((-quality, position, tag.strip().lower().split("-")[0]))
    for _, _, primary in sorted(ranked):
        if primary in supported:
            return primary
    return None


class I18n:
    """Loads and caches every per-locale resource. Thread safe."""

    def __init__(
        self,
        default_locale: str = FALLBACK_LOCALE,
        locales_dir: Path = LOCALES_DIR,
        knowledge_dir: Path = KNOWLEDGE_DIR,
        supported: tuple[str, ...] = SUPPORTED_LOCALES,
    ) -> None:
        self.supported = supported
        self.default_locale = default_locale if default_locale in supported else FALLBACK_LOCALE
        self._locales_dir = locales_dir
        self._knowledge_dir = knowledge_dir
        self._lock = threading.Lock()
        self._catalogs: dict[str, MessageCatalog] = {}
        self._lexicons: dict[str, Lexicon] = {}
        self._formats: dict[str, CorpusFormat] = {}
        self._ui: dict[str, dict[str, Any]] = {}

    def resolve(self, requested: str | None = None, accept_language: str | None = None) -> str:
        """Explicit request > ``Accept-Language`` > configured default."""
        if requested:
            primary = requested.strip().lower().replace("_", "-").split("-")[0]
            if primary in self.supported:
                return primary
        return parse_accept_language(accept_language, self.supported) or self.default_locale

    def _checked(self, locale: str) -> str:
        if locale not in self.supported:
            raise KeyError(f"unsupported locale {locale!r}; supported: {self.supported}")
        return locale

    def locale_dir(self, locale: str) -> Path:
        return self._locales_dir / self._checked(locale)

    def knowledge_dir(self, locale: str) -> Path:
        return self._knowledge_dir / self._checked(locale)

    def catalog(self, locale: str) -> MessageCatalog:
        locale = self._checked(locale)
        with self._lock:
            if locale not in self._catalogs:
                fallback = None
                if locale != FALLBACK_LOCALE:
                    fallback = self._catalogs.get(FALLBACK_LOCALE) or MessageCatalog.from_file(
                        FALLBACK_LOCALE, self._locales_dir / FALLBACK_LOCALE / "messages.json"
                    )
                    self._catalogs.setdefault(FALLBACK_LOCALE, fallback)
                self._catalogs[locale] = MessageCatalog.from_file(
                    locale, self._locales_dir / locale / "messages.json", fallback
                )
            return self._catalogs[locale]

    def lexicon(self, locale: str) -> Lexicon:
        locale = self._checked(locale)
        with self._lock:
            if locale not in self._lexicons:
                self._lexicons[locale] = Lexicon.from_file(
                    locale, self._locales_dir / locale / "lexicon.json"
                )
            return self._lexicons[locale]

    def corpus_format(self, locale: str) -> CorpusFormat:
        locale = self._checked(locale)
        with self._lock:
            if locale not in self._formats:
                self._formats[locale] = CorpusFormat.from_file(
                    locale, self._locales_dir / locale / "corpus.json"
                )
            return self._formats[locale]

    def ui_messages(self, locale: str) -> dict[str, Any]:
        locale = self._checked(locale)
        with self._lock:
            if locale not in self._ui:
                self._ui[locale] = json.loads(
                    (self._locales_dir / locale / "ui.json").read_text(encoding="utf-8")
                )
            return self._ui[locale]
