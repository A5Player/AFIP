"""Risk-adjusted decision action model for financial execution control."""

from dataclasses import dataclass

@dataclass(frozen=True)
class DecisionRiskAdjustmentResult:
    status: str
    action: str
    adjusted_confidence: float
    risk_status: str
    reason: str

class DecisionRiskAdjustment:
    """Applies financial risk constraints to a proposed decision."""

    def adjust(self, action: str, confidence: float, drawdown_ratio: float = 0.0, exposure_ratio: float = 0.0) -> DecisionRiskAdjustmentResult:
        action = str(action).upper()
        base = max(0.0, min(100.0, float(confidence)))
        drawdown = max(0.0, float(drawdown_ratio))
        exposure = max(0.0, float(exposure_ratio))
        penalty = min(60.0, drawdown * 100.0 * 0.45 + exposure * 100.0 * 0.35)
        adjusted = round(max(0.0, base - penalty), 2)
        if drawdown >= 0.25 or exposure >= 0.90:
            risk_status = "RESTRICTED"
            final_action = "NO_ACTION"
        elif drawdown >= 0.12 or exposure >= 0.70:
            risk_status = "CAUTION"
            final_action = "REDUCE" if action in {"BUY", "SELL"} else action
        else:
            risk_status = "ACCEPTABLE"
            final_action = action
        status = "DECISION_RISK_ADJUSTED"
        return DecisionRiskAdjustmentResult(status, final_action, adjusted, risk_status, f"risk_{risk_status.lower()}")
