"""The agent's registration document (EIP-8004), and its data URI.

The shape was NOT invented: it is the one used by the agents already registered in the
testnet Identity Registry, read from agent #0 on 2026-09-16 (see docs/en/blockchain.md).
The ``type`` field is the one fixed by the 8004 standard.

``agent_uri`` in the contract is a STRING, and what people store there is a
``data:application/json;base64,...``: the metadata travels ON the chain, with no server to
maintain. Hence a hard size cap, checked here - before anything is signed or sent.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from mirag.core.errors import MiragError

REGISTRATION_TYPE = "https://eips.ethereum.org/EIPS/eip-8004#registration-v1"
DATA_URI_PREFIX = "data:application/json;base64,"
# The data URI goes into a Soroban STRING. 8 KiB is the limit the ecosystem documents; we
# stay far below it on purpose: this metadata describes an agent, it does not contain it.
MAX_URI_BYTES = 8 * 1024


class MetadataTooLargeError(ValueError, MiragError):
    """The registration document does not fit in the on-chain data URI."""


@dataclass(frozen=True, slots=True)
class AgentProfile:
    """Who the agent says it is. No paid services: this phase charges nothing."""

    name: str
    description: str
    role: str
    version: str
    capabilities: tuple[str, ...]

    def document(self, wallet: str = "") -> dict[str, Any]:
        """The registration JSON.

        ``wallet`` also goes here, besides its dedicated slot in the contract: the slot is
        the truth (``get_agent_wallet``), this is only so a human reading the URI sees it.
        """
        document: dict[str, Any] = {
            "type": REGISTRATION_TYPE,
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "version": self.version,
            "capabilities": list(self.capabilities),
        }
        if wallet:
            document["agentWallet"] = wallet
        return document


BACKEND_PROFILE = AgentProfile(
    name="Mirag Backend Agent",
    description=("Backend engineering agent: retrieves from its corpus, generates a "
                 "multi-file project, runs it, tests it and packages it verified."),
    role="backend",
    version="1.0.0",
    capabilities=("backend-generation", "project-generation", "code-verification"),
)


def registration_document(profile: AgentProfile = BACKEND_PROFILE,
                          wallet: str = "") -> dict[str, Any]:
    return profile.document(wallet)


def to_uri(document: dict[str, Any]) -> str:
    """The data URI stored on the chain. Raises if it does not fit: better here than on-chain."""
    raw = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    uri = DATA_URI_PREFIX + base64.b64encode(raw).decode("ascii")
    if len(uri) > MAX_URI_BYTES:
        raise MetadataTooLargeError(
            f"the metadata takes {len(uri)} bytes and the cap is {MAX_URI_BYTES}")
    return uri


def from_uri(uri: str | None) -> dict[str, Any] | None:
    """Undo :func:`to_uri`. ``None`` when the URI is not a data URI we can read.

    Tolerant on purpose: somebody else (or an older version of this code) wrote the URI, and
    not being able to read it is information, not an exception.
    """
    text = uri or ""
    if not text.startswith(DATA_URI_PREFIX):
        return None
    try:
        decoded = json.loads(base64.b64decode(text[len(DATA_URI_PREFIX):], validate=True))
    except (ValueError, TypeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def backend_uri(wallet: str = "") -> str:
    return to_uri(registration_document(BACKEND_PROFILE, wallet))
