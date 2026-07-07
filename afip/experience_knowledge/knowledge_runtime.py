"""Experience knowledge runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .knowledge_policy import ExperienceKnowledgePolicy
from .knowledge_report import ExperienceKnowledgeReport
from .knowledge_repository import ExperienceKnowledgeRepository


class ExperienceKnowledgeRuntime:
    """Build deterministic experience knowledge profiles from closed evidence."""

    def __init__(self, policy: ExperienceKnowledgePolicy | None = None) -> None:
        self.policy = policy or ExperienceKnowledgePolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> ExperienceKnowledgeReport:
        repository = ExperienceKnowledgeRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(
            profiles,
            invalid_market_regime_count=repository.invalid_market_regime_count,
        )
        return ExperienceKnowledgeReport(decision=decision, profiles=profiles)
