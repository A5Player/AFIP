"""Production Milestone A Pack 4: production control integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.regime_risk_budget import RegimeRiskBudget
from afip.intelligence.signal_quality_auditor import SignalQualityAuditor
from afip.learning.optimization_parameter_governor import OptimizationParameterGovernor
from afip.runtime.production_milestone_a_decision_bridge import ProductionMilestoneADecisionBridge


@dataclass(frozen=True)
class ProductionMilestoneAProductionControlResult:
    """Final Pack 4 production control output."""

    status: str
    production_allowed: bool
    action: str
    confidence: float
    risk_budget_level: str
    audit_status: str
    optimization_status: str
    decision_bridge: Dict[str, Any]
    signal_audit: Dict[str, Any]
    risk_budget: Dict[str, Any]
    optimization_governor: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "production_milestone_a_control_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "risk_budget_level": self.risk_budget_level,
            "audit_status": self.audit_status,
            "optimization_status": self.optimization_status,
            "decision_bridge": dict(self.decision_bridge),
            "signal_audit": dict(self.signal_audit),
            "risk_budget": dict(self.risk_budget),
            "optimization_governor": dict(self.optimization_governor),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneAProductionControl:
    """Final additive control that validates Pack 1-3 output before production use."""

    def __init__(self) -> None:
        self.decision_bridge = ProductionMilestoneADecisionBridge()
        self.signal_auditor = SignalQualityAuditor()
        self.risk_budget = RegimeRiskBudget()
        self.parameter_governor = OptimizationParameterGovernor()

    def evaluate(self, context: Mapping[str, Any]) -> ProductionMilestoneAProductionControlResult:
        bridge = self.decision_bridge.evaluate(context).to_dict()
        audit = self.signal_auditor.audit(context.get("signals", [])).to_dict()
        budget = self.risk_budget.evaluate(
            bridge.get("enhanced_runtime", {}).get("market_regime", {}),
            bridge.get("exposure_control", {}),
            bridge.get("learning_stability", {}),
        ).to_dict()
        governor = self.parameter_governor.govern(
            context.get("optimization_parameters", context.get("base_thresholds", {})),
            bridge.get("learning_stability", {}),
            budget,
        ).to_dict()

        blockers: list[str] = []
        if not bridge["production_allowed"]:
            blockers.extend(f"decision_bridge:{item}" for item in bridge.get("blockers", []))
        if audit["status"] != "READY":
            blockers.extend(f"signal_audit:{item}" for item in audit.get("blockers", []))
        if budget["status"] != "READY":
            blockers.extend(f"risk_budget:{item}" for item in budget.get("blockers", []))
        if governor["status"] != "READY":
            blockers.extend(f"optimization_governor:{item}" for item in governor.get("blockers", []))

        production_allowed = not blockers and bridge["production_allowed"] and governor["approved"]
        return ProductionMilestoneAProductionControlResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=bridge["action"] if production_allowed else "HOLD",
            confidence=bridge["confidence"] if production_allowed else min(float(bridge.get("confidence", 0.0)), 50.0),
            risk_budget_level=budget["risk_budget_level"],
            audit_status=audit["status"],
            optimization_status=governor["status"],
            decision_bridge=bridge,
            signal_audit=audit,
            risk_budget=budget,
            optimization_governor=governor,
            blockers=blockers,
            reason="production_milestone_a_control_ready" if production_allowed else "production_milestone_a_control_protective_observation",
        )
