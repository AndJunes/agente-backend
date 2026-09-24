"""Does the dependency gate really lift the ceiling, inside the sandbox and nowhere else?

    python scripts/check_installation.py

The unit tests replace Docker with a double, because what they are about is the decisions —
which volume, when to reuse, what to do with a non-zero exit — and none of that needs a
daemon. This one is the other half: it pulls a real package from PyPI into a real Docker
volume, mounts that volume into the real sandbox, and asks the real analyzer whether the
import that was missing is now there.

It needs Docker and the runner image (`make runner-image`), and it skips cleanly without
them. It creates one volume and removes it again; nothing is written to this checkout, to the
host filesystem or to the interpreter running this script — which is the property the whole
module exists to have.

What it checks:

  1. A package the sandbox does NOT have is reported missing, as a LIMIT.
  2. `DockerInstaller` puts it in a volume, and the volume is labelled so it can be found.
  3. The analyzer, asked again WITH the volume, says the import resolves.
  4. `DockerCodeRunner` runs code that imports it — which is the thing the ceiling stopped.
  5. The test container still has no network, and gets the volume read-only.
  6. The second install of the same requirements downloads nothing.
  7. Nothing landed outside Docker.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mirag.container import _docker_probe_argv
from mirag.core.settings import Settings
from mirag.execution.docker_runner import DockerCodeRunner
from mirag.projects.dependencies import DependencyAnalyzer, Severity
from mirag.projects.installation import (
    LABEL,
    DockerInstaller,
    parse_requirements,
)
from mirag.projects.model import Project

# Tiny, pure Python, no build step, and not in the runner image. The point is the plumbing.
PACKAGE = "six"
VERSION = "1.17.0"

SOURCE = f"""\
import {PACKAGE}


def create_thing():
    return {PACKAGE}.__name__
"""

IMAGE = "mirag-runner:latest"

failures: list[str] = []


def check(what: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {what}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(what)


def demo_project() -> Project:
    return Project.from_mapping("install-demo", {
        "app/__init__.py": "",
        "app/main.py": SOURCE,
        "tests/test_main.py": "def test_it():\n    assert True\n",
        "requirements.txt": f"{PACKAGE}=={VERSION}\n",
    })


def docker(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", *argv], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60, check=False)


def available() -> str:
    """``""`` when this machine can run the check, else why it cannot."""
    try:
        if docker("version", "--format", "{{.Server.Version}}").returncode != 0:
            return "the Docker daemon is not answering"
    except (OSError, subprocess.SubprocessError) as exc:
        return f"docker could not be run: {exc}"
    if docker("image", "inspect", IMAGE).returncode != 0:
        return f"the image {IMAGE!r} is missing — build it once with `make runner-image`"
    return ""


def main() -> int:
    if reason := available():
        print(f"SKIP: {reason}")
        return 0

    settings = Settings.from_env(dotenv=False)
    analyzer = DependencyAnalyzer(
        DockerCodeRunner(image=IMAGE).interpreters,
        probe_argv=_docker_probe_argv(Settings(docker_image=IMAGE, env=settings.env)))
    runner = DockerCodeRunner(image=IMAGE, enabled=True)
    installer = DockerInstaller(image=IMAGE, enabled=True)
    project = demo_project()
    volume = ""

    try:
        print(f"=== 1. before installing, {PACKAGE!r} is a LIMIT, not an error ===")
        _imports, findings = analyzer.analyze(project)
        missing = [f for f in findings if f.kind == "missing_dependency"]
        already = not missing
        if already:
            print(f"  SKIP  {PACKAGE!r} is already in the image; the ceiling cannot be shown")
        else:
            check(f"{PACKAGE!r} is reported missing", missing[0].subject == PACKAGE)
            check("and it is a LIMIT, never an ERROR", missing[0].severity is Severity.LIMIT)
            check("so nothing about the project itself is wrong",
                  not DependencyAnalyzer.of_severity(findings, Severity.ERROR))

        print("\n=== 2. the install ===")
        report = installer.install(project)
        check("it succeeded", report.ok, report.detail)
        if not report.ok:
            print(report.log[-1500:])
            return 1
        volume = report.volume
        check("it named a volume, not a path",
              "/" not in volume and "\\" not in volume, volume)
        listed = docker("volume", "ls", "--filter", f"label={LABEL}", "-q").stdout
        check("and the volume is labelled so it can be found again", volume in listed)

        print("\n=== 3. the analyzer, asked again with that volume ===")
        _imports, findings = analyzer.analyze(project, volume)
        check("the import now resolves",
              not [f for f in findings if f.kind == "missing_dependency"],
              str([f.detail for f in findings if f.kind == "missing_dependency"]))

        print("\n=== 4. and real code in the sandbox can really import it ===")
        probe = {**project.as_text_mapping(),
                 "_check.py": "from app.main import create_thing\n"
                              f"print('TEST:import:' + ('PASS' if create_thing() == {PACKAGE!r} "
                              "else 'FAIL'))\n"}
        result = runner.run(probe, "python3 _check.py", dependencies=volume)
        check("the run is green", result.is_green, result.header)
        check("and the marker came from the imported package",
              result.markers.get("import") == "PASS", str(result.markers))

        without = runner.run(probe, "python3 _check.py")
        if not already:
            check("without the volume the same run fails, which is the ceiling",
                  not without.is_green, without.header)

        print("\n=== 5. the sandbox is still a sandbox ===")
        offline = runner.run(
            {"_net.py": "import socket\n"
                        "try:\n"
                        "    socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
                        "    print('TEST:offline:FAIL')\n"
                        "except OSError:\n"
                        "    print('TEST:offline:PASS')\n"},
            "python3 _net.py", dependencies=volume)
        check("the test container has no network even while mounting the volume",
              offline.markers.get("offline") == "PASS", offline.header)

        readonly = runner.run(
            {"_ro.py": "import pathlib\n"
                       "try:\n"
                       "    pathlib.Path('/deps/evil.py').write_text('x')\n"
                       "    print('TEST:readonly:FAIL')\n"
                       "except OSError:\n"
                       "    print('TEST:readonly:PASS')\n"},
            "python3 _ro.py", dependencies=volume)
        check("and it cannot write into the dependency volume",
              readonly.markers.get("readonly") == "PASS", readonly.header)

        print("\n=== 6. the same requirements a second time ===")
        again = installer.install(demo_project())
        check("it was reused, not downloaded", again.reused)
        check("and it is the same volume", again.volume == volume)

        print("\n=== 7. nothing landed outside Docker ===")
        root = Path(__file__).resolve().parent.parent
        check("no deps directory appeared in the checkout", not (root / "var" / "deps").exists())
        check(f"{PACKAGE!r} is still not importable by THIS interpreter",
              PACKAGE not in sys.modules and _not_importable(PACKAGE))

        print("\n=== 8. a requirements.txt of pip flags ===")
        accepted, refused = parse_requirements(
            "-r /etc/passwd\n--index-url https://evil.invalid/simple\n-e .\n"
            "git+ssh://git@evil.invalid/x.git\n")
        check("nothing is accepted", accepted == (), str(accepted))
        check("and all four are named back", len(refused) == 4, str(refused))
    finally:
        if volume:
            docker("volume", "rm", "-f", volume)

    print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILED: {failures}"))
    return 1 if failures else 0


def _not_importable(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is None


if __name__ == "__main__":
    sys.exit(main())
