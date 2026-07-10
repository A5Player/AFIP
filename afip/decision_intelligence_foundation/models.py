"""Models for deterministic Decision Intelligence Foundation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class DecisionEvidence:
    source: str
    status: str
    direction: str
    score: float
    confidence: float
    weight: float
    weighted_score: float
    explanation_en: str
    explanation_th: str
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class DecisionIntelligenceReport:
    status: str
    reason: str
    consensus: str
    conflict_state: str
    opportunity_state: str
    aggregate_score: float
    confidence: float
    supporting_count: int
    opposing_count: int
    neutral_count: int
    ready_evidence_count: int
    total_evidence_count: int
    market_regime: str
    market_regime_bias: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    evidence: tuple[DecisionEvidence, ...]
    decision_ready: bool
    execution_allowed: bool = False
    live_execution_enabled: bool = False
