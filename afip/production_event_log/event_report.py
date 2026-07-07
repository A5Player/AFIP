"""Production event log report for deterministic operational review."""

from __future__ import annotations

from dataclasses import dataclass

from .event_profile import ProductionEventProfile


@dataclass(frozen=True)
class ProductionEventReport:
    """Human-readable financial runtime event report."""

    profile: ProductionEventProfile

    @property
    def market_regime(self) -> str:
        return self.profile.market_regime

    @property
    def signal_context(self) -> str:
        return self.profile.signal_context

    def as_text(self) -> str:
        return "\n".join([
            "Production Event Log Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Event type: {self.profile.event_type}",
            f"Event sequence: {self.profile.event_sequence}",
            f"Config version: {self.profile.config_version}",
            f"Previous config version: {self.profile.previous_config_version}",
            f"Event log score: {self.profile.event_log_score}",
            f"Configuration score: {self.profile.configuration_score}",
            f"Audit score: {self.profile.audit_score}",
            f"Decision reason: {self.profile.reason}",
        ])
