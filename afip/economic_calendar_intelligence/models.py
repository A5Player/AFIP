"""Data models for deterministic economic calendar intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class EconomicEventIntelligence:
    event_id: str
    title: str
    country: str
    currency: str
    scheduled_time_utc: str
    impact: str
    gold_relevance: str
    event_category: str
    minutes_until_event: int
    event_window: str
    trading_allowed: bool
    trading_block_reason: str
    explanation_en: str
    explanation_th: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class EconomicCalendarReport:
    status: str
    reason: str
    current_time_utc: str
    event_count: int
    high_impact_count: int
    gold_relevant_count: int
    trading_allowed: bool
    trading_block_reason: str
    next_event_time_utc: str
    next_review_time_utc: str
    events: tuple[EconomicEventIntelligence, ...]
    live_execution_enabled: bool = False
