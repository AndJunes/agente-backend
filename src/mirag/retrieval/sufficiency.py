"""Is what was retrieved enough to answer, or must we say that it is not known?

THE PROBLEM IT SOLVES
    Retrieval ALWAYS returns something. Ask about Raft and it returns "CAP, PACELC and
    consistency" with a good score, because Raft is mentioned four times in the corpus. A
    system that does not tell MENTION from COVERAGE answers confidently about something that
    was never documented.

THE SIGNAL THAT SEPARATES THEM
    The corpus has structure: each chunk has a TITLE and most have a CARD. A concept the
    corpus really covers appears in a title or a card. A concept that is only mentioned
    appears only in prose.

        Kubernetes  -> there is a chunk titled "Kubernetes"          -> covered
        Raft        -> it only appears loose inside other chunks     -> mentioned
        WebRTC      -> it appears nowhere                            -> absent

WHAT IS DONE WITH THE VERDICT
    Only saying it. This module does not decide whether to answer: it marks the grade and
    the reason so the pipeline and the UI can say "this is not covered" instead of padding.

KNOWN LIMITS
    · It works on words: a question using synonyms of something covered can come out
      'mentioned'. That is a false negative, and it is preferred over the opposite error.
    · A common term that appears in any title counts as covered even if that title is
      unrelated.
    · It does not measure whether the ANSWER is correct, only whether the corpus has
      material on the topic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from typing import Any

from mirag.core.text import distinctive_terms, normalize
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.lexicon import Lexicon
from mirag.retrieval.corpus import Chunk, KnowledgeCorpus
from mirag.retrieval.plan import RetrievalPlan


class Grade(StrEnum):
    COVERED = "covered"
    MENTIONED = "mentioned"
    ABSENT = "absent"
    NOT_EVALUATED = "not_evaluated"


MIN_TERM = 4
"""Below this a word discriminates nothing."""
TOO_COMMON = 25
"""A term found in more than N chunks cannot judge coverage."""
REALLY_RARE = 6
"""To say "only mentioned" the term must be rare."""
MIN_ABSENT = 6
"""A short missing word ('slot', 'left') is not a hole in the corpus."""
PREFIX = 4
"""'reserven' must match 'reservar'; 'indexing' must match 'index': same word."""


@dataclass(frozen=True, slots=True)
class SufficiencyVerdict:
    sufficient: bool
    grade: Grade
    reason: str
    terms: dict[str, str] = field(default_factory=dict)
    """term -> ``title`` | ``card`` | ``prose`` | ``absent``."""
    signals: dict[str, Any] = field(default_factory=dict)
    warning: str = ""
    """What is shown to whoever asked. Empty when there is nothing honest to warn about."""


class SufficiencyEvaluator:
    """Judges whether the corpus covers a query, using the whole corpus (not the hits)."""

    def __init__(self, corpus: KnowledgeCorpus, lexicon: Lexicon, catalog: MessageCatalog) -> None:
        self._corpus = corpus
        self._stopwords = lexicon.words("stopwords.sufficiency")
        self._suffixes = lexicon.inflection_suffixes
        self._t = catalog
        self._titles = [normalize(c.title) for c in corpus.chunks]
        self._where = lru_cache(maxsize=4096)(self._locate)

    def not_evaluated(self, reason: str) -> SufficiencyVerdict:
        """SUFFICIENCY=off. ``sufficient=True`` does not claim coverage: it claims there is no
        warning to give, because nobody looked. That stays in the reason, not in a silence."""
        return SufficiencyVerdict(True, Grade.NOT_EVALUATED, reason, {}, {"evaluated": False})

    def _locate(self, term: str) -> tuple[str, int]:
        """Where a term lives and in how many chunks: ``(place, frequency)``."""
        short = term[:PREFIX]

        def inside(text: str) -> bool:
            return term in text or short in text

        frequency = sum(1 for c in self._corpus.chunks if inside(c.norm))
        if any(inside(title) for title in self._titles):
            return "title", frequency
        if any(inside(card.norm) for card in self._corpus.cards):
            return "card", frequency
        return ("prose" if frequency else "absent"), frequency

    def evaluate(
        self,
        query: str,
        retrieved: Sequence[tuple[Chunk, float]] = (),
        plan: RetrievalPlan | None = None,
    ) -> SufficiencyVerdict:
        terms = distinctive_terms(query, MIN_TERM, self._stopwords)
        # what the plan says is strictly needed weighs the same as what the user asked
        if plan is not None:
            for extra in (*plan.technologies, *plan.required_knowledge):
                for word in distinctive_terms(str(extra), MIN_TERM, self._stopwords):
                    if word not in terms:
                        terms.append(word)
        if not terms:
            return SufficiencyVerdict(
                True, Grade.COVERED, self._t("sufficiency.reason.no_terms"), {}, {"terms": 0}
            )

        places = {t: self._where(t) for t in terms}
        where = {t: place for t, (place, _) in places.items()}
        # Only RARE terms judge. One found in half the encyclopedia ('service') says
        # nothing about whether the topic is covered, and averaging it drowned exactly the
        # term that mattered: 'webrtc' got lost among 'streaming', 'video' and 'time'.
        judging = {t: place for t, (place, freq) in places.items() if freq <= TOO_COMMON}
        ignored = [t for t in terms if t not in judging]
        covered = [t for t, place in judging.items() if place in ("title", "card")]
        only_prose = [t for t, place in judging.items() if place == "prose" and places[t][1] <= REALLY_RARE]
        # an absent term only counts if it is not inflected language and it is long:
        # 'webrtc' or 'pytorch' missing is the whole topic; 'slot' missing is nothing.
        absent = [
            t for t, place in judging.items()
            if place == "absent" and not t.endswith(self._suffixes) and len(t) >= MIN_ABSENT
        ]
        scores = [score for _, score in retrieved]
        signals = {
            "terms": len(terms), "judging": len(judging), "ignored_as_common": ignored,
            "covered": len(covered), "only_prose": len(only_prose), "absent": len(absent),
            "best_score": round(scores[0], 3) if scores else 0.0, "retrieved": len(retrieved),
        }

        if not retrieved:
            return self._insufficient(Grade.ABSENT, self._t("sufficiency.reason.nothing_retrieved"),
                                      where, signals)
        # ONE rare uncovered term is enough not to be able to answer: it carries the topic
        if absent:
            return self._insufficient(Grade.ABSENT, self._t("sufficiency.reason.absent", terms=", ".join(absent)),
                                      where, signals)
        if only_prose:
            return self._insufficient(Grade.MENTIONED,
                                      self._t("sufficiency.reason.mentioned", terms=", ".join(only_prose)),
                                      where, signals)
        if not judging:
            return SufficiencyVerdict(True, Grade.COVERED, self._t("sufficiency.reason.all_common"), where, signals)
        return SufficiencyVerdict(
            True, Grade.COVERED, self._t("sufficiency.reason.covered", count=len(judging)), where, signals
        )

    def _insufficient(
        self, grade: Grade, reason: str, where: dict[str, str], signals: dict[str, Any]
    ) -> SufficiencyVerdict:
        weak = [t for t, place in where.items() if place in ("prose", "absent")] or list(where)
        key = "sufficiency.warning.absent" if grade is Grade.ABSENT else "sufficiency.warning.mentioned"
        warning = self._t(key, terms=", ".join(weak), boxes=len(self._corpus.boxes))
        return SufficiencyVerdict(False, grade, reason, where, signals, warning)
