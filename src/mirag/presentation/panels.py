"""JSON panels for the page. Data, not markdown: the page draws them and tests check them
without parsing HTML."""

from __future__ import annotations

import json
import re
from typing import Any

from mirag.evidence.properties import PropertyStatus
from mirag.i18n.catalog import MessageCatalog
from mirag.llm.budget import BudgetSnapshot
from mirag.pipeline.models import PipelineRun, Step

INTERNAL_RETRIEVAL_STAGE = re.compile(r"^(filter|bm25|vector|rrf|reranker):")


class StepSerializer:
    """A pipeline step as a JSON event."""

    @staticmethod
    def to_event(step: Step) -> dict[str, Any]:
        detail = step.detail
        if isinstance(detail, list | tuple):
            detail = [list(item) if isinstance(item, tuple) else item for item in detail]
        try:
            json.dumps(detail)
        except (TypeError, ValueError):
            detail = str(detail)[:2000]
        return {"type": "step", "name": step.name, "status": step.status.value, "summary": step.summary,
                "ms": round(step.ms, 1), "source": step.source.value if step.source else "", "detail": detail}


class EvidencePanelPresenter:
    """The four layers, separated on purpose. It is the centre of the product.

        MODEL CLAIM    what the model said it would cover
        OBSERVED       what Mirag saw when running: command, exit code, markers
        VERIFIED       what was declared AND the execution proved
        NOT VERIFIED   what was declared and the execution did NOT prove

    Mixing them in one table was for a long time how a model claim looked like a fact. Here
    they cannot be confused because they do not share a place.
    """

    def present(self, run: PipelineRun, catalog: MessageCatalog) -> dict[str, Any]:
        rows = list(run.evidence or [])
        execution = run.execution
        observed: dict[str, Any] | None = None
        if execution is not None:
            observed = {"status": execution.status.value, "header": execution.describe(catalog),
                        "markers": dict(execution.markers), "passed": execution.passed,
                        "failed": execution.failed, "truncated": execution.truncated}
        elif run.delivery:
            observed = {"status": "not_executed", "header": catalog.t("panel.delivered_not_executed")}
        return {
            "claim": [r.public() for r in rows],
            "observed": observed,
            "verified": [r.public() for r in rows if r.status is PropertyStatus.VERIFIED],
            "simulated": [r.public() for r in rows if r.status is PropertyStatus.VERIFIED_IN_SIMULATION],
            "not_verified": [r.public() for r in rows
                             if r.status in (PropertyStatus.UNVERIFIED, PropertyStatus.REFUTED)],
            # what the model admitted not covering: it is ITS claim, it goes with its claims
            "uncovered": [str(x) for x in ((run.delivery or {}).get("uncovered") or [])],
        }


class TimelinePresenter:
    """A run, in human language. The trace has thirty fields; this has a handful of rows.

    The internal retrieval stages fold into one: fifteen ``bm25:`` and ``rrf:`` rows do not
    tell the story of what happened, they hide it.
    """

    def present(self, run: PipelineRun) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        elapsed = 0.0
        retrieval_ms = sum(s.ms for s in run.steps if INTERNAL_RETRIEVAL_STAGE.match(s.name))
        for step in run.steps:
            if INTERNAL_RETRIEVAL_STAGE.match(step.name):
                continue
            ms = step.ms + (retrieval_ms if step.name == "retrieval" else 0.0)
            elapsed += ms
            rows.append({"t": round(elapsed / 1000, 2), "ms": round(ms, 1), "stage": step.name,
                         "status": step.status.value, "summary": step.summary,
                         "source": step.source.value if step.source else ""})
        return rows


class CostPresenter:
    """Without false precision: a double costs nothing and says so, it is not dressed as $0.0000."""

    def present(self, run: PipelineRun, spent: BudgetSnapshot, catalog: MessageCatalog,
                demo: str | None = None, model: str = "") -> dict[str, Any]:
        if run.simulated:
            # A demo has a script and answers; without a demo there was no decision at all.
            # Saying "it came from a script" when there was no script would be inventing.
            return {"simulated": True, "demo": demo, "calls": 0,
                    "text": catalog.t("cost.simulated") if demo else catalog.t("cost.no_model")}
        if spent.calls and spent.cost_usd == 0:
            # Real calls reporting exactly 0: a free model (the provider sends no cost). "$0.0000"
            # would suggest a spend measurement nobody made. It is free, and it says of what.
            return {"simulated": False, "free": True, "model": model, "text": catalog.t("cost.free", model=model),
                    "calls": spent.calls, "tokens": spent.tokens}
        return {"simulated": False, "free": False, "text": f"${spent.cost_usd:.4f}", "calls": spent.calls,
                "tokens": spent.tokens}
