"""What the layer hands upwards. Standard library only: the core can read it without the SDK.

The rule that governs this file: **no object here can carry a private key**. Not a field,
not a default, not a ``__repr__`` that fetches it from somewhere. If signing is ever needed,
the key stays in ``wallet/keys.py`` and what arrives here is the result of the signature,
never the key.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from mirag.core.errors import MiragError

DEFAULT_AGENT = "backend"

# A Stellar keypair as text: 56 base32 characters. The public one starts with G, the secret
# one with S. ``SECRET_SEED`` exists so that we can ASSERT a secret is not where it must not
# be. It has no anchors on purpose: a seed embedded in a longer string still counts.
PUBLIC_KEY = re.compile(r"\AG[A-Z2-7]{55}\Z")
SECRET_SEED = re.compile(r"S[A-Z2-7]{55}")
CONTRACT_ID = re.compile(r"\AC[A-Z2-7]{55}\Z")

# The registration URI is a data URI of up to 8 KiB; the page only needs a preview of it.
URI_PREVIEW_CHARS = 120


class SecretLeakError(RuntimeError, MiragError):
    """Something shaped like a Stellar secret seed was about to leave the process."""


def is_public_key(text: str | None) -> bool:
    return bool(PUBLIC_KEY.match(text or ""))


def is_contract(text: str | None) -> bool:
    return bool(CONTRACT_ID.match(text or ""))


def contains_seed(text: str | None) -> bool:
    """Does anything shaped like a secret key appear in this text?

    Used as a safety net before writing to disk, to an HTTP response or to the page. False
    positives are possible (56 base32 characters that are not a key) and that is fine: the
    cost of a false positive is an alarm, the cost of a false negative is a published key.
    """
    return bool(SECRET_SEED.search(text or ""))


@dataclass(frozen=True, slots=True)
class Wallet:
    """The agent's Stellar account. Public data only."""

    agent: str
    address: str
    network: str
    balance: str = ""  # in XLM, as Horizon gives it ("5.0000000"); "" = not read
    exists: bool = False  # an unfunded account does NOT exist on the ledger

    def summary(self) -> dict[str, Any]:
        return {"agent": self.agent, "address": self.address, "network": self.network,
                "balance": self.balance, "exists": self.exists}


@dataclass(frozen=True, slots=True)
class Payment:
    """An incoming payment, as Horizon reports it."""

    tx_hash: str
    sender: str
    amount: str
    asset: str
    at: str

    def summary(self) -> dict[str, Any]:
        return {"hash": self.tx_hash, "from": self.sender, "amount": self.amount,
                "asset": self.asset, "at": self.at}


@dataclass(frozen=True, slots=True)
class Identity:
    """The agent's 8004 identity and - what matters - where each piece of data comes from.

    ``onchain_wallet`` is what ``get_agent_wallet(agent_id)`` returned. ``verified`` is that
    address compared with the wallet Mirag believes it has. They are kept apart on purpose:
    what Mirag claims is one thing, what the chain says is another.
    """

    agent: str
    agent_id: int | None
    registry: str  # the Identity Registry contract
    network: str
    onchain_wallet: str = ""
    uri: str = ""
    registration_tx: str = ""
    wallet_tx: str = ""
    verified: bool = False
    reason: str = ""  # why it is NOT verified, when it is not

    def summary(self) -> dict[str, Any]:
        return {"agent": self.agent, "agent_id": self.agent_id, "registry": self.registry,
                "network": self.network, "onchain_wallet": self.onchain_wallet,
                "uri": self.uri[:URI_PREVIEW_CHARS], "registration_tx": self.registration_tx,
                "wallet_tx": self.wallet_tx, "verified": self.verified, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class AgentStatus:
    """What the page sees. One object, with ``available`` always present."""

    available: bool
    reason: str = ""
    identity: Identity | None = None
    wallet: Wallet | None = None
    last_payment: Payment | None = None
    links: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # A frozen status with a mutable dict inside would not be frozen at all.
        object.__setattr__(self, "links", MappingProxyType(dict(self.links)))

    def for_page(self) -> dict[str, Any]:
        """The JSON that goes out over HTTP. Raises on a seed: better to fail than to leak."""
        payload = {
            "available": self.available,
            "reason": self.reason,
            "identity": self.identity.summary() if self.identity else None,
            "wallet": self.wallet.summary() if self.wallet else None,
            "last_payment": self.last_payment.summary() if self.last_payment else None,
            "links": dict(self.links),
        }
        if contains_seed(json.dumps(payload, ensure_ascii=False)):
            raise SecretLeakError(
                "something shaped like a Stellar secret key was about to go out over HTTP")
        return payload


def disabled(reason: str) -> AgentStatus:
    """The status of a layer that cannot answer, saying why."""
    return AgentStatus(available=False, reason=reason)
