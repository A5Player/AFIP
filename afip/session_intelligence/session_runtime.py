"""Production Milestone E Pack 1 session intelligence runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .session_policy import SessionIntelligencePolicy
from .session_report import SessionIntelligenceReport
from .session_repository import SessionRepository


class SessionIntelligenceRuntime:
    """Build deterministic session intelligence from regime-first observations."""

    def __init__(self, policy: SessionIntelligencePolicy | None = None) -> None:
        self.policy = policy or SessionIntelligencePolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> SessionIntelligenceReport:
        repository = SessionRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return SessionIntelligenceReport.from_profiles(profiles, decision)
