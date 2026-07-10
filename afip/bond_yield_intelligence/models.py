"""Data models for deterministic bond-yield intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class BondYieldObservation:
    observation_id: str
    us2y_yield: float
    us10y_yield: float
    real_yield: float
    previous_us2y_yield: float
    previous_us10y_yield: float
    previous_real_yield: float
    curve_spread_bps: float
    curve_shape: str
    nominal_yield_trend: str
    real_yield_trend: str
    gold_effect: str
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class BondYieldIntelligenceReport:
    status: str
    reason: str
    observation_count: int
    rising_nominal_count: int
    falling_nominal_count: int
    rising_real_count: int
    falling_real_count: int
    inverted_curve_count: int
    aggregate_yield_trend: str
    aggregate_real_yield_trend: str
    aggregate_curve_shape: str
    aggregate_gold_effect: str
    aggregate_score: float
    confidence: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    observations: tuple[BondYieldObservation, ...]
    live_execution_enabled: bool = False
