"""Shared fixtures.

Every test runs OFFLINE (no model call can ever be made) and with an isolated data
directory: no test may write into the repository or into another test's folders.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from mirag.container import Container, build_container
from mirag.core.settings import Settings
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.runner import CodeRunner
from mirag.execution.syntax import SyntaxChecker
from mirag.features.flags import FeatureGate
from mirag.i18n.catalog import MessageCatalog
from mirag.i18n.registry import I18n
from mirag.retrieval.engine import RetrievalEngine, RetrievalEngineFactory
from mirag.retrieval.vectors import VectorStoreFactory

LOCALES = ("en", "es")


def offline_settings(data_dir: Path, **extra: str) -> Settings:
    env = {"MIRAG_OFFLINE": "1", "MIRAG_DATA_DIR": str(data_dir), **extra}
    return Settings.from_env(env)


@pytest.fixture(scope="session")
def i18n() -> I18n:
    return I18n("en")


@pytest.fixture(scope="session")
def catalog_en(i18n: I18n) -> MessageCatalog:
    return i18n.catalog("en")


@pytest.fixture(scope="session")
def catalog_es(i18n: I18n) -> MessageCatalog:
    return i18n.catalog("es")


@pytest.fixture(scope="session")
def engines(i18n: I18n) -> RetrievalEngineFactory:
    """Retrieval engines with the default (measured) feature policy and no env overrides."""
    return RetrievalEngineFactory(i18n, FeatureGate({}), VectorStoreFactory("local"))


@pytest.fixture(scope="session")
def engine_en(engines: RetrievalEngineFactory) -> RetrievalEngine:
    return engines.get("en")


@pytest.fixture(scope="session")
def engine_es(engines: RetrievalEngineFactory) -> RetrievalEngine:
    return engines.get("es")


@pytest.fixture(params=LOCALES)
def engine(request: pytest.FixtureRequest, engines: RetrievalEngineFactory) -> RetrievalEngine:
    """Parametrised over every supported locale."""
    return engines.get(request.param)


@pytest.fixture(scope="session")
def interpreters() -> InterpreterRegistry:
    return InterpreterRegistry()


@pytest.fixture(scope="session")
def runner(interpreters: InterpreterRegistry) -> CodeRunner:
    return CodeRunner(interpreters, timeout_s=30)


@pytest.fixture(scope="session")
def syntax(runner: CodeRunner) -> SyntaxChecker:
    return SyntaxChecker(runner)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return offline_settings(tmp_path / "var")


@pytest.fixture
def container(settings: Settings) -> Container:
    return build_container(settings)


@pytest.fixture(scope="session")
def shared_container(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Container]:
    """One container for read-only tests: building engines per test would cost seconds."""
    yield build_container(offline_settings(tmp_path_factory.mktemp("shared") / "var"))
