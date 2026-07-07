"""Validation profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationProfile:
    """Regime-first validation profile for AI integration readiness."""

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

    @property
    def validation_score(self) -> float:
        risk_adjusted_evidence = self.evidence_quality * (1.0 - (self.validation_risk * 0.55))
        value = (
            self.ai_alignment_score * 0.30
            + self.recommended_ai_weight * 0.20
            + self.runtime_stability * 0.15
            + risk_adjusted_evidence * 0.35
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def approved_runtime_weight(self) -> float:
        value = self.recommended_ai_weight * self.validation_score
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def validation_state(self) -> str:
        if self.data_quality < 0.60 or self.knowledge_quality < 0.60:
            return "VALIDATION_REVIEW_REQUIRED"
        if self.explainability_score < 0.60 or self.validation_sample_quality < 0.60:
            return "VALIDATION_REVIEW_REQUIRED"
        if self.runtime_stability < 0.60 or self.validation_consistency < 0.60:
            return "VALIDATION_REVIEW_REQUIRED"
        if self.validation_risk > 0.70:
            return "VALIDATION_RISK_REVIEW_REQUIRED"
        if self.validation_score >= 0.70:
            return "VALIDATION_READY"
        return "VALIDATION_OBSERVATION_ONLY"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "ai_alignment_score": self.ai_alignment_score,
            "recommended_ai_weight": self.recommended_ai_weight,
            "integration_quality": self.integration_quality,
            "data_quality": self.data_quality,
            "knowledge_quality": self.knowledge_quality,
            "explainability_score": self.explainability_score,
            "runtime_stability": self.runtime_stability,
            "validation_sample_quality": self.validation_sample_quality,
            "validation_consistency": self.validation_consistency,
            "validation_risk": self.validation_risk,
            "evidence_quality": self.evidence_quality,
            "validation_score": self.validation_score,
            "approved_runtime_weight": self.approved_runtime_weight,
            "validation_state": self.validation_state,
        }
