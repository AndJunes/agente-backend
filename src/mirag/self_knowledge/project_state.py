"""What Mirag knows about itself, without asking retrieval or the model.

Questions like "which model do you use?" or "how many boxes are there?" need no search and
no LLM: the answer is a fact of the project. This shortcut answers them in milliseconds and
at zero cost.

If the question does NOT fit, it returns ``None`` and the normal flow goes on: a shortcut
that guesses is worse than no shortcut. And if the request is a WORK ORDER, the shortcut
steps aside: it answers questions ABOUT Mirag, it does not accept jobs. Without that guard,
a prompt asking to generate and verify code was swallowed by the shortcut because of the
word "output", returning 0 calls and no work done.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from mirag.core.text import normalize
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.lexicon import Lexicon
from mirag.retrieval.corpus import KnowledgeCorpus

ENTRY_POINTS: tuple[tuple[str, str], ...] = (
    ("api/server.py", "server"),
    ("pipeline/orchestrator.py", "pipeline"),
    ("retrieval/service.py", "retrieval"),
    ("execution/verdict.py", "verdict"),
    ("evidence/obligations.py", "obligations"),
    ("features/flags.py", "features"),
    ("offline/demos.py", "demos"),
)


@dataclass(frozen=True, slots=True)
class SystemFacts:
    """The facts the shortcut answers with. Built from the real objects, never repeated by hand."""

    model: str
    modes: Sequence[str]
    tools: Sequence[str]
    output_dir: Path
    symbol_summary: Mapping[str, int] = field(default_factory=dict)
    module_count: int = 0


class ProjectStateResponder:
    def __init__(self, lexicon: Lexicon, catalog: MessageCatalog, corpus: KnowledgeCorpus,
                 facts: Callable[[], SystemFacts]) -> None:
        self._work = lexicon.pattern("project_state.work_verbs")
        self._shortcuts = lexicon.patterns("project_state.shortcuts")
        self._t = catalog
        self._corpus = corpus
        self._facts = facts

    def is_work_order(self, question: str) -> bool:
        return bool(self._work.search(normalize(question)))

    def answer(self, question: str) -> str | None:
        """The answer if the question is about Mirag itself; ``None`` otherwise."""
        text = normalize(question)
        if self.is_work_order(text):
            return None  # there is work to do: not a state question
        for name, pattern in self._shortcuts.items():
            if pattern.search(text):
                facts = self._facts()
                body = getattr(self, f"_{name}")(facts)
                return (f"## {self._t(f'state.title.{name}')}\n\n{body}\n\n"
                        f"*{self._t('state.footer')}*")
        return None

    # ── one renderer per shortcut ────────────────────────────────────────────

    def _model(self, facts: SystemFacts) -> str:
        return self._t("state.model", model=facts.model)

    def _modes(self, facts: SystemFacts) -> str:
        return "\n".join(f"- **{mode}** — {self._t(f'state.mode.{mode}')}" for mode in facts.modes)

    def _tools(self, facts: SystemFacts) -> str:
        return "\n".join(f"- `{tool}`" for tool in facts.tools)

    def _corpus_size(self, facts: SystemFacts) -> str:
        stats = self._corpus.stats()
        return self._t("state.corpus_size", boxes=stats["boxes"], chunks=stats["chunks"], cards=stats["cards"],
                       anti_patterns=stats["anti_patterns"], tokens=f"{stats['characters'] // 4:,}")

    def _boxes(self, facts: SystemFacts) -> str:
        return "\n".join(f"- {box}" for box in self._corpus.boxes)

    def _output_location(self, facts: SystemFacts) -> str:
        return self._t("state.output_location", folder=str(facts.output_dir))

    def _structure(self, facts: SystemFacts) -> str:
        """Where to start, not an ``ls``."""
        lines = [f"**{self._t('state.structure.entry')}**", ""]
        lines += [f"- `{path}` — {self._t(f'state.structure.{key}')}" for path, key in ENTRY_POINTS]
        summary = facts.symbol_summary
        if summary.get("modules"):
            lines += ["", self._t("state.structure.rest", modules=facts.module_count or summary.get("modules", 0),
                                  classes=summary.get("classes", "?"), functions=summary.get("functions", "?"),
                                  tests=summary.get("tests", "?"))]
        lines += ["", self._t("state.structure.dependencies")]
        return "\n".join(lines)
