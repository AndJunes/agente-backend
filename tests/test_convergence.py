"""The loop that replaced three hand-written copies of itself.

What is checked here is exactly what the three copies had already got wrong once: who spends
which attempts, what "the repairer declined" means, and whether anything looks at the clock.
"""

from __future__ import annotations

import threading

from conftest import ScriptedRepairer
from mirag.core.timing import Deadline
from mirag.projects.convergence import ConvergenceLoop, Round, Stop, Verdict
from mirag.projects.dependencies import Finding, Severity
from mirag.projects.model import Project


def finding(file: str = "app/main.py") -> Finding:
    return Finding("failing_test", Severity.ERROR, file, 3, "it blew up")


def project() -> Project:
    return Project.from_mapping("demo", {"app/main.py": "x = 1\n"})


def green_after(n: int):
    """A probe that reports red until it has been called ``n`` times."""
    calls = {"count": 0}

    def probe(candidate: Project) -> Verdict:
        calls["count"] += 1
        return Verdict(green=calls["count"] >= n, findings=(finding(),), output="output")

    probe.calls = calls  # type: ignore[attr-defined]
    return probe


def test_a_green_verdict_spends_no_attempt() -> None:
    repairer = ScriptedRepairer({"app/main.py": "x = 2\n"})
    result = ConvergenceLoop(3).converge(
        "tests", project(), Verdict(green=True), green_after(1), repairer)

    assert result.stop is Stop.NOTHING_TO_DO
    assert result.green
    assert result.rounds == ()
    assert repairer.calls == [], "a repairer must not be called about something already green"


def test_it_repairs_until_green_and_stops_there() -> None:
    repairer = ScriptedRepairer({"app/main.py": "x = 2\n"}, {"app/main.py": "x = 3\n"})
    result = ConvergenceLoop(3).converge(
        "tests", project(), Verdict(False, (finding(),)), green_after(2), repairer)

    assert result.stop is Stop.GREEN
    assert result.attempts == 2
    assert result.repaired
    assert [attempt for attempt, _ in repairer.calls] == [1, 2]
    assert result.project.get("app/main.py").text == "x = 3\n"


def test_a_declined_repair_ends_the_loop_without_spending_the_rest() -> None:
    """Declining is the repairer having nothing to offer for this diagnosis.

    Asking again sends the same prompt and pays for the same silence, so the loop stops —
    and the round is still recorded, because a call was made and it cost something.
    """
    repairer = ScriptedRepairer(None)
    result = ConvergenceLoop(3).converge(
        "syntax", project(), Verdict(False, (finding(),)), green_after(99), repairer)

    assert result.stop is Stop.DECLINED
    assert result.attempts == 1
    assert not result.repaired
    assert result.rounds[0].declined
    assert result.rounds[0].cause == "nothing left to change"


def test_each_motive_gets_its_own_attempts() -> None:
    """The bug this module exists for: three loops drawing from one pool.

    Two separate `converge` calls on the same loop object must each get the full ceiling —
    the loop holds the CEILING, never a running total.
    """
    loop = ConvergenceLoop(2)
    first = loop.converge("syntax", project(), Verdict(False, (finding(),)),
                          green_after(99), ScriptedRepairer({"a.py": "1\n"}, {"a.py": "2\n"}))
    second = loop.converge("tests", project(), Verdict(False, (finding(),)),
                           green_after(99), ScriptedRepairer({"b.py": "1\n"}, {"b.py": "2\n"}))

    assert first.stop is Stop.EXHAUSTED
    assert second.stop is Stop.EXHAUSTED
    assert first.attempts == second.attempts == 2


def test_an_expired_clock_stops_it_before_the_next_call() -> None:
    """A run whose time is spent used to keep paying for repairs nobody was waiting for."""
    loop = ConvergenceLoop(3, Deadline(limit_s=0.000_001))
    repairer = ScriptedRepairer({"app/main.py": "x = 2\n"})
    result = loop.converge("tests", project(), Verdict(False, (finding(),)),
                           green_after(99), repairer)

    assert result.stop is Stop.DEADLINE
    assert repairer.calls == [], "no repair may START once the clock is out"


def test_a_closed_tab_counts_as_out_of_time() -> None:
    cancelled = threading.Event()
    cancelled.set()
    loop = ConvergenceLoop(3, Deadline(limit_s=600, cancelled=cancelled))

    assert loop.out_of_time()
    result = loop.converge("tests", project(), Verdict(False, (finding(),)),
                           green_after(99), ScriptedRepairer({"a.py": "1\n"}))
    assert result.stop is Stop.DEADLINE


def test_without_a_repairer_it_says_nobody_tried() -> None:
    """"It was tried and failed" and "nobody tried" must not read the same."""
    result = ConvergenceLoop(3).converge(
        "imports", project(), Verdict(False, (finding(),)), green_after(1), None)

    assert result.stop is Stop.UNREPAIRABLE
    assert result.rounds == ()


def test_zero_attempts_is_the_same_answer_as_no_repairer() -> None:
    result = ConvergenceLoop(0).converge(
        "imports", project(), Verdict(False, (finding(),)), green_after(1),
        ScriptedRepairer({"a.py": "1\n"}))

    assert result.stop is Stop.UNREPAIRABLE


def test_the_repair_row_is_emitted_before_the_recheck() -> None:
    """The trace has to read in the order things happened.

    `on_repair` fires when the repairer answers and `on_round` after the re-check. A probe
    that writes its own row (the tests phase does) would otherwise land ahead of the row
    saying what was touched to produce it.
    """
    order: list[str] = []

    def probe(candidate: Project) -> Verdict:
        order.append("recheck")
        return Verdict(green=True)

    ConvergenceLoop(3).converge(
        "tests", project(), Verdict(False, (finding(),)), probe,
        ScriptedRepairer({"app/main.py": "x = 2\n"}),
        on_repair=lambda round: order.append(f"repair:{round.attempt}"),
        on_round=lambda round: order.append("round"))

    assert order == ["repair:1", "recheck", "round"]


def test_a_declined_round_still_reaches_the_listener() -> None:
    """It is the only listener a declined round reaches, and the round has to be recorded:
    a call was made and it cost something."""
    seen: list[Round] = []
    result = ConvergenceLoop(3).converge(
        "tests", project(), Verdict(False, (finding(),)), green_after(99),
        ScriptedRepairer(None), on_repair=seen.append,
        on_round=lambda round: seen.append(round))

    assert [round.attempt for round in seen] == [1]
    assert seen[0].verdict is None
    assert result.records == ({"attempt": 1, "files": [], "cause": "nothing left to change",
                               "motive": "tests"},)


def test_the_findings_of_the_latest_verdict_are_what_the_next_repair_sees() -> None:
    """A repair works from the CURRENT failure, not from the one that opened the loop."""
    verdicts = iter([Verdict(False, (finding("app/second.py"),), "second output"),
                     Verdict(green=True)])
    repairer = ScriptedRepairer({"a.py": "1\n"}, {"b.py": "2\n"})

    ConvergenceLoop(3).converge("tests", project(),
                                Verdict(False, (finding("app/first.py"),), "first output"),
                                lambda _project: next(verdicts), repairer)

    assert repairer.calls == [(1, ("app/first.py",)), (2, ("app/second.py",))]
