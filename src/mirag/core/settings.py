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
DEFAULT_LOCALE = "en"


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
    openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"
    budget_usd: float = 0.50
    """Spending cap per request. 0 disables the cap (accounting only)."""

    max_output_tokens: int = 12_000
    llm_timeout_s: float = 60.0

    default_locale: str = DEFAULT_LOCALE
    host: str = "127.0.0.1"
    """Loopback on purpose: a single-user local tool with no auth must not face the network."""
    port: int = 8000

    data_dir: Path = field(default_factory=default_data_dir)
    symbols_root: Path | None = None
    vector_backend: str = "local"
    code_timeout_s: int = 30

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
        data_dir = Path(env["MIRAG_DATA_DIR"]) if env.get("MIRAG_DATA_DIR") else default_data_dir()
        symbols_root = env.get("MIRAG_SYMBOLS_ROOT")
        return cls(
            offline=_flag(env, "MIRAG_OFFLINE", True),
            model=env.get("MIRAG_MODEL", DEFAULT_MODEL),
            openrouter_api_key=env.get("OPENROUTER_API_KEY", ""),
            budget_usd=_float(env, "MIRAG_BUDGET_USD", 0.50),
            max_output_tokens=_int(env, "MIRAG_MAX_OUTPUT_TOKENS", 12_000),
            default_locale=(env.get("MIRAG_LOCALE") or DEFAULT_LOCALE).strip().lower(),
            host=env.get("MIRAG_HOST", "127.0.0.1"),
            port=_int(env, "MIRAG_PORT", 8000),
            data_dir=data_dir,
            symbols_root=Path(symbols_root) if symbols_root else None,
            vector_backend=(env.get("MIRAG_VECTOR_BACKEND") or "local").strip().lower(),
            code_timeout_s=_int(env, "MIRAG_CODE_TIMEOUT_S", 30),
            env=env,
        )

    def resolved_symbols_root(self) -> Path:
        """The code base the symbol index reads: Mirag's own sources by default."""
        if self.symbols_root is not None:
            return self.symbols_root
        root = source_checkout_root()
        from mirag.paths import PACKAGE_ROOT

        return (root / "src") if root else PACKAGE_ROOT
