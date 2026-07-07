"""Strategy evolution readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .evolution_profile import StrategyEvolutionProfile


@dataclass(frozen=True)
class StrategyEvolutionDecision:
    """Deterministic strategy evolution decision."""

    status: str
    readiness: str
    reason: str
    evolution_score: float
    review_profile_count: int
    invalid_market_regime_count: int
    runtime_write: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "evolution_score": self.evolution_score,
            "review_profile_count": self.review_profile_count,
            "invalid_market_regime_count": self.invalid_market_regime_count,
            "runtime_write": self.runtime_write,
        }


@dataclass(frozen=True)
class StrategyEvolutionPolicy:
    """Allow strategy evolution candidates only when knowledge quality is sufficient."""

    minimum_evidence_quality: float = 0.60
    maximum_weight_adjustment: float = 0.20

    def decide(
        self,
        profiles: tuple[StrategyEvolutionProfile, ...],
        *,
        invalid_market_regime_count: int = 0,
    ) -> StrategyEvolutionDecision:
        if invalid_market_regime_count:
            return StrategyEvolutionDecision(
                status="STRATEGY_EVOLUTION_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_strategy_evolution",
                evolution_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=invalid_market_regime_count,
            )
        if not profiles:
            return StrategyEvolutionDecision(
                status="STRATEGY_EVOLUTION_WAIT",
                readiness="WAIT",
                reason="experience_knowledge_required",
                evolution_score=0.0,
                review_profile_count=0,
                invalid_market_regime_count=0,
            )
        review_profiles = tuple(
            item
            for item in profiles
            if item.average_evidence_quality < self.minimum_evidence_quality
            or item.average_data_quality < self.minimum_evidence_quality
            or item.average_knowledge_quality < self.minimum_evidence_quality
            or item.average_reliability_score < self.minimum_evidence_quality
            or abs(item.weight_adjustment) > self.maximum_weight_adjustment
        )
        score = round(mean(item.evolution_pressure for item in profiles), 6)
        if review_profiles:
            return StrategyEvolutionDecision(
                status="STRATEGY_EVOLUTION_REVIEW_REQUIRED",
                readiness="REVIEW",
                reason="strategy_evolution_evidence_review_required",
                evolution_score=score,
                review_profile_count=len(review_profiles),
                invalid_market_regime_count=0,
            )
        return StrategyEvolutionDecision(
            status="STRATEGY_EVOLUTION_READY",
            readiness="READY",
            reason="strategy_evolution_candidates_ready",
            evolution_score=score,
            review_profile_count=0,
            invalid_market_regime_count=0,
        )
