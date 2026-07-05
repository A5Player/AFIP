"""Production Milestone A3: Learning and Optimization.

The optimizer only proposes bounded parameter adjustments. It does not place
orders and does not bypass production safety gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping

from afip.intelligence.adaptive_intelligence_core import clamp


@dataclass(frozen=True)
class LearningSample:
    outcome: str
    entry_score: float
    position_confidence: float
    net_points: float = 0.0
    regime: str = "UNKNOWN"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LearningSample":
        return cls(
            outcome=str(payload.get("outcome", "UNKNOWN")).upper(),
            entry_score=float(payload.get("entry_score", 50.0)),
            position_confidence=float(payload.get("position_confidence", 50.0)),
            net_points=float(payload.get("net_points", 0.0)),
            regime=str(payload.get("regime", "UNKNOWN")),
        )


@dataclass(frozen=True)
class OptimizationResult:
    status: str
    sample_count: int
    entry_threshold: float
    position_threshold: float
    risk_adjustment: float
    reason: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "sample_count": self.sample_count,
            "entry_threshold": round(self.entry_threshold, 2),
            "position_threshold": round(self.position_threshold, 2),
            "risk_adjustment": round(self.risk_adjustment, 2),
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


class AdaptiveLearningOptimizer:
    """Bounded optimization for entry, position and risk parameters."""

    def optimize(self, samples: Iterable[LearningSample | Mapping[str, Any]], base: Mapping[str, Any] | None = None) -> OptimizationResult:
        normalized = [s if isinstance(s, LearningSample) else LearningSample.from_mapping(s) for s in samples]
        base = dict(base or {})
        entry_threshold = clamp(float(base.get("entry_threshold", 70.0)), 55.0, 90.0)
        position_threshold = clamp(float(base.get("position_threshold", 62.0)), 50.0, 85.0)

        if len(normalized) < 5:
            return OptimizationResult("LEARNING", len(normalized), entry_threshold, position_threshold, 0.0, "insufficient_learning_samples", {"minimum_samples": 5})

        wins = [s for s in normalized if s.outcome in {"WIN", "PROFIT"}]
        losses = [s for s in normalized if s.outcome in {"LOSS", "DRAWDOWN"}]
        win_rate = len(wins) / len(normalized) if normalized else 0.0
        average_points = sum(s.net_points for s in normalized) / len(normalized)

        if win_rate >= 0.62 and average_points > 0:
            entry_threshold -= 2.0
            position_threshold -= 1.0
            risk_adjustment = 4.0
            reason = "learning_supports_selective_optimization"
        elif win_rate <= 0.45 or average_points < 0:
            entry_threshold += 4.0
            position_threshold += 3.0
            risk_adjustment = -8.0
            reason = "learning_requires_more_conservative_parameters"
        else:
            risk_adjustment = 0.0
            reason = "learning_parameters_stable"

        return OptimizationResult(
            "READY",
            len(normalized),
            clamp(entry_threshold, 55.0, 90.0),
            clamp(position_threshold, 50.0, 85.0),
            clamp(risk_adjustment, -20.0, 10.0),
            reason,
            {"win_rate": round(win_rate * 100.0, 2), "average_points": round(average_points, 2), "wins": len(wins), "losses": len(losses)},
        )
