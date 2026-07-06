"""Production Milestone E Pack 3 market memory profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .memory_observation import MarketMemoryObservation


@dataclass(frozen=True)
class MarketMemoryProfile:
    """Data-derived profile for one market-regime historical memory pattern."""

    profile_key: str
    market_regime: str
    memory_pattern: str
    direction: str
    sample_count: int
    average_similarity_score: float
    average_recurrence_score: float
    average_outcome_consistency: float
    average_context_age_score: float
    average_execution_cost_score: float
    favorable_outcome_rate: float
    memory_edge_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[MarketMemoryObservation, ...]

    @classmethod
    def from_observations(cls, observations: Tuple[MarketMemoryObservation, ...]) -> "MarketMemoryProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                memory_pattern="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                average_similarity_score=0.0,
                average_recurrence_score=0.0,
                average_outcome_consistency=0.0,
                average_context_age_score=0.0,
                average_execution_cost_score=0.0,
                favorable_outcome_rate=0.0,
                memory_edge_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        total_samples = sum(item.sample_count for item in observations)
        avg_similarity = round(sum(item.similarity_score for item in observations) / len(observations), 4)
        avg_recurrence = round(sum(item.recurrence_score for item in observations) / len(observations), 4)
        avg_consistency = round(sum(item.outcome_consistency for item in observations) / len(observations), 4)
        avg_age = round(sum(item.context_age_score for item in observations) / len(observations), 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / len(observations), 4)
        outcome_rate = round(sum(item.favorable_outcome_rate for item in observations) / len(observations), 4)
        memory_edge = round(
            (avg_similarity * 0.25)
            + (avg_recurrence * 0.15)
            + (avg_consistency * 0.2)
            + (avg_age * 0.1)
            + (avg_cost * 0.1)
            + (outcome_rate * 0.2),
            4,
        )
        return cls(
            profile_key=first.regime_memory_key,
            market_regime=first.market_regime,
            memory_pattern=first.memory_pattern,
            direction=first.direction,
            sample_count=total_samples,
            average_similarity_score=avg_similarity,
            average_recurrence_score=avg_recurrence,
            average_outcome_consistency=avg_consistency,
            average_context_age_score=avg_age,
            average_execution_cost_score=avg_cost,
            favorable_outcome_rate=outcome_rate,
            memory_edge_score=memory_edge,
            trace_ids=tuple(sorted(item.trace_id for item in observations if item.trace_id)),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.memory_pattern != "UNKNOWN"
            and self.sample_count >= 20
            and self.average_similarity_score >= 60.0
            and self.average_recurrence_score >= 50.0
            and self.average_outcome_consistency >= 55.0
            and self.average_context_age_score >= 40.0
            and self.average_execution_cost_score >= 50.0
            and self.favorable_outcome_rate >= 55.0
            and self.memory_edge_score >= 60.0
            and bool(self.trace_ids)
        )
