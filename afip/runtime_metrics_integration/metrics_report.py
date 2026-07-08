"""Runtime metrics report for deterministic performance review."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics_profile import RuntimeMetricsProfile


@dataclass(frozen=True)
class RuntimeMetricsReport:
    """Human-readable runtime metrics report for production review."""

    profile: RuntimeMetricsProfile

    @property
    def market_regime(self) -> str:
        return self.profile.market_regime

    @property
    def signal_context(self) -> str:
        return self.profile.signal_context

    def as_text(self) -> str:
        return "\n".join([
            "Runtime Metrics Integration Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Runtime component: {self.profile.runtime_component}",
            f"Feature flag state: {self.profile.feature_flag_state}",
            f"Configuration version: {self.profile.configuration_version}",
            f"Decision latency ms: {self.profile.decision_latency_ms}",
            f"Engine latency ms: {self.profile.engine_latency_ms}",
            f"Memory usage ratio: {self.profile.memory_usage_ratio}",
            f"Cache hit ratio: {self.profile.cache_hit_ratio}",
            f"Latency score: {self.profile.latency_score}",
            f"Resource score: {self.profile.resource_score}",
            f"Bottleneck: {self.profile.bottleneck}",
            f"Decision reason: {self.profile.reason}",
        ])
