"""Adaptive confidence observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class AdaptiveConfidenceObservation:
    """Normalized evidence record for deterministic confidence adaptation."""

    market_regime: str
    signal_context: str
    raw_confidence: float
    self_evaluation_score: float
    data_quality: float
    knowledge_quality: float
    stability_score: float
    sample_size: float
    evidence_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AdaptiveConfidenceObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        raw_confidence = _ratio(value.get("raw_confidence", value.get("confidence", 0.0)))
        self_evaluation_score = _ratio(value.get("self_evaluation_score", value.get("evaluation_score", 0.0)))
        data_quality = _ratio(value.get("data_quality", value.get("quality", 0.0)))
        knowledge_quality = _ratio(value.get("knowledge_quality", value.get("knowledge", data_quality)))
        stability_score = _ratio(value.get("stability_score", value.get("stability", 1.0)))
        sample_size = max(float(value.get("sample_size", value.get("samples", 1.0))), 0.0)
        evidence_source = str(value.get("evidence_source", value.get("source", "CONFIDENCE"))).strip().upper() or "CONFIDENCE"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            raw_confidence=raw_confidence,
            self_evaluation_score=self_evaluation_score,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            stability_score=stability_score,
            sample_size=sample_size,
            evidence_source=evidence_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def evidence_quality(self) -> float:
        value = (self.self_evaluation_score + self.data_quality + self.knowledge_quality + self.stability_score) / 4.0
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def weighted_raw_confidence(self) -> float:
        return self.raw_confidence * self.sample_size

    @property
    def weighted_evidence_quality(self) -> float:
        return self.evidence_quality * self.sample_size


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
