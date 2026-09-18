"""Contrasts what the model CLAIMS with what the execution DEMONSTRATES.

WHY IT IS NEEDED EVEN THOUGH THE EXECUTOR NO LONGER LIES
    The runner no longer tells an empty script "TESTS PASSED". But the model can claim
    whatever it wants in its final prose, and that prose was reviewed by nobody:

        real execution   ->  NO EVIDENCE (0 markers)
        final answer     ->  "Perfect. The 3 test cases really passed."

    Both sentences lived on the same screen without contradicting each other. This makes
    them contradict each other.

WHAT IT DOES AND WHAT IT DOES NOT
    It does NOT rewrite or trim the model's answer: the code may be perfectly fine and only
    the marker format is missing. It PREPENDS a warning so nobody reads the claim without the
    context. It does not judge whether the code is correct; it judges whether the CLAIM is
    backed.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from enum import StrEnum

from mirag.execution.verdict import ExecutionResult, ExecutionStatus
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.lexicon import Lexicon


class ClaimStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    REFUTED = "refuted"
    NOT_EXECUTED = "not_executed"
    NO_CLAIM = "no_claim"


class ClaimAuditor:
    def __init__(self, lexicon: Lexicon, catalog: MessageCatalog) -> None:
        # The success pattern is deliberately short: the more forms, the more false
        # positives, and a warning that fires when it should not ends up ignored.
        self._claims_success = lexicon.pattern("claims.success")
        self._already_warns = lexicon.pattern("claims.already_warns")
        self._t = catalog

    @staticmethod
    def all_markers(results: Iterable[ExecutionResult]) -> dict[str, str]:
        markers: dict[str, str] = {}
        for result in results:
            markers.update(result.markers)
        return markers

    def audit(
        self,
        answer: str | None,
        results: Sequence[ExecutionResult] = (),
        declared_properties: Iterable[object] | None = None,
    ) -> tuple[str | None, ClaimStatus]:
        """``(warning | None, status)``."""
        text = answer or ""
        markers = self.all_markers(results)
        passing = [k for k, v in markers.items() if v == "PASS"]
        failing = [k for k, v in markers.items() if v == "FAIL"]
        claims = bool(self._claims_success.search(text))

        # 1. the model claims that something that failed passed
        if claims and failing:
            ids = ", ".join(f"`{f}`" for f in sorted(failing))
            return self._warning("contradicted", count=len(failing), ids=ids), ClaimStatus.REFUTED

        # 2. it claims, but nothing even ran
        if claims and results and all(r.status is ExecutionStatus.NOT_EXECUTED for r in results):
            return (self._warning("not_executed", header=results[-1].describe(self._t)),
                    ClaimStatus.NOT_EXECUTED)

        # 3. it claims and there is not one marker backing it - the empty-script case
        if claims and not passing and not self._already_warns.search(text):
            key = "no_markers" if results else "nothing_ran"
            return self._warning(key), ClaimStatus.UNSUPPORTED

        # 4. it declared properties and none appeared in the output
        declared = [p for p in (declared_properties or ()) if isinstance(p, Mapping)]
        test_ids = [str(p.get("test_id", "")).strip() for p in declared]
        if test_ids and not any(i in markers for i in test_ids if i):
            return self._warning("no_property_proved", count=len(test_ids)), ClaimStatus.UNSUPPORTED

        if claims and passing:
            return None, ClaimStatus.SUPPORTED
        return None, ClaimStatus.NO_CLAIM

    def _warning(self, key: str, **params: object) -> str:
        title = self._t(f"claims.{key}.title")
        body = self._t(f"claims.{key}.body", **params)
        return f"> ⚠️ **{title}**\n>\n> {body}"

    def apply(
        self,
        answer: str | None,
        results: Sequence[ExecutionResult] = (),
        declared_properties: Iterable[object] | None = None,
    ) -> tuple[str, ClaimStatus]:
        """The answer with the warning prepended when needed. The original text is untouched."""
        warning, status = self.audit(answer, results, declared_properties)
        if not warning:
            return answer or "", status
        return f"{warning}\n\n{answer or ''}", status
