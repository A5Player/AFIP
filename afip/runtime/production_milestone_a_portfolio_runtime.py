"""Production Milestone A Pack 5: portfolio runtime integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.execution_quality_index import ExecutionQualityIndex
from afip.intelligence.portfolio_exposure_allocator import PortfolioExposureAllocator
from afip.learning.learning_feedback_index import LearningFeedbackIndex
from afip.runtime.production_milestone_a_production_control import ProductionMilestoneAProductionControl


@dataclass(frozen=True)
class ProductionMilestoneAPortfolioRuntimeResult:
    """Pack 5 integrated production result for portfolio-aware runtime decisions."""

    status: str
    production_allowed: bool
    action: str
    confidence: float
    allocation_status: str
    exposure_units: int
    capital_fraction: float
    production_control: Dict[str, Any]
    execution_quality: Dict[str, Any]
    learning_feedback: Dict[str, Any]
    portfolio_allocation: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "production_milestone_a_portfolio_runtime_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "allocation_status": self.allocation_status,
            "exposure_units": self.exposure_units,
            "capital_fraction": round(self.capital_fraction, 4),
            "production_control": dict(self.production_control),
            "execution_quality": dict(self.execution_quality),
            "learning_feedback": dict(self.learning_feedback),
            "portfolio_allocation": dict(self.portfolio_allocation),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneAPortfolioRuntime:
    """Additive Pack 5 runtime that combines production control with portfolio allocation."""

    def __init__(self) -> None:
        self.production_control = ProductionMilestoneAProductionControl()
        self.execution_quality = ExecutionQualityIndex()
        self.learning_feedback = LearningFeedbackIndex()
        self.exposure_allocator = PortfolioExposureAllocator()

    def evaluate(self, context: Mapping[str, Any]) -> ProductionMilestoneAPortfolioRuntimeResult:
        control = self.production_control.evaluate(context).to_dict()
        execution = self.execution_quality.evaluate({
            "cost_quality": context.get("cost_quality", {}),
            "liquidity_quality": context.get("liquidity_quality", {}),
            "decision_quality": {
                "confidence": control.get("confidence", 0.0),
                "signal_consistency": control.get("signal_audit", {}).get("side_consistency", 0.0),
            },
        }).to_dict()
        feedback = self.learning_feedback.evaluate(context.get("learning_samples", [])).to_dict()
        allocation = self.exposure_allocator.allocate(
            control.get("risk_budget", {}),
            execution,
            context.get("portfolio_state", {}),
        ).to_dict()

        blockers: list[str] = []
        if not control["production_allowed"]:
            blockers.extend(f"production_control:{item}" for item in control.get("blockers", []))
        if execution["status"] != "READY":
            blockers.extend(f"execution_quality:{item}" for item in execution.get("blockers", []))
        if feedback["status"] != "READY":
            blockers.extend(f"learning_feedback:{item}" for item in feedback.get("blockers", []))
        if allocation["status"] != "READY":
            blockers.extend(f"portfolio_allocation:{item}" for item in allocation.get("blockers", []))

        production_allowed = not blockers and control["production_allowed"] and allocation["exposure_units"] > 0
        return ProductionMilestoneAPortfolioRuntimeResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=control["action"] if production_allowed else "HOLD",
            confidence=control["confidence"] if production_allowed else min(float(control.get("confidence", 0.0)), 50.0),
            allocation_status=allocation["allocation_status"],
            exposure_units=allocation["exposure_units"] if production_allowed else 0,
            capital_fraction=allocation["capital_fraction"] if production_allowed else 0.0,
            production_control=control,
            execution_quality=execution,
            learning_feedback=feedback,
            portfolio_allocation=allocation,
            blockers=blockers,
            reason="production_milestone_a_portfolio_runtime_ready" if production_allowed else "production_milestone_a_portfolio_runtime_protective_observation",
        )
