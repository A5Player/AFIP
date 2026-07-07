"""Runtime observability observation contract for Production Milestone G Pack 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimeObservabilityObservation:
    """Normalized runtime metrics and explainability evidence for deterministic audits."""

    market_regime: str
    signal_context: str
    decision_latency_ms: float
    engine_latency_ms: float
    validation_latency_ms: float
    report_latency_ms: float
    memory_usage_mb: float
    data_quality: float
    knowledge_quality: float
    strategy_quality: float
    validation_quality: float
    production_readiness_score: float
    explainability_quality: float
    metrics_quality: float
    monitoring_quality: float
    observability_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RuntimeObservabilityObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        decision_latency_ms = _non_negative(value.get("decision_latency_ms", value.get("runtime_latency_ms", 0.0)))
        engine_latency_ms = _non_negative(value.get("engine_latency_ms", value.get("processing_latency_ms", decision_latency_ms)))
        validation_latency_ms = _non_negative(value.get("validation_latency_ms", 0.0))
        report_latency_ms = _non_negative(value.get("report_latency_ms", value.get("explainability_latency_ms", 0.0)))
        memory_usage_mb = _non_negative(value.get("memory_usage_mb", value.get("memory_mb", 0.0)))
        data_quality = _ratio(value.get("data_quality", 0.0))
        knowledge_quality = _ratio(value.get("knowledge_quality", data_quality))
        strategy_quality = _ratio(value.get("strategy_quality", knowledge_quality))
        validation_quality = _ratio(value.get("validation_quality", strategy_quality))
        production_readiness_score = _ratio(value.get("production_readiness_score", value.get("readiness_score", validation_quality)))
        explainability_quality = _ratio(value.get("explainability_quality", value.get("explanation_quality", production_readiness_score)))
        metrics_quality = _ratio(value.get("metrics_quality", value.get("runtime_metrics_quality", explainability_quality)))
        monitoring_quality = _ratio(value.get("monitoring_quality", metrics_quality))
        observability_source = str(value.get("observability_source", value.get("source", "RUNTIME_OBSERVABILITY"))).strip().upper() or "RUNTIME_OBSERVABILITY"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            decision_latency_ms=decision_latency_ms,
            engine_latency_ms=engine_latency_ms,
            validation_latency_ms=validation_latency_ms,
            report_latency_ms=report_latency_ms,
            memory_usage_mb=memory_usage_mb,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            strategy_quality=strategy_quality,
            validation_quality=validation_quality,
            production_readiness_score=production_readiness_score,
            explainability_quality=explainability_quality,
            metrics_quality=metrics_quality,
            monitoring_quality=monitoring_quality,
            observability_source=observability_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def total_latency_ms(self) -> float:
        value = self.decision_latency_ms + self.engine_latency_ms + self.validation_latency_ms + self.report_latency_ms
        return round(value, 6)

    @property
    def evidence_quality(self) -> float:
        value = (
            self.data_quality * 0.20
            + self.knowledge_quality * 0.20
            + self.strategy_quality * 0.15
            + self.validation_quality * 0.15
            + self.production_readiness_score * 0.10
            + self.explainability_quality * 0.10
            + self.metrics_quality * 0.10
        )
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _non_negative(value: Any) -> float:
    return round(max(float(value), 0.0), 6)
