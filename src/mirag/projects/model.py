"""A whole project as ONE object: the artifact everything else comes from.

WHAT IT GUARANTEES AND WHAT IT DOES NOT
    YES: no path escapes the project, the tree is immutable once sealed, and hashes are
    computed ONCE over the exact bytes.
    NO: it does not judge whether the code is good, does not run it and does not decide
    whether it is verified. That belongs to certification, and execution gives the verdict.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from mirag.core.errors import ForbiddenDestinationError, ForbiddenPathError, SealedProjectError
from mirag.core.text import sha256_hex
from mirag.paths import PACKAGE_ROOT, source_checkout_root

# Caps. They are not aesthetics: a model gone wild must not fill the disk or build a ZIP
# nobody can open.
MAX_FILES = 40
MAX_DEPTH = 6
MAX_PATH = 120
MAX_FILE_BYTES = 60 * 1024
MAX_TOTAL_BYTES = 400 * 1024

# An ALLOW-list of segments, not a deny-list: what is known is accepted and the rest is
# rejected. Enumerating the forbidden always leaves something out.
SEGMENT = re.compile(r"\A[A-Za-z0-9_][A-Za-z0-9._-]{0,63}\Z")
ALLOWED_HIDDEN = frozenset({".gitignore", ".env.example", ".dockerignore", ".editorconfig"})
FORBIDDEN_SEGMENTS = frozenset({"__pycache__", ".git", ".env", "node_modules", ".venv", "venv", ".DS_Store"})
EXTENSIONS = frozenset({".py", ".js", ".ts", ".json", ".md", ".txt", ".sql", ".yml", ".yaml",
                        ".toml", ".cfg", ".ini", ".html", ".css", ".example", ".gitignore", ".sh"})
EXTENSIONLESS = frozenset({"Dockerfile", "Makefile", "LICENSE", "NOTICE", "Procfile",
                           "README", "CHANGELOG", "AUTHORS", "VERSION", "CODEOWNERS"})
"""Ordinary files of a delivered project that simply have no extension.

The allow-list was written against the books demo, whose fourteen files all end in `.py` or
`.md`, so nothing ever hit this. A `docs` group that plans a `Dockerfile` and a `LICENSE` —
both normal, neither in the demo — had them rejected one by one, and the group reported an
error for files it had written correctly."""
FILE_KINDS = ("code", "test", "entrypoint", "config", "doc")


def safe_path(path: object) -> str:
    """The normalised path, or :class:`ForbiddenPathError`. **The only place a path is born.**

    Nothing that comes from the model reaches the disk without passing through here. It
    rejects absolute paths, ``..``, ``~``, NUL, Windows drives, empty segments and names that
    must never enter a generated project (``__pycache__``, ``.git``, ``.env``).
    """
    if not isinstance(path, str) or not path.strip():
        raise ForbiddenPathError(f"empty path or not text: {path!r}")
    raw = path.strip().replace("\\", "/")
    if "\x00" in raw:
        raise ForbiddenPathError("the path contains a NUL")
    if raw.startswith(("/", "~")) or re.match(r"\A[A-Za-z]:", raw):
        raise ForbiddenPathError(f"absolute path: {path!r}")
    if len(raw) > MAX_PATH:
        raise ForbiddenPathError(f"path of {len(raw)} characters, the cap is {MAX_PATH}")
    parts = list(PurePosixPath(raw).parts)
    if not parts:
        raise ForbiddenPathError(f"path without segments: {path!r}")
    if len(parts) > MAX_DEPTH:
        raise ForbiddenPathError(f"{len(parts)} levels, the cap is {MAX_DEPTH}")
    for part in parts:
        if part in ("..", ".", ""):
            raise ForbiddenPathError(f"segment not allowed {part!r} in {path!r}")
        if part in FORBIDDEN_SEGMENTS:
            raise ForbiddenPathError(f"{part!r} never enters a generated project")
        if part.startswith(".") and part not in ALLOWED_HIDDEN:
            raise ForbiddenPathError(f"hidden file not allowed: {part!r}")
        if part not in ALLOWED_HIDDEN and not SEGMENT.match(part):
            raise ForbiddenPathError(f"segment with forbidden characters: {part!r}")
    last = parts[-1]
    if (PurePosixPath(last).suffix.lower() not in EXTENSIONS
            and last not in ALLOWED_HIDDEN and last not in EXTENSIONLESS):
        raise ForbiddenPathError(f"extension not allowed in {last!r}")
    return "/".join(parts)


def safe_name(name: object) -> str:
    """A project name usable as a folder and as a file name.

    Sanitised here and checked again before writing it into an HTTP header: a ``\\r\\n`` in
    the name would split ``Content-Disposition`` in two.
    """
    clean = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode()
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", clean).strip("-._").lower()
    # Stripped again AFTER the cut: truncating can leave a trailing '.', and Windows silently
    # drops it, so the folder in the ZIP and the folder on disk would stop being the same.
    clean = re.sub(r"-{2,}", "-", clean)[:48].rstrip("-._")
    return clean or "project"


def mirag_root() -> Path:
    """Mirag's own tree: the source checkout when running from one, else the installed package."""
    return source_checkout_root() or PACKAGE_ROOT


@dataclass(frozen=True, slots=True)
class ProjectFile:
    path: str
    data: bytes
    kind: str = "code"
    """``code`` | ``test`` | ``entrypoint`` | ``config`` | ``doc``."""
    purpose: str = ""
    exports: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    group: str = ""

    @property
    def sha256(self) -> str:
        return sha256_hex(self.data)

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def lines(self) -> int:
        return self.data.count(b"\n") + (0 if self.data.endswith(b"\n") else 1)

    @property
    def text(self) -> str:
        return self.data.decode("utf-8", "replace")

    @property
    def module(self) -> str:
        """``"app/books/repository.py"`` -> ``"app.books.repository"``. Empty if not Python."""
        return self.path[:-3].replace("/", ".") if self.path.endswith(".py") else ""


class Project:
    """The artifact. Mutable while being generated; sealed before being verified."""

    def __init__(self, name: str, spec: Mapping[str, Any] | None = None) -> None:
        self.name = safe_name(name)
        self.spec = dict(spec or {})
        self._files: dict[str, ProjectFile] = {}
        self._sealed = False

    @classmethod
    def from_mapping(cls, name: str, files: Mapping[str, str | bytes], spec: Mapping[str, Any] | None = None) -> Project:
        project = cls(name, spec)
        for path, content in files.items():
            project.add(path, content)
        return project

    # ── building ─────────────────────────────────────────────────────────────

    @property
    def sealed(self) -> bool:
        return self._sealed

    def add(self, path: str, content: str | bytes, *, kind: str = "code", purpose: str = "",
            exports: tuple[str, ...] = (), depends_on: tuple[str, ...] = (), group: str = "") -> ProjectFile:
        """Add or replace a file. The path always goes through :func:`safe_path`."""
        if self._sealed:
            raise SealedProjectError("the project is sealed: a repair creates a new one")
        clean = safe_path(path)
        data = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        if len(data) > MAX_FILE_BYTES:
            raise ForbiddenPathError(f"{clean}: {len(data)} bytes, the cap is {MAX_FILE_BYTES}")
        updated = dict(self._files)
        updated[clean] = ProjectFile(clean, data, kind, purpose, tuple(exports), tuple(depends_on), group)
        if len(updated) > MAX_FILES:
            raise ForbiddenPathError(f"{len(updated)} files, the cap is {MAX_FILES}")
        total = sum(f.size for f in updated.values())
        if total > MAX_TOTAL_BYTES:
            raise ForbiddenPathError(f"{total} bytes in total, the cap is {MAX_TOTAL_BYTES}")
        self._files = updated
        return updated[clean]

    def seal(self) -> Project:
        """From here on the tree does not change. What gets verified is what gets packaged."""
        self._sealed = True
        return self

    def copy(self) -> Project:
        """An unsealed copy, for repairs."""
        clone = Project(self.name, self.spec)
        clone._files = dict(self._files)
        return clone

    # ── reading ──────────────────────────────────────────────────────────────

    def get(self, path: str) -> ProjectFile | None:
        """The file, or ``None``. **Reading never raises.**

        Strict when writing, tolerant when reading: a path that cannot exist is simply a path
        that is not there. When this raised, a dependency declared badly by the model
        (``depends_on: ["app/books/api"]``, without extension) blew the whole generation up.
        """
        try:
            return self._files.get(safe_path(path))
        except ForbiddenPathError:
            return None

    def files(self, kind: str | None = None) -> tuple[ProjectFile, ...]:
        return tuple(f for f in sorted(self._files.values(), key=lambda f: f.path) if kind is None or f.kind == kind)

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(self._files))

    def as_text_mapping(self) -> dict[str, str]:
        """``{path: text}``: exactly what the code runner consumes."""
        return {f.path: f.text for f in self.files()}

    def tree(self) -> dict[str, Any]:
        """The implicit directories, derived from the paths. For display."""
        nodes: dict[str, Any] = {}
        for path in self.paths():
            current = nodes
            parts = path.split("/")
            for part in parts[:-1]:
                current = current.setdefault(part + "/", {})
            current[parts[-1]] = None
        return nodes

    @property
    def totals(self) -> dict[str, int]:
        files = self.files()
        directories = {"/".join(f.path.split("/")[:-1]) for f in files} - {""}
        return {"files": len(files), "directories": len(directories),
                "lines": sum(f.lines for f in files), "bytes": sum(f.size for f in files)}

    # ── to disk ──────────────────────────────────────────────────────────────

    def materialize(self, destination: Path, protected_root: Path | None = None,
                    allowed_area: Path | None = None) -> Path:
        """Write the tree. Never on top of Mirag.

        Exactly two places are allowed: anywhere OUTSIDE the protected roots (a temporary
        folder, for example) and ``allowed_area`` (the artifacts area, where each project has
        its own folder with an opaque id). A generated project cannot write over the agent.

        Mirag's own tree (:func:`mirag_root`) is ALWAYS protected; ``protected_root`` adds one
        more. When the guard depended on the caller passing it, the only caller did not, and
        "never on top of Mirag" had quietly become "wherever you are told".
        """
        destination = Path(destination).resolve()
        allowed = allowed_area is not None and destination.is_relative_to(Path(allowed_area).resolve())
        roots = [mirag_root(), *([Path(protected_root)] if protected_root is not None else [])]
        for root in roots:
            protected = root.resolve()
            inside = destination == protected or protected in destination.parents
            if inside and not allowed:
                raise ForbiddenDestinationError(f"a project is never written inside Mirag: {destination}")
        destination.mkdir(parents=True, exist_ok=True)
        for file in self.files():
            target = (destination / file.path).resolve()
            if not target.is_relative_to(destination):  # the second belt, as in the runner
                raise ForbiddenPathError(f"escapes the destination: {file.path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(file.data)  # bytes, never write_text: it translates newlines
        return destination
