"""Milestone F completion policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .final_profile import MilestoneFCompletionProfile


@dataclass(frozen=True)
class MilestoneFCompletionDecision:
    """Deterministic Milestone F completion decision."""

    status: str
    completion: str
    reason: str
    completion_score: float
    review_profile_count: int
    invalid_market_regime_count: int
    next_milestone_allowed: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "completion": self.completion,
            "reason": self.reason,
            "completion_score": self.completion_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
            "next_milestone_allowed": self.next_milestone_allowed,
        }


@dataclass(frozen=True)
class MilestoneFCompletionPolicy:
    """Close Milestone F only when readiness evidence, controls, and handoff are complete."""

    minimum_completion_quality: float = 0.60
    minimum_completion_score: float = 0.74
    maximum_completion_risk: float = 0.70

    def decide(
        self,
        profiles: tuple[MilestoneFCompletionProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> MilestoneFCompletionDecision:
        if invalid_market_regime_count:
            return MilestoneFCompletionDecision(
                status="MILESTONE_F_COMPLETION_BLOCKED",
                completion="BLOCKED",
                reason="market_regime_required_before_milestone_completion",
                completion_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return MilestoneFCompletionDecision(
                status="MILESTONE_F_COMPLETION_WAIT",
                completion="WAIT",
                reason="production_readiness_required",
                completion_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )
        review_profiles = tuple(
            item
            for item in profiles
            if item.milestone_evidence_quality < self.minimum_completion_quality
            or item.data_quality < self.minimum_completion_quality
            or item.knowledge_quality < self.minimum_completion_quality
            or item.strategy_quality < self.minimum_completion_quality
            or item.runtime_stability < self.minimum_completion_quality
            or item.validation_quality < self.minimum_completion_quality
            or item.monitoring_quality < self.minimum_completion_quality
            or item.rollback_readiness < self.minimum_completion_quality
            or item.documentation_quality < self.minimum_completion_quality
            or item.handoff_quality < self.minimum_completion_quality
            or item.completion_risk > self.maximum_completion_risk
        )
        score = round(mean(item.milestone_completion_score for item in profiles), 6)
        if review_profiles:
            return MilestoneFCompletionDecision(
                status="MILESTONE_F_COMPLETION_REVIEW_REQUIRED",
                completion="REVIEW",
                reason="milestone_f_completion_review_required",
                completion_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        if score >= self.minimum_completion_score:
            return MilestoneFCompletionDecision(
                status="MILESTONE_F_COMPLETE",
                completion="COMPLETE",
                reason="production_readiness_and_handoff_complete",
                completion_score=score,
                review_profile_count=0,
                invalid_market_regime_count=0,
                next_milestone_allowed=True,
            )
        return MilestoneFCompletionDecision(
            status="MILESTONE_F_COMPLETION_OBSERVATION_ONLY",
            completion="OBSERVE",
            reason="milestone_f_completion_score_below_threshold",
            completion_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
