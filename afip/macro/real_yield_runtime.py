"""Real yield assessment for gold macro context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RealYieldAssessment:
    """Real yield change assessment used by gold macro scoring."""

    status: str
    direction: str
    pressure_score: float
    real_yield_change_bps: float
    estimated_real_yield_percent: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "direction": self.direction,
            "pressure_score": self.pressure_score,
            "real_yield_change_bps": self.real_yield_change_bps,
            "estimated_real_yield_percent": self.estimated_real_yield_percent,
            "reason": self.reason,
        }


class RealYieldRuntime:
    """Estimate and assess real yield pressure for gold."""

    def assess(self, factors: Mapping[str, object] | None = None) -> RealYieldAssessment:
        factors = factors or {}
        real_change = self._real_yield_change(factors)
        estimated_real_yield = self._estimated_real_yield(factors)
        if real_change <= -3.0:
            return RealYieldAssessment("REAL_YIELD_READY", "GOLD_SUPPORTIVE", 88.0, real_change, estimated_real_yield, "real_yield_decline_supports_gold")
        if real_change >= 3.0:
            return RealYieldAssessment("REAL_YIELD_READY", "GOLD_PRESSURE", 88.0, real_change, estimated_real_yield, "real_yield_increase_pressures_gold")
        return RealYieldAssessment("REAL_YIELD_READY", "NEUTRAL", 50.0, real_change, estimated_real_yield, "real_yield_balanced")

    def _real_yield_change(self, factors: Mapping[str, object]) -> float:
        explicit = factors.get("real_yield_change_bps")
        if explicit is not None:
            return self._to_float(explicit)
        nominal_change = self._to_float(factors.get("us10y_change_bps"))
        inflation_expectation_change = self._to_float(factors.get("inflation_expectation_change_bps"))
        return round(nominal_change - inflation_expectation_change, 3)

    def _estimated_real_yield(self, factors: Mapping[str, object]) -> float:
        explicit = factors.get("real_yield_percent")
        if explicit is not None:
            return self._to_float(explicit)
        nominal = self._to_float(factors.get("us10y_yield_percent"))
        inflation_expectation = self._to_float(factors.get("inflation_expectation_percent"))
        return round(nominal - inflation_expectation, 3)

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
