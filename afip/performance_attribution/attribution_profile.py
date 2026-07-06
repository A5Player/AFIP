"""Production Milestone E Pack 6 performance attribution profile model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .attribution_observation import PerformanceAttributionObservation


@dataclass(frozen=True)
class PerformanceAttributionProfile:
    """Data-derived profile for regime-first performance attribution."""

    profile_key: str
    market_regime: str
    attribution_source: str
    direction: str
    sample_count: int
    total_gross_pnl: float
    total_net_pnl: float
    average_contribution_score: float
    average_decision_alignment_rate: float
    average_execution_quality_score: float
    average_drawdown_impact: float
    attribution_efficiency_score: float
    trace_ids: Tuple[str, ...]
    observations: Tuple[PerformanceAttributionObservation, ...]

    @classmethod
    def from_observations(
        cls,
        observations: Tuple[PerformanceAttributionObservation, ...],
    ) -> "PerformanceAttributionProfile":
        if not observations:
            return cls(
                profile_key="UNKNOWN:UNKNOWN:FLAT",
                market_regime="UNKNOWN",
                attribution_source="UNKNOWN",
                direction="FLAT",
                sample_count=0,
                total_gross_pnl=0.0,
                total_net_pnl=0.0,
                average_contribution_score=0.0,
                average_decision_alignment_rate=0.0,
                average_execution_quality_score=0.0,
                average_drawdown_impact=0.0,
                attribution_efficiency_score=0.0,
                trace_ids=(),
                observations=(),
            )
        first = observations[0]
        total_samples = sum(item.sample_count for item in observations)
        total_gross = round(sum(item.gross_pnl for item in observations), 4)
        total_net = round(sum(item.net_pnl for item in observations), 4)
        avg_contribution = round(sum(item.contribution_score for item in observations) / len(observations), 4)
        avg_alignment = round(sum(item.decision_alignment_rate for item in observations) / len(observations), 4)
        avg_quality = round(sum(item.execution_quality_score for item in observations) / len(observations), 4)
        avg_drawdown = round(sum(item.drawdown_impact for item in observations) / len(observations), 4)
        pnl_efficiency = 0.0 if total_gross == 0 else max(min((total_net / abs(total_gross)) * 100.0, 100.0), -100.0)
        attribution_efficiency = round(
            (avg_contribution * 0.25)
            + (avg_alignment * 0.25)
            + (avg_quality * 0.2)
            + (pnl_efficiency * 0.2)
            + ((100.0 - avg_drawdown) * 0.1),
            4,
        )
        return cls(
            profile_key=first.attribution_key,
            market_regime=first.market_regime,
            attribution_source=first.attribution_source,
            direction=first.direction,
            sample_count=total_samples,
            total_gross_pnl=total_gross,
            total_net_pnl=total_net,
            average_contribution_score=avg_contribution,
            average_decision_alignment_rate=avg_alignment,
            average_execution_quality_score=avg_quality,
            average_drawdown_impact=avg_drawdown,
            attribution_efficiency_score=attribution_efficiency,
            trace_ids=tuple(sorted(item.trace_id for item in observations if item.trace_id)),
            observations=observations,
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.market_regime != "UNKNOWN"
            and self.attribution_source != "UNKNOWN"
            and self.sample_count >= 20
            and self.total_net_pnl > 0.0
            and self.average_contribution_score >= 50.0
            and self.average_decision_alignment_rate >= 55.0
            and self.average_execution_quality_score >= 55.0
            and self.average_drawdown_impact <= 35.0
            and self.attribution_efficiency_score >= 60.0
            and bool(self.trace_ids)
        )
