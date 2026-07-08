"""Production hardening report for Production Milestone G Pack 5."""

from __future__ import annotations

from dataclasses import dataclass

from .hardening_profile import ProductionHardeningProfile


@dataclass(frozen=True)
class ProductionHardeningReport:
    """Human-readable deterministic production hardening report."""

    profile: ProductionHardeningProfile

    def as_text(self) -> str:
        return "\n".join([
            "Production Hardening Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Runtime component: {self.profile.runtime_component}",
            f"Configuration version: {self.profile.configuration_version}",
            f"Feature flag state: {self.profile.feature_flag_state}",
            f"Integration quality: {self.profile.integration_quality:.4f}",
            f"Hardening score: {self.profile.hardening_score:.4f}",
            f"Readiness gate: {self.profile.readiness_gate}",
            f"Decision reason: {self.profile.reason}",
        ])
