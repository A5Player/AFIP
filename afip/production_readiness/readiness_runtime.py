"""Production readiness runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .readiness_observation import ProductionReadinessObservation
from .readiness_policy import ProductionReadinessPolicy
from .readiness_report import ProductionReadinessReport
from .readiness_repository import ProductionReadinessRepository


class ProductionReadinessRuntime:
    """Review validated AI evidence and operational controls before production use."""

    def __init__(
        self,
        repository: ProductionReadinessRepository | None = None,
        policy: ProductionReadinessPolicy | None = None,
    ) -> None:
        self._repository = repository or ProductionReadinessRepository()
        self._policy = policy or ProductionReadinessPolicy()

    def run(self, records: Sequence[Mapping[str, Any]]) -> ProductionReadinessReport:
        observations = tuple(ProductionReadinessObservation.from_mapping(item) for item in records)
        valid = tuple(item for item in observations if item.has_market_regime)
        invalid_market_regime_count = len(observations) - len(valid)
        profiles = self._repository.build_profiles(valid)
        decision = self._policy.decide(profiles, invalid_market_regime_count=invalid_market_regime_count)
        return ProductionReadinessReport(decision=decision, profiles=profiles)
