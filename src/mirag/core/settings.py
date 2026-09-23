"""Application settings, read once from the environment (and an optional ``.env``).

Every tunable lives here with its default, so there is one place to read what can be
configured. Services receive a :class:`Settings` instance through the container; none of
them reads ``os.environ`` on its own (the blockchain layer is the documented exception:
its lock is re-read on every call so that tests can flip it between cases).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from mirag.paths import default_data_dir, source_checkout_root

DEFAULT_MODEL = "anthropic/claude-haiku-4.5"
DEFAULT_LLM_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_LOCALE = "en"

# The three clocks, declared once so the dataclass default and the `from_env` default cannot
# drift apart. They already had: `budget_usd` writes 0.50 in both places.
DEFAULT_LLM_TIMEOUT_S = 60.0
DEFAULT_LLM_CALL_TIMEOUT_S = 600.0
DEFAULT_RUN_TIMEOUT_S = 2_100.0

_LEGACY_NAMES = {"MIRAG_MODELO": "MIRAG_MODEL", "LIMITE_USD": "MIRAG_BUDGET_USD",
                 "MIRAG_EJECUCION": "MIRAG_EXECUTION"}


def load_dotenv(path: Path, environ: dict[str, str] | None = None) -> bool:
    """Load ``KEY=value`` lines into the environment without overriding existing keys.

    A missing file is not an error: the project must import on a clean machine without
    keys (tests run offline). Only whoever actually calls the model fails.
    """
    target = os.environ if environ is None else environ
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key.strip():
            target.setdefault(key.strip(), value.strip())
    return True


def _flag(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off", "")


def _float(env: Mapping[str, str], name: str, default: float) -> float:
    try:
        return float(env.get(name, default))
    except (TypeError, ValueError):
        return default


def _int(env: Mapping[str, str], name: str, default: int) -> int:
    try:
        return int(env.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime configuration."""

    offline: bool = True
    """The lock: by default nobody is called. Spending real money is opt-in (MIRAG_OFFLINE=0)."""

    model: str = DEFAULT_MODEL
    openrouter_api_key: str = ""
    openrouter_url: str = DEFAULT_LLM_URL
    budget_usd: float = 0.50
    """Spending cap per request. 0 disables the cap (accounting only)."""

    max_output_tokens: int = 12_000

    llm_timeout_s: float = DEFAULT_LLM_TIMEOUT_S
    """Seconds allowed for ONE SOCKET OPERATION, and the name has been read as more than that.

    It bounds a single `recv`, and every byte that arrives rearms it — so a provider sending
    one byte a minute never trips it. It is the cheap first line against a peer that says
    nothing at all; `llm_call_timeout_s` is the bound."""

    llm_call_timeout_s: float = DEFAULT_LLM_CALL_TIMEOUT_S
    """Total wall clock for one model call, its retries and its backoff sleeps included.

    Measured: one call on a free model averages 234 seconds, so this is about 2.5x."""

    run_timeout_s: float = DEFAULT_RUN_TIMEOUT_S
    """Total wall clock for one request: generation, certification and everything between.

    35 minutes against a measured 15-25 minute worst case. `0` disables it, which is what a
    CLI run or a benchmark wants — neither has anybody waiting on the other end."""

    cancel_on_disconnect: bool = True
    """Whether closing the tab stops the work, or only stops the writing.

    It was only ever the second. A closed tab left the generation running and being billed
    to the end, because the flag that noticed only guarded the SSE writes."""

    default_locale: str = DEFAULT_LOCALE
    host: str = "127.0.0.1"
    """Loopback on purpose: opening it to a network must be a deliberate, visible act."""
    port: int = 8000
    api_token: str = field(default="", repr=False)
    """Shared secret the caller sends in ``X-Mirag-Token``. Empty = the server is open to
    whoever reaches its port (the local mode), and it says so at startup. There is no default
    token on purpose: a factory secret is known to everybody."""

    data_dir: Path = field(default_factory=default_data_dir)
    symbols_root: Path | None = None
    vector_backend: str = "local"
    code_timeout_s: int = 30
    execution: bool = False
    """Run the generated code and its tests? Off: the agent delivers them WITHOUT running them
    (running them is the QA agent's job) and the verdict is ``not_executed`` - never a pass,
    never a fail. The machinery stays whole: the demos and the benchmarks switch it on."""

    console: bool = False
    """Let a caller run commands against a delivered project (``POST .../artifacts/{id}/exec``).

    OFF unless asked for, and it is not the same switch as `execution`. Verification runs code
    Mirag chose, against a fixed probe. This runs whatever command the caller types, on this
    machine, in a copy of the project: an interpreter and a package manager on demand. That is
    exactly what a person needs to see a generated server start, and exactly what must not be
    reachable by anybody who happens to find the port — so it needs the flag AND the token."""

    console_timeout_s: int = 600
    """How long one console command may run before it is stopped. A server left running is the
    normal case, so this is minutes, not the 30 seconds a test gets."""

    install_dependencies: bool = True
    """Install what a generated project declares, instead of reporting that it cannot run here.

    ON by default, and that is not the exception to the rest of these defaults it looks like:
    it can only ever happen inside `execution`, which is OFF. A deployment that has not asked
    for code to run never reaches this; one that HAS asked is a deployment that wants the
    tests to actually mean something, and `fastapi is not installed on this machine` is not an
    answer that deployment wanted. Only `requirements.txt`, only pinned package names, and
    only into a directory of their own — see `projects/installation.py`."""

    install_timeout_s: int = 300
    """Wall clock for ONE install. The run's own deadline is the real bound; this stops a
    single wheel that will not build from eating all of it."""

    max_repairs: int = 3
    """Repair attempts PER MOTIVE (syntax, imports, failing tests), spent by the convergence
    loop. `0` delivers whatever the generator produced, unrepaired."""

    execution_backend: str = "subprocess"
    """Where a probe actually runs. ``"subprocess"``: the host, allow-listed and stripped down
    (``execution/runner.py``) - today's behaviour, unchanged for anyone who has not opted in.
    ``"docker"``: a disposable, capped, network-isolated container per probe
    (``execution/docker_runner.py``), built from ``docker/runner.Dockerfile``. Anything else
    falls back to ``"subprocess"`` rather than raising - a typo here should not take execution
    down, the same lenient convention ``vector_backend`` already uses.

    Defaults to the host: Docker Desktop is not guaranteed to be on every machine this agent
    runs on, the same reasoning behind every other safety-relevant default here."""

    docker_image: str = "mirag-runner:latest"
    docker_memory: str = "512m"
    docker_cpus: str = "1.0"
    docker_pids_limit: int = 128
    """Ceilings for ONE disposable probe container - tighter than the long-lived `mirag`
    service's own (1g / 1.5 cpus / 256 pids in docker-compose.yml): this runs one bounded test
    invocation, not a server absorbing concurrent requests."""

    docker_cli_timeout_s: int = 10
    """Seconds allowed for the `docker` CLI itself (the image-existence check, forced cleanup)
    - separate from `code_timeout_s`, which bounds what runs INSIDE the container."""

    knowledge_dir: Path | None = None
    """Where the corpus lives. ``None`` means the one bundled with the package.

    It exists so that a second process can serve a different body of knowledge from the same
    image, which is how two agents share this code without sharing a corpus. ``I18n`` has
    always accepted the directory as an argument; until now nothing passed one.

    Deliberately ``None`` rather than the package default: keeping ``KNOWLEDGE_DIR`` imported
    in exactly one module (``i18n/registry.py``) is what makes "this process reads one corpus"
    checkable with a grep instead of by reading every file.
    """

    locales_dir: Path | None = None
    """Where ``messages/ui/lexicon/corpus.json`` live. ``None`` means the bundled ones.

    Travels with ``knowledge_dir``: the lexicon is the agent's vocabulary — which words mean
    code, which mean a project, which demos exist — so a different corpus with the same
    lexicon would be an agent that reads one subject and classifies questions as another.
    """

    supported_locales: tuple[str, ...] | None = None
    """Which locales this process serves. ``None`` means the bundled tuple."""

    system_prompt: str = ""
    """What the agent is told it is. Empty means the bundled backend prompt.

    Read from ``MIRAG_SYSTEM_PROMPT``. It sits beside the corpus and the lexicon because the
    three have to agree: a process reading product-management documents, classifying questions
    with product-management vocabulary and then told it is a backend tutor would answer in the
    wrong voice about the right material.
    """

    env: Mapping[str, str] = field(default_factory=dict, repr=False, compare=False)
    """The environment the settings were read from; feature flags resolve against it."""

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "output"

    @property
    def artifacts_dir(self) -> Path:
        return self.data_dir / "artifacts"

    @property
    def traces_dir(self) -> Path:
        return self.data_dir / "traces"

    @property
    def workspaces_dir(self) -> Path:
        return self.data_dir / "workspaces"

    @property
    def embeddings_dir(self) -> Path:
        return self.data_dir / "embeddings"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None, *, dotenv: bool = True) -> Settings:
        """Build settings from ``environ`` (default: ``os.environ`` plus ``.env``)."""
        if environ is None:
            if dotenv and (root := source_checkout_root()) is not None:
                load_dotenv(root / ".env")
            environ = dict(os.environ)
        env = dict(environ)
        # Deployments made before the move to src/ used Spanish names. Ignoring them silently
        # would, for example, switch a free-model server to the paid default.
        for legacy, current in _LEGACY_NAMES.items():
            if legacy in env and current not in env:
                env[current] = env[legacy]
        data_dir = Path(env["MIRAG_DATA_DIR"]) if env.get("MIRAG_DATA_DIR") else default_data_dir()
        symbols_root = env.get("MIRAG_SYMBOLS_ROOT")
        knowledge_dir = env.get("MIRAG_KNOWLEDGE_DIR")
        locales_dir = env.get("MIRAG_LOCALES_DIR")
        locales = tuple(c.strip().lower() for c in env.get("MIRAG_LOCALES", "").split(",") if c.strip())
        return cls(
            offline=_flag(env, "MIRAG_OFFLINE", True),
            model=(env.get("MIRAG_MODEL") or "").strip() or DEFAULT_MODEL,
            openrouter_api_key=env.get("OPENROUTER_API_KEY", ""),
            # Every provider worth using (OpenRouter, NVIDIA, Groq, Gemini) speaks the same
            # chat/completions dialect: switching is this URL plus the model, nothing else.
            openrouter_url=(env.get("MIRAG_LLM_URL") or "").strip() or DEFAULT_LLM_URL,
            budget_usd=_float(env, "MIRAG_BUDGET_USD", 0.50),
            # `llm_timeout_s` was declared and never read from the environment: `from_env`
            # simply did not list it, so it was pinned at its default in every deployment.
            llm_timeout_s=_float(env, "MIRAG_LLM_TIMEOUT_S", DEFAULT_LLM_TIMEOUT_S),
            llm_call_timeout_s=_float(env, "MIRAG_LLM_CALL_TIMEOUT_S", DEFAULT_LLM_CALL_TIMEOUT_S),
            run_timeout_s=_float(env, "MIRAG_RUN_TIMEOUT_S", DEFAULT_RUN_TIMEOUT_S),
            cancel_on_disconnect=_flag(env, "MIRAG_CANCEL_ON_DISCONNECT", True),
            max_output_tokens=_int(env, "MIRAG_MAX_OUTPUT_TOKENS", 12_000),
            default_locale=(env.get("MIRAG_LOCALE") or DEFAULT_LOCALE).strip().lower(),
            host=(env.get("MIRAG_HOST") or "").strip() or "127.0.0.1",
            port=_int(env, "MIRAG_PORT", 8000),
            api_token=(env.get("MIRAG_TOKEN") or "").strip(),
            data_dir=data_dir,
            symbols_root=Path(symbols_root) if symbols_root else None,
            vector_backend=(env.get("MIRAG_VECTOR_BACKEND") or "local").strip().lower(),
            code_timeout_s=_int(env, "MIRAG_CODE_TIMEOUT_S", 30),
            execution=_flag(env, "MIRAG_EXECUTION", False),
            console=_flag(env, "MIRAG_CONSOLE", False),
            console_timeout_s=_int(env, "MIRAG_CONSOLE_TIMEOUT_S", 600),
            install_dependencies=_flag(env, "MIRAG_INSTALL_DEPENDENCIES", True),
            install_timeout_s=_int(env, "MIRAG_INSTALL_TIMEOUT_S", 300),
            max_repairs=_int(env, "MIRAG_MAX_REPAIRS", 3),
            execution_backend=(env.get("MIRAG_EXECUTION_BACKEND") or "subprocess").strip().lower(),
            docker_image=(env.get("MIRAG_DOCKER_IMAGE") or "").strip() or "mirag-runner:latest",
            docker_memory=(env.get("MIRAG_DOCKER_MEMORY") or "").strip() or "512m",
            docker_cpus=(env.get("MIRAG_DOCKER_CPUS") or "").strip() or "1.0",
            docker_pids_limit=_int(env, "MIRAG_DOCKER_PIDS_LIMIT", 128),
            docker_cli_timeout_s=_int(env, "MIRAG_DOCKER_CLI_TIMEOUT_S", 10),
            knowledge_dir=Path(knowledge_dir) if knowledge_dir else None,
            locales_dir=Path(locales_dir) if locales_dir else None,
            supported_locales=locales or None,
            system_prompt=(env.get("MIRAG_SYSTEM_PROMPT") or "").strip(),
            env=env,
        )

    def resolved_symbols_root(self) -> Path:
        """The code base the symbol index reads: Mirag's own sources by default."""
        if self.symbols_root is not None:
            return self.symbols_root
        root = source_checkout_root()
        from mirag.paths import PACKAGE_ROOT

        return (root / "src") if root else PACKAGE_ROOT
