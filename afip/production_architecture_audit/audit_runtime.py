"""Production architecture audit runtime for Production Freeze Pack P1."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .audit_observation import ProductionArchitectureAuditObservation
from .audit_policy import ProductionArchitectureAuditPolicy
from .audit_profile import ProductionArchitectureAuditProfile
from .audit_report import ProductionArchitectureAuditReport
from .audit_repository import ProductionArchitectureAuditRepository


class ProductionArchitectureAuditRuntime:
    """Evaluates architecture audit evidence without modifying trading decisions."""

    def __init__(self, policy: ProductionArchitectureAuditPolicy | None = None, repository: ProductionArchitectureAuditRepository | None = None) -> None:
        self.policy = policy or ProductionArchitectureAuditPolicy()
        self.repository = repository or ProductionArchitectureAuditRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionArchitectureAuditProfile:
        observation = ProductionArchitectureAuditObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = ProductionArchitectureAuditProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[ProductionArchitectureAuditProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> ProductionArchitectureAuditReport:
        return ProductionArchitectureAuditReport(self.evaluate_one(record))
