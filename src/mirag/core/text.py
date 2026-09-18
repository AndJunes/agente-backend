"""Text helpers shared by retrieval, planning and auditing.

They live in one place so that "normalised" means exactly the same thing everywhere: a
query normalised one way and a chunk normalised another never match, and the bug looks
like bad ranking instead of what it is.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable

_WORD = re.compile(r"[a-z0-9]+")


def strip_accents(text: str) -> str:
    """``"cuántos días"`` -> ``"cuantos dias"``. Case is preserved."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def normalize(text: str) -> str:
    """Lower case and without accents, so that ``"Índice"`` matches ``"indice"``."""
    return strip_accents((text or "").lower())


def normalize_words(text: str) -> str:
    """Lower case, no accents, punctuation collapsed to single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", normalize(text)).strip()


def distinctive_terms(text: str, min_length: int, stopwords: Iterable[str] = ()) -> list[str]:
    """The words of ``text`` long enough to discriminate, in order and without repeats."""
    stop = set(stopwords)
    words = re.findall(rf"[a-z0-9]{{{min_length},}}", normalize(text))
    return [w for w in dict.fromkeys(words) if w not in stop]


def sha256_hex(data: bytes) -> str:
    """The FULL sha256. Never truncated when the hash is a proof of identity."""
    return hashlib.sha256(data).hexdigest()


def short_hash(text: str, length: int = 16) -> str:
    """A truncated hash, only for change detection (never for integrity)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def first_json_object(text: str) -> dict | None:
    """The first balanced JSON object embedded in ``text`` (which may be wrapped in prose).

    It walks balanced braces instead of using a regex: models nest objects, and both a
    greedy and a lazy ``\\{.*\\}`` get it wrong in opposite directions.
    """
    start = text.find("{")
    while start != -1:
        depth, in_string, escaped = 0, False, False
        for index in range(start, len(text)):
            char = text[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
            elif char == '"':
                in_string = not in_string
            elif not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            value = json.loads(text[start : index + 1], strict=False)
                        except json.JSONDecodeError:
                            break
                        return value if isinstance(value, dict) else None
        start = text.find("{", start + 1)
    return None


def repair_truncated_json(text: str) -> dict | None:
    """Last attempt on a JSON object cut in half (``max_tokens`` stops mid-object).

    It records every "healthy" cut point (a comma or a closing bracket outside strings)
    together with the brackets still open there. Cutting at one of those points and closing
    that stack always yields valid JSON, even when the cut fell inside a nested array.
    """
    start = text.find("{")
    if start == -1:
        return None
    body = text[start:]
    stack: list[str] = []
    in_string = escaped = False
    healthy: list[tuple[int, tuple[str, ...]]] = []
    for index, char in enumerate(body):
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            in_string = not in_string
        elif not in_string:
            if char in "{[":
                stack.append("}" if char == "{" else "]")
            elif char in "}]":
                if stack:
                    stack.pop()
                healthy.append((index + 1, tuple(stack)))
            elif char == ",":
                healthy.append((index, tuple(stack)))
    for cut, still_open in reversed(healthy):
        attempt = body[:cut] + "".join(reversed(still_open))
        try:
            value = json.loads(attempt, strict=False)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def as_list(value: object, limit: int = 12) -> list[str]:
    """Whatever the model sent -> a clean list of strings. Models send everything."""
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[object] = re.split(r"[,;\n]", value)
    elif isinstance(value, dict):
        items = list(value.values())
    elif isinstance(value, list | tuple | set):
        items = value
    else:
        items = [value]
    out: list[str] = []
    for item in items:
        text = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        text = text.strip(" \t\"'*·-")
        if text and text.lower() not in ("none", "null", "n/a", "-"):
            out.append(text)
    return out[:limit]


def as_bool(value: object) -> bool:
    """``"true"``, ``"sí"``, ``"yes"``, ``1`` -> ``True``."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "si", "sí", "yes", "1")
    return bool(value)


def lenient_json_list(value: object) -> list:
    """A list, however it arrives.

    Shapes that really arrived from models: a list of dicts, a list of strings, a string
    with JSON inside (sometimes DOUBLE escaped), a bare string and ``None``. Structured
    outputs narrow the output; they do not guarantee it.
    """
    if value is None:
        return []
    if isinstance(value, str):

        def unescape(raw: str) -> str:
            # unicode_escape reads bytes as Latin-1 and breaks UTF-8 ("acción" -> "acciÃ³n");
            # the round trip through latin-1 keeps it intact.
            return raw.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")

        for prepare in (lambda raw: raw, unescape):
            try:
                return lenient_json_list(json.loads(prepare(value), strict=False))
            except (json.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError):
                continue
        return [value]
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


def text_list(value: object) -> list[str]:
    """Like :func:`lenient_json_list`, with every element rendered as text."""
    return [
        item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        for item in lenient_json_list(value)
    ]


def words(text: str) -> list[str]:
    return _WORD.findall(normalize(text))
