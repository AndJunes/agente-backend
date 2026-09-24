"""Installing what the project declares — inside the sandbox, and nowhere else.

THE CEILING THIS REMOVES
    ``dependencies.py`` tells a broken import (the project is wrong) from a missing external
    package (this machine cannot check it), and certification turns the second into a CEILING:
    the project stays VALIDATED, says which package is missing, and its tests are never run.
    That is the honest verdict for a machine that cannot install anything. It is the wrong
    verdict for a machine that can: a FastAPI project was being delivered unexecuted because
    ``fastapi`` was not importable, when installing it is one bounded command.

    So the ceiling stays and stops being the FIRST answer. Install what the project declared,
    ask the analyzer again, and only then decide. When the install fails — no network, a
    package that does not exist, a wheel that will not build — nothing is lost: the old
    ceiling is exactly where the run lands, now with the install log attached to say why.

WHERE THE PACKAGES GO, WHICH IS THE POINT OF THIS FILE
    Into a **Docker volume**, mounted into the same sandbox the tests run in. Not into the
    interpreter running Mirag, not into this checkout, not anywhere on the host filesystem at
    all — a generated project's dependencies are untrusted third-party code chosen by a model,
    and the one place they belong is the disposable container that was already going to run
    that project's tests.

    The first version of this installed to ``var/deps`` with ``pip --target`` and pointed
    ``PYTHONPATH`` at it. That put arbitrary packages inside the source tree, and on the
    default backend it put them on the host outright. A volume is the same idea with the
    isolation actually present: Docker owns it, nothing on the host can see it, and removing
    it is ``docker volume rm``.

    Which means installing REQUIRES the Docker execution backend. On the host backend there is
    no sandbox to install into, so there is no install: certification gets a
    :class:`NullInstaller` that says exactly that, and the project keeps the old ceiling.

TWO CONTAINERS, AND WHY NOT ONE
    The install container has a network and no project code in it. The test container has the
    project and ``--network none``, and receives the volume READ-ONLY. If those were one
    container, a generated test could pass by calling the network — which is the failure mode
    the whole execution sandbox exists to prevent.

    A third, very short container seals the volume afterwards: it writes the marker file that
    makes the volume reusable and makes the tree readable by the unprivileged uid the test
    container runs as. It exists so that nothing here needs a shell — every container is
    started with an argv, so a package name can never be a shell fragment.

WHAT IS INSTALLED, AND WHAT IS REFUSED
    Only ``requirements.txt``, only lines that are a package name with an optional extras list
    and an optional version specifier, and the names are passed to pip AS ARGUMENTS — the file
    itself is never handed over with ``-r``. That is the whole point of parsing it here: a
    ``requirements.txt`` written by a model is untrusted input, and ``-r`` makes every line of
    it a potential pip flag. ``--index-url``, ``-e .``, ``git+ssh://…`` and a bare path are all
    ordinary lines of a requirements file and every one of them is refused, by name, in the
    report.

PYTHON ONLY, ON PURPOSE
    Node's resolution walks up from the importing file and ``NODE_PATH`` does not apply to ESM,
    which is what the Node probe is written in, so there is no equivalent of a single mounted
    directory here. A Node project therefore gets the same honest ceiling it got before, and
    the report says that is why.
"""

from __future__ import annotations

import re
import subprocess
import threading
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from mirag.core.text import sha256_hex
from mirag.projects.model import Project

MAX_PACKAGES = 30
"""More than any project of `MAX_FILES` files legitimately needs, and a bound on how long a
cold install can take before the run's own clock has to care about it."""

MAX_ARGUMENT = 120
"""Characters of one requirement. A name with a 4 KiB "version" is not a version."""

INSTALL_TIMEOUT_S = 300
"""A cold install of a web framework and a test client, measured, is well under a minute on a
warm index and a few minutes on a cold one. It is bounded rather than generous: the run's own
deadline is what people actually wait on."""

DOCKER_CLI_TIMEOUT_S = 15
"""For the short calls — creating a volume, asking whether one is already filled. Separate
from the install's own clock, which bounds a download."""

VOLUME_PREFIX = "mirag-deps-"
"""Volumes are named after the requirements, so two projects asking for the same versions
share one and the second installs nothing. The prefix is what makes them findable:
``docker volume ls --filter label=mirag.deps=1``."""

LABEL = "mirag.deps=1"
FINGERPRINT_LABEL = "mirag.requirements"

MARKER = "/deps/.mirag-installed"
"""Written LAST, by the sealing container, and only after pip exited zero. Its presence is
what makes a volume reusable — a half-filled one has no marker and is never mistaken for a
finished install."""

SEAL = (
    "import os, pathlib, time\n"
    "root = pathlib.Path('/deps')\n"
    # pip runs as root in the install container and the tests run as uid 10001. Without this,
    # a package whose files land 0600 is invisible to the process that has to import it, and
    # the failure reads as "no module named X" rather than as a permission problem.
    "for path in root.rglob('*'):\n"
    "    try:\n"
    "        os.chmod(path, 0o755 if path.is_dir() else 0o644)\n"
    "    except OSError:\n"
    "        pass\n"
    "os.chmod(root, 0o755)\n"
    "pathlib.Path('" + MARKER + "').write_text(str(time.time()))\n"
)

CHECK = (
    "import os, sys\n"
    "sys.exit(0 if os.path.isfile('" + MARKER + "') else 1)\n"
)

# PEP 508 reduced to what a generated `requirements.txt` legitimately holds. Anything this
# does not match is refused and named in the report; it is never silently dropped.
NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
EXTRAS = r"\[[A-Za-z0-9](?:[A-Za-z0-9,._-]*[A-Za-z0-9])?\]"
OPERATOR = r"(?:===|==|!=|~=|>=|<=|>|<)"
VERSION = r"[A-Za-z0-9*][A-Za-z0-9*.+!_-]*"
REQUIREMENT = re.compile(
    rf"\A(?P<name>{NAME})(?P<extras>{EXTRAS})?"
    rf"(?P<specifier>{OPERATOR}{VERSION}(?:\s*,\s*{OPERATOR}{VERSION})*)?\Z"
)

# Import roots that do not follow from the distribution name. Only the ones a generated
# backend project actually reaches for; the rule below covers everything else.
IMPORT_ROOTS = {
    "beautifulsoup4": "bs4", "pillow": "PIL", "pyyaml": "yaml", "python-dotenv": "dotenv",
    "python-multipart": "multipart", "psycopg2-binary": "psycopg2", "attrs": "attr",
    "python-jose": "jose", "pyjwt": "jwt", "msgpack-python": "msgpack",
    "typing-extensions": "typing_extensions", "sqlalchemy": "sqlalchemy",
}


@dataclass(frozen=True, slots=True)
class Requirement:
    """One accepted line of ``requirements.txt``, taken apart."""

    name: str
    extras: str = ""
    specifier: str = ""

    @property
    def argument(self) -> str:
        """Exactly what is handed to pip, as ONE argv element."""
        return f"{self.name}{self.extras}{self.specifier}"

    @property
    def module(self) -> str:
        """The import root this distribution is expected to provide.

        A guess, and it only has to be good enough to match what the analyzer reported
        missing: the authority on whether the install worked is the analyzer asking the
        interpreter again, never this property.
        """
        key = self.name.lower()
        return IMPORT_ROOTS.get(key, key.replace("-", "_"))


@dataclass(frozen=True, slots=True)
class InstallReport:
    """What the install did. Never raises upwards; failure is a value like any other."""

    ok: bool
    detail: str
    volume: str = ""
    """The Docker volume the packages are in. Empty when nothing was installed.

    A volume NAME and not a path, deliberately: there is no host directory to hand anybody,
    which is the property this module exists to have."""
    installed: tuple[str, ...] = ()
    refused: tuple[str, ...] = ()
    """Lines of ``requirements.txt`` that are not a plain pinned package, quoted back."""
    log: str = ""
    reused: bool = False
    """The volume already existed, sealed, from an earlier run. Nothing was downloaded."""

    def as_record(self) -> dict[str, object]:
        return {"ok": self.ok, "detail": self.detail, "installed": list(self.installed),
                "refused": list(self.refused), "reused": self.reused, "volume": self.volume}


def parse_requirements(text: str) -> tuple[tuple[Requirement, ...], tuple[str, ...]]:
    """``(accepted, refused)``. The refused ones are returned VERBATIM so a person can see them.

    An environment marker (``; python_version >= "3.10"``) is dropped rather than refused: it
    is ordinary, and installing a package this interpreter would not have needed is a wasted
    download, not a risk. Everything else that is not a plain name-and-version is refused.
    """
    accepted: list[Requirement] = []
    refused: list[str] = []
    seen: set[str] = set()
    for raw in (text or "").splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        candidate = line.split(";")[0].strip()  # the marker, dropped
        if len(candidate) > MAX_ARGUMENT:
            refused.append(raw.strip()[:MAX_ARGUMENT])
            continue
        found = REQUIREMENT.match(candidate.replace(" ", ""))
        if found is None:
            # -r, -e, --index-url, git+…, ./local, http://…, name @ url: every one of these is
            # a legal requirements.txt line and none of them may reach pip from here.
            refused.append(raw.strip())
            continue
        requirement = Requirement(found["name"], found["extras"] or "", found["specifier"] or "")
        if requirement.name.lower() in seen:
            continue
        seen.add(requirement.name.lower())
        accepted.append(requirement)
    return tuple(accepted[:MAX_PACKAGES]), tuple(refused)


def requirements_of(project: Project) -> tuple[tuple[Requirement, ...], tuple[str, ...]]:
    file = project.get("requirements.txt")
    return parse_requirements(file.text) if file is not None else ((), ())


def fingerprint(requirements: Iterable[Requirement]) -> str:
    """The volume's name. Same requirements, same volume — across runs and processes."""
    return sha256_hex("\n".join(sorted(r.argument for r in requirements)).encode("utf-8"))[:16]


def volume_for(requirements: Iterable[Requirement]) -> str:
    return VOLUME_PREFIX + fingerprint(requirements)


@runtime_checkable
class DependencyInstaller(Protocol):
    """What certification needs from whoever can install: a switch and one bounded call."""

    enabled: bool

    def install(self, project: Project) -> InstallReport: ...


OFF_REASON = "dependency installation is switched off (MIRAG_INSTALL_DEPENDENCIES=0)"

NO_SANDBOX_REASON = (
    "dependencies are only ever installed inside the execution sandbox, and this deployment "
    "runs probes on the host (MIRAG_EXECUTION_BACKEND=subprocess). Set "
    "MIRAG_EXECUTION_BACKEND=docker and build the image once with `make runner-image`."
)
"""The whole reason the host installer was removed.

Installing a generated project's dependencies means running third-party code chosen by a
model. There is exactly one place that belongs, and it is the disposable container that was
already going to run that project's tests. With no such container there is no install, and
the project keeps the ceiling it had — which is a true statement about this machine."""


class NullInstaller:
    """The installer of a deployment that cannot, or has not opted in. Says which, installs
    nothing.

    It exists so certification can call ``self._installer.install(...)`` unconditionally
    instead of guarding every call site with ``is not None`` — the branch that used to decide
    whether a project could run at all should not also be the branch that decides whether the
    attribute is set.
    """

    def __init__(self, reason: str = OFF_REASON) -> None:
        self.enabled = False
        self.reason = reason

    def install(self, project: Project) -> InstallReport:
        del project
        return InstallReport(ok=False, detail=self.reason)


Execute = Callable[[Sequence[str], int], "subprocess.CompletedProcess[str] | str"]
"""``(argv, timeout seconds) -> the finished process, or a string saying why there is none``.

Injected so the decisions in this file — which volume, when to reuse, what to do with a
non-zero exit — are testable without a Docker daemon. The default runs the argv."""


def run_argv(argv: Sequence[str], timeout_s: int) -> subprocess.CompletedProcess[str] | str:
    """The default :data:`Execute`. Every failure to START is a sentence, not an exception."""
    try:
        return subprocess.run(list(argv), capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return f"it did not finish in {timeout_s}s"
    except FileNotFoundError:
        return "the 'docker' command is not installed on this machine"
    except OSError as exc:
        return f"it could not be started: {exc}"


class DockerInstaller:
    """Installs a project's declared packages into a Docker volume, for the sandbox to mount.

    The volume name travels back in :attr:`InstallReport.volume` and is handed to the runner
    for that one call. Nothing lands on the host, nothing lands in this checkout, and nothing
    lands in the interpreter running Mirag.
    """

    def __init__(
        self,
        image: str = "mirag-runner:latest",
        timeout_s: int = INSTALL_TIMEOUT_S,
        enabled: bool = False,
        docker_timeout_s: int = DOCKER_CLI_TIMEOUT_S,
        memory: str = "1g",
        cpus: str = "2.0",
        pids_limit: int = 256,
        execute: Execute | None = None,
    ) -> None:
        self.image = image
        self.timeout_s = timeout_s
        self.enabled = enabled
        self._docker_timeout_s = docker_timeout_s
        self._memory = memory
        self._cpus = cpus
        self._pids_limit = pids_limit
        self._execute = execute or run_argv
        self._locks: dict[str, threading.Lock] = {}
        self._registry = threading.Lock()

    # ── the argv of each container ───────────────────────────────────────────

    def create_argv(self, volume: str, mark: str) -> list[str]:
        """``docker volume create`` is idempotent: it answers the name either way.

        The labels are not decoration. They are how an operator finds these later —
        ``docker volume ls --filter label=mirag.deps=1`` — and how `make clean-deps` knows
        which volumes are ours to remove. They are also why this runs FIRST: on an existing
        volume this command adds nothing, and any `docker run` that mounts a missing volume
        creates it unlabelled.
        """
        return ["docker", "volume", "create", "--label", LABEL,
                "--label", f"{FINGERPRINT_LABEL}={mark}", volume]

    def check_argv(self, volume: str) -> list[str]:
        """Is this volume already sealed? Read-only, no network, no project code."""
        return [
            "docker", "run", "--rm", "--network", "none",
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL", "--read-only",
            "--pids-limit", "64", "--memory", "256m",
            "-v", f"{volume}:/deps:ro", "-e", "HOME=/tmp",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            self.image, "python3", "-c", CHECK,
        ]

    def install_argv(self, volume: str, arguments: Sequence[str]) -> list[str]:
        """The ONE container in this code base that has a network.

        It holds no project code, which is why giving it one is safe: there is nothing in it
        that a generated test could use to reach out.

        ``--user 0:0`` overrides the image's own unprivileged user, and it has to: a fresh
        Docker volume is created root-owned, so pip writing into it as uid 10001 fails with
        ``PermissionError: /deps/six.py`` — measured, not guessed. Root here is bounded by a
        disposable container with every capability dropped and no project code in it, and the
        sealing container then makes the tree readable by the uid the tests really run as.
        """
        return [
            "docker", "run", "--rm", "--init",
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
            "--pids-limit", str(self._pids_limit),
            "--memory", self._memory, "--cpus", self._cpus,
            "--user", "0:0",
            "-e", "HOME=/tmp", "-e", "PIP_NO_INPUT=1",
            "-v", f"{volume}:/deps", "-w", "/tmp",
            self.image, "python3", "-m", "pip", "install",
            "--no-input", "--disable-pip-version-check", "--no-warn-script-location",
            "--target", "/deps", *arguments,
        ]

    def seal_argv(self, volume: str) -> list[str]:
        """Make it readable by the test user and write the marker. No network, and no shell.

        As root, for the same reason the install is: it is chmod-ing files root wrote. It is
        the last thing that touches the volume, and everything after it mounts read-only.
        """
        return [
            "docker", "run", "--rm", "--network", "none",
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
            "--pids-limit", "64", "--memory", "256m",
            "--user", "0:0",
            "-v", f"{volume}:/deps", "-e", "HOME=/tmp",
            self.image, "python3", "-c", SEAL,
        ]

    # ── the call certification makes ─────────────────────────────────────────

    def install(self, project: Project) -> InstallReport:
        if not self.enabled:
            return InstallReport(ok=False, detail=OFF_REASON)
        requirements, refused = requirements_of(project)
        if not requirements:
            return InstallReport(
                ok=False,
                detail=("requirements.txt declares nothing this can install"
                        if refused else "the project declares no requirements.txt"),
                refused=refused)

        mark = fingerprint(requirements)
        volume = VOLUME_PREFIX + mark
        arguments = [r.argument for r in requirements]

        # One lock per fingerprint, so two runs of the same project in this process do not
        # have two pips writing into one volume. Across processes the marker is still only
        # written on success, so a loser installs again rather than reading a half-filled one.
        with self._lock_for(volume):
            # Created BEFORE it is inspected, and the order matters. `docker run -v name:/…`
            # auto-creates a missing volume — silently, and WITHOUT labels — so asking "is it
            # sealed?" first brings the volume into existence unlabelled, and the `create`
            # that follows is a no-op on something that already exists. The result is a
            # working install in a volume no `--filter label=…` can find, which is the same
            # as one that cannot be cleaned up. Measured on a real run; the unit tests could
            # not see it, because a Docker double does not auto-create anything.
            created = self._execute(self.create_argv(volume, mark), self._docker_timeout_s)
            if isinstance(created, str):
                return InstallReport(False, f"the volume could not be created: {created}",
                                     refused=refused)
            if created.returncode != 0:
                return InstallReport(False, "the volume could not be created",
                                     refused=refused, log=_output(created))

            if self._sealed(volume):
                return InstallReport(True, f"already installed: {', '.join(arguments)}",
                                     volume, tuple(arguments), refused, reused=True)

            installed = self._execute(self.install_argv(volume, arguments), self.timeout_s)
            if isinstance(installed, str):
                return InstallReport(False, f"the install did not run: {installed}",
                                     refused=refused)
            log = _output(installed)
            if installed.returncode != 0:
                return InstallReport(False, f"the install failed (exit {installed.returncode})",
                                     refused=refused, log=log)

            sealed = self._execute(self.seal_argv(volume), self._docker_timeout_s)
            if isinstance(sealed, str) or sealed.returncode != 0:
                # pip succeeded and the packages ARE in the volume, but without the marker
                # the next run will install them again, and without the chmod the tests may
                # not be able to read them. Reporting success here would hide both.
                detail = sealed if isinstance(sealed, str) else _output(sealed)
                return InstallReport(False, f"the packages could not be sealed: {detail[:200]}",
                                     refused=refused, log=log)

            return InstallReport(True, f"installed {len(arguments)}: {', '.join(arguments)}",
                                 volume, tuple(arguments), refused, log)

    def _sealed(self, volume: str) -> bool:
        """Has this volume a finished install in it? A failure to ask is a "no"."""
        answered = self._execute(self.check_argv(volume), self._docker_timeout_s)
        return not isinstance(answered, str) and answered.returncode == 0

    def _lock_for(self, volume: str) -> threading.Lock:
        with self._registry:
            return self._locks.setdefault(volume, threading.Lock())


def _output(completed: subprocess.CompletedProcess[str]) -> str:
    return ((completed.stdout or "") + (completed.stderr or "")).strip()[-4000:]


__all__ = [
    "FINGERPRINT_LABEL",
    "INSTALL_TIMEOUT_S",
    "LABEL",
    "MARKER",
    "NO_SANDBOX_REASON",
    "OFF_REASON",
    "VOLUME_PREFIX",
    "DependencyInstaller",
    "DockerInstaller",
    "Execute",
    "InstallReport",
    "NullInstaller",
    "Requirement",
    "fingerprint",
    "parse_requirements",
    "requirements_of",
    "run_argv",
    "volume_for",
]

# `make clean-deps` is these two commands, and they are here so the label the Makefile
# filters on cannot drift from the label `create_argv` writes:
#   docker volume ls --filter label=mirag.deps=1 -q | xargs docker volume rm
