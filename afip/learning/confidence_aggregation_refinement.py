"""Production Milestone A Pack 10: confidence aggregation refinement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class ConfidenceAggregationRefinementResult:
    """Refined confidence result for adaptive production decisions."""

    status: str
    optimization_allowed: bool
    refined_confidence: float
    aggregation_state: str
    entry_confidence: float
    position_confidence: float
    regime_confidence: float
    learning_confidence: float
    risk_adjustment: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "confidence_aggregation_refinement_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "optimization_allowed": self.optimization_allowed,
            "refined_confidence": round(self.refined_confidence, 2),
            "aggregation_state": self.aggregation_state,
            "entry_confidence": round(self.entry_confidence, 2),
            "position_confidence": round(self.position_confidence, 2),
            "regime_confidence": round(self.regime_confidence, 2),
            "learning_confidence": round(self.learning_confidence, 2),
            "risk_adjustment": round(self.risk_adjustment, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ConfidenceAggregationRefinement:
    """Refine decision confidence using entry, position, regime, learning, and risk evidence."""

    def evaluate(self, confidence_state: Mapping[str, Any]) -> ConfidenceAggregationRefinementResult:
        entry_confidence = _bounded(confidence_state.get("entry_confidence", confidence_state.get("entry_score", 50.0)))
        position_confidence = _bounded(confidence_state.get("position_confidence", 50.0))
        regime_confidence = _bounded(confidence_state.get("regime_confidence", confidence_state.get("regime_score", 50.0)))
        learning_confidence = _bounded(confidence_state.get("learning_confidence", confidence_state.get("learning_score", 50.0)))
        risk_adjustment = _bounded(confidence_state.get("risk_adjustment", 100.0))

        raw_confidence = (
            entry_confidence * 0.32
            + position_confidence * 0.25
            + regime_confidence * 0.20
            + learning_confidence * 0.13
            + risk_adjustment * 0.10
        )
        refined_confidence = raw_confidence * (0.70 + risk_adjustment / 333.34)
        refined_confidence = max(0.0, min(100.0, refined_confidence))

        blockers: list[str] = []
        if entry_confidence < 58.0:
            blockers.append("entry_confidence_below_aggregation_threshold")
        if position_confidence < 55.0:
            blockers.append("position_confidence_below_aggregation_threshold")
        if regime_confidence < 52.0:
            blockers.append("regime_confidence_below_aggregation_threshold")
        if risk_adjustment < 45.0:
            blockers.append("risk_adjustment_below_aggregation_threshold")

        optimization_allowed = refined_confidence >= 62.0 and not blockers
        if refined_confidence >= 84.0:
            aggregation_state = "HIGH_CONFIDENCE"
        elif refined_confidence >= 62.0:
            aggregation_state = "STANDARD_CONFIDENCE"
        else:
            aggregation_state = "LOW_CONFIDENCE"

        return ConfidenceAggregationRefinementResult(
            status="READY" if optimization_allowed else "OBSERVE",
            optimization_allowed=optimization_allowed,
            refined_confidence=refined_confidence,
            aggregation_state=aggregation_state,
            entry_confidence=entry_confidence,
            position_confidence=position_confidence,
            regime_confidence=regime_confidence,
            learning_confidence=learning_confidence,
            risk_adjustment=risk_adjustment,
            blockers=blockers,
            reason="confidence_aggregation_ready" if optimization_allowed else "confidence_aggregation_observation_required",
        )


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 50.0
    return max(0.0, min(100.0, numeric))
