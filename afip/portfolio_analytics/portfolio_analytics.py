"""Integrated portfolio analytics layer."""

from __future__ import annotations

from typing import Iterable, Mapping

from afip.portfolio_analytics.allocation_efficiency import AllocationEfficiency
from afip.portfolio_analytics.analytics_summary import AnalyticsSummary
from afip.portfolio_analytics.equity_trend import EquityTrend
from afip.portfolio_analytics.risk_efficiency import RiskEfficiency


class PortfolioAnalytics:
    """Run portfolio analytics using equity, performance, risk, and capital inputs."""

    def __init__(self) -> None:
        self.equity_trend = EquityTrend()
        self.risk_efficiency = RiskEfficiency()
        self.allocation_efficiency = AllocationEfficiency()
        self.analytics_summary = AnalyticsSummary()

    def calculate(
        self,
        equity_observations: Iterable[Mapping[str, object]],
        performance_summary: Mapping[str, object] | object,
        risk_snapshot: Mapping[str, object] | object,
        capital_snapshot: Mapping[str, object] | object,
    ):
        equity = self.equity_trend.calculate(equity_observations)
        risk = self.risk_efficiency.calculate(performance_summary, risk_snapshot)
        allocation = self.allocation_efficiency.calculate(capital_snapshot)
        return self.analytics_summary.summarize(equity, risk, allocation)
