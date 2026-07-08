"""Production operations profile for Production Freeze Pack P4."""

from __future__ import annotations

from dataclasses import dataclass

from .operations_observation import ProductionOperationsObservation


@dataclass(frozen=True)
class ProductionOperationsProfile:
    """Deterministic deployment and operations readiness profile."""

    market_regime: str
    signal_context: str
    status: str
    reason: str
    deployment_score: float
    resolution_score: float
    operations_score: float
    unresolved_operations_items: int
    source: str

    @classmethod
    def from_observation(cls, observation: ProductionOperationsObservation, *, status: str, reason: str) -> "ProductionOperationsProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            status=status,
            reason=reason,
            deployment_score=observation.deployment_score,
            resolution_score=observation.resolution_score,
            operations_score=observation.operations_score,
            unresolved_operations_items=observation.unresolved_operations_items,
            source=observation.source,
        )

    @property
    def operations_gate(self) -> str:
        if self.status == "READY":
            return "PRODUCTION_OPERATIONS_READY"
        if self.status == "REVIEW":
            return "REVIEW_REQUIRED"
        return "BLOCKED"
