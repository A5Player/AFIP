"""Production Milestone A Pack 5: portfolio exposure allocator.

Additive portfolio allocation intelligence for Milestone A.
The module uses international financial terminology only and does not alter
existing runtime contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class PortfolioExposureAllocationResult:
    """Portfolio exposure allocation derived from risk budget and execution quality."""

    status: str
    allocation_status: str
    exposure_units: int
    exposure_multiplier: float
    capital_fraction: float
    execution_adjusted: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "portfolio_exposure_allocation_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "allocation_status": self.allocation_status,
            "exposure_units": self.exposure_units,
            "exposure_multiplier": round(self.exposure_multiplier, 4),
            "capital_fraction": round(self.capital_fraction, 4),
            "execution_adjusted": self.execution_adjusted,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class PortfolioExposureAllocator:
    """Calculates conservative portfolio allocation for production runtime use."""

    def __init__(self, base_capital_fraction: float = 0.01) -> None:
        self.base_capital_fraction = float(base_capital_fraction)

    def allocate(
        self,
        risk_budget: Mapping[str, Any],
        execution_quality: Mapping[str, Any] | None = None,
        portfolio_state: Mapping[str, Any] | None = None,
    ) -> PortfolioExposureAllocationResult:
        execution_quality = execution_quality or {}
        portfolio_state = portfolio_state or {}

        budget_status = str(risk_budget.get("status", "OBSERVE")).upper()
        budget_multiplier = float(risk_budget.get("risk_budget_multiplier", 0.0))
        maximum_units = int(risk_budget.get("maximum_allocation_units", 0))
        execution_score = float(execution_quality.get("execution_quality_score", 0.0))
        open_exposure = float(portfolio_state.get("open_exposure", 0.0))
        maximum_exposure = float(portfolio_state.get("maximum_exposure", 1.0))

        blockers: list[str] = []
        if budget_status != "READY":
            blockers.append("risk_budget_not_ready")
        if budget_multiplier <= 0.0 or maximum_units <= 0:
            blockers.append("zero_risk_budget")
        if execution_quality and execution_score < 55.0:
            blockers.append("low_execution_quality")
        if maximum_exposure <= 0.0 or open_exposure >= maximum_exposure:
            blockers.append("portfolio_exposure_limit_reached")

        if blockers:
            return PortfolioExposureAllocationResult(
                status="OBSERVE",
                allocation_status="PROTECTED",
                exposure_units=0,
                exposure_multiplier=0.0,
                capital_fraction=0.0,
                execution_adjusted=bool(execution_quality),
                blockers=blockers,
                reason="portfolio_exposure_allocation_protected",
            )

        execution_adjustment = 1.0
        execution_adjusted = False
        if execution_quality:
            execution_adjusted = True
            if execution_score >= 85.0:
                execution_adjustment = 1.0
            elif execution_score >= 70.0:
                execution_adjustment = 0.75
            else:
                execution_adjustment = 0.5

        available_ratio = max(0.0, min(1.0, (maximum_exposure - open_exposure) / maximum_exposure))
        exposure_multiplier = min(1.0, budget_multiplier * execution_adjustment * available_ratio)
        exposure_units = 1 if exposure_multiplier > 0.0 else 0
        capital_fraction = self.base_capital_fraction * exposure_multiplier

        allocation_status = "STANDARD" if exposure_multiplier >= 0.95 else "REDUCED"
        return PortfolioExposureAllocationResult(
            status="READY",
            allocation_status=allocation_status,
            exposure_units=min(exposure_units, maximum_units),
            exposure_multiplier=exposure_multiplier,
            capital_fraction=capital_fraction,
            execution_adjusted=execution_adjusted,
            blockers=[],
            reason="portfolio_exposure_allocation_ready",
        )
