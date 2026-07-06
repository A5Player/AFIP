"""Adaptive AI foundation runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .foundation_policy import AdaptiveAIFoundationPolicy
from .foundation_report import AdaptiveAIFoundationReport
from .foundation_repository import AdaptiveAIFoundationRepository


class AdaptiveAIFoundationRuntime:
    """Build adaptive AI foundation context from regime-first market knowledge."""

    def __init__(self, policy: AdaptiveAIFoundationPolicy | None = None) -> None:
        self.policy = policy or AdaptiveAIFoundationPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> AdaptiveAIFoundationReport:
        repository = AdaptiveAIFoundationRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles, invalid_regime_count=repository.invalid_regime_count)
        return AdaptiveAIFoundationReport(decision=decision, profiles=profiles)
