"""Production Milestone A Pack 2: enhanced runtime integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.adaptive_intelligence_core import AdaptiveIntelligenceCore, AdaptiveSignal
from afip.intelligence.adaptive_signal_calibrator import AdaptiveSignalCalibrator
from afip.intelligence.market_regime_intelligence_v2 import MarketRegimeIntelligenceV2
from afip.intelligence.market_regime_transition_intelligence import MarketRegimeTransitionIntelligence
from afip.learning.adaptive_learning_optimizer import AdaptiveLearningOptimizer


@dataclass(frozen=True)
class EnhancedMilestoneAResult:
    status: str
    production_allowed: bool
    action: str
    confidence: float
    adaptive_intelligence: Dict[str, Any]
    market_regime: Dict[str, Any]
    regime_transition: Dict[str, Any]
    calibration: Dict[str, Any]
    learning_optimization: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "enhanced_milestone_a_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "adaptive_intelligence": dict(self.adaptive_intelligence),
            "market_regime": dict(self.market_regime),
            "regime_transition": dict(self.regime_transition),
            "calibration": dict(self.calibration),
            "learning_optimization": dict(self.learning_optimization),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneAEnhancedRuntime:
    """Additive production layer for calibration and regime transition controls."""

    def __init__(self) -> None:
        self.calibrator = AdaptiveSignalCalibrator()
        self.adaptive_core = AdaptiveIntelligenceCore()
        self.regime_intelligence = MarketRegimeIntelligenceV2()
        self.transition_intelligence = MarketRegimeTransitionIntelligence()
        self.learning_optimizer = AdaptiveLearningOptimizer()

    def evaluate(self, context: Mapping[str, Any]) -> EnhancedMilestoneAResult:
        raw_signals = [s if isinstance(s, AdaptiveSignal) else AdaptiveSignal.from_mapping(s) for s in context.get("signals", [])]
        learning_samples = list(context.get("learning_samples", []) or [])
        group = str(context.get("calibration_group", raw_signals[0].group if raw_signals else "general"))
        calibration_profile = self.calibrator.build_profile(group, learning_samples)
        calibrated_signals = [self.calibrator.calibrate_signal(signal, calibration_profile) for signal in raw_signals]

        adaptive = self.adaptive_core.evaluate(calibrated_signals, context=context).to_dict()
        regime = self.regime_intelligence.classify(context.get("regime_features", {})).to_dict()
        transition = self.transition_intelligence.evaluate(context.get("regime_history", [])).to_dict()
        learning = self.learning_optimizer.optimize(learning_samples, context.get("base_thresholds", {})).to_dict()

        blockers: list[str] = []
        if calibration_profile.status != "READY":
            blockers.append("calibration_layer_not_ready")
        if transition["risk_bias"] == "REDUCE_EXPOSURE":
            blockers.append(f"regime_transition_requires_reduced_exposure:{transition['transition']}")
        if regime["action_bias"] == "HOLD" and adaptive["action"] != "HOLD":
            blockers.append(f"regime_requires_hold:{regime['regime']}")
        if adaptive["confidence"] < learning["entry_threshold"]:
            blockers.append("adaptive_confidence_below_entry_threshold")
        if learning["status"] == "LEARNING":
            blockers.append("learning_layer_not_ready")

        production_allowed = not blockers and adaptive["action"] in {"BUY", "SELL"}
        return EnhancedMilestoneAResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=adaptive["action"] if production_allowed else "HOLD",
            confidence=adaptive["confidence"],
            adaptive_intelligence=adaptive,
            market_regime=regime,
            regime_transition=transition,
            calibration=calibration_profile.to_dict(),
            learning_optimization=learning,
            blockers=blockers,
            reason="enhanced_milestone_a_production_ready" if production_allowed else "enhanced_milestone_a_safe_observation",
        )
