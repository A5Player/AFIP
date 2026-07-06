"""Adaptive AI foundation observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class AdaptiveAIFoundationObservation:
    """Normalized market observation for deterministic adaptive AI foundation."""

    market_regime: str
    signal_context: str
    result_amount: float
    confidence_score: float
    knowledge_quality: float
    sample_weight: float
    source_key: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AdaptiveAIFoundationObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("signal", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        result_amount = float(value.get("result_amount", value.get("net_result", 0.0)))
        confidence_score = _ratio(value.get("confidence_score", value.get("confidence", 0.0)))
        knowledge_quality = _ratio(value.get("knowledge_quality", value.get("quality", 0.0)))
        sample_weight = max(float(value.get("sample_weight", value.get("weight", 1.0))), 0.0)
        source_key = str(value.get("source_key", value.get("source", "OBSERVATION"))).strip().upper() or "OBSERVATION"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            result_amount=result_amount,
            confidence_score=confidence_score,
            knowledge_quality=knowledge_quality,
            sample_weight=sample_weight,
            source_key=source_key,
        )

    @property
    def has_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def weighted_result(self) -> float:
        return self.result_amount * self.sample_weight


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
