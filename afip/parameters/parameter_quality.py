"""Production Milestone C Pack 13 adaptive parameter quality assessment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from afip.parameters.parameter_repository import ParameterProfile


@dataclass(frozen=True)
class ParameterQualityResult:
    status: str
    quality_score: float
    approved: bool
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "quality_score": round(self.quality_score, 4),
            "approved": self.approved,
            "reasons": list(self.reasons),
        }


class ParameterQualityAssessment:
    """Approves only sufficiently observed, cost-aware parameter candidates."""

    def __init__(self, minimum_observations: int = 5, maximum_average_cost_points: float = 45.0) -> None:
        self.minimum_observations = int(minimum_observations)
        self.maximum_average_cost_points = float(maximum_average_cost_points)

    def assess(self, profile: ParameterProfile | None) -> ParameterQualityResult:
        if profile is None:
            return ParameterQualityResult("PARAMETER_OBSERVE_ONLY", 0.0, False, ["no_parameter_profile"])

        reasons: list[str] = []
        if profile.observations < self.minimum_observations:
            reasons.append("insufficient_parameter_observations")
        if profile.average_cost_points > self.maximum_average_cost_points:
            reasons.append("execution_cost_above_parameter_threshold")
        if profile.expectancy <= 0.0:
            reasons.append("non_positive_parameter_expectancy")

        observation_score = min(100.0, (profile.observations / max(1, self.minimum_observations)) * 35.0)
        win_score = min(35.0, profile.win_rate * 0.35)
        expectancy_score = min(20.0, max(0.0, profile.expectancy) * 0.7)
        cost_score = max(0.0, 10.0 - max(0.0, profile.average_cost_points - 25.0) * 0.4)
        quality_score = observation_score + win_score + expectancy_score + cost_score
        approved = not reasons and quality_score >= 70.0
        status = "PARAMETER_RESEARCH_READY" if approved else "PARAMETER_OBSERVE_ONLY"
        if not approved and quality_score < 70.0:
            reasons.append("parameter_quality_below_research_threshold")
        return ParameterQualityResult(status, round(quality_score, 4), approved, reasons)
