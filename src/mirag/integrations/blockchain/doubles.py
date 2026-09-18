"""Canned Stellar answers, to test without network and without the SDK.

The same role the scripted chat model plays for the LLM: the whole suite must run on a plain
interpreter, without ``stellar-sdk`` installed, without going to the internet and in
constant time.

The data is NOT invented: it has the exact shape Horizon and the contract return, copied
from real reads on 2026-09-16.
"""

from __future__ import annotations

from dataclasses import replace

from mirag.integrations.blockchain.config import NETWORKS, TESTNET
from mirag.integrations.blockchain.metadata import backend_uri
from mirag.integrations.blockchain.models import (
    DEFAULT_AGENT,
    AgentStatus,
    Identity,
    Payment,
    Wallet,
)

# An address and hashes with the right shape. The wallet is the one of agent #1 of the
# testnet registry, which really exists; the rest is filler with a valid shape.
WALLET = "GDAOXABLEOFZP2M4PRM7N6YKOKXWMPFOSLU35WL5ZQY4PQFHF3VCIDS6"
PAYER = "GCCWEPP2MFAUF5HWICYGXDVPBVSHFQWSLQOAMNARLDQIWC2AZVGNRSQV"
REGISTRATION_TX = "8f2a1c0b" + "0" * 56
WALLET_TX = "c91e4d73" + "0" * 56
PAYMENT_TX = "a17b93ec" + "0" * 56
AGENT_ID = 26


def status(verified: bool = True, with_payment: bool = True,
           balance: str = "10005.0000000") -> AgentStatus:
    """The status the page would see with everything working."""
    network = NETWORKS[TESTNET]
    identity = Identity(
        agent=DEFAULT_AGENT, agent_id=AGENT_ID, registry=network.identity_registry,
        network=TESTNET,
        onchain_wallet=WALLET if verified else "",
        uri=backend_uri(WALLET),
        registration_tx=REGISTRATION_TX, wallet_tx=WALLET_TX,
        verified=verified,
        reason="" if verified else "get_agent_wallet returned no address")
    wallet = Wallet(DEFAULT_AGENT, WALLET, TESTNET, balance, True)
    payment = (Payment(PAYMENT_TX, PAYER, "5.0000000", "XLM", "2026-09-16T12:00:00Z")
               if with_payment else None)
    links = {"account": network.account_link(WALLET),
             "registry": network.contract_link(network.identity_registry)}
    if payment:
        links["tx"] = network.tx_link(payment.tx_hash)
    return AgentStatus(True, "", identity, wallet, payment, links)


def without_identity() -> AgentStatus:
    """A funded wallet, not yet registered in the 8004 registry."""
    return replace(status(), identity=None)


def not_verified() -> AgentStatus:
    """The dangerous one: there is an identity, but the chain does not confirm the link.

    The page must show this as NOT verified, never as good.
    """
    return status(verified=False, with_payment=False)
