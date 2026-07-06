"""Production Milestone E Pack 6 performance attribution policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .attribution_profile import PerformanceAttributionProfile


@dataclass(frozen=True)
class PerformanceAttributionDecision:
    """Deterministic decision describing attribution readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class PerformanceAttributionPolicy:
    """Select the strongest data-derived performance attribution profile."""

    def decide(self, profiles: Tuple[PerformanceAttributionProfile, ...]) -> PerformanceAttributionDecision:
        if not profiles:
            return PerformanceAttributionDecision(
                status="PERFORMANCE_ATTRIBUTION_WAIT",
                action="WAIT",
                reason="no_usable_performance_attribution_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return PerformanceAttributionDecision(
                status="PERFORMANCE_ATTRIBUTION_WAIT",
                action="WAIT",
                reason="insufficient_performance_attribution_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.attribution_efficiency_score,
                -item.total_net_pnl,
                item.average_drawdown_impact,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return PerformanceAttributionDecision(
            status="PERFORMANCE_ATTRIBUTION_READY",
            action="APPLY_PERFORMANCE_ATTRIBUTION",
            reason="performance_attribution_profile_ready",
            selected_profile_key=selected.profile_key,
        )
