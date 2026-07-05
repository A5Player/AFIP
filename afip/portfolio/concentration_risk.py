"""Portfolio concentration risk evaluation for production controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ConcentrationRiskResult:
    """Concentration evaluation result across position values."""

    status: str
    position_count: int
    total_exposure: float
    largest_position_value: float
    largest_position_ratio: float
    maximum_position_ratio: float
    within_limit: bool
    reason: str


class ConcentrationRisk:
    """Evaluate whether one position dominates portfolio exposure."""

    def evaluate(self, positions: Iterable[Mapping[str, object]], limits: Mapping[str, object] | None = None) -> ConcentrationRiskResult:
        limits = limits or {}
        values = [abs(self._number(position.get("market_value", position.get("value", 0.0)))) for position in positions]
        maximum_ratio = self._number(limits.get("maximum_position_ratio"), 0.6)
        if not values:
            return ConcentrationRiskResult("CONCENTRATION_RISK_REVIEW", 0, 0.0, 0.0, 0.0, maximum_ratio, False, "no_positions_available")
        total = round(sum(values), 8)
        if total <= 0:
            return ConcentrationRiskResult("CONCENTRATION_RISK_REVIEW", len(values), total, 0.0, 0.0, maximum_ratio, False, "total_exposure_not_positive")
        largest = round(max(values), 8)
        ratio = round(largest / total, 8)
        if ratio > maximum_ratio:
            return ConcentrationRiskResult("CONCENTRATION_RISK_REVIEW", len(values), total, largest, ratio, maximum_ratio, False, "largest_position_ratio_above_limit")
        return ConcentrationRiskResult("CONCENTRATION_RISK_READY", len(values), total, largest, ratio, maximum_ratio, True, "concentration_risk_ready")

    @staticmethod
    def _number(value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
