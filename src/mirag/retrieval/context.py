"""THE only place that decides what enters the prompt.

No other module may call the corpus searches again to assemble the context of a request
that already went through here. If more knowledge is needed, it is requested in the
:class:`RetrievalResult`, not through a second path.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from mirag.core.text import short_hash
from mirag.retrieval.service import INDICES, RetrievalResult

CONTEXT_LIMIT = 24_000
"""Characters (~6k tokens): a hard ceiling so the prompt does not grow on its own."""

SECTION_HEADERS = {
    "knowledge": "=== RETRIEVED KNOWLEDGE ===",
    "anti_patterns": "=== ANTI-PATTERNS (cover EACH ONE with a test) ===",
    "failures": "=== KNOWN FAILURE MODES ===",
}


@dataclass(frozen=True, slots=True)
class ContextMeasures:
    chars: int
    approx_tokens: int
    included: int
    discarded: list[tuple[str, str]]
    sha: str

    def as_dict(self, with_discarded: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "chars": self.chars, "approx_tokens": self.approx_tokens,
            "included": self.included, "sha": self.sha,
        }
        if with_discarded:
            data["discarded"] = [list(item) for item in self.discarded]
        return data


class ContextBuilder:
    """Builds the model context from a :class:`RetrievalResult`."""

    def __init__(self, limit: int = CONTEXT_LIMIT) -> None:
        self.limit = limit

    def build(
        self,
        result: RetrievalResult,
        request: str | None = None,
        symbols: Sequence[str] = (),
        coverage_warning: str | None = None,
        extra_instructions: str | None = None,
        limit: int | None = None,
    ) -> tuple[str, ContextMeasures]:
        limit = self.limit if limit is None else limit
        request = result.query if request is None else request
        blocks = [f"USER REQUEST:\n{request}"]
        seen: set[tuple[str, str]] = set()  # dedup by identity, not by text
        discarded: list[tuple[str, str]] = []

        for spec in INDICES:
            texts = []
            for rc in result.by_index.get(spec.name, ()):
                if rc.chunk.key in seen:  # the same chunk may come from two indices
                    discarded.append((rc.id, "duplicate"))
                    continue
                seen.add(rc.chunk.key)
                texts.append(rc.chunk.text)
            blocks.append(f"{SECTION_HEADERS[spec.name]}\n" + (spec.separator.join(texts) or "No results."))

        if symbols:
            blocks.append("=== PROJECT CODE ===\n" + "\n".join(symbols))
        if coverage_warning:
            blocks.append("=== COVERAGE WARNING ===\n" + coverage_warning
                          + "\nDo not invent what is missing: say that the corpus does not cover it.")
        if extra_instructions:
            blocks.append(extra_instructions)

        context = "\n\n".join(blocks)
        if len(context) > limit:
            # A hard cut of the tail, and it is said: the tail holds the failure modes and
            # the extra instructions. With the per-index k values the context stays well below
            # the limit in practice; the cut exists so it can never grow without bound.
            context = context[:limit] + "\n\n[context truncated at the limit]"
            discarded.append(("(tail of the context)", f"limit of {limit} characters"))
        return context, ContextMeasures(
            chars=len(context),
            approx_tokens=len(context) // 4,
            included=len(seen),
            discarded=discarded,
            sha=short_hash(context),
        )
