"""Self evaluation observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class SelfEvaluationObservation:
    """Normalized closed-decision record for deterministic self evaluation."""

    market_regime: str
    decision_status: str
    expected_confidence: float
    realized_result: float
    data_quality: float
    knowledge_quality: float
    sample_weight: float
    evidence_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SelfEvaluationObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        decision_status = str(value.get("decision_status", value.get("decision", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        expected_confidence = _ratio(value.get("expected_confidence", value.get("confidence", 0.0)))
        realized_result = float(value.get("realized_result", value.get("result_amount", 0.0)))
        data_quality = _ratio(value.get("data_quality", value.get("quality", 0.0)))
        knowledge_quality = _ratio(value.get("knowledge_quality", value.get("knowledge", data_quality)))
        sample_weight = max(float(value.get("sample_weight", value.get("weight", 1.0))), 0.0)
        evidence_source = str(value.get("evidence_source", value.get("source", "EVALUATION"))).strip().upper() or "EVALUATION"
        return cls(
            market_regime=market_regime,
            decision_status=decision_status,
            expected_confidence=expected_confidence,
            realized_result=realized_result,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            sample_weight=sample_weight,
            evidence_source=evidence_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def weighted_result(self) -> float:
        return self.realized_result * self.sample_weight

    @property
    def confidence_error(self) -> float:
        actual_score = 1.0 if self.realized_result > 0.0 else 0.0
        return abs(self.expected_confidence - actual_score)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
