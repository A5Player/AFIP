"""Equity curve analytics for account growth and drawdown."""
from __future__ import annotations

from afip.analytics._common import AnalyticsResult, safe_divide


class EquityCurveEngine:
    """Evaluate equity curve stability, peak equity, and maximum drawdown."""

    name = "EquityCurveEngine"

    def evaluate(self, equity_points: list[float]) -> dict:
        points = [float(point) for point in equity_points or []]
        if not points:
            return AnalyticsResult(self.name, "NO_DATA", 0.0, "no_equity_points", {
                "start_equity": 0.0,
                "end_equity": 0.0,
                "net_change": 0.0,
                "max_drawdown": 0.0,
                "max_drawdown_percent": 0.0,
                "equity_points": 0,
            }).as_dict()
        peak = points[0]
        max_drawdown = 0.0
        for point in points:
            peak = max(peak, point)
            max_drawdown = max(max_drawdown, peak - point)
        start = points[0]
        end = points[-1]
        net_change = round(end - start, 2)
        max_drawdown_percent = round(safe_divide(max_drawdown * 100.0, max(points)), 2)
        growth_percent = round(safe_divide(net_change * 100.0, start), 2)
        stability = max(0.0, 100.0 - max_drawdown_percent * 3.0)
        score = min(100.0, max(0.0, stability * 0.7 + max(0.0, growth_percent) * 0.3))
        return AnalyticsResult(self.name, "READY", score, "equity_curve_ready", {
            "start_equity": round(start, 2),
            "end_equity": round(end, 2),
            "net_change": net_change,
            "growth_percent": growth_percent,
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_percent": max_drawdown_percent,
            "equity_points": len(points),
        }).as_dict()
