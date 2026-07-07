"""Adaptive confidence runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .confidence_policy import AdaptiveConfidencePolicy
from .confidence_report import AdaptiveConfidenceReport
from .confidence_repository import AdaptiveConfidenceRepository


class AdaptiveConfidenceRuntime:
    """Build deterministic adaptive confidence profiles from validated evidence."""

    def __init__(self, policy: AdaptiveConfidencePolicy | None = None) -> None:
        self.policy = policy or AdaptiveConfidencePolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> AdaptiveConfidenceReport:
        repository = AdaptiveConfidenceRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(
            profiles,
            invalid_market_regime_count=repository.invalid_market_regime_count,
        )
        return AdaptiveConfidenceReport(decision=decision, profiles=profiles)
