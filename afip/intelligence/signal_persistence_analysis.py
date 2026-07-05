"""Production Milestone A Pack 10: signal persistence analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class SignalPersistenceAnalysisResult:
    """Signal persistence result for production decision continuity."""

    status: str
    production_ready: bool
    persistence_score: float
    persistence_state: str
    side_persistence: float
    strength_persistence: float
    timeframe_confirmation: float
    volatility_adjustment: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "signal_persistence_analysis_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_ready": self.production_ready,
            "persistence_score": round(self.persistence_score, 2),
            "persistence_state": self.persistence_state,
            "side_persistence": round(self.side_persistence, 2),
            "strength_persistence": round(self.strength_persistence, 2),
            "timeframe_confirmation": round(self.timeframe_confirmation, 2),
            "volatility_adjustment": round(self.volatility_adjustment, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class SignalPersistenceAnalysis:
    """Evaluate whether a signal persists across recent market observations."""

    def evaluate(self, signal_state: Mapping[str, Any]) -> SignalPersistenceAnalysisResult:
        observations = list(signal_state.get("observations", []))
        current_side = str(signal_state.get("side", signal_state.get("action", "BUY"))).upper()

        side_persistence = _side_persistence(observations, current_side)
        strength_persistence = _strength_persistence(observations)
        timeframe_confirmation = _bounded(signal_state.get("timeframe_confirmation", signal_state.get("multi_timeframe_confirmation", 50.0)))
        volatility_penalty = _bounded(signal_state.get("volatility_penalty", 0.0))
        volatility_adjustment = max(0.0, 100.0 - volatility_penalty)

        persistence_score = (
            side_persistence * 0.35
            + strength_persistence * 0.25
            + timeframe_confirmation * 0.25
            + volatility_adjustment * 0.15
        )

        blockers: list[str] = []
        if side_persistence < 60.0:
            blockers.append("side_persistence_below_signal_threshold")
        if strength_persistence < 55.0:
            blockers.append("strength_persistence_below_signal_threshold")
        if timeframe_confirmation < 55.0:
            blockers.append("timeframe_confirmation_below_signal_threshold")
        if volatility_adjustment < 50.0:
            blockers.append("volatility_adjustment_below_signal_threshold")

        production_ready = persistence_score >= 62.0 and not blockers
        if persistence_score >= 84.0:
            persistence_state = "HIGH_PERSISTENCE"
        elif persistence_score >= 62.0:
            persistence_state = "STANDARD_PERSISTENCE"
        else:
            persistence_state = "LOW_PERSISTENCE"

        return SignalPersistenceAnalysisResult(
            status="READY" if production_ready else "OBSERVE",
            production_ready=production_ready,
            persistence_score=persistence_score,
            persistence_state=persistence_state,
            side_persistence=side_persistence,
            strength_persistence=strength_persistence,
            timeframe_confirmation=timeframe_confirmation,
            volatility_adjustment=volatility_adjustment,
            blockers=blockers,
            reason="signal_persistence_ready" if production_ready else "signal_persistence_observation_required",
        )


def _side_persistence(observations: Iterable[Mapping[str, Any]], current_side: str) -> float:
    rows = list(observations)
    if not rows:
        return 50.0
    matching = 0
    total = 0
    for row in rows:
        side = str(row.get("side", row.get("direction", ""))).upper()
        if side not in {"BUY", "SELL", "HOLD", "FLAT"}:
            continue
        total += 1
        if side == current_side:
            matching += 1
    if total == 0:
        return 50.0
    return (matching / total) * 100.0


def _strength_persistence(observations: Iterable[Mapping[str, Any]]) -> float:
    strengths = [_bounded(row.get("strength", row.get("confidence", 50.0))) for row in observations]
    if not strengths:
        return 50.0
    average_strength = sum(strengths) / len(strengths)
    last_strength = strengths[-1]
    continuity = max(0.0, 100.0 - abs(last_strength - average_strength) * 2.0)
    return average_strength * 0.65 + continuity * 0.35


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 50.0
    return max(0.0, min(100.0, numeric))
