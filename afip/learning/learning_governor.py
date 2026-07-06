"""Govern learning profile promotion for deterministic production use."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningGovernorResult:
    status: str
    action: str
    score: float
    reasons: tuple[str, ...]
    regime_first_key: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "score": self.score,
            "reasons": list(self.reasons),
            "regime_first_key": self.regime_first_key,
        }


@dataclass(frozen=True)
class LearningGovernor:
    """Allow learning suggestions only when data quality supports them."""

    minimum_observations: int = 4
    minimum_win_rate: float = 55.0
    minimum_expectancy: float = 0.0
    maximum_average_cost_points: float = 45.0

    def evaluate(self, profile: dict[str, object]) -> LearningGovernorResult:
        observations = int(profile.get("observations", 0))
        win_rate = float(profile.get("win_rate", 0.0))
        expectancy = float(profile.get("expectancy", 0.0))
        average_cost = float(profile.get("average_execution_cost_points", 0.0))
        efficiency = float(profile.get("learning_efficiency", 0.0))
        risk_hint = float(profile.get("risk_adjustment_hint", 0.0))
        reasons: list[str] = []

        if observations < self.minimum_observations:
            reasons.append("insufficient_learning_observations")
        if win_rate < self.minimum_win_rate:
            reasons.append("learning_win_rate_below_threshold")
        if expectancy <= self.minimum_expectancy:
            reasons.append("learning_expectancy_not_positive")
        if average_cost > self.maximum_average_cost_points:
            reasons.append("learning_execution_cost_above_threshold")

        score = round(win_rate * 0.35 + max(expectancy, 0.0) * 1.5 + efficiency * 0.25 + max(risk_hint, 0.0) * 2.0 - average_cost * 0.2, 4)
        if reasons:
            return LearningGovernorResult(
                status="LEARNING_OBSERVE_ONLY",
                action="KEEP_CURRENT_PARAMETERS",
                score=score,
                reasons=tuple(reasons),
                regime_first_key=str(profile.get("regime_first_key", "UNKNOWN")),
            )
        return LearningGovernorResult(
            status="LEARNING_UPDATE_READY",
            action="PROPOSE_BOUNDED_PARAMETER_UPDATE",
            score=score,
            reasons=("learning_profile_passed_governance",),
            regime_first_key=str(profile.get("regime_first_key", "UNKNOWN")),
        )
