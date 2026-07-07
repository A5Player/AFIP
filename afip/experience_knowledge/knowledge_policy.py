"""Experience knowledge readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .knowledge_profile import ExperienceKnowledgeProfile


@dataclass(frozen=True)
class ExperienceKnowledgeDecision:
    """Deterministic experience knowledge decision."""

    status: str
    readiness: str
    reason: str
    experience_score: float
    review_profile_count: int
    invalid_market_regime_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "experience_score": self.experience_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
        }


@dataclass(frozen=True)
class ExperienceKnowledgePolicy:
    """Accept experience knowledge only when evidence quality is sufficient."""

    minimum_experience_score: float = 0.60
    minimum_data_quality: float = 0.60
    minimum_knowledge_quality: float = 0.60
    minimum_recency_score: float = 0.50

    def decide(
        self,
        profiles: tuple[ExperienceKnowledgeProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> ExperienceKnowledgeDecision:
        if invalid_market_regime_count:
            return ExperienceKnowledgeDecision(
                status="EXPERIENCE_KNOWLEDGE_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_experience_knowledge",
                experience_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return ExperienceKnowledgeDecision(
                status="EXPERIENCE_KNOWLEDGE_WAIT",
                readiness="WAIT",
                reason="experience_observations_required",
                experience_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )

        score = round(mean(item.experience_score for item in profiles), 6)
        review_profiles = tuple(
            item
            for item in profiles
            if item.experience_score < self.minimum_experience_score
            or item.average_data_quality < self.minimum_data_quality
            or item.average_knowledge_quality < self.minimum_knowledge_quality
            or item.average_recency_score < self.minimum_recency_score
        )
        if review_profiles:
            return ExperienceKnowledgeDecision(
                status="EXPERIENCE_KNOWLEDGE_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="experience_profiles_need_validation_before_runtime_use",
                experience_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        return ExperienceKnowledgeDecision(
            status="EXPERIENCE_KNOWLEDGE_READY",
            readiness="READY",
            reason="experience_profiles_ready_for_deterministic_runtime_use",
            experience_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
