"""Production hardening observation contract for Production Milestone G Pack 5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionHardeningObservation:
    """Normalized integration evidence for deterministic production hardening review."""

    market_regime: str
    signal_context: str
    runtime_component: str
    feature_flag_state: str
    configuration_version: str
    observability_score: float
    event_log_score: float
    feature_flag_score: float
    runtime_metrics_score: float
    dependency_alignment: float
    rollback_readiness: float
    monitoring_coverage: float
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionHardeningObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        runtime_component = str(value.get("runtime_component", value.get("component", "AFIP_RUNTIME"))).strip().upper() or "AFIP_RUNTIME"
        feature_flag_state = _state(value.get("feature_flag_state", value.get("flag_state", "ON")))
        configuration_version = str(value.get("configuration_version", value.get("config_version", "v1"))).strip() or "v1"
        observability_score = _ratio(value.get("observability_score", value.get("runtime_observability_score", 0.0)))
        event_log_score = _ratio(value.get("event_log_score", value.get("production_event_score", 0.0)))
        feature_flag_score = _ratio(value.get("feature_flag_score", value.get("flag_quality", 0.0)))
        runtime_metrics_score = _ratio(value.get("runtime_metrics_score", value.get("metrics_score", 0.0)))
        dependency_alignment = _ratio(value.get("dependency_alignment", value.get("integration_alignment", 0.0)))
        rollback_readiness = _ratio(value.get("rollback_readiness", value.get("rollback_score", 0.0)))
        monitoring_coverage = _ratio(value.get("monitoring_coverage", value.get("monitoring_score", 0.0)))
        source = str(value.get("source", "PRODUCTION_HARDENING")).strip().upper() or "PRODUCTION_HARDENING"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            runtime_component=runtime_component,
            feature_flag_state=feature_flag_state,
            configuration_version=configuration_version,
            observability_score=observability_score,
            event_log_score=event_log_score,
            feature_flag_score=feature_flag_score,
            runtime_metrics_score=runtime_metrics_score,
            dependency_alignment=dependency_alignment,
            rollback_readiness=rollback_readiness,
            monitoring_coverage=monitoring_coverage,
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
    def integration_quality(self) -> float:
        value = (
            self.observability_score * 0.18
            + self.event_log_score * 0.18
            + self.feature_flag_score * 0.16
            + self.runtime_metrics_score * 0.18
            + self.dependency_alignment * 0.14
            + self.rollback_readiness * 0.08
            + self.monitoring_coverage * 0.08
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def hardening_score(self) -> float:
        value = self.integration_quality * 0.70 + min(self.rollback_readiness, self.monitoring_coverage) * 0.30
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


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
