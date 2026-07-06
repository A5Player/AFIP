"""Production Milestone E Pack 3 market memory policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .memory_profile import MarketMemoryProfile


@dataclass(frozen=True)
class MarketMemoryDecision:
    """Deterministic decision describing market memory readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class MarketMemoryPolicy:
    """Select the strongest data-derived market memory profile."""

    def decide(self, profiles: Tuple[MarketMemoryProfile, ...]) -> MarketMemoryDecision:
        if not profiles:
            return MarketMemoryDecision(
                status="MARKET_MEMORY_WAIT",
                action="WAIT",
                reason="no_usable_market_memory_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return MarketMemoryDecision(
                status="MARKET_MEMORY_WAIT",
                action="WAIT",
                reason="insufficient_market_memory_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.memory_edge_score,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return MarketMemoryDecision(
            status="MARKET_MEMORY_READY",
            action="USE_MARKET_MEMORY_CONTEXT",
            reason="market_memory_profile_ready",
            selected_profile_key=selected.profile_key,
        )
