"""Validation readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .validation_profile import ValidationProfile


@dataclass(frozen=True)
class ValidationDecision:
    """Deterministic validation decision."""

    status: str
    readiness: str
    reason: str
    validation_score: float
    review_profile_count: int
    invalid_market_regime_count: int
    production_write_allowed: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "validation_score": self.validation_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
            "production_write_allowed": self.production_write_allowed,
        }


@dataclass(frozen=True)
class ValidationPolicy:
    """Approve validation only when evidence is stable, explainable, and low risk."""

    minimum_evidence_quality: float = 0.60
    maximum_validation_risk: float = 0.70

    def decide(
        self,
        profiles: tuple[ValidationProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> ValidationDecision:
        if invalid_market_regime_count:
            return ValidationDecision(
                status="VALIDATION_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_validation",
                validation_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return ValidationDecision(
                status="VALIDATION_WAIT",
                readiness="WAIT",
                reason="ai_integration_required",
                validation_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )
        review_profiles = tuple(
            item
            for item in profiles
            if item.evidence_quality < self.minimum_evidence_quality
            or item.data_quality < self.minimum_evidence_quality
            or item.knowledge_quality < self.minimum_evidence_quality
            or item.runtime_stability < self.minimum_evidence_quality
            or item.validation_sample_quality < self.minimum_evidence_quality
            or item.validation_consistency < self.minimum_evidence_quality
            or item.validation_risk > self.maximum_validation_risk
        )
        score = round(mean(item.validation_score for item in profiles), 6)
        if review_profiles:
            return ValidationDecision(
                status="VALIDATION_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="validation_review_required",
                validation_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        return ValidationDecision(
            status="VALIDATION_READY",
            readiness="READY",
            reason="validation_ready_for_production_readiness_review",
            validation_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
            production_write_allowed=False,
        )
