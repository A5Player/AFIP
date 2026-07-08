"""Production documentation runtime for Production Freeze Pack P3."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .documentation_observation import ProductionDocumentationObservation
from .documentation_policy import ProductionDocumentationPolicy
from .documentation_profile import ProductionDocumentationProfile
from .documentation_report import ProductionDocumentationReport
from .documentation_repository import ProductionDocumentationRepository


class ProductionDocumentationRuntime:
    """Evaluates documentation readiness without changing trading decisions."""

    def __init__(self, policy: ProductionDocumentationPolicy | None = None, repository: ProductionDocumentationRepository | None = None) -> None:
        self.policy = policy or ProductionDocumentationPolicy()
        self.repository = repository or ProductionDocumentationRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionDocumentationProfile:
        observation = ProductionDocumentationObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = ProductionDocumentationProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionDocumentationProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> ProductionDocumentationReport:
        return ProductionDocumentationReport(self.evaluate_one(record))
