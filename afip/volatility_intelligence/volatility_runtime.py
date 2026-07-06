"""Production Milestone E Pack 2 volatility intelligence runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .volatility_policy import VolatilityIntelligencePolicy
from .volatility_report import VolatilityIntelligenceReport
from .volatility_repository import VolatilityRepository


class VolatilityIntelligenceRuntime:
    """Build deterministic volatility intelligence from regime-first observations."""

    def __init__(self, policy: VolatilityIntelligencePolicy | None = None) -> None:
        self.policy = policy or VolatilityIntelligencePolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> VolatilityIntelligenceReport:
        repository = VolatilityRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return VolatilityIntelligenceReport.from_profiles(profiles, decision)
