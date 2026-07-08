"""Production acceptance test runtime for Production Freeze Pack P2."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .acceptance_observation import ProductionAcceptanceTestObservation
from .acceptance_policy import ProductionAcceptanceTestPolicy
from .acceptance_profile import ProductionAcceptanceTestProfile
from .acceptance_report import ProductionAcceptanceTestReport
from .acceptance_repository import ProductionAcceptanceTestRepository


class ProductionAcceptanceTestRuntime:
    """Evaluates production scenario readiness without changing trading decisions."""

    def __init__(self, policy: ProductionAcceptanceTestPolicy | None = None, repository: ProductionAcceptanceTestRepository | None = None) -> None:
        self.policy = policy or ProductionAcceptanceTestPolicy()
        self.repository = repository or ProductionAcceptanceTestRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionAcceptanceTestProfile:
        observation = ProductionAcceptanceTestObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = ProductionAcceptanceTestProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionAcceptanceTestProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> ProductionAcceptanceTestReport:
        return ProductionAcceptanceTestReport(self.evaluate_one(record))
