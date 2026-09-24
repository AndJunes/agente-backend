"""Run a command against a delivered project and report what it prints, as it prints it.

The certifier runs a project's TESTS, once, through a probe Mirag wrote. Nothing ever STARTED
the project: a generated server was reported verified or not without anybody having watched it
come up, and there was nowhere to type `npm install` or `node src/server.js` and see what
happens. This is that place.

WHAT IT IS, AND WHAT IT IS NOT

It is a terminal restricted to a short list of programs, working in a copy of ONE project. It is
not a sandbox: whatever the command does, it does as this process's user, with this machine's
network. That is the same trust the test probes already extend to generated code, and the
reason it is behind its own switch (`MIRAG_CONSOLE`) and the shared token rather than open
whenever execution is.

What keeps it from being more than it is:

    the allow-list    a program name, checked as the resolved executable, never a shell string
    no shell          the arguments are a list. `&&`, `|` and `>` are refused with a sentence
                      instead of being passed to a program that would misread them
    the environment   the same stripped one the probes get: no API key, no seed
    the folder        a copy per artifact, so what a command writes never touches the artifact
    the ceilings      wall clock, total output, and the client leaving all stop the process —
                      and stopping means the whole TREE, because `npm start` is `node` under
                      `npm`, and killing only the parent leaves the server holding its port
"""

from __future__ import annotations

import os
import queue
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from mirag.execution.backend import write_workspace
from mirag.execution.interpreters import InterpreterRegistry
from mirag.execution.runner import child_environment

ALLOWED: tuple[str, ...] = ("node", "npm", "npx", "python3", "python", "pytest", "curl")
"""What may be typed first. No `pip`: it installs into whichever interpreter answers, and for
`python3` that can be the very environment this agent runs in."""

MAX_COMMAND_CHARS = 500
MAX_LINE_BYTES = 8_192
MAX_OUTPUT_BYTES = 1_000_000
"""A build that prints a megabyte is a build nobody is reading, and the browser holds all of it."""

WORKSPACE_TTL_S = 24 * 3600

SHELL_OPERATORS = frozenset({"&&", "||", "|", ";", ">", ">>", "<", "&", "2>&1"})

# What npm and node-gyp look for on Windows and the probe environment leaves out.
_EXTRA_ENVIRONMENT = ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)", "ProgramData",
                      "ALLUSERSPROFILE", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE")

Emit = Callable[[dict[str, Any]], None]


def console_environment() -> dict[str, str]:
    """The probe environment, plus what a package manager needs to find its cache.

    Still no credential: this is `child_environment()` and a fixed list of OS locations. The
    rest only quiets what a person watching does not need — colour codes, the update banner,
    the funding and audit chatter that npm appends to every install.
    """
    env = child_environment()
    env.update({name: os.environ[name] for name in _EXTRA_ENVIRONMENT if name in os.environ})
    env.update({"NO_COLOR": "1", "FORCE_COLOR": "0", "CI": "1", "npm_config_fund": "false",
                "npm_config_audit": "false", "npm_config_update_notifier": "false",
                "npm_config_progress": "false", "npm_config_loglevel": "warn"})
    return env


class ProjectConsole:
    def __init__(self, folder: Path, enabled: bool = False, timeout_s: int = 600,
                 interpreters: InterpreterRegistry | None = None) -> None:
        self.enabled = enabled
        self._folder = Path(folder).resolve()
        self._timeout_s = timeout_s
        self._interpreters = interpreters or InterpreterRegistry(allowed=ALLOWED)

    # ── the folder ───────────────────────────────────────────────────────────────

    def sweep(self, now: float | None = None) -> None:
        """Drop copies nobody has touched for a day. `node_modules` is most of the disk."""
        if not self._folder.is_dir():
            return
        cutoff = (now if now is not None else time.time()) - WORKSPACE_TTL_S
        for child in self._folder.iterdir():
            try:
                if child.is_dir() and child.stat().st_mtime < cutoff:
                    shutil.rmtree(child, ignore_errors=True)
            except OSError:
                continue

    def workspace(self, artifact_id: str, files: Mapping[str, str]) -> Path:
        """The project's own folder, made once and then KEPT.

        Kept on purpose: `npm install` in one command has to still be there for `npm start` in
        the next, which is the entire point of having a console instead of a one-shot runner.
        """
        root = (self._folder / artifact_id).resolve()
        if not root.is_relative_to(self._folder):
            raise ValueError("the artifact id is not a folder name")
        if not root.exists():
            root.mkdir(parents=True)
            if write_workspace(files, root) is not None:
                shutil.rmtree(root, ignore_errors=True)
                raise ValueError("a file in the project points outside its own folder")
        else:
            os.utime(root)  # in use: the sweep counts from the last command, not the first
        return root

    # ── the command ──────────────────────────────────────────────────────────────

    def parse(self, command: str) -> tuple[list[str], str]:
        """``(argv, "")`` when the command may run, ``([], reason)`` when it may not."""
        text = (command or "").strip()
        if not text:
            return [], "the command is empty"
        if len(text) > MAX_COMMAND_CHARS:
            return [], f"the command is longer than {MAX_COMMAND_CHARS} characters"
        if sys.platform == "win32":
            # POSIX quoting reads a backslash as an escape, so `node src\server.js` would arrive
            # as `srcserver.js`. Every program allowed here takes forward slashes on Windows.
            text = text.replace("\\", "/")
        try:
            parts = shlex.split(text)
        except ValueError as error:
            return [], f"malformed command ({error})"
        if not parts:
            return [], "the command is empty"
        if any(part in SHELL_OPERATORS for part in parts):
            return [], ("there is no shell here, so `&&`, `|`, `;` and `>` mean nothing: run one "
                        "command at a time (a server can stay running while you start another)")
        executable = self._interpreters.resolve(parts[0])
        if executable is None:
            return [], f"only {self._interpreters.describe()} may run here. You asked: {parts[0]!r}"
        if parts[0] in ("npm", "npx") and any(a in ("-g", "--global") for a in parts[1:]):
            return [], "a global install would change this machine, not the project"
        if parts[0] in ("python", "python3") and "pip" in parts[1:3]:
            return [], "pip would install into the environment this agent itself runs in"
        return [executable, *parts[1:]], ""

    def run(self, artifact_id: str, files: Mapping[str, str], command: str, emit: Emit,
            cancelled: threading.Event) -> None:
        """Run ``command`` and emit events until it ends.

        Events are ``start``, then ``stdout`` / ``stderr`` lines, then exactly one ``exit`` —
        or a single ``error`` when the command was never started. Never raises for a bad
        command: a refusal is something to show, not something to crash on.
        """
        if not self.enabled:
            emit({"type": "error", "message": "the console is switched off (MIRAG_CONSOLE)"})
            return
        argv, reason = self.parse(command)
        if reason:
            emit({"type": "error", "message": reason})
            return
        try:
            root = self.workspace(artifact_id, files)
        except (ValueError, OSError) as error:
            emit({"type": "error", "message": f"could not prepare the project folder: {error}"})
            return

        popen: dict[str, Any] = {"cwd": root, "stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE,
                                 "stderr": subprocess.PIPE, "env": console_environment()}
        if sys.platform != "win32":
            popen["start_new_session"] = True  # its own group, so the whole tree can be stopped
        try:
            process = subprocess.Popen(argv, **popen)
        except OSError as error:
            emit({"type": "error", "message": f"{argv[0]} could not start: {error}"})
            return

        started = time.monotonic()
        emit({"type": "start", "command": command.strip()})
        lines: queue.Queue[tuple[str, str] | None] = queue.Queue()

        def pump(pipe: Any, kind: str) -> None:
            try:
                for raw in iter(lambda: pipe.readline(MAX_LINE_BYTES), b""):
                    lines.put((kind, raw.decode("utf-8", "replace").rstrip("\r\n")))
            finally:
                lines.put(None)

        readers = [threading.Thread(target=pump, args=(process.stdout, "stdout"), daemon=True),
                   threading.Thread(target=pump, args=(process.stderr, "stderr"), daemon=True)]
        for reader in readers:
            reader.start()

        reason_stopped = ""
        emitted = 0
        finished = 0
        deadline = started + self._timeout_s
        while finished < len(readers):
            idle = False
            try:
                item = lines.get(timeout=0.25)
            except queue.Empty:
                item, idle = None, True  # nothing yet: only the checks below run
            if not idle:
                if item is None:
                    finished += 1  # one pipe reached EOF
                else:
                    emitted += len(item[1]) + 1
                    emit({"type": item[0], "text": item[1]})
            if reason_stopped:
                continue  # already being stopped: keep draining what the pipes still hold
            if cancelled.is_set():
                reason_stopped = "stopped"
            elif time.monotonic() > deadline:
                reason_stopped = "timeout"
            elif emitted > MAX_OUTPUT_BYTES:
                reason_stopped = "output"
            if reason_stopped:
                _kill_tree(process)

        try:
            code = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _kill_tree(process)
            code = process.wait(timeout=5)
        emit({"type": "exit", "code": code, "ms": int((time.monotonic() - started) * 1000),
              "reason": reason_stopped})


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Stop the process AND everything it started.

    `Popen.kill()` reaches only the direct child. `npm start` is npm running node: kill npm and
    node keeps running with the port bound, and the next "start" fails with EADDRINUSE on a
    server nobody can see any more.
    """
    if process.poll() is not None:
        return
    try:
        # `sys.platform` and not `os.name`: it is the form a type checker narrows on, so `killpg`
        # is only looked up on the platforms that have it.
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True,
                           check=False, timeout=10)
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        process.kill()
