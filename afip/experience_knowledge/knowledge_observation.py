"""Experience knowledge observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ExperienceKnowledgeObservation:
    """Normalized market experience record for deterministic knowledge building."""

    market_regime: str
    signal_context: str
    outcome_state: str
    realized_result: float
    adaptive_confidence: float
    self_evaluation_score: float
    data_quality: float
    knowledge_quality: float
    recency_score: float
    sample_weight: float
    evidence_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExperienceKnowledgeObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        outcome_state = str(value.get("outcome_state", value.get("result_state", "CLOSED"))).strip().upper() or "CLOSED"
        realized_result = float(value.get("realized_result", value.get("result", value.get("net_result", 0.0))))
        adaptive_confidence = _ratio(value.get("adaptive_confidence", value.get("confidence", 0.0)))
        self_evaluation_score = _ratio(value.get("self_evaluation_score", value.get("evaluation_score", 0.0)))
        data_quality = _ratio(value.get("data_quality", value.get("quality", 0.0)))
        knowledge_quality = _ratio(value.get("knowledge_quality", value.get("knowledge", data_quality)))
        recency_score = _ratio(value.get("recency_score", value.get("recency", 1.0)))
        sample_weight = max(float(value.get("sample_weight", value.get("weight", value.get("sample_size", 1.0)))), 0.0)
        evidence_source = str(value.get("evidence_source", value.get("source", "EXPERIENCE"))).strip().upper() or "EXPERIENCE"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            outcome_state=outcome_state,
            realized_result=realized_result,
            adaptive_confidence=adaptive_confidence,
            self_evaluation_score=self_evaluation_score,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            recency_score=recency_score,
            sample_weight=sample_weight,
            evidence_source=evidence_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def positive_weight(self) -> float:
        return self.sample_weight if self.realized_result > 0.0 else 0.0

    @property
    def weighted_result(self) -> float:
        return self.realized_result * self.sample_weight

    @property
    def reliability_score(self) -> float:
        value = (self.adaptive_confidence + self.self_evaluation_score + self.data_quality + self.knowledge_quality + self.recency_score) / 5.0
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def weighted_reliability(self) -> float:
        return self.reliability_score * self.sample_weight


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
