"""Data models for deterministic central-bank intelligence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class CentralBankObservation:
    observation_id: str
    institution: str
    communication_type: str
    speaker: str
    policy_bias: str
    gold_effect: str
    confidence: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class CentralBankIntelligenceReport:
    status: str
    reason: str
    observation_count: int
    hawkish_count: int
    dovish_count: int
    neutral_count: int
    aggregate_policy_bias: str
    aggregate_gold_effect: str
    aggregate_score: float
    confidence: float
    intelligence_ready: bool
    execution_allowed: bool
    next_review_time_utc: str
    observations: tuple[CentralBankObservation, ...]
    live_execution_enabled: bool = False
