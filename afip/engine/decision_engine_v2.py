"""Decision engine V2 for AFIP production signal selection."""
from __future__ import annotations

from afip.engine.adaptive_risk_engine import AdaptiveRiskEngine
from afip.engine.confluence_score_engine import ConfluenceScoreEngine
from afip.engine.execution_readiness_engine import ExecutionReadinessEngine
from afip.engine.institutional_score_engine import InstitutionalScoreEngine
from afip.engine.position_engine import PositionEngine
from afip.engine.signal_quality_engine import SignalQualityEngine
from afip.engine._common import EngineResult, clamp


class DecisionEngineV2:
    """Combine institutional, confluence, signal quality, risk, and position engines."""

    name = "DecisionEngineV2"

    def __init__(self):
        self.institutional = InstitutionalScoreEngine()
        self.confluence = ConfluenceScoreEngine()
        self.signal_quality = SignalQualityEngine()
        self.adaptive_risk = AdaptiveRiskEngine()
        self.position = PositionEngine()
        self.execution = ExecutionReadinessEngine()

    def evaluate(self, snapshot: dict) -> dict:
        institutional = self.institutional.evaluate(snapshot)
        confluence = self.confluence.evaluate(snapshot)
        signal_quality = self.signal_quality.evaluate(snapshot)
        spread_usage = self._spread_usage(snapshot.get("trading_cost", {}))
        drawdown_percent = float(snapshot.get("drawdown_percent", 0.0) or 0.0)
        preliminary_confidence = self._combined_confidence(institutional, confluence, signal_quality)
        risk = self.adaptive_risk.evaluate({
            "decision_confidence": preliminary_confidence,
            "drawdown_percent": drawdown_percent,
            "spread_usage": spread_usage,
        })
        position = self.position.evaluate(snapshot)
        execution = self.execution.evaluate({"checks": [risk, position, confluence]})
        action = self._select_action(institutional, confluence, signal_quality, risk, execution)
        confidence = self._combined_confidence(institutional, confluence, signal_quality, risk, execution)
        if action == "WAIT":
            confidence = min(confidence, 54.0)
        return EngineResult(
            self.name,
            "READY" if action != "WAIT" else "CAUTION",
            action,
            confidence,
            "decision_v2_ready" if action != "WAIT" else "decision_v2_wait",
            {
                "institutional": institutional,
                "confluence": confluence,
                "signal_quality": signal_quality,
                "adaptive_risk": risk,
                "position": position,
                "execution_readiness": execution,
                "spread_usage": round(spread_usage, 4),
            },
        ).as_dict()

    @staticmethod
    def _spread_usage(trading_cost: dict) -> float:
        spread = float(trading_cost.get("spread_points", 0.0) or 0.0)
        limit = float(trading_cost.get("max_spread_points", 35.0) or 35.0)
        return spread / limit if limit > 0 else 1.0

    @staticmethod
    def _combined_confidence(*items: dict) -> float:
        weights = {
            "InstitutionalScoreEngine": 1.3,
            "ConfluenceScoreEngine": 1.4,
            "SignalQualityEngine": 1.0,
            "AdaptiveRiskEngine": 1.2,
            "ExecutionReadinessEngine": 1.5,
        }
        total_weight = 0.0
        total = 0.0
        for item in items:
            weight = weights.get(item.get("name"), 1.0)
            total += float(item.get("confidence", 0.0) or 0.0) * weight
            total_weight += weight
        return clamp(total / max(1.0, total_weight))

    @staticmethod
    def _select_action(*items: dict) -> str:
        blocking = [item for item in items if item.get("status") == "BLOCKED" or item.get("action") in {"WAIT", "REDUCE_RISK"}]
        if any(item.get("status") == "BLOCKED" for item in blocking):
            return "WAIT"
        buy_votes = sum(1 for item in items if item.get("action") == "BUY")
        sell_votes = sum(1 for item in items if item.get("action") == "SELL")
        if buy_votes >= 2 and buy_votes > sell_votes:
            return "BUY"
        if sell_votes >= 2 and sell_votes > buy_votes:
            return "SELL"
        return "WAIT"
