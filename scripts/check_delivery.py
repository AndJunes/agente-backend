"""The delivery contract: what was planned is what gets delivered, or nothing does.

    python scripts/check_delivery.py

Two rules, and both were broken in a way that shipped:

1. **A project missing files the plan asked for is INCOMPLETE.** `validate_structure` checks
   four things and none of them is "the planned files exist" — it never reads the plan at all.
   Measured on a real run: a blueprint of 36 files delivered 12, the twelve happened to compile
   and import each other cleanly, and the verdict came out with a download button.

2. **A rejected verdict takes the download away.** `Artifact.downloadable` asked only whether
   the ZIP was well formed, which says nothing about the project inside it. FAILED projects
   were downloadable too.

The third case here is the one that keeps the rule honest: a file the model wrote WITHOUT it
being planned is allowed. Models consolidate two planned modules into one that carries both,
and that is usually the better call.

Run by CI. It uses no model and no network.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.runner import CodeRunner
from mirag.execution.syntax import SyntaxChecker
from mirag.i18n.catalog import MessageCatalog
from mirag.projects.artifacts import ArtifactRegistry
from mirag.projects.certification import ProjectCertifier, ProjectStatus
from mirag.projects.dependencies import DependencyAnalyzer
from mirag.projects.model import Project
from mirag.projects.packaging import Packager

MAIN = '''\
"""The server."""
import http.server

from app.store import Store


def create_server(port=0, db=":memory:"):
    return http.server.ThreadingHTTPServer(("127.0.0.1", port),
                                           http.server.BaseHTTPRequestHandler)
'''
STORE = '''\
"""Where the things live."""


class Store:
    def __init__(self):
        self.rows = {}
'''
PLANNED = ("app/__init__.py", "app/main.py", "app/store.py",
           "tests/__init__.py", "tests/test_app.py", "README.md")


def build(*, drop: str = "", add: str = "") -> Project:
    project = Project("clinic", {"entity": "visit"})
    project.add("app/__init__.py", "", kind="code")
    project.add("app/main.py", MAIN, kind="entrypoint")
    if drop != "app/store.py":
        project.add("app/store.py", STORE, kind="code")
    project.add("tests/__init__.py", "", kind="test")
    if drop != "tests/test_app.py":
        project.add("tests/test_app.py", "import unittest\n", kind="test")
    if drop != "README.md":
        project.add("README.md", "# Clinic\n\nRun it with `python -m app.main`.\n", kind="doc")
    if add:
        project.add(add, "# an extra the model decided to write\n", kind="code")
    return project


def certify(project: Project, expected=PLANNED):
    runner = CodeRunner(InterpreterRegistry(), enabled=False)
    certifier = ProjectCertifier(runner, SyntaxChecker(runner),
                                 DependencyAnalyzer(InterpreterRegistry()))
    catalog = MessageCatalog.from_file("en", Path("src/mirag/locales/en/messages.json"))
    return certifier.certify(project.seal(), catalog, expected=expected)


def downloadable(project: Project, certificate) -> bool:
    package = Packager().seal(project, certificate)
    with tempfile.TemporaryDirectory() as folder:
        artifact = ArtifactRegistry(Path(folder)).save(project, certificate, package,
                                                       on_disk=False)
        return artifact.download_url is not None


def main() -> int:
    failures = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    print("\n=== every planned file is there ===")
    whole = build()
    verdict = certify(whole)
    check("not INCOMPLETE", verdict.status is not ProjectStatus.INCOMPLETE, verdict.status.value)
    check("downloadable", downloadable(verdict.project or whole, verdict))
    check("the plan phase says so",
          any(p.name == "plan" and p.status.value == "ok" for p in verdict.phases),
          "; ".join(f"{p.name}={p.status.value}" for p in verdict.phases))

    for missing in ("app/store.py", "README.md", "tests/test_app.py"):
        print(f"\n=== missing {missing} ===")
        broken = build(drop=missing)
        verdict = certify(broken)
        check("INCOMPLETE", verdict.status is ProjectStatus.INCOMPLETE, verdict.status.value)
        check("the reason names the file", missing in verdict.reason, verdict.reason[:100])
        check("NOT downloadable", not downloadable(verdict.project or broken, verdict))

    print("\n=== a file nobody planned ===")
    generous = build(add="app/extra.py")
    verdict = certify(generous)
    check("still not INCOMPLETE", verdict.status is not ProjectStatus.INCOMPLETE, verdict.status.value)
    check("downloadable", downloadable(verdict.project or generous, verdict))

    print("\n=== no plan given: the old behaviour is untouched ===")
    verdict = certify(build(drop="README.md"), expected=())
    check("no plan means no plan check", verdict.status is not ProjectStatus.INCOMPLETE,
          verdict.status.value)

    print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILED: {failures}"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
