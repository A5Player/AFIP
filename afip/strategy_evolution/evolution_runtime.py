"""Strategy evolution runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .evolution_observation import StrategyEvolutionObservation
from .evolution_policy import StrategyEvolutionPolicy
from .evolution_report import StrategyEvolutionReport
from .evolution_repository import StrategyEvolutionRepository


class StrategyEvolutionRuntime:
    """Create deterministic strategy evolution candidates from experience knowledge."""

    def __init__(
        self,
        repository: StrategyEvolutionRepository | None = None,
        policy: StrategyEvolutionPolicy | None = None,
    ) -> None:
        self._repository = repository or StrategyEvolutionRepository()
        self._policy = policy or StrategyEvolutionPolicy()

    def run(self, records: Sequence[Mapping[str, Any]]) -> StrategyEvolutionReport:
        observations = tuple(StrategyEvolutionObservation.from_mapping(item) for item in records)
        valid = tuple(item for item in observations if item.has_market_regime)
        invalid_market_regime_count = len(observations) - len(valid)
        profiles = self._repository.build_profiles(valid)
        decision = self._policy.decide(profiles, invalid_market_regime_count=invalid_market_regime_count)
        return StrategyEvolutionReport(decision=decision, profiles=profiles)
