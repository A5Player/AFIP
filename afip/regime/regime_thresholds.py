"""Learned regime thresholds derived from historical evidence."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Mapping, Any

from .regime_evidence import RegimeEvidence


@dataclass(frozen=True)
class RegimeThresholds:
    quiet_range_percent: float
    expansion_range_percent: float
    trend_efficiency_floor: float
    participation_floor: float
    transition_pressure_ceiling: float
    source_observations: int

    def as_dict(self) -> dict[str, object]:
        return {
            "quiet_range_percent": self.quiet_range_percent,
            "expansion_range_percent": self.expansion_range_percent,
            "trend_efficiency_floor": self.trend_efficiency_floor,
            "participation_floor": self.participation_floor,
            "transition_pressure_ceiling": self.transition_pressure_ceiling,
            "source_observations": self.source_observations,
        }


class RegimeThresholdLearner:
    """Build deterministic thresholds from evidence rather than fixed signal constants."""

    minimum_observations: int = 3

    def learn(self, evidence: Iterable[RegimeEvidence | Mapping[str, Any]]) -> RegimeThresholds | None:
        records = [item if isinstance(item, RegimeEvidence) else RegimeEvidence.from_mapping(item) for item in evidence]
        if len(records) < self.minimum_observations:
            return None
        ranges = sorted(item.range_percent for item in records)
        efficiencies = sorted(item.trend_efficiency for item in records)
        participation = sorted(item.participation_score for item in records)
        pressure = sorted(abs(item.transition_pressure) for item in records)
        return RegimeThresholds(
            quiet_range_percent=round(self._percentile(ranges, 0.34), 6),
            expansion_range_percent=round(self._percentile(ranges, 0.67), 6),
            trend_efficiency_floor=round(median(efficiencies), 6),
            participation_floor=round(median(participation), 6),
            transition_pressure_ceiling=round(self._percentile(pressure, 0.67), 6),
            source_observations=len(records),
        )

    @staticmethod
    def _percentile(values: list[float], fraction: float) -> float:
        if not values:
            return 0.0
        index = int(round((len(values) - 1) * fraction))
        return values[max(0, min(len(values) - 1, index))]
