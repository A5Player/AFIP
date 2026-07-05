"""Contribution breakdown for production portfolio performance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class PerformanceBreakdownResult:
    """Position-level performance contribution output."""

    status: str
    ready: bool
    contribution_count: int
    total_contribution: float
    contributions: tuple[dict[str, object], ...]
    reason: str


class PerformanceBreakdown:
    """Break portfolio performance into weighted position contributions."""

    def calculate(self, position_performance: Iterable[Mapping[str, object]]) -> PerformanceBreakdownResult:
        rows = tuple(position_performance)
        if not rows:
            return PerformanceBreakdownResult("PERFORMANCE_BREAKDOWN_REVIEW", False, 0, 0.0, (), "position_performance_empty")
        total_profit = sum(float(row.get("net_profit", 0.0) or 0.0) for row in rows)
        contributions: list[dict[str, object]] = []
        for row in rows:
            net_profit = float(row.get("net_profit", 0.0) or 0.0)
            contribution_ratio = 0.0 if total_profit == 0.0 else net_profit / total_profit
            contributions.append(
                {
                    "account_id": row.get("account_id", "PORTFOLIO"),
                    "symbol": row.get("symbol", "PORTFOLIO"),
                    "net_profit": net_profit,
                    "contribution_ratio": round(contribution_ratio, 6),
                    "contribution_percent": round(contribution_ratio * 100.0, 4),
                }
            )
        return PerformanceBreakdownResult(
            status="PERFORMANCE_BREAKDOWN_READY",
            ready=True,
            contribution_count=len(contributions),
            total_contribution=round(total_profit, 6),
            contributions=tuple(contributions),
            reason="performance_breakdown_calculated",
        )
