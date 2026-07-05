"""Portfolio exposure limit evaluation for production portfolio controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ExposureLimitResult:
    """Exposure limit evaluation result."""

    status: str
    gross_exposure: float
    equity: float
    exposure_ratio: float
    maximum_exposure_ratio: float
    within_limit: bool
    reason: str


class ExposureLimit:
    """Evaluate gross exposure relative to portfolio equity."""

    def evaluate(self, gross_exposure: float, equity: float, limits: Mapping[str, object] | None = None) -> ExposureLimitResult:
        limits = limits or {}
        gross_value = round(abs(float(gross_exposure or 0.0)), 8)
        equity_value = round(float(equity or 0.0), 8)
        maximum_ratio = self._number(limits.get("maximum_exposure_ratio"), 1.5)
        if equity_value <= 0:
            return ExposureLimitResult("EXPOSURE_LIMIT_REVIEW", gross_value, equity_value, 0.0, maximum_ratio, False, "equity_not_positive")
        exposure_ratio = round(gross_value / equity_value, 8)
        if exposure_ratio > maximum_ratio:
            return ExposureLimitResult("EXPOSURE_LIMIT_REVIEW", gross_value, equity_value, exposure_ratio, maximum_ratio, False, "exposure_ratio_above_limit")
        return ExposureLimitResult("EXPOSURE_LIMIT_READY", gross_value, equity_value, exposure_ratio, maximum_ratio, True, "exposure_limit_ready")

    @staticmethod
    def _number(value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
