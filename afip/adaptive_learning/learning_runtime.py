"""Production Milestone E Pack 9 adaptive learning runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .learning_policy import AdaptiveLearningPolicy
from .learning_report import AdaptiveLearningReport
from .learning_repository import AdaptiveLearningRepository


class AdaptiveLearningRuntime:
    """Build deterministic adaptive learning context from regime-first observations."""

    def __init__(self, policy: AdaptiveLearningPolicy | None = None) -> None:
        self.policy = policy or AdaptiveLearningPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> AdaptiveLearningReport:
        repository = AdaptiveLearningRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return AdaptiveLearningReport.from_profiles(profiles, decision)
