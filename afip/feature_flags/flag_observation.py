"""Feature flag observation contract for Production Milestone G Pack 3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class FeatureFlagObservation:
    """Normalized feature flag evidence for deterministic production control review."""

    market_regime: str
    signal_context: str
    feature_name: str
    current_state: str
    requested_state: str
    configuration_version: str
    production_event_score: float
    observability_score: float
    rollout_quality: float
    rollback_quality: float
    dependency_quality: float
    operator_review_quality: float
    audit_quality: float
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FeatureFlagObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        feature_name = str(value.get("feature_name", value.get("feature", "RUNTIME_FEATURE"))).strip().upper() or "RUNTIME_FEATURE"
        current_state = _state(value.get("current_state", value.get("enabled", "OFF")))
        requested_state = _state(value.get("requested_state", value.get("desired_state", current_state)))
        configuration_version = str(value.get("configuration_version", value.get("config_version", "v1"))).strip() or "v1"
        production_event_score = _ratio(value.get("production_event_score", value.get("event_log_score", 0.0)))
        observability_score = _ratio(value.get("observability_score", value.get("runtime_observability_score", production_event_score)))
        rollout_quality = _ratio(value.get("rollout_quality", value.get("change_quality", observability_score)))
        rollback_quality = _ratio(value.get("rollback_quality", rollout_quality))
        dependency_quality = _ratio(value.get("dependency_quality", value.get("dependency_check_quality", rollback_quality)))
        operator_review_quality = _ratio(value.get("operator_review_quality", value.get("review_quality", dependency_quality)))
        audit_quality = _ratio(value.get("audit_quality", value.get("traceability_quality", operator_review_quality)))
        source = str(value.get("source", value.get("event_source", "FEATURE_FLAG_FRAMEWORK"))).strip().upper() or "FEATURE_FLAG_FRAMEWORK"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            feature_name=feature_name,
            current_state=current_state,
            requested_state=requested_state,
            configuration_version=configuration_version,
            production_event_score=production_event_score,
            observability_score=observability_score,
            rollout_quality=rollout_quality,
            rollback_quality=rollback_quality,
            dependency_quality=dependency_quality,
            operator_review_quality=operator_review_quality,
            audit_quality=audit_quality,
            source=source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def has_configuration_version(self) -> bool:
        return bool(self.configuration_version)

    @property
    def state_changed(self) -> bool:
        return self.current_state != self.requested_state

    @property
    def evidence_quality(self) -> float:
        value = (
            self.production_event_score * 0.18
            + self.observability_score * 0.16
            + self.rollout_quality * 0.16
            + self.rollback_quality * 0.14
            + self.dependency_quality * 0.14
            + self.operator_review_quality * 0.12
            + self.audit_quality * 0.10
        )
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
