"""Runtime metrics profile for Production Milestone G Pack 4."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics_observation import RuntimeMetricsObservation


@dataclass(frozen=True)
class RuntimeMetricsProfile:
    """Deterministic runtime metrics profile for production performance review."""

    market_regime: str
    signal_context: str
    runtime_component: str
    feature_flag_state: str
    configuration_version: str
    decision_latency_ms: float
    engine_latency_ms: float
    memory_usage_ratio: float
    cache_hit_ratio: float
    latency_score: float
    resource_score: float
    evidence_quality: float
    status: str
    review_required: bool
    reason: str

    @classmethod
    def from_observation(cls, observation: RuntimeMetricsObservation, status: str, reason: str) -> "RuntimeMetricsProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            runtime_component=observation.runtime_component,
            feature_flag_state=observation.feature_flag_state,
            configuration_version=observation.configuration_version,
            decision_latency_ms=round(observation.decision_latency_ms, 4),
            engine_latency_ms=round(observation.engine_latency_ms, 4),
            memory_usage_ratio=round(observation.memory_usage_ratio, 4),
            cache_hit_ratio=round(observation.cache_hit_ratio, 4),
            latency_score=round(observation.latency_efficiency, 4),
            resource_score=round(observation.resource_efficiency, 4),
            evidence_quality=round(observation.evidence_quality, 4),
            status=status,
            review_required=status != "READY",
            reason=reason,
        )

    @property
    def bottleneck(self) -> str:
        if self.memory_usage_ratio >= 0.85:
            return "MEMORY_USAGE"
        if self.latency_score < 0.35:
            return "LATENCY"
        if self.resource_score < 0.35:
            return "RESOURCE_EFFICIENCY"
        return "NONE"
