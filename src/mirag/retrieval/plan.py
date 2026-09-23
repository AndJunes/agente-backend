"""The retrieval plan: what to search, where, and which stages would be needed.

TWO IDEAS HOLD THIS MODULE UP

1. It costs no call. A deterministic plan is deduced from the request itself; asking the
   model for a separate planning call would break the call ceiling of the cheap path.

2. It does not depend on the model's format. A plan that only works if the model writes
   exactly the JSON we asked for breaks on Tuesday. :class:`PlanParser` accepts seven
   shapes and, if none fits, falls back to the deduced plan: worse, but it always exists.

The plan does not DECIDE which stages run either. It says what would be needed
(``needs_graph``, ``needs_symbols``); the :class:`~mirag.features.FeatureGate` decides.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Any

from mirag.core.text import as_bool, as_list, first_json_object, repair_truncated_json
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.lexicon import Lexicon
from mirag.llm.messages import function_tool
from mirag.retrieval.corpus import KnowledgeCorpus
from mirag.retrieval.ranking import Ranker


class Depth(StrEnum):
    SHALLOW = "shallow"
    NORMAL = "normal"
    DEEP = "deep"


# Language-neutral signals: a file name or a call signature is not a question in any
# language, and runtimes are named the same everywhere.
SIGNATURE = re.compile(r"\w+\.(py|js|ts|sql|json)\b|\w+\s*\([^)]*\)")
RUNTIME = re.compile(r"\b(node\.?js|python|typescript|javascript|golang|java|ruby|rust|\.net|c\+\+)\b", re.I)
MINIMUM_LAYERS = 2


@dataclass(frozen=True, slots=True)
class RetrievalPlan:
    goal: str = ""
    domains: tuple[str, ...] = ()
    """Box numbers: ``("04", "08")``."""
    technologies: tuple[str, ...] = ()
    required_knowledge: tuple[str, ...] = ()
    artifact_types: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    depth: str = Depth.NORMAL.value
    needs_code: bool = False
    needs_graph: bool = False
    needs_symbols: bool = False
    needs_project: bool = False
    """Is a whole project requested, not a single file?"""
    origin: str = "unknown"
    """Where the plan came from (a code, translated as ``plan.origin.<code>``)."""
    origin_note: str = ""
    """Extra origin qualifier (``no_boxes`` when the model gave none)."""

    def summary(self, catalog: MessageCatalog) -> str:
        """One line for the UI: what it will search and where."""
        parts: list[str] = []
        if self.domains:
            parts.append(catalog.t("plan.summary.boxes", boxes=", ".join(self.domains)))
        if self.technologies:
            parts.append(catalog.t("plan.summary.technologies", items=", ".join(self.technologies)))
        if self.required_knowledge:
            parts.append(catalog.t("plan.summary.concepts", count=len(self.required_knowledge)))
        needs = [
            catalog.t(f"plan.need.{name}")
            for name, value in (
                ("project", self.needs_project),
                ("code", self.needs_code),
                ("graph", self.needs_graph),
                ("symbols", self.needs_symbols),
            )
            if value
        ]
        if needs:
            parts.append(catalog.t("plan.summary.needs", items="+".join(needs)))
        return " · ".join(parts) or catalog.t("plan.summary.unbounded")

    def describe_origin(self, catalog: MessageCatalog) -> str:
        text = catalog.t(f"plan.origin.{self.origin}")
        return f"{text} ({catalog.t(f'plan.origin_note.{self.origin_note}')})" if self.origin_note else text

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


EMPTY_PLAN = RetrievalPlan(origin="disabled")
"""The plan that narrows nothing: ``MIRAG_RETRIEVAL_PLAN=off`` and the baseline arm of the
benchmarks. It has its own origin so the trace never says "deduced" about a plan nobody made."""


class IntentClassifier:
    """Decides by FORM, not by vocabulary, what a request asks for.

    What separates a code request from a question is not the technical vocabulary (both
    share it) but the shape: a code request names an artifact or a runtime and does NOT
    start by asking. Measured on the original set of real requests: 11/11 detected, 1 false
    positive out of 49 conceptual questions.
    """

    def __init__(self, lexicon: Lexicon) -> None:
        self._question = lexicon.pattern("intent.question_start")
        self._verbs = lexicon.pattern("intent.code_verbs")
        self._artifacts = lexicon.pattern("intent.code_artifacts")
        self._scaffolding = lexicon.pattern("intent.project_scaffolding")
        self._layers = lexicon.pattern("intent.project_layers")
        self._composite = lexicon.pattern("intent.project_composite")
        self._companions = lexicon.pattern("intent.project_companions")
        # Read here on purpose, from the same lexicon file. See asks_for_project.
        self._project_demo = lexicon.pattern("demos.project")
        self._symbols = lexicon.pattern("intent.symbol_hints")
        self._graph = lexicon.pattern("intent.graph_hints")
        self._depth = lexicon.pattern("intent.depth_hints")

    def asks_for_code(self, request: str) -> bool:
        request = request or ""
        if SIGNATURE.search(request):
            return True  # a `calculator.py` or an `f(a, b)` is not a question
        if self._question.search(request):
            return False  # it starts by asking: it is a query
        if self._verbs.search(request) or self._artifacts.search(request) or RUNTIME.search(request):
            return True
        # A project is code by definition. Without this the invariant below depended on
        # every lexicon listing every verb: "Split router, service and repository" named
        # three layers (a project) with a verb the English list lacked (no code).
        return self.asks_for_project(request)

    def asks_for_project(self, request: str) -> bool:
        """Is a whole project requested, with its structure?

        Invariant pinned by a test: ``asks_for_project(q)`` implies ``asks_for_code(q)``.
        If they contradicted each other the pipeline would take the project branch without
        asking for code, or the other way round.

        Second invariant, and it cost a broken delivery to find: this must never be narrower
        than ``demos.project``. The offline catalogue reads that key to decide whether a
        question deserves the multi-file script; this function decides whether the pipeline
        takes the multi-file branch. Two readings of one question, and they disagreed.

        "Una API de reservas. CRUD completo: crear, listar, consultar, modificar, borrar"
        matched ``crud completo`` there and nothing here — ``crud`` is composite, but with no
        layer and no companion the last line said no. So the scripted model was handed
        ``books_project``, whose first call is ``specify_project``, while the pipeline was on
        the single-file branch, whose reader wants ``files``. It found none and answered
        ``no_files``: no project, no ZIP, and a step coloured red with nothing wrong upstream.

        Reading the same pattern is what keeps them from drifting apart again. Every branch
        of that key names a whole deliverable — ``api rest``, ``api de libros``, ``books-api``,
        ``crud completo``, ``por dominios`` — so it belongs to this vocabulary anyway; it was
        only ever written down in the demos' half of the lexicon.
        """
        request = request or ""
        if self._question.search(request):
            return False  # "what is a CRUD?" is not an order
        if self._scaffolding.search(request) or self._project_demo.search(request):
            return True  # they ask for it by name
        layers = {m.group(0).lower() for m in self._layers.finditer(request)}
        if len(layers) >= MINIMUM_LAYERS:
            return True  # it names pieces that have to live together
        return bool(self._composite.search(request)) and bool(layers or self._companions.search(request))

    def needs_symbols(self, request: str) -> bool:
        return bool(self._symbols.search(request or ""))

    def needs_graph(self, request: str) -> bool:
        return bool(self._graph.search(request or ""))

    def depth(self, request: str) -> str:
        return Depth.DEEP.value if self._depth.search(request or "") else Depth.NORMAL.value


class PlanDeducer:
    """The deterministic plan: no model, no format to parse, always available.

    The boxes come from where the best chunks of a direct search came from. It is worse
    than a reasoned plan, but it depends on nobody: it is the floor.
    """

    def __init__(self, corpus: KnowledgeCorpus, ranker: Ranker, classifier: IntentClassifier) -> None:
        self._corpus = corpus
        self._ranker = ranker
        self.classifier = classifier

    def deduce(self, request: str, k: int = 4) -> RetrievalPlan:
        best = self._ranker.rank(self._corpus.chunks, request, k * 2)
        boxes = list(dict.fromkeys(chunk.box_number for chunk, _ in best))[:k]
        needs_project = self.classifier.asks_for_project(request)
        return RetrievalPlan(
            goal=request.strip()[:200],
            domains=tuple(boxes),
            required_knowledge=tuple(re.findall(r"\w{4,}", request.lower())[:8]),
            depth=self.classifier.depth(request),
            needs_code=self.classifier.asks_for_code(request) or needs_project,
            needs_project=needs_project,
            needs_graph=self.classifier.needs_graph(request),
            needs_symbols=self.classifier.needs_symbols(request),
            origin="deduced",
        )

    def normalise_boxes(self, values: object) -> tuple[str, ...]:
        """To two-digit box numbers, tolerating names. Invented boxes are dropped."""
        names = {chunk.box_name.lower(): chunk.box_number for chunk in self._corpus.chunks}
        out: list[str] = []
        for value in as_list(values):
            if match := re.search(r"\b(\d{1,2})\b", str(value)):
                number = match.group(1).zfill(2)
                if self._corpus.has_box(number):
                    out.append(number)
                    continue
            key = str(value).strip().lower()
            for name, number in names.items():
                if key and (key in name or name in key):
                    out.append(number)
                    break
        return tuple(dict.fromkeys(out))[:6]


class PlanParser:
    """Turns whatever the model said into a usable plan. Never raises.

    Accepted shapes, in order of attempt:
      1. an already parsed dict          5. JSON cut in half (repaired)
      2. valid JSON text                 6. the legacy ``BOXES: 03, 07`` line
      3. JSON wrapped in prose           7. nothing / garbage -> deduced plan
      4. JSON inside a fenced block
    """

    LEGACY_BOXES = re.compile(r"(?:BOXES|CAJAS)\s*:?\**(.*)$", re.IGNORECASE | re.MULTILINE)

    def __init__(self, deducer: PlanDeducer) -> None:
        self._deducer = deducer

    def parse(self, response: object, request: str = "", k: int = 4) -> RetrievalPlan:
        floor = self._deducer.deduce(request, k) if request else RetrievalPlan(origin="empty")
        if response is None:
            return replace(floor, origin="no_model_answer")

        raw, origin = (response, "model_dict") if isinstance(response, dict) else self._extract(str(response))

        if not isinstance(raw, dict):
            if isinstance(response, str) and (match := self.LEGACY_BOXES.search(response)):
                numbers = re.findall(r"\b(\d{1,2})\b", match.group(1))
                if numbers:
                    domains = tuple(n.zfill(2) for n in dict.fromkeys(numbers))[:k]
                    return replace(floor, domains=domains, origin="legacy_boxes")
            return replace(floor, origin="not_understood")

        known = set(RetrievalPlan.__dataclass_fields__)
        if not (set(raw) & (known | {"cajas", "boxes"})):
            return replace(floor, origin="json_without_plan_fields")

        depth = str(raw.get("depth", Depth.NORMAL.value)).strip().lower()
        domains = self._deducer.normalise_boxes(raw.get("domains") or raw.get("boxes") or raw.get("cajas"))
        return RetrievalPlan(
            goal=str(raw.get("goal") or request or "").strip()[:200],
            domains=domains or floor.domains,  # a plan without boxes narrows nothing: use the floor
            technologies=tuple(as_list(raw.get("technologies"))),
            required_knowledge=tuple(as_list(raw.get("required_knowledge"))),
            artifact_types=tuple(as_list(raw.get("artifact_types"))),
            exclude=self._deducer.normalise_boxes(raw.get("exclude")),
            depth=depth if depth in {d.value for d in Depth} else Depth.NORMAL.value,
            needs_code=as_bool(raw.get("needs_code", floor.needs_code)),
            needs_graph=as_bool(raw.get("needs_graph", floor.needs_graph)),
            needs_symbols=as_bool(raw.get("needs_symbols", floor.needs_symbols)),
            needs_project=as_bool(raw.get("needs_project", floor.needs_project)),
            origin=origin,
            origin_note="" if domains else "no_boxes",
        )

    @staticmethod
    def _extract(text: str) -> tuple[object, str]:
        """The JSON inside the answer and where it was found, or ``(None, "")``.

        RecursionError is caught next to ValueError on purpose: an answer with thousands of
        nested brackets makes the JSON decoder overflow instead of failing to parse, and
        this parser promises never to raise.
        """
        if match := re.search(r"```(?:json)?\s*(.+?)```", text, re.S):
            candidate, candidate_origin = match.group(1), "json_block"
        else:
            candidate, candidate_origin = text, "json_text"
        try:
            return json.loads(candidate, strict=False), candidate_origin
        except (ValueError, RecursionError):
            pass
        for rescue, origin in ((first_json_object, "json_in_prose"), (repair_truncated_json, "json_repaired")):
            try:
                raw = rescue(text)
            except (ValueError, RecursionError):
                continue
            if raw is not None:
                return raw, origin
        return None, ""


PLAN_TOOL = function_tool(
    "search_plan",
    "Before answering, say WHAT must be searched and where. Only once.",
    {
        "type": "object",
        "properties": {
            "goal": {"type": "string", "description": "what has to be solved, in one line"},
            "domains": {"type": "array", "items": {"type": "string"},
                        "description": "box numbers (01-19) to look in"},
            "technologies": {"type": "array", "items": {"type": "string"}},
            "required_knowledge": {"type": "array", "items": {"type": "string"},
                                   "description": "concepts that are strictly needed"},
            "artifact_types": {"type": "array", "items": {"type": "string"},
                               "description": "concept | card | failure | anti_pattern"},
            "exclude": {"type": "array", "items": {"type": "string"}},
            "depth": {"type": "string", "enum": [d.value for d in Depth]},
            "needs_code": {"type": "boolean"},
            "needs_graph": {"type": "boolean",
                            "description": "true only if several areas must be related"},
            "needs_symbols": {"type": "boolean",
                              "description": "true only if existing code must be searched"},
        },
        "required": ["goal", "domains"],
    },
)

__all__ = [
    "EMPTY_PLAN",
    "PLAN_TOOL",
    "Depth",
    "IntentClassifier",
    "PlanDeducer",
    "PlanParser",
    "RetrievalPlan",
]
