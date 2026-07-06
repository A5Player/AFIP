"""Production Milestone E Pack 2 volatility profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .volatility_observation import VolatilityObservation


@dataclass(frozen=True)
class VolatilityProfile:
    """Data-derived profile for one market-regime and volatility state."""

    profile_key: str
    market_regime: str
    volatility_state: str
    direction: str
    sample_count: int
    average_atr_points: float
    average_realized_volatility: float
    average_expected_volatility: float
    average_expansion_score: float
    average_compression_score: float
    average_execution_cost_score: float
    favorable_outcome_rate: float
    volatility_edge_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[VolatilityObservation, ...]

    @classmethod
    def from_observations(cls, observations: Tuple[VolatilityObservation, ...]) -> "VolatilityProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                volatility_state="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                average_atr_points=0.0,
                average_realized_volatility=0.0,
                average_expected_volatility=0.0,
                average_expansion_score=0.0,
                average_compression_score=0.0,
                average_execution_cost_score=0.0,
                favorable_outcome_rate=0.0,
                volatility_edge_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        total_samples = sum(item.sample_count for item in observations)
        avg_atr = round(sum(item.atr_points for item in observations) / len(observations), 4)
        avg_realized = round(sum(item.realized_volatility for item in observations) / len(observations), 4)
        avg_expected = round(sum(item.expected_volatility for item in observations) / len(observations), 4)
        avg_expansion = round(sum(item.expansion_score for item in observations) / len(observations), 4)
        avg_compression = round(sum(item.compression_score for item in observations) / len(observations), 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / len(observations), 4)
        outcome_rate = round(sum(item.favorable_outcome_rate for item in observations) / len(observations), 4)
        directional_pressure = max(avg_expansion, avg_compression)
        volatility_edge = round(
            (avg_realized * 0.2)
            + (avg_expected * 0.15)
            + (directional_pressure * 0.25)
            + (avg_cost * 0.15)
            + (outcome_rate * 0.25),
            4,
        )
        return cls(
            profile_key=first.regime_volatility_key,
            market_regime=first.market_regime,
            volatility_state=first.volatility_state,
            direction=first.direction,
            sample_count=total_samples,
            average_atr_points=avg_atr,
            average_realized_volatility=avg_realized,
            average_expected_volatility=avg_expected,
            average_expansion_score=avg_expansion,
            average_compression_score=avg_compression,
            average_execution_cost_score=avg_cost,
            favorable_outcome_rate=outcome_rate,
            volatility_edge_score=volatility_edge,
            trace_ids=tuple(item.trace_id for item in observations if item.trace_id),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.volatility_state != "UNKNOWN"
            and self.sample_count >= 20
            and self.average_atr_points > 0
            and self.average_realized_volatility >= 45.0
            and self.average_expected_volatility >= 45.0
            and max(self.average_expansion_score, self.average_compression_score) >= 55.0
            and self.average_execution_cost_score >= 50.0
            and self.favorable_outcome_rate >= 55.0
            and self.volatility_edge_score >= 60.0
            and bool(self.trace_ids)
        )
