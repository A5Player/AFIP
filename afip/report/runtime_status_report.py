"""Runtime status report formatter for AFIP production simulation output."""
from __future__ import annotations


class RuntimeStatusReport:
    """Format selected runtime and analytics fields into stable text lines."""

    name = "RuntimeStatusReport"

    def build_lines(self, report: dict) -> list[str]:
        if not report:
            return ["Runtime Analytics: NO_DATA"]
        lines = ["Runtime Analytics:"]
        score = report.get("production_score", 0.0)
        lines.append(f" - Production Score : {score}")
        performance = report.get("performance", {})
        equity = report.get("equity_curve", {})
        backtest = report.get("backtest_metrics", {})
        lines.append(f" - Win Rate         : {performance.get('win_rate', 0.0)}%")
        lines.append(f" - Profit Factor    : {performance.get('profit_factor', 0.0)}")
        lines.append(f" - Max Drawdown     : {equity.get('max_drawdown_percent', 0.0)}%")
        lines.append(f" - Backtest Status  : {backtest.get('status', 'NO_DATA')}")
        return lines
