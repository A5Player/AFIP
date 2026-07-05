"""Portfolio quality assessment for AFIP Production Milestone A Pack 12."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for portfolio assessment."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class PortfolioQualityResult:
    """Portfolio quality output for production readiness integration."""

    quality_score: float
    status: str
    allocation_policy: str
    reason: str


class PortfolioQualityAssessment:
    """Assess portfolio quality using financial exposure and capital metrics."""

    def assess(self, metrics: Mapping[str, float]) -> PortfolioQualityResult:
        """Return portfolio quality and allocation policy."""
        capital_efficiency = _ratio(metrics.get("capital_efficiency", 0.50))
        exposure_balance = _ratio(metrics.get("exposure_balance", 0.50))
        liquidity_quality = _ratio(metrics.get("liquidity_quality", 0.50))
        return_consistency = _ratio(metrics.get("return_consistency", 0.50))
        concentration_pressure = _ratio(metrics.get("concentration_pressure", 0.50))

        base_score = (
            capital_efficiency * 0.24
            + exposure_balance * 0.22
            + liquidity_quality * 0.20
            + return_consistency * 0.20
            + (1.0 - concentration_pressure) * 0.14
        )
        quality_score = _ratio(base_score)

        if quality_score >= 0.78 and concentration_pressure <= 0.30:
            status = "PORTFOLIO_QUALITY_READY"
            allocation_policy = "BALANCED_ALLOCATION_ELIGIBLE"
            reason = "portfolio_quality_supports_balanced_allocation"
        elif quality_score >= 0.58:
            status = "PORTFOLIO_QUALITY_STABLE"
            allocation_policy = "MAINTAIN_CURRENT_ALLOCATION"
            reason = "portfolio_quality_supports_current_allocation"
        else:
            status = "PORTFOLIO_QUALITY_REVIEW"
            allocation_policy = "REDUCE_ALLOCATION_PRESSURE"
            reason = "portfolio_quality_requires_capital_preservation"

        return PortfolioQualityResult(
            quality_score=round(quality_score, 4),
            status=status,
            allocation_policy=allocation_policy,
            reason=reason,
        )
