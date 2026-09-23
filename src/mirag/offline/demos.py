"""The prepared demos: recognisable, scripted, and never served for the wrong question.

There are FOUR prepared scripts. If the question is one of them, it is answered with its
script and marked SIMULATED. If not, nothing is invented: it says there is no model, and the
rest of the pipeline - plan, retrieval, context, sufficiency - runs and is shown for real,
which is the only thing that is not simulated here.

ORDER MATTERS: from the most specific to the most general. "create a project with a
calculator" is a project request and must not take the ``code`` script.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.lexicon import Lexicon
from mirag.offline.scripts import ScriptLibrary

Script = list[dict[str, Any]]

DEMO_ORDER = ("project", "repair", "code", "conceptual")


@dataclass(frozen=True, slots=True)
class CanonicalDemo:
    """What must be possible to show without fear. ``script`` is explicit on purpose: making a
    canonical demo re-discover its script by regex is asking to be served another one."""

    key: str
    script: str | None
    requires: dict[str, Any] = field(default_factory=dict)


CANONICAL: dict[str, CanonicalDemo] = {
    "project": CanonicalDemo("project", "project", {
        "took_project_branch": True, "has_project": True, "files": 10, "project_status": ("VERIFIED",), "integrity_ok": True,
        "crud_verified": 7, "has_download": True}),
    "knowledge": CanonicalDemo("knowledge", "conceptual", {
        "has_answer": True, "has_retrieval": True, "has_code": False, "sufficiency": ("covered", "mentioned")}),
    "construction": CanonicalDemo("construction", "code", {
        "has_answer": True, "has_retrieval": True, "has_code": True, "executed": True,
        "execution_status": ("passed",), "verified_properties": 1}),
    "abstention": CanonicalDemo("abstention", None, {  # precisely: no script, that is what it proves
        "has_answer": True, "has_retrieval": True, "has_code": False,
        "sufficiency": ("mentioned", "absent"), "warns_coverage": True}),
}


class DemoCatalog:
    """Recognises the demos of one locale and hands out their scripts."""

    def __init__(self, lexicon: Lexicon, catalog: MessageCatalog) -> None:
        self._patterns = {key: lexicon.pattern(f"demos.{key}") for key in DEMO_ORDER}
        self._t = catalog
        self._scripts = ScriptLibrary(catalog)
        self._factories: dict[str, Callable[[], Script]] = {
            "project": self._scripts.books_project,
            "repair": self._scripts.broken_then_fixed,
            "code": self._scripts.calculator,
            "conceptual": self._scripts.conceptual,
        }

    @property
    def scripts(self) -> ScriptLibrary:
        return self._scripts

    def recognize(self, question: str) -> tuple[str | None, Script | None]:
        for key in DEMO_ORDER:
            if self._patterns[key].search(question or ""):
                return key, self._factories[key]()
        return None, None

    def script(self, key: str | None) -> Script:
        """The script of a demo by name. ``None`` = the "no model" one."""
        if key is None:
            return self._scripts.no_model()
        if key not in self._factories:
            raise KeyError(f"unknown script: {key!r}")
        return self._factories[key]()

    def script_for(self, question: str) -> tuple[str | None, Script]:
        """The offline script for this question. Never a demo that does not belong to it."""
        key, script = self.recognize(question)
        if key is None or script is None:
            return None, self._scripts.no_model()
        return key, script

    def canonical_question(self, key: str) -> str:
        return self._t(f"demo.canonical.{key}.question")

    def listing(self) -> list[dict[str, Any]]:
        """What the page offers: the canonical demos with their localised texts."""
        return [{"key": key, "title": self._t(f"demo.canonical.{key}.title"),
                 "question": self.canonical_question(key),
                 "demonstrates": self._t(f"demo.canonical.{key}.demonstrates"),
                 "script": CANONICAL[key].script}
                for key in ("knowledge", "construction", "abstention", "project")]

    def available_scripts(self) -> list[str]:
        return list(DEMO_ORDER)
