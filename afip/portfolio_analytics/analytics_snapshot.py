"""Portfolio analytics snapshot builder."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsSnapshot:
    """Consolidated portfolio analytics snapshot."""

    status: str
    ready: bool
    equity_trend_status: str
    risk_efficiency_status: str
    allocation_efficiency_status: str
    trend_direction: str
    trend_strength_percent: float
    risk_efficiency_ratio: float
    capital_utilization_percent: float
    failed_rules: tuple[str, ...]
