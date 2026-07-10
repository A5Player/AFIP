"""Data models for deterministic COT intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class COTObservation:
    report_id: str
    market: str
    commercial_long: int
    commercial_short: int
    noncommercial_long: int
    noncommercial_short: int
    commercial_net: int
    noncommercial_net: int
    noncommercial_net_change: int
    positioning_trend: str
    gold_effect: str
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class COTIntelligenceReport:
    status: str
    reason: str
    observation_count: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    aggregate_positioning_bias: str
    aggregate_score: float
    confidence: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    observations: tuple[COTObservation, ...]
    live_execution_enabled: bool = False
