"""Production Milestone E Pack 7 portfolio intelligence policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .portfolio_profile import PortfolioProfile


@dataclass(frozen=True)
class PortfolioDecision:
    """Deterministic decision describing portfolio intelligence readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class PortfolioPolicy:
    """Select the strongest data-derived portfolio intelligence profile."""

    def decide(self, profiles: Tuple[PortfolioProfile, ...]) -> PortfolioDecision:
        if not profiles:
            return PortfolioDecision(
                status="PORTFOLIO_INTELLIGENCE_WAIT",
                action="WAIT",
                reason="no_usable_portfolio_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return PortfolioDecision(
                status="PORTFOLIO_INTELLIGENCE_WAIT",
                action="WAIT",
                reason="insufficient_portfolio_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.portfolio_resilience_score,
                item.average_correlation_score,
                item.average_risk_budget_utilization,
                item.average_drawdown_pressure,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return PortfolioDecision(
            status="PORTFOLIO_INTELLIGENCE_READY",
            action="APPLY_PORTFOLIO_CONTEXT",
            reason="portfolio_profile_ready",
            selected_profile_key=selected.profile_key,
        )
