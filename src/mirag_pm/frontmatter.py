"""Reading the YAML frontmatter of the corpus, without a YAML library.

``pyproject.toml`` declares ``dependencies = []`` and calls it a design constraint rather than
an accident; the Dockerfile's whole security argument rests on the image installing nothing.
Pulling in PyYAML to read eleven fields would spend that for very little.

This is not a YAML parser and does not pretend to be one. It reads the shapes this corpus
actually uses — measured across all 91 documents — and raises on anything else rather than
guessing:

    title: Product Roadmap              a scalar
    topics: [roadmap, themes]           an inline list
    sources:                            a block list
      - S119
    provenance:                         one level of nesting, values as above
      primary: [E012]

A document whose frontmatter it cannot read is a document that would silently lose its
filters, so the failure is loud.
"""

from __future__ import annotations

from dataclasses import dataclass

DELIMITER = "---"


class FrontmatterError(ValueError):
    """Malformed frontmatter. Raised rather than swallowed: a document that loses its
    metadata still retrieves, and then filtering quietly stops working for it."""


@dataclass(frozen=True, slots=True)
class Document:
    """A corpus document, split into its metadata and its prose."""

    meta: dict[str, object]
    body: str

    def text(self, key: str, default: str = "") -> str:
        value = self.meta.get(key)
        return value if isinstance(value, str) else default

    def list(self, key: str) -> tuple[str, ...]:
        value = self.meta.get(key)
        if isinstance(value, list):
            return tuple(str(item) for item in value)
        return (str(value),) if isinstance(value, str) and value else ()

    def nested(self, key: str) -> dict[str, tuple[str, ...]]:
        value = self.meta.get(key)
        if not isinstance(value, dict):
            return {}
        return {
            k: tuple(str(i) for i in v) if isinstance(v, list) else ((str(v),) if v else ())
            for k, v in value.items()
        }


def _scalar(raw: str) -> object:
    """A value, an inline list, or the empty marker that opens a block."""
    raw = raw.strip()
    if not raw:
        return None  # a block list or nested mapping follows
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()] if inner else []
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    return raw.strip("'\"")


def parse(content: str, *, source: str = "<corpus>") -> Document:
    """Split a document into frontmatter and body."""
    text = content.replace("\r\n", "\n")
    if not text.startswith(DELIMITER):
        return Document({}, text)  # the meta files carry no frontmatter, and that is fine

    end = text.find(f"\n{DELIMITER}", len(DELIMITER))
    if end == -1:
        raise FrontmatterError(f"{source}: frontmatter opened and never closed")

    meta: dict[str, object] = {}
    parent: str | None = None
    for number, line in enumerate(text[len(DELIMITER) : end].split("\n"), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line[:1].isspace()
        stripped = line.strip()

        if stripped.startswith("- "):  # a block list item, belonging to the open key
            if parent is None:
                raise FrontmatterError(f"{source}:{number}: list item before any key")
            # A key with no value could open either a list or a mapping; which one it is is
            # decided here, by the first child line, rather than guessed when the key is read.
            # Guessing wrong dropped every block list in the corpus without saying anything.
            if meta.get(parent) is None:
                meta[parent] = []
            target = meta[parent]
            if not isinstance(target, list):
                raise FrontmatterError(f"{source}:{number}: {parent!r} is both a mapping and a list")
            target.append(stripped[2:].strip().strip("'\""))
            continue

        key, separator, raw = stripped.partition(":")
        if not separator:
            raise FrontmatterError(f"{source}:{number}: {stripped!r} is not `key: value`")
        key = key.strip()
        value = _scalar(raw)

        if indented and parent is not None:
            if meta.get(parent) is None:
                meta[parent] = {}
            nested = meta[parent]
            if not isinstance(nested, dict):
                raise FrontmatterError(f"{source}:{number}: {parent!r} is both a list and a mapping")
            nested[key] = value if value is not None else []
        else:
            meta[key] = value
            parent = key if value is None else None

    return Document(meta, text[end + len(DELIMITER) + 1 :].lstrip("\n"))

