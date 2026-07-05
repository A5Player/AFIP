"""Production Milestone A Pack 4: adaptive optimization parameter governor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class OptimizationParameterGovernorResult:
    """Governed parameter set for adaptive learning and optimization."""

    status: str
    entry_threshold: float
    position_threshold: float
    learning_rate: float
    adjustment_limit: float
    approved: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "optimization_parameter_governor_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "entry_threshold": round(self.entry_threshold, 2),
            "position_threshold": round(self.position_threshold, 2),
            "learning_rate": round(self.learning_rate, 4),
            "adjustment_limit": round(self.adjustment_limit, 2),
            "approved": self.approved,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class OptimizationParameterGovernor:
    """Keeps adaptive optimization bounded for production compatibility."""

    def govern(self, parameters: Mapping[str, Any], stability: Mapping[str, Any], risk_budget: Mapping[str, Any]) -> OptimizationParameterGovernorResult:
        entry_threshold = float(parameters.get("entry_threshold", 70.0))
        position_threshold = float(parameters.get("position_threshold", 62.0))
        learning_rate = float(parameters.get("learning_rate", 0.05))
        requested_adjustment = abs(float(parameters.get("requested_adjustment", 0.0)))
        stability_score = float(stability.get("stability_score", 0.0))
        risk_multiplier = float(risk_budget.get("risk_budget_multiplier", 0.0))

        blockers: list[str] = []
        if not 50.0 <= entry_threshold <= 90.0:
            blockers.append("entry_threshold_out_of_bounds")
        if not 45.0 <= position_threshold <= 90.0:
            blockers.append("position_threshold_out_of_bounds")
        if not 0.0 < learning_rate <= 0.2:
            blockers.append("learning_rate_out_of_bounds")
        if stability_score < 60.0:
            blockers.append("insufficient_stability_for_optimization")
        if risk_multiplier <= 0.0:
            blockers.append("risk_budget_not_available")

        adjustment_limit = 2.0 if stability_score >= 75.0 and risk_multiplier >= 1.0 else 1.0
        if requested_adjustment > adjustment_limit:
            blockers.append("requested_adjustment_exceeds_limit")

        approved = not blockers
        return OptimizationParameterGovernorResult(
            status="READY" if approved else "OBSERVE",
            entry_threshold=entry_threshold,
            position_threshold=position_threshold,
            learning_rate=learning_rate if approved else min(max(learning_rate, 0.01), 0.05),
            adjustment_limit=adjustment_limit,
            approved=approved,
            blockers=blockers,
            reason="optimization_parameters_approved" if approved else "optimization_parameters_protected",
        )
