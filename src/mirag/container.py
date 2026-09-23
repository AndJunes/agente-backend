"""The composition root: the only place where concrete classes are chosen and wired.

Every service receives its collaborators through its constructor (dependency inversion).
Tests build a container with their own settings - an isolated data directory, the offline
lock on - and get exactly the same object graph production uses.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from mirag import __version__
from mirag.agent.architect import ArchitectWorkflow
from mirag.agent.loop import AgentLoop
from mirag.api.chat_service import ChatService
from mirag.core.settings import Settings
from mirag.evidence.claims import ClaimAuditor
from mirag.execution.backend import CodeExecutionBackend
from mirag.execution.calculator import SafeCalculator
from mirag.execution.docker_runner import DockerCodeRunner
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.runner import CodeRunner
from mirag.execution.syntax import SyntaxChecker
from mirag.features.flags import FeatureGate, GainsRepository
from mirag.i18n.registry import I18n
from mirag.llm.gateway import LLMGatewayFactory, ModelBuilder
from mirag.observability.tracing import TraceWriter
from mirag.offline.demos import DemoCatalog
from mirag.paths import FEATURE_GAINS_FILE, WEB_DIR
from mirag.pipeline.code_stage import CodeDeliveryStage
from mirag.pipeline.delivery import OutputWriter
from mirag.pipeline.knowledge_stage import KnowledgeStage
from mirag.pipeline.orchestrator import QuestionPipeline
from mirag.pipeline.project_stage import ProjectDeliveryStage
from mirag.pipeline.prompts import SYSTEM_PROMPT
from mirag.projects.artifacts import ArtifactRegistry
from mirag.projects.certification import ProjectCertifier
from mirag.projects.dependencies import DependencyAnalyzer
from mirag.projects.generator import ProjectGenerator
from mirag.projects.packaging import Packager
from mirag.retrieval.engine import RetrievalEngineFactory
from mirag.retrieval.symbols import SymbolIndexCache, SymbolIndexer
from mirag.retrieval.vectors import VectorStoreFactory
from mirag.self_knowledge.project_state import ProjectStateResponder, SystemFacts
from mirag.tools.builtin import build_default_tools
from mirag.tools.registry import ToolRegistry

T = TypeVar("T")


class PerLocale(dict[str, T]):
    """A thread-safe lazy cache of one object per locale."""

    def __init__(self, factory: Callable[[str], T]) -> None:
        super().__init__()
        self._factory = factory
        self._lock = threading.Lock()

    def __call__(self, locale: str) -> T:
        with self._lock:
            if locale not in self:
                self[locale] = self._factory(locale)
            return self[locale]


@dataclass
class Container:
    settings: Settings
    i18n: I18n
    gate: FeatureGate
    interpreters: InterpreterRegistry
    runner: CodeExecutionBackend
    syntax: SyntaxChecker
    engines: RetrievalEngineFactory
    symbol_cache: SymbolIndexCache
    artifacts: ArtifactRegistry
    traces: TraceWriter
    gateways: LLMGatewayFactory
    generator: ProjectGenerator
    certifier: ProjectCertifier
    packager: Packager
    pipeline: QuestionPipeline = field(init=False)
    chat: ChatService = field(init=False)
    tools: PerLocale[ToolRegistry] = field(init=False)
    demos: PerLocale[DemoCatalog] = field(init=False)
    state: PerLocale[ProjectStateResponder] = field(init=False)
    architect: PerLocale[ArchitectWorkflow] = field(init=False)
    page_path: Path = WEB_DIR / "index.html"

    operations: Mapping[str, Callable[[Mapping[str, Any], str], dict[str, Any]]] | None = None
    """Named JSON operations this agent exposes, or ``None``.

    Kept as a plain mapping rather than a typed workflow so that `mirag` does not have to
    import whatever package defines them. An agent that answers questions needs none of these;
    one that has to produce a specific artifact for a specific caller — a plan, a revision —
    cannot express that through `/chat`, whose request body has room for a question and
    nothing else.
    """

    tools_builder: Callable[[RetrievalEngine, str], ToolRegistry] | None = None
    """How this agent's tools are built. ``None`` means the backend's own set.

    A tool set is part of what an agent IS — `builtin.py` says it outright: the description is
    the routing signal, because the model chooses by reading it. An agent over a different
    corpus needs descriptions in that corpus's terms, and needs some of these tools absent
    rather than reworded."""

    def __post_init__(self) -> None:
        self.tools = PerLocale(lambda locale: (
            self.tools_builder(self.engines.get(locale), locale) if self.tools_builder
            else build_default_tools(self.engines.get(locale).search, self.runner, SafeCalculator())))
        self.demos = PerLocale(lambda locale: DemoCatalog(self.i18n.lexicon(locale), self.i18n.catalog(locale)))
        self.state = PerLocale(lambda locale: ProjectStateResponder(
            self.i18n.lexicon(locale), self.i18n.catalog(locale), self.engines.get(locale).corpus, self.system_facts))
        self.architect = PerLocale(lambda locale: ArchitectWorkflow(
            AgentLoop(self.tools(locale), ClaimAuditor(self.i18n.lexicon(locale), self.i18n.catalog(locale))),
            self.i18n.catalog(locale)))
        self.pipeline = QuestionPipeline(
            engines=self.engines,
            state=self.state,
            knowledge=KnowledgeStage(self.gate, self.symbol_cache, self.settings.resolved_symbols_root()),
            code=CodeDeliveryStage(self.syntax, self.interpreters, OutputWriter(self.settings.output_dir),
                                   system_prompt=self.settings.system_prompt or SYSTEM_PROMPT),
            project=ProjectDeliveryStage(self.generator, self.certifier, self.packager, self.artifacts),
            traces=self.traces,
        )
        self.chat = ChatService(self.i18n, self.gateways, self.pipeline, self.state, self.demos, self.architect)

    # ── facts and status ─────────────────────────────────────────────────────

    def system_facts(self) -> SystemFacts:
        """Built from the real objects: modes, tools and symbols are never repeated by hand."""
        root = self.settings.resolved_symbols_root()
        try:
            symbols = self.symbol_cache.get(root)
            summary = SymbolIndexer.summary(symbols)
        except OSError:
            summary = {}
        return SystemFacts(
            model=self.settings.model,
            modes=[mode.value for mode in ChatService.MODES],
            tools=self.tools(self.i18n.default_locale).names,
            output_dir=self.settings.output_dir,
            symbol_summary=summary,
            module_count=summary.get("files", 0),
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "offline": self.settings.offline,
            "execution": self.settings.execution,
            "execution_backend": self.settings.execution_backend,
            "token_required": bool(self.settings.api_token),
            "model": self.settings.model,
            "locales": list(self.i18n.supported),
            "default_locale": self.i18n.default_locale,
            "interpreters": list(self.interpreters.available),
            "features": {name: decision.enabled for name, decision in self.gate.summary().items()},
        }

    def blockchain_status(self) -> dict[str, Any]:
        """Lazy on purpose: the optional layer must never be able to take the server down."""
        try:
            from mirag.integrations import blockchain

            return blockchain.status().for_page()
        except Exception as exc:
            return {"available": False, "reason": f"{type(exc).__name__}: {exc}", "identity": None,
                    "wallet": None, "last_payment": None, "links": {}}


def _docker_probe_argv(settings: Settings) -> Callable[[str], list[str]]:
    """How `DependencyAnalyzer` checks whether an external import is importable, when the
    docker backend is selected: inside the SAME image the tests actually run in, not the host's
    Python. Without this, a curated library the runner image genuinely has would still be
    reported as a `missing_dependency` LIMIT, because the analyzer would be asking the wrong
    interpreter.

    Its own hardening stanza, scaled down from `DockerCodeRunner`'s: this is a sub-second
    `importlib.util.find_spec` check, not a test run, so tighter ceilings are enough and starting
    it faster matters more than for a probe that already has real work to do.
    """
    def build(script: str) -> list[str]:
        return [
            "docker", "run", "--rm", "--network", "none",
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL", "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
            "--pids-limit", "64", "--memory", "256m",
            "--user", "10001:10001", "-e", "HOME=/tmp",
            settings.docker_image, "python3", "-c", script,
        ]
    return build


def build_container(settings: Settings | None = None, model_builder: ModelBuilder | None = None,
                    gains: GainsRepository | None = None, corpus_loader: CorpusLoader | None = None,
                    tools_builder: Callable[[RetrievalEngine, str], ToolRegistry] | None = None) -> Container:
    settings = settings or Settings.from_env()
    # Only what is set is forwarded, so `I18n`'s own defaults stay the single definition of
    # where the bundled corpus is. Passing them unconditionally would put that path in two
    # places and invite the two to drift.
    overrides = {name: value for name, value in (
        ("knowledge_dir", settings.knowledge_dir),
        ("locales_dir", settings.locales_dir),
        ("supported", settings.supported_locales),
    ) if value is not None}
    i18n = I18n(settings.default_locale, **overrides)
    gate = FeatureGate(settings.env, gains or GainsRepository(FEATURE_GAINS_FILE))
    interpreters = InterpreterRegistry()
    runner: CodeExecutionBackend
    if settings.execution_backend == "docker":
        runner = DockerCodeRunner(
            image=settings.docker_image, timeout_s=settings.code_timeout_s,
            enabled=settings.execution, docker_timeout_s=settings.docker_cli_timeout_s,
            memory=settings.docker_memory, cpus=settings.docker_cpus,
            pids_limit=settings.docker_pids_limit)
        analyzer = DependencyAnalyzer(interpreters, probe_argv=_docker_probe_argv(settings))
    else:
        runner = CodeRunner(interpreters, timeout_s=settings.code_timeout_s, enabled=settings.execution)
        analyzer = DependencyAnalyzer(interpreters)
    syntax = SyntaxChecker(runner)
    vectors = VectorStoreFactory(settings.vector_backend, settings.openrouter_api_key, settings.offline,
                                 settings.embeddings_dir)
    artifacts = ArtifactRegistry(settings.artifacts_dir)
    artifacts.sweep_orphans()  # without this the folder grows without a ceiling
    gateways = LLMGatewayFactory(settings, model_builder) if model_builder else LLMGatewayFactory(settings)
    return Container(
        settings=settings,
        i18n=i18n,
        gate=gate,
        interpreters=interpreters,
        runner=runner,
        syntax=syntax,
        engines=(RetrievalEngineFactory(i18n, gate, vectors, corpus_loader) if corpus_loader
                 else RetrievalEngineFactory(i18n, gate, vectors)),
        symbol_cache=SymbolIndexCache(),
        artifacts=artifacts,
        traces=TraceWriter(settings.traces_dir / "pipeline.jsonl"),
        gateways=gateways,
        generator=ProjectGenerator(interpreters),
        certifier=ProjectCertifier(runner, syntax, analyzer),
        packager=Packager(),
        tools_builder=tools_builder,
    )
