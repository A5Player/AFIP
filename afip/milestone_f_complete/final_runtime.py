"""Milestone F completion runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .final_observation import MilestoneFCompletionObservation
from .final_policy import MilestoneFCompletionPolicy
from .final_report import MilestoneFCompletionReport
from .final_repository import MilestoneFCompletionRepository


class MilestoneFCompletionRuntime:
    """Finalize Milestone F using production readiness evidence without enabling live execution."""

    def __init__(
        self,
        repository: MilestoneFCompletionRepository | None = None,
        policy: MilestoneFCompletionPolicy | None = None,
    ) -> None:
        self._repository = repository or MilestoneFCompletionRepository()
        self._policy = policy or MilestoneFCompletionPolicy()

    def run(self, records: Sequence[Mapping[str, Any]]) -> MilestoneFCompletionReport:
        observations = tuple(MilestoneFCompletionObservation.from_mapping(item) for item in records)
        valid = tuple(item for item in observations if item.has_market_regime)
        invalid_market_regime_count = len(observations) - len(valid)
        profiles = self._repository.build_profiles(valid)
        decision = self._policy.decide(profiles, invalid_market_regime_count=invalid_market_regime_count)
        return MilestoneFCompletionReport(decision=decision, profiles=profiles)
