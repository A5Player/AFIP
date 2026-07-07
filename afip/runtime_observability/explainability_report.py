"""Runtime explainability report builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .metrics_profile import RuntimeObservabilityProfile


@dataclass(frozen=True)
class RuntimeExplainabilityReport:
    """Compact deterministic explanation for runtime observability decisions."""

    market_regime: str
    signal_context: str
    status: str
    reason: str
    observability_score: float
    explanation_lines: Tuple[str, ...]

    @classmethod
    def from_profile(cls, profile: RuntimeObservabilityProfile) -> "RuntimeExplainabilityReport":
        lines = (
            f"Market regime: {profile.market_regime}",
            f"Signal context: {profile.signal_context}",
            f"Runtime observability score: {profile.observability_score:.4f}",
            f"Latency score: {profile.latency_score:.4f}",
            f"Memory score: {profile.memory_score:.4f}",
            f"Evidence quality: {profile.evidence_quality:.4f}",
            f"Explainability quality: {profile.explainability_quality:.4f}",
            f"Metrics quality: {profile.metrics_quality:.4f}",
            f"Monitoring quality: {profile.monitoring_quality:.4f}",
            f"Production readiness: {profile.production_readiness_score:.4f}",
            f"Decision status: {profile.status}",
            f"Decision reason: {profile.reason}",
        )
        return cls(
            market_regime=profile.market_regime,
            signal_context=profile.signal_context,
            status=profile.status,
            reason=profile.reason,
            observability_score=profile.observability_score,
            explanation_lines=lines,
        )

    def as_text(self) -> str:
        return "\n".join(self.explanation_lines)
