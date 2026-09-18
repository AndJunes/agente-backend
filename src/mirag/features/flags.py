"""One place for every pipeline switch, and the gate that decides whether a stage runs.

Two kinds of stage, treated differently on purpose:

``CORE``
    On unless you switch it off. It is the brain of retrieval.
``CONDITIONAL``
    In ``auto`` the decision is not mine: measurement decides. A stage nobody measured is
    born off, and one that measures worse than it costs switches itself off. The policy is
    written by the benchmarks into ``resources/feature_gains.json``, not by this file.

Every switch accepts ``on`` / ``off`` / ``auto`` through ``MIRAG_<NAME>``.

A flag nobody reads is a lie about what can be configured: you set ``MIRAG_X=on``, nothing
happens, and nothing tells you. So each flag declares what it is really wired to, and a
test flips each one and checks that something changes.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from mirag.i18n.catalog import MessageCatalog
from mirag.paths import FEATURE_GAINS_FILE

ENV_PREFIX = "MIRAG_"
MRR_THRESHOLD = 0.02
"""Below this a gain is noise, not an improvement."""


class FlagMode(StrEnum):
    ON = "on"
    OFF = "off"
    AUTO = "auto"


class FlagStatus(StrEnum):
    WIRED = "wired"
    """Changing it changes what the pipeline does."""
    EXPERIMENTAL = "experimental"
    """The module exists and works, but it is not on the production path."""
    NOT_IMPLEMENTED = "not_implemented"
    """There is no code behind it."""


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    name: str
    default_mode: FlagMode
    status: FlagStatus

    @property
    def env_var(self) -> str:
        return ENV_PREFIX + self.name.upper()


FEATURES: dict[str, FeatureSpec] = {
    spec.name: spec
    for spec in (
        # core: on unless switched off
        FeatureSpec("retrieval_plan", FlagMode.ON, FlagStatus.WIRED),
        FeatureSpec("metadata_routing", FlagMode.ON, FlagStatus.WIRED),
        FeatureSpec("hybrid_retrieval", FlagMode.ON, FlagStatus.WIRED),
        FeatureSpec("symbol_retrieval", FlagMode.ON, FlagStatus.WIRED),
        FeatureSpec("sufficiency", FlagMode.ON, FlagStatus.WIRED),
        # conditional: in auto, the measured gains decide
        FeatureSpec("vector_signal", FlagMode.AUTO, FlagStatus.WIRED),
        FeatureSpec("reranker", FlagMode.AUTO, FlagStatus.WIRED),
        FeatureSpec("graph_retrieval", FlagMode.AUTO, FlagStatus.WIRED),
        FeatureSpec("model_routing", FlagMode.AUTO, FlagStatus.EXPERIMENTAL),
        FeatureSpec("semantic_cache", FlagMode.AUTO, FlagStatus.EXPERIMENTAL),
        FeatureSpec("knowledge_tree", FlagMode.AUTO, FlagStatus.EXPERIMENTAL),
        FeatureSpec("contextual_chunks", FlagMode.AUTO, FlagStatus.NOT_IMPLEMENTED),
        FeatureSpec("colbert", FlagMode.OFF, FlagStatus.NOT_IMPLEMENTED),
    )
}


@dataclass(frozen=True, slots=True)
class GateDecision:
    """Whether a stage runs, and why. The reason matters as much as the decision: the UI
    must be able to explain why Mirag did NOT use the reranker, and "not measured yet" is a
    legitimate answer."""

    enabled: bool
    code: str
    params: Mapping[str, Any] = field(default_factory=dict)

    def explain(self, catalog: MessageCatalog) -> str:
        return catalog.t(f"features.reason.{self.code}", **self.params)

    def __bool__(self) -> bool:
        return self.enabled


class GainsRepository:
    """Reads the measured gains per stage and query family. Never raises."""

    def __init__(self, path: Path = FEATURE_GAINS_FILE) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}  # no measurements: everything in 'auto' stays off
        return data if isinstance(data, dict) else {}


class FeatureGate:
    """Decides, for each stage, whether it runs. Stateless apart from its inputs."""

    def __init__(self, env: Mapping[str, str], gains: GainsRepository | None = None) -> None:
        self._env = env
        self._gains = gains or GainsRepository()

    # ── modes ────────────────────────────────────────────────────────────────

    def spec(self, stage: str) -> FeatureSpec | None:
        return FEATURES.get(stage.lower())

    def mode(self, stage: str) -> FlagMode:
        spec = self.spec(stage)
        default = spec.default_mode if spec else FlagMode.AUTO
        raw = self._env.get(ENV_PREFIX + stage.upper())
        if raw is None:
            return default
        try:
            return FlagMode(raw.strip().lower())
        except ValueError:
            return default

    def set_by_hand(self, stage: str) -> bool:
        """Distinguish what you asked for from what comes by default."""
        return (ENV_PREFIX + stage.upper()) in self._env

    # ── the decision ─────────────────────────────────────────────────────────

    def decide(
        self,
        stage: str,
        family: str = "general",
        gains: Mapping[str, Any] | None = None,
    ) -> GateDecision:
        spec = self.spec(stage)
        var = ENV_PREFIX + stage.upper()
        if spec is None or spec.status is FlagStatus.NOT_IMPLEMENTED:
            # No code behind it: switching it on would print "ON" in the trace and a UI
            # that claims something that does not happen. It never starts, not even by hand.
            return GateDecision(False, "not_implemented", {"stage": stage})
        mode = self.mode(stage)
        by_hand = self.set_by_hand(stage)
        if spec.status is FlagStatus.EXPERIMENTAL:
            # It can be tried on purpose (MIRAG_X=on) but never switches itself on: a good
            # measurement is not enough when the module is off the production path. That
            # includes MIRAG_X=auto written by hand: 'auto' hands the decision to the
            # measurement, which is exactly what may not switch it on.
            if by_hand and mode is FlagMode.ON:
                return GateDecision(True, "experimental_forced_on", {"stage": stage, "var": var})
            if by_hand and mode is FlagMode.OFF:
                return GateDecision(False, "forced_off", {"var": var})
            return GateDecision(False, "experimental", {"stage": stage})
        if mode is FlagMode.ON:
            return GateDecision(True, "forced_on" if by_hand else "core_always_on", {"var": var})
        if mode is FlagMode.OFF:
            return GateDecision(False, "forced_off" if by_hand else "off_by_default", {"var": var})
        return self._measured(stage, family, self._gains.load() if gains is None else gains)

    def _measured(self, stage: str, family: str, table: Mapping[str, Any]) -> GateDecision:
        # An unreadable policy, or one whose shape changed, can NOT switch anything on:
        # when in doubt, off. Same criterion as "not measured".
        try:
            entry = table.get(stage) or {}
            measured = entry.get(family) or entry.get("general")
        except AttributeError:
            return GateDecision(False, "unreadable_measurement")
        if measured is None:
            return GateDecision(False, "not_measured")
        try:
            delta = float(measured["delta_mrr"])
            cost = float(measured.get("normalized_cost", 0.0))
        except (AttributeError, TypeError, KeyError, ValueError):
            return GateDecision(False, "unreadable_measurement")
        if not (math.isfinite(delta) and math.isfinite(cost)):
            # Python's json reads NaN and Infinity, and NaN fails every comparison below:
            # it slipped through both thresholds and switched the stage ON.
            return GateDecision(False, "unreadable_measurement")
        params = {"delta": f"{delta:+.3f}", "cost": f"{cost:.3f}", "threshold": MRR_THRESHOLD}
        if delta < MRR_THRESHOLD:
            return GateDecision(False, "below_threshold", params)
        if delta <= cost:
            return GateDecision(False, "not_worth_cost", params)
        return GateDecision(True, "measured_gain", params)

    # ── reporting ────────────────────────────────────────────────────────────

    def summary(self) -> dict[str, GateDecision]:
        """For reports and the UI: the state of every switch."""
        return {name: self.decide(name) for name in FEATURES}

    def dead_flag_warnings(self) -> list[tuple[str, FlagStatus]]:
        """``MIRAG_X`` set by hand on a flag that does nothing: that must be said."""
        return [
            (spec.env_var, spec.status)
            for spec in FEATURES.values()
            if spec.status is not FlagStatus.WIRED and spec.env_var in self._env
        ]
