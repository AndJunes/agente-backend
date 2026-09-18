from __future__ import annotations

from pathlib import Path

from mirag.core.settings import DEFAULT_MODEL, Settings, load_dotenv


def test_the_lock_is_on_by_default() -> None:
    assert Settings.from_env({}).offline is True


def test_the_lock_opens_only_on_purpose() -> None:
    assert Settings.from_env({"MIRAG_OFFLINE": "0"}).offline is False
    assert Settings.from_env({"MIRAG_OFFLINE": "false"}).offline is False
    assert Settings.from_env({"MIRAG_OFFLINE": "1"}).offline is True
    assert Settings.from_env({"MIRAG_OFFLINE": "yes"}).offline is True


def test_defaults_are_safe_and_explicit() -> None:
    settings = Settings.from_env({})
    assert settings.host == "127.0.0.1"  # loopback: no auth, never facing the network
    assert settings.port == 8000
    assert settings.model == DEFAULT_MODEL
    assert settings.budget_usd == 0.50
    assert settings.default_locale == "en"


def test_invalid_numbers_fall_back_to_defaults() -> None:
    settings = Settings.from_env({"MIRAG_PORT": "abc", "MIRAG_BUDGET_USD": "lots"})
    assert settings.port == 8000
    assert settings.budget_usd == 0.50


def test_runtime_folders_hang_from_the_data_dir(tmp_path: Path) -> None:
    settings = Settings.from_env({"MIRAG_DATA_DIR": str(tmp_path)})
    assert settings.output_dir == tmp_path / "output"
    assert settings.artifacts_dir == tmp_path / "artifacts"
    assert settings.traces_dir == tmp_path / "traces"


def test_locale_is_normalised() -> None:
    assert Settings.from_env({"MIRAG_LOCALE": " ES "}).default_locale == "es"


def test_dotenv_never_overrides_the_environment(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("# comment\nA=from_file\nB=from_file\n\n", encoding="utf-8")
    environ = {"A": "from_env"}
    assert load_dotenv(dotenv, environ) is True
    assert environ == {"A": "from_env", "B": "from_file"}


def test_a_missing_dotenv_is_not_an_error(tmp_path: Path) -> None:
    assert load_dotenv(tmp_path / "missing.env", {}) is False
