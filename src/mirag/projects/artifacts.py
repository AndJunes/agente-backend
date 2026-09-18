"""Where generated projects live and how they are identified without exposing the disk.

WHY A REGISTRY AND NOT A FOLDER
    The single-file output folder is emptied on every request and flattens paths. With a
    threaded server two requests would step on each other there: a download button pointing
    to it would deliver the project of the other tab.

THE PROPERTY THAT CANNOT BE RELAXED
    The id is **never concatenated to a Path**. It is validated against a 24-hex regex,
    looked up in an in-memory dictionary, and the artifact brings its own folder already
    built. If somebody ever writes ``folder / ident``, the hole the route allow-list closed
    comes back whole.

THE BYTES ARE SERVED FROM MEMORY
    ``Package.data`` is the source of the download. The ``.zip`` on disk is a convenience
    copy nobody reads to serve. So there is no window between "the gate inspected these
    bytes" and "the server wrote these other ones".
"""

from __future__ import annotations

import re
import secrets
import shutil
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mirag.projects.certification import Certificate
from mirag.projects.model import Project
from mirag.projects.packaging import MANIFEST_NAME, SECRETS, Manifest, Package

VALID_ID = re.compile(r"\A[0-9a-f]{24}\Z")
MAX_TEXT_BYTES = 2 * 1024 * 1024
"""Cap of the file text sent in the JSON. A normal generated project is tens of KB."""
TTL_S = 3600
MAX_ALIVE = 20
MEMORY_LIMIT = 64 * 1024 * 1024
ORPHAN_AGE_S = 24 * 3600


@dataclass(frozen=True, slots=True)
class Artifact:
    id: str
    name: str
    created: float
    folder: Path
    project: Project
    certificate: Certificate | None
    package: Package | None
    simulated: bool = False
    """Did the model's decision come from a script?"""

    @property
    def downloadable(self) -> bool:
        return self.package is not None and self.package.ok

    @property
    def status(self) -> str:
        return self.certificate.status.value if self.certificate is not None else "GENERATED"

    @property
    def download_url(self) -> str | None:
        """The page NEVER builds this URL: it uses it as is or draws no button."""
        return f"/api/v1/artifacts/{self.id}/download" if self.downloadable else None

    def _files(self, manifest: Manifest | None) -> list[dict[str, Any]]:
        """The manifest fingerprints, plus the TEXT of every file.

        The text travels here because the consumer is no longer only the own page: CodeZard
        has to SHOW the code, and until now the content lived only inside the ZIP.

        Two guards, and neither is spare:

        1. :data:`MAX_TEXT_BYTES` in total. Past it the paths go WITHOUT text and say why:
           silently sending a response of tens of MB is not a delivery, it is a failure that
           shows up later and somewhere else.
        2. The same :data:`SECRETS` pattern the package inspection uses. It already stops a
           secret from travelling inside a ZIP, but this payload is emitted EVEN WHEN the ZIP
           is not downloadable. Without this guard the text would open through the API the very
           door the ZIP keeps shut. A file with something shaped like a key sends its path only.
        """
        rows: list[dict[str, Any]] = [{"path": f.path, "bytes": f.size, "lines": f.lines, "sha256": f.sha256}
                                      for f in (manifest.files if manifest else ())]
        total = sum(row["bytes"] for row in rows)
        texts = self.project.as_text_mapping()
        for row in rows:
            text = texts.get(row["path"])
            if total > MAX_TEXT_BYTES:
                row["text"], row["text_omitted"] = None, (
                    f"the project takes {total} bytes and the API cap is {MAX_TEXT_BYTES}: download the ZIP")
            elif text is None:
                row["text"], row["text_omitted"] = None, "not among the project files"
            elif SECRETS.search(text.encode("utf-8", "replace")):
                row["text"], row["text_omitted"] = None, "it contains something shaped like a credential"
            else:
                row["text"] = text
        return rows

    def for_page(self) -> dict[str, Any]:
        """What travels to the browser. Without a single filesystem path."""
        manifest = self.package.manifest if self.package else None
        inspection = self.package.inspection if self.package else None
        cert = self.certificate
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "simulated": self.simulated,
            "reason": cert.reason if cert else "",
            "files": self._files(manifest),
            "totals": self.project.totals,
            "verification": manifest.verification if manifest else {},
            "phases": [{"name": p.name, "status": p.status.value, "detail": p.detail}
                       for p in (cert.phases if cert else ())],
            "zip": ({"name": self.package.name, "bytes": self.package.size, "sha256": self.package.sha256}
                    if self.package else None),
            "integrity": ({"ok": inspection.ok, "reason": inspection.reason,
                           "checks": [list(c) for c in inspection.checks]}
                          if inspection else {"ok": False, "reason": "not packaged", "checks": []}),
            "download_url": self.download_url,
        }


class ArtifactRegistry:
    """In-memory registry with optional disk copies. Thread safe."""

    def __init__(self, folder: Path, ttl_s: int = TTL_S, max_alive: int = MAX_ALIVE,
                 memory_limit: int = MEMORY_LIMIT, clock: Callable[[], float] = time.time) -> None:
        self.folder = Path(folder).resolve()
        self._ttl_s = ttl_s
        self._max_alive = max_alive
        self._memory_limit = memory_limit
        self._clock = clock
        self._items: dict[str, Artifact] = {}
        self._lock = threading.Lock()

    def _reserve(self) -> tuple[str, Path]:
        """``mkdir`` without ``exist_ok``: on a collision it fails instead of overwriting."""
        for _ in range(5):
            ident = secrets.token_hex(12)
            folder = self.folder / ident
            try:
                folder.mkdir(parents=True)
                return ident, folder
            except FileExistsError:
                continue
        raise RuntimeError("no free id could be reserved")

    def save(self, project: Project, certificate: Certificate | None, package: Package | None,
             on_disk: bool = True, simulated: bool = False) -> Artifact:
        """Register the artifact, ready to show and to download.

        ``on_disk=False`` does not touch the filesystem: the artifact lives only in memory and
        **can be downloaded all the same**, because the served bytes come from the package.
        """
        ident = secrets.token_hex(12)
        folder = self.folder / ident
        if on_disk:
            ident, folder = self._reserve()
            # The registry's own folder is the one area inside Mirag a project may be written to
            # (in a source checkout the default data directory lives under the repository).
            project.materialize(folder / "project", allowed_area=self.folder)
            if package is not None and package.data:
                (folder / package.name).write_bytes(package.data)
                (folder / MANIFEST_NAME).write_bytes(package.manifest.to_bytes())
        artifact = Artifact(ident, project.name, self._clock(), folder, project, certificate, package, simulated)
        with self._lock:
            self._items[artifact.id] = artifact
        self._expire()
        return artifact

    def get(self, ident: object) -> Artifact | None:
        """The artifact, or ``None``. The id never touches the disk: it is looked up in the index."""
        if not isinstance(ident, str) or not VALID_ID.match(ident):
            return None
        with self._lock:
            artifact = self._items.get(ident)
        if artifact is None:
            return None
        if self._clock() - artifact.created > self._ttl_s:
            self.forget(ident)
            return None
        return artifact

    def forget(self, ident: str) -> bool:
        with self._lock:
            artifact = self._items.pop(ident, None)
        if artifact is not None:
            self._delete(artifact)
        return artifact is not None

    def alive(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._items)

    def _delete(self, artifact: Artifact) -> None:
        # Only what this registry created is deleted. Never sweep the whole folder.
        if artifact.folder.parent == self.folder and artifact.folder.name == artifact.id and artifact.folder.exists():
            shutil.rmtree(artifact.folder, ignore_errors=True)

    def _expire(self) -> list[str]:
        now = self._clock()
        with self._lock:
            living = sorted(self._items.values(), key=lambda a: a.created)
            out = [a for a in living if now - a.created > self._ttl_s]
            rest = [a for a in living if a not in out]
            while len(rest) > self._max_alive:
                out.append(rest.pop(0))
            memory = sum(a.package.size for a in rest if a.package)
            while memory > self._memory_limit and len(rest) > 1:
                oldest = rest.pop(0)
                memory -= oldest.package.size if oldest.package else 0
                out.append(oldest)
            for artifact in out:
                self._items.pop(artifact.id, None)
        for artifact in out:
            self._delete(artifact)
        return [a.id for a in out]

    def sweep_orphans(self, age_s: float = ORPHAN_AGE_S) -> list[str]:
        """Folders left on disk by previous processes, which nobody knows about any more.

        The registry lives in MEMORY and dies with the process, so expiry never reaches the
        folders of earlier runs. Only what looks like an artifact (a 24-hex id) and is older
        than ``age_s`` is touched.
        """
        removed: list[str] = []
        if not self.folder.exists():
            return removed
        with self._lock:
            known = set(self._items)
        now = self._clock()
        for folder in self.folder.iterdir():
            if not folder.is_dir() or not VALID_ID.match(folder.name) or folder.name in known:
                continue
            try:
                if now - folder.stat().st_mtime > age_s:
                    shutil.rmtree(folder, ignore_errors=True)
                    removed.append(folder.name)
            except OSError:
                continue
        return removed
