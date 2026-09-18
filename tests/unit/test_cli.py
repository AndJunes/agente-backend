"""The command line, driven in process with an isolated data directory."""

from __future__ import annotations

from pathlib import Path

import pytest

from mirag import __version__
from mirag.cli import build_parser, main


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_OFFLINE", "1")
    monkeypatch.setenv("MIRAG_DATA_DIR", str(tmp_path / "var"))


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_a_command_is_required() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_features_explain_every_flag(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["features", "--locale", "es"]) == 0
    out = capsys.readouterr().out
    assert "reranker" in out and "colbert" in out
    assert "no implementado" in out


def test_ask_runs_the_pipeline_offline_without_writing(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert main(["ask", "What is a PostgreSQL index?", "--locale", "en", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "retrieval" in out
    assert "SIMULATED" in out
    assert not (tmp_path / "var" / "traces").exists()


def test_traces_when_there_are_none(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["traces"]) == 0
    assert "No traces yet" in capsys.readouterr().out


@pytest.mark.slow
def test_demo_checks_a_contract(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo", "knowledge", "--locale", "es"]) == 0
    assert "[OK ]" in capsys.readouterr().out
