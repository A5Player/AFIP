"""Production Milestone E Pack 5 dynamic weight profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .weight_observation import DynamicWeightObservation


@dataclass(frozen=True)
class DynamicWeightProfile:
    """Data-derived profile for one regime-first intelligence weight."""

    profile_key: str
    market_regime: str
    intelligence_name: str
    direction: str
    sample_count: int
    average_contribution_score: float
    average_accuracy_rate: float
    average_stability_score: float
    average_recency_score: float
    average_execution_cost_score: float
    average_conflict_score: float
    normalized_weight_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[DynamicWeightObservation, ...]

    @classmethod
    def from_observations(
        cls,
        observations: Tuple[DynamicWeightObservation, ...],
    ) -> "DynamicWeightProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                intelligence_name="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                average_contribution_score=0.0,
                average_accuracy_rate=0.0,
                average_stability_score=0.0,
                average_recency_score=0.0,
                average_execution_cost_score=0.0,
                average_conflict_score=0.0,
                normalized_weight_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        total_samples = sum(item.sample_count for item in observations)
        avg_contribution = round(sum(item.contribution_score for item in observations) / len(observations), 4)
        avg_accuracy = round(sum(item.accuracy_rate for item in observations) / len(observations), 4)
        avg_stability = round(sum(item.stability_score for item in observations) / len(observations), 4)
        avg_recency = round(sum(item.recency_score for item in observations) / len(observations), 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / len(observations), 4)
        avg_conflict = round(sum(item.conflict_score for item in observations) / len(observations), 4)
        normalized_weight = round(
            (avg_contribution * 0.3)
            + (avg_accuracy * 0.25)
            + (avg_stability * 0.15)
            + (avg_recency * 0.15)
            + (avg_cost * 0.1)
            + ((100.0 - avg_conflict) * 0.05),
            4,
        )
        return cls(
            profile_key=first.regime_weight_key,
            market_regime=first.market_regime,
            intelligence_name=first.intelligence_name,
            direction=first.direction,
            sample_count=total_samples,
            average_contribution_score=avg_contribution,
            average_accuracy_rate=avg_accuracy,
            average_stability_score=avg_stability,
            average_recency_score=avg_recency,
            average_execution_cost_score=avg_cost,
            average_conflict_score=avg_conflict,
            normalized_weight_score=normalized_weight,
            trace_ids=tuple(sorted(item.trace_id for item in observations if item.trace_id)),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.intelligence_name != "UNKNOWN"
            and self.sample_count >= 20
            and self.average_contribution_score >= 50.0
            and self.average_accuracy_rate >= 55.0
            and self.average_stability_score >= 50.0
            and self.average_recency_score >= 50.0
            and self.average_execution_cost_score >= 50.0
            and self.average_conflict_score <= 35.0
            and self.normalized_weight_score >= 60.0
            and bool(self.trace_ids)
        )
