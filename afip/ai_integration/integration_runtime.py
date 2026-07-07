"""AI integration runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .integration_observation import AIIntegrationObservation
from .integration_policy import AIIntegrationPolicy
from .integration_report import AIIntegrationReport
from .integration_repository import AIIntegrationRepository


class AIIntegrationRuntime:
    """Create deterministic AI assist plans from runtime adaptation evidence."""

    def __init__(
        self,
        repository: AIIntegrationRepository | None = None,
        policy: AIIntegrationPolicy | None = None,
    ) -> None:
        self._repository = repository or AIIntegrationRepository()
        self._policy = policy or AIIntegrationPolicy()

    def run(self, records: Sequence[Mapping[str, Any]]) -> AIIntegrationReport:
        observations = tuple(AIIntegrationObservation.from_mapping(item) for item in records)
        valid = tuple(item for item in observations if item.has_market_regime)
        invalid_market_regime_count = len(observations) - len(valid)
        profiles = self._repository.build_profiles(valid)
        decision = self._policy.decide(profiles, invalid_market_regime_count=invalid_market_regime_count)
        return AIIntegrationReport(decision=decision, profiles=profiles)
