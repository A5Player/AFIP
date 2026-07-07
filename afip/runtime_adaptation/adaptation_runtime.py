"""Runtime adaptation planner."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .adaptation_observation import RuntimeAdaptationObservation
from .adaptation_policy import RuntimeAdaptationPolicy
from .adaptation_report import RuntimeAdaptationReport
from .adaptation_repository import RuntimeAdaptationRepository


class RuntimeAdaptationRuntime:
    """Create deterministic runtime adaptation plans from strategy evolution evidence."""

    def __init__(
        self,
        repository: RuntimeAdaptationRepository | None = None,
        policy: RuntimeAdaptationPolicy | None = None,
    ) -> None:
        self._repository = repository or RuntimeAdaptationRepository()
        self._policy = policy or RuntimeAdaptationPolicy()

    def run(self, records: Sequence[Mapping[str, Any]]) -> RuntimeAdaptationReport:
        observations = tuple(RuntimeAdaptationObservation.from_mapping(item) for item in records)
        valid = tuple(item for item in observations if item.has_market_regime)
        invalid_market_regime_count = len(observations) - len(valid)
        profiles = self._repository.build_profiles(valid)
        decision = self._policy.decide(profiles, invalid_market_regime_count=invalid_market_regime_count)
        return RuntimeAdaptationReport(decision=decision, profiles=profiles)
