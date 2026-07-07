"""Self evaluation readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .evaluation_profile import SelfEvaluationProfile


@dataclass(frozen=True)
class SelfEvaluationDecision:
    """Deterministic self evaluation decision."""

    status: str
    readiness: str
    reason: str
    evaluation_score: float
    review_profile_count: int
    invalid_market_regime_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "evaluation_score": self.evaluation_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
        }


@dataclass(frozen=True)
class SelfEvaluationPolicy:
    """Evaluate closed decisions without randomness or production learning writes."""

    minimum_evaluation_score: float = 0.60
    maximum_confidence_error: float = 0.40

    def decide(
        self,
        profiles: tuple[SelfEvaluationProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> SelfEvaluationDecision:
        if invalid_market_regime_count:
            return SelfEvaluationDecision(
                status="SELF_EVALUATION_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_for_closed_decision_evaluation",
                evaluation_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return SelfEvaluationDecision(
                status="SELF_EVALUATION_WAIT",
                readiness="WAIT",
                reason="closed_decision_observations_required",
                evaluation_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )

        score = round(mean(item.evaluation_score for item in profiles), 6)
        review_profiles = tuple(
            item
            for item in profiles
            if item.evaluation_score < self.minimum_evaluation_score
            or item.average_confidence_error > self.maximum_confidence_error
        )
        if review_profiles:
            return SelfEvaluationDecision(
                status="SELF_EVALUATION_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="closed_decision_profiles_need_review_before_adaptation",
                evaluation_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        return SelfEvaluationDecision(
            status="SELF_EVALUATION_READY",
            readiness="READY",
            reason="closed_decision_profiles_ready_for_validated_learning",
            evaluation_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
