"""Production Milestone B Pack 18 runtime for performance attribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.performance.performance_attribution import PerformanceAttribution


@dataclass(frozen=True)
class ProductionMilestoneBPerformanceRuntimeResult:
    """Integrated Pack 18 runtime result."""

    status: str
    performance_attribution_status: str
    return_status: str
    risk_adjusted_status: str
    breakdown_status: str
    comparison_status: str
    summary_status: str
    ready: bool
    opening_equity: float
    closing_equity: float
    net_profit: float
    return_percent: float
    risk_adjusted_ratio: float
    excess_return_percent: float
    contribution_count: int
    failed_rules: tuple[str, ...]
    contributions: tuple[dict[str, object], ...]


class ProductionMilestoneBPerformanceRuntime:
    """Run performance attribution against portfolio, risk, and position inputs."""

    def __init__(self) -> None:
        self.performance_attribution = PerformanceAttribution()

    def run(
        self,
        portfolio_snapshot: Mapping[str, object] | object,
        risk_snapshot: Mapping[str, object] | object,
        position_performance: Iterable[Mapping[str, object]],
        benchmark_return_ratio: float = 0.0,
    ) -> ProductionMilestoneBPerformanceRuntimeResult:
        summary = self.performance_attribution.calculate(portfolio_snapshot, risk_snapshot, position_performance, benchmark_return_ratio)
        return ProductionMilestoneBPerformanceRuntimeResult(
            status="PRODUCTION_MILESTONE_B_PERFORMANCE_READY" if summary.ready else "PRODUCTION_MILESTONE_B_PERFORMANCE_REVIEW",
            performance_attribution_status=summary.status,
            return_status=summary.return_status,
            risk_adjusted_status=summary.risk_adjusted_status,
            breakdown_status=summary.breakdown_status,
            comparison_status=summary.comparison_status,
            summary_status=summary.summary_status,
            ready=summary.ready,
            opening_equity=summary.opening_equity,
            closing_equity=summary.closing_equity,
            net_profit=summary.net_profit,
            return_percent=summary.return_percent,
            risk_adjusted_ratio=summary.risk_adjusted_ratio,
            excess_return_percent=summary.excess_return_percent,
            contribution_count=summary.contribution_count,
            failed_rules=summary.failed_rules,
            contributions=summary.contributions,
        )
