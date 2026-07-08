"""Production hardening runtime for Production Milestone G Pack 5."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .hardening_observation import ProductionHardeningObservation
from .hardening_policy import ProductionHardeningPolicy
from .hardening_profile import ProductionHardeningProfile
from .hardening_report import ProductionHardeningReport
from .hardening_repository import ProductionHardeningRepository


class ProductionHardeningRuntime:
    """Reviews production integration readiness without changing trading decisions."""

    def __init__(self, policy: ProductionHardeningPolicy | None = None, repository: ProductionHardeningRepository | None = None) -> None:
        self.policy = policy or ProductionHardeningPolicy()
        self.repository = repository or ProductionHardeningRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionHardeningProfile:
        observation = ProductionHardeningObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = ProductionHardeningProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionHardeningProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> ProductionHardeningReport:
        return ProductionHardeningReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionHardeningReport]:
        return [self.explain_one(record) for record in records]
