"""The three operations CodeZard calls: analyse an idea, produce a plan, revise it.

Structured output comes from a tool schema, not from parsing prose. `prompts.deliver_tool` is
the working precedent in this codebase and the reason is the same here: a model asked for JSON
in a sentence produces JSON most of the time, and the failures are silent and shaped like
success.

**What the plan does not contain, and why.** The schema CodeZard expects carries
``entities[].fields[]`` and ``roles[].can[]`` — a data model and a permissions matrix. The
corpus is explicit that neither belongs in this document: `prd.md` records that a requirements
document *"may not dictate a specific implementation"*, and separates *"PRD = what; functional
specification = how."* So the model is asked for entities as domain concepts and roles as
personas, the two implementation-shaped fields are sent empty, and the plan says so in its own
open questions rather than leaving the reader to notice. The interface is unchanged; what
changes is that this agent stops answering a question the knowledge base says is not its own.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from mirag.container import Container
from mirag.core.errors import OfflineModeError
from mirag.llm.messages import first_tool_arguments, function_tool
from mirag.llm.models import ANY_TOOL
from mirag_pm import offline
from mirag_pm.audit import CitationAuditor

Operation = Callable[[Mapping[str, Any], str], dict[str, Any]]

MAX_IDEA_CHARS = 8_000

SCHEMA_NOTE = (
    "Leave `entities[].fields` and `roles[].can` empty. A field list is a data schema and a "
    "`can` list is a permissions design; this document says WHAT is needed, not HOW it is "
    "built, and the implementer derives both. Put that in openQuestions instead."
)

_ENTITY = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "a thing the product is about, in the user's language"},
        "description": {"type": "string", "description": "what it is, in one line"},
        "fields": {"type": "array", "items": {"type": "string"}, "description": "LEAVE EMPTY"},
    },
    "required": ["name", "description", "fields"],
}

_ROLE = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "a persona, not a job title"},
        "can": {"type": "array", "items": {"type": "string"}, "description": "LEAVE EMPTY"},
    },
    "required": ["name", "can"],
}

_FLOW = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}, "description": "what the user does, in order"},
    },
    "required": ["name", "steps"],
}

_CONSTRAINT = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["performance", "security", "compatibility", "other"]},
        "statement": {"type": "string", "description": "true whether or not anyone likes it"},
    },
    "required": ["kind", "statement"],
}

_QUESTION = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "short, stable, lowercase"},
        "text": {"type": "string", "description": "in plain language, no jargon without a gloss"},
        "options": {"type": "array", "items": {"type": "string"},
                    "description": "omit for a free-text answer; options make answers comparable"},
    },
    "required": ["id", "text"],
}


def plan_tool() -> dict[str, Any]:
    return function_tool(
        "deliver_plan",
        "Deliver the plan. Call it ONCE, with everything inside. " + SCHEMA_NOTE,
        {
            "type": "object",
            "properties": {
                "purpose": {"type": "string",
                            "description": "what this is for AND how it fits what the user is trying to do"},
                "entities": {"type": "array", "items": _ENTITY},
                "roles": {"type": "array", "items": _ROLE},
                "flows": {"type": "array", "items": _FLOW},
                "constraints": {"type": "array", "items": _CONSTRAINT},
                "openQuestions": {
                    "type": "array", "items": {"type": "string"},
                    "description": "What this plan does NOT settle. An empty list is a claim, and "
                                   "almost always a false one. Always include the data model and "
                                   "the permissions, which are the implementer's to derive.",
                },
            },
            "required": ["purpose", "entities", "roles", "flows", "constraints", "openQuestions"],
        },
    )


def questionnaire_tool(with_summary: bool = False) -> dict[str, Any]:
    """Ask for what cannot be inferred.

    ``with_summary`` folds the restatement of the idea INTO the tool call, and that is not a
    convenience. Asked for prose *and* a tool call in one turn, models reliably do one or the
    other: observed live, one run wrote the restatement and never called the tool, so the
    questionnaire silently disappeared and the flow went straight to planning without asking
    anything. Everything inside one call removes the choice — which is exactly why
    ``deliver_plan`` is shaped that way.
    """
    properties: dict[str, Any] = {
        "reason": {"type": "string", "description": "why these questions and not others"},
        "questions": {"type": "array", "items": _QUESTION},
    }
    required = ["reason", "questions"]
    if with_summary:
        properties = {
            "summary": {"type": "string",
                        "description": "what you understood, plainly, proposing no solution"},
            **properties,
        }
        required = ["summary", *required]
    return function_tool(
        "ask_questions",
        "Restate what you understood and ask for the decisions you cannot infer. Call it ONCE, "
        "with everything inside." if with_summary
        else "Ask for the decisions you cannot infer. Prefer asking to assuming. Call it ONCE.",
        {"type": "object", "properties": properties, "required": required},
    )


class PmWorkflow:
    """The three operations, over the PM container."""

    def __init__(self, container: Container, auditor: CitationAuditor | None = None) -> None:
        self._container = container
        self._auditor = auditor

    def operations(self) -> dict[str, Operation]:
        return {"analyze": self.analyze, "plan": self.plan, "revise": self.revise}

    # ── the operations ───────────────────────────────────────────────────────

    def analyze(self, payload: Mapping[str, Any], locale: str) -> dict[str, Any]:
        """An idea -> what was understood, and what must be decided before planning."""
        idea = _text(payload, "idea")
        context = self._context(idea, locale, "scope-a-discovery")
        message = self._ask(
            locale,
            "The user has described an idea. Restate what you understood, plainly and without "
            "proposing a solution. Then call ask_questions with the decisions that cannot be "
            "inferred from what they said — the ones that would change the shape of the work. "
            "Four at most. Ask; do not assume.",
            f"{context}\n\n=== THE IDEA ===\n{idea}",
            [questionnaire_tool(with_summary=True)],
            operation="analyze",
        )
        arguments = first_tool_arguments(message) or {}
        # The tool's summary when there is one, the prose otherwise. A model that answered in
        # prose still said something useful; it just did not ask anything.
        summary = str(arguments.get("summary") or "") or (message.get("content") or "")
        if findings := self._audit(summary):
            summary = f"{summary}\n\n" + "\n".join(f"⚠️ {f}" for f in findings)

        result: dict[str, Any] = {"summary": summary}
        # Only when there is something to ask. An empty questionnaire is not a questionnaire:
        # it crashed the screen, which opened the popup and read question zero of none.
        if questions := _questions(arguments.get("questions")):
            result["questionnaire"] = {"reason": str(arguments.get("reason") or ""), "questions": questions}
        return result

    def plan(self, payload: Mapping[str, Any], locale: str) -> dict[str, Any]:
        """An idea plus answers -> a plan, or another round of questions."""
        idea = _text(payload, "idea")
        answers = payload.get("answers") or []
        answered = "\n".join(
            f"- {a.get('questionId')}: {a.get('value')}" for a in answers if isinstance(a, Mapping)
        ) or "(none: the user chose to go on without answering)"
        # The caller says which round this is, and the LAST one is enforced by not offering the
        # tool at all. Asking the model to stop asking is a request; removing `ask_questions`
        # from the turn is a fact. Observed live: three rounds in, the agent was asking what it
        # should produce — a question about its own task, which the caller had already settled.
        round_number = _int(payload.get("round"), 0)
        last_round = round_number >= _int(payload.get("maxRounds"), 2)
        tools = [plan_tool()] if last_round else [plan_tool(), questionnaire_tool()]

        context = self._context(idea, locale, "write-requirements")
        instruction = "Produce the plan by calling deliver_plan. " + (
            "This is the last round: whatever is still unresolved goes in openQuestions, "
            "which is what that field is for. Do not ask again — say what you do not know "
            "and plan around it."
            if last_round else
            "If the answers have opened a decision you still cannot make, call ask_questions "
            "instead — a second round is a normal outcome, not a failure. Ask about the "
            "PRODUCT, never about what you should be producing: that is already decided."
        ) + " " + SCHEMA_NOTE
        content = f"{context}\n\n=== THE IDEA ===\n{idea}\n\n=== WHAT THEY ANSWERED ===\n{answered}"
        return self._attempt(
            lambda insist: self._plan_or_questions(
                self._ask(locale, instruction + insist, content, tools, require=ANY_TOOL,
                          operation="plan"),
                version=1),
        )

    def revise(self, payload: Mapping[str, Any], locale: str) -> dict[str, Any]:
        """A plan plus a rejection -> the next version, never an edit of the last."""
        previous = payload.get("plan")
        if not isinstance(previous, Mapping):
            raise ValueError("revise needs the plan being revised")
        feedback = _text(payload, "feedback")
        version = int(previous.get("version") or 1)
        context = self._context(feedback, locale, "revise-plan")
        instruction = (
            "The user rejected this plan for the reason given. Produce the NEXT VERSION with "
            "deliver_plan. Read the feedback as a constraint, not as something to append: a "
            "rejection often invalidates a decision made earlier in the plan. " + SCHEMA_NOTE
        )
        content = (f"{context}\n\n=== THE PLAN THEY REJECTED ===\n{_render(previous)}"
                   f"\n\n=== WHY ===\n{feedback}")
        result = self._attempt(
            lambda insist: self._plan_or_questions(
                self._ask(locale, instruction + insist, content, [plan_tool()],
                          require="deliver_plan", operation="revise"),
                version=version + 1),
        )
        if "version" in result:
            result["revisionOf"] = {"version": version, "feedback": feedback}
        return result

    # ── the machinery ────────────────────────────────────────────────────────

    def _context(self, question: str, locale: str, skill: str) -> str:
        """Retrieved knowledge plus the skill that governs this operation.

        The skill is fetched by name rather than searched for: which operation this is, is
        known here, and leaving it to a lexical match would occasionally hand the model the
        wrong method for a step whose method is not in question.
        """
        engine = self._container.engines.get(locale)
        parts = [engine.search.docs(question, k=3)]
        if found := self._container.tools(locale).get("find_skill"):
            parts.append(found.invoke(task=skill).text)
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _attempt(once: Callable[[str], dict[str, Any]]) -> dict[str, Any]:
        """Run ``once``, and run it again with a blunter instruction if it did not deliver.

        The project generator has carried this reasoning from the start, with a comment
        saying free providers drop calls; it was never applied to this half, where a single
        empty `deliver_plan` came back through the API as a finished plan with nothing in it.
        The second attempt is not the same request: it is told what went wrong, because
        repeating a prompt a model just failed is a reasonable way to fail twice.
        """
        try:
            return once("")
        except RuntimeError as first:
            return once(
                f"\n\nYOUR PREVIOUS ANSWER WAS REJECTED: {first}. Call the tool, and put the "
                f"real content INSIDE the call — an empty call is worse than a short one."
            )

    def _ask(self, locale: str, instruction: str, content: str, tools: list[dict[str, Any]],
             require: str | None = None, operation: str = "") -> dict[str, Any]:
        catalog = self._container.i18n.catalog(locale)
        system = (
            f"{self._container.settings.system_prompt}\n\n{instruction}\n\n"
            f"{catalog.t('llm.language_directive')}"
        )
        # With the lock on, the DECISION is scripted and everything else is not: the corpus is
        # really loaded, the retrieval really ran to build `content`, the citation audit really
        # inspects what comes back. This half used to have no double at all and answered 502,
        # which meant the whole flow needed a key and a network from its very first step —
        # every run starts with a PM call.
        script = offline.script_for(operation) if self._container.gateways.offline else None
        gateway = self._container.gateways.create(script=script)
        try:
            return gateway.chat([{"role": "system", "content": system},
                                 {"role": "user", "content": content}], tools=tools, require=require)
        except OfflineModeError as error:  # pragma: no cover - the script is passed above
            raise RuntimeError(
                f"The PM agent has no model: {error}. These operations need one."
            ) from error

    def _plan_or_questions(self, message: Mapping[str, Any], version: int) -> dict[str, Any]:
        why: list[str] = []
        # Read by NAME, and the questionnaire first. Taking `tool_calls[0]` whatever it was
        # meant that when the model emitted both — which it does, having been offered both —
        # whichever came first won, and a `deliver_plan` sitting second was never seen.
        asked = first_tool_arguments(dict(message), why, name="ask_questions")
        if asked is not None:
            if questions := _questions(asked.get("questions")):
                return {"reason": str(asked.get("reason") or ""), "questions": questions}
            raise RuntimeError("the model opened a questionnaire with no usable questions")
        arguments = first_tool_arguments(dict(message), why, name="deliver_plan")
        if arguments is None:
            raise RuntimeError(
                "the model produced neither a plan nor a questionnaire" + (f": {why[0]}" if why else "")
            )
        if empty := _empty_plan(arguments):
            # An empty `deliver_plan` used to come back through the API as a plan with 200:
            # no purpose, no entities, no flows, and one openQuestion saying the plan declared
            # nothing open. That reads as a finished document and is the absence of one.
            raise RuntimeError(f"the model called deliver_plan with nothing in it: {empty}")
        return {
            "version": version,
            "purpose": str(arguments.get("purpose") or ""),
            # `fields` and `can` are dropped rather than trusted: the schema says to leave them
            # empty and a model that fills them anyway has answered the implementer's question.
            "entities": [{"name": str(e.get("name") or ""), "description": str(e.get("description") or ""),
                          "fields": []}
                         for e in _items(arguments.get("entities"))],
            "roles": [{"name": str(r.get("name") or ""), "can": []} for r in _items(arguments.get("roles"))],
            "flows": [{"name": str(f.get("name") or ""), "steps": [str(s) for s in _list(f.get("steps"))]}
                      for f in _items(arguments.get("flows"))],
            "constraints": [{"kind": _kind(c.get("kind")), "statement": str(c.get("statement") or "")}
                            for c in _items(arguments.get("constraints"))],
            "openQuestions": _open_questions(arguments, self._audit) or [
                "This plan declared nothing open, which is almost never true. Treat that as a "
                "gap in the plan rather than as completeness."
            ],
            "status": "draft",
        }


    def _audit(self, *texts: str) -> list[str]:
        return [str(f) for f in self._auditor.audit(*texts)] if self._auditor else []


def _empty_plan(arguments: Mapping[str, Any]) -> str:
    """Why this is not a plan, or ``""``.

    A purpose alone is not enough and neither is a lone list: a plan says what it is for AND
    names something concrete about the work. Both halves are required because each has been
    seen without the other.
    """
    missing = []
    if not str(arguments.get("purpose") or "").strip():
        missing.append("purpose")
    if not any(_items(arguments.get(field)) for field in ("entities", "roles", "flows", "constraints")):
        missing.append("entities, roles, flows and constraints are all empty")
    return "; ".join(missing)


def _open_questions(arguments: Mapping[str, Any], audit: Any) -> list[str]:
    """What the plan does not settle, plus anything the audit found.

    The findings go here rather than into a field of their own because this is the one place
    the interface already renders prominently, in the colour it uses for a warning. A field
    the front end does not know about is a warning nobody sees.
    """
    declared = [str(q) for q in _list(arguments.get("openQuestions"))]
    prose = " ".join([str(arguments.get("purpose") or ""), *declared])
    return declared + audit(prose)


# ── reading what the model sent ──────────────────────────────────────────────

KINDS = ("performance", "security", "compatibility", "other")


def _text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key!r} must be a non-empty string")
    if len(value) > MAX_IDEA_CHARS:
        raise ValueError(f"{key!r} is longer than {MAX_IDEA_CHARS} characters")
    return value.strip()


def _int(value: Any, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else default


def _list(value: Any) -> list[Any]:
    return [v for v in value] if isinstance(value, list) else []


def _items(value: Any) -> list[Mapping[str, Any]]:
    return [v for v in _list(value) if isinstance(v, Mapping)]


def _kind(value: Any) -> str:
    return value if value in KINDS else "other"


def _questions(value: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, raw in enumerate(_items(value), start=1):
        question: dict[str, Any] = {
            "id": str(raw.get("id") or f"q{index}"),
            "text": str(raw.get("text") or ""),
        }
        if options := [str(o) for o in _list(raw.get("options"))]:
            question["options"] = options
        if question["text"]:
            out.append(question)
    return out


def _render(plan: Mapping[str, Any]) -> str:
    lines = [f"Purpose: {plan.get('purpose')}"]
    for name, key in (("Entities", "entities"), ("Roles", "roles"), ("Flows", "flows")):
        if items := _items(plan.get(key)):
            lines.append(f"{name}: " + "; ".join(str(i.get("name") or "") for i in items))
    if constraints := _items(plan.get("constraints")):
        lines.append("Constraints: " + "; ".join(str(c.get("statement") or "") for c in constraints))
    if open_questions := _list(plan.get("openQuestions")):
        lines.append("Open: " + "; ".join(str(q) for q in open_questions))
    return "\n".join(lines)
