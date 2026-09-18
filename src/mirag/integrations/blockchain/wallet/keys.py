"""The agent's secret key. The only file in the repository that sees it.

The rules, and what enforces each one:

    the key does not leave this file     ``signer()`` returns a Keypair, never the string.
                                         No function returns the secret except
                                         ``generate()``, for a brand new key.
    it is never printed                  ``AgentKeys.__repr__`` does not touch it, errors
                                         never echo it, no print of the layer receives it.
    it never reaches the page            ``AgentStatus.for_page()`` RAISES if it detects
                                         something shaped like a seed in the output JSON.
    it never slips into a ZIP            ``mirag.projects.packaging.SECRETS`` catches it.
    no other module reads it             an AST test checks the whole ``src/mirag`` tree.

Tests check each of these sentences. If one stops being true, they go red.

The SDK (``Keypair``, pure cryptography: it opens no socket) is imported inside the methods,
so importing this module does not import ``stellar_sdk``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING

from mirag.core.errors import MiragError

if TYPE_CHECKING:
    from stellar_sdk import Keypair

SECRET_VARIABLE = "STELLAR_SECRET_KEY"
PUBLIC_VARIABLE = "STELLAR_PUBLIC_KEY"


class MissingKeyError(RuntimeError, MiragError):
    """No usable key is configured. A normal condition, not a program failure."""


class AgentKeys:
    """Access to the agent's keypair, read from the environment on every call.

    ``environ`` is injectable for tests; by default it is ``os.environ``. The secret is
    never stored on the object: it is read, turned into a Keypair and dropped.
    """

    SECRET_VARIABLE = SECRET_VARIABLE
    PUBLIC_VARIABLE = PUBLIC_VARIABLE

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = environ

    def __repr__(self) -> str:
        return f"{type(self).__name__}(<the secret is never shown>)"

    def _env(self) -> Mapping[str, str]:
        return os.environ if self._environ is None else self._environ

    def _raw_secret(self) -> str:
        return (self._env().get(SECRET_VARIABLE) or "").strip()

    def has_secret(self) -> bool:
        return bool(self._raw_secret())

    def address(self) -> str:
        """The agent's public address, or ``""`` if none is configured.

        It is derived from the secret when there is one - so the two can never drift apart -
        and falls back to ``STELLAR_PUBLIC_KEY`` when there is only an address, which is the
        read-only case.
        """
        if self.has_secret():
            return self.signer().public_key
        return (self._env().get(PUBLIC_VARIABLE) or "").strip()

    def signer(self) -> Keypair:
        """The Keypair that signs. ``StellarClient.invoke`` consumes it and nobody else.

        Returning a Keypair and not a string is deliberate: a Keypair does not end up in an
        f-string without anyone noticing, nor in a log by accident.
        """
        raw = self._raw_secret()
        if not raw:
            raise MissingKeyError(
                f"there is no {SECRET_VARIABLE}. For the demo: generate one with "
                f"`python scripts/blockchain_agent_demo.py --create` and put it in .env")
        from stellar_sdk import Keypair  # the SDK, only in here

        try:
            return Keypair.from_secret(raw)
        except Exception as exc:
            # Without the value in the message: an error that echoes the key publishes it
            # in the logs.
            raise MissingKeyError(f"{SECRET_VARIABLE} is not a valid Stellar secret key "
                                  f"({type(exc).__name__})") from None

    def can_sign(self) -> bool:
        try:
            self.signer()
        except MissingKeyError:
            return False
        return True

    @staticmethod
    def generate() -> tuple[str, str]:
        """A brand new keypair. Returns ``(public, secret)`` exactly ONCE.

        It is the ONLY function in the whole repository that returns a secret, and it lives
        here so that fact can be found in a single file. The demo calls it with ``--create``,
        with the operator in front, who copies the key into ``.env`` by hand. It is not
        persisted, not logged and cannot be read again.
        """
        from stellar_sdk import Keypair

        keypair = Keypair.random()
        return keypair.public_key, keypair.secret
