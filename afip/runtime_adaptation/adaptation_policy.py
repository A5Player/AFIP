"""Runtime adaptation readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .adaptation_profile import RuntimeAdaptationProfile


@dataclass(frozen=True)
class RuntimeAdaptationDecision:
    """Deterministic runtime adaptation decision."""

    status: str
    readiness: str
    reason: str
    adaptation_score: float
    review_profile_count: int
    invalid_market_regime_count: int
    runtime_write: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "adaptation_score": self.adaptation_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
            "runtime_write": self.runtime_write,
        }


@dataclass(frozen=True)
class RuntimeAdaptationPolicy:
    """Accept runtime adaptation plans only when evidence is stable and review-safe."""

    minimum_adaptation_quality: float = 0.60
    maximum_execution_cost: float = 0.70
    maximum_runtime_delta: float = 0.10

    def decide(
        self,
        profiles: tuple[RuntimeAdaptationProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> RuntimeAdaptationDecision:
        if invalid_market_regime_count:
            return RuntimeAdaptationDecision(
                status="RUNTIME_ADAPTATION_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_runtime_adaptation",
                adaptation_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return RuntimeAdaptationDecision(
                status="RUNTIME_ADAPTATION_WAIT",
                readiness="WAIT",
                reason="strategy_evolution_required",
                adaptation_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )
        review_profiles = tuple(
            item
            for item in profiles
            if item.adaptation_quality < self.minimum_adaptation_quality
            or item.data_quality < self.minimum_adaptation_quality
            or item.knowledge_quality < self.minimum_adaptation_quality
            or item.stability_score < self.minimum_adaptation_quality
            or item.execution_cost > self.maximum_execution_cost
            or abs(item.runtime_weight_delta) > self.maximum_runtime_delta
        )
        score = round(mean(item.adaptation_strength for item in profiles), 6)
        if review_profiles:
            return RuntimeAdaptationDecision(
                status="RUNTIME_ADAPTATION_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="runtime_adaptation_review_required",
                adaptation_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        return RuntimeAdaptationDecision(
            status="RUNTIME_ADAPTATION_READY",
            readiness="READY",
            reason="runtime_adaptation_plan_ready",
            adaptation_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
