"""Production Milestone E Pack 1 session intelligence report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .session_policy import SessionIntelligenceDecision
from .session_profile import SessionProfile


@dataclass(frozen=True)
class SessionIntelligenceReport:
    """Immutable report for session intelligence runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_session: str
    selected_overlap: str
    selected_direction: str
    session_strength_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(
        cls,
        profiles: Tuple[SessionProfile, ...],
        decision: SessionIntelligenceDecision,
    ) -> "SessionIntelligenceReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_session=selected.session_key if selected else "UNKNOWN",
            selected_overlap=selected.overlap_key if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            session_strength_score=selected.session_strength_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "SESSION_INTELLIGENCE_READY" and bool(selected and selected.is_ready),
        )
