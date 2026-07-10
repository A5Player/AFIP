"""Data models for deterministic structured news intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class NewsItemIntelligence:
    news_id: str
    headline: str
    source: str
    published_time_utc: str
    category: str
    sentiment: str
    sentiment_score: float
    reliability_score: float
    gold_relevance: str
    duplicate: bool
    duplicate_of: str
    structured_signal: str
    explanation_en: str
    explanation_th: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class NewsIntelligenceReport:
    status: str
    reason: str
    item_count: int
    unique_item_count: int
    duplicate_count: int
    high_reliability_count: int
    gold_relevant_count: int
    aggregate_sentiment: str
    aggregate_sentiment_score: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    items: tuple[NewsItemIntelligence, ...]
    live_execution_enabled: bool = False
