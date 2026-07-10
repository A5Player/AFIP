"""Data models for deterministic GOLD# macro intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MacroIndicatorIntelligence:
    indicator_id: str
    indicator: str
    category: str
    actual: float | None
    forecast: float | None
    previous: float | None
    surprise: float
    direction: str
    gold_effect: str
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]: return self.__dict__.copy()

@dataclass(frozen=True)
class GoldMacroIntelligenceReport:
    status: str
    reason: str
    indicator_count: int
    inflation_count: int
    employment_count: int
    growth_count: int
    activity_count: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    aggregate_bias: str
    aggregate_score: float
    confidence: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    indicators: tuple[MacroIndicatorIntelligence, ...]
    live_execution_enabled: bool = False
