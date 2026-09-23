"""The ZIP, and the proof that it is the same project that was verified.

THE CHAIN THAT MUST BE PROVABLE

    artifact -> workspace -> verification -> manifest -> ZIP -> reopening -> download

Between each pair there must be checkable identity, or the defect that ran through this
whole project comes back: the ZIP downloaded != the project verified != the tree shown.

TWO DIFFERENT CRITERIA, ON PURPOSE
    The builder includes by ALLOW-list: only what is in the manifest gets in, so ``.env``,
    ``__pycache__`` or Mirag's traces cannot slip in by construction.

    The inspector rejects by DENY-list of patterns and by content. If the inspector reused
    the builder's filter, a single bug would open both doors and the test would stay green.

ON DETERMINISM, WITHOUT OVERPROMISING
    Same tree and same interpreter give the same bytes. Across zlib versions that is not
    guaranteed, so what is claimed - and tested - is the strong property: the set of
    (name, CRC-32, size) is always the same.
"""

from __future__ import annotations

import io
import json
import re
import tempfile
import time
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mirag.core.text import sha256_hex
from mirag.projects.model import Project

if TYPE_CHECKING:
    from mirag.projects.certification import Certificate

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
"""No mtimes: they are non-deterministic noise."""
MAX_ZIP = 8 * 1024 * 1024
MANIFEST_NAME = "MIRAG_ARTIFACT.json"

# What can NEVER appear inside the ZIP. PATTERNS over each entry.
FORBIDDEN = (
    re.compile(r"(^|/)\.env$"),  # .env.example does not match: the $ comes after 'env'
    re.compile(r"(^|/)__pycache__(/|$)"),
    re.compile(r"\.py[co]$"),
    re.compile(r"(^|/)(traces?|trazas).*\.jsonl$"),
    re.compile(r"(^|/)eval_cache\.json$"),
    re.compile(r"(^|/)\.git(/|$)"),
    re.compile(r"(^|/)\.DS_Store$"),
    re.compile(r"(^|/)(node_modules|\.venv|venv)(/|$)"),
    re.compile(r"\.(key|pem|p12|keystore)$"),
    re.compile(r"(^|/)(id_rsa|\.npmrc|\.netrc|\.pypirc)$"),
    re.compile(r"(^|/)_probe_\w+\.py$"),  # Mirag's harness does not belong to the user
)
# Shapes that ARE a secret wherever they appear: nothing legitimate looks like these.
SECRETS = re.compile(
    rb"sk-or-v1-[A-Za-z0-9]{16,}|sk-ant-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}"
    rb"|BEGIN [A-Z ]*PRIVATE KEY"
    # A Stellar seed: 'S' + 55 base32. It is the signing key and the only way to catch it is
    # its shape. A false positive costs an alarm; a false negative publishes a private key.
    rb"|\bS[A-Z2-7]{55}\b"
)

# Names that are only a finding when something real is ASSIGNED to them.
#
# `OPENROUTER_API_KEY` used to be in SECRETS as a bare literal, which matched the NAME and not
# a value. The model carries Mirag's own corpus as context, so documenting that variable in a
# README or an `.env.example` is entirely plausible — and it failed the integrity check,
# which removes the download button. A project is punished for documenting its configuration.
NAMED_SECRET = re.compile(
    rb"(?i)\b(OPENROUTER_API_KEY|STELLAR_SECRET_KEY|ANTHROPIC_API_KEY|OPENAI_API_KEY"
    rb"|AWS_SECRET_ACCESS_KEY|SECRET_KEY|API_KEY|API_TOKEN|PASSWORD)\b\s*[:=]\s*"
    rb"[\"']?([^\s\"'#,;]+)"
)
PLACEHOLDER = re.compile(
    rb"(?i)\A(?:x+$|\.+$|-+$|_+$|<|your|my-|the-|put-|insert|replace|change|placeholder"
    rb"|todo|tbd|none|null|empty|example|dummy|fake|test|secret|password|hunter2|abc123|123)"
)
NOT_A_VALUE = re.compile(rb"(?i)[(){}\[\]$<>]|\bos\.|getenv|environ|process\.|config\.|settings\.|self\.")
"""`SECRET_KEY = os.environ.get("SECRET_KEY")` is how a project is SUPPOSED to read a secret.
Reading the right-hand side as if it were the secret would fail the integrity check on the
one line that proves the project does not hardcode it."""


def carries_secret(raw: bytes) -> str:
    """The secret found in ``raw``, or ``""``.

    Two passes on purpose: a shape is a secret anywhere, a name is one only when what follows
    it is not a placeholder. `KEY=your-key-here` documents; `KEY=sk-or-v1-8f2...` leaks.
    """
    if found := SECRETS.search(raw):
        return found.group(0).decode("utf-8", "replace")[:24]
    for name, value in NAMED_SECRET.findall(raw):
        if len(value) >= 12 and not PLACEHOLDER.match(value) and not NOT_A_VALUE.search(value):
            return name.decode("utf-8", "replace")
    return ""


@dataclass(frozen=True, slots=True)
class Fingerprint:
    path: str
    sha256: str
    size: int
    lines: int


@dataclass(frozen=True, slots=True)
class Manifest:
    project: str
    generated_at: str
    version: str
    status: str
    verification: dict[str, Any]
    files: tuple[Fingerprint, ...]

    def paths(self) -> tuple[str, ...]:
        return tuple(f.path for f in self.files)

    def by_path(self) -> dict[str, Fingerprint]:
        return {f.path: f for f in self.files}

    def to_bytes(self) -> bytes:
        body = {
            "project": self.project, "generated_at": self.generated_at, "mirag": self.version,
            "status": self.status, "verification": self.verification,
            "files": [{"path": f.path, "sha256": f.sha256, "bytes": f.size, "lines": f.lines}
                      for f in self.files],
        }
        return json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"


@dataclass(frozen=True, slots=True)
class Inspection:
    ok: bool
    checks: tuple[tuple[str, bool, str], ...]
    """``((code, ok, detail), ...)``. Codes are stable; the UI translates them."""
    reason: str

    def failed(self) -> tuple[tuple[str, bool, str], ...]:
        return tuple(c for c in self.checks if not c[1])


@dataclass(frozen=True, slots=True)
class Package:
    name: str
    data: bytes
    sha256: str
    manifest: Manifest
    inspection: Inspection
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.inspection.ok

    @property
    def size(self) -> int:
        return len(self.data)


def build_manifest(project: Project, certificate: Certificate | None = None, version: str = "mirag") -> Manifest:
    """Computed AFTER verifying: it represents what was checked."""
    verification: dict[str, Any] = {}
    if certificate is not None:
        verification = {"status": certificate.status.value, "reason": certificate.reason,
                        "markers": dict(certificate.markers),
                        "passed": certificate.passed, "failed": certificate.failed}
    return Manifest(
        project=project.name,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        version=version,
        status=certificate.status.value if certificate is not None else "GENERATED",
        verification=verification,
        files=tuple(Fingerprint(f.path, f.sha256, f.size, f.lines) for f in project.files()),
    )


class ZipBuilder:
    """The bytes of the ZIP. Allow-list: only what the manifest declares gets in."""

    @staticmethod
    def _info(name: str) -> zipfile.ZipInfo:
        info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3  # fixed unix: otherwise it differs by OS
        info.external_attr = 0o644 << 16
        return info

    def build(self, project: Project, manifest: Manifest) -> bytes:
        root = manifest.project
        allowed = set(manifest.paths())
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for file in project.files():
                if file.path not in allowed:
                    continue  # not in the manifest: it does not get in
                archive.writestr(self._info(f"{root}/{file.path}"), file.data)
            archive.writestr(self._info(f"{root}/{MANIFEST_NAME}"), manifest.to_bytes())
        return buffer.getvalue()


class ZipInspector:
    """REOPENS the ZIP and checks it is what the manifest says. Never raises."""

    def inspect(self, data: bytes, manifest: Manifest) -> Inspection:
        checks: list[tuple[str, bool, str]] = []

        def check(code: str, ok: bool, detail: str = "") -> bool:
            checks.append((code, bool(ok), detail))
            return bool(ok)

        def done(reason: str = "") -> Inspection:
            failed = [c for c in checks if not c[1]]
            text = reason or "; ".join(f"{c[0]}: {c[2]}" if c[2] else c[0] for c in failed)
            return Inspection(not failed, tuple(checks), text)

        if not check("fits_cap", len(data) <= MAX_ZIP, f"{len(data)} bytes"):
            return done("the ZIP exceeds the size cap")
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
            names = archive.namelist()
        except Exception as exc:
            check("reopens", False, f"{type(exc).__name__}: {exc}")
            return done("the ZIP cannot be reopened")
        check("reopens", True, f"{len(names)} entries")

        try:
            corrupt = archive.testzip()
        except Exception as exc:
            corrupt = type(exc).__name__
        if not check("crc_ok", corrupt is None, str(corrupt or "")):
            return done(f"corrupt CRC in {corrupt}")

        root = manifest.project
        outside = [n for n in names if not n.startswith(f"{root}/")]
        check("single_root", not outside, ", ".join(outside[:3]))
        escaping = [n for n in names if n.startswith("/") or ".." in n.split("/") or "\\" in n]
        check("no_path_escapes", not escaping, ", ".join(escaping[:3]))
        links = [i.filename for i in archive.infolist() if (i.external_attr >> 16) & 0o170000 == 0o120000]
        check("no_symlinks", not links, ", ".join(links[:3]))

        relative = [n[len(root) + 1:] for n in names if n.startswith(f"{root}/")]
        vetoed = [(n, p.pattern) for n in relative for p in FORBIDDEN if p.search(n)]
        check("no_junk_or_secret_names", not vetoed, "; ".join(f"{n} ({p})" for n, p in vetoed[:3]))

        declared = set(manifest.paths())
        present = set(relative) - {MANIFEST_NAME}
        missing, extra = sorted(declared - present), sorted(present - declared)
        # A second entry with the same name is an extra file too. The set above hid it, and the
        # re-hash below cannot see it: extraction keeps the LAST copy, while another unzip tool
        # may keep the first - which can be anything.
        duplicated = sorted(n for n, times in Counter(relative).items() if times > 1)
        check("no_missing_files", not missing, ", ".join(missing[:3]))
        check("no_extra_files", not extra and not duplicated,
              ", ".join([*extra, *(f"{n} (duplicated)" for n in duplicated)][:3]))

        # the re-hash: really extracted, as the user will do
        mismatched: list[tuple[str, str]] = []
        with_secret: list[str] = []
        # ignore_cleanup_errors: on Windows a file still held by a scanner makes the cleanup
        # raise, and "never raises" has to hold on the way out too.
        with tempfile.TemporaryDirectory(prefix="mirag-zip-", ignore_cleanup_errors=True) as tmp:
            try:
                archive.extractall(tmp)
            except Exception as exc:
                check("extracts", False, f"{type(exc).__name__}: {exc}")
                return done("the ZIP cannot be extracted")
            check("extracts", True, "")
            for path, fingerprint in manifest.by_path().items():
                extracted = Path(tmp) / root / path
                # is_file, not exists: a hostile ZIP can put a DIRECTORY where the manifest
                # declares a file, and reading it raised out of a method that never raises.
                if not extracted.is_file():
                    mismatched.append((path, "not extracted"))
                    continue
                try:
                    raw = extracted.read_bytes()
                except OSError as exc:
                    mismatched.append((path, f"unreadable ({type(exc).__name__})"))
                    continue
                if sha256_hex(raw) != fingerprint.sha256:
                    mismatched.append((path, "different hash"))
                elif len(raw) != fingerprint.size:
                    mismatched.append((path, "different size"))
                if found := carries_secret(raw):
                    with_secret.append(f"{path} ({found})")
            embedded = Path(tmp) / root / MANIFEST_NAME
            try:
                same_manifest = embedded.is_file() and embedded.read_bytes() == manifest.to_bytes()
            except OSError:
                same_manifest = False

        check("hashes_match", not mismatched, "; ".join(f"{p}: {why}" for p, why in mismatched[:3]))
        check("no_secret_content", not with_secret, ", ".join(with_secret[:3]))
        check("embedded_manifest_matches", same_manifest, "")
        return done()


class Packager:
    def __init__(self, builder: ZipBuilder | None = None, inspector: ZipInspector | None = None) -> None:
        self._builder = builder or ZipBuilder()
        self._inspector = inspector or ZipInspector()

    def seal(self, project: Project, certificate: Certificate | None = None, version: str = "mirag") -> Package:
        """Build and inspect. **Never raises**: an integrity failure cannot take down an
        answer that already cost money and verification."""
        manifest = build_manifest(project, certificate, version)
        try:
            data = self._builder.build(project, manifest)
        except Exception as exc:
            failed = Inspection(False, (("builds", False, f"{type(exc).__name__}: {exc}"),),
                                f"the ZIP could not be built: {exc}")
            return Package(f"{project.name}.zip", b"", "", manifest, failed)
        return Package(f"{project.name}.zip", data, sha256_hex(data), manifest, self._inspector.inspect(data, manifest))
