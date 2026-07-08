"""Feature flag profile for Production Milestone G Pack 3."""

from __future__ import annotations

from dataclasses import dataclass

from .flag_observation import FeatureFlagObservation


@dataclass(frozen=True)
class FeatureFlagProfile:
    """Deterministic feature flag readiness profile for production control."""

    market_regime: str
    signal_context: str
    feature_name: str
    current_state: str
    requested_state: str
    configuration_version: str
    evidence_quality: float
    rollout_score: float
    control_score: float
    audit_score: float
    status: str
    review_required: bool
    reason: str

    @classmethod
    def from_observation(cls, observation: FeatureFlagObservation, status: str, reason: str) -> "FeatureFlagProfile":
        rollout_score = _rollout_score(observation)
        control_score = _control_score(observation)
        audit_score = _audit_score(observation)
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            feature_name=observation.feature_name,
            current_state=observation.current_state,
            requested_state=observation.requested_state,
            configuration_version=observation.configuration_version,
            evidence_quality=observation.evidence_quality,
            rollout_score=rollout_score,
            control_score=control_score,
            audit_score=audit_score,
            status=status,
            review_required=status != "READY",
            reason=reason,
        )

    @property
    def state_change_required(self) -> bool:
        return self.current_state != self.requested_state


def _rollout_score(observation: FeatureFlagObservation) -> float:
    value = observation.rollout_quality * 0.45 + observation.dependency_quality * 0.30 + observation.production_event_score * 0.25
    return round(min(max(value, 0.0), 1.0), 4)


def _control_score(observation: FeatureFlagObservation) -> float:
    value = observation.rollback_quality * 0.40 + observation.operator_review_quality * 0.35 + observation.observability_score * 0.25
    return round(min(max(value, 0.0), 1.0), 4)


def _audit_score(observation: FeatureFlagObservation) -> float:
    value = observation.audit_quality * 0.50 + observation.production_event_score * 0.25 + observation.observability_score * 0.25
    return round(min(max(value, 0.0), 1.0), 4)
