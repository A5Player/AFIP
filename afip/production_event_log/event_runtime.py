"""Production event log runtime for Production Milestone G Pack 2."""

from __future__ import annotations

from typing import Iterable, Mapping, Any

from .event_observation import ProductionEventObservation
from .event_policy import ProductionEventPolicy
from .event_profile import ProductionEventProfile
from .event_report import ProductionEventReport
from .event_repository import ProductionEventRepository


class ProductionEventRuntime:
    """Evaluates runtime event records without changing trading decisions or configuration files."""

    def __init__(self, policy: ProductionEventPolicy | None = None, repository: ProductionEventRepository | None = None) -> None:
        self.policy = policy or ProductionEventPolicy()
        self.repository = repository or ProductionEventRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionEventProfile:
        observation = ProductionEventObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = ProductionEventProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionEventProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> ProductionEventReport:
        return ProductionEventReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionEventReport]:
        return [self.explain_one(record) for record in records]
