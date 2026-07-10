"""Data models for deterministic USD index intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class USDIndexObservation:
    observation_id: str
    index_name: str
    current_value: float
    previous_value: float
    change_pct: float
    trend: str
    gold_correlation: str
    divergence: str
    gold_effect: str
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class USDIndexIntelligenceReport:
    status: str
    reason: str
    observation_count: int
    rising_count: int
    falling_count: int
    stable_count: int
    divergence_count: int
    aggregate_usd_trend: str
    aggregate_gold_effect: str
    aggregate_score: float
    confidence: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    observations: tuple[USDIndexObservation, ...]
    live_execution_enabled: bool = False
