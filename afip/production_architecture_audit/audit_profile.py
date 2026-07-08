"""Production architecture audit profile for Production Freeze Pack P1."""

from __future__ import annotations

from dataclasses import dataclass

from .audit_observation import ProductionArchitectureAuditObservation


@dataclass(frozen=True)
class ProductionArchitectureAuditProfile:
    market_regime: str
    signal_context: str
    execution_mode: str
    architecture_quality: float
    finding_quality: float
    audit_score: float
    duplicate_logic_findings: int
    circular_dependency_findings: int
    unresolved_findings: int
    status: str
    reason: str

    @classmethod
    def from_observation(
        cls,
        observation: ProductionArchitectureAuditObservation,
        *,
        status: str,
        reason: str,
    ) -> "ProductionArchitectureAuditProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            execution_mode=observation.execution_mode,
            architecture_quality=observation.architecture_quality,
            finding_quality=observation.finding_quality,
            audit_score=observation.audit_score,
            duplicate_logic_findings=observation.duplicate_logic_findings,
            circular_dependency_findings=observation.circular_dependency_findings,
            unresolved_findings=observation.unresolved_findings,
            status=status,
            reason=reason,
        )

    @property
    def audit_gate(self) -> str:
        if self.status == "READY":
            return "PRODUCTION_ARCHITECTURE_AUDIT_READY"
        if self.status == "BLOCKED":
            return "BLOCKED"
        return "REVIEW_REQUIRED"
