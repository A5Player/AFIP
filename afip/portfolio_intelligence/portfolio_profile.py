"""Production Milestone E Pack 7 portfolio intelligence profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .portfolio_observation import PortfolioObservation


@dataclass(frozen=True)
class PortfolioProfile:
    """Data-derived profile for regime-first portfolio intelligence."""

    profile_key: str
    market_regime: str
    portfolio_scope: str
    direction: str
    sample_count: int
    average_exposure_score: float
    average_correlation_score: float
    average_risk_budget_utilization: float
    average_diversification_score: float
    average_portfolio_return_score: float
    average_drawdown_pressure: float
    average_execution_cost_score: float
    portfolio_resilience_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[PortfolioObservation, ...]

    @classmethod
    def from_observations(cls, observations: Tuple[PortfolioObservation, ...]) -> "PortfolioProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                portfolio_scope="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                average_exposure_score=0.0,
                average_correlation_score=0.0,
                average_risk_budget_utilization=0.0,
                average_diversification_score=0.0,
                average_portfolio_return_score=0.0,
                average_drawdown_pressure=0.0,
                average_execution_cost_score=0.0,
                portfolio_resilience_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        count = len(observations)
        samples = sum(item.sample_count for item in observations)
        avg_exposure = round(sum(item.exposure_score for item in observations) / count, 4)
        avg_correlation = round(sum(item.correlation_score for item in observations) / count, 4)
        avg_risk_budget = round(sum(item.risk_budget_utilization for item in observations) / count, 4)
        avg_diversification = round(sum(item.diversification_score for item in observations) / count, 4)
        avg_return = round(sum(item.portfolio_return_score for item in observations) / count, 4)
        avg_drawdown = round(sum(item.drawdown_pressure for item in observations) / count, 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / count, 4)
        controlled_exposure = max(0.0, 100.0 - abs(avg_exposure - 70.0))
        correlation_safety = max(0.0, 100.0 - avg_correlation)
        budget_safety = max(0.0, 100.0 - avg_risk_budget)
        drawdown_safety = max(0.0, 100.0 - avg_drawdown)
        cost_safety = max(0.0, 100.0 - avg_cost)
        resilience = round(
            (controlled_exposure * 0.18)
            + (correlation_safety * 0.18)
            + (budget_safety * 0.18)
            + (avg_diversification * 0.16)
            + (avg_return * 0.14)
            + (drawdown_safety * 0.1)
            + (cost_safety * 0.06),
            4,
        )
        return cls(
            profile_key=first.portfolio_key,
            market_regime=first.market_regime,
            portfolio_scope=first.portfolio_scope,
            direction=first.direction,
            sample_count=samples,
            average_exposure_score=avg_exposure,
            average_correlation_score=avg_correlation,
            average_risk_budget_utilization=avg_risk_budget,
            average_diversification_score=avg_diversification,
            average_portfolio_return_score=avg_return,
            average_drawdown_pressure=avg_drawdown,
            average_execution_cost_score=avg_cost,
            portfolio_resilience_score=resilience,
            trace_ids=tuple(sorted(item.trace_id for item in observations if item.trace_id)),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.portfolio_scope != "UNKNOWN"
            and self.sample_count >= 20
            and 35.0 <= self.average_exposure_score <= 90.0
            and self.average_correlation_score <= 75.0
            and self.average_risk_budget_utilization <= 80.0
            and self.average_diversification_score >= 45.0
            and self.average_portfolio_return_score >= 50.0
            and self.average_drawdown_pressure <= 35.0
            and self.average_execution_cost_score <= 35.0
            and self.portfolio_resilience_score >= 60.0
            and bool(self.trace_ids)
        )
