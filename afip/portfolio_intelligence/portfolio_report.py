"""Production Milestone E Pack 7 portfolio intelligence report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .portfolio_policy import PortfolioDecision
from .portfolio_profile import PortfolioProfile


@dataclass(frozen=True)
class PortfolioReport:
    """Immutable report for portfolio intelligence runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_portfolio_scope: str
    selected_direction: str
    average_exposure_score: float
    average_correlation_score: float
    average_risk_budget_utilization: float
    average_diversification_score: float
    average_portfolio_return_score: float
    average_drawdown_pressure: float
    average_execution_cost_score: float
    portfolio_resilience_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(cls, profiles: Tuple[PortfolioProfile, ...], decision: PortfolioDecision) -> "PortfolioReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_portfolio_scope=selected.portfolio_scope if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            average_exposure_score=selected.average_exposure_score if selected else 0.0,
            average_correlation_score=selected.average_correlation_score if selected else 0.0,
            average_risk_budget_utilization=selected.average_risk_budget_utilization if selected else 0.0,
            average_diversification_score=selected.average_diversification_score if selected else 0.0,
            average_portfolio_return_score=selected.average_portfolio_return_score if selected else 0.0,
            average_drawdown_pressure=selected.average_drawdown_pressure if selected else 0.0,
            average_execution_cost_score=selected.average_execution_cost_score if selected else 0.0,
            portfolio_resilience_score=selected.portfolio_resilience_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "PORTFOLIO_INTELLIGENCE_READY" and selected is not None,
        )
