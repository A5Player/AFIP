"""Feature flag report for deterministic production control review."""

from __future__ import annotations

from dataclasses import dataclass

from .flag_profile import FeatureFlagProfile


@dataclass(frozen=True)
class FeatureFlagReport:
    """Human-readable feature flag readiness report."""

    profile: FeatureFlagProfile

    @property
    def market_regime(self) -> str:
        return self.profile.market_regime

    @property
    def signal_context(self) -> str:
        return self.profile.signal_context

    def as_text(self) -> str:
        return "\n".join([
            "Feature Flag Framework Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Feature name: {self.profile.feature_name}",
            f"Current state: {self.profile.current_state}",
            f"Requested state: {self.profile.requested_state}",
            f"Configuration version: {self.profile.configuration_version}",
            f"Rollout score: {self.profile.rollout_score}",
            f"Control score: {self.profile.control_score}",
            f"Audit score: {self.profile.audit_score}",
            f"Decision reason: {self.profile.reason}",
        ])
