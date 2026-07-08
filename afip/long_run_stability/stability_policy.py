"""Long-run stability policy for deterministic production stability review."""

from __future__ import annotations

from dataclasses import dataclass

from .stability_observation import LongRunStabilityObservation


@dataclass(frozen=True)
class LongRunStabilityPolicy:
    """Deterministic gate for simulated long-run stability evidence."""

    minimum_paper_trading_score: float = 0.72
    minimum_hardening_score: float = 0.72
    minimum_runtime_metrics_score: float = 0.70
    minimum_feature_flag_score: float = 0.68
    minimum_repeated_runs: int = 6
    minimum_deterministic_consistency: float = 0.90
    minimum_state_integrity_score: float = 0.84
    minimum_resource_trend_score: float = 0.70
    maximum_anomaly_rate: float = 0.12
    maximum_drawdown: float = 0.30
    minimum_stability_quality: float = 0.76
    minimum_long_run_score: float = 0.76

    def evaluate_reason(self, observation: LongRunStabilityObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_long_run_stability"
        if not observation.has_repeated_run_sample:
            return "repeated_run_sample_required"
        if observation.paper_trading_score < self.minimum_paper_trading_score:
            return "paper_trading_review_required"
        if observation.production_hardening_score < self.minimum_hardening_score:
            return "production_hardening_review_required"
        if observation.runtime_metrics_score < self.minimum_runtime_metrics_score:
            return "runtime_metrics_review_required"
        if observation.feature_flag_score < self.minimum_feature_flag_score:
            return "feature_flag_review_required"
        if observation.repeated_runs < self.minimum_repeated_runs:
            return "long_run_sample_review_required"
        if observation.deterministic_consistency < self.minimum_deterministic_consistency:
            return "deterministic_consistency_review_required"
        if observation.state_integrity_score < self.minimum_state_integrity_score:
            return "state_integrity_review_required"
        if observation.resource_trend_score < self.minimum_resource_trend_score:
            return "resource_trend_review_required"
        if observation.anomaly_rate > self.maximum_anomaly_rate:
            return "runtime_anomaly_review_required"
        if observation.max_drawdown > self.maximum_drawdown:
            return "long_run_drawdown_review_required"
        if observation.stability_quality < self.minimum_stability_quality:
            return "stability_quality_review_required"
        if observation.long_run_score < self.minimum_long_run_score:
            return "long_run_score_review_required"
        return "long_run_stability_ready"

    def status_for(self, observation: LongRunStabilityObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_long_run_stability", "repeated_run_sample_required"}:
            return "BLOCKED"
        if reason == "long_run_stability_ready":
            return "READY"
        return "REVIEW"
