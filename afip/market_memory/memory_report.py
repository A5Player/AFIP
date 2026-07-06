"""Production Milestone E Pack 3 market memory report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .memory_policy import MarketMemoryDecision
from .memory_profile import MarketMemoryProfile


@dataclass(frozen=True)
class MarketMemoryReport:
    """Immutable report for market memory runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_memory_pattern: str
    selected_direction: str
    average_similarity_score: float
    memory_edge_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(
        cls,
        profiles: Tuple[MarketMemoryProfile, ...],
        decision: MarketMemoryDecision,
    ) -> "MarketMemoryReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_memory_pattern=selected.memory_pattern if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            average_similarity_score=selected.average_similarity_score if selected else 0.0,
            memory_edge_score=selected.memory_edge_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "MARKET_MEMORY_READY" and selected is not None,
        )
