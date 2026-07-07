"""Production readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .readiness_profile import ProductionReadinessProfile


@dataclass(frozen=True)
class ProductionReadinessDecision:
    """Deterministic production readiness decision."""

    status: str
    readiness: str
    reason: str
    readiness_score: float
    review_profile_count: int
    invalid_market_regime_count: int
    live_execution_allowed: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "readiness_score": self.readiness_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
            "live_execution_allowed": self.live_execution_allowed,
        }


@dataclass(frozen=True)
class ProductionReadinessPolicy:
    """Approve production readiness only when validated evidence and controls are stable."""

    minimum_readiness_quality: float = 0.60
    minimum_production_score: float = 0.72
    maximum_validation_risk: float = 0.70

    def decide(
        self,
        profiles: tuple[ProductionReadinessProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> ProductionReadinessDecision:
        if invalid_market_regime_count:
            return ProductionReadinessDecision(
                status="PRODUCTION_READINESS_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_production_readiness",
                readiness_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return ProductionReadinessDecision(
                status="PRODUCTION_READINESS_WAIT",
                readiness="WAIT",
                reason="validation_required",
                readiness_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )
        review_profiles = tuple(
            item
            for item in profiles
            if item.readiness_evidence_quality < self.minimum_readiness_quality
            or item.data_quality < self.minimum_readiness_quality
            or item.knowledge_quality < self.minimum_readiness_quality
            or item.explainability_score < self.minimum_readiness_quality
            or item.runtime_stability < self.minimum_readiness_quality
            or item.validation_sample_quality < self.minimum_readiness_quality
            or item.validation_consistency < self.minimum_readiness_quality
            or item.deployment_control_quality < self.minimum_readiness_quality
            or item.monitoring_quality < self.minimum_readiness_quality
            or item.rollback_readiness < self.minimum_readiness_quality
            or item.validation_risk > self.maximum_validation_risk
        )
        score = round(mean(item.production_readiness_score for item in profiles), 6)
        if review_profiles:
            return ProductionReadinessDecision(
                status="PRODUCTION_READINESS_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="production_readiness_review_required",
                readiness_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        if score >= self.minimum_production_score:
            return ProductionReadinessDecision(
                status="PRODUCTION_READY",
                readiness="READY",
                reason="validated_evidence_and_controls_ready",
                readiness_score=score,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )
        return ProductionReadinessDecision(
            status="PRODUCTION_READINESS_OBSERVATION_ONLY",
            readiness="OBSERVE",
            reason="production_readiness_score_below_threshold",
            readiness_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
