"""Production Milestone A Pack 3: runtime decision bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.adaptive_intelligence_core import AdaptiveSignal
from afip.intelligence.adaptive_weight_allocator import AdaptiveWeightAllocator
from afip.intelligence.regime_exposure_controller import RegimeExposureController
from afip.learning.learning_stability_monitor import LearningStabilityMonitor
from afip.runtime.production_milestone_a_enhanced_runtime import ProductionMilestoneAEnhancedRuntime


@dataclass(frozen=True)
class MilestoneADecisionBridgeResult:
    """Final additive bridge result for Milestone A Pack 3."""

    status: str
    production_allowed: bool
    action: str
    confidence: float
    exposure_multiplier: float
    enhanced_runtime: Dict[str, Any]
    exposure_control: Dict[str, Any]
    learning_stability: Dict[str, Any]
    weight_allocation: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "milestone_a_decision_bridge_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "exposure_multiplier": round(self.exposure_multiplier, 4),
            "enhanced_runtime": dict(self.enhanced_runtime),
            "exposure_control": dict(self.exposure_control),
            "learning_stability": dict(self.learning_stability),
            "weight_allocation": dict(self.weight_allocation),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneADecisionBridge:
    """Coordinates weight allocation, stability, exposure, and enhanced runtime."""

    def __init__(self) -> None:
        self.weight_allocator = AdaptiveWeightAllocator()
        self.enhanced_runtime = ProductionMilestoneAEnhancedRuntime()
        self.exposure_controller = RegimeExposureController()
        self.stability_monitor = LearningStabilityMonitor()

    def evaluate(self, context: Mapping[str, Any]) -> MilestoneADecisionBridgeResult:
        raw_signals = [s if isinstance(s, AdaptiveSignal) else AdaptiveSignal.from_mapping(s) for s in context.get("signals", [])]
        group = str(context.get("allocation_group", raw_signals[0].group if raw_signals else "general"))
        allocation_profile = self.weight_allocator.build_profile(group, context.get("quality_factors", {}))
        allocated_signals = self.weight_allocator.allocate(raw_signals, {group: allocation_profile})
        bridge_context = dict(context)
        bridge_context["signals"] = allocated_signals

        enhanced = self.enhanced_runtime.evaluate(bridge_context).to_dict()
        exposure = self.exposure_controller.evaluate(enhanced.get("market_regime", {}), enhanced.get("regime_transition", {}), context.get("cost_quality", {})).to_dict()
        stability = self.stability_monitor.evaluate(context.get("learning_samples", [])).to_dict()

        blockers: list[str] = []
        if allocation_profile.status != "READY":
            blockers.append("weight_allocation_not_ready")
        if not enhanced["production_allowed"]:
            blockers.extend(f"enhanced_runtime:{item}" for item in enhanced.get("blockers", []))
        if exposure["status"] == "OBSERVE":
            blockers.extend(f"exposure_control:{item}" for item in exposure.get("blockers", []))
        if stability["status"] == "LEARNING":
            blockers.extend(f"learning_stability:{item}" for item in stability.get("blockers", []))

        production_allowed = not blockers and enhanced["production_allowed"] and exposure["exposure_multiplier"] > 0.0
        action = enhanced["action"] if production_allowed else "HOLD"
        status = "READY" if production_allowed else "OBSERVE"
        return MilestoneADecisionBridgeResult(
            status=status,
            production_allowed=production_allowed,
            action=action,
            confidence=enhanced["confidence"],
            exposure_multiplier=exposure["exposure_multiplier"] if production_allowed else 0.0,
            enhanced_runtime=enhanced,
            exposure_control=exposure,
            learning_stability=stability,
            weight_allocation=allocation_profile.to_dict(),
            blockers=blockers,
            reason="milestone_a_decision_bridge_ready" if production_allowed else "milestone_a_decision_bridge_safe_observation",
        )
