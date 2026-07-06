"""Production Milestone E Pack 1 session profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .session_observation import SessionObservation


@dataclass(frozen=True)
class SessionProfile:
    """Data-derived profile for one market-regime and session combination."""

    profile_key: str
    market_regime: str
    session_key: str
    overlap_key: str
    direction: str
    sample_count: int
    average_range_points: float
    average_volatility: float
    average_liquidity_score: float
    average_execution_cost_score: float
    favorable_outcome_rate: float
    session_strength_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[SessionObservation, ...]

    @classmethod
    def from_observations(cls, observations: Tuple[SessionObservation, ...]) -> "SessionProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:NONE:FLAT",
                market_regime="UNKNOWN",
                session_key="UNKNOWN",
                overlap_key="NONE",
                direction="FLAT",
                sample_count=0,
                average_range_points=0.0,
                average_volatility=0.0,
                average_liquidity_score=0.0,
                average_execution_cost_score=0.0,
                favorable_outcome_rate=0.0,
                session_strength_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        total_samples = sum(item.sample_count for item in observations)
        avg_range = round(sum(item.average_range_points for item in observations) / len(observations), 4)
        avg_volatility = round(sum(item.realized_volatility for item in observations) / len(observations), 4)
        avg_liquidity = round(sum(item.liquidity_score for item in observations) / len(observations), 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / len(observations), 4)
        outcome_rate = round(sum(item.favorable_outcome_rate for item in observations) / len(observations), 4)
        session_strength = round(
            (avg_range * 0.2)
            + (avg_volatility * 0.15)
            + (avg_liquidity * 0.25)
            + (avg_cost * 0.15)
            + (outcome_rate * 0.25),
            4,
        )
        return cls(
            profile_key=first.regime_session_key,
            market_regime=first.market_regime,
            session_key=first.session_key,
            overlap_key=first.overlap_key,
            direction=first.direction,
            sample_count=total_samples,
            average_range_points=avg_range,
            average_volatility=avg_volatility,
            average_liquidity_score=avg_liquidity,
            average_execution_cost_score=avg_cost,
            favorable_outcome_rate=outcome_rate,
            session_strength_score=session_strength,
            trace_ids=tuple(item.trace_id for item in observations if item.trace_id),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.session_key != "UNKNOWN"
            and self.sample_count >= 20
            and self.average_liquidity_score >= 55.0
            and self.average_execution_cost_score >= 50.0
            and self.favorable_outcome_rate >= 55.0
            and self.session_strength_score >= 60.0
            and bool(self.trace_ids)
        )
