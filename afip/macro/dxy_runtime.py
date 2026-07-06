"""DXY factor assessment for gold macro context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class DxyAssessment:
    """Dollar Index assessment used by the gold macro layer."""

    status: str
    direction: str
    pressure_score: float
    change_percent: float
    momentum_percent: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "direction": self.direction,
            "pressure_score": self.pressure_score,
            "change_percent": self.change_percent,
            "momentum_percent": self.momentum_percent,
            "reason": self.reason,
        }


class DxyRuntime:
    """Assess whether dollar movement supports or pressures gold."""

    def assess(self, factors: Mapping[str, object] | None = None) -> DxyAssessment:
        factors = factors or {}
        change = self._to_float(factors.get("dxy_change_percent"))
        momentum = self._to_float(factors.get("dxy_momentum_percent"), fallback=change)
        composite = (change * 0.65) + (momentum * 0.35)
        if composite <= -0.25:
            return DxyAssessment("DXY_READY", "GOLD_SUPPORTIVE", 82.0, change, momentum, "dxy_softness_supports_gold")
        if composite >= 0.25:
            return DxyAssessment("DXY_READY", "GOLD_PRESSURE", 82.0, change, momentum, "dxy_strength_pressures_gold")
        return DxyAssessment("DXY_READY", "NEUTRAL", 50.0, change, momentum, "dxy_balanced")

    @staticmethod
    def _to_float(value: object, fallback: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback
