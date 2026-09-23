"""Runs a command inside a disposable, per-invocation Docker container instead of directly on
the host. Same contract as `CodeRunner` (`CodeExecutionBackend` in `backend.py`) — every
consumer (`SyntaxChecker`, `ProjectCertifier`, the `run_code` tool) is unaware which backend it
is talking to.

`CodeRunner.child_environment()` exists because a host subprocess still shares the host's
filesystem, users and network, and has to be stripped down to a safe allow-list. A container
starts with none of that: no host env var reaches it unless this file passes one with `-e`, and
only one ever is. That is the actual security upgrade this backend buys, not merely relocating
where the same subprocess runs.
"""

from __future__ import annotations

import contextlib
import subprocess
import tempfile
import threading
import uuid
from collections.abc import Mapping
from pathlib import Path

from mirag.execution.backend import resolve_command, write_workspace
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.verdict import MAX_OUTPUT, ExecutionResult

IMAGE_INTERPRETERS: tuple[str, ...] = ("python3", "python", "pytest")
"""No "node": `docker/runner.Dockerfile` deliberately does not install it. The whole
certification pipeline (structure validation, the tests probe, the CRUD probe,
`DependencyAnalyzer`) is Python-only in practice already; a stray `.js` file's
`SyntaxChecker.check()` reports NOT EXECUTED under this backend — the same failure mode as
running on any host with no `node` on PATH."""

DISABLED_REASON = (
    "execution is switched off (MIRAG_EXECUTION=off). The code and its tests are delivered "
    "without running them; running them is the QA agent's job. This is neither a pass nor a "
    "fail: nothing was observed."
)


def _image_interpreters() -> InterpreterRegistry:
    """Declared, not probed: spawning a container just to ask "is pytest on PATH" is wasted
    work for an image whose exact contents were pinned at build time."""
    return InterpreterRegistry(
        allowed=IMAGE_INTERPRETERS, which=lambda name: name, probe=lambda path, args: True
    )


def _make_world_writable(root: Path) -> None:
    """The container runs as uid 10001, the host temp dir is owned by whoever runs Mirag: on
    Linux that uid cannot create files under `root` (e.g. `.pytest_cache/`) without this. A
    no-op on Windows — `Path.chmod` there only toggles the read-only attribute — which is fine,
    Windows has no such ownership mismatch for a Docker Desktop bind mount."""
    with contextlib.suppress(OSError):
        root.chmod(0o777)


class DockerCodeRunner:
    """A `CodeExecutionBackend`: one `docker run --rm` per call, hardened, cleaned up either
    way it ends."""

    def __init__(self, image: str = "mirag-runner:latest", timeout_s: int = 30,
                 max_output: int = MAX_OUTPUT, enabled: bool = True,
                 docker_timeout_s: int = 10, memory: str = "512m", cpus: str = "1.0",
                 pids_limit: int = 128) -> None:
        self.interpreters = _image_interpreters()
        self.image = image
        self.timeout_s = timeout_s
        self.max_output = max_output
        self.enabled = enabled
        self._docker_timeout_s = docker_timeout_s
        self._memory = memory
        self._cpus = cpus
        self._pids_limit = pids_limit
        self._image_ready: bool | None = None
        self._lock = threading.Lock()

    def image_available(self) -> bool:
        """Checked once, then cached — the same lazy-then-cached pattern
        `InterpreterRegistry.resolve` already uses, for the same reason: the image does not
        change between calls, so asking Docker about it on every one is wasted work."""
        with self._lock:
            if self._image_ready is None:
                self._image_ready = self._inspect_image()
            return self._image_ready

    def _inspect_image(self) -> bool:
        try:
            completed = subprocess.run(
                ["docker", "image", "inspect", self.image],
                capture_output=True, timeout=self._docker_timeout_s, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return completed.returncode == 0

    def run(self, files: Mapping[str, str], command: str) -> ExecutionResult:
        if not self.enabled:  # before touching the disk at all
            return ExecutionResult.not_executed(DISABLED_REASON)
        if not files:
            return ExecutionResult.not_executed("no file was given")
        resolved = resolve_command(command, self.interpreters)
        if isinstance(resolved, ExecutionResult):
            return resolved
        executable, parts = resolved
        if not self.image_available():
            return ExecutionResult.not_executed(
                f"the Docker runner image {self.image!r} was not found. Build it once with "
                "'make runner-image' (from agente-backend), then try again."
            )

        with tempfile.TemporaryDirectory(prefix="mirag-run-") as folder:
            root = Path(folder).resolve()
            error = write_workspace(files, root)
            if error is not None:
                return error
            _make_world_writable(root)

            name = f"mirag-run-{uuid.uuid4().hex}"
            argv = [
                "docker", "run", "--rm", "--init", "--name", name,
                "--network", "none",
                "--security-opt", "no-new-privileges",
                "--cap-drop", "ALL",
                "--read-only",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                "--pids-limit", str(self._pids_limit),
                "--memory", self._memory,
                "--cpus", self._cpus,
                "--user", "10001:10001",
                "-e", "HOME=/tmp",
                "-v", f"{root}:/workspace",
                "-w", "/workspace",
                self.image, executable, *parts[1:],
            ]
            try:
                completed = subprocess.run(
                    argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=self.timeout_s, check=False,
                )
            except subprocess.TimeoutExpired:
                return ExecutionResult.not_executed(
                    f"TIMEOUT, it did not finish in {self.timeout_s}s "
                    "(an infinite loop, or waiting on the network?)"
                )
            except FileNotFoundError:
                return ExecutionResult.not_executed(
                    "the 'docker' command is not installed on this machine"
                )
            finally:
                # `--rm` handles the ordinary exit. It does NOT guarantee the container is gone
                # when the `except TimeoutExpired` branch above kills the `docker run` CLI
                # process instead of letting it finish — the CLI dies, the container it started
                # may not. This runs on every path and is harmless if `--rm` already won.
                self._force_cleanup(name)

        output = ((completed.stdout or "") + (completed.stderr or "")).strip()
        return ExecutionResult.from_run(output, completed.returncode, self.max_output)

    def _force_cleanup(self, name: str) -> None:
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True, timeout=self._docker_timeout_s, check=False,
            )
