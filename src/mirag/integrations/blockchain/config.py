"""The layer's lock, and the networks this code knows how to name.

Standard library only, on purpose: the facade imports this module before it knows whether
``stellar_sdk`` even exists, and it must be able to say "the layer is off" without touching
the package.

``MIRAG_OFFLINE`` does NOT cover this layer. That lock guards the model and the embeddings,
not the network in general, so the layer carries its own - and, unlike the rest of the
settings, it is re-read on every call instead of once at start-up: tests flip it between
cases, and a lock that was read once is a lock that can be stale.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from mirag.core.errors import MiragError, UnknownNetworkError

LOCK_VARIABLE = "MIRAG_BLOCKCHAIN"
OFF = "off"
TESTNET = "testnet"

OFF_REASON = f"{LOCK_VARIABLE} is off: Stellar is not contacted"


class BlockchainDisabledError(RuntimeError, MiragError):
    """Something tried to reach Stellar while the lock is on (``MIRAG_BLOCKCHAIN=off``)."""


@dataclass(frozen=True, slots=True)
class NetworkSettings:
    """Everything the layer needs to know about one Stellar network."""

    name: str
    horizon: str
    rpc: str
    passphrase: str
    friendbot: str
    explorer: str
    identity_registry: str

    def account_link(self, address: str) -> str:
        return f"{self.explorer}/account/{address}"

    def tx_link(self, tx_hash: str) -> str:
        return f"{self.explorer}/tx/{tx_hash}"

    def contract_link(self, contract: str) -> str:
        return f"{self.explorer}/contract/{contract}"


# ── the networks that exist ──────────────────────────────────────────────────
# Mainnet is not here, and it is not an oversight: while it is absent, no path of this code
# can reach it, neither by accident nor through a misspelt environment variable.
NETWORKS: Mapping[str, NetworkSettings] = MappingProxyType({
    TESTNET: NetworkSettings(
        name=TESTNET,
        horizon="https://horizon-testnet.stellar.org",
        rpc="https://soroban-testnet.stellar.org",
        passphrase="Test SDF Network ; September 2015",
        friendbot="https://friendbot.stellar.org",
        explorer="https://stellar.expert/explorer/testnet",
        # Stellar 8004 Identity Registry. Read and verified on 2026-09-16:
        # version() = "0.1.0", total_agents() = 26. See docs/en/blockchain.md.
        identity_registry="CDE3K4COIAGWNNJQQLL26SYI3KBJF5FUDHXG5FA6GYDJCG7T5V7FIWZH",
    ),
})


class BlockchainLock:
    """Reads ``MIRAG_BLOCKCHAIN`` on every call and turns it into a decision.

    ``environ`` is injectable for tests; by default it is ``os.environ``, read each time
    (never copied at construction, so a lock object can never go stale).
    """

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = environ

    def _env(self) -> Mapping[str, str]:
        return os.environ if self._environ is None else self._environ

    def network(self) -> str:
        """The configured network name, normalised. ``off`` when unset."""
        return (self._env().get(LOCK_VARIABLE) or OFF).strip().lower()

    def obstacle(self) -> str:
        """Why Stellar can NOT be contacted right now, or ``""`` if it can.

        An unknown value raises instead of falling back to a default: a silent default is
        exactly how one ends up talking to mainnet by accident.
        """
        name = self.network()
        if name in ("", OFF):
            return OFF_REASON
        if name not in NETWORKS:
            raise UnknownNetworkError(
                f"{LOCK_VARIABLE}={name!r} is not a network this code knows. "
                f"Known: {sorted(NETWORKS)}. Mainnet is absent on purpose.")
        return ""

    def available(self) -> bool:
        return not self.obstacle()

    def settings(self) -> NetworkSettings:
        """The active network. Raises when there is none: it never returns a default."""
        if reason := self.obstacle():
            raise BlockchainDisabledError(reason)
        return NETWORKS[self.network()]


# ── module-level shortcuts over the process environment ──────────────────────
# Each one builds a fresh lock over ``os.environ``: there is no cached state to go stale.

def network() -> str:
    return BlockchainLock().network()


def obstacle() -> str:
    return BlockchainLock().obstacle()


def available() -> bool:
    return BlockchainLock().available()


def settings() -> NetworkSettings:
    return BlockchainLock().settings()


def account_link(address: str) -> str:
    return settings().account_link(address)


def tx_link(tx_hash: str) -> str:
    return settings().tx_link(tx_hash)


def contract_link(contract: str) -> str:
    return settings().contract_link(contract)
