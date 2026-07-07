"""AI integration observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class AIIntegrationObservation:
    """Normalized runtime adaptation evidence for deterministic AI integration planning."""

    market_regime: str
    signal_context: str
    planned_runtime_weight: float
    adaptation_quality: float
    runtime_stability: float
    model_confidence: float
    data_quality: float
    knowledge_quality: float
    explainability_score: float
    integration_risk: float
    adaptation_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AIIntegrationObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        planned_runtime_weight = _ratio(value.get("planned_runtime_weight", value.get("runtime_weight", 0.50)))
        adaptation_quality = _ratio(value.get("adaptation_quality", value.get("quality", 0.0)))
        runtime_stability = _ratio(value.get("runtime_stability", value.get("stability_score", 1.0)))
        model_confidence = _ratio(value.get("model_confidence", value.get("ai_confidence", planned_runtime_weight)))
        data_quality = _ratio(value.get("data_quality", adaptation_quality))
        knowledge_quality = _ratio(value.get("knowledge_quality", adaptation_quality))
        explainability_score = _ratio(value.get("explainability_score", value.get("explainability", 1.0)))
        integration_risk = _ratio(value.get("integration_risk", value.get("risk_pressure", 0.0)))
        adaptation_source = str(value.get("adaptation_source", value.get("source", "RUNTIME_ADAPTATION"))).strip().upper() or "RUNTIME_ADAPTATION"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            planned_runtime_weight=planned_runtime_weight,
            adaptation_quality=adaptation_quality,
            runtime_stability=runtime_stability,
            model_confidence=model_confidence,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            explainability_score=explainability_score,
            integration_risk=integration_risk,
            adaptation_source=adaptation_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def integration_quality(self) -> float:
        quality = (
            self.adaptation_quality * 0.25
            + self.runtime_stability * 0.20
            + self.data_quality * 0.20
            + self.knowledge_quality * 0.20
            + self.explainability_score * 0.15
        )
        return round(min(max(quality, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)
