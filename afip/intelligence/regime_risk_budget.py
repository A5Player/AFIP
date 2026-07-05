"""Production Milestone A Pack 4: market regime risk budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class RegimeRiskBudgetResult:
    """Risk budget derived from current market regime quality."""

    status: str
    risk_budget_level: str
    risk_budget_multiplier: float
    maximum_allocation_units: int
    review_required: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "regime_risk_budget_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "risk_budget_level": self.risk_budget_level,
            "risk_budget_multiplier": round(self.risk_budget_multiplier, 4),
            "maximum_allocation_units": self.maximum_allocation_units,
            "review_required": self.review_required,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class RegimeRiskBudget:
    """Converts regime, transition, and cost quality into a conservative risk budget."""

    def evaluate(
        self,
        market_regime: Mapping[str, Any],
        exposure_control: Mapping[str, Any] | None = None,
        learning_stability: Mapping[str, Any] | None = None,
    ) -> RegimeRiskBudgetResult:
        exposure_control = exposure_control or {}
        learning_stability = learning_stability or {}
        regime = str(market_regime.get("regime", "UNKNOWN")).upper()
        confidence = float(market_regime.get("confidence", 0.0))
        exposure_multiplier = float(exposure_control.get("exposure_multiplier", 0.0))
        stability_score = float(learning_stability.get("stability_score", 0.0))

        blockers: list[str] = []
        if regime in {"HIGH_VOLATILITY", "RANGE", "UNKNOWN"}:
            blockers.append("protective_market_regime")
        if confidence < 60.0:
            blockers.append("low_regime_confidence")
        if exposure_multiplier <= 0.0:
            blockers.append("zero_exposure_control")
        if learning_stability and stability_score < 60.0:
            blockers.append("low_learning_stability")

        if blockers:
            return RegimeRiskBudgetResult(
                status="OBSERVE",
                risk_budget_level="PROTECTED",
                risk_budget_multiplier=0.0,
                maximum_allocation_units=0,
                review_required=True,
                blockers=blockers,
                reason="regime_risk_budget_protected",
            )

        if regime == "TRENDING" and confidence >= 78.0 and stability_score >= 75.0 and exposure_multiplier >= 1.0:
            return RegimeRiskBudgetResult("READY", "STANDARD", 1.0, 1, False, [], "regime_risk_budget_standard")

        return RegimeRiskBudgetResult("READY", "REDUCED", 0.5, 1, True, [], "regime_risk_budget_reduced")
