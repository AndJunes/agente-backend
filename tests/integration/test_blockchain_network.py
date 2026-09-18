"""The part of the Stellar layer that needs ``stellar-sdk``.

Without the SDK the whole module is SKIPPED - reported as such by pytest, never disguised as
green. With it, every test except the ``network`` ones still runs without touching the
network: the lock, the keys and the verification logic are checked with doubles.

The ``network`` tests talk to the real Stellar testnet and only run with
``MIRAG_BLOCKCHAIN_NETWORK_TESTS=1``.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

stellar_sdk = pytest.importorskip("stellar_sdk")

from mirag.core.errors import UnknownNetworkError  # noqa: E402
from mirag.integrations import blockchain  # noqa: E402
from mirag.integrations.blockchain import doubles, metadata  # noqa: E402
from mirag.integrations.blockchain.config import BlockchainDisabledError  # noqa: E402
from mirag.integrations.blockchain.identity.registry import IdentityRegistry  # noqa: E402
from mirag.integrations.blockchain.stellar.client import StellarClient, scval  # noqa: E402
from mirag.integrations.blockchain.wallet.keys import AgentKeys, MissingKeyError  # noqa: E402

LAYER_VARIABLES = ("MIRAG_BLOCKCHAIN", "STELLAR_PUBLIC_KEY", "STELLAR_SECRET_KEY",
                   "STELLAR_AGENT_ID", "STELLAR_REGISTRATION_TX", "STELLAR_WALLET_TX")
PUBLIC = "G" + "A" * 55

requires_network = pytest.mark.skipif(
    os.environ.get("MIRAG_BLOCKCHAIN_NETWORK_TESTS") != "1",
    reason="talks to the real Stellar testnet: set MIRAG_BLOCKCHAIN_NETWORK_TESTS=1 to run it")


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in LAYER_VARIABLES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def registered(monkeypatch: pytest.MonkeyPatch) -> tuple[IdentityRegistry, str]:
    """A registry for agent #26 whose keypair is brand new. No read reaches the network:
    each test replaces the contract reads it needs."""
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    monkeypatch.setenv("STELLAR_AGENT_ID", "26")
    public, secret = AgentKeys.generate()
    monkeypatch.setenv("STELLAR_SECRET_KEY", secret)
    registry = IdentityRegistry(StellarClient(), AgentKeys())
    return registry, public


# ══ the lock, now with the SDK present ════════════════════════════════════════

def test_with_the_layer_off_the_client_does_not_go_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """The acid test: the SDK is here, a key is here, and still nobody is called."""
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "off")
    client = StellarClient()
    signer = stellar_sdk.Keypair.random()
    calls = (lambda: client.account(PUBLIC),
             lambda: client.payments_received(PUBLIC),
             lambda: client.fund(PUBLIC),
             lambda: client.read("version", source=PUBLIC),
             lambda: client.invoke("version", signer=signer),
             client.contract_spec)
    for call in calls:
        with pytest.raises(BlockchainDisabledError, match="off"):
            call()


def test_the_choke_point_cannot_be_bypassed(monkeypatch: pytest.MonkeyPatch) -> None:
    """If somebody patches ``_request``, EVERY network path has to notice."""
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    client = StellarClient()
    seen: list[str] = []

    # An empty dict serves all three: ``account`` returns it as is, ``payments_received``
    # iterates it (empty) and ``fund`` calls .get() on it. Each path runs to the end
    # without any of them touching the network.
    def spy(what: str, call: Any) -> dict[str, Any]:
        seen.append(what)
        return {}

    monkeypatch.setattr(client, "_request", spy)
    assert client.account(PUBLIC) == {}
    assert client.payments_received(PUBLIC) == []
    assert client.fund(PUBLIC) == ""
    assert len(seen) == 3, f"some path skipped _request: {seen}"


def test_mainnet_is_still_unreachable_with_the_sdk_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "mainnet")
    with pytest.raises(UnknownNetworkError):
        StellarClient().account(PUBLIC)


def test_without_a_wallet_the_facade_says_so_without_the_network(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    status = blockchain.status()
    assert not status.available and "no wallet" in status.reason
    assert set(status.links) == {"registry"}
    status.for_page()


# ══ the keys ══════════════════════════════════════════════════════════════════

def test_without_a_key_it_is_said_and_nothing_breaks() -> None:
    keys = AgentKeys()
    assert not keys.has_secret() and keys.address() == ""
    assert not keys.can_sign()
    with pytest.raises(MissingKeyError, match="STELLAR_SECRET_KEY"):
        keys.signer()


def test_an_invalid_key_is_not_echoed_in_the_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """An error message that repeats the key publishes it in the logs."""
    garbage = "SGARBAGETHATISNOTAVALIDKEYBUTLOOKSVERYMUCHLIKEONE1234567"
    monkeypatch.setenv("STELLAR_SECRET_KEY", garbage)
    with pytest.raises(MissingKeyError) as caught:
        AgentKeys().signer()
    assert garbage not in str(caught.value), f"the error echoes the key: {caught.value}"
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


def test_the_address_is_derived_from_the_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """So public and secret can never drift apart."""
    public, secret = AgentKeys.generate()
    monkeypatch.setenv("STELLAR_SECRET_KEY", secret)
    monkeypatch.setenv("STELLAR_PUBLIC_KEY", "G" + "Z" * 55)  # a deliberate lie
    assert AgentKeys().address() == public, "the variable won over the secret"


def test_generate_gives_a_different_key_every_time() -> None:
    first, _ = AgentKeys.generate()
    second, _ = AgentKeys.generate()
    assert first != second and first.startswith("G") and len(first) == 56


# ══ the metadata, against the real contract format ════════════════════════════

def test_the_uri_we_generate_is_understood_by_the_standard() -> None:
    uri = metadata.backend_uri(PUBLIC)
    document = metadata.from_uri(uri)
    assert document is not None and document["type"].endswith("#registration-v1")
    assert len(uri) < metadata.MAX_URI_BYTES
    # It encodes as the Soroban STRING the contract takes.
    assert scval.from_string(scval.to_string(uri)).decode() == uri


# ══ the registry, without touching the network ════════════════════════════════

def test_the_identity_is_not_asserted_without_reading_the_chain(
        monkeypatch: pytest.MonkeyPatch, registered: tuple[IdentityRegistry, str]) -> None:
    """The heart of the phase: ``verified`` comes from ``get_agent_wallet``, not from config."""
    registry, public = registered
    reads: list[tuple[str, int]] = []
    monkeypatch.setattr(registry, "exists", lambda agent_id: reads.append(("exists", agent_id)) or True)
    monkeypatch.setattr(registry, "uri_of", lambda agent_id: "")

    monkeypatch.setattr(registry, "wallet_of", lambda agent_id: reads.append(("wallet", agent_id)) or public)
    identity = registry.identity()
    assert identity is not None and identity.verified, \
        f"the chain returned the same wallet and it came out unverified: {identity}"
    assert ("wallet", 26) in reads, "it said 'verified' without calling get_agent_wallet"
    assert identity.onchain_wallet == public

    monkeypatch.setattr(registry, "wallet_of", lambda agent_id: "G" + "Q" * 55)  # the chain disagrees
    identity = registry.identity()
    assert identity is not None and not identity.verified, \
        "the chain named ANOTHER wallet and it came out verified anyway"
    assert identity.reason, "not verified and not saying why"

    monkeypatch.setattr(registry, "wallet_of", lambda agent_id: "")  # registered, no wallet
    identity = registry.identity()
    assert identity is not None and not identity.verified and identity.reason


def test_the_registry_hashes_are_claims_carried_from_the_environment(
        monkeypatch: pytest.MonkeyPatch, registered: tuple[IdentityRegistry, str]) -> None:
    registry, public = registered
    monkeypatch.setenv("STELLAR_REGISTRATION_TX", "ab" * 32)
    monkeypatch.setenv("STELLAR_WALLET_TX", "cd" * 32)
    monkeypatch.setattr(registry, "exists", lambda agent_id: True)
    monkeypatch.setattr(registry, "uri_of", lambda agent_id: metadata.backend_uri(public))
    monkeypatch.setattr(registry, "wallet_of", lambda agent_id: public)
    identity = registry.identity()
    assert identity is not None
    assert (identity.registration_tx, identity.wallet_tx) == ("ab" * 32, "cd" * 32)
    assert identity.summary()["uri"].startswith(metadata.DATA_URI_PREFIX)


def test_without_an_agent_id_there_is_no_identity_and_no_error(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    registry = IdentityRegistry(StellarClient(), AgentKeys())
    assert registry.configured_agent_id() is None
    assert registry.identity() is None


def test_a_testnet_reset_is_noticed_and_explained(
        monkeypatch: pytest.MonkeyPatch, registered: tuple[IdentityRegistry, str]) -> None:
    """If the contract no longer knows the agent, say it; do not show the wallet alone."""
    registry, _ = registered
    monkeypatch.setattr(registry, "exists", lambda agent_id: False)
    identity = registry.identity()
    assert identity is not None and not identity.verified
    assert "testnet" in identity.reason.lower()


def test_writes_refuse_to_sign_without_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    registry = IdentityRegistry(StellarClient(), AgentKeys())
    with pytest.raises(MissingKeyError):
        registry.register_with_uri()
    with pytest.raises(MissingKeyError):
        registry.set_agent_wallet(26)


# ══ the real testnet (opt-in) ═════════════════════════════════════════════════

@pytest.mark.network
@requires_network
def test_the_real_registry_answers_a_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    client = StellarClient()
    if client.account(doubles.WALLET) is None:
        pytest.skip("the reference account no longer exists: testnet was probably reset")
    total = client.read("total_agents", source=doubles.WALLET, parse=scval.from_uint32)
    assert isinstance(total, int) and total >= 1


@pytest.mark.network
@requires_network
def test_the_real_status_of_a_read_only_wallet(monkeypatch: pytest.MonkeyPatch) -> None:
    """With only a public key (no secret, no agent id) the page shows the wallet, honestly."""
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    monkeypatch.setenv("STELLAR_PUBLIC_KEY", doubles.WALLET)
    status = blockchain.status()
    assert status.available, status.reason
    assert status.wallet is not None and status.wallet.address == doubles.WALLET
    assert status.identity is None
    status.for_page()
