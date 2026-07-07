"""Production event log profile for Pack G2."""

from __future__ import annotations

from dataclasses import dataclass

from .event_observation import ProductionEventObservation


@dataclass(frozen=True)
class ProductionEventProfile:
    """Deterministic runtime event log profile used for audit and rollback review."""

    market_regime: str
    signal_context: str
    event_type: str
    event_sequence: int
    config_version: str
    previous_config_version: str
    evidence_quality: float
    event_log_score: float
    configuration_score: float
    audit_score: float
    status: str
    review_required: bool
    reason: str

    @classmethod
    def from_observation(cls, observation: ProductionEventObservation, status: str, reason: str) -> "ProductionEventProfile":
        event_log_score = _event_log_score(observation)
        configuration_score = _configuration_score(observation)
        audit_score = _audit_score(observation)
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            event_type=observation.event_type,
            event_sequence=observation.event_sequence,
            config_version=observation.config_version,
            previous_config_version=observation.previous_config_version,
            evidence_quality=observation.evidence_quality,
            event_log_score=event_log_score,
            configuration_score=configuration_score,
            audit_score=audit_score,
            status=status,
            review_required=status != "READY",
            reason=reason,
        )


def _event_log_score(observation: ProductionEventObservation) -> float:
    value = observation.event_completeness * 0.45 + observation.event_order_quality * 0.35 + observation.runtime_observability_score * 0.20
    return round(min(max(value, 0.0), 1.0), 4)


def _configuration_score(observation: ProductionEventObservation) -> float:
    value = observation.config_change_quality * 0.55 + observation.rollback_quality * 0.45
    return round(min(max(value, 0.0), 1.0), 4)


def _audit_score(observation: ProductionEventObservation) -> float:
    value = observation.audit_quality * 0.50 + observation.explainability_quality * 0.30 + observation.event_order_quality * 0.20
    return round(min(max(value, 0.0), 1.0), 4)
