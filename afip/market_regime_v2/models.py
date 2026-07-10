"""Data models for deterministic Market Regime V2 intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MarketRegimeComponent:
    name: str
    status: str
    effect: str
    score: float
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class MarketRegimeV2Report:
    status: str
    reason: str
    regime: str
    directional_bias: str
    risk_state: str
    aggregate_score: float
    confidence: float
    ready_component_count: int
    total_component_count: int
    component_alignment: str
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    components: tuple[MarketRegimeComponent, ...]
    live_execution_enabled: bool = False
