"""Portfolio analytics summary controls."""

from __future__ import annotations

from afip.portfolio_analytics.analytics_snapshot import AnalyticsSnapshot


class AnalyticsSummary:
    """Summarize portfolio analytics readiness across equity, risk, and capital."""

    def summarize(self, equity_trend: object, risk_efficiency: object, allocation_efficiency: object) -> AnalyticsSnapshot:
        failed: list[str] = []
        if getattr(equity_trend, "status", "") != "EQUITY_TREND_READY":
            failed.append("equity_trend_not_ready")
        if getattr(risk_efficiency, "status", "") != "RISK_EFFICIENCY_READY":
            failed.append("risk_efficiency_not_ready")
        if getattr(allocation_efficiency, "status", "") != "ALLOCATION_EFFICIENCY_READY":
            failed.append("allocation_efficiency_not_ready")
        ready = not failed
        return AnalyticsSnapshot(
            status="PORTFOLIO_ANALYTICS_READY" if ready else "PORTFOLIO_ANALYTICS_REVIEW",
            ready=ready,
            equity_trend_status=str(getattr(equity_trend, "status", "")),
            risk_efficiency_status=str(getattr(risk_efficiency, "status", "")),
            allocation_efficiency_status=str(getattr(allocation_efficiency, "status", "")),
            trend_direction=str(getattr(equity_trend, "trend_direction", "FLAT")),
            trend_strength_percent=float(getattr(equity_trend, "trend_strength_percent", 0.0) or 0.0),
            risk_efficiency_ratio=float(getattr(risk_efficiency, "efficiency_ratio", 0.0) or 0.0),
            capital_utilization_percent=float(getattr(allocation_efficiency, "utilization_percent", 0.0) or 0.0),
            failed_rules=tuple(failed),
        )
