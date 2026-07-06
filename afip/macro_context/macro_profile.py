"""Production Milestone E Pack 8 macro context profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .macro_observation import MacroObservation


@dataclass(frozen=True)
class MacroProfile:
    """Data-derived profile for regime-first macro context intelligence."""

    profile_key: str
    market_regime: str
    macro_theme: str
    direction: str
    sample_count: int
    average_dxy_alignment_score: float
    average_yield_alignment_score: float
    average_inflation_surprise_score: float
    average_labor_market_pressure: float
    average_policy_rate_bias_score: float
    average_news_risk_score: float
    average_macro_consensus_score: float
    average_execution_cost_score: float
    macro_context_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[MacroObservation, ...]

    @classmethod
    def from_observations(cls, observations: Tuple[MacroObservation, ...]) -> "MacroProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                macro_theme="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                average_dxy_alignment_score=0.0,
                average_yield_alignment_score=0.0,
                average_inflation_surprise_score=0.0,
                average_labor_market_pressure=0.0,
                average_policy_rate_bias_score=0.0,
                average_news_risk_score=0.0,
                average_macro_consensus_score=0.0,
                average_execution_cost_score=0.0,
                macro_context_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        count = len(observations)
        samples = sum(item.sample_count for item in observations)
        avg_dxy = round(sum(item.dxy_alignment_score for item in observations) / count, 4)
        avg_yield = round(sum(item.yield_alignment_score for item in observations) / count, 4)
        avg_inflation = round(sum(item.inflation_surprise_score for item in observations) / count, 4)
        avg_labor = round(sum(item.labor_market_pressure for item in observations) / count, 4)
        avg_policy = round(sum(item.policy_rate_bias_score for item in observations) / count, 4)
        avg_news = round(sum(item.news_risk_score for item in observations) / count, 4)
        avg_consensus = round(sum(item.macro_consensus_score for item in observations) / count, 4)
        avg_cost = round(sum(item.execution_cost_score for item in observations) / count, 4)
        news_safety = max(0.0, 100.0 - avg_news)
        cost_safety = max(0.0, 100.0 - avg_cost)
        labor_stability = max(0.0, 100.0 - avg_labor)
        score = round(
            (avg_dxy * 0.16)
            + (avg_yield * 0.16)
            + (avg_inflation * 0.12)
            + (labor_stability * 0.12)
            + (avg_policy * 0.14)
            + (news_safety * 0.12)
            + (avg_consensus * 0.14)
            + (cost_safety * 0.04),
            4,
        )
        return cls(
            profile_key=first.macro_key,
            market_regime=first.market_regime,
            macro_theme=first.macro_theme,
            direction=first.direction,
            sample_count=samples,
            average_dxy_alignment_score=avg_dxy,
            average_yield_alignment_score=avg_yield,
            average_inflation_surprise_score=avg_inflation,
            average_labor_market_pressure=avg_labor,
            average_policy_rate_bias_score=avg_policy,
            average_news_risk_score=avg_news,
            average_macro_consensus_score=avg_consensus,
            average_execution_cost_score=avg_cost,
            macro_context_score=score,
            trace_ids=tuple(sorted(item.trace_id for item in observations if item.trace_id)),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.macro_theme != "UNKNOWN"
            and self.sample_count >= 20
            and self.average_dxy_alignment_score >= 50.0
            and self.average_yield_alignment_score >= 50.0
            and self.average_policy_rate_bias_score >= 50.0
            and self.average_macro_consensus_score >= 55.0
            and self.average_news_risk_score <= 45.0
            and self.average_execution_cost_score <= 35.0
            and self.macro_context_score >= 60.0
            and bool(self.trace_ids)
        )
