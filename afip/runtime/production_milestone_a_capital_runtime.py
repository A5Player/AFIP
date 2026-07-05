"""Production Milestone A Pack 7: capital-aware runtime integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.capital_preservation_index import CapitalPreservationIndex
from afip.intelligence.market_participation_quality import MarketParticipationQuality
from afip.learning.learning_confidence_interval import LearningConfidenceInterval
from afip.runtime.production_milestone_a_maturity_runtime import ProductionMilestoneAMaturityRuntime


@dataclass(frozen=True)
class ProductionMilestoneACapitalRuntimeResult:
    """Integrated Pack 7 result for capital-aware production decisions."""

    status: str
    production_allowed: bool
    action: str
    confidence: float
    capital_state: str
    participation_state: str
    confidence_state: str
    maturity_runtime: Dict[str, Any]
    capital_preservation: Dict[str, Any]
    market_participation: Dict[str, Any]
    learning_confidence: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "production_milestone_a_capital_runtime_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "capital_state": self.capital_state,
            "participation_state": self.participation_state,
            "confidence_state": self.confidence_state,
            "maturity_runtime": dict(self.maturity_runtime),
            "capital_preservation": dict(self.capital_preservation),
            "market_participation": dict(self.market_participation),
            "learning_confidence": dict(self.learning_confidence),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneACapitalRuntime:
    """Additive runtime combining maturity, capital, participation, and learning quality."""

    def __init__(self) -> None:
        self.maturity_runtime = ProductionMilestoneAMaturityRuntime()
        self.capital_preservation = CapitalPreservationIndex()
        self.market_participation = MarketParticipationQuality()
        self.learning_confidence = LearningConfidenceInterval()

    def evaluate(self, context: Mapping[str, Any]) -> ProductionMilestoneACapitalRuntimeResult:
        maturity = self.maturity_runtime.evaluate(context).to_dict()
        capital = self.capital_preservation.evaluate(context.get("portfolio_state", {})).to_dict()
        participation = self.market_participation.evaluate(context.get("execution_state", {})).to_dict()
        learning = self.learning_confidence.evaluate(context.get("learning_samples", [])).to_dict()

        blockers: list[str] = []
        if not maturity["production_allowed"]:
            blockers.extend(f"maturity_runtime:{item}" for item in maturity.get("blockers", []))
        if not capital["production_ready"]:
            blockers.extend(f"capital_preservation:{item}" for item in capital.get("blockers", []))
        if not participation["production_ready"]:
            blockers.extend(f"market_participation:{item}" for item in participation.get("blockers", []))
        if not learning["optimization_allowed"]:
            blockers.extend(f"learning_confidence:{item}" for item in learning.get("blockers", []))

        production_allowed = not blockers and maturity["production_allowed"]
        if production_allowed:
            confidence = min(
                float(maturity.get("confidence", 0.0)),
                float(capital.get("preservation_score", 0.0)),
                float(participation.get("participation_score", 0.0)),
                float(learning.get("confidence_interval_score", 0.0)),
            )
            action = maturity["action"]
        else:
            confidence = min(float(maturity.get("confidence", 0.0)), 50.0)
            action = "HOLD"

        return ProductionMilestoneACapitalRuntimeResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=action,
            confidence=confidence,
            capital_state=capital["capital_state"],
            participation_state=participation["participation_state"],
            confidence_state=learning["confidence_state"],
            maturity_runtime=maturity,
            capital_preservation=capital,
            market_participation=participation,
            learning_confidence=learning,
            blockers=blockers,
            reason="production_milestone_a_capital_runtime_ready" if production_allowed else "production_milestone_a_capital_runtime_observation_required",
        )
