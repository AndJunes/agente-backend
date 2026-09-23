"""Where this package's own resources live.

Anchored to the package for the same reason ``mirag.paths`` is: starting the server from
another folder must not change which corpus it reads.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent

KNOWLEDGE_DIR = PACKAGE_ROOT / "knowledge"
LOCALES_DIR = PACKAGE_ROOT / "locales"
SKILLS_DIR = PACKAGE_ROOT / "skills"
EXAMPLES_DIR = PACKAGE_ROOT / "examples"

DOCUMENTS_LOCALE = "en"
"""The one language the documents are written in.

The knowledge base is English throughout; that is a fact about the content, not a
configuration choice. Spanish is still a supported *answer* language — the locale selects the
message catalogue, which carries the directive telling the model which language to write in,
and the documents it reads are the same either way. ``PmCorpus.load`` resolves this, so the
fact is stated in one place instead of being simulated with a duplicated directory tree.
"""
