"""Production release candidate runtime for Production Milestone G Pack 8."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .rc_observation import ProductionReleaseCandidateObservation
from .rc_policy import ProductionReleaseCandidatePolicy
from .rc_profile import ProductionReleaseCandidateProfile
from .rc_report import ProductionReleaseCandidateReport
from .rc_repository import ProductionReleaseCandidateRepository


class ProductionReleaseCandidateRuntime:
    """Evaluates RC readiness without changing trading decisions or live execution."""

    def __init__(
        self,
        policy: ProductionReleaseCandidatePolicy | None = None,
        repository: ProductionReleaseCandidateRepository | None = None,
    ) -> None:
        self.policy = policy or ProductionReleaseCandidatePolicy()
        self.repository = repository or ProductionReleaseCandidateRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionReleaseCandidateProfile:
        observation = ProductionReleaseCandidateObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = ProductionReleaseCandidateProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionReleaseCandidateProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> ProductionReleaseCandidateReport:
        return ProductionReleaseCandidateReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionReleaseCandidateReport]:
        return [self.explain_one(record) for record in records]
