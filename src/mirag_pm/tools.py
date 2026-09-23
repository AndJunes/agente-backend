"""What the PM agent can do, as tools the model chooses between.

``builtin.py`` states the rule this file follows: *the description IS the routing signal —
each says what it is for AND what it is not for, because the model chooses by reading it.*
Every description here is therefore written in product-management terms, and several say
outright which question belongs to a different tool.

**There is no ``run_code``, no ``calculate`` and no ``deliver_implementation``.** An agent that
reads product-management documents and can also write and execute code is the two agents
blending, in the most concrete form the failure takes. Leaving them out also makes the
execution audit honest rather than merely quiet: ``AgentLoop`` filters its audit on the
``run_code`` step, so with no such tool there is nothing that could be misreported.

``related_boxes`` is absent too, and for a different reason. The PM corpus contains no
``[04, 09]`` cross-references, so the box graph is empty and the tool would answer *"nothing
references this"* for every document in the corpus — a tool whose description promises a
dependency map and always returns nothing is worse than its absence. ``reason-across-domains``
covers the same need from ``CONCEPT_GRAPH.md``, which was written for it.
"""

from __future__ import annotations

import re
from typing import Any

from mirag.i18n.catalog import MessageCatalog
from mirag.retrieval.ranking import Bm25Ranker
from mirag.retrieval.search import KnowledgeSearch
from mirag.tools.registry import FunctionTool, ToolRegistry

from mirag_pm.skills import SkillLibrary

SPELLING = re.compile(r"is(?=[ae]\b|ing\b|ed\b|ation\b)")
"""`prioritise` and `prioritize` are the same request. The skills are written one way and
people ask the other, and a lookup that misses on an `s` is a lookup nobody trusts twice."""

CITATION = re.compile(r"^\s*\|?\s*\**\[?([SE]\d{3})\]?\**", re.MULTILINE)
"""A row of `SOURCES.md` begins with its id. The register is a table, so it is read as one."""


def _string_parameter(name: str, description: str) -> dict[str, Any]:
    return {"type": "object", "properties": {name: {"type": "string", "description": description}},
            "required": [name]}


def _lookup_rows(text: str, needle: str, limit: int = 8) -> list[str]:
    """Lines of a table that mention ``needle``, case-insensitively."""
    wanted = needle.strip().lower()
    if not wanted:
        return []
    return [line.strip() for line in text.split("\n") if wanted in line.lower()][:limit]


def build_pm_tools(
    search: KnowledgeSearch,
    skills: SkillLibrary,
    lookups: dict[str, str],
    catalog: MessageCatalog,
) -> ToolRegistry:
    """The PM agent's tools. ``lookups`` holds INDEX.md, SOURCES.md and GLOSSARY.md whole."""
    # Skills are ranked with the same BM25 the corpus uses, over the cards as chunks. A
    # hand-rolled score was tried first and was worse in the way hand-rolled scores are: with
    # every matched word worth the same, "prioritise the backlog" was decided by "backlog"
    # appearing in a skill's NAME and "should we sunset this product" by the word "product",
    # which is in a third of them. BM25 already discounts a term by how common it is.
    catalogue = skills.chunks()
    ranker = Bm25Ranker()

    def resolve_source(citation: str) -> str:
        """`[S127]` -> the row of the register that defines it."""
        register = lookups.get("SOURCES.md", "")
        match = CITATION.search(citation) or re.search(r"[SE]\d{3}", citation.upper())
        if not register or not match:
            return catalog.t("search.no_results")
        identifier = match.group(0).strip("[]* ")
        rows = _lookup_rows(register, identifier, limit=3)
        if not rows:
            return (f"{identifier} is not in the register. It may be a typo, or a citation this "
                    f"knowledge base does not carry — say so rather than describing it.")
        prefix = "corpus source" if identifier.startswith("S") else "external, Phase-2 source"
        return f"{identifier} — {prefix}:\n" + "\n".join(rows)

    def look_up_term(term: str) -> str:
        """The glossary definition and the documents that own the concept."""
        parts: list[str] = []
        if rows := _lookup_rows(lookups.get("GLOSSARY.md", ""), term, limit=4):
            parts.append("From the glossary:\n" + "\n".join(rows))
        if rows := _lookup_rows(lookups.get("INDEX.md", ""), term, limit=6):
            parts.append("Documents that cover it:\n" + "\n".join(rows))
        if not parts:
            # The index carries its own gap markers, so silence here is informative: the
            # corpus does not index this term, which is a finding rather than a miss.
            return (f"Neither the glossary nor the 633-term index carries {term!r}. That is "
                    f"itself the answer: say the knowledge base does not cover it.")
        return "\n\n".join(parts)

    def find_skill(task: str) -> str:
        """Which operation fits, with its method and — above all — its refusals."""
        wanted = SPELLING.sub("iz", task.strip().lower())
        if not wanted:
            return "Name the task."
        best = ranker.rank(catalogue, wanted, 3)
        if not best:
            return (f"No skill covers {task!r}. Before answering it directly, check whether it "
                    f"is one of this knowledge base's declared gaps.")
        return "\n\n---\n\n".join(chunk.text for chunk, _ in best)

    return ToolRegistry([
        FunctionTool(
            "search_pm_knowledge",
            "The general search over 91 product-management documents in 13 domains: foundations, "
            "discovery, market intelligence, strategy, planning, requirements, execution, "
            "ideation, metrics, risk, lifecycle and launch, design and UX, and working with AI "
            "implementers. USE THIS by default to explain a concept or a method. Do NOT use it to "
            "find out what a claim does not establish (search_limitations) or what the sources "
            "disagree about (search_disputed) — and do not use it for anything about writing, "
            "running or reviewing code, which this agent does not do.",
            _string_parameter("query", "The product-management concept, method or artifact"),
            lambda query: search.docs(query),
        ),
        FunctionTool(
            "search_limitations",
            "Returns the LIMITATIONS sections: what the sources do not establish, where a method "
            "stops working, and what a document admits it does not cover. Use it before making any "
            "confident recommendation, and whenever the question is 'when would this not work'. "
            "This is the single most important tool here: this knowledge base's value is that it "
            "says what it does not know, and an answer built without this sounds more certain than "
            "its evidence.",
            _string_parameter("topic", "The method, framework or claim to bound"),
            lambda topic: search.anti_patterns(topic),
        ),
        FunctionTool(
            "search_disputed",
            "Returns what is marked as unsafe to assert: disputed points where sources contradict "
            "each other, unverified claims, vendor projections, figures marked 'do not cite', "
            "low-confidence documents, and the two reference documents on what is disputed and "
            "what has expired. Use it before repeating any striking statistic, attribution or "
            "origin story. If a claim appears here, give both positions and say they differ — "
            "never state it as settled.",
            _string_parameter("topic", "The claim, figure or attribution to check"),
            lambda topic: search.failures(topic),
        ),
        FunctionTool(
            "search_evidence",
            "Returns the metadata card of each relevant document: its type, its evidence_type, its "
            "confidence, its source ids and its provenance — what the creator said, what a later "
            "reading says, what is current practice, and what has been measured. Use it when the "
            "question is HOW WELL something is known rather than what it is. An empty 'empirical' "
            "list means nobody has measured it, which is an answer worth giving.",
            _string_parameter("topic", "The topic whose evidential backing you need"),
            lambda topic: search.tradeoffs(topic),
        ),
        FunctionTool(
            "resolve_source",
            "Resolves a citation like [S127] or [E006] to its entry in the source register. "
            "[Snnn] are the 143 corpus sources; [Ennn] are the 14 externally researched ones, kept "
            "in a separate register with a reliability tier. Use it whenever you are about to pass "
            "a citation through, which you should be doing: traceability is the point of this "
            "knowledge base.",
            _string_parameter("citation", "The citation, e.g. S127 or [E006]"),
            resolve_source,
        ),
        FunctionTool(
            "look_up_term",
            "Looks a term up in the glossary and in the 633-term concept index, which maps each "
            "term to the document that owns it. Use it FIRST on any terminology question: it "
            "answers by exact lookup, which is more reliable than searching prose, and it tells "
            "you which document to search next. Its gap markers are inline, so it also says when "
            "the corpus has no answer.",
            _string_parameter("term", "The term to look up"),
            look_up_term,
        ),
        FunctionTool(
            "find_skill",
            "Returns the operation that fits a task: when to use it, what it needs, the ordered "
            "method composed from the documents, what it produces, and the claims it must NOT "
            "make. Use it BEFORE starting any piece of product work — writing requirements, "
            "prioritising, assessing risk, planning a discovery — because several of these "
            "operations exist mainly to refuse: estimation, metric design and MVP scoping are "
            "gaps in this knowledge base and the skill says so rather than letting you invent an "
            "answer.",
            _string_parameter("task", "What you are about to do"),
            find_skill,
        ),
    ])
