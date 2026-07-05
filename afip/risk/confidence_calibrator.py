from afip.risk.risk_assessor import RiskAssessor
from afip.decision.risk_aware_decision_service import RiskAwareDecisionService
from afip.execution.protected_simulation_order_builder import ProtectedSimulationOrderBuilder


class ConfidenceCalibrator:
    """
    Aligns Risk confidence with official Modular Intelligence confidence.
    This prevents a mismatch where Intelligence shows a strong decision but
    the older multi-timeframe score still blocks the simulated order.
    """

    def __init__(self, risk_assessor=None, decision_service=None, order_builder=None):
        self.risk_assessor = risk_assessor or RiskAssessor()
        self.decision_service = decision_service or RiskAwareDecisionService()
        self.order_builder = order_builder or ProtectedSimulationOrderBuilder()

    def calibrate(self, protected: dict, modular: dict, balance: float = 1000.0) -> dict:
        base = protected.get("base", {})
        signal = base.get("signal", {})
        snapshots = signal.get("snapshots", {})
        first_snapshot = next(iter(snapshots.values()), {}) if snapshots else {}

        modular_decision = modular.get("decision", {}) if modular else {}
        original_score = dict(signal.get("score", {}))
        calibrated_score = dict(original_score)

        modular_confidence = float(modular_decision.get("confidence", original_score.get("overall_confidence", 0)))
        buy_score = float(modular_decision.get("buy_score", original_score.get("buy_score", 0)))
        sell_score = float(modular_decision.get("sell_score", original_score.get("sell_score", 0)))
        modular_penalty = float(modular_decision.get("penalties", original_score.get("risk_penalty", 0)))

        calibrated_score.update({
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "overall_confidence": round(modular_confidence, 2),
            "risk_penalty": round(min(modular_penalty, original_score.get("risk_penalty", 0)), 2),
            "direction": modular_decision.get("action", original_score.get("direction", "WAIT")),
            "reason": "modular_intelligence_confidence_calibrated",
        })

        calibrated_risk = self.risk_assessor.assess(first_snapshot, calibrated_score)
        calibrated_decision = self.decision_service.decide(modular_decision, calibrated_risk)
        calibrated_order = self.order_builder.build(calibrated_decision, first_snapshot, balance=balance)

        calibrated_base = dict(base)
        calibrated_signal = dict(signal)
        calibrated_signal["score"] = calibrated_score
        calibrated_base["signal"] = calibrated_signal
        calibrated_base["risk"] = calibrated_risk
        calibrated_base["decision"] = calibrated_decision
        calibrated_base["order"] = calibrated_order

        return {
            **protected,
            "base": calibrated_base,
            "protected_order": calibrated_order,
            "confidence_calibration": {
                "status": "APPLIED",
                "source": "MODULAR_INTELLIGENCE",
                "original_confidence": original_score.get("overall_confidence", 0),
                "calibrated_confidence": round(modular_confidence, 2),
                "risk_allowed": calibrated_risk.get("allowed", False),
                "risk_reasons": calibrated_risk.get("reasons", []),
            },
        }
