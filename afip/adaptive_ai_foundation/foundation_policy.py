"""Adaptive AI foundation readiness policy."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .foundation_profile import AdaptiveAIFoundationProfile


@dataclass(frozen=True)
class AdaptiveAIFoundationDecision:
    """Deterministic foundation decision produced after regime-first profiling."""

    status: str
    readiness: str
    reason: str
    foundation_score: float
    selected_market_regime: str | None
    invalid_regime_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "reason": self.reason,
            "foundation_score": self.foundation_score,
            "selected_market_regime": self.selected_market_regime,
            "invalid_regime_count": self.invalid_regime_count,
        }


class AdaptiveAIFoundationPolicy:
    """Select adaptive foundation state without randomness or fixed market assumptions."""

    def decide(
        self,
        profiles: tuple[AdaptiveAIFoundationProfile, ...],
        *,
        invalid_regime_count: int = 0,
    ) -> AdaptiveAIFoundationDecision:
        if invalid_regime_count:
            return AdaptiveAIFoundationDecision(
                status="ADAPTIVE_AI_FOUNDATION_BLOCKED",
                readiness="BLOCKED",
                reason="market_regime_required_before_signal_context",
                foundation_score=0.0,
                selected_market_regime=None,
                invalid_regime_count=invalid_regime_count,
            )
        if not profiles:
            return AdaptiveAIFoundationDecision(
                status="ADAPTIVE_AI_FOUNDATION_WAIT",
                readiness="WAIT",
                reason="market_knowledge_observations_required",
                foundation_score=0.0,
                selected_market_regime=None,
                invalid_regime_count=0,
            )

        selected = max(profiles, key=lambda item: (item.readiness_score, item.expectancy, item.market_regime))
        foundation_score = round(mean(item.readiness_score for item in profiles), 6)
        return AdaptiveAIFoundationDecision(
            status="ADAPTIVE_AI_FOUNDATION_READY",
            readiness="READY",
            reason="regime_first_adaptive_foundation_ready",
            foundation_score=foundation_score,
            selected_market_regime=selected.market_regime,
            invalid_regime_count=0,
        )
