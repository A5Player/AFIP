"""Data models for deterministic gold ETF flow intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ETFFlowObservation:
    observation_id: str
    fund: str
    daily_flow_usd: float
    weekly_flow_usd: float
    holdings_change_tonnes: float
    flow_trend: str
    gold_effect: str
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class ETFFlowIntelligenceReport:
    status: str
    reason: str
    observation_count: int
    inflow_count: int
    outflow_count: int
    neutral_count: int
    aggregate_flow_trend: str
    aggregate_gold_effect: str
    aggregate_score: float
    total_daily_flow_usd: float
    total_weekly_flow_usd: float
    confidence: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    observations: tuple[ETFFlowObservation, ...]
    live_execution_enabled: bool = False
