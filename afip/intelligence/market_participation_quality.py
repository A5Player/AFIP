"""Production Milestone A Pack 7: market participation quality.

Additive market participation intelligence for execution participation quality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class MarketParticipationQualityResult:
    """Market participation quality result for production execution decisions."""

    status: str
    participation_score: float
    spread_quality_score: float
    liquidity_access_score: float
    execution_alignment_score: float
    participation_state: str
    production_ready: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "market_participation_quality_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "participation_score": round(self.participation_score, 2),
            "spread_quality_score": round(self.spread_quality_score, 2),
            "liquidity_access_score": round(self.liquidity_access_score, 2),
            "execution_alignment_score": round(self.execution_alignment_score, 2),
            "participation_state": self.participation_state,
            "production_ready": self.production_ready,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class MarketParticipationQuality:
    """Evaluates cost, liquidity, and execution alignment for market participation."""

    def evaluate(self, execution_state: Mapping[str, Any]) -> MarketParticipationQualityResult:
        spread_quality = float(execution_state.get("spread_quality", 75.0))
        slippage_quality = float(execution_state.get("slippage_quality", 75.0))
        liquidity_score = float(execution_state.get("liquidity_score", 75.0))
        fill_probability = float(execution_state.get("fill_probability", 75.0))
        signal_consistency = float(execution_state.get("signal_consistency", 75.0))
        decision_confidence = float(execution_state.get("decision_confidence", 70.0))

        spread_quality_score = _clamp((spread_quality * 0.65) + (slippage_quality * 0.35))
        liquidity_access_score = _clamp((liquidity_score * 0.55) + (fill_probability * 0.45))
        execution_alignment_score = _clamp((signal_consistency * 0.50) + (decision_confidence * 0.50))
        participation_score = (spread_quality_score * 0.30) + (liquidity_access_score * 0.35) + (execution_alignment_score * 0.35)

        blockers: list[str] = []
        if spread_quality_score < 58.0:
            blockers.append("spread_quality_below_production_threshold")
        if liquidity_access_score < 60.0:
            blockers.append("liquidity_access_below_production_threshold")
        if execution_alignment_score < 62.0:
            blockers.append("execution_alignment_below_production_threshold")
        if participation_score < 64.0:
            blockers.append("market_participation_score_low")

        if participation_score >= 82.0 and not blockers:
            participation_state = "EFFICIENT"
        elif participation_score >= 68.0 and not blockers:
            participation_state = "ACCEPTABLE"
        else:
            participation_state = "CONSERVATIVE"

        production_ready = not blockers and participation_score >= 68.0
        return MarketParticipationQualityResult(
            status="READY" if production_ready else "OBSERVE",
            participation_score=participation_score,
            spread_quality_score=spread_quality_score,
            liquidity_access_score=liquidity_access_score,
            execution_alignment_score=execution_alignment_score,
            participation_state=participation_state,
            production_ready=production_ready,
            blockers=blockers,
            reason="market_participation_quality_ready" if production_ready else "market_participation_quality_observation_required",
        )
