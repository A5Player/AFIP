"""Deterministic regime-first learning profile aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping, Any

from .learning_observation import LearningObservation


@dataclass(frozen=True)
class LearningProfileResult:
    """Aggregated learning profile for one regime-first group."""

    regime_first_key: str
    observations: int
    win_rate: float
    expectancy: float
    average_confidence: float
    average_execution_cost_points: float
    learning_efficiency: float
    risk_adjustment_hint: float
    status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "regime_first_key": self.regime_first_key,
            "observations": self.observations,
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            "average_confidence": self.average_confidence,
            "average_execution_cost_points": self.average_execution_cost_points,
            "learning_efficiency": self.learning_efficiency,
            "risk_adjustment_hint": self.risk_adjustment_hint,
            "status": self.status,
        }


@dataclass
class LearningProfileRepository:
    """In-memory learning repository grouped by market regime before signal."""

    observations: list[LearningObservation]

    def __init__(self, observations: Iterable[LearningObservation | Mapping[str, Any]] | None = None) -> None:
        self.observations = []
        if observations:
            self.extend(observations)

    def add(self, observation: LearningObservation | Mapping[str, Any]) -> None:
        item = observation if isinstance(observation, LearningObservation) else LearningObservation.from_mapping(observation)
        self.observations.append(item)
        self.observations.sort(key=lambda value: (value.regime_first_key, value.observed_at.isoformat()))

    def extend(self, observations: Iterable[LearningObservation | Mapping[str, Any]]) -> None:
        for observation in observations:
            self.add(observation)

    def grouped(self) -> dict[str, list[LearningObservation]]:
        groups: dict[str, list[LearningObservation]] = {}
        for observation in self.observations:
            groups.setdefault(observation.regime_first_key, []).append(observation)
        return dict(sorted(groups.items()))

    def profiles(self) -> list[LearningProfileResult]:
        results: list[LearningProfileResult] = []
        for key, group in self.grouped().items():
            wins = sum(1 for item in group if item.net_learning_amount > 0)
            win_rate = wins / len(group) * 100.0
            expectancy = mean(item.net_learning_amount for item in group)
            average_cost = mean(item.execution_cost_points for item in group)
            average_confidence = mean(item.confidence for item in group)
            gross_result = sum(abs(item.result_amount) for item in group) or 1.0
            learning_efficiency = max(0.0, min(100.0, (sum(item.net_learning_amount for item in group) / gross_result) * 100.0))
            risk_adjustment_hint = max(-10.0, min(8.0, (win_rate - 50.0) / 5.0 + expectancy / 20.0 - average_cost / 50.0))
            status = "LEARNING_PROFILE_POSITIVE" if expectancy > 0 and win_rate >= 55.0 else "LEARNING_PROFILE_REVIEW"
            results.append(
                LearningProfileResult(
                    regime_first_key=key,
                    observations=len(group),
                    win_rate=round(win_rate, 4),
                    expectancy=round(expectancy, 4),
                    average_confidence=round(average_confidence, 4),
                    average_execution_cost_points=round(average_cost, 4),
                    learning_efficiency=round(learning_efficiency, 4),
                    risk_adjustment_hint=round(risk_adjustment_hint, 4),
                    status=status,
                )
            )
        return results

    def as_dict(self) -> dict[str, object]:
        return {
            "observation_count": len(self.observations),
            "profile_count": len(self.grouped()),
            "profiles": [profile.as_dict() for profile in self.profiles()],
        }
