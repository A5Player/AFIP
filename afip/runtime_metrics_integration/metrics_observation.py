"""Runtime metrics observation contract for Production Milestone G Pack 4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimeMetricsObservation:
    """Normalized runtime performance evidence for deterministic production review."""

    market_regime: str
    signal_context: str
    runtime_component: str
    feature_flag_state: str
    configuration_version: str
    decision_latency_ms: float
    engine_latency_ms: float
    memory_usage_mb: float
    memory_limit_mb: float
    cache_hit_ratio: float
    event_log_score: float
    observability_score: float
    measurement_quality: float
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RuntimeMetricsObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        runtime_component = str(value.get("runtime_component", value.get("component", "AFIP_RUNTIME"))).strip().upper() or "AFIP_RUNTIME"
        feature_flag_state = _state(value.get("feature_flag_state", value.get("flag_state", "ON")))
        configuration_version = str(value.get("configuration_version", value.get("config_version", "v1"))).strip() or "v1"
        decision_latency_ms = _non_negative(value.get("decision_latency_ms", value.get("decision_time_ms", 0.0)))
        engine_latency_ms = _non_negative(value.get("engine_latency_ms", value.get("engine_time_ms", decision_latency_ms)))
        memory_usage_mb = _non_negative(value.get("memory_usage_mb", value.get("memory_mb", 0.0)))
        memory_limit_mb = _non_negative(value.get("memory_limit_mb", value.get("memory_budget_mb", 1.0))) or 1.0
        cache_hit_ratio = _ratio(value.get("cache_hit_ratio", value.get("cache_hit", 0.0)))
        event_log_score = _ratio(value.get("event_log_score", value.get("production_event_score", 0.0)))
        observability_score = _ratio(value.get("observability_score", value.get("runtime_observability_score", event_log_score)))
        measurement_quality = _ratio(value.get("measurement_quality", value.get("metrics_quality", observability_score)))
        source = str(value.get("source", value.get("event_source", "RUNTIME_METRICS_INTEGRATION"))).strip().upper() or "RUNTIME_METRICS_INTEGRATION"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            runtime_component=runtime_component,
            feature_flag_state=feature_flag_state,
            configuration_version=configuration_version,
            decision_latency_ms=decision_latency_ms,
            engine_latency_ms=engine_latency_ms,
            memory_usage_mb=memory_usage_mb,
            memory_limit_mb=memory_limit_mb,
            cache_hit_ratio=cache_hit_ratio,
            event_log_score=event_log_score,
            observability_score=observability_score,
            measurement_quality=measurement_quality,
            source=source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def has_configuration_version(self) -> bool:
        return bool(self.configuration_version)

    @property
    def feature_flag_enabled(self) -> bool:
        return self.feature_flag_state == "ON"

    @property
    def memory_usage_ratio(self) -> float:
        value = self.memory_usage_mb / self.memory_limit_mb
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def latency_efficiency(self) -> float:
        decision_score = _latency_score(self.decision_latency_ms, 1200.0)
        engine_score = _latency_score(self.engine_latency_ms, 900.0)
        return round(decision_score * 0.55 + engine_score * 0.45, 6)

    @property
    def resource_efficiency(self) -> float:
        memory_score = 1.0 - self.memory_usage_ratio
        value = memory_score * 0.60 + self.cache_hit_ratio * 0.40
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def evidence_quality(self) -> float:
        value = (
            self.event_log_score * 0.22
            + self.observability_score * 0.22
            + self.measurement_quality * 0.20
            + self.latency_efficiency * 0.18
            + self.resource_efficiency * 0.18
        )
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _non_negative(value: Any) -> float:
    return max(float(value), 0.0)


def _latency_score(value_ms: float, target_ms: float) -> float:
    if target_ms <= 0:
        return 0.0
    value = 1.0 - min(value_ms / target_ms, 1.0)
    return min(max(value, 0.0), 1.0)


def _state(value: Any) -> str:
    if isinstance(value, bool):
        return "ON" if value else "OFF"
    text = str(value).strip().upper()
    if text in {"1", "TRUE", "YES", "ENABLED", "ENABLE", "ON"}:
        return "ON"
    if text in {"0", "FALSE", "NO", "DISABLED", "DISABLE", "OFF"}:
        return "OFF"
    if text == "REVIEW":
        return "REVIEW"
    return text or "OFF"
