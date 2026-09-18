"""The agent's 8004 identity: register it, read it and - what matters - verify it.

The ABI below was read from the WASM deployed on testnet, not from documentation. The public
web page was wrong on one specific point: ``register(caller)`` does **not** take a
``metadata_uri``. To register with metadata one must use ``register_with_uri``. See
docs/en/blockchain.md.

    register_with_uri(caller: ADDRESS, agent_uri: STRING)  -> U32
    set_agent_wallet(caller, agent_id: U32, new_wallet)    -> Result<VOID, IdentityError>
    get_agent_wallet(agent_id: U32)                        -> Option<ADDRESS>
    agent_uri(agent_id: U32)                               -> Result<STRING, IdentityError>
    agent_exists(agent_id: U32)                            -> BOOL
    total_agents()                                         -> U32

**The identity <-> wallet link is not asserted: it is read back.** :meth:`identity` calls
``get_agent_wallet`` and compares it with the wallet Mirag believes it has. That comparison
is the whole difference between "I registered it" and "it is registered".
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from mirag.integrations.blockchain.config import BlockchainLock
from mirag.integrations.blockchain.metadata import backend_uri
from mirag.integrations.blockchain.models import DEFAULT_AGENT, Identity
from mirag.integrations.blockchain.stellar.client import StellarClient, scval
from mirag.integrations.blockchain.wallet.keys import AgentKeys, MissingKeyError

AGENT_ID_VARIABLE = "STELLAR_AGENT_ID"
# Registration hashes cannot be recomputed: either they are kept when they happen, or they
# are lost. The agent_id could be found by walking the contract, but that costs one read per
# agent; keeping it is cheaper and also makes it clear that it is a CLAIM by Mirag, which
# ``identity()`` then checks against the chain.
REGISTRATION_TX_VARIABLE = "STELLAR_REGISTRATION_TX"
WALLET_TX_VARIABLE = "STELLAR_WALLET_TX"


class IdentityRegistry:
    """Reads and writes of the Stellar 8004 Identity Registry, for one agent keypair."""

    def __init__(self, client: StellarClient, keys: AgentKeys, lock: BlockchainLock | None = None,
                 environ: Mapping[str, str] | None = None) -> None:
        self._client = client
        self._keys = keys
        self._lock = lock or BlockchainLock(environ)
        self._environ = environ

    def _env(self) -> Mapping[str, str]:
        return os.environ if self._environ is None else self._environ

    def _variable(self, name: str) -> str:
        return (self._env().get(name) or "").strip()

    def configured_agent_id(self) -> int | None:
        """The id Mirag believes it has. A claim, not a verification."""
        raw = self._variable(AGENT_ID_VARIABLE)
        return int(raw) if raw.isdigit() else None

    # ── reads ────────────────────────────────────────────────────────────────

    def _source(self) -> str:
        """An existing address to originate the simulations from. It signs nothing."""
        address = self._keys.address()
        if not address:
            raise MissingKeyError("there is no address to simulate a read with")
        return address

    def total(self) -> int:
        return int(self._client.read("total_agents", source=self._source(),
                                     parse=scval.from_uint32))

    def exists(self, agent_id: int) -> bool:
        return bool(self._client.read("agent_exists", scval.to_uint32(agent_id),
                                      source=self._source(), parse=scval.from_bool))

    def wallet_of(self, agent_id: int) -> str:
        """``get_agent_wallet(agent_id)`` -> the address, or ``""`` if the slot is empty."""
        value: Any = self._client.read("get_agent_wallet", scval.to_uint32(agent_id),
                                       source=self._source())
        if value is None:
            return ""
        try:
            return str(scval.from_address(value).address)
        except Exception:
            return ""  # SCV_VOID: registered, but no wallet linked

    def uri_of(self, agent_id: int) -> str:
        try:
            value: Any = self._client.read("agent_uri", scval.to_uint32(agent_id),
                                           source=self._source())
            return scval.from_string(value).decode("utf-8") if value is not None else ""
        except Exception:
            return ""  # UriNotSet, or the agent does not exist

    # ── writes ───────────────────────────────────────────────────────────────

    def register_with_uri(self, wallet: str = "") -> tuple[int, str]:
        """``register_with_uri``. Returns ``(agent_id, tx_hash)``.

        The caller is the same keypair that will be the wallet: ``set_agent_wallet`` requires
        authorisation from the owner AND the wallet, and with one keypair one signature is
        enough. It is a decision, written down in docs/en/blockchain.md, not an accident.
        """
        signer = self._keys.signer()
        uri = backend_uri(wallet or signer.public_key)  # raises BEFORE going on-chain if too big
        agent_id, tx_hash = self._client.invoke(
            "register_with_uri",
            scval.to_address(signer.public_key),
            scval.to_string(uri),
            signer=signer, parse=scval.from_uint32)
        return int(agent_id), tx_hash

    def set_agent_wallet(self, agent_id: int, wallet: str = "") -> str:
        """``set_agent_wallet``. Returns the hash. Checks nothing: :meth:`identity` does."""
        signer = self._keys.signer()
        _, tx_hash = self._client.invoke(
            "set_agent_wallet",
            scval.to_address(signer.public_key),
            scval.to_uint32(agent_id),
            scval.to_address(wallet or signer.public_key),
            signer=signer)
        return tx_hash

    # ── what the page sees ───────────────────────────────────────────────────

    def identity(self, agent: str = DEFAULT_AGENT, registration_tx: str | None = None,
                 wallet_tx: str | None = None) -> Identity | None:
        """The identity read from the chain, with ``verified`` computed, not asserted.

        ``None`` when no agent_id is configured: that is not an error, the agent simply has
        not registered yet.
        """
        agent_id = self.configured_agent_id()
        if agent_id is None:
            return None
        base = Identity(
            agent=agent, agent_id=agent_id,
            registry=self._lock.settings().identity_registry, network=self._lock.network(),
            registration_tx=(self._variable(REGISTRATION_TX_VARIABLE)
                             if registration_tx is None else registration_tx),
            wallet_tx=self._variable(WALLET_TX_VARIABLE) if wallet_tx is None else wallet_tx)
        mine = self._keys.address()
        if not self.exists(agent_id):
            return replace(base, reason=f"the registry knows no agent #{agent_id}. "
                                        f"Was testnet reset?")
        onchain = self.wallet_of(agent_id)
        base = replace(base, onchain_wallet=onchain, uri=self.uri_of(agent_id))
        if not onchain:
            return replace(base, reason=f"agent #{agent_id} exists but has no wallet linked")
        if onchain != mine:
            return replace(base, reason=f"the chain says the wallet of #{agent_id} is "
                                        f"{onchain[:8]}… and Mirag uses {mine[:8]}…")
        return replace(base, verified=True)
