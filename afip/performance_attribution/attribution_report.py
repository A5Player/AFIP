"""Production Milestone E Pack 6 performance attribution report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .attribution_policy import PerformanceAttributionDecision
from .attribution_profile import PerformanceAttributionProfile


@dataclass(frozen=True)
class PerformanceAttributionReport:
    """Immutable report for performance attribution runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_attribution_source: str
    selected_direction: str
    total_net_pnl: float
    average_contribution_score: float
    average_decision_alignment_rate: float
    average_execution_quality_score: float
    average_drawdown_impact: float
    attribution_efficiency_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(
        cls,
        profiles: Tuple[PerformanceAttributionProfile, ...],
        decision: PerformanceAttributionDecision,
    ) -> "PerformanceAttributionReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_attribution_source=selected.attribution_source if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            total_net_pnl=selected.total_net_pnl if selected else 0.0,
            average_contribution_score=selected.average_contribution_score if selected else 0.0,
            average_decision_alignment_rate=selected.average_decision_alignment_rate if selected else 0.0,
            average_execution_quality_score=selected.average_execution_quality_score if selected else 0.0,
            average_drawdown_impact=selected.average_drawdown_impact if selected else 0.0,
            attribution_efficiency_score=selected.attribution_efficiency_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "PERFORMANCE_ATTRIBUTION_READY" and selected is not None,
        )
