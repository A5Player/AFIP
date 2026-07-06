"""Replay validation controls for historical market research."""

from __future__ import annotations

from dataclasses import dataclass, field

from afip.replay.replay_timeline import ReplayTimeline


@dataclass(frozen=True)
class ReplayValidationResult:
    """Validation result for a replay timeline."""

    status: str
    quality_score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "quality_score": round(float(self.quality_score), 4),
            "reasons": list(self.reasons),
        }


@dataclass
class ReplayValidationEngine:
    """Assess whether a timeline is sufficient for a replay session."""

    minimum_snapshots: int = 3
    maximum_average_spread_points: float = 45.0

    def validate(self, timeline: ReplayTimeline) -> ReplayValidationResult:
        reasons: list[str] = []
        score = 100.0
        if len(timeline) < self.minimum_snapshots:
            reasons.append("insufficient_replay_snapshots")
            score -= 40.0
        if timeline.average_spread() > self.maximum_average_spread_points:
            reasons.append("replay_spread_above_research_limit")
            score -= 25.0
        if not timeline.direction_counts():
            reasons.append("missing_direction_distribution")
            score -= 20.0
        if not timeline.regime_counts():
            reasons.append("missing_market_regime_distribution")
            score -= 20.0
        score = max(0.0, min(100.0, score))
        if score >= 75.0:
            status = "REPLAY_VALIDATION_READY"
        elif score >= 50.0:
            status = "REPLAY_VALIDATION_REVIEW"
        else:
            status = "REPLAY_VALIDATION_BLOCKED"
        return ReplayValidationResult(status=status, quality_score=score, reasons=tuple(reasons or ["replay_validation_pass"]))
