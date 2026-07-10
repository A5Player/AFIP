"""Data models for deterministic open-interest intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class OpenInterestObservation:
    observation_id: str
    market: str
    price_change_pct: float
    open_interest: int
    previous_open_interest: int
    open_interest_change: int
    open_interest_change_pct: float
    participation_trend: str
    market_interpretation: str
    gold_effect: str
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class OpenInterestIntelligenceReport:
    status: str
    reason: str
    observation_count: int
    rising_count: int
    falling_count: int
    stable_count: int
    aggregate_participation: str
    aggregate_gold_effect: str
    aggregate_score: float
    confidence: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    observations: tuple[OpenInterestObservation, ...]
    live_execution_enabled: bool = False
