"""Runtime observability profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeObservabilityProfile:
    """Deterministic profile used to audit runtime efficiency and explanation completeness."""

    market_regime: str
    signal_context: str
    observability_score: float
    latency_score: float
    memory_score: float
    evidence_quality: float
    explainability_quality: float
    metrics_quality: float
    monitoring_quality: float
    production_readiness_score: float
    status: str
    review_required: bool
    reason: str

    @property
    def is_ready(self) -> bool:
        return self.status == "READY" and not self.review_required
