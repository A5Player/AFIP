"""Milestone F completion profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MilestoneFCompletionProfile:
    """Regime-first final profile for Milestone F closure."""

    market_regime: str
    signal_context: str
    production_readiness_score: float
    production_runtime_weight: float
    readiness_evidence_quality: float
    data_quality: float
    knowledge_quality: float
    strategy_quality: float
    runtime_stability: float
    validation_quality: float
    monitoring_quality: float
    rollback_readiness: float
    documentation_quality: float
    handoff_quality: float
    completion_risk: float

    @property
    def operational_closure_quality(self) -> float:
        value = (
            self.monitoring_quality * 0.35
            + self.rollback_readiness * 0.30
            + self.documentation_quality * 0.20
            + self.handoff_quality * 0.15
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def milestone_evidence_quality(self) -> float:
        value = (
            self.readiness_evidence_quality * 0.20
            + self.data_quality * 0.15
            + self.knowledge_quality * 0.15
            + self.strategy_quality * 0.10
            + self.runtime_stability * 0.15
            + self.validation_quality * 0.10
            + self.operational_closure_quality * 0.15
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def milestone_completion_score(self) -> float:
        risk_adjusted_evidence = self.milestone_evidence_quality * (1.0 - (self.completion_risk * 0.55))
        value = (
            self.production_readiness_score * 0.35
            + self.production_runtime_weight * 0.10
            + self.runtime_stability * 0.15
            + self.validation_quality * 0.10
            + self.operational_closure_quality * 0.10
            + risk_adjusted_evidence * 0.20
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def final_runtime_weight(self) -> float:
        value = self.production_runtime_weight * self.milestone_completion_score
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def completion_state(self) -> str:
        if self.data_quality < 0.60 or self.knowledge_quality < 0.60:
            return "MILESTONE_F_REVIEW_REQUIRED"
        if self.strategy_quality < 0.60 or self.validation_quality < 0.60:
            return "MILESTONE_F_REVIEW_REQUIRED"
        if self.runtime_stability < 0.60:
            return "RUNTIME_REVIEW_REQUIRED"
        if self.monitoring_quality < 0.60 or self.rollback_readiness < 0.60:
            return "OPERATIONAL_REVIEW_REQUIRED"
        if self.documentation_quality < 0.60 or self.handoff_quality < 0.60:
            return "DOCUMENTATION_REVIEW_REQUIRED"
        if self.completion_risk > 0.70:
            return "MILESTONE_F_RISK_REVIEW_REQUIRED"
        if self.milestone_completion_score >= 0.74:
            return "MILESTONE_F_COMPLETE"
        return "MILESTONE_F_OBSERVATION_ONLY"

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "production_readiness_score": self.production_readiness_score,
            "production_runtime_weight": self.production_runtime_weight,
            "readiness_evidence_quality": self.readiness_evidence_quality,
            "data_quality": self.data_quality,
            "knowledge_quality": self.knowledge_quality,
            "strategy_quality": self.strategy_quality,
            "runtime_stability": self.runtime_stability,
            "validation_quality": self.validation_quality,
            "monitoring_quality": self.monitoring_quality,
            "rollback_readiness": self.rollback_readiness,
            "documentation_quality": self.documentation_quality,
            "handoff_quality": self.handoff_quality,
            "completion_risk": self.completion_risk,
            "operational_closure_quality": self.operational_closure_quality,
            "milestone_evidence_quality": self.milestone_evidence_quality,
            "milestone_completion_score": self.milestone_completion_score,
            "final_runtime_weight": self.final_runtime_weight,
            "completion_state": self.completion_state,
        }
