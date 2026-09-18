"""The facade: the only thing the Mirag core knows about the optional Stellar layer.

    Container.blockchain_status()  --lazy import-->  blockchain.status()  -->  AgentStatus

Two rules this file exists to keep:

1. **Importing it does NOT import ``stellar_sdk``.** Only ``config``, ``models``,
   ``metadata`` and ``doubles``, which are pure standard library. The SDK comes in when -
   and only when - somebody asks to talk to the real network. That is why the core server
   starts and the whole core suite runs on a machine without the package installed.

2. **It never raises.** If the layer is off, if the SDK is missing, if the network does not
   answer or if the contract no longer exists after a testnet reset, the answer is an
   ``AgentStatus(available=False, reason=...)``. The server does not fall over because of
   this, and the page has something honest to show.
"""

from __future__ import annotations

from mirag.core.errors import UnknownNetworkError
from mirag.integrations.blockchain import config, doubles, metadata, models
from mirag.integrations.blockchain.models import (
    DEFAULT_AGENT,
    AgentStatus,
    Identity,
    Payment,
    Wallet,
    disabled,
)

__all__ = [
    "DEFAULT_AGENT",
    "AgentStatus",
    "Identity",
    "Payment",
    "UnknownNetworkError",
    "Wallet",
    "available",
    "config",
    "doubles",
    "metadata",
    "models",
    "status",
]

MISSING_DEPENDENCY_HINT = 'pip install -e ".[blockchain]"'


def available() -> bool:
    """Can Stellar be contacted right now? Never raises."""
    try:
        return config.available()
    except Exception:  # an unknown network, or anything else: "no" is the honest answer
        return False


def status(agent: str = DEFAULT_AGENT, simulate: bool | None = None) -> AgentStatus:
    """Everything the page needs to know, in one object. Never raises.

    ``simulate=True`` forces the doubles. With ``None`` the lock decides: if the layer is
    off there is nothing real to read, so nothing is simulated either - the status says it
    is off. A double that switched itself on would be the UI lying.
    """
    if simulate:
        return doubles.status()
    try:
        reason = config.obstacle()
    except Exception as exc:  # UnknownNetworkError above all: say it, do not default
        return disabled(str(exc) or type(exc).__name__)
    if reason:
        return disabled(reason)
    try:
        # Here, and only here, the SDK comes in.
        from mirag.integrations.blockchain.service import build_status_service
    except ImportError as exc:
        return disabled(f"the layer is on but its dependency is missing: {exc}. "
                        f"Install it with: {MISSING_DEPENDENCY_HINT}")
    try:
        return build_status_service().read(agent)
    except Exception as exc:  # the network, the contract, a testnet reset
        return disabled(f"{type(exc).__name__}: {exc}")
