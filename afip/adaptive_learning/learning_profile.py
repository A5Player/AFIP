"""Production Milestone E Pack 9 adaptive learning profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .learning_observation import AdaptiveLearningObservation


@dataclass(frozen=True)
class AdaptiveLearningProfile:
    """Data-derived profile for regime-first adaptive learning intelligence."""

    profile_key: str
    market_regime: str
    learning_context: str
    direction: str
    sample_count: int
    average_reinforcement_score: float
    average_adaptation_score: float
    average_forgetting_score: float
    average_validation_score: float
    average_stability_score: float
    average_drift_risk_score: float
    average_execution_cost_score: float
    adaptive_learning_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[AdaptiveLearningObservation, ...]

    @classmethod
    def from_observations(cls, observations: Tuple[AdaptiveLearningObservation, ...]) -> "AdaptiveLearningProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                learning_context="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                average_reinforcement_score=0.0,
                average_adaptation_score=0.0,
                average_forgetting_score=0.0,
                average_validation_score=0.0,
                average_stability_score=0.0,
                average_drift_risk_score=0.0,
                average_execution_cost_score=0.0,
                adaptive_learning_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        count = len(observations)
        samples = sum(item.sample_count for item in observations)
        avg_reinforcement = round(sum(item.reinforcement_score for item in observations) / count, 4)
        avg_adaptation = round(sum(item.adaptation_score for item in observations) / count, 4)
        avg_forgetting = round(sum(item.forgetting_score for item in observations) / count, 4)
        avg_validation = round(sum(item.validation_score for item in observations) / count, 4)
        avg_stability = round(sum(item.stability_score for item in observations) / count, 4)
        avg_drift = round(sum(item.drift_risk_score for item in observations) / count, 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / count, 4)
        forgetting_quality = max(0.0, 100.0 - avg_forgetting)
        drift_safety = max(0.0, 100.0 - avg_drift)
        cost_safety = max(0.0, 100.0 - avg_cost)
        score = round(
            (avg_reinforcement * 0.18)
            + (avg_adaptation * 0.18)
            + (avg_validation * 0.16)
            + (avg_stability * 0.16)
            + (drift_safety * 0.14)
            + (forgetting_quality * 0.10)
            + (cost_safety * 0.08),
            4,
        )
        return cls(
            profile_key=first.learning_key,
            market_regime=first.market_regime,
            learning_context=first.learning_context,
            direction=first.direction,
            sample_count=samples,
            average_reinforcement_score=avg_reinforcement,
            average_adaptation_score=avg_adaptation,
            average_forgetting_score=avg_forgetting,
            average_validation_score=avg_validation,
            average_stability_score=avg_stability,
            average_drift_risk_score=avg_drift,
            average_execution_cost_score=avg_cost,
            adaptive_learning_score=score,
            trace_ids=tuple(sorted(item.trace_id for item in observations if item.trace_id)),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.learning_context != "UNKNOWN"
            and self.sample_count >= 20
            and self.average_reinforcement_score >= 55.0
            and self.average_adaptation_score >= 55.0
            and self.average_validation_score >= 55.0
            and self.average_stability_score >= 55.0
            and self.average_drift_risk_score <= 45.0
            and self.average_execution_cost_score <= 35.0
            and self.adaptive_learning_score >= 60.0
            and bool(self.trace_ids)
        )
