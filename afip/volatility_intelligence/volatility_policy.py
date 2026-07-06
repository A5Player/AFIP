"""Production Milestone E Pack 2 volatility intelligence policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .volatility_profile import VolatilityProfile


@dataclass(frozen=True)
class VolatilityIntelligenceDecision:
    """Deterministic decision describing volatility intelligence readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class VolatilityIntelligencePolicy:
    """Select the strongest data-derived market-regime volatility profile."""

    def decide(self, profiles: Tuple[VolatilityProfile, ...]) -> VolatilityIntelligenceDecision:
        if not profiles:
            return VolatilityIntelligenceDecision(
                status="VOLATILITY_INTELLIGENCE_WAIT",
                action="WAIT",
                reason="no_usable_volatility_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return VolatilityIntelligenceDecision(
                status="VOLATILITY_INTELLIGENCE_WAIT",
                action="WAIT",
                reason="insufficient_volatility_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.volatility_edge_score,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return VolatilityIntelligenceDecision(
            status="VOLATILITY_INTELLIGENCE_READY",
            action="USE_VOLATILITY_CONTEXT",
            reason="volatility_profile_ready",
            selected_profile_key=selected.profile_key,
        )
