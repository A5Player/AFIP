"""Production Milestone A Pack 6: market regime consistency index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class MarketRegimeConsistencyResult:
    """Consistency result for recent market regime observations."""

    status: str
    dominant_regime: str
    consistency_score: float
    transition_count: int
    market_state: str
    production_ready: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "market_regime_consistency_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "dominant_regime": self.dominant_regime,
            "consistency_score": round(self.consistency_score, 2),
            "transition_count": self.transition_count,
            "market_state": self.market_state,
            "production_ready": self.production_ready,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class MarketRegimeConsistencyIndex:
    """Measures whether the market regime is stable enough for production allocation."""

    def evaluate(self, regime_history: Iterable[Mapping[str, Any]]) -> MarketRegimeConsistencyResult:
        regimes = [str(item.get("regime", "UNKNOWN")).upper() for item in regime_history]
        regimes = [item for item in regimes if item and item != "UNKNOWN"]

        if not regimes:
            return MarketRegimeConsistencyResult(
                status="OBSERVE",
                dominant_regime="UNKNOWN",
                consistency_score=0.0,
                transition_count=0,
                market_state="INSUFFICIENT_DATA",
                production_ready=False,
                blockers=["regime_history_missing"],
                reason="market_regime_consistency_missing_history",
            )

        counts = {regime: regimes.count(regime) for regime in set(regimes)}
        dominant_regime = max(counts, key=counts.get)
        dominant_ratio = counts[dominant_regime] / len(regimes)
        transitions = sum(1 for previous, current in zip(regimes, regimes[1:]) if previous != current)
        transition_penalty = min(35.0, transitions * 7.0)
        consistency_score = max(0.0, dominant_ratio * 100.0 - transition_penalty)

        blockers: list[str] = []
        if consistency_score < 58.0:
            blockers.append("regime_consistency_score_low")
        if transitions >= max(3, len(regimes) // 2):
            blockers.append("regime_transition_frequency_high")

        if not blockers and consistency_score >= 75.0:
            market_state = "CONSISTENT"
        elif not blockers:
            market_state = "ACCEPTABLE"
        else:
            market_state = "VARIABLE"

        production_ready = not blockers
        return MarketRegimeConsistencyResult(
            status="READY" if production_ready else "OBSERVE",
            dominant_regime=dominant_regime,
            consistency_score=consistency_score,
            transition_count=transitions,
            market_state=market_state,
            production_ready=production_ready,
            blockers=blockers,
            reason="market_regime_consistency_ready" if production_ready else "market_regime_consistency_observation_required",
        )
