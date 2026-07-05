"""Production Milestone A Pack 8: efficiency-aware runtime integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.allocation_discipline_index import AllocationDisciplineIndex
from afip.intelligence.liquidity_efficiency_index import LiquidityEfficiencyIndex
from afip.learning.learning_efficiency_score import LearningEfficiencyScore
from afip.runtime.production_milestone_a_capital_runtime import ProductionMilestoneACapitalRuntime


@dataclass(frozen=True)
class ProductionMilestoneAEfficiencyRuntimeResult:
    """Integrated Pack 8 result for efficiency-aware production decisions."""

    status: str
    production_allowed: bool
    action: str
    confidence: float
    liquidity_efficiency_state: str
    allocation_discipline_state: str
    learning_efficiency_state: str
    capital_runtime: Dict[str, Any]
    liquidity_efficiency: Dict[str, Any]
    allocation_discipline: Dict[str, Any]
    learning_efficiency: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "production_milestone_a_efficiency_runtime_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "liquidity_efficiency_state": self.liquidity_efficiency_state,
            "allocation_discipline_state": self.allocation_discipline_state,
            "learning_efficiency_state": self.learning_efficiency_state,
            "capital_runtime": dict(self.capital_runtime),
            "liquidity_efficiency": dict(self.liquidity_efficiency),
            "allocation_discipline": dict(self.allocation_discipline),
            "learning_efficiency": dict(self.learning_efficiency),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneAEfficiencyRuntime:
    """Additive runtime combining capital readiness with efficiency discipline."""

    def __init__(self) -> None:
        self.capital_runtime = ProductionMilestoneACapitalRuntime()
        self.liquidity_efficiency = LiquidityEfficiencyIndex()
        self.allocation_discipline = AllocationDisciplineIndex()
        self.learning_efficiency = LearningEfficiencyScore()

    def evaluate(self, context: Mapping[str, Any]) -> ProductionMilestoneAEfficiencyRuntimeResult:
        capital = self.capital_runtime.evaluate(context).to_dict()
        liquidity = self.liquidity_efficiency.evaluate(context.get("execution_state", {})).to_dict()
        allocation = self.allocation_discipline.evaluate(context.get("portfolio_state", {})).to_dict()
        learning = self.learning_efficiency.evaluate(context.get("learning_samples", [])).to_dict()

        blockers: list[str] = []
        if not capital["production_allowed"]:
            blockers.extend(f"capital_runtime:{item}" for item in capital.get("blockers", []))
        if not liquidity["production_ready"]:
            blockers.extend(f"liquidity_efficiency:{item}" for item in liquidity.get("blockers", []))
        if not allocation["production_ready"]:
            blockers.extend(f"allocation_discipline:{item}" for item in allocation.get("blockers", []))
        if not learning["optimization_allowed"]:
            blockers.extend(f"learning_efficiency:{item}" for item in learning.get("blockers", []))

        production_allowed = not blockers and capital["production_allowed"]
        if production_allowed:
            confidence = min(
                float(capital.get("confidence", 0.0)),
                float(liquidity.get("efficiency_score", 0.0)),
                float(allocation.get("discipline_score", 0.0)),
                float(learning.get("efficiency_score", 0.0)),
            )
            action = capital["action"]
        else:
            confidence = min(float(capital.get("confidence", 0.0)), 50.0)
            action = "HOLD"

        return ProductionMilestoneAEfficiencyRuntimeResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=action,
            confidence=confidence,
            liquidity_efficiency_state=liquidity["efficiency_state"],
            allocation_discipline_state=allocation["discipline_state"],
            learning_efficiency_state=learning["efficiency_state"],
            capital_runtime=capital,
            liquidity_efficiency=liquidity,
            allocation_discipline=allocation,
            learning_efficiency=learning,
            blockers=blockers,
            reason="production_milestone_a_efficiency_runtime_ready" if production_allowed else "production_milestone_a_efficiency_runtime_observation_required",
        )
