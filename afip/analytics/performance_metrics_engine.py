"""Performance metrics engine for closed trade statistics."""
from __future__ import annotations

from afip.analytics._common import AnalyticsResult, safe_divide


class PerformanceMetricsEngine:
    """Calculate win rate, expectancy, profit factor, and average trade metrics."""

    name = "PerformanceMetricsEngine"

    def evaluate(self, trades: list[dict]) -> dict:
        closed = [trade for trade in trades or [] if str(trade.get("status", "CLOSED")).upper() == "CLOSED"]
        profits = [float(trade.get("profit", 0.0) or 0.0) for trade in closed]
        wins = [value for value in profits if value > 0]
        losses = [value for value in profits if value < 0]
        total_profit = round(sum(profits), 2)
        total_loss = abs(round(sum(losses), 2))
        total_gain = round(sum(wins), 2)
        total_trades = len(profits)
        win_rate = round(safe_divide(len(wins) * 100.0, total_trades), 2)
        average_trade = round(safe_divide(total_profit, total_trades), 2)
        profit_factor = round(safe_divide(total_gain, total_loss, default=total_gain if total_gain > 0 else 0.0), 2)
        expectancy = round((win_rate / 100.0) * safe_divide(total_gain, len(wins)) - (1 - win_rate / 100.0) * abs(safe_divide(sum(losses), len(losses))), 2)
        score = min(100.0, max(0.0, 50.0 + average_trade * 2.0 + (profit_factor - 1.0) * 15.0 + (win_rate - 50.0) * 0.4))
        status = "READY" if total_trades > 0 else "NO_DATA"
        return AnalyticsResult(self.name, status, score, "performance_metrics_ready" if total_trades else "no_closed_trades", {
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": win_rate,
            "net_profit": total_profit,
            "average_trade": average_trade,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
        }).as_dict()
