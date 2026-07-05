"""Production analytics report builder for AFIP review output."""
from __future__ import annotations

from afip.analytics.equity_curve_engine import EquityCurveEngine
from afip.analytics.performance_metrics_engine import PerformanceMetricsEngine
from afip.analytics.time_window_analytics_engine import TimeWindowAnalyticsEngine
from afip.analytics.trade_distribution_engine import TradeDistributionEngine
from afip.backtest.backtest_metrics_engine import BacktestMetricsEngine
from afip.backtest.scenario_stress_engine import ScenarioStressEngine
from afip.backtest.walk_forward_engine import WalkForwardEngine


class AnalyticsReportBuilder:
    """Build a compact production analytics report from trade, equity, and validation data."""

    name = "AnalyticsReportBuilder"

    def __init__(self):
        self.performance = PerformanceMetricsEngine()
        self.equity = EquityCurveEngine()
        self.time_windows = TimeWindowAnalyticsEngine()
        self.distribution = TradeDistributionEngine()
        self.backtest = BacktestMetricsEngine()
        self.walk_forward = WalkForwardEngine()
        self.stress = ScenarioStressEngine()

    def build(self, payload: dict) -> dict:
        trades = list(payload.get("trades", []) or [])
        equity_points = list(payload.get("equity_points", []) or [])
        report = {
            "name": self.name,
            "status": "READY",
            "performance": self.performance.evaluate(trades),
            "equity_curve": self.equity.evaluate(equity_points),
            "time_windows": self.time_windows.evaluate(trades),
            "trade_distribution": self.distribution.evaluate(trades),
            "backtest_metrics": self.backtest.evaluate(trades, equity_points),
            "walk_forward": self.walk_forward.evaluate(list(payload.get("walk_forward_windows", []) or [])),
            "scenario_stress": self.stress.evaluate(list(payload.get("stress_scenarios", []) or [])),
        }
        component_scores = [value.get("score", 0.0) for key, value in report.items() if isinstance(value, dict) and "score" in value]
        report["production_score"] = round(sum(component_scores) / max(1, len(component_scores)), 2)
        report["status"] = "READY" if report["production_score"] >= 55.0 else "CAUTION"
        return report
