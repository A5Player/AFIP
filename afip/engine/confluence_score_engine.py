"""Confluence score engine for multi-factor market alignment."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp, direction_scores


class ConfluenceScoreEngine:
    """Evaluate market, institutional, risk, and cost alignment."""

    name = "ConfluenceScoreEngine"

    def evaluate(self, snapshot: dict) -> dict:
        intelligence = list(snapshot.get("intelligence", []))
        if not intelligence:
            return EngineResult(self.name, "LEARNING", "WAIT", 30.0, "no_intelligence_inputs", {}).as_dict()

        buy_score, sell_score, flat_score = direction_scores(intelligence)
        spread_penalty = self._spread_penalty(snapshot.get("trading_cost", {}))
        risk_penalty = self._risk_penalty(snapshot.get("risk", {}))
        edge = abs(buy_score - sell_score)
        confidence = clamp(max(buy_score, sell_score, flat_score) + edge * 0.2 - spread_penalty - risk_penalty)
        action = "BUY" if buy_score >= sell_score + 7 else "SELL" if sell_score >= buy_score + 7 else "WAIT"
        if confidence < 55:
            action = "WAIT"
        return EngineResult(
            self.name,
            "READY",
            action,
            confidence,
            "confluence_ready" if action != "WAIT" else "confluence_wait",
            {
                "buy_score": round(buy_score, 2),
                "sell_score": round(sell_score, 2),
                "flat_score": round(flat_score, 2),
                "spread_penalty": round(spread_penalty, 2),
                "risk_penalty": round(risk_penalty, 2),
                "input_count": len(intelligence),
            },
        ).as_dict()

    @staticmethod
    def _spread_penalty(trading_cost: dict) -> float:
        spread = float(trading_cost.get("spread_points", 0.0) or 0.0)
        limit = float(trading_cost.get("max_spread_points", 35.0) or 35.0)
        if limit <= 0:
            return 10.0
        usage = spread / limit
        if usage >= 1.0:
            return 25.0
        if usage >= 0.8:
            return 10.0
        return 0.0

    @staticmethod
    def _risk_penalty(risk: dict) -> float:
        if risk and not risk.get("allowed", True):
            return 50.0
        return 0.0
