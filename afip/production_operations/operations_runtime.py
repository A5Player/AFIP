"""Production operations runtime for Production Freeze Pack P4."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .operations_observation import ProductionOperationsObservation
from .operations_policy import ProductionOperationsPolicy
from .operations_profile import ProductionOperationsProfile
from .operations_report import ProductionOperationsReport
from .operations_repository import ProductionOperationsRepository


class ProductionOperationsRuntime:
    """Evaluates deployment and operations readiness without changing trading decisions."""

    def __init__(self, policy: ProductionOperationsPolicy | None = None, repository: ProductionOperationsRepository | None = None) -> None:
        self.policy = policy or ProductionOperationsPolicy()
        self.repository = repository or ProductionOperationsRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionOperationsProfile:
        observation = ProductionOperationsObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = ProductionOperationsProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionOperationsProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> ProductionOperationsReport:
        return ProductionOperationsReport(self.evaluate_one(record))
