"""Long-run stability profile for Production Milestone G Pack 7."""

from __future__ import annotations

from dataclasses import dataclass

from .stability_observation import LongRunStabilityObservation


@dataclass(frozen=True)
class LongRunStabilityProfile:
    """Deterministic profile summarizing long-run stability readiness."""

    market_regime: str
    signal_context: str
    runtime_component: str
    execution_mode: str
    configuration_version: str
    paper_trading_score: float
    production_hardening_score: float
    runtime_metrics_score: float
    feature_flag_score: float
    repeated_runs: int
    deterministic_matches: int
    deterministic_consistency: float
    state_integrity_score: float
    resource_trend_score: float
    anomaly_rate: float
    max_drawdown: float
    stability_quality: float
    long_run_score: float
    status: str
    review_required: bool
    reason: str

    @classmethod
    def from_observation(cls, observation: LongRunStabilityObservation, status: str, reason: str) -> "LongRunStabilityProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            runtime_component=observation.runtime_component,
            execution_mode=observation.execution_mode,
            configuration_version=observation.configuration_version,
            paper_trading_score=round(observation.paper_trading_score, 4),
            production_hardening_score=round(observation.production_hardening_score, 4),
            runtime_metrics_score=round(observation.runtime_metrics_score, 4),
            feature_flag_score=round(observation.feature_flag_score, 4),
            repeated_runs=observation.repeated_runs,
            deterministic_matches=observation.deterministic_matches,
            deterministic_consistency=round(observation.deterministic_consistency, 4),
            state_integrity_score=round(observation.state_integrity_score, 4),
            resource_trend_score=round(observation.resource_trend_score, 4),
            anomaly_rate=round(observation.anomaly_rate, 4),
            max_drawdown=round(observation.max_drawdown, 4),
            stability_quality=round(observation.stability_quality, 4),
            long_run_score=round(observation.long_run_score, 4),
            status=status,
            review_required=status != "READY",
            reason=reason,
        )

    @property
    def readiness_gate(self) -> str:
        if self.status == "BLOCKED":
            return "BLOCKED"
        if self.status == "REVIEW":
            return "REVIEW_REQUIRED"
        return "LONG_RUN_STABILITY_READY"
