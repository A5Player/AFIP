"""Data-derived market regime profiles."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping, Any

from .regime_evidence import RegimeEvidence


@dataclass(frozen=True)
class RegimeProfile:
    regime_first_key: str
    market_regime: str
    volatility_bucket: str
    direction: str
    observations: int
    average_range_percent: float
    average_trend_efficiency: float
    average_participation_score: float
    average_transition_pressure: float
    average_result_amount: float

    @property
    def regime_quality_score(self) -> float:
        participation = self.average_participation_score
        efficiency = self.average_trend_efficiency
        pressure_penalty = abs(self.average_transition_pressure) * 0.5
        result_bonus = max(min(self.average_result_amount, 20.0), -20.0) * 0.5
        return round(max(0.0, min(100.0, participation + efficiency - pressure_penalty + result_bonus)), 4)

    def as_dict(self) -> dict[str, object]:
        return {
            "regime_first_key": self.regime_first_key,
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "direction": self.direction,
            "observations": self.observations,
            "average_range_percent": self.average_range_percent,
            "average_trend_efficiency": self.average_trend_efficiency,
            "average_participation_score": self.average_participation_score,
            "average_transition_pressure": self.average_transition_pressure,
            "average_result_amount": self.average_result_amount,
            "regime_quality_score": self.regime_quality_score,
        }


class RegimeProfileRepository:
    """Store regime evidence grouped by market regime before directional logic."""

    def __init__(self, evidence: Iterable[RegimeEvidence | Mapping[str, Any]] | None = None) -> None:
        self._evidence: list[RegimeEvidence] = []
        for item in evidence or []:
            self.add(item)

    def add(self, evidence: RegimeEvidence | Mapping[str, Any]) -> None:
        normalized = evidence if isinstance(evidence, RegimeEvidence) else RegimeEvidence.from_mapping(evidence)
        self._evidence.append(normalized)
        self._evidence.sort(key=lambda item: (item.regime_first_key, item.observed_at.isoformat()))

    def grouped(self) -> dict[str, list[RegimeEvidence]]:
        groups: dict[str, list[RegimeEvidence]] = {}
        for item in self._evidence:
            groups.setdefault(item.regime_first_key, []).append(item)
        return dict(sorted(groups.items()))

    def profiles(self) -> list[RegimeProfile]:
        profiles: list[RegimeProfile] = []
        for key, items in self.grouped().items():
            profiles.append(
                RegimeProfile(
                    regime_first_key=key,
                    market_regime=items[0].market_regime,
                    volatility_bucket=items[0].volatility_bucket,
                    direction=items[0].direction,
                    observations=len(items),
                    average_range_percent=round(mean(item.range_percent for item in items), 6),
                    average_trend_efficiency=round(mean(item.trend_efficiency for item in items), 6),
                    average_participation_score=round(mean(item.participation_score for item in items), 6),
                    average_transition_pressure=round(mean(item.transition_pressure for item in items), 6),
                    average_result_amount=round(mean(item.result_amount for item in items), 6),
                )
            )
        profiles.sort(key=lambda profile: (-profile.regime_quality_score, profile.regime_first_key))
        return profiles

    def as_dict(self) -> dict[str, object]:
        profiles = [profile.as_dict() for profile in self.profiles()]
        return {
            "status": "REGIME_PROFILE_READY" if self._evidence else "REGIME_PROFILE_DATA_REQUIRED",
            "evidence_count": len(self._evidence),
            "group_count": len(profiles),
            "profiles": profiles,
        }
