"""Backtest metrics engine for AFIP production validation."""
from __future__ import annotations

from afip.analytics.equity_curve_engine import EquityCurveEngine
from afip.analytics.performance_metrics_engine import PerformanceMetricsEngine


class BacktestMetricsEngine:
    """Combine trade and equity statistics into a backtest quality report."""

    name = "BacktestMetricsEngine"

    def __init__(self):
        self.performance = PerformanceMetricsEngine()
        self.equity_curve = EquityCurveEngine()

    def evaluate(self, trades: list[dict], equity_points: list[float]) -> dict:
        performance = self.performance.evaluate(trades)
        equity = self.equity_curve.evaluate(equity_points)
        survival = equity.get("end_equity", 0.0) > 0 and equity.get("max_drawdown_percent", 100.0) < 35.0
        score = round(performance.get("score", 0.0) * 0.55 + equity.get("score", 0.0) * 0.45, 2)
        if not survival:
            score = min(score, 49.0)
        return {
            "name": self.name,
            "status": "READY" if performance.get("status") == "READY" and equity.get("status") == "READY" else "NO_DATA",
            "score": score,
            "survival": survival,
            "reason": "backtest_metrics_ready" if survival else "backtest_survival_risk",
            "performance": performance,
            "equity_curve": equity,
        }
