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


def questionnaire_tool() -> dict[str, Any]:
    return function_tool(
        "ask_questions",
        "Ask for the decisions you cannot infer. Prefer asking to assuming. Call it ONCE.",
        {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "why these and not others"},
                "questions": {"type": "array", "items": _QUESTION},
            },
            "required": ["reason", "questions"],
        },
    )


class PmWorkflow:
    """The three operations, over the PM container."""

    def __init__(self, container: Container) -> None:
        self._container = container

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
            [questionnaire_tool()],
        )
        result: dict[str, Any] = {"summary": message.get("content") or ""}
        if arguments := first_tool_arguments(message):
            result["questionnaire"] = {
                "reason": str(arguments.get("reason") or ""),
                "questions": _questions(arguments.get("questions")),
            }
        return result

    def plan(self, payload: Mapping[str, Any], locale: str) -> dict[str, Any]:
        """An idea plus answers -> a plan, or another round of questions."""
        idea = _text(payload, "idea")
        answers = payload.get("answers") or []
        answered = "\n".join(
            f"- {a.get('questionId')}: {a.get('value')}" for a in answers if isinstance(a, Mapping)
        ) or "(none: the user chose to go on without answering)"
        context = self._context(idea, locale, "write-requirements")
        message = self._ask(
            locale,
            "Produce the plan by calling deliver_plan. If the answers have opened a decision you "
            "still cannot make, call ask_questions instead — a second round is a normal outcome, "
            "not a failure. " + SCHEMA_NOTE,
            f"{context}\n\n=== THE IDEA ===\n{idea}\n\n=== WHAT THEY ANSWERED ===\n{answered}",
            [plan_tool(), questionnaire_tool()],
        )
        return self._plan_or_questions(message, version=1)

    def revise(self, payload: Mapping[str, Any], locale: str) -> dict[str, Any]:
        """A plan plus a rejection -> the next version, never an edit of the last."""
        previous = payload.get("plan")
        if not isinstance(previous, Mapping):
            raise ValueError("revise needs the plan being revised")
        feedback = _text(payload, "feedback")
        version = int(previous.get("version") or 1)
        context = self._context(feedback, locale, "revise-plan")
        message = self._ask(
            locale,
            "The user rejected this plan for the reason given. Produce the NEXT VERSION with "
            "deliver_plan. Read the feedback as a constraint, not as something to append: a "
            "rejection often invalidates a decision made earlier in the plan. " + SCHEMA_NOTE,
            f"{context}\n\n=== THE PLAN THEY REJECTED ===\n{_render(previous)}"
            f"\n\n=== WHY ===\n{feedback}",
            [plan_tool()],
        )
        result = self._plan_or_questions(message, version=version + 1)
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

    def _ask(self, locale: str, instruction: str, content: str, tools: list[dict[str, Any]]) -> dict[str, Any]:
        catalog = self._container.i18n.catalog(locale)
        system = (
            f"{self._container.settings.system_prompt}\n\n{instruction}\n\n"
            f"{catalog.t('llm.language_directive')}"
        )
        gateway = self._container.gateways.create()
        try:
            return gateway.chat([{"role": "system", "content": system},
                                 {"role": "user", "content": content}], tools=tools)
        except OfflineModeError as error:
            # Said plainly rather than as a 500: the offline lock is a deliberate state, and
            # these three operations have no scripted double to fall back on.
            raise RuntimeError(
                f"The PM agent has no model: {error}. These operations need one — there is no "
                f"scripted demo for this corpus."
            ) from error

    def _plan_or_questions(self, message: Mapping[str, Any], version: int) -> dict[str, Any]:
        arguments = first_tool_arguments(dict(message))
        if arguments is None:
            raise RuntimeError("the model answered in prose where a plan was required")
        if "questions" in arguments:
            return {"reason": str(arguments.get("reason") or ""),
                    "questions": _questions(arguments.get("questions"))}
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
            "openQuestions": [str(q) for q in _list(arguments.get("openQuestions"))] or [
                "This plan declared nothing open, which is almost never true. Treat that as a "
                "gap in the plan rather than as completeness."
            ],
            "status": "draft",
        }


# ── reading what the model sent ──────────────────────────────────────────────

KINDS = ("performance", "security", "compatibility", "other")


def _text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key!r} must be a non-empty string")
    if len(value) > MAX_IDEA_CHARS:
        raise ValueError(f"{key!r} is longer than {MAX_IDEA_CHARS} characters")
    return value.strip()


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
