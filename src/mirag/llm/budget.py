"""Real spending, counted per request. OpenRouter returns the cost of every call."""

from __future__ import annotations

from dataclasses import dataclass

from mirag.core.errors import BudgetExceededError


@dataclass(frozen=True, slots=True)
class BudgetSnapshot:
    cost_usd: float = 0.0
    calls: int = 0
    tokens: int = 0

    def minus(self, earlier: BudgetSnapshot) -> BudgetSnapshot:
        """What was spent between ``earlier`` and this snapshot."""
        return BudgetSnapshot(
            cost_usd=self.cost_usd - earlier.cost_usd,
            calls=self.calls - earlier.calls,
            tokens=self.tokens - earlier.tokens,
        )


class Budget:
    """Accumulates cost and tokens and cuts BEFORE spending more, not after the invoice.

    One instance per request: with a threaded server, two requests sharing a counter reset
    each other's totals and the cap stopped meaning anything.
    """

    def __init__(self, limit_usd: float = 0.0) -> None:
        self.limit_usd = limit_usd
        self.cost_usd = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def capped(self) -> bool:
        return 0 < self.limit_usd < 1e6

    def record(self, prompt_tokens: int = 0, completion_tokens: int = 0, cost_usd: float = 0.0) -> None:
        self.calls += 1
        self.input_tokens += prompt_tokens
        self.output_tokens += completion_tokens
        self.cost_usd += cost_usd

    def check(self) -> None:
        """Raise :class:`BudgetExceededError` if the cap was reached. 0 = no cap."""
        if self.limit_usd <= 0:
            return
        if self.cost_usd >= self.limit_usd:
            raise BudgetExceededError(
                f"Spending cap reached: ${self.cost_usd:.4f} of ${self.limit_usd:.2f} "
                f"in {self.calls} calls. Raise MIRAG_BUDGET_USD to continue."
            )

    def snapshot(self) -> BudgetSnapshot:
        return BudgetSnapshot(self.cost_usd, self.calls, self.tokens)

    def __str__(self) -> str:
        cap = f"of ${self.limit_usd:.2f}" if self.capped else "no cap"
        return f"{self.calls} calls · {self.tokens:,} tokens · ${self.cost_usd:.4f} {cap}"
