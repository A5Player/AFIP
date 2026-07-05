"""Drawdown engine for AFIP risk protection."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp


class DrawdownEngine:
    """Evaluate current drawdown against a configured maximum."""

    name = "DrawdownEngine"

    def __init__(self, max_drawdown_percent: float = 12.0):
        self.max_drawdown_percent = max(1.0, float(max_drawdown_percent))

    def evaluate(self, snapshot: dict) -> dict:
        balance = float(snapshot.get("balance", 0.0) or 0.0)
        equity = float(snapshot.get("equity", balance) or balance)
        if balance <= 0:
            return EngineResult(self.name, "LEARNING", "WAIT", 30.0, "balance_not_available", {}).as_dict()
        drawdown_percent = max(0.0, (balance - equity) / balance * 100.0)
        blocked = drawdown_percent >= self.max_drawdown_percent
        warning = drawdown_percent >= self.max_drawdown_percent * 0.7
        status = "BLOCKED" if blocked else "CAUTION" if warning else "READY"
        confidence = clamp(100.0 - drawdown_percent / self.max_drawdown_percent * 100.0)
        action = "WAIT" if blocked else "REDUCE_RISK" if warning else "ALLOW"
        reason = "drawdown_limit_reached" if blocked else "drawdown_near_limit" if warning else "drawdown_within_limit"
        return EngineResult(
            self.name,
            status,
            action,
            confidence,
            reason,
            {
                "balance": round(balance, 2),
                "equity": round(equity, 2),
                "drawdown_percent": round(drawdown_percent, 2),
                "max_drawdown_percent": round(self.max_drawdown_percent, 2),
            },
        ).as_dict()
