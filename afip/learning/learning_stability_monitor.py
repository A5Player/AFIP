"""Production Milestone A Pack 3: learning stability monitor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping

from afip.intelligence.adaptive_intelligence_core import clamp


@dataclass(frozen=True)
class LearningStabilityReport:
    """Stability report for recent adaptive learning observations."""

    status: str
    sample_count: int
    stability_score: float
    drift_score: float
    recommendation: str
    blockers: list[str] = field(default_factory=list)
    reason: str = "learning_stability_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "sample_count": self.sample_count,
            "stability_score": round(self.stability_score, 2),
            "drift_score": round(self.drift_score, 2),
            "recommendation": self.recommendation,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class LearningStabilityMonitor:
    """Detects whether recent outcomes are stable enough for production use."""

    def __init__(self, minimum_samples: int = 6) -> None:
        self.minimum_samples = max(1, int(minimum_samples))

    def evaluate(self, samples: Iterable[Mapping[str, Any]]) -> LearningStabilityReport:
        records = list(samples)
        if len(records) < self.minimum_samples:
            return LearningStabilityReport(
                status="LEARNING",
                sample_count=len(records),
                stability_score=0.0,
                drift_score=100.0,
                recommendation="KEEP_BASE_THRESHOLDS",
                blockers=["insufficient_learning_stability_samples"],
                reason="learning_stability_waiting_for_samples",
            )

        returns = [float(item.get("net_points", 0.0) or 0.0) for item in records]
        midpoint = len(returns) // 2
        first = returns[:midpoint]
        second = returns[midpoint:]
        first_avg = sum(first) / len(first) if first else 0.0
        second_avg = sum(second) / len(second) if second else 0.0
        average_abs = sum(abs(v) for v in returns) / len(returns) or 1.0
        drift_score = clamp(abs(second_avg - first_avg) / average_abs * 100.0)
        positive_ratio = sum(1 for value in returns if value > 0) / len(returns) * 100.0
        stability_score = clamp(positive_ratio * 0.65 + (100.0 - drift_score) * 0.35)

        blockers: list[str] = []
        if stability_score < 45.0:
            blockers.append("learning_stability_below_production_preference")
        if drift_score > 65.0:
            blockers.append("learning_drift_above_production_preference")

        status = "READY" if not blockers else "CAUTION"
        recommendation = "ALLOW_ADAPTIVE_ADJUSTMENT" if status == "READY" else "KEEP_BASE_THRESHOLDS"
        return LearningStabilityReport(
            status=status,
            sample_count=len(records),
            stability_score=stability_score,
            drift_score=drift_score,
            recommendation=recommendation,
            blockers=blockers,
            reason="learning_stability_ready" if status == "READY" else "learning_stability_protective",
        )
