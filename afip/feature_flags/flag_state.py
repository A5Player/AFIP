"""Feature flag state helper for controlled production rollout review."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureFlagState:
    """Immutable feature flag state record used for deterministic rollback checks."""

    feature_name: str
    current_state: str
    requested_state: str
    configuration_version: str
    rollback_available: bool

    @property
    def normalized_feature_name(self) -> str:
        return self.feature_name.strip().upper()

    @property
    def state_changed(self) -> bool:
        return self.current_state.strip().upper() != self.requested_state.strip().upper()

    @property
    def rollout_status(self) -> str:
        if not self.state_changed:
            return "NO_CHANGE_REQUIRED"
        if self.rollback_available:
            return "ROLLOUT_REVIEW_READY"
        return "ROLLOUT_REVIEW_REQUIRED"
