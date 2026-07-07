"""Runtime observability policy for Production Milestone G Pack 1."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics_observation import RuntimeObservabilityObservation
from .metrics_profile import RuntimeObservabilityProfile


@dataclass(frozen=True)
class RuntimeObservabilityPolicy:
    """Thresholds for deterministic runtime metrics and explainability review."""

    max_total_latency_ms: float = 250.0
    max_memory_usage_mb: float = 512.0
    minimum_evidence_quality: float = 0.62
    minimum_explainability_quality: float = 0.64
    minimum_metrics_quality: float = 0.64
    minimum_monitoring_quality: float = 0.60
    minimum_observability_score: float = 0.65

    def evaluate(self, observation: RuntimeObservabilityObservation) -> RuntimeObservabilityProfile:
        if not observation.has_market_regime:
            return RuntimeObservabilityProfile(
                market_regime="UNKNOWN",
                signal_context=observation.signal_context,
                observability_score=0.0,
                latency_score=0.0,
                memory_score=0.0,
                evidence_quality=observation.evidence_quality,
                explainability_quality=observation.explainability_quality,
                metrics_quality=observation.metrics_quality,
                monitoring_quality=observation.monitoring_quality,
                production_readiness_score=observation.production_readiness_score,
                status="BLOCKED",
                review_required=True,
                reason="market_regime_required",
            )

        latency_score = _inverse_score(observation.total_latency_ms, self.max_total_latency_ms)
        memory_score = _inverse_score(observation.memory_usage_mb, self.max_memory_usage_mb)
        evidence_quality = observation.evidence_quality
        observability_score = round(
            latency_score * 0.20
            + memory_score * 0.15
            + evidence_quality * 0.20
            + observation.explainability_quality * 0.15
            + observation.metrics_quality * 0.15
            + observation.monitoring_quality * 0.10
            + observation.production_readiness_score * 0.05,
            6,
        )

        review_required = (
            evidence_quality < self.minimum_evidence_quality
            or observation.explainability_quality < self.minimum_explainability_quality
            or observation.metrics_quality < self.minimum_metrics_quality
            or observation.monitoring_quality < self.minimum_monitoring_quality
            or observability_score < self.minimum_observability_score
        )
        if observation.explainability_quality < self.minimum_explainability_quality:
            reason = "explainability_review_required"
        elif observation.metrics_quality < self.minimum_metrics_quality:
            reason = "runtime_metrics_review_required"
        elif observation.monitoring_quality < self.minimum_monitoring_quality:
            reason = "monitoring_review_required"
        elif evidence_quality < self.minimum_evidence_quality:
            reason = "evidence_review_required"
        elif observability_score < self.minimum_observability_score:
            reason = "observability_score_review_required"
        else:
            reason = "runtime_observability_ready"

        return RuntimeObservabilityProfile(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            observability_score=observability_score,
            latency_score=latency_score,
            memory_score=memory_score,
            evidence_quality=evidence_quality,
            explainability_quality=observation.explainability_quality,
            metrics_quality=observation.metrics_quality,
            monitoring_quality=observation.monitoring_quality,
            production_readiness_score=observation.production_readiness_score,
            status="REVIEW" if review_required else "READY",
            review_required=review_required,
            reason=reason,
        )


def _inverse_score(value: float, limit: float) -> float:
    if limit <= 0:
        return 0.0
    ratio = min(max(value / limit, 0.0), 1.0)
    return round(1.0 - ratio, 6)
