"""Provider routing and automatic fallback for AFIP financial data sources."""

from __future__ import annotations

from dataclasses import dataclass

from afip.provider_management.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class ProviderRouteResult:
    """Selected provider route used by runtime integrations."""

    status: str
    provider_name: str | None
    decision: str
    score: float
    fallback_used: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "provider_name": self.provider_name,
            "decision": self.decision,
            "score": round(self.score, 4),
            "fallback_used": self.fallback_used,
            "reason": self.reason,
        }


class ProviderRouter:
    """Select the best provider while preserving safe fallback behavior."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    def route(self, preferred_provider: str | None = None) -> ProviderRouteResult:
        scores = self.registry.quality_scores()
        if not scores:
            return ProviderRouteResult(
                status="PROVIDER_ROUTE_EMPTY",
                provider_name=None,
                decision="UNAVAILABLE",
                score=0.0,
                fallback_used=False,
                reason="no_provider_scores_available",
            )

        if preferred_provider:
            preferred = next((score for score in scores if score.provider_name == preferred_provider), None)
            if preferred and preferred.decision == "READY":
                return ProviderRouteResult(
                    status="PROVIDER_ROUTE_READY",
                    provider_name=preferred.provider_name,
                    decision=preferred.decision,
                    score=preferred.score,
                    fallback_used=False,
                    reason="preferred_provider_ready",
                )

        for score in scores:
            if score.decision == "READY":
                return ProviderRouteResult(
                    status="PROVIDER_ROUTE_READY",
                    provider_name=score.provider_name,
                    decision=score.decision,
                    score=score.score,
                    fallback_used=bool(preferred_provider and score.provider_name != preferred_provider),
                    reason="provider_route_selected",
                )

        for score in scores:
            if score.decision == "REVIEW":
                return ProviderRouteResult(
                    status="PROVIDER_ROUTE_REVIEW",
                    provider_name=score.provider_name,
                    decision=score.decision,
                    score=score.score,
                    fallback_used=bool(preferred_provider and score.provider_name != preferred_provider),
                    reason="provider_route_review_only",
                )

        return ProviderRouteResult(
            status="PROVIDER_ROUTE_UNAVAILABLE",
            provider_name=None,
            decision="UNAVAILABLE",
            score=0.0,
            fallback_used=bool(preferred_provider),
            reason="all_providers_unavailable",
        )
