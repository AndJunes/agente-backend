"""Domain exceptions.

Each one names a condition the application handles on purpose. Anything else is a bug and
is allowed to propagate to the boundary (the HTTP handler or the CLI), which reports it.
"""

from __future__ import annotations


class MiragError(Exception):
    """Base class for every error raised on purpose by Mirag."""


class BudgetExceededError(MiragError):
    """The per-request spending cap was reached. Raised BEFORE spending more, not after."""


class RateLimitedError(MiragError):
    """The provider refused the call because of its own limits, not because of the request.

    It has a name because without one it arrived at the user as "the model returned no usable
    blueprint" — a sentence about the model's answer, for a call that never got an answer. An
    hour went into the wrong question before the raw 429 was read.
    """


class OfflineModeError(MiragError):
    """Somebody tried to call the model while the offline lock is on.

    It fails loudly on purpose: a red test is preferable to an invoice.
    """


class ForbiddenPathError(ValueError, MiragError):
    """A path that can never exist inside a generated project."""


class ForbiddenDestinationError(ValueError, MiragError):
    """An attempt to materialise a generated project on top of Mirag itself."""


class SealedProjectError(RuntimeError, MiragError):
    """A sealed project cannot change: what was verified is what gets packaged."""


class UnknownNetworkError(RuntimeError, MiragError):
    """``MIRAG_BLOCKCHAIN`` names a network this code does not know.

    It raises instead of falling back to a default: a silent default is exactly how one
    ends up talking to mainnet by accident.
    """
