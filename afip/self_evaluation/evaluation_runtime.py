"""Self evaluation runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .evaluation_policy import SelfEvaluationPolicy
from .evaluation_report import SelfEvaluationReport
from .evaluation_repository import SelfEvaluationRepository


class SelfEvaluationRuntime:
    """Evaluate closed decisions before any adaptive learning is accepted."""

    def __init__(self, policy: SelfEvaluationPolicy | None = None) -> None:
        self.policy = policy or SelfEvaluationPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> SelfEvaluationReport:
        repository = SelfEvaluationRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(
            profiles,
            invalid_market_regime_count=repository.invalid_market_regime_count,
        )
        return SelfEvaluationReport(decision=decision, profiles=profiles)
