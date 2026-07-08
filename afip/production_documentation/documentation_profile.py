"""Production documentation profile for Production Freeze Pack P3."""

from __future__ import annotations

from dataclasses import dataclass

from .documentation_observation import ProductionDocumentationObservation


@dataclass(frozen=True)
class ProductionDocumentationProfile:
    """Deterministic documentation readiness profile."""

    market_regime: str
    signal_context: str
    status: str
    reason: str
    coverage_score: float
    completeness_score: float
    documentation_score: float
    unresolved_documentation_items: int
    source: str

    @classmethod
    def from_observation(cls, observation: ProductionDocumentationObservation, *, status: str, reason: str) -> "ProductionDocumentationProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            status=status,
            reason=reason,
            coverage_score=observation.coverage_score,
            completeness_score=observation.completeness_score,
            documentation_score=observation.documentation_score,
            unresolved_documentation_items=observation.unresolved_documentation_items,
            source=observation.source,
        )

    @property
    def documentation_gate(self) -> str:
        if self.status == "READY":
            return "PRODUCTION_DOCUMENTATION_READY"
        if self.status == "REVIEW":
            return "REVIEW_REQUIRED"
        return "BLOCKED"
