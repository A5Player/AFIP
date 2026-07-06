"""Production Milestone C Pack 13 adaptive parameter repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from afip.parameters.parameter_observation import ParameterObservation


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * max(0.0, min(1.0, ratio))))
    return ordered[index]


@dataclass
class ParameterProfile:
    """Aggregated adaptive parameter profile for one market grouping."""

    parameter_key: str
    records: list[ParameterObservation] = field(default_factory=list)

    def observe(self, observation: ParameterObservation) -> None:
        if observation.parameter_key != self.parameter_key:
            raise ValueError("observation_parameter_key_mismatch")
        self.records.append(observation)

    @property
    def observations(self) -> int:
        return len(self.records)

    @property
    def win_rate(self) -> float:
        return round((sum(1 for item in self.records if item.won) / self.observations) * 100.0, 4) if self.records else 0.0

    @property
    def expectancy(self) -> float:
        return round(_safe_mean([item.result_amount for item in self.records]), 4)

    @property
    def average_cost_points(self) -> float:
        return round(_safe_mean([item.execution_cost_points for item in self.records]), 4)

    def candidate(self) -> dict[str, float]:
        favorable = [item.favorable_excursion_points for item in self.records if item.favorable_excursion_points > 0.0]
        adverse = [item.adverse_excursion_points for item in self.records if item.adverse_excursion_points > 0.0]
        stops = [item.stop_distance_points for item in self.records if item.stop_distance_points > 0.0]
        holding = [item.holding_minutes for item in self.records if item.holding_minutes > 0.0]
        quality = [item.entry_quality for item in self.records]
        adaptive_stop = max(_percentile(adverse, 0.80), _safe_mean(stops))
        profit_objective = max(_percentile(favorable, 0.60), adaptive_stop * 1.25)
        holding_period = _percentile(holding, 0.60)
        confidence_floor = min(86.0, max(55.0, _safe_mean(quality) - max(0.0, self.average_cost_points - 25.0) * 0.15))
        return {
            "adaptive_stop_points": round(adaptive_stop, 4),
            "profit_objective_points": round(profit_objective, 4),
            "holding_period_minutes": round(holding_period, 4),
            "confidence_floor": round(confidence_floor, 4),
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "parameter_key": self.parameter_key,
            "observations": self.observations,
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            "average_cost_points": self.average_cost_points,
            "candidate": self.candidate(),
        }


class ParameterRepository:
    """Stores compact parameter profiles by regime-first grouping."""

    def __init__(self) -> None:
        self._profiles: dict[str, ParameterProfile] = {}

    def observe(self, observation: ParameterObservation) -> ParameterProfile:
        profile = self._profiles.setdefault(observation.parameter_key, ParameterProfile(observation.parameter_key))
        profile.observe(observation)
        return profile

    def ranked(self) -> list[ParameterProfile]:
        return sorted(
            self._profiles.values(),
            key=lambda profile: (profile.expectancy, profile.win_rate, profile.observations),
            reverse=True,
        )

    def as_dict(self) -> dict[str, Any]:
        ranked = self.ranked()
        return {
            "unique_profiles": len(ranked),
            "total_observations": sum(profile.observations for profile in ranked),
            "profiles": [profile.as_dict() for profile in ranked],
        }
