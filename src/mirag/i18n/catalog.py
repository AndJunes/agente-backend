"""Message catalogs: dotted keys to localised templates."""

from __future__ import annotations

import json
import string
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class _SafeFormatter(string.Formatter):
    """``str.format`` that leaves unknown placeholders visible instead of raising.

    A missing parameter in a message must never take down a response that already cost
    money; it shows up as ``{name}`` and a test catches it.
    """

    def get_value(self, key: int | str, args: Any, kwargs: Any) -> Any:
        if isinstance(key, str) and key not in kwargs:
            return "{" + key + "}"
        return super().get_value(key, args, kwargs)


_FORMATTER = _SafeFormatter()


def flatten(tree: Mapping[str, Any], prefix: str = "") -> dict[str, str]:
    """``{"a": {"b": "x"}}`` -> ``{"a.b": "x"}``."""
    flat: dict[str, str] = {}
    for key, value in tree.items():
        dotted = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(flatten(value, dotted + "."))
        else:
            flat[dotted] = str(value)
    return flat


class MessageCatalog:
    """Translates dotted keys for one locale, falling back to another catalog."""

    def __init__(
        self,
        locale: str,
        messages: Mapping[str, str],
        fallback: MessageCatalog | None = None,
    ) -> None:
        self.locale = locale
        self._messages = dict(messages)
        self._fallback = fallback

    @classmethod
    def from_file(cls, locale: str, path: Path, fallback: MessageCatalog | None = None) -> MessageCatalog:
        tree = json.loads(path.read_text(encoding="utf-8"))
        return cls(locale, flatten(tree), fallback)

    def keys(self) -> set[str]:
        return set(self._messages)

    def has(self, key: str) -> bool:
        return key in self._messages or (self._fallback is not None and self._fallback.has(key))

    def template(self, key: str) -> str:
        if key in self._messages:
            return self._messages[key]
        if self._fallback is not None:
            return self._fallback.template(key)
        return key

    def t(self, key: str, **params: Any) -> str:
        """The message for ``key`` in this locale, formatted with ``params``."""
        template = self.template(key)
        if not params:
            return template
        return _FORMATTER.format(template, **params)

    def plural(self, key: str, count: int, **params: Any) -> str:
        """``key.one`` when ``count == 1``, else ``key.other``."""
        form = "one" if count == 1 else "other"
        return self.t(f"{key}.{form}", count=count, **params)

    __call__ = t
