"""AI integration profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIIntegrationProfile:
    """Regime-first AI integration plan without autonomous execution writes."""

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

    @property
    def ai_alignment_score(self) -> float:
        risk_adjusted_quality = self.integration_quality * (1.0 - (self.integration_risk * 0.50))
        value = self.model_confidence * 0.40 + self.planned_runtime_weight * 0.25 + risk_adjusted_quality * 0.35
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def recommended_ai_weight(self) -> float:
        capped_weight = max(min(self.planned_runtime_weight, 0.85), 0.15)
        value = capped_weight * self.ai_alignment_score
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def integration_state(self) -> str:
        if self.data_quality < 0.60 or self.knowledge_quality < 0.60:
            return "AI_REVIEW_REQUIRED"
        if self.runtime_stability < 0.60 or self.explainability_score < 0.60:
            return "AI_REVIEW_REQUIRED"
        if self.integration_risk > 0.70:
            return "INTEGRATION_RISK_REVIEW_REQUIRED"
        if self.recommended_ai_weight >= 0.50:
            return "AI_ASSIST_READY"
        return "AI_OBSERVATION_ONLY"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "planned_runtime_weight": self.planned_runtime_weight,
            "adaptation_quality": self.adaptation_quality,
            "runtime_stability": self.runtime_stability,
            "model_confidence": self.model_confidence,
            "data_quality": self.data_quality,
            "knowledge_quality": self.knowledge_quality,
            "explainability_score": self.explainability_score,
            "integration_risk": self.integration_risk,
            "integration_quality": self.integration_quality,
            "ai_alignment_score": self.ai_alignment_score,
            "recommended_ai_weight": self.recommended_ai_weight,
            "integration_state": self.integration_state,
        }
