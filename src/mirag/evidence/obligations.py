"""Retrieved anti-patterns are an obligation. Here it is checked whether it was met.

THE GAP THIS CLOSES
    The prompt says anti-patterns must be covered "with a test EACH". Nobody checked it: the
    evidence crossed the test ids the MODEL declared with the markers, never with the
    anti-patterns that were retrieved. A model could receive six anti-patterns, declare one
    property and leave with a clean "1 verified".

WHAT IT DOES AND WHAT IT DOES NOT
    It turns each retrieved anti-pattern into an obligation with an identity and says whether
    the delivery covers it, does not, or cannot even be checked. It does NOT judge whether
    the code is correct, does not call the model, and does NOT mark an obligation covered by
    vague similarity. When in doubt: ``not_verifiable``.

WHAT CANNOT BE CLAIMED YET (measured)
    That the retrieved anti-patterns APPLY to the task. BM25 returns k results per query
    whether they are related or not, and the scores do not separate the relevant ones. So no
    threshold is set here and the table does NOT claim relevance: it says what the corpus
    brought and what the execution demonstrated.

HOW IT DECIDES
    Without calling anyone: it crosses the distinctive terms of the anti-pattern with the
    text of the properties the model declared, and then checks whether that property was
    VERIFIED by a real marker. Both are needed.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from mirag.core.text import distinctive_terms
from mirag.evidence.properties import EvidenceRow, PropertyStatus
from mirag.i18n.lexicon import Lexicon
from mirag.retrieval.service import RetrievalResult

MIN_TERM = 5
MIN_SHARED = 2
"""How many terms must coincide to consider the anti-pattern treated."""
AVOID_LINE = re.compile(r"✗ [^:\n]+:\s*(.+)")
PREFER_LINE = re.compile(r"✓ [^:\n]+:\s*(.+)")


class ObligationStatus(StrEnum):
    COVERED = "covered"
    """A declared property treats the anti-pattern AND the execution proved it."""
    DECLARED = "declared"
    """The model said it covered it and the execution did NOT prove it."""
    NOT_COVERED = "not_covered"
    """No declared property treats this anti-pattern."""
    NOT_VERIFIABLE = "not_verifiable"
    """The anti-pattern has too few distinctive terms to cross."""


@dataclass(frozen=True, slots=True)
class Obligation:
    id: str
    box: str
    title: str
    avoid: str
    prefer: str
    terms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CoverageRow:
    obligation: str
    status: ObligationStatus
    reason_code: str
    avoid: str
    property: str | None = None
    test_id: str | None = None
    property_status: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class ObligationChecker:
    def __init__(self, lexicon: Lexicon) -> None:
        self._stopwords = lexicon.words("stopwords.obligations")

    def _terms(self, *texts: str) -> tuple[str, ...]:
        words: list[str] = []
        for text in texts:
            words += distinctive_terms(text or "", MIN_TERM, self._stopwords)
        return tuple(dict.fromkeys(words))

    def from_retrieval(self, result: RetrievalResult) -> list[Obligation]:
        """The obligations of the anti-patterns REALLY retrieved."""
        out = []
        for rc in result.anti_patterns:
            text = rc.chunk.text
            avoid = (m.group(1).strip() if (m := AVOID_LINE.search(text)) else "")
            prefer = (m.group(1).strip() if (m := PREFER_LINE.search(text)) else "")
            if not avoid:
                continue  # without a "do not do this" there is nothing to measure
            out.append(Obligation(
                id=f"{rc.chunk.box_number} · {rc.chunk.title}", box=rc.chunk.box_number,
                title=rc.chunk.title, avoid=avoid, prefer=prefer,
                terms=self._terms(avoid, prefer, rc.chunk.title),
            ))
        return out

    def coverage(self, obligations: Iterable[Obligation], evidence: Sequence[EvidenceRow]) -> list[CoverageRow]:
        rows = []
        for ob in obligations:
            if len(ob.terms) < MIN_SHARED:
                rows.append(CoverageRow(ob.id, ObligationStatus.NOT_VERIFIABLE, "too_few_terms", ob.avoid))
                continue
            best: EvidenceRow | None = None
            best_shared = 0
            for row in evidence:
                shared = len(set(ob.terms) & set(self._terms(f"{row.risk} {row.property}")))
                if shared > best_shared:
                    best, best_shared = row, shared
            if best is None or best_shared < MIN_SHARED:
                rows.append(CoverageRow(ob.id, ObligationStatus.NOT_COVERED, "no_property", ob.avoid))
            elif best.status is PropertyStatus.VERIFIED:
                rows.append(CoverageRow(ob.id, ObligationStatus.COVERED, "proved_by_test", ob.avoid,
                                        best.property, best.test_id, best.status.value))
            else:
                rows.append(CoverageRow(ob.id, ObligationStatus.DECLARED, "declared_not_proved", ob.avoid,
                                        best.property, best.test_id, best.status.value))
        return rows

    @staticmethod
    def count(rows: Iterable[CoverageRow]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.status.value] = counts.get(row.status.value, 0) + 1
        return counts
