"""Joins identity and wallet into the ``AgentStatus`` the page sees.

Importing this module imports ``stellar_sdk``. That is why the facade (``__init__.py``)
imports it INSIDE ``status()`` and not at the top: ``import mirag.integrations.blockchain``
keeps working on a machine without the package.
"""

from __future__ import annotations

from collections.abc import Mapping

from mirag.integrations.blockchain.config import BlockchainLock
from mirag.integrations.blockchain.identity.registry import IdentityRegistry
from mirag.integrations.blockchain.models import DEFAULT_AGENT, AgentStatus
from mirag.integrations.blockchain.stellar.client import StellarClient
from mirag.integrations.blockchain.wallet.keys import AgentKeys
from mirag.integrations.blockchain.wallet.service import WalletService


class StatusService:
    def __init__(self, lock: BlockchainLock, keys: AgentKeys, wallets: WalletService,
                 registry: IdentityRegistry) -> None:
        self._lock = lock
        self._keys = keys
        self._wallets = wallets
        self._registry = registry

    def read(self, agent: str = DEFAULT_AGENT) -> AgentStatus:
        """Everything that can be known right now. What is not known is said, not filled in."""
        network = self._lock.settings()
        registry_link = network.contract_link(network.identity_registry)

        if not self._keys.address():
            return AgentStatus(
                available=False,
                reason=(f"the layer is on but there is no wallet: set "
                        f"{AgentKeys.SECRET_VARIABLE} (or {AgentKeys.PUBLIC_VARIABLE}) in .env"),
                links={"registry": registry_link})

        wallet = self._wallets.wallet(agent)
        payment = self._wallets.last_payment() if (wallet and wallet.exists) else None

        try:
            identity = self._registry.identity(agent)
        except Exception as exc:
            # A testnet reset, the contract gone, the RPC not answering. The reason is said
            # instead of showing the wallet as if the identity were fine.
            identity = None
            reason = f"the 8004 registry could not be read: {type(exc).__name__}: {exc}"
        else:
            reason = ""

        links = {"account": network.account_link(wallet.address) if wallet else "",
                 "registry": registry_link,
                 "tx": network.tx_link(payment.tx_hash) if payment else ""}
        return AgentStatus(available=True, reason=reason, identity=identity, wallet=wallet,
                           last_payment=payment,
                           links={name: url for name, url in links.items() if url})


def build_status_service(environ: Mapping[str, str] | None = None) -> StatusService:
    """Wire the SDK side. ``environ`` defaults to ``os.environ``, read on every call."""
    lock = BlockchainLock(environ)
    keys = AgentKeys(environ)
    client = StellarClient(lock)
    return StatusService(lock, keys, WalletService(keys, client, lock),
                         IdentityRegistry(client, keys, lock, environ))
