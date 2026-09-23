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


class ModelUnreachableError(MiragError):
    """The call never got to the provider: DNS, TLS, a refused connection, a timeout.

    Distinct from :class:`RateLimitedError`, which means the provider answered and said no.
    It was nothing at all before: a TLS failure on this machine escaped the handler, the
    server dropped the connection without a body, and the gateway reported the AGENT as
    unreachable after sixty seconds. Three machines and the wrong one named.
    """


class RunStoppedError(MiragError):
    """The run stopped for a reason that is neither the provider's nor the request's: the
    clock ran out, or the person who asked went away.

    It is caught wherever the three model errors are caught, because the handling is
    identical — keep what was built, stop asking — and it is named apart because reporting
    "the spending cap was reached" for a run that ran out of TIME is exactly the misleading
    sentence this codebase keeps having to remove.
    """


class DeadlineExceededError(RunStoppedError):
    """The wall clock ran out.

    Distinct from a socket timeout, which only ever bounded one ``recv``: a provider sending
    one byte a minute rearms that timer forever and never times out at all.
    """


class ClientGoneError(RunStoppedError):
    """Nobody is waiting for this answer any more.

    The work is stopped, not only the writing. Before this, a closed tab set a flag that
    suppressed the SSE writes and left the generation running — and being billed — to the end.
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
