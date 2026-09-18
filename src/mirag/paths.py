"""Filesystem anchors.

Every path the application reads or writes is derived from here, never from the current
working directory: starting the server from another folder must not make it read another
corpus or empty somebody else's ``output/`` folder.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
"""``src/mirag`` - package code and bundled resources."""

LOCALES_DIR = PACKAGE_ROOT / "locales"
KNOWLEDGE_DIR = PACKAGE_ROOT / "knowledge"
RESOURCES_DIR = PACKAGE_ROOT / "resources"
WEB_DIR = PACKAGE_ROOT / "web"

FEATURE_GAINS_FILE = RESOURCES_DIR / "feature_gains.json"
"""Measured gains per retrieval stage. Production reads it; the benchmarks write it."""


def source_checkout_root() -> Path | None:
    """The repository root when running from a source checkout, else ``None``."""
    candidate = PACKAGE_ROOT.parent.parent
    return candidate if (candidate / "pyproject.toml").is_file() else None


def default_data_dir() -> Path:
    """Where runtime output goes when ``MIRAG_DATA_DIR`` is not set.

    In a source checkout it is ``<repo>/var`` (git-ignored). In an installed package it is
    ``~/.mirag``: writing into ``site-packages`` is never acceptable.
    """
    root = source_checkout_root()
    return (root / "var") if root else (Path.home() / ".mirag")
