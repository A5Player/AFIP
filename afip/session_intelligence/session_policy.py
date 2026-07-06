"""Production Milestone E Pack 1 session intelligence policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .session_profile import SessionProfile


@dataclass(frozen=True)
class SessionIntelligenceDecision:
    """Deterministic decision describing session intelligence readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class SessionIntelligencePolicy:
    """Select the strongest data-derived market-session profile."""

    def decide(self, profiles: Tuple[SessionProfile, ...]) -> SessionIntelligenceDecision:
        if not profiles:
            return SessionIntelligenceDecision(
                status="SESSION_INTELLIGENCE_WAIT",
                action="WAIT",
                reason="no_usable_session_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return SessionIntelligenceDecision(
                status="SESSION_INTELLIGENCE_WAIT",
                action="WAIT",
                reason="insufficient_session_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.session_strength_score,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return SessionIntelligenceDecision(
            status="SESSION_INTELLIGENCE_READY",
            action="USE_SESSION_CONTEXT",
            reason="session_profile_ready",
            selected_profile_key=selected.profile_key,
        )
