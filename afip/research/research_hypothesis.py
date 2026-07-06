"""Research hypothesis evaluation for market-regime-first data."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchHypothesisResult:
    name: str
    status: str
    score: float
    observations: int
    reasons: tuple[str, ...]
    regime_first_key: str

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "score": self.score,
            "observations": self.observations,
            "reasons": list(self.reasons),
            "regime_first_key": self.regime_first_key,
        }


@dataclass(frozen=True)
class ResearchHypothesis:
    """Rules for promoting a grouped research profile to review-ready state."""

    name: str = "REGIME_FIRST_SIGNAL_EDGE"
    minimum_observations: int = 4
    minimum_win_rate: float = 55.0
    minimum_expectancy: float = 0.0
    maximum_average_cost_points: float = 45.0

    def evaluate(self, group: dict[str, object]) -> ResearchHypothesisResult:
        observations = int(group.get("observations", 0))
        win_rate = float(group.get("win_rate", 0.0))
        expectancy = float(group.get("expectancy", 0.0))
        average_cost = float(group.get("average_execution_cost_points", 0.0))
        profit_factor = float(group.get("profit_factor", 0.0))
        reasons: list[str] = []

        if observations < self.minimum_observations:
            reasons.append("insufficient_research_observations")
        if win_rate < self.minimum_win_rate:
            reasons.append("win_rate_below_research_threshold")
        if expectancy <= self.minimum_expectancy:
            reasons.append("expectancy_not_positive")
        if average_cost > self.maximum_average_cost_points:
            reasons.append("execution_cost_above_research_threshold")

        score = round((win_rate * 0.4) + (max(expectancy, 0.0) * 2.0) + (profit_factor * 5.0) - average_cost, 4)
        status = "RESEARCH_REVIEW_READY" if not reasons else "RESEARCH_OBSERVE_ONLY"
        return ResearchHypothesisResult(
            name=self.name,
            status=status,
            score=score,
            observations=observations,
            reasons=tuple(reasons),
            regime_first_key=str(group.get("regime_first_key", "UNKNOWN")),
        )
