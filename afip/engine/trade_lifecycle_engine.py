"""Trade lifecycle engine for position state transitions."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp


class TradeLifecycleEngine:
    """Classify trade lifecycle state from profit, confidence, and protection data."""

    name = "TradeLifecycleEngine"

    def evaluate(self, snapshot: dict) -> dict:
        floating_profit = float(snapshot.get("floating_profit", 0.0) or 0.0)
        peak_profit = float(snapshot.get("peak_profit", max(0.0, floating_profit)) or 0.0)
        confidence = float(snapshot.get("position_confidence", 50.0) or 50.0)
        giveback = max(0.0, peak_profit - floating_profit)
        giveback_percent = giveback / peak_profit * 100.0 if peak_profit > 0 else 0.0
        if confidence < 35.0:
            state = "EXIT_REVIEW"
            action = "REDUCE_OR_CLOSE"
            reason = "position_confidence_weak"
        elif peak_profit > 0 and giveback_percent >= 45.0:
            state = "PROFIT_PROTECTION"
            action = "PROTECT_PROFIT"
            reason = "profit_giveback_high"
        elif floating_profit > 0 and confidence >= 70.0:
            state = "HOLDING_STRENGTH"
            action = "HOLD"
            reason = "position_confidence_strong"
        else:
            state = "MONITORING"
            action = "MONITOR"
            reason = "position_monitoring"
        return EngineResult(
            self.name,
            "READY",
            action,
            clamp(confidence),
            reason,
            {"lifecycle_state": state, "floating_profit": floating_profit, "peak_profit": peak_profit, "giveback_percent": round(giveback_percent, 2)},
        ).as_dict()
