"""The Docker execution backend, proven against the real certifier.

    python scripts/check_docker_runner.py

Same shape as `check_delivery.py`: a hand-built `Project`, the real `ProjectCertifier`, no
model, no network cost. What is different here is `DockerCodeRunner` instead of `CodeRunner` —
this proves the curated bundle (`docker/runner-requirements.txt`) really resolves INSIDE the
container, that the marker-parsing contract (`TEST:<id>:PASS/FAIL`) survives the container hop
in both directions, that a hardening flag (`--read-only`) does not break pytest's need to write
`.pytest_cache/`, and that a disposable container is always gone afterwards - including when a
run is killed on timeout, which `--rm` alone does not guarantee.

Needs `make runner-image` run first (from `agente-backend`), and Docker reachable. Skips - does
not fail - when either is missing, the same way this script would behave in an environment that
never opted into MIRAG_EXECUTION_BACKEND=docker.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from mirag.execution.docker_runner import DockerCodeRunner
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.syntax import SyntaxChecker
from mirag.i18n.catalog import MessageCatalog
from mirag.projects.certification import ProjectCertifier, ProjectStatus
from mirag.projects.dependencies import DependencyAnalyzer
from mirag.projects.model import Project

IMAGE = "mirag-runner:latest"

MAIN = '''\
"""The service."""
from fastapi import FastAPI

app = FastAPI()


@app.get("/ping")
def ping():
    return {"ok": True}
'''

TEST_OK = '''\
import unittest

from fastapi.testclient import TestClient

from app.main import app


class PingTest(unittest.TestCase):
    def test_ping(self):
        client = TestClient(app)
        response = client.get("/ping")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
'''

TEST_BROKEN = TEST_OK.replace("self.assertEqual(response.status_code, 200)",
                              "self.assertEqual(response.status_code, 404)  # deliberately wrong")


def _docker_probe_argv(image: str):
    """The same probe stanza `container.py`'s `_docker_probe_argv` builds for the live agent -
    duplicated here on purpose, the way `check_delivery.py` wires its own `CodeRunner` rather
    than importing `container.py`: this script proves the PIECES, not the composition root."""
    def build(script: str) -> list[str]:
        return [
            "docker", "run", "--rm", "--network", "none",
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL", "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
            "--pids-limit", "64", "--memory", "256m",
            "--user", "10001:10001", "-e", "HOME=/tmp",
            image, "python3", "-c", script,
        ]
    return build


def docker_available() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=10,
                              check=False).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def build(*, test: str = TEST_OK) -> Project:
    project = Project("pingsvc")
    project.add("app/__init__.py", "", kind="code")
    project.add("app/main.py", MAIN, kind="entrypoint")
    project.add("tests/__init__.py", "", kind="test")
    project.add("tests/test_app.py", test, kind="test")
    return project


def certify(project: Project, test_command: str | None = None):
    runner = DockerCodeRunner(image=IMAGE, timeout_s=30, enabled=True)
    analyzer = DependencyAnalyzer(InterpreterRegistry(), probe_argv=_docker_probe_argv(IMAGE))
    certifier = ProjectCertifier(runner, SyntaxChecker(runner), analyzer)
    catalog = MessageCatalog.from_file("en", Path("src/mirag/locales/en/messages.json"))
    return certifier.certify(project.seal(), catalog, test_command=test_command)


def running_containers() -> list[str]:
    completed = subprocess.run(
        ["docker", "ps", "-a", "--filter", "name=mirag-run-", "--format", "{{.Names}}"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def main() -> int:
    if not docker_available():
        print("SKIP: docker is not reachable on this machine.")
        return 0
    check_image = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True,
                                 timeout=10, check=False)
    if check_image.returncode != 0:
        print(f"SKIP: image {IMAGE!r} not found. Build it first with 'make runner-image'.")
        return 0

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    print("\n=== A. the curated bundle resolves inside the container ===")
    certificate = certify(build())
    check("VERIFIED", certificate.status is ProjectStatus.VERIFIED, certificate.status.value)
    check("a passing marker was seen",
          any(v == "PASS" for v in certificate.markers.values()), str(certificate.markers))

    print("\n=== B. a failing test survives the container hop ===")
    certificate = certify(build(test=TEST_BROKEN))
    check("not VERIFIED", certificate.status is not ProjectStatus.VERIFIED, certificate.status.value)
    check("a failing marker was seen",
          any(v == "FAIL" for v in certificate.markers.values()), str(certificate.markers))

    print("\n=== C. pytest writes .pytest_cache/ under a --read-only root fs ===")
    certificate = certify(build(), test_command="pytest -q")
    check("documented_command ok",
          any(p.name == "documented_command" and p.status.value == "ok" for p in certificate.phases),
          "; ".join(f"{p.name}={p.status.value}" for p in certificate.phases))

    print("\n=== D. cleanup: no container left behind, including on a forced timeout ===")
    left = running_containers()
    check("nothing dangling after A-C", not left, str(left))

    runner = DockerCodeRunner(image=IMAGE, timeout_s=1, enabled=True)
    result = runner.run({"slow.py": "import time\ntime.sleep(10)\n"}, "python3 slow.py")
    check("the slow run reports NOT EXECUTED", result.status.value == "not_executed", result.header)
    left = running_containers()
    check("nothing dangling after a timeout", not left, str(left))

    print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILED: {failures}"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
