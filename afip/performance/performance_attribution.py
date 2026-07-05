"""Performance attribution coordinator for production portfolio analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.performance.benchmark_comparison import BenchmarkComparison
from afip.performance.performance_breakdown import PerformanceBreakdown
from afip.performance.performance_summary import PerformanceSummary
from afip.performance.portfolio_return import PortfolioReturn
from afip.performance.risk_adjusted_return import RiskAdjustedReturn


@dataclass(frozen=True)
class PerformanceAttributionSummary:
    """Integrated performance attribution summary."""

    status: str
    ready: bool
    return_status: str
    risk_adjusted_status: str
    breakdown_status: str
    comparison_status: str
    summary_status: str
    opening_equity: float
    closing_equity: float
    net_profit: float
    return_percent: float
    risk_adjusted_ratio: float
    excess_return_percent: float
    contribution_count: int
    failed_rules: tuple[str, ...]
    contributions: tuple[dict[str, object], ...]


class PerformanceAttribution:
    """Coordinate return, risk-adjusted return, breakdown, and comparison outputs."""

    def __init__(self) -> None:
        self.portfolio_return = PortfolioReturn()
        self.risk_adjusted_return = RiskAdjustedReturn()
        self.performance_breakdown = PerformanceBreakdown()
        self.benchmark_comparison = BenchmarkComparison()
        self.performance_summary = PerformanceSummary()

    def calculate(
        self,
        portfolio_snapshot: Mapping[str, object] | object,
        risk_snapshot: Mapping[str, object] | object,
        position_performance: Iterable[Mapping[str, object]],
        benchmark_return_ratio: float = 0.0,
    ) -> PerformanceAttributionSummary:
        return_result = self.portfolio_return.calculate(portfolio_snapshot)
        risk_adjusted_result = self.risk_adjusted_return.calculate(return_result, risk_snapshot)
        breakdown_result = self.performance_breakdown.calculate(position_performance)
        comparison_result = self.benchmark_comparison.compare(return_result, benchmark_return_ratio)
        summary_result = self.performance_summary.summarize(return_result, risk_adjusted_result, breakdown_result, comparison_result)
        return PerformanceAttributionSummary(
            status="PERFORMANCE_ATTRIBUTION_READY" if summary_result.ready else "PERFORMANCE_ATTRIBUTION_REVIEW",
            ready=summary_result.ready,
            return_status=return_result.status,
            risk_adjusted_status=risk_adjusted_result.status,
            breakdown_status=breakdown_result.status,
            comparison_status=comparison_result.status,
            summary_status=summary_result.status,
            opening_equity=return_result.opening_equity,
            closing_equity=return_result.closing_equity,
            net_profit=return_result.net_profit,
            return_percent=return_result.return_percent,
            risk_adjusted_ratio=risk_adjusted_result.risk_adjusted_ratio,
            excess_return_percent=comparison_result.excess_return_percent,
            contribution_count=breakdown_result.contribution_count,
            failed_rules=summary_result.failed_rules,
            contributions=breakdown_result.contributions,
        )
