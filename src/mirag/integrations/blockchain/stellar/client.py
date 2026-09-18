"""The only place in the layer where a socket is opened, and the one that imports the SDK.

It carries the lock even when the caller already checked it: this is the ONE point where
the layer goes out to the network, and a new path that reached it without going through the
others would talk to Stellar silently. Every public network method goes through
:meth:`StellarClient._request`, and an AST test checks it.

The exact rule - also checked by an AST test - is about the SOCKET, not the package: no
other module of the layer may name ``Server``, ``SorobanServer``, ``ContractClient`` or
``urlopen``. ``wallet/keys.py`` does import ``Keypair``, which is pure cryptography and opens
nothing; that is the only exception, and the test declares it.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, TypeVar

from stellar_sdk import Keypair, Server, SorobanServer, scval
from stellar_sdk.contract import ContractClient
from stellar_sdk.exceptions import NotFoundError
from stellar_sdk.xdr import SCSpecEntryKind, SCSpecType

from mirag.integrations.blockchain.config import (
    BlockchainDisabledError,
    BlockchainLock,
    NetworkSettings,
)
from mirag.integrations.blockchain.models import Payment

__all__ = ["Keypair", "StellarClient", "scval"]

T = TypeVar("T")


class StellarClient:
    """Horizon, Soroban RPC, Friendbot and the Identity Registry contract, behind one lock."""

    TIMEOUT_S = 20  # a demo that hangs for 5 minutes shows nothing
    MAX_FEE_STROOPS = 1_000_000  # 0.1 XLM ceiling: Soroban charges per resource, not per operation
    USER_AGENT = "Mirag/2.0 (+stdlib urllib)"

    def __init__(self, lock: BlockchainLock | None = None) -> None:
        self._lock = lock or BlockchainLock()

    def _request(self, what: str, call: Callable[[], T]) -> T:
        """Every trip to the network goes through here. No exceptions."""
        if reason := self._lock.obstacle():  # raises UnknownNetworkError for mainnet & co.
            raise BlockchainDisabledError(f"{what}: {reason}")
        return call()

    def _network(self) -> NetworkSettings:
        return self._lock.settings()

    def _horizon(self) -> Server:
        return Server(horizon_url=self._network().horizon)

    def _contract(self) -> ContractClient:
        network = self._network()
        return ContractClient(network.identity_registry, network.rpc, network.passphrase)

    # ── accounts ─────────────────────────────────────────────────────────────

    def account(self, address: str) -> dict[str, Any] | None:
        """The account data, or ``None`` if it does not exist on the ledger yet.

        On Stellar an unfunded account does NOT exist: it is not a zero balance, it is a
        404. The difference matters to the page, so ``None`` is returned, not a fake balance.
        """
        def go() -> dict[str, Any] | None:
            try:
                return self._horizon().accounts().account_id(address).call()
            except NotFoundError:
                return None
        return self._request("read the account", go)

    @staticmethod
    def xlm_balance(account_data: dict[str, Any] | None) -> str:
        """The native balance in an account record, or ``""``. Pure parsing, no network."""
        for balance in (account_data or {}).get("balances", []):
            if balance.get("asset_type") == "native":
                return str(balance.get("balance", ""))
        return ""

    def payments_received(self, address: str, limit: int = 5) -> list[Payment]:
        """The most recent INCOMING payments. Outgoing ones and other operations are dropped."""
        def go() -> Any:
            page = (self._horizon().payments().for_account(address).order(desc=True)
                    .limit(min(limit * 4, 50)).call())
            return page.get("_embedded", {}).get("records", [])
        payments: list[Payment] = []
        for record in self._request("read the payments", go):
            if record.get("type") not in ("payment", "create_account"):
                continue
            if (record.get("to") or record.get("account")) != address:
                continue
            payments.append(Payment(
                tx_hash=record.get("transaction_hash", ""),
                sender=record.get("from") or record.get("funder", ""),
                amount=record.get("amount") or record.get("starting_balance", ""),
                asset=("XLM" if record.get("asset_type", "native") == "native"
                       else record.get("asset_code", "?")),
                at=record.get("created_at", ""),
            ))
            if len(payments) >= limit:
                break
        return payments

    def fund(self, address: str) -> str:
        """Friendbot. It only exists on testnet, and the lock already guarantees we are there."""
        def go() -> Any:
            url = self._network().friendbot + "?" + urllib.parse.urlencode({"addr": address})
            # Friendbot answers 403 to urllib's default User-Agent ("Python-urllib/3.x"): a
            # filter in front takes it for a bot. Checked: the same GET with curl gets 200,
            # and with urllib and no header gets 403.
            request = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
            with urllib.request.urlopen(request, timeout=self.TIMEOUT_S) as response:
                return json.loads(response.read())
        answer = self._request("fund with friendbot", go)
        return str(answer.get("hash") or answer.get("id", ""))

    # ── the Identity Registry contract ───────────────────────────────────────

    def read(self, function: str, *args: Any, source: str,
             parse: Callable[[Any], Any] | None = None) -> Any:
        """A contract read: simulated, unsigned, never submitted, free.

        ``source`` is an address that exists on the ledger; it is only the origin of the
        simulation and signs nothing.
        """
        def go() -> Any:
            return self._contract().invoke(function, list(args), parse_result_xdr_fn=parse,
                                           source=source).result()
        return self._request(f"read {function}()", go)

    def invoke(self, function: str, *args: Any, signer: Keypair,
               parse: Callable[[Any], Any] | None = None) -> tuple[Any, str]:
        """A write: signed and submitted. Returns ``(result, transaction_hash)``.

        ``signer`` is a Keypair. This is the only place in the whole repository where
        something is signed, and the key arrives already built from ``wallet/keys.py``: no
        environment variable is read and no file is touched here.

        The hash is NOT what ``sign_and_submit`` returns - that is the contract function's
        return value - but lives in ``send_transaction_response``. Without the hash there is
        nothing to show in the explorer, so it is extracted explicitly.
        """
        def go() -> tuple[Any, str]:
            tx = self._contract().invoke(function, list(args), source=signer.public_key,
                                         signer=signer, base_fee=self.MAX_FEE_STROOPS,
                                         parse_result_xdr_fn=parse)
            result = tx.sign_and_submit()
            sent = tx.send_transaction_response
            return result, (getattr(sent, "hash", "") if sent else "")
        return self._request(f"invoke {function}()", go)

    def contract_spec(self) -> list[str]:
        """The registry's function signatures, read FROM the chain (the deployed WASM).

        This is what produced the ABI in docs/en/blockchain.md: the public documentation was
        wrong on one point, so the ABI is read from what actually runs.
        """
        def go() -> list[str]:
            network = self._network()
            spec = SorobanServer(network.rpc).get_contract_spec(network.identity_registry)
            signatures = []
            for entry in spec:
                function = entry.function_v0
                if entry.kind != SCSpecEntryKind.SC_SPEC_ENTRY_FUNCTION_V0 or function is None:
                    continue
                arguments = ", ".join(f"{_text(arg.name)}: {_type_name(arg.type)}"
                                      for arg in function.inputs)
                outputs = ", ".join(_type_name(output) for output in function.outputs) or "()"
                signatures.append(f"{_text(function.name)}({arguments}) -> {outputs}")
            return signatures
        return self._request("read the contract spec", go)


def _text(value: Any) -> str:
    for attribute in ("sc_symbol", "sc_string"):
        if hasattr(value, attribute):
            value = getattr(value, attribute)
    return value.decode() if isinstance(value, bytes) else str(value)


def _type_name(spec_type: Any) -> str:
    name = SCSpecType(spec_type.type.value).name.replace("SC_SPEC_TYPE_", "")
    if name == "UDT":
        return _text(spec_type.udt.name)
    if name == "OPTION":
        return f"Option<{_type_name(spec_type.option.value_type)}>"
    if name == "VEC":
        return f"Vec<{_type_name(spec_type.vec.element_type)}>"
    if name == "RESULT":
        return (f"Result<{_type_name(spec_type.result.ok_type)},"
                f"{_type_name(spec_type.result.error_type)}>")
    return name
