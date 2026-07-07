"""AI integration readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .integration_profile import AIIntegrationProfile


@dataclass(frozen=True)
class AIIntegrationDecision:
    """Deterministic AI integration decision."""

    status: str
    readiness: str
    reason: str
    integration_score: float
    review_profile_count: int
    invalid_market_regime_count: int
    autonomous_execution: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "integration_score": self.integration_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
            "autonomous_execution": self.autonomous_execution,
        }


@dataclass(frozen=True)
class AIIntegrationPolicy:
    """Permit AI assistance only when deterministic evidence is review-safe."""

    minimum_integration_quality: float = 0.60
    maximum_integration_risk: float = 0.70

    def decide(
        self,
        profiles: tuple[AIIntegrationProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> AIIntegrationDecision:
        if invalid_market_regime_count:
            return AIIntegrationDecision(
                status="AI_INTEGRATION_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_ai_integration",
                integration_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return AIIntegrationDecision(
                status="AI_INTEGRATION_WAIT",
                readiness="WAIT",
                reason="runtime_adaptation_required",
                integration_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )
        review_profiles = tuple(
            item
            for item in profiles
            if item.integration_quality < self.minimum_integration_quality
            or item.data_quality < self.minimum_integration_quality
            or item.knowledge_quality < self.minimum_integration_quality
            or item.runtime_stability < self.minimum_integration_quality
            or item.explainability_score < self.minimum_integration_quality
            or item.integration_risk > self.maximum_integration_risk
        )
        score = round(mean(item.ai_alignment_score for item in profiles), 6)
        if review_profiles:
            return AIIntegrationDecision(
                status="AI_INTEGRATION_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="ai_integration_review_required",
                integration_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        return AIIntegrationDecision(
            status="AI_INTEGRATION_READY",
            readiness="READY",
            reason="ai_integration_assist_ready",
            integration_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
