"""Production readiness profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionReadinessProfile:
    """Regime-first production readiness profile before live execution approval."""

    market_regime: str
    signal_context: str
    validation_score: float
    approved_runtime_weight: float
    evidence_quality: float
    data_quality: float
    knowledge_quality: float
    explainability_score: float
    runtime_stability: float
    validation_sample_quality: float
    validation_consistency: float
    validation_risk: float
    deployment_control_quality: float
    monitoring_quality: float
    rollback_readiness: float

    @property
    def operational_quality(self) -> float:
        quality = (
            self.deployment_control_quality * 0.35
            + self.monitoring_quality * 0.35
            + self.rollback_readiness * 0.30
        )
        return round(min(max(quality, 0.0), 1.0), 6)

    @property
    def readiness_evidence_quality(self) -> float:
        quality = (
            self.evidence_quality * 0.20
            + self.data_quality * 0.15
            + self.knowledge_quality * 0.15
            + self.explainability_score * 0.10
            + self.runtime_stability * 0.15
            + self.validation_sample_quality * 0.10
            + self.validation_consistency * 0.10
            + self.operational_quality * 0.05
        )
        return round(min(max(quality, 0.0), 1.0), 6)

    @property
    def production_readiness_score(self) -> float:
        risk_adjusted_evidence = self.readiness_evidence_quality * (1.0 - (self.validation_risk * 0.60))
        value = (
            self.validation_score * 0.35
            + self.approved_runtime_weight * 0.15
            + self.runtime_stability * 0.15
            + self.operational_quality * 0.15
            + risk_adjusted_evidence * 0.20
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def production_runtime_weight(self) -> float:
        value = self.approved_runtime_weight * self.production_readiness_score
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def readiness_state(self) -> str:
        if self.data_quality < 0.60 or self.knowledge_quality < 0.60:
            return "PRODUCTION_REVIEW_REQUIRED"
        if self.explainability_score < 0.60 or self.validation_sample_quality < 0.60:
            return "PRODUCTION_REVIEW_REQUIRED"
        if self.runtime_stability < 0.60 or self.validation_consistency < 0.60:
            return "PRODUCTION_REVIEW_REQUIRED"
        if self.deployment_control_quality < 0.60 or self.monitoring_quality < 0.60 or self.rollback_readiness < 0.60:
            return "OPERATIONAL_REVIEW_REQUIRED"
        if self.validation_risk > 0.70:
            return "PRODUCTION_RISK_REVIEW_REQUIRED"
        if self.production_readiness_score >= 0.72:
            return "PRODUCTION_READY"
        return "PRODUCTION_OBSERVATION_ONLY"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "validation_score": self.validation_score,
            "approved_runtime_weight": self.approved_runtime_weight,
            "evidence_quality": self.evidence_quality,
            "data_quality": self.data_quality,
            "knowledge_quality": self.knowledge_quality,
            "explainability_score": self.explainability_score,
            "runtime_stability": self.runtime_stability,
            "validation_sample_quality": self.validation_sample_quality,
            "validation_consistency": self.validation_consistency,
            "validation_risk": self.validation_risk,
            "deployment_control_quality": self.deployment_control_quality,
            "monitoring_quality": self.monitoring_quality,
            "rollback_readiness": self.rollback_readiness,
            "operational_quality": self.operational_quality,
            "readiness_evidence_quality": self.readiness_evidence_quality,
            "production_readiness_score": self.production_readiness_score,
            "production_runtime_weight": self.production_runtime_weight,
            "readiness_state": self.readiness_state,
        }
