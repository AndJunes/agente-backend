"""Checking what the agent is about to say against what the corpus permits.

`ClaimAuditor` is the precedent: mirag compares a claim that tests passed against whether
anything ran, and warns when the two disagree. The equivalent here is different, because this
agent runs nothing. What it can get wrong is citation — and citation is the one promise this
knowledge base makes.

Two checks, both mechanical, both cheap:

**An invented citation.** The register holds 165 resolvable ids. An answer carrying `[S404]`
has fabricated a source, and that is worse than an unsourced answer: it is an unsourced answer
wearing the corpus's own guarantee. Nothing else in the system would notice.

**A figure the corpus says not to repeat.** A handful of numbers are reproduced in the
documents so that the claims made around them are visible, with an explicit instruction not to
cite them. They are listed below with where each comes from, rather than pattern-matched,
because "a number near a warning" is not something to guess at.

What is deliberately NOT checked: whether a claim is true, whether the provenance is the right
kind, whether a disputed point was presented as settled. Those need reading, which is what the
governance skills are for. A checker that pretended to do them would be the false assurance
this whole corpus is built to avoid.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CITATION = re.compile(r"\[([SE]\d{3})\]")
REGISTERED = re.compile(r"\b([SE]\d{3})\b")

UNCITABLE: tuple[tuple[str, str, str], ...] = (
    (r"90\s*%[^.]{0,60}(complain|unhappy)",
     "the '>90% of unhappy customers never complain' figure",
     "02-discovery/identifying-unmet-needs.md — marked 'do not cite'"),
    (r"\$\s*3\.8\s*(trillion|billion)",
     "the '$3.8 trillion cost of poor customer experience' figure",
     "02-discovery/identifying-unmet-needs.md — marked 'do not cite'"),
    (r"\b20\s*%\s*(time|rule|project)",
     "Google's '20% time' and the Gmail/Maps attribution",
     "11-lifecycle-and-launch/managing-maturity.md — 'widely repeated and contested', no source"),
    (r"\b19\s*%\s*(slower|faster)",
     "the '19% slower' result, quoted without its scope conditions",
     "13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md — the honest answer is 'unresolved'"),
    (r"\$\s*11\.6\s*M",
     "the '$11.6M first-year' modelled figure",
     "13-ai-agent-collaboration/evidence-on-ai-assisted-delivery.md — [E010], a vendor projection"),
)


@dataclass(frozen=True, slots=True)
class Finding:
    kind: str
    detail: str

    def __str__(self) -> str:
        return self.detail


class CitationAuditor:
    """Reads the source register once, then checks answers against it."""

    def __init__(self, register: str) -> None:
        self._known = frozenset(REGISTERED.findall(register))
        self._uncitable = tuple((re.compile(p, re.IGNORECASE), what, where) for p, what, where in UNCITABLE)

    @property
    def registered(self) -> int:
        return len(self._known)

    def audit(self, *texts: str) -> list[Finding]:
        joined = "\n".join(t for t in texts if t)
        findings: list[Finding] = []

        if self._known:
            invented = sorted({c for c in CITATION.findall(joined) if c not in self._known})
            if invented:
                findings.append(Finding(
                    "invented_citation",
                    f"{', '.join(f'[{c}]' for c in invented)} "
                    f"{'is' if len(invented) == 1 else 'are'} not in the source register. A "
                    f"citation that does not resolve is worse than none: it carries this "
                    f"knowledge base's guarantee without its backing. Treat the claim as "
                    f"unsourced.",
                ))

        for pattern, what, where in self._uncitable:
            if pattern.search(joined):
                findings.append(Finding(
                    "uncitable_figure",
                    f"This repeats {what}, which the corpus reproduces so the claim is visible "
                    f"and instructs is not cited ({where}).",
                ))
        return findings
