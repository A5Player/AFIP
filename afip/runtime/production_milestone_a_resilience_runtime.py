"""Production Milestone A Pack 9: resilience runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.execution_consistency_index import ExecutionConsistencyIndex
from afip.intelligence.portfolio_resilience_index import PortfolioResilienceIndex
from afip.learning.learning_resilience_score import LearningResilienceScore


@dataclass(frozen=True)
class ProductionMilestoneAResilienceRuntimeResult:
    """Combined runtime result for Pack 9 resilience evaluation."""

    status: str
    production_allowed: bool
    action: str
    resilience_score: float
    execution_consistency: Dict[str, Any]
    portfolio_resilience: Dict[str, Any]
    learning_resilience: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "production_milestone_a_resilience_runtime_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "resilience_score": round(self.resilience_score, 2),
            "execution_consistency": dict(self.execution_consistency),
            "portfolio_resilience": dict(self.portfolio_resilience),
            "learning_resilience": dict(self.learning_resilience),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneAResilienceRuntime:
    """Coordinate execution, portfolio, and learning resilience for production."""

    def evaluate(self, context: Mapping[str, Any]) -> ProductionMilestoneAResilienceRuntimeResult:
        execution_result = ExecutionConsistencyIndex().evaluate(context.get("execution_state", {})).to_dict()
        portfolio_result = PortfolioResilienceIndex().evaluate(context.get("portfolio_state", {})).to_dict()
        learning_result = LearningResilienceScore().evaluate(context.get("learning_samples", [])).to_dict()

        blockers: list[str] = []
        for name, result in (
            ("execution_consistency", execution_result),
            ("portfolio_resilience", portfolio_result),
            ("learning_resilience", learning_result),
        ):
            for blocker in result.get("blockers", []):
                blockers.append(f"{name}:{blocker}")

        resilience_score = (
            execution_result["consistency_score"] * 0.35
            + portfolio_result["resilience_score"] * 0.35
            + learning_result["resilience_score"] * 0.30
        )
        production_allowed = resilience_score >= 62.0 and not blockers
        action = _resolve_action(context, production_allowed)

        return ProductionMilestoneAResilienceRuntimeResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=action,
            resilience_score=resilience_score,
            execution_consistency=execution_result,
            portfolio_resilience=portfolio_result,
            learning_resilience=learning_result,
            blockers=blockers,
            reason="production_resilience_ready" if production_allowed else "production_resilience_observation_required",
        )


def _resolve_action(context: Mapping[str, Any], production_allowed: bool) -> str:
    if not production_allowed:
        return "HOLD"
    decision_quality = context.get("decision_quality", {})
    side = str(decision_quality.get("side", context.get("action", "BUY"))).upper()
    if side in {"BUY", "SELL"}:
        return side
    return "BUY"
