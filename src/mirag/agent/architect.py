"""The EXPERIMENTAL architecture workflow: ordered phases over the same agent and corpus.

Difference with the plain agent loop: there the model decides EVERYTHING in one loop. Here
the pipeline sets the order and each phase has a concrete job, because the order of reasoning
(understand -> associate -> decide -> design) is exactly what sets a senior apart.

Its phases do NOT go through the evidence discipline of the pipeline: what it shows is what
the model says, not execution evidence. The UI labels it experimental.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mirag.agent.loop import AgentLoop, AgentResult
from mirag.core.errors import BudgetExceededError
from mirag.execution.verdict import ExecutionStatus
from mirag.i18n.catalog import MessageCatalog
from mirag.llm.gateway import LLMGateway

SYSTEM = """You are a senior backend architect. You work over a knowledge base of 19 areas and you ALWAYS
consult it before claiming anything technical; cite the box each thing comes from.

Your method has three operations:
- ASSOCIATE: connect concepts from different areas that the problem touches at once.
- REASON: analyse consequences, limits and risks of each option.
- DECIDE: choose one and say what would change your mind.

Rules: propose nothing you cannot justify with a requirement. Say out loud what you assume.
Prefer the simplest solution that meets the real requirements.

FORMAT: lists and tables, no filler prose nor summaries of what earlier phases said (the reader
has them). When a phase demands sections with concrete titles, they are mandatory and in order.
Do ONLY the work of your phase; if you get ahead of the next one, you spoil it."""

PHASES: tuple[tuple[str, str], ...] = (
    ("understand", """Extract from the problem:
(a) FUNCTIONAL requirements: what the system must do;
(b) NON-FUNCTIONAL requirements: scale, target latency, consistency, availability,
    durability, regulatory compliance and cost;
(c) what the user did NOT say and must be assumed, with the assumption written explicitly;
(d) what TYPE of problem it is (CRUD, read heavy, transactional, event-driven, batch, real time...).
End with the question that would most change the design if answered differently.
Do NOT propose a solution, technologies or architecture yet."""),
    ("associate", """Identify which knowledge areas are involved and how they connect.
Use related_boxes to see the dependency map and search_docs for the key concepts.
Return ONLY: (a) a table area -> the 2-3 concrete concepts it brings to the problem,
and (b) the dependencies between those concepts (what needs what).
Forbidden in this phase: proposing technologies, comparing options, giving capacity numbers or
sketching architecture. That belongs to phases 3 and 4."""),
    ("decide", """For each open decision you detected: use search_tradeoffs, compare 2-3 real
alternatives, and DECIDE one. Format: one block per decision, only this - Decision · Chosen ·
Discarded alternatives · Why (tied to a requirement from phase 1) · Trade-off you accept · What
would change your mind. Forbidden in this phase: table schemas, endpoints, code, or describing the
design. Only DECISIONS. End by naming the global architecture in ONE line."""),
    ("design", """Apply the decisions of phase 3 to the concrete design.
Your answer MUST have EXACTLY these five sections, with these titles and in this order:

## API            endpoints, methods, status codes and key headers
## Data           tables with columns, keys and indexes
## Asynchrony     what leaves the request, queues, jobs and their idempotency
## Security       authentication, per-object authorisation and tenant isolation
## Reliability    timeouts, retries, degradation; and what to measure and alert on

Schemas and signatures, never long function bodies. Do NOT validate yet: failures are phase 5."""),
    ("validate", """Review the design of phase 4 looking for its seams. Use search_failures for each
component you proposed. Your answer MUST have EXACTLY these three sections:

## What can go wrong   failures of THIS design (not generic), symptom and mitigation
## What it does NOT cover   known limits and from which point it would need a redesign
## Verdict             in 3 lines: is it ready to be built? what would you solve first?"""),
    ("implement", """Turn the design into real code. Implement ONLY the critical path: the operation
where the risk you identified in phase 3 lives. No filler CRUD around it.

Your answer MUST have EXACTLY these four sections, with these titles and in this order:

## Schema          the DDL of the tables the critical path touches, with indexes and constraints
## Critical path   the complete function: transaction, concurrency, errors and idempotency
## Edges           input validation, authorisation and the HTTP handler
## Tests           the 3-4 tests that prove the hard part works (concurrency, retry, permission)

Runnable code, not pseudocode. Do NOT review your own code: that is phase 7."""),
    ("review", """Review the code of phase 6 as if it were someone else's. This phase runs NOTHING:
it produces HYPOTHESES that phase 8 must prove or refute. Contrast with the knowledge base:
search_anti_patterns and search_failures.

Your answer MUST have EXACTLY these four sections:

## Suspicions          what you believe fails, ORDERED by severity, each with the code fragment,
                       why you suspect it, and HOW IT COULD BE PROVED with a test
## Design deviations   where the code does not do what phases 3 and 4 decided
## Untestable risks    what fails in production but cannot be reproduced in a test
## Priority            which suspicion to test first and why"""),
    ("verify", """Your only job is to turn the suspicions of phase 7 into EVIDENCE. Do not give
opinions: run things. For EACH falsifiable suspicion write a test that proves or discards it and
pass it through run_code. Also ALWAYS write these three: CONCURRENCY (two simultaneous operations
on the same resource - a sequential test does NOT count), IDEMPOTENCY (the same retry twice does
not duplicate the effect) and FAILURE (what happens when the dependency is slow, fails or answers
oddly). THE TEST MUST EXIT WITH A NON-ZERO CODE IF SOMETHING FAILS. Each test prints
TEST:<id>:PASS or TEST:<id>:FAIL.

Your answer MUST have EXACTLY these three sections:

## Evidence       per suspicion: PROVED or DISCARDED, with the real output and its exit code
## New findings   what failed without anyone suspecting it
## Not tested     what stayed unverified and why

Do NOT fix the code: that is phase 9, and only if something fails."""),
)

FIX = ("fix", """Phase 8 proved that something fails. Fix it. Rewrite ONLY what is needed for the
failing tests to pass without breaking the passing ones. For each fix say what failed, what you
changed and why that is the right solution according to the knowledge base (cite it). Then run the
SAME tests again with run_code and show the real output.

Your answer MUST have EXACTLY these three sections:

## What failed      the failing test and the root cause in the code
## What I changed   the corrected code and the citation that justifies it
## New evidence     the real output of running again, with its exit code""")

EventListener = Callable[[dict[str, Any]], None]


@dataclass
class ArchitectResult:
    phases: list[dict[str, Any]] = field(default_factory=list)
    design: str = ""
    pending: str | None = None
    exhausted: str | None = None

    @property
    def final_answer(self) -> str:
        return self.phases[-1]["answer"] if self.phases else ""


class ArchitectWorkflow:
    def __init__(self, loop: AgentLoop, catalog: MessageCatalog) -> None:
        self._loop = loop
        self._t = catalog

    def needs_fix(self, result: AgentResult) -> str | None:
        """Did something stay demonstrably broken? The real exit code first; as a safety net,
        a phase that declares a PROVED suspicion (a test can print FAIL and exit 0)."""
        executions = result.executions
        if executions:
            last = executions[-1]
            if last.status is ExecutionStatus.FAILED:
                return self._t("architect.fix.non_zero_exit")
            if last.status is ExecutionStatus.NOT_EXECUTED:
                return self._t("architect.fix.not_executed", header=last.describe(self._t))
            if last.status is ExecutionStatus.NO_EVIDENCE:
                return self._t("architect.fix.no_markers")
        if re.search(r"\bPROVED\b|DEMOSTRADA|✗ FAIL|CRITICAL", result.answer):
            return self._t("architect.fix.declared")
        return None

    def _phase(self, key: str, instruction: str, context: str, gateway: LLMGateway, turns: int,
               on_event: EventListener | None, label: str) -> AgentResult:
        if on_event:
            on_event({"type": "phase", "text": label})
        system = f"{SYSTEM}\n\n{self._t('llm.language_directive')}"
        result = self._loop.run(f"{context}\n\n--- TASK OF THIS PHASE ---\n{instruction}", gateway,
                                system=system, max_turns=turns, on_event=on_event)
        if on_event:
            on_event({"type": "thought", "text": result.answer})
            on_event({"type": "cost", "text": str(gateway.budget)})
        return result

    def design(self, problem: str, gateway: LLMGateway, max_fixes: int = 2,
               on_event: EventListener | None = None) -> ArchitectResult:
        out = ArchitectResult()
        context = f"PROBLEM:\n{problem}"
        last: AgentResult | None = None
        try:
            for number, (key, instruction) in enumerate(PHASES, 1):
                label = f"{number} · {self._t(f'architect.phase.{key}')}"
                last = self._phase(key, instruction, context, gateway, 6, on_event, label)
                context += f"\n\n=== RESULT OF PHASE {label} ===\n{last.answer}"
                out.phases.append({"phase": label, "answer": last.answer})
            # the fix loop: only if the REAL execution failed, not if the model thinks it did
            for attempt in range(max_fixes):
                reason = self.needs_fix(last) if last else None
                if not reason:
                    break
                for key, instruction in (FIX, PHASES[-1]):
                    label = f"{self._t(f'architect.phase.{key}')} ({self._t('architect.attempt', number=attempt + 1)})"
                    last = self._phase(key, instruction, context, gateway, 8, on_event, label)
                    context += f"\n\n=== RESULT OF {label} ===\n{last.answer}"
                    out.phases.append({"phase": label, "answer": last.answer})
        except BudgetExceededError as exc:
            out.exhausted = str(exc)  # stop with what is done, do not blow up
        except Exception as exc:  # a failure in phase 4 does not throw away phases 1-3
            where = out.phases[-1]["phase"] if out.phases else self._t("architect.first_phase")
            out.exhausted = self._t("architect.error_in", phase=where, error=f"{type(exc).__name__}: {exc}")
        out.design = context
        out.pending = (self.needs_fix(last) if last else self._t("architect.nothing_ran"))
        return out
