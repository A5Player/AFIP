"""Adaptive confidence readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .confidence_profile import AdaptiveConfidenceProfile


@dataclass(frozen=True)
class AdaptiveConfidenceDecision:
    """Deterministic adaptive confidence decision."""

    status: str
    readiness: str
    reason: str
    confidence_score: float
    review_profile_count: int
    invalid_market_regime_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "confidence_score": self.confidence_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
        }


@dataclass(frozen=True)
class AdaptiveConfidencePolicy:
    """Accept confidence adaptation only when evidence is validated."""

    minimum_evidence_quality: float = 0.60
    minimum_data_quality: float = 0.60
    minimum_stability_score: float = 0.55
    maximum_absolute_adjustment: float = 0.25

    def decide(
        self,
        profiles: tuple[AdaptiveConfidenceProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> AdaptiveConfidenceDecision:
        if invalid_market_regime_count:
            return AdaptiveConfidenceDecision(
                status="ADAPTIVE_CONFIDENCE_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_confidence_adaptation",
                confidence_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return AdaptiveConfidenceDecision(
                status="ADAPTIVE_CONFIDENCE_WAIT",
                readiness="WAIT",
                reason="confidence_evidence_required",
                confidence_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )

        confidence_score = round(mean(item.adaptive_confidence for item in profiles), 6)
        review_profiles = tuple(
            item
            for item in profiles
            if item.average_evidence_quality < self.minimum_evidence_quality
            or item.average_data_quality < self.minimum_data_quality
            or item.average_stability_score < self.minimum_stability_score
            or abs(item.confidence_adjustment) > self.maximum_absolute_adjustment
        )
        if review_profiles:
            return AdaptiveConfidenceDecision(
                status="ADAPTIVE_CONFIDENCE_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="confidence_profiles_need_validation_before_runtime_use",
                confidence_score=confidence_score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        return AdaptiveConfidenceDecision(
            status="ADAPTIVE_CONFIDENCE_READY",
            readiness="READY",
            reason="confidence_profiles_ready_for_deterministic_runtime_use",
            confidence_score=confidence_score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
