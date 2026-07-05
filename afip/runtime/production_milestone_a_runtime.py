"""Production Milestone A4: Runtime Integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.adaptive_intelligence_core import AdaptiveIntelligenceCore
from afip.intelligence.market_regime_intelligence_v2 import MarketRegimeIntelligenceV2
from afip.learning.adaptive_learning_optimizer import AdaptiveLearningOptimizer


@dataclass(frozen=True)
class MilestoneARuntimeResult:
    status: str
    production_allowed: bool
    action: str
    confidence: float
    adaptive_intelligence: Dict[str, Any]
    market_regime: Dict[str, Any]
    learning_optimization: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "milestone_a_runtime_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "adaptive_intelligence": dict(self.adaptive_intelligence),
            "market_regime": dict(self.market_regime),
            "learning_optimization": dict(self.learning_optimization),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneARuntime:
    """Coordinates A1-A3 outputs without changing existing runtime contracts."""

    def __init__(self) -> None:
        self.adaptive_core = AdaptiveIntelligenceCore()
        self.regime_intelligence = MarketRegimeIntelligenceV2()
        self.learning_optimizer = AdaptiveLearningOptimizer()

    def evaluate(self, context: Mapping[str, Any]) -> MilestoneARuntimeResult:
        adaptive = self.adaptive_core.evaluate(context.get("signals", []), context=context).to_dict()
        regime = self.regime_intelligence.classify(context.get("regime_features", {})).to_dict()
        learning = self.learning_optimizer.optimize(context.get("learning_samples", []), context.get("base_thresholds", {})).to_dict()

        blockers: list[str] = []
        if regime["action_bias"] == "HOLD" and adaptive["action"] != "HOLD":
            blockers.append(f"regime_requires_hold:{regime['regime']}")
        if adaptive["confidence"] < learning["entry_threshold"]:
            blockers.append("adaptive_confidence_below_entry_threshold")
        if learning["status"] == "LEARNING":
            blockers.append("learning_layer_not_ready")

        production_allowed = not blockers and adaptive["action"] in {"BUY", "SELL"}
        status = "READY" if production_allowed else "OBSERVE"
        action = adaptive["action"] if production_allowed else "HOLD"
        reason = "milestone_a_production_ready" if production_allowed else "milestone_a_safe_observation"

        return MilestoneARuntimeResult(
            status=status,
            production_allowed=production_allowed,
            action=action,
            confidence=adaptive["confidence"],
            adaptive_intelligence=adaptive,
            market_regime=regime,
            learning_optimization=learning,
            blockers=blockers,
            reason=reason,
        )
