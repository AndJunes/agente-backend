"""Internationalisation: one folder per locale (``locales/en``, ``locales/es``).

Each locale folder holds four resources, loaded lazily and cached:

* ``messages.json`` - every user-facing string produced by the backend.
* ``ui.json``       - every string of the web page (served at ``/api/v1/i18n/<locale>``).
* ``lexicon.json``  - the language-specific heuristics: intent patterns, stop words,
                      inflection suffixes and synonym bridges.
* ``corpus.json``   - the markers of the knowledge corpus written in that language.

The knowledge corpus itself lives in ``knowledge/<locale>/``.
"""

from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.corpus_format import CorpusFormat
from mirag.i18n.lexicon import Lexicon
from mirag.i18n.registry import SUPPORTED_LOCALES, I18n, parse_accept_language

__all__ = [
    "SUPPORTED_LOCALES",
    "CorpusFormat",
    "I18n",
    "Lexicon",
    "MessageCatalog",
    "parse_accept_language",
]
