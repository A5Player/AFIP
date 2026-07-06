"""Production Milestone E Pack 2 volatility intelligence report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .volatility_policy import VolatilityIntelligenceDecision
from .volatility_profile import VolatilityProfile


@dataclass(frozen=True)
class VolatilityIntelligenceReport:
    """Immutable report for volatility intelligence runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_volatility_state: str
    selected_direction: str
    average_atr_points: float
    volatility_edge_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(
        cls,
        profiles: Tuple[VolatilityProfile, ...],
        decision: VolatilityIntelligenceDecision,
    ) -> "VolatilityIntelligenceReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_volatility_state=selected.volatility_state if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            average_atr_points=selected.average_atr_points if selected else 0.0,
            volatility_edge_score=selected.volatility_edge_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "VOLATILITY_INTELLIGENCE_READY" and selected is not None,
        )
