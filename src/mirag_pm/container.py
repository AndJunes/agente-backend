"""Wiring the PM agent out of mirag's parts.

Nothing is subclassed and nothing is forked. `build_container` already takes everything that
differs — where the corpus is, how to read it, what the tools are, what the agent is told it
is — so this is a factory that supplies those four and lets the rest be shared.

The defaults are applied here rather than in `Settings` so that an operator can still override
any of them from the environment: what is set stays set, and only what is missing is filled in
with this package's own resources.
"""

from __future__ import annotations

from dataclasses import replace

from mirag.container import Container, build_container
from mirag.core.settings import Settings
from mirag.retrieval.engine import RetrievalEngine
from mirag.tools.registry import ToolRegistry

from mirag_pm.corpus import PmCorpus, lookup_tables
from mirag_pm.paths import DOCUMENTS_LOCALE, KNOWLEDGE_DIR, LOCALES_DIR, SKILLS_DIR
from mirag_pm.prompts import SYSTEM_PROMPT
from mirag_pm.skills import SkillLibrary
from mirag_pm.tools import build_pm_tools

SUPPORTED_LOCALES = ("en", "es")
"""Two answer languages over one body of documents. The corpus is English; the locale picks
the message catalogue, whose language directive decides what the answer is written in."""


def pm_settings(settings: Settings | None = None) -> Settings:
    """``settings``, with anything unset filled in from this package."""
    settings = settings or Settings.from_env()
    return replace(
        settings,
        knowledge_dir=settings.knowledge_dir or KNOWLEDGE_DIR,
        locales_dir=settings.locales_dir or LOCALES_DIR,
        supported_locales=settings.supported_locales or SUPPORTED_LOCALES,
        system_prompt=settings.system_prompt or SYSTEM_PROMPT,
    )


def build_pm_container(settings: Settings | None = None) -> Container:
    settings = pm_settings(settings)
    # Loaded once for the process, not per locale: the skills and the lookup tables are the
    # same documents whichever language the answer comes out in.
    skills = SkillLibrary.load(SKILLS_DIR)
    lookups = lookup_tables(KNOWLEDGE_DIR / DOCUMENTS_LOCALE)

    def tools(engine: RetrievalEngine, _locale: str) -> ToolRegistry:
        return build_pm_tools(engine.search, skills, lookups, engine.catalog)

    return build_container(settings, corpus_loader=PmCorpus.load, tools_builder=tools)
