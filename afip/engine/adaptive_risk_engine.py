"""Adaptive risk engine for AFIP production readiness."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp


class AdaptiveRiskEngine:
    """Adjust risk tier from drawdown, signal confidence, and trading cost."""

    name = "AdaptiveRiskEngine"

    def evaluate(self, snapshot: dict) -> dict:
        decision_confidence = float(snapshot.get("decision_confidence", 0.0) or 0.0)
        drawdown_percent = float(snapshot.get("drawdown_percent", 0.0) or 0.0)
        spread_usage = float(snapshot.get("spread_usage", 0.0) or 0.0)
        if drawdown_percent >= 12.0 or spread_usage >= 1.0:
            tier = "RISK_OFF"
            risk_percent = 0.0
            action = "WAIT"
            reason = "risk_off_conditions"
        elif drawdown_percent >= 8.0 or spread_usage >= 0.85:
            tier = "DEFENSIVE"
            risk_percent = 0.35
            action = "REDUCE_RISK"
            reason = "defensive_risk_conditions"
        elif decision_confidence >= 80.0 and drawdown_percent <= 3.0 and spread_usage <= 0.70:
            tier = "OPPORTUNITY"
            risk_percent = 1.0
            action = "ALLOW"
            reason = "opportunity_risk_conditions"
        else:
            tier = "BALANCED"
            risk_percent = 0.60
            action = "ALLOW"
            reason = "balanced_risk_conditions"
        confidence = clamp(100.0 - drawdown_percent * 5.0 - spread_usage * 20.0 + decision_confidence * 0.2)
        return EngineResult(
            self.name,
            "READY" if action != "WAIT" else "BLOCKED",
            action,
            confidence,
            reason,
            {"risk_tier": tier, "risk_percent": risk_percent, "drawdown_percent": drawdown_percent, "spread_usage": spread_usage},
        ).as_dict()
