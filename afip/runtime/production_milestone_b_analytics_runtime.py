"""Production Milestone B Pack 19 runtime for portfolio analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.portfolio_analytics.portfolio_analytics import PortfolioAnalytics


@dataclass(frozen=True)
class ProductionMilestoneBAnalyticsRuntimeResult:
    """Integrated Pack 19 runtime result."""

    status: str
    portfolio_analytics_status: str
    ready: bool
    equity_trend_status: str
    risk_efficiency_status: str
    allocation_efficiency_status: str
    trend_direction: str
    trend_strength_percent: float
    risk_efficiency_ratio: float
    capital_utilization_percent: float
    failed_rules: tuple[str, ...]


class ProductionMilestoneBAnalyticsRuntime:
    """Run portfolio analytics for production reporting and review."""

    def __init__(self) -> None:
        self.portfolio_analytics = PortfolioAnalytics()

    def run(
        self,
        equity_observations: Iterable[Mapping[str, object]],
        performance_summary: Mapping[str, object] | object,
        risk_snapshot: Mapping[str, object] | object,
        capital_snapshot: Mapping[str, object] | object,
    ) -> ProductionMilestoneBAnalyticsRuntimeResult:
        summary = self.portfolio_analytics.calculate(equity_observations, performance_summary, risk_snapshot, capital_snapshot)
        return ProductionMilestoneBAnalyticsRuntimeResult(
            status="PRODUCTION_MILESTONE_B_ANALYTICS_READY" if summary.ready else "PRODUCTION_MILESTONE_B_ANALYTICS_REVIEW",
            portfolio_analytics_status=summary.status,
            ready=summary.ready,
            equity_trend_status=summary.equity_trend_status,
            risk_efficiency_status=summary.risk_efficiency_status,
            allocation_efficiency_status=summary.allocation_efficiency_status,
            trend_direction=summary.trend_direction,
            trend_strength_percent=summary.trend_strength_percent,
            risk_efficiency_ratio=summary.risk_efficiency_ratio,
            capital_utilization_percent=summary.capital_utilization_percent,
            failed_rules=summary.failed_rules,
        )
