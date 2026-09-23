"""Repair until it is green, or until saying honestly why it is not. ONE loop, reused.

WHY THIS FILE EXISTS
    Certification had three repair loops written out by hand — syntax, imports, failing
    tests — and they had already drifted apart: one of them started its range at
    ``len(repairs) + 1`` and drew from a pool the other two had emptied, so a project that
    needed two syntax repairs reached its failing tests with zero attempts left and the tests
    were never asked about. Three copies of a loop are three places for that to happen again.

    They are the same loop. Something is wrong, a repairer is asked to fix it, the thing is
    CHECKED AGAIN, and that repeats until it is green, until the repairer declines, until the
    attempts run out or until the clock does. What differs between the three is only the probe
    and the diagnosis, and both of those arrive as arguments.

WHAT IT REFUSES TO DO
    It never decides a status. It returns what happened — the rounds, the last verdict and
    WHY it stopped — and :class:`~mirag.projects.certification.StatusDeriver` stays the only
    thing in the code base that turns observations into a verdict.

THE CLOCK IS CHECKED HERE, AND IT WAS NOT BEFORE
    The three hand-written loops never looked at the deadline. A run whose time was already
    spent could still make six model calls, one per remaining attempt, for an answer nobody
    was waiting for. The loop asks before each attempt, never in the middle of one: a repair
    that is already paid for is always finished and always recorded.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum

from mirag.core.timing import Deadline, Stopwatch
from mirag.projects.dependencies import Finding
from mirag.projects.model import Project

MAX_ATTEMPTS = 3
"""Repair attempts PER MOTIVE, and per motive is the point.

Raised from the two the hand-written loops allowed, because the ceiling that mattered was
never this one: the deadline and the spending cap both cut earlier and both know what they
are protecting. A project one repair away from green used to be delivered red so that a
counter nobody had tuned could stay where it was."""


class Stop(StrEnum):
    """Why the loop stopped. Every value is a different sentence to a reader."""

    GREEN = "green"
    """It converged. This is the only value that means the problem is gone."""

    NOTHING_TO_DO = "nothing_to_do"
    """It was already green when the loop was entered: no attempt was made."""

    DECLINED = "declined"
    """The repairer returned no changed file. Not a failure of the project — the repairer
    looking at the diagnosis and having nothing to offer. Attempting again would send the
    same prompt and pay for the same silence."""

    EXHAUSTED = "exhausted"
    """``max_attempts`` repairs were made and it is still not green."""

    DEADLINE = "deadline"
    """The run's clock ran out, or the client hung up, before the next attempt."""

    UNREPAIRABLE = "unrepairable"
    """It is not green and no repairer was given. A certification run with no model behind it
    reaches here, and "nobody tried" must not read the same as "it was tried and failed"."""


@dataclass(frozen=True, slots=True)
class Verdict:
    """What one probe of the project observed. The loop reads ``green`` and nothing else."""

    green: bool
    findings: tuple[Finding, ...] = ()
    """What to repair. Handed to the repairer untouched."""
    output: str = ""
    """The raw output the probe produced, for the repairer to read."""
    detail: str = ""
    """One line for whoever is watching. The loop never parses it."""


@dataclass(frozen=True, slots=True)
class Round:
    """One repair attempt: what it changed, why, and what the re-check then said."""

    motive: str
    attempt: int
    changed: tuple[str, ...]
    cause: str
    ms: float
    verdict: Verdict | None = None
    """The re-check AFTER this round, or ``None`` when the repairer changed nothing and there
    was nothing to re-check."""

    @property
    def declined(self) -> bool:
        return not self.changed

    def as_record(self) -> dict[str, object]:
        """The shape `Certificate.repairs` has always had, so traces do not change meaning."""
        return {"attempt": self.attempt, "files": list(self.changed), "cause": self.cause,
                "motive": self.motive}


@dataclass(frozen=True, slots=True)
class Convergence:
    """The whole loop as one value: what came out, how it got there and why it stopped."""

    motive: str
    project: Project
    """The project as it ended up. The SAME object when nothing was changed."""
    verdict: Verdict
    stop: Stop
    rounds: tuple[Round, ...] = field(default_factory=tuple)

    @property
    def green(self) -> bool:
        return self.verdict.green

    @property
    def repaired(self) -> bool:
        """Did any attempt actually change a file?"""
        return any(round.changed for round in self.rounds)

    @property
    def attempts(self) -> int:
        return len(self.rounds)

    @property
    def records(self) -> tuple[dict[str, object], ...]:
        return tuple(round.as_record() for round in self.rounds)


Probe = Callable[[Project], Verdict]
"""Check the project again. Called once per successful repair, never otherwise."""

Repairer = Callable[[Project, Sequence[Finding], str, int],
                    tuple[Project, tuple[str, ...], str]]
"""``(project, findings, output, attempt) -> (new project, changed paths, cause)``.

The same type ``certification`` has always declared; it lives here now because the loop is
what calls it, and ``certification`` re-exports it so no import anywhere had to move."""

RoundListener = Callable[[Round], None]
"""Two of them exist and the difference is WHEN, which is the difference a reader sees.

``on_repair`` fires the moment the repairer answers, before anything is checked again, so the
row saying "three files were touched" lands ahead of the row saying what happened next. It is
also the only one a declined round reaches — there is nothing to re-check when nothing
changed, and that round still has to be recorded. ``on_round`` fires after the re-check, with
the verdict filled in."""


class ConvergenceLoop:
    """Repair-and-recheck for ONE motive, bounded by attempts and by the run's clock.

    Holds no state between calls: the deadline and the ceiling are the only things it
    remembers, and both are about the run rather than about any one motive.
    """

    def __init__(self, max_attempts: int = MAX_ATTEMPTS, deadline: Deadline | None = None) -> None:
        self._max_attempts = max(0, max_attempts)
        self._deadline = deadline

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def out_of_time(self) -> bool:
        """Is there still a reason to start one more piece of work?

        Cancellation counts as much as expiry: a closed tab and a spent clock are the same
        answer to "is anybody waiting for this".
        """
        deadline = self._deadline
        return deadline is not None and (deadline.expired() or deadline.cancelled.is_set())

    def converge(
        self,
        motive: str,
        project: Project,
        verdict: Verdict,
        probe: Probe,
        repairer: Repairer | None = None,
        on_repair: RoundListener | None = None,
        on_round: RoundListener | None = None,
    ) -> Convergence:
        """Repair ``motive`` until ``verdict.green``, and report what happened either way.

        ``verdict`` is the check the caller has ALREADY made — the one that revealed the
        problem. Taking it as an argument instead of probing again is what keeps this loop
        from paying twice for the first observation of every motive.
        """
        rounds: list[Round] = []

        def finish(stop: Stop) -> Convergence:
            return Convergence(motive, project, verdict, stop, tuple(rounds))

        if verdict.green:
            return finish(Stop.NOTHING_TO_DO)
        if repairer is None or self._max_attempts == 0:
            return finish(Stop.UNREPAIRABLE)

        for attempt in range(1, self._max_attempts + 1):
            # Asked BEFORE the call, never during one. A repair already paid for is always
            # finished and always recorded; what this refuses is starting another.
            if self.out_of_time():
                return finish(Stop.DEADLINE)

            clock = Stopwatch()
            repaired, changed, cause = repairer(project, verdict.findings, verdict.output, attempt)
            round = Round(motive, attempt, tuple(changed), cause, clock.ms)
            if on_repair is not None:
                on_repair(round)
            if not changed:
                rounds.append(round)
                return finish(Stop.DECLINED)

            project = repaired
            verdict = probe(project)
            round = replace(round, verdict=verdict)
            rounds.append(round)
            if on_round is not None:
                on_round(round)
            if verdict.green:
                return finish(Stop.GREEN)

        return finish(Stop.EXHAUSTED)
