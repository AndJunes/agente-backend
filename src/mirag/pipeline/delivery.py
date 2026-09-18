"""Reading what the model delivered, and keeping it on disk."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mirag.core.errors import ForbiddenPathError
from mirag.projects.model import safe_path

HOW_TO_RUN = "HOW_TO_RUN.txt"


class DeliveryReader:
    """What the model delivered, tolerating a cut or malformed call."""

    @staticmethod
    def read(message: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        """``(delivery, None)`` or ``(None, error_code)``."""
        call = (message.get("tool_calls") or [None])[0]
        if not call:
            return None, "no_call"
        raw = (call.get("function") or {}).get("arguments") or "{}"
        try:
            data = json.loads(raw, strict=False)
        except json.JSONDecodeError:
            return None, "invalid_json"
        if not isinstance(data, dict) or not isinstance(data.get("files"), dict) or not data["files"]:
            return None, "no_files"
        return data, None


class OutputWriter:
    """The code runs in a temporary folder and would be lost. Here it stays on disk.

    Two things that were wrong and broke the product: ``unlink()`` does not remove folders
    (running the delivered code creates ``__pycache__``, and from then on EVERY later code
    task died with PermissionError after paying for the call), and the folder was relative to
    the cwd instead of anchored.
    """

    def __init__(self, folder: Path) -> None:
        self.folder = Path(folder)

    def save(self, delivery: Mapping[str, Any], folder: Path | None = None) -> Path:
        target = Path(folder) if folder else self.folder
        if target.exists():
            for old in target.iterdir():  # do not mix with the previous run
                shutil.rmtree(old) if old.is_dir() else old.unlink()
        target.mkdir(parents=True, exist_ok=True)
        for path, content in (delivery.get("files") or {}).items():
            try:
                relative = safe_path(path)
            except ForbiddenPathError:
                relative = Path(str(path)).name  # no odd paths from the model
                if not relative:
                    continue
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(str(content).encode("utf-8"))
        (target / HOW_TO_RUN).write_text(
            f"{delivery.get('test_command', '?')}\n\n{delivery.get('decisions', '')}\n", encoding="utf-8")
        return target
