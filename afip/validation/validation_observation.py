"""Validation observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ValidationObservation:
    """Normalized AI integration evidence for deterministic validation."""

    market_regime: str
    signal_context: str
    ai_alignment_score: float
    recommended_ai_weight: float
    integration_quality: float
    data_quality: float
    knowledge_quality: float
    explainability_score: float
    runtime_stability: float
    validation_sample_quality: float
    validation_consistency: float
    validation_risk: float
    validation_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidationObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        ai_alignment_score = _ratio(value.get("ai_alignment_score", value.get("alignment_score", 0.0)))
        recommended_ai_weight = _ratio(value.get("recommended_ai_weight", value.get("ai_weight", 0.0)))
        integration_quality = _ratio(value.get("integration_quality", value.get("quality", 0.0)))
        data_quality = _ratio(value.get("data_quality", integration_quality))
        knowledge_quality = _ratio(value.get("knowledge_quality", integration_quality))
        explainability_score = _ratio(value.get("explainability_score", value.get("explainability", 1.0)))
        runtime_stability = _ratio(value.get("runtime_stability", value.get("stability_score", 1.0)))
        validation_sample_quality = _ratio(value.get("validation_sample_quality", value.get("sample_quality", data_quality)))
        validation_consistency = _ratio(value.get("validation_consistency", value.get("consistency", runtime_stability)))
        validation_risk = _ratio(value.get("validation_risk", value.get("risk_pressure", 0.0)))
        validation_source = str(value.get("validation_source", value.get("source", "AI_INTEGRATION"))).strip().upper() or "AI_INTEGRATION"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            ai_alignment_score=ai_alignment_score,
            recommended_ai_weight=recommended_ai_weight,
            integration_quality=integration_quality,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            explainability_score=explainability_score,
            runtime_stability=runtime_stability,
            validation_sample_quality=validation_sample_quality,
            validation_consistency=validation_consistency,
            validation_risk=validation_risk,
            validation_source=validation_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def evidence_quality(self) -> float:
        quality = (
            self.integration_quality * 0.20
            + self.data_quality * 0.20
            + self.knowledge_quality * 0.20
            + self.explainability_score * 0.15
            + self.validation_sample_quality * 0.15
            + self.validation_consistency * 0.10
        )
        return round(min(max(quality, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
