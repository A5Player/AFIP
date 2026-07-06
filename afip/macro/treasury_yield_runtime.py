"""Treasury yield assessment for gold macro context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class TreasuryYieldAssessment:
    """Treasury yield movement and curve assessment."""

    status: str
    direction: str
    pressure_score: float
    us02y_change_bps: float
    us10y_change_bps: float
    curve_change_bps: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "direction": self.direction,
            "pressure_score": self.pressure_score,
            "us02y_change_bps": self.us02y_change_bps,
            "us10y_change_bps": self.us10y_change_bps,
            "curve_change_bps": self.curve_change_bps,
            "reason": self.reason,
        }


class TreasuryYieldRuntime:
    """Assess yield movement as supportive, pressure, or neutral for gold."""

    def assess(self, factors: Mapping[str, object] | None = None) -> TreasuryYieldAssessment:
        factors = factors or {}
        us02y = self._to_float(factors.get("us02y_change_bps"))
        us10y = self._to_float(factors.get("us10y_change_bps"))
        curve = us10y - us02y
        weighted_yield = (us10y * 0.70) + (us02y * 0.30)
        if weighted_yield <= -5.0:
            return TreasuryYieldAssessment("TREASURY_YIELD_READY", "GOLD_SUPPORTIVE", 76.0, us02y, us10y, round(curve, 3), "treasury_yield_decline_supports_gold")
        if weighted_yield >= 5.0:
            return TreasuryYieldAssessment("TREASURY_YIELD_READY", "GOLD_PRESSURE", 76.0, us02y, us10y, round(curve, 3), "treasury_yield_increase_pressures_gold")
        return TreasuryYieldAssessment("TREASURY_YIELD_READY", "NEUTRAL", 50.0, us02y, us10y, round(curve, 3), "treasury_yield_balanced")

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
