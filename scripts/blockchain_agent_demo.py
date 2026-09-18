"""The whole flow: wallet, funding, 8004 registration and verification against the chain.

    python scripts/blockchain_agent_demo.py              # read and show
    python scripts/blockchain_agent_demo.py --create     # a new keypair
    python scripts/blockchain_agent_demo.py --fund       # Friendbot (testnet only)
    python scripts/blockchain_agent_demo.py --register   # register_with_uri + set_agent_wallet
    python scripts/blockchain_agent_demo.py --abi        # the contract spec, read from the chain

Nothing here runs on its own. Every step that writes to the chain needs its flag, with the
operator in front. Without flags it only reads and shows.

It needs the optional dependency (``pip install -e ".[blockchain]"``) and
``MIRAG_BLOCKCHAIN=testnet``. With the lock on (the default) the demo says what is missing
and exits without touching the network.
"""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parent.parent
if (ROOT / "src" / "mirag").is_dir() and str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))  # a source checkout without `pip install -e .`

from mirag.core.errors import UnknownNetworkError  # noqa: E402
from mirag.core.settings import load_dotenv  # noqa: E402
from mirag.integrations import blockchain  # noqa: E402
from mirag.integrations.blockchain import config, metadata  # noqa: E402
from mirag.integrations.blockchain.wallet.keys import AgentKeys  # noqa: E402

WIDTH = 74
INSTALL_HINT = 'pip install -e ".[blockchain]"'


class AgentDemo:
    """Each command returns an exit code: 0 when everything it claims was checked."""

    def __init__(self, out: TextIO | None = None) -> None:
        self._out = out or sys.stdout

    # ── output ───────────────────────────────────────────────────────────────

    def _print(self, text: str = "") -> None:
        print(text, file=self._out)

    def _rule(self, char: str = "─") -> None:
        self._print(char * WIDTH)

    def _field(self, name: str, value: object, short: bool = False) -> None:
        text = str(value) if value is not None else "—"
        if short and len(text) > 44:
            text = text[:44] + "…"
        self._print(f"  {name:<22} {text}")

    def _network_obstacle(self) -> str:
        """Why the network can not be used, or ``""``. Printed, never raised."""
        try:
            reason = config.obstacle()
        except UnknownNetworkError as exc:
            return str(exc)
        if reason:
            return (f"{reason}\n    For the demo: MIRAG_BLOCKCHAIN=testnet "
                    f"python scripts/blockchain_agent_demo.py")
        return ""

    def _refuse(self, reason: str) -> int:
        self._print(f"  ✗ {reason}")
        return 1

    # ── commands ─────────────────────────────────────────────────────────────

    def abi(self) -> int:
        """Reads the contract spec FROM the chain. This is what produced docs/en/blockchain.md."""
        if reason := self._network_obstacle():
            return self._refuse(reason)
        from mirag.integrations.blockchain.stellar.client import StellarClient

        self._print(f"\n  ABI read from {config.settings().identity_registry}\n")
        for signature in StellarClient().contract_spec():
            self._print(f"    {signature}")
        return 0

    def create(self) -> int:
        keys = AgentKeys()
        if keys.has_secret():
            return self._refuse(f"{AgentKeys.SECRET_VARIABLE} is already set. It is not "
                                f"overwritten: remove it by hand if you want another one.")
        public, secret = AgentKeys.generate()
        self._print("\n  New wallet. Copy these two lines into .env (which is NOT versioned):\n")
        self._print(f"    {AgentKeys.PUBLIC_VARIABLE}={public}")
        self._print(f"    {AgentKeys.SECRET_VARIABLE}={secret}")
        self._print("\n  The secret cannot be read again. Next: --fund and --register.")
        return 0

    def fund(self) -> int:
        if reason := self._network_obstacle():
            return self._refuse(reason)
        from mirag.integrations.blockchain.stellar.client import StellarClient
        from mirag.integrations.blockchain.wallet.service import WalletService

        wallets = WalletService(AgentKeys(), StellarClient())
        self._print(f"  funding {wallets.address()} with Friendbot…")
        tx_hash = wallets.fund_testnet()
        wallet = wallets.wallet()
        self._field("tx", tx_hash)
        self._field("balance", f"{wallet.balance} XLM" if wallet else "—")
        return 0

    def register(self) -> int:
        if reason := self._network_obstacle():
            return self._refuse(reason)
        from mirag.integrations.blockchain.identity.registry import (
            AGENT_ID_VARIABLE,
            REGISTRATION_TX_VARIABLE,
            WALLET_TX_VARIABLE,
            IdentityRegistry,
        )
        from mirag.integrations.blockchain.stellar.client import StellarClient

        keys = AgentKeys()
        registry = IdentityRegistry(StellarClient(), keys)
        if (existing := registry.configured_agent_id()) is not None:
            return self._refuse(f"{AGENT_ID_VARIABLE}={existing} is already set. Remove it "
                                f"from .env if you want to register another agent.")
        mine = keys.address()
        self._print(f"  the registry holds {registry.total()} agents")
        self._print(f"  register_with_uri(caller={mine[:10]}…, agent_uri=<data URI>) signing…")
        agent_id, registration_tx = registry.register_with_uri()
        self._field("agent_id", agent_id)
        self._field("tx", registration_tx)
        self._print(f"  set_agent_wallet({agent_id}, {mine[:10]}…) signing…")
        wallet_tx = registry.set_agent_wallet(agent_id)
        self._field("tx", wallet_tx)
        self._print("\n  Copy this into .env:\n")
        self._print(f"    {AGENT_ID_VARIABLE}={agent_id}")
        self._print(f"    {REGISTRATION_TX_VARIABLE}={registration_tx}")
        self._print(f"    {WALLET_TX_VARIABLE}={wallet_tx}")
        return 0

    def show(self) -> int:
        status = blockchain.status()
        self._rule("═")
        self._print("  BACKEND AGENT · Stellar 8004")
        self._rule("═")
        if not status.available:
            return self._refuse(status.reason)
        wallet, identity, payment = status.wallet, status.identity, status.last_payment
        self._field("network", config.network())
        if wallet:
            self._field("wallet", wallet.address)
            self._field("balance", f"{wallet.balance} XLM" if wallet.exists
                        else "the account does not exist (not funded)")
        self._rule()
        if not identity:
            self._print("  no identity: the agent is not registered in the 8004 registry yet")
            if status.reason:
                self._print(f"    {status.reason}")
            self._print("  → --register")
        else:
            self._field("agent id", f"#{identity.agent_id}")
            self._field("identity registry", identity.registry)
            self._field("wallet ON THE CHAIN", identity.onchain_wallet or "—")
            self._field("registration tx", identity.registration_tx or "—", short=True)
            self._field("wallet tx", identity.wallet_tx or "—", short=True)
            document = metadata.from_uri(identity.uri)
            self._field("metadata", (f"{document.get('name')} · "
                                     f"{', '.join(document.get('capabilities', []))}")
                        if document else "—", short=True)
            self._rule()
            if identity.verified:
                self._print("  ✓ VERIFIED ON-CHAIN")
                self._print(f"    get_agent_wallet({identity.agent_id}) returns the same wallet "
                            f"Mirag uses.")
                self._print("    It is not what Mirag says about itself: it is what the "
                            "contract answers.")
            else:
                self._print("  ✗ NOT VERIFIED")
                self._print(f"    {identity.reason}")
        if payment:
            self._rule()
            self._field("last payment", f"+{payment.amount} {payment.asset} "
                                        f"from {payment.sender[:10]}…")
            self._field("tx", payment.tx_hash, short=True)
        self._rule()
        for name, url in status.links.items():
            self._field(name, url)
        self._rule("═")
        self._print("  capability: RECEIVE · outgoing payments: NOT IMPLEMENTED · "
                    "mainnet: NOT REACHABLE")
        return 0 if (identity and identity.verified) else 1


def main(argv: Sequence[str] | None = None, *, dotenv: bool = True,
         out: TextIO | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mirag's Stellar 8004 identity, step by step (testnet only).")
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument("--create", action="store_true", help="generate a new keypair")
    commands.add_argument("--fund", action="store_true", help="fund the wallet with Friendbot")
    commands.add_argument("--register", action="store_true",
                          help="register the agent and link its wallet (signs two transactions)")
    commands.add_argument("--abi", action="store_true",
                          help="print the registry's ABI, read from the deployed contract")
    args = parser.parse_args(argv)
    if out is None and isinstance(sys.stdout, io.TextIOWrapper):
        # A Windows pipe is cp1252: the box-drawing characters must degrade, not crash.
        sys.stdout.reconfigure(errors="replace")
    if dotenv:
        # The real environment wins over the file, as everywhere else in Mirag.
        load_dotenv(ROOT / ".env")
    demo = AgentDemo(out)
    try:
        if args.create:
            return demo.create()
        if args.fund:
            return demo.fund()
        if args.register:
            return demo.register()
        if args.abi:
            return demo.abi()
        return demo.show()
    except ImportError as exc:
        print(f"  ✗ the optional dependency is missing ({exc}). Install it with: {INSTALL_HINT}",
              file=out or sys.stdout)
        return 1


if __name__ == "__main__":
    sys.exit(main())
