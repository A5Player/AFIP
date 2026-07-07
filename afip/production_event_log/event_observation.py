"""Production event log observation contract for Production Milestone G Pack 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionEventObservation:
    """Normalized event and configuration evidence for deterministic runtime audit trails."""

    market_regime: str
    signal_context: str
    event_type: str
    event_sequence: int
    config_version: str
    previous_config_version: str
    runtime_observability_score: float
    explainability_quality: float
    event_completeness: float
    event_order_quality: float
    config_change_quality: float
    rollback_quality: float
    audit_quality: float
    event_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProductionEventObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        event_type = str(value.get("event_type", value.get("runtime_event", "RUNTIME_REVIEW"))).strip().upper() or "RUNTIME_REVIEW"
        event_sequence = _sequence(value.get("event_sequence", value.get("sequence", 0)))
        config_version = str(value.get("config_version", value.get("current_config_version", "v1"))).strip() or "v1"
        previous_config_version = str(value.get("previous_config_version", value.get("rollback_config_version", config_version))).strip() or config_version
        runtime_observability_score = _ratio(value.get("runtime_observability_score", value.get("observability_score", 0.0)))
        explainability_quality = _ratio(value.get("explainability_quality", runtime_observability_score))
        event_completeness = _ratio(value.get("event_completeness", value.get("event_quality", explainability_quality)))
        event_order_quality = _ratio(value.get("event_order_quality", value.get("ordering_quality", event_completeness)))
        config_change_quality = _ratio(value.get("config_change_quality", value.get("configuration_quality", event_order_quality)))
        rollback_quality = _ratio(value.get("rollback_quality", config_change_quality))
        audit_quality = _ratio(value.get("audit_quality", value.get("traceability_quality", rollback_quality)))
        event_source = str(value.get("event_source", value.get("source", "PRODUCTION_EVENT_LOG"))).strip().upper() or "PRODUCTION_EVENT_LOG"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            event_type=event_type,
            event_sequence=event_sequence,
            config_version=config_version,
            previous_config_version=previous_config_version,
            runtime_observability_score=runtime_observability_score,
            explainability_quality=explainability_quality,
            event_completeness=event_completeness,
            event_order_quality=event_order_quality,
            config_change_quality=config_change_quality,
            rollback_quality=rollback_quality,
            audit_quality=audit_quality,
            event_source=event_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def has_config_version(self) -> bool:
        return bool(self.config_version)

    @property
    def config_changed(self) -> bool:
        return self.config_version != self.previous_config_version

    @property
    def evidence_quality(self) -> float:
        value = (
            self.runtime_observability_score * 0.20
            + self.explainability_quality * 0.15
            + self.event_completeness * 0.15
            + self.event_order_quality * 0.15
            + self.config_change_quality * 0.15
            + self.rollback_quality * 0.10
            + self.audit_quality * 0.10
        )
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _sequence(value: Any) -> int:
    return max(int(value), 0)
