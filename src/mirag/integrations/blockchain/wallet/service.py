"""The agent's wallet seen from above: address, balance, incoming payments, testnet funding.

What this module does NOT have, and that is the point: **there is no secret getter**. The
key stays in ``keys.py`` and only ``StellarClient.invoke`` receives the Keypair. A test
checks that nothing here exposes it.

There is no outgoing payment either (no pay, send or transfer). The capability of this phase
is to RECEIVE.
"""

from __future__ import annotations

from mirag.integrations.blockchain.config import BlockchainLock
from mirag.integrations.blockchain.models import DEFAULT_AGENT, Payment, Wallet
from mirag.integrations.blockchain.stellar.client import StellarClient
from mirag.integrations.blockchain.wallet.keys import AgentKeys, MissingKeyError


class WalletService:
    def __init__(self, keys: AgentKeys, client: StellarClient,
                 lock: BlockchainLock | None = None) -> None:
        self._keys = keys
        self._client = client
        self._lock = lock or BlockchainLock()

    def address(self) -> str:
        return self._keys.address()

    def wallet(self, agent: str = DEFAULT_AGENT) -> Wallet | None:
        """The account as it is right now. An unfunded account does not exist: ``exists=False``."""
        address = self.address()
        if not address:
            return None
        data = self._client.account(address)
        return Wallet(agent=agent, address=address, network=self._lock.network(),
                      balance=StellarClient.xlm_balance(data), exists=data is not None)

    def payments(self, limit: int = 5) -> list[Payment]:
        address = self.address()
        return self._client.payments_received(address, limit) if address else []

    def last_payment(self) -> Payment | None:
        payments = self.payments(1)
        return payments[0] if payments else None

    def fund_testnet(self) -> str:
        """Friendbot. The lock already guarantees the network is testnet; Friendbot exists nowhere else."""
        address = self.address()
        if not address:
            raise MissingKeyError("there is no wallet configured to fund")
        return self._client.fund(address)
